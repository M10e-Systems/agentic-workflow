# Workflow State

## Run
- Run ID: example-2025-01-15-001
- Status: blocked
- Updated At: 2025-01-15T10:30:00Z

## Current
- Phase: stage-2
- Stage: ticket-drafting
- Step: draft tickets
- Objective: Produce tickets.yaml from approved requirements

## Blockers
- oq-1: Confirm target OS/kernel constraints for this change. (owner: Project Sponsor <sponsor@example.com>)

## Next Step
- id: resolve-oq-1 | agent: human | inputs: ['artifacts/requirements/requirements.md'] | outputs: ['artifacts/workflow_state.json']

## Last Accepted Authoritative Artifact
- id: requirements-001 | type: requirements | path: artifacts/requirements/requirements.md | accepted_at: 2025-01-15T10:20:00Z | accepted_by: Project Sponsor <sponsor@example.com>

## Quality
### Checks (fail/warn)
- id: ticket-draft-ready | status: warn | notes: Ticket drafting paused due to missing target constraints.
### Risks
- id: risk-1 | risk: Target constraints unknown; ticket scope may be invalid. | mitigation: Resolve oq-1 before drafting tickets.

## Notes for Humans
- Awaiting target OS/kernel constraints to proceed.
