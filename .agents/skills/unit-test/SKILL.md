---
name: unit-test
description: Write and run focused unit and regression tests for new or modified XDDPMAPP code, preserve existing behavior, and clean up test artifacts. Use after implementation or when asked to test a change; not for end-to-end testing or real model inference.
---

# Unit Test

Write reusable tests for the requested behavior and relevant existing behavior. Report defects without changing product code unless the current development task already authorizes the fix. Passing unit tests provides evidence for covered cases, not a guarantee that all existing functionality is unaffected.

## Establish scope and prerequisites

1. Read applicable `AGENTS.md` files and `docs/code_style.md`. Use `README.md` for delivered scope, `docs/api.md` for relevant behavior, and `docs/framework.md` for boundaries. Consult domain documents only when the change touches them; do not treat long-term plans as implemented requirements.
2. Prefer the user's explicit patch or file list. Otherwise inspect staged and unstaged diffs and untracked source files, excluding generated, vendor, dependency, and cache directories. Record pre-existing modifications and relevant artifacts before running commands; preserve staged state and unrelated user work.
3. Inspect actual source, callers, existing tests, package manifests, lockfiles, and test configuration. Follow established commands and layout. `docs/devlog.md` plans Vitest for the frontend and pytest for Python; these are directions, not proof of installed tools. Playwright belongs to separate end-to-end work.
4. If there is no executable code, report that there is nothing to unit-test yet. Do not create placeholder tests or scaffold an application from documentation. If code exists but test setup is missing, identify the missing pieces. Add only minimal setup needed by an authorized implementation/testing task; do not silently install packages, select a new package manager, upgrade dependencies, or create a second lockfile.

## Design and run tests

- Before adding tests, run the relevant existing unit tests when runnable to record the current baseline. This baseline describes the current working tree, not the state before the user's change. Do not reset or stash user work to establish a baseline. If unavailable, report the limitation; do not assume every failure was introduced by this change.
- Derive expectations from requirements and observable behavior, not by copying the implementation. Test meaningful changed behavior, boundary inputs, failure paths, and affected existing consumers. Avoid duplicate cases, assertions on private implementation details, and tests solely for low-impact text or formatting edits.
- Reuse existing test layout and fixtures. When no layout exists, use colocated `*.test.ts` / `*.test.tsx` frontend files and `tests/` under the relevant Python component with `test_*.py` names. Keep only fixtures needed by actual cases.
- Isolate database access, object storage, Modal calls, network access, and model inference behind mocks or small fakes at external boundaries. Exercise the real logic under test. Do not start live services, download weights, or run GPU workloads as unit tests. Identify behavior that requires integration or end-to-end verification separately.
- Use small synthetic arrays/images and deterministic seeds where relevant. Check shape, type, coordinate consistency, and expected numerical results for `masks[N, H, W]` and analysis logic. Choose tolerances from the algorithm's intended precision, not from a failing result.
- When affected, cover task state transitions, cancellation, retry/restart, stable IDs, and stale results according to the API contract. Unit tests with fakes cannot prove database constraints or live distributed behavior.
- Run tests in finite, non-watch mode using the project's configured environment. Start with the changed behavior and related existing tests. Broaden to affected consumers or component suites for shared contracts/core logic; run the full local unit suite when impact cannot be bounded. Repeat after changes or unresolved failures, not after an adequate passing check without new evidence.
- Investigate failures as product defects, incorrect tests, environment problems, or possibly pre-existing failures, and state the evidence. Correct test mistakes. Change product code only within existing repair authorization; otherwise report the defect and retain a valid failing regression test, clearly marked in the result. Never weaken assertions, skip cases, or update snapshots merely to get a pass.

## Keep tests reusable and artifacts contained

- Keep useful test source, required small fixtures, and necessary test configuration. These provide future regression protection and are not disposable artifacts.
- Prefer framework-managed temporary directories and teardown hooks. Route one-off files, logs, caches, and reports into a unique directory owned by this invocation when supported. Avoid generating coverage reports unless needed by the task or existing checks.
- Track any processes and files created by this invocation. Use teardown or `finally` to restore mocks, timers, environment changes, and working directories and to close handles even when assertions fail. Stop only processes started by this invocation; after interruption, inspect recorded resources before cleanup.
- Remove only disposable artifacts whose ownership is established. A new or untracked file is not by itself proof that it belongs to this test run. Do not remove pre-existing caches, user data, useful fixtures, or files concurrently created by others. Do not use `git clean`, reset, or broad shared-temp deletion as cleanup.
- On Windows, resolve and verify every recursive deletion target is within the intended invocation-owned directory; reject paths escaping through links or junctions. Use native PowerShell `Remove-Item -LiteralPath` without passing computed paths to another shell. If ownership or containment is uncertain, leave the item and report its path and reason.
- Compare the final diff and artifact inventory with the initial state. Ensure only intentional test/setup changes and separately authorized fixes remain. Do not silently revert unexpected user-file changes; report them and any incomplete cleanup.

## Report to the user

Respond in the user's language with a concise account of:

- Tested behavior and tests added or changed.
- Actual commands, working directories, and passed/failed/skipped counts when available; distinguish checks that could not run and zero collected tests from a pass.
- Failures with locations, evidence, and whether a product fix was authorized and made.
- Useful files retained, temporary resources cleaned, and any remaining artifacts or verification gaps.

Do not create a separate report file unless requested. When no code or runnable environment exists, explain the concrete next prerequisite instead of claiming verification.
