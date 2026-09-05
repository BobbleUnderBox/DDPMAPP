"""Render the accompanying Traditional Chinese paper review without dependencies.

Supported Markdown: a leading ``# title``, blank-line-separated paragraphs,
``**bold**``, and ``[label](https://...)`` links. No Word installation is needed.
Run ``python render_review.py`` or pass the path to another Markdown file.
Every generated DOCX is checked for well-formed XML and internal relationships
before either output file is written.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path, PurePosixPath
import re
from typing import Iterable
import xml.etree.ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile


DEFAULT_MARKDOWN = "Bayesian_MRI_2023_學術評析_zh-TW.md"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
XML = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("w", W)
ET.register_namespace("r", R)


@dataclass(frozen=True)
class Span:
    text: str
    bold: bool = False
    url: str | None = None
    highlighted: bool = False


@dataclass(frozen=True)
class Paragraph:
    spans: tuple[Span, ...]
    title: bool = False


def _inline(text: str, bold: bool = False, url: str | None = None) -> list[Span]:
    """Parse the deliberately small Markdown subset used by this review."""
    result: list[Span] = []
    pattern = re.compile(r"\*\*(.+?)\*\*|\[([^\]]+)\]\(([^\s]+?)\)")
    position = 0
    for match in pattern.finditer(text):
        if match.start() > position:
            result.append(Span(text[position:match.start()], bold, url))
        if match.group(1) is not None:
            result.extend(_inline(match.group(1), bold=True, url=url))
        else:
            result.extend(_inline(match.group(2), bold=bold, url=match.group(3)))
        position = match.end()
    if position < len(text):
        result.append(Span(text[position:], bold, url))
    return result


def _highlight_english_quotes(spans: Iterable[Span]) -> tuple[Span, ...]:
    """Shade English curly-quoted passages, even across bold/link boundaries."""
    spans = tuple(spans)
    plain = "".join(span.text for span in spans)
    quote_ranges = [
        (match.start(), match.end())
        for match in re.finditer(r"“[^”\n]+”", plain)
        if re.search(r"[A-Za-z]", match.group())
        and not re.search(r"[\u3400-\u9fff]", match.group())
    ]
    result: list[Span] = []
    offset = 0
    for span in spans:
        end = offset + len(span.text)
        boundaries = {offset, end}
        for start_quote, end_quote in quote_ranges:
            if start_quote < end and end_quote > offset:
                boundaries.add(max(offset, start_quote))
                boundaries.add(min(end, end_quote))
        ordered = sorted(boundaries)
        for start, stop in zip(ordered, ordered[1:]):
            if start == stop:
                continue
            highlighted = any(a <= start < b for a, b in quote_ranges)
            result.append(replace(span, text=span.text[start-offset:stop-offset],
                                  highlighted=highlighted))
        offset = end
    return tuple(result)


def parse_markdown(markdown: str) -> tuple[Paragraph, ...]:
    markdown = markdown.lstrip("\ufeff").strip()
    if not markdown:
        raise ValueError("The Markdown input is empty.")
    lines = markdown.splitlines()
    if not lines[0].startswith("# "):
        raise ValueError("The first line must be a '# ' document title.")
    title = lines[0][2:].strip()
    if not title:
        raise ValueError("The document title is empty.")
    result = [Paragraph(_highlight_english_quotes(_inline(title)), title=True)]
    body = "\n".join(lines[1:]).strip()
    for block in re.split(r"\n\s*\n", body):
        if not block.strip():
            continue
        text = " ".join(line.strip() for line in block.splitlines())
        result.append(Paragraph(_highlight_english_quotes(_inline(text))))
    return tuple(result)


def _node(parent: ET.Element, tag: str, **attributes: str) -> ET.Element:
    return ET.SubElement(parent, f"{{{W}}}{tag}",
                         {f"{{{W}}}{key}": str(value) for key, value in attributes.items()})


def _xml(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _fonts(parent: ET.Element) -> None:
    _node(parent, "rFonts", ascii="Times New Roman", hAnsi="Times New Roman",
          eastAsia="新細明體", cs="Times New Roman", hint="eastAsia")


def _run(parent: ET.Element, span: Span) -> None:
    run = _node(parent, "r")
    properties = _node(run, "rPr")
    if span.url:
        _node(properties, "rStyle", val="Hyperlink")
    _fonts(properties)
    if span.bold:
        _node(properties, "b")
        _node(properties, "bCs")
    if span.highlighted:
        # Run shading allows a pale yellow unavailable in Word's highlight palette.
        _node(properties, "shd", val="clear", color="auto", fill="FFF2CC")
    text = _node(run, "t")
    text.set(f"{{{XML}}}space", "preserve")
    text.text = span.text


def _styles() -> bytes:
    root = ET.Element(f"{{{W}}}styles")
    defaults = _node(root, "docDefaults")
    run_default = _node(defaults, "rPrDefault")
    run_properties = _node(run_default, "rPr")
    _fonts(run_properties)
    _node(run_properties, "sz", val="24")
    _node(run_properties, "szCs", val="24")
    _node(run_properties, "lang", val="zh-TW", eastAsia="zh-TW", bidi="en-US")
    paragraph_default = _node(defaults, "pPrDefault")
    paragraph_properties = _node(paragraph_default, "pPr")
    _node(paragraph_properties, "widowControl")
    _node(paragraph_properties, "spacing", after="160", line="360", lineRule="auto")

    normal = _node(root, "style", type="paragraph", default="1", styleId="Normal")
    _node(normal, "name", val="Normal")
    _node(normal, "qFormat")
    properties = _node(normal, "pPr")
    _node(properties, "jc", val="both")

    title = _node(root, "style", type="paragraph", styleId="Title")
    _node(title, "name", val="Title")
    _node(title, "basedOn", val="Normal")
    _node(title, "next", val="Normal")
    _node(title, "qFormat")
    properties = _node(title, "pPr")
    _node(properties, "keepNext")
    _node(properties, "keepLines")
    _node(properties, "spacing", before="0", after="360", line="360", lineRule="auto")
    _node(properties, "jc", val="center")
    properties = _node(title, "rPr")
    _node(properties, "b")
    _node(properties, "bCs")
    _node(properties, "color", val="19354D")
    _node(properties, "sz", val="42")
    _node(properties, "szCs", val="42")

    link = _node(root, "style", type="character", styleId="Hyperlink")
    _node(link, "name", val="Hyperlink")
    properties = _node(link, "rPr")
    _node(properties, "color", val="175A8A")
    _node(properties, "u", val="single")
    return _xml(root)


def _footer() -> bytes:
    root = ET.Element(f"{{{W}}}ftr")
    paragraph = _node(root, "p")
    properties = _node(paragraph, "pPr")
    _node(properties, "spacing", after="0", line="240", lineRule="auto")
    _node(properties, "jc", val="center")
    field = _node(paragraph, "fldSimple", instr=" PAGE ")
    run = _node(field, "r")
    properties = _node(run, "rPr")
    _fonts(properties)
    _node(properties, "sz", val="20")
    _node(properties, "szCs", val="20")
    _node(run, "t").text = "1"
    return _xml(root)


def _relationships(entries: Iterable[tuple[str, str, str, bool]]) -> bytes:
    root = ET.Element("Relationships", xmlns=REL)
    for identifier, relationship_type, target, external in entries:
        attributes = {"Id": identifier, "Type": relationship_type, "Target": target}
        if external:
            attributes["TargetMode"] = "External"
        ET.SubElement(root, "Relationship", attributes)
    return _xml(root)


def build_docx(paragraphs: tuple[Paragraph, ...]) -> bytes:
    root = ET.Element(f"{{{W}}}document")
    body = _node(root, "body")
    urls: dict[str, str] = {}
    for paragraph in paragraphs:
        element = _node(body, "p")
        properties = _node(element, "pPr")
        _node(properties, "pStyle", val="Title" if paragraph.title else "Normal")
        _node(properties, "widowControl")
        for span in paragraph.spans:
            if span.url:
                identifier = urls.setdefault(span.url, f"rIdLink{len(urls) + 1}")
                hyperlink = _node(element, "hyperlink", history="1")
                hyperlink.set(f"{{{R}}}id", identifier)
                _run(hyperlink, span)
            else:
                _run(element, span)
    section = _node(body, "sectPr")
    footer_reference = _node(section, "footerReference", type="default")
    footer_reference.set(f"{{{R}}}id", "rIdFooter")
    _node(section, "pgSz", w="11906", h="16838")
    _node(section, "pgMar", top="1440", right="1440", bottom="1440", left="1440",
          header="720", footer="720", gutter="0")
    _node(section, "pgNumType", start="1")

    settings = ET.Element(f"{{{W}}}settings")
    _node(settings, "zoom", percent="100")
    _node(settings, "defaultTabStop", val="720")
    _node(settings, "updateFields", val="true")
    compatibility = _node(settings, "compat")
    _node(compatibility, "compatSetting", name="compatibilityMode",
          uri="http://schemas.microsoft.com/office/word", val="15")
    fonts = ET.Element(f"{{{W}}}fonts")
    for name in ("Times New Roman", "新細明體"):
        font = _node(fonts, "font", name=name)
        _node(font, "family", val="roman")
        _node(font, "pitch", val="variable")

    content_types = ET.Element("Types", xmlns=CONTENT_TYPES)
    for extension, mime in (("rels", "application/vnd.openxmlformats-package.relationships+xml"),
                            ("xml", "application/xml")):
        ET.SubElement(content_types, "Default", Extension=extension, ContentType=mime)
    overrides = {
        "/word/document.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
        "/word/styles.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
        "/word/settings.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml",
        "/word/fontTable.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml",
        "/word/footer1.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
        "/docProps/core.xml": "application/vnd.openxmlformats-package.core-properties+xml",
        "/docProps/app.xml": "application/vnd.openxmlformats-officedocument.extended-properties+xml",
    }
    for name, mime in overrides.items():
        ET.SubElement(content_types, "Override", PartName=name, ContentType=mime)

    title = "".join(span.text for span in paragraphs[0].spans)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f'<dc:title>{escape(title)}</dc:title><dc:language>zh-TW</dc:language>'
        '<dc:creator>Codex</dc:creator>'
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>'
        '</cp:coreProperties>'
    ).encode("utf-8")
    app = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        '<Application>Python standard-library review renderer</Application>'
        '</Properties>'
    ).encode("utf-8")
    document_relationships = [
        ("rIdStyles", f"{R}/styles", "styles.xml", False),
        ("rIdSettings", f"{R}/settings", "settings.xml", False),
        ("rIdFonts", f"{R}/fontTable", "fontTable.xml", False),
        ("rIdFooter", f"{R}/footer", "footer1.xml", False),
    ]
    document_relationships.extend(
        (identifier, f"{R}/hyperlink", url, True) for url, identifier in urls.items()
    )
    parts = {
        "[Content_Types].xml": _xml(content_types),
        "_rels/.rels": _relationships([
            ("rIdDocument", f"{R}/officeDocument", "word/document.xml", False),
            ("rIdCore", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
             "docProps/core.xml", False),
            ("rIdApp", f"{R}/extended-properties", "docProps/app.xml", False),
        ]),
        "word/document.xml": _xml(root),
        "word/styles.xml": _styles(),
        "word/settings.xml": _xml(settings),
        "word/fontTable.xml": _xml(fonts),
        "word/footer1.xml": _footer(),
        "word/_rels/document.xml.rels": _relationships(document_relationships),
        "docProps/core.xml": core,
        "docProps/app.xml": app,
    }
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)
    result = buffer.getvalue()
    validate_docx(result)
    return result


def validate_docx(data: bytes) -> None:
    """Check ZIP integrity, XML syntax, referenced parts, and link identifiers.

    These are package integrity checks, not a full OOXML schema validation or a
    visual pagination check. Word/LibreOffice can be used for the latter.
    """
    with ZipFile(BytesIO(data)) as archive:
        invalid = archive.testzip()
        if invalid:
            raise ValueError(f"Corrupt DOCX archive entry: {invalid}")
        names = set(archive.namelist())
        required = {"[Content_Types].xml", "_rels/.rels", "word/document.xml",
                    "word/styles.xml", "word/footer1.xml", "word/_rels/document.xml.rels"}
        if not required <= names:
            raise ValueError(f"Missing DOCX parts: {required - names}")
        parsed = {
            name: ET.fromstring(archive.read(name))
            for name in names if name.endswith((".xml", ".rels"))
        }
        for name, root in parsed.items():
            if not name.endswith(".rels"):
                continue
            base = PurePosixPath(".") if name == "_rels/.rels" else PurePosixPath(name).parent.parent
            for relationship in root:
                if relationship.get("TargetMode") != "External":
                    target = str(base / relationship.attrib["Target"])
                    if target not in names:
                        raise ValueError(f"Broken DOCX relationship: {name} -> {target}")
        relationships = parsed["word/_rels/document.xml.rels"]
        identifiers = {element.attrib["Id"] for element in relationships}
        if len(identifiers) != len(relationships):
            raise ValueError("Duplicate DOCX relationship identifiers.")
        for element in parsed["word/document.xml"].iter():
            identifier = element.get(f"{{{R}}}id")
            if identifier and identifier not in identifiers:
                raise ValueError(f"Unresolved document relationship: {identifier}")


def build_html(paragraphs: tuple[Paragraph, ...]) -> str:
    title = escape("".join(span.text for span in paragraphs[0].spans))
    blocks = []
    for paragraph in paragraphs:
        contents = []
        for span in paragraph.spans:
            text = escape(span.text)
            if span.highlighted:
                text = f"<mark>{text}</mark>"
            if span.bold:
                text = f"<strong>{text}</strong>"
            if span.url:
                text = f'<a href="{escape(span.url, quote=True)}">{text}</a>'
            contents.append(text)
        tag = "h1" if paragraph.title else "p"
        blocks.append(f"<{tag}>{''.join(contents)}</{tag}>")
    return f'''<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ color-scheme: light; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: #f4f4f1; color: #20272d;
       font-family: "Times New Roman", "新細明體", "PMingLiU", "Noto Serif CJK TC", serif;
       font-size: 18px; line-height: 1.85; }}
main {{ width: min(52rem, calc(100% - 2rem)); margin: 2rem auto; padding: 3rem 3.5rem;
       background: white; box-shadow: 0 1px 12px #0000000b; }}
h1 {{ margin: 0 0 1.6em; color: #19354d; font-size: 1.8em; line-height: 1.55;
     font-weight: 700; text-align: center; break-after: avoid; }}
p {{ margin: 0 0 1.2em; text-align: justify; overflow-wrap: anywhere; orphans: 2; widows: 2; }}
strong {{ font-weight: 700; color: #142d40; }}
a {{ color: #175a8a; text-decoration: underline; text-underline-offset: .15em; }}
mark {{ color: inherit; background: #fff2cc; padding: .05em 0; }}
@media (max-width: 600px) {{ main {{ padding: 1.6rem 1.2rem; }} h1 {{ font-size: 1.5em; }} }}
@page {{ size: A4; margin: 25.4mm; }}
@media print {{
  body {{ background: white; font-size: 12pt; line-height: 1.5; }}
  main {{ width: auto; margin: 0; padding: 0; box-shadow: none; }}
  h1 {{ font-size: 21pt; margin-bottom: 18pt; }}
  p {{ margin-bottom: 8pt; }}
  mark {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
}}
</style>
</head>
<body>
<main>
{chr(10).join(blocks)}
</main>
</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", nargs="?", type=Path,
                        default=Path(__file__).with_name(DEFAULT_MARKDOWN))
    arguments = parser.parse_args()
    source = arguments.markdown.resolve()
    if not source.is_file():
        parser.error(f"Markdown file does not exist: {source}")
    paragraphs = parse_markdown(source.read_text(encoding="utf-8-sig"))
    docx = build_docx(paragraphs)
    html = build_html(paragraphs)
    docx_path = source.with_suffix(".docx")
    html_path = source.with_suffix(".html")
    docx_path.write_bytes(docx)
    html_path.write_text(html, encoding="utf-8")
    print(f"DOCX: {docx_path}")
    print(f"HTML: {html_path}")
    print(f"Validated {len(paragraphs)} paragraphs (including title); XML and relationships are valid.")


if __name__ == "__main__":
    main()
