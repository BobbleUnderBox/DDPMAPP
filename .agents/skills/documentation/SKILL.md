---
name: documentation
description: Review XDDPMAPP's important documents and local skills for drift, duplication, broken references, and excessive length; use for periodic maintenance recommendations, not routine documentation editing.
metadata:
  short-description: Check important docs and skills for concise consistency
---

# Documentation

Use this skill for a periodic or explicitly requested, read-only maintenance review of XDDPMAPP documentation and project-local skills. Give recommendations only; do not edit files unless the user later authorizes a separate change.

## Review scope

1. Follow `AGENTS.md` as the project instruction source, but do not treat its file list as the maintenance scope.
2. Read `README.md` and derive the document scope from every local Markdown link target in it. Include missing or malformed targets as link findings; also review `README.md` itself.
3. Inspect the five current project-local skill entrypoints: `code-review`, `documentation`, `git-operations`, `refactoring-cleanup`, and `unit-test`. Inspect a skill's `agents/openai.yaml` only when metadata or invocation behavior is relevant.

## Checks

- Compare the README-indexed documents for delivery-scope, architecture, API, model/tool progress, development-rule, and style contradictions, stale claims, or duplicated sources of truth.
- Check every README link target for path errors, missing files, and unclear ownership. Keep `docs/project_goal.md` separate from current delivery requirements.
- Compare the five skills for overlapping instructions, stale project assumptions, unclear invocation boundaries, and unnecessary repetition.
- Treat 100 lines as a soft warning threshold for important documents and skill entrypoints. A length warning alone is not a defect; suggest removing repetition or moving deep, mode-specific guidance into a linked `references/` file.
- Prefer one canonical rule with links from other files. Do not recommend rewriting coherent content only to reduce the line count.

## Output

- Start with the files and skill entrypoints checked, including line-count warnings when relevant.
- Return at most five recommendations, ordered by impact. Each item must include priority, file and section, concise evidence, and a concrete maintenance direction.
- Do not quote long passages. If no meaningful issue is found, say that no maintenance change is recommended.

## Boundaries

- Do not modify project files, create a report file, install skills, or create a scheduler as part of this review.
- Do not infer delivered behavior from long-term plans, research notes, or model/tool backlogs.
