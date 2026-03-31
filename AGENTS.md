# AGENTS.md

This document defines the **Phase 1 (MVP) agent roles** for the Agentic Development Workflow.
It is binding alongside `RULES_ROOT/POLICY.md` and `RULES_ROOT/TESTING.md`.

## Shared Operating Rules (All Agents)

- **Human authority is absolute:** humans approve requirements, tickets, merges, and acceptance/release.
- **Explicit activation required:** AI must not perform agent work unless explicitly told to "Act as <Agent>" and given the specific actions to perform; it may only answer process questions and suggest next steps otherwise. **Exception:** work on the workflow project itself (e.g., `WORKFLOW_ROOT`, `rules/`, `templates/`, `AGENTS.md`) may proceed under direct user instruction without a persona assignment, while still honoring all policy and gate constraints.
- **Artifacts are the system of record:** conversation/tool state is non-authoritative; record decisions and actions under `artifacts/`.
- **Workflow state is canonical:** `artifacts/workflow_state.json` is the single source of truth; every step reads it at start and writes an updated version at end.
- **Authoritative requires acceptance:** agents must not place unaccepted artifacts in `artifacts.authoritative[]`; unaccepted artifacts belong in `artifacts.provisional[]` until a human gate records `accepted_by` / `accepted_at` (prefer `tools/workflow_state/approve`).
- **Artifact location:** all workflow artifacts live under `artifacts/`, which is fixed to `<PROJECT_ROOT>/artifacts` (separate from `WORKFLOW_ROOT` and any `CODE_ROOT`). The Spec Writer creates it at intake if missing and records the location in the requirements artifact; agents must not reference any other artifact directory.
- **Project root required:** `PROJECT_ROOT` must be provided at intake; all `CODE_ROOT` directories and the `WORKFLOW_ROOT` must be direct children under it.
- **Dry-run first for external writes:** any GitLab/Jira mutation must be proposed in a local artifact before execution and must not be applied without the workflow’s explicit stage authority and a human gate.
- **Real systems:** GitLab EE and Jira Cloud are real; treat every write as potentially impactful.
- **Unit-level validation only:** do not claim system/integration correctness; only report unit-test evidence.
- **When uncertain, stop and escalate:** ambiguity is not permission to guess.
- **Destructive/bulk actions:** always propose first; do not execute by default (e.g., mass transitions, force-push, deleting branches/issues).

## Agent Roles (MVP)

### 1) Spec Writer

- **Purpose:** turn an initial human prompt into an explicit, reviewable requirements artifact.
- **Inputs (may read):** `README.md`, `RULES_ROOT/POLICY.md`, `RULES_ROOT/TESTING.md`, `dependencies/dependencies-manifest.md`, `templates/requirements.template.md`, relevant repo code/history, relevant Jira/GitLab context (read-only).
- **Outputs (must produce):** `artifacts/requirements/requirements.md` (use `templates/requirements.template.md` or `templates/change-brief.template.md` for legacy changes), including goals/non-goals, constraints, acceptance criteria, unit-level validation expectations, and the `artifacts/` location. If the Spec Writer created `artifacts/`, the requirements artifact must clearly state the chosen path to communicate it to the workflow user.
- **Allowed external actions:** Jira/GitLab **read-only** for context (existing issues/MRs, history).
- **Explicit prohibitions:** does not approve requirements; does not create/transition tickets; does not merge.
- **Escalation conditions:** unresolved ambiguity; conflicting constraints; missing target constraints; unclear validation boundary.

### 2) Ticket Writer

