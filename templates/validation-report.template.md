# Validation Report Template

Workflow state update required: update `artifacts/workflow_state.json` with this artifact, any blockers, and a quality check entry.

## Change Summary
- Jira ticket(s):
- GitLab MR(s):
- Commit(s):

## Validation Scope
- Unit-level testing only (system-level testing out of scope for this workflow)

## Environment
- Where validation ran: (local dev, CI runner, other)
- OS/distro:
- Toolchain versions:
- Notes on cached runtime / dependency sourcing:

## Commands Executed
- <CODE_ROOT>: <unit_test_command> — Result: PASS/FAIL — Notes: <notes>
- <CODE_ROOT>: <unit_test_command> — Result: PASS/FAIL — Notes: <notes>

Notes:
- Commands should come from ticket-declared `unit_test_commands` in `artifacts/tickets/tickets.yaml`.
- If a default framework (gtest/pytest/bats) is applicable, record the concrete command you executed (e.g., `ctest -V`, `pytest -q`, `bats tests/shell`).

## Optional Fast Checks
- <shellcheck/ruff/etc if run>

## What Was Not Run (and why)
- <explicit omissions>

## Evidence / Artifacts
- <paths to logs, screenshots, CI links, etc.>

## Risk Assessment
- Low/Med/High: <brief rationale>
