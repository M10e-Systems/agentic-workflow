---
name: workflow-runner
description: >-
  Run or resume the accelerated agentic engineering workflow in this
  repository using canonical artifact state, explicit agent roles, and human
  gates. Use for requirements intake, ticket drafting, implementation, test
  review, integration preparation, unit validation, or optional external-ticket
  intake and bounded in-work claims.
---

# Workflow Runner

Run one workflow step at a time, preserve auditability in `artifacts/`, and
avoid unauthorized external writes.

## Workspace and Authority

Resolve `WORKFLOW_ROOT` to the workflow repository, `PROJECT_ROOT` to the parent
of the workflow and code repositories, and `CODE_ROOT` to each code repository
in scope. Require `PROJECT_ROOT` at intake; all workflow and code roots must be
direct children. Resolve `RULES_ROOT` using the repository runbook. All paths
starting with `artifacts/` below are relative to `PROJECT_ROOT`, never the skill
installation or workflow repository. Tool and template paths are relative to
`WORKFLOW_ROOT`.

Read `WORKFLOW_ROOT/AGENTS.md`, `RULES_ROOT/WORKFLOW.md`,
`RULES_ROOT/POLICY.md`,
`RULES_ROOT/TESTING.md`, `RULES_ROOT/CONTRACTS.md`, and
`WORKFLOW_ROOT/docs/workflow_state_spec.md`. These govern execution; this skill
must not override them. Use existing repository templates and tooling.

## Execution Checklist

1. Require explicit role activation (`Act as <Agent>`) and a bounded action,
   except for direct work on the workflow project itself under `AGENTS.md`.
   If kickoff omits the role, request activation as `Spec Writer` before intake.
1. Read `artifacts/workflow_state.json` at step start. For a new run, the
   activated Spec Writer initializes state using the schema and specification.
   Create the artifact directory if missing; never overwrite an existing run.
1. If kickoff names a Jira issue as input, collect Jira context below. For any
   external intake ticket, apply the Stage 1 intake claim rule when authorized.
1. Determine the stage, approvals, blockers, and allowed actions from state and
   the runbook. Perform only the authorized step.
1. Write the active role's required artifacts under `artifacts/`.
1. Update state with outputs, decisions, blockers, `current`, next steps, an
   advanced `run.updated_at`, and at least one `quality.checks` entry. Record
   output paths and hashes where available. Unaccepted artifacts stay provisional.
1. From `PROJECT_ROOT`, validate state and render its derived Markdown view,
   with `WORKFLOW_ROOT` set to the resolved workflow repository:

   ```sh
   python3 "$WORKFLOW_ROOT/tools/workflow_state/validate" \
     artifacts/workflow_state.json
   python3 "$WORKFLOW_ROOT/tools/workflow_state/render" md \
     artifacts/workflow_state.json
   ```

   Resolve validation failures before claiming completion. JSON remains canonical.
1. Report the result and next required role or human gate. Stop at gates; a
   queued step or generated artifact grants no approval. Acceptance requires
   human approval and `accepted_by` / `accepted_at` metadata. Prefer the
   repository's `tools/workflow_state/approve` to record authorized approval.

## Jira Quick Start Rule

- Trigger when a request both names a Jira issue key (for example `ABC-42`) and
  asks to start workflow work from that issue.
- Use an available configured Jira connector or CLI in read-only mode before
  requirements intake. Jira tooling is optional for other runs; do not install
  tools or embed credentials in the skill.
- Collect the issue key, summary, description, and all comments, including
  authors and timestamps when returned. Retrieve every comments page.
- Normalize context into a concise local artifact at
  `artifacts/requirements/jira-intake-<ISSUE-KEY>.md` and cite it as the source
  input for Spec Writer requirements creation.
- Surface conflicts between user requirements and Jira text and ask for direction.
  Otherwise treat user clarifications as additive constraints.
- If access fails or context is incomplete, record the blocker and ask for supplied
  ticket context or access. Do not guess ticket content or advance affected work.
- Context collection is read-only. When the human also instructs Spec Writer to
  start work on the issue, the bounded intake claim below is permitted.

## External Intake Claim (Any Ticket System)

- Follow `RULES_ROOT/POLICY.md` section 4.1 during Stage 1. A human instruction
  to start Spec Writer work on an identified ticket authorizes marking that
  ticket as in work; merely mentioning it or requesting read-only intake does not.
