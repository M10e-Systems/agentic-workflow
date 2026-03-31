# Requirements Template

This template is appropriate for **new software / greenfield components** and for larger feature work where a fuller requirements write-up is helpful.

For **legacy/existing software**, prefer `templates/change-brief.template.md` to avoid creating a piecemeal, misleading “partial spec” of the whole system. If you use this template for legacy work, keep it explicitly **change-scoped** and include “Non-Goals” that state what you are *not* attempting to specify.

Workflow state update required: update `artifacts/workflow_state.json` with this artifact, any blockers, and a quality check entry.

## Title
<short, descriptive title>

## Artifact Root (ARTIFACT_ROOT)
<path to the artifact root (must be <PROJECT_ROOT>/artifacts); state that it was created at intake if it did not exist>

## Problem Statement
<what is wrong / missing today?>

## Context / Existing Behavior (Optional; Recommended for Legacy)
<what the system does today, as observed at the boundary, and what must not change>

## Goals
- <goal 1>
- <goal 2>

## Non-Goals
- <explicit non-goal 1>
- <explicit non-goal 2>

## Constraints

### Operational Constraints
- Air-gapped deployment targets may exist (deployment), but unit testing/CI is not air-gapped.
- Public dependencies are allowed for testing only if compatible with the project's cached runtime practices.

### Target Constraints (if applicable)
- Target OS / distro:
- Kernel version constraints:
- Required modules/drivers:
- Hardware dependencies:
- Privilege/capability requirements:
- Performance expectations (if applicable):

## Acceptance Criteria
- <criterion 1>
- <criterion 2>

## Validation Plan (Unit-Level Only)
- Boundary under test: <CLI/API/messages/files/logs/exit codes>
- Languages/toolchains in scope: <list>
- Unit test framework(s): <list> (defaults when applicable: gtest/pytest/bats)
- Proposed unit test commands: <high-level; exact commands recorded per ticket in artifacts/tickets/tickets.yaml>
- Out of scope: system-level testing (owned elsewhere)

## Risks / Unknowns
- <risk 1>
- <unknown 1>

## Artifacts to Produce
- Requirements doc updates
- Jira tickets (generated)
- Code + unit tests
- Validation report
