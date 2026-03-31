# Ticket Template

Workflow state update required: update `artifacts/workflow_state.json` with this artifact, any blockers, and a quality check entry.

Ticket scope rule: this ticket must represent exactly one discrete work item with a clear deliverable.

## Summary
<one sentence>

## Priority
<One of: Highest, High, Medium, Low, Lowest. Default: Medium>

## Status
<One of: Draft, Ready, In Progress, Done, Accepted. Default: Draft>

## CODE_ROOT
<repo name/path from CODE_ROOTS (or explicit path); required to move to Ready>

## Unit Test Commands
<commands to run from CODE_ROOT that prove acceptance criteria; required to move to Ready>

## Background / Context
<link to requirement + relevant context>

## Scope
- In scope:
- Out of scope:

## Acceptance Criteria
- <testable criterion 1>
- <testable criterion 2>

## Dependencies
- Blocks:
- Blocked by: <ticket IDs; “unblocked” means empty, or contains only tickets whose status is Accepted>

## Validation Classification
- Unit-only: Yes
- Environment: dev / target / simulated (pick one; explain if not dev)
- Evidence required: (logs, report links)

## Unit Test Plan (Required)
- Boundary under test: <CLI/API/messages/files/logs/exit codes>
- Per language/component: <framework/tooling> — <what to add/modify?> (include meaningful negative cases)
- If introducing a new primary language/toolchain or changing the unit-test framework, link to the Stage 1 requirements approval and ensure `dependencies/dependencies-manifest.md` is updated.
- If “none”, justify explicitly.

## Implementation Notes
- Constraints (perf, compatibility, kernel/hw):
- Assumptions:
