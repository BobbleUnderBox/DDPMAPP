---
name: code-review
description: Review newly added or modified XDDPMAPP code against the project style guide, architecture/API contracts, and general quality expectations. Use for Git diffs, patches, or explicitly specified files; do not use this skill to implement fixes.
metadata:
  short-description: Review new code against project conventions
---

# Code Review

Review only the requested change and produce actionable findings. The canonical project rules are in `docs/code_style.md`; read it before evaluating code.

## Review input

Use this order when determining what to review:

1. An explicit patch, diff, or file list from the user takes precedence.
2. Otherwise inspect the repository status, staged diff, unstaged diff, and untracked source files. Do not treat generated, vendor, build, cache, or dependency directories as new source.
3. If there is no reviewable change, say so and identify what input is missing. Do not invent findings from documentation alone.

Review the changed lines and their direct consequences. Do not report unrelated pre-existing issues unless they are necessary to explain a regression introduced by the change.

## Context to read

Before reviewing, read the applicable `AGENTS.md` files and `docs/code_style.md`. For project behavior and structure, consult `README.md`, `docs/api.md`, and `docs/framework.md`. Read model, uncertainty, contract, or other domain documents only when the change touches that area. Inspect nearby approved code and repository tool configuration when available; do not assume a formatter or linter that the repository does not configure.

## What to check

- Naming, imports, typing, structure, comments, duplication, and consistency with the language conventions in `docs/code_style.md`.
- Correct layer boundaries: React feature organization; thin FastAPI API entry points; service-owned business rules; isolated database, external integration, model-worker, and analysis responsibilities.
- API and worker contracts, task state transitions, stable IDs, idempotency, cancellation, restart/retry behavior, and protection against stale work overwriting current results.
- Input validation, error propagation, logging context, resource cleanup, and obvious correctness or maintainability problems.
- Tests for changed behavior, especially boundary inputs, failure paths, status transitions, contracts, random seeds, and `masks[N, H, W]` boolean outputs when relevant.
- Documentation updates required by changed public behavior, data shapes, migrations, or user-visible results.

This is not a full security, performance, dependency, or medical-correctness audit. Report such concerns only when they are obvious and directly introduced by the change; otherwise state that those areas were not assessed.

## Review workflow

1. Start with a short, high-level list of the important findings, ordered by severity. Keep this list concise and omit empty categories.
2. Expand each finding with `file:line`, severity, category, evidence, impact, and a concrete correction direction. Do not make vague requests such as “clean this up”.
3. Separate blocking problems from non-blocking suggestions. A missing test is blocking only when the changed behavior has a meaningful regression risk or violates an explicit project contract.
4. End with a compact summary of reviewed files, checks/tests actually run, and limitations or unresolved questions.

Use these severities:

- **Must fix**: likely defect, explicit contract/architecture violation, data-loss or stale-state risk, or a missing validation/test that makes the change unsafe to accept.
- **Suggestion**: style, readability, maintainability, or test improvement that does not make the change unsafe by itself.
- **Note**: useful context or a deliberate trade-off that does not require a change.

Do not modify files while performing a review unless the user separately asks for fixes. Read-only inspection and relevant, non-destructive checks are allowed. Do not install dependencies, contact external services, or run expensive workloads without explicit permission.