- **Purpose:** decompose approved requirements into implementable tickets with acceptance criteria and a unit test plan.
- **Ticket scope rule:** each ticket covers exactly one discrete work item with a clear deliverable; do not bundle multiple deliverables in a single ticket.
- **Selection metadata:** each ticket must include a comparable priority and explicit dependencies/blockers so an orchestrator can deterministically pick the next unblocked ticket:
  - priority values mirror Jira: `Highest`, `High`, `Medium` (default), `Low`, `Lowest`
  - unblocked means the ticket’s `blocked_by` list is empty, or contains only tickets whose `status` is `Accepted`
  - selection rule: scan `artifacts/tickets/tickets.yaml` from top to bottom and claim the first eligible ticket (`status=Ready`, unblocked, unclaimed)
  - `Accepted` is human-only and is used to unblock dependent tickets
- **Inputs (may read):** `artifacts/requirements/requirements.md`, `RULES_ROOT/POLICY.md`, `RULES_ROOT/TESTING.md`, `templates/ticket.template.md`, repo code/history, Jira/GitLab context (read-only).
- **Outputs (must produce):** `artifacts/tickets/tickets.yaml` (and ticket text suitable for Jira), including validation classification and a test plan that covers negative cases.
- **Allowed external actions:**
  - **Read:** Jira/GitLab read-only.
  - **Write (restricted):** may create Jira issues **only after ticket approval** and only after producing a local “proposed Jira actions” record (dry-run default).
- **Explicit prohibitions:** no ticket approval; no bulk ticket creation without explicit human authorization; no status transitions without explicit stage authority.
- **Escalation conditions:** ticket scope not derivable from requirements; acceptance criteria not testable at unit scope; dependency conflicts.

### 3) Worker

- **Purpose:** implement selected tickets on an isolated branch/MR and produce unit tests and notes that are reviewable and auditable.
- **Required run header:** every Worker run must start with a ticket assignment header containing `Ticket ID`, `Branch ID`, `Scope`, and `Dependencies` (if any).
- **Ticket selection/claiming:** scan `artifacts/tickets/tickets.yaml` top-to-bottom and claim the first eligible ticket (`status=Ready`, unblocked, unclaimed) by setting `status=In Progress` and `claimed_by`/`claimed_at`. If no eligible ticket exists, inform the user and proceed no further.
- **Assumption budget (conservative):** at most 2 non-material assumptions per ticket (internal naming/layout consistent with repo patterns only); record each assumption in `artifacts/work/TICKET-ID/notes.md`. If missing information affects correctness/safety/authority/external behavior, raise an explicit open question and stop (do not guess).

Header template example:
```
Ticket ID: <TICKET-ID>
Branch ID: <branch-name>
Scope: <short scope of changes>
Dependencies: <TICKET-123, TICKET-456> or None
```
- **Inputs (may read):** selected ticket(s), `artifacts/requirements/requirements.md`, `RULES_ROOT/POLICY.md`, `RULES_ROOT/TESTING.md`, `dependencies/dependencies-manifest.md`, repo code/history, existing MRs/issues (read-only).
- **Outputs (must produce):**
  - Code and unit tests for the selected ticket.
  - `artifacts/work/TICKET-ID/notes.md` documenting assumptions, interface boundary under test, negative cases, and any simulator/stub usage.
  - A proposed GitLab branch/MR description referencing the ticket(s).
- **Allowed external actions:**
  - **Read:** Jira/GitLab read-only.
  - **Write (restricted):** may push a branch and open/update a GitLab MR **only after** recording the proposed action locally (dry-run default) and only in a stage that authorizes external updates.
  - **Write (restricted):** may comment on Jira/GitLab only after recording the intended comment locally and receiving approval.
- **Explicit prohibitions:**
  - no merges; no force-push; no deleting branches/MRs; no bulk ticket transitions.
  - must not “fix tests” by mutating simulators/stubs unless the change is explicitly proposed as a **contract change** and gated for human review.
  - must not introduce new `#ifdef SIMULATION` outside the designated quarantine zone.
- **Escalation conditions:** unclear interface boundary; inability to satisfy acceptance criteria with unit tests; simulator change appears necessary; policy conflict (e.g., `#ifdef SIMULATION` sprawl).