- Use configured tooling to read the ticket state, ownership, and supported
  operations. Discover the actual in-work transition or claim mechanism from
  system metadata or explicit project configuration; never hardcode Jira status
  names/IDs or assume another system uses statuses.
- Before writing, record the proposed action and authorization source in
  `artifacts/requirements/intake-claim.md` and reference it as provisional in
  canonical state. Apply only the necessary transition/claim operation, then
  verify and record the observed outcome. An appropriate existing state is a
  no-op when there is no ownership conflict.
- Set ownership only if required by the mechanism and the intended owner is
  supplied or configured. Do not take over another owner's claim or reopen
  completed tickets. Block affected work on ambiguous mappings, permissions,
  ownership conflicts, or uncertain results; re-read before any retry.
- This does not grant ticket creation, comments, bulk actions, completion,
  acceptance, or requirements approval. Local Worker ticket selection is separate.

## Role Operating Rules

### Spec Writer

- Produce `artifacts/requirements/requirements.md` from template.
- Include goals, non-goals, constraints, acceptance criteria, and unit-level
  validation expectations.
- Record the fixed `artifacts/` location in the requirements artifact.
- When quick-starting from Jira, cite
  `artifacts/requirements/jira-intake-<ISSUE-KEY>.md` as an input source.
- Do not approve requirements or mutate external services beyond the authorized
  Stage 1 intake claim.

### Ticket Writer

- Produce `artifacts/tickets/tickets.yaml`.
- Ensure each ticket covers exactly one deliverable.
- Include `priority`, `blocked_by`, acceptance criteria, and a negative-case
  unit test plan. Require `code_root` and executable `unit_test_commands` for
  Ready.
- Claim no external transitions or bulk updates without explicit authority.

### Worker

- Select first eligible ticket in `artifacts/tickets/tickets.yaml`
  (top-to-bottom, Ready, unblocked, unclaimed).
- Set ticket to `In Progress` with `claimed_by` and `claimed_at`.
- Start output with a run header containing `Ticket ID`, `Branch ID`, `Scope`,
  and `Dependencies`.
- Implement code and unit tests.
- Write `artifacts/work/<TICKET-ID>/notes.md` with assumptions, tested boundary,
  negative cases, and simulator/stub usage.
- Keep assumptions conservative (max 2 non-material assumptions); escalate
  correctness-impacting gaps.

### Test Steward

- Review for behavior-first tests at a clear interface boundary.
- Enforce meaningful negative cases and anti-trivial assertions.
- Treat simulator/stub edits as contract changes requiring gate review.
- Reject new `#ifdef SIMULATION` outside quarantine.
- Record the review in `artifacts/work/<TICKET-ID>/notes.md`; do not edit
  code/tests
  or mark tickets `Accepted` (human-only under this repository's rules).

### Integrator

- Produce `artifacts/integration/merge-summary.md`.
- Record unaccepted integration artifacts as provisional, not authoritative.
- Do not merge or override ownership without explicit handoff.

### Validator

- Produce `artifacts/validation/validation-report.md`.
- Run ticket-declared `unit_test_commands` and report commands, environment,
  results,
  omissions, testing posture, negative coverage, simulator/stub changes and
  approval
  state, quarantine check result, and a critical-test failure sanity check.
- Claim only unit-level evidence.

## Ticket Selection Rule

Select the first ticket in `artifacts/tickets/tickets.yaml` that is:

- `status: Ready`
- unblocked (`blocked_by` empty or only tickets with `status: Accepted`)
- unclaimed

If no eligible ticket exists, report that and stop.

## External Write Safety

- Treat external service writes as impactful, including issue trackers and Git
  hosts.
- Prepare proposed actions in local artifacts before any external write.
- Apply writes only when workflow stage authority and human gate approval exist.
  For the bounded Stage 1 intake claim, an instruction to start Spec Writer work
  on the identified ticket supplies both under POLICY.md section 4.1.
- Permit Jira reads for quick-start intake through configured tooling; record
  the
  retrieved source context locally for auditability.
- Default to read-only if authority is unclear.

## Escalation Triggers

Stop and ask for direction when:

- Requirements are ambiguous or conflicting.
- Acceptance criteria are not unit-testable.
- Interface boundaries are unclear.
- Simulator/stub updates are needed to make tests pass.
- Authority for destructive or bulk actions is not explicit.
- Jira quick-start intake cannot retrieve complete ticket context.
