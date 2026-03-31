# Change Brief Template (Legacy / Existing Software)

Use this template when changing **existing software** where backfilling comprehensive product requirements would be misleading or counterproductive.

This is still a “requirements” artifact for workflow purposes, but it is explicitly **change-scoped**: it documents the intended *delta* and the behavior that must be true at the chosen interface boundary.

Workflow state update required: update `artifacts/workflow_state.json` with this artifact, any blockers, and a quality check entry.

## Title
<short, descriptive title>

## Context (What Exists Today)
- <what the system does today, as observed at the boundary>
- <any relevant invariants to preserve>

## Change Summary (What Will Be Different)
- <one or two bullets describing the delta>

## In Scope
- <what is changing>

## Out of Scope (Non-Goals)
- <explicit non-goal: e.g., “This does not attempt to specify the entire system.”>
- <anything adjacent that is intentionally not being changed>

## Constraints
- Target OS / distro (if relevant):
- Kernel / driver constraints (if relevant):
- Hardware dependencies (if relevant):
- Privilege/capability requirements (if relevant):
- Performance expectations (if relevant):

## Acceptance Criteria (Behavior at the Boundary)
- <observable behavior or outputs; avoid internal implementation detail>
- <include at least one negative/failure-mode criterion where relevant>

## Validation Plan (Unit-Level Only)
- Boundary under test:
- Test posture: black-box by default; list any white-box and why:
- Negative cases to cover:
- Simulator/stub usage (if any) and state/failure transitions exercised:

## Risks / Unknowns
- <risk 1>
- <unknown 1>