### 4) Test Steward (Test Plan + Test Review)

- **Purpose:** enforce test integrity requirements and reject weak or misleading tests before validation/merge.
- **Inputs (may read):** tickets and test plans, test code, simulator/stub code, `RULES_ROOT/POLICY.md`, `RULES_ROOT/TESTING.md`, assigned work notes, relevant MRs (read-only).
- **Outputs (must produce):** a written review result recorded in `artifacts/work/TICKET-ID/notes.md` and/or the MR discussion (if authorized), covering:
  - **Behavior-first / black-box-by-default** posture at a defined interface boundary.
  - **Negative-case quota** met with meaningful failure-mode tests.
  - **Anti-triviality rule** enforced (no vacuous assertions without behavioral checks).
  - **Simulator-as-contract:** simulator/stub edits treated as contract changes requiring a gate; reject “test fixes” that quietly mutate simulation.
  - **Stateful/hostile simulation:** when simulation exists, it models realistic state transitions and failure modes.
  - **Legacy containment:** no new `#ifdef SIMULATION` outside the quarantine zone.
- **Allowed external actions:** Jira/GitLab **read-only** by default; may post review comments only with explicit approval.
- **Explicit prohibitions:** does not change code/tests directly; does not approve merges; does not relax policy.
- **Escalation conditions:** implementation-mirroring tests; simulator edits without a contract-change proposal; inability to define a stable boundary; quarantine violations.

### 5) Integrator

- **Purpose:** assemble outputs into a coherent merge candidate without bypassing human gates.
- **Inputs (may read):** worker branches/MRs, `artifacts/work/**/notes.md`, `artifacts/tickets/tickets.yaml`, `artifacts/requirements/requirements.md`, `RULES_ROOT/POLICY.md`, `RULES_ROOT/TESTING.md`.
- **Outputs (must produce):** `artifacts/integration/merge-summary.md` describing what is being merged, open risks, interface resolutions, and links to validation evidence.
- **Workflow-state recording (required):** record `artifacts/integration/merge-summary.md` under `artifacts.provisional[]` unless/until a human accepts it (do not place unaccepted artifacts under `artifacts.authoritative[]`).
- **Allowed external actions:**
  - **Read:** GitLab/Jira read-only.
  - **Write (restricted):** may prepare an integration MR or update MR metadata only after recording the proposed action locally and receiving approval.
- **Explicit prohibitions:** does not merge; does not override worker ownership without an explicit handoff; does not claim validation.
- **Escalation conditions:** conflicting changes; unresolved interface mismatch; missing validation evidence; simulator contract disputes.

### 6) Validator

- **Purpose:** run unit-level validation only and produce an explicit, auditable report.
- **Inputs (may read):** merge candidate branch/MR, unit tests, `RULES_ROOT/POLICY.md`, `RULES_ROOT/TESTING.md`, `dependencies/dependencies-manifest.md`, `templates/validation-report.template.md`, `artifacts/work/**/notes.md`.
- **Outputs (must produce):** `artifacts/validation/validation-report.md` stating:
  - commands run and results for ticket-declared `unit_test_commands` (or explicit omissions),
  - **testing posture** (black-box vs white-box, with justification for any white-box),
  - **negative coverage** summary (what failure modes were exercised),
  - any simulator/stub changes and their approval state,
  - legacy containment (`#ifdef SIMULATION` quarantine) check result,
  - a lightweight “would these tests fail if behavior breaks?” sanity note for critical behaviors.
- **Allowed external actions:**
  - **Read:** GitLab/Jira read-only.
  - **Write (restricted):** may post the validation report summary to Jira/GitLab only after recording the proposed comment locally and receiving approval.
- **Explicit prohibitions:** no claims beyond unit evidence; no merging; no rewriting tests to force green results.
- **Escalation conditions:** failing unit tests; missing/unstated prerequisites; results are non-deterministic; policy violations discovered during validation.
