# Agentic Development Workflow (MVP)

## Overview

This repository contains a **prototype agentic development workflow** designed to demonstrate how AI can accelerate real software engineering work **without replacing engineering discipline, human judgment, or existing workflows**.

The system is intentionally:
- Platform-agnostic
- LLM-agnostic
- Tooling-agnostic (via adapters)
- Artifact-driven

Conversation is ephemeral. **Artifacts are the system of record.**

The MVP demonstrates an end-to-end flow:

> **Requirements → Tickets → Work → Merge → Validation**

with explicit human gates at irreversible decision points.

Note: this `README.md` uses a compressed stage view for readability; `rules/WORKFLOW.md` is the authoritative runbook (with the detailed stage numbering and required step outputs).

---

## Why This Exists

For organizations which develop software that must run in:
- **air-gapped environments**
- **embedded or hardware-adjacent systems**
- **kernels and drivers that differ from development machines**

Traditional “AI coding demos” ignore these realities. This workflow encodes them.

This workflow focuses on:
- faster execution of well-specified work
- reduced rework caused by unclear requirements
- clear sequencing without chaos
- improved maintainability over time

---

## Design Principles

- **Humans own intent**
- **AI executes bounded work**
- **Artifacts, not chat logs, carry state**
- **Existing Git workflows are respected**
- **Autonomy is earned, not assumed**
- **Systems stay agnostic, demos stay impactful** (defaults matter)

---

## Workflow State (Canonical)

`artifacts/workflow_state.json` is the **single source of truth** for workflow state.
Every agent step must:

- Read `artifacts/workflow_state.json` at step start.
- Write an updated `artifacts/workflow_state.json` at step end.
- Reference every produced artifact by path (and hash when available).
- Record blockers and unknowns explicitly (no guessing).
- Update at least one `quality.checks` entry.

Views are derived outputs generated from JSON and are non-authoritative.

### Tooling

Validate and render views using the minimal-dependency tools:

```
<WORKFLOW_ROOT>/tools/workflow_state/validate artifacts/workflow_state.json
<WORKFLOW_ROOT>/tools/workflow_state/render md artifacts/workflow_state.json
```

The Markdown view is written to `artifacts/workflow_state.md`.
See `docs/workflow_state_spec.md` and `docs/workflow_state_schema.json` for rules and schema.

### CI Enforcement (Required)

CI must fail if validation fails or if the rendered Markdown diverges from JSON:

```
<WORKFLOW_ROOT>/tools/workflow_state/validate artifacts/workflow_state.json
<WORKFLOW_ROOT>/tools/workflow_state/render md artifacts/workflow_state.json
git diff --exit-code artifacts/workflow_state.md
```

---

## Codex Workflow Runner Skill

The portable [workflow-runner skill](skills/workflow-runner/SKILL.md) runs the
accelerated agentic engineering workflow using this repository's roles, artifacts,
and human gates. It includes optional read-only Jira intake through a configured
connector or CLI. Jira access is unnecessary for requirements supplied directly.

To install, copy `skills/workflow-runner/` into your Codex skills directory
(`$CODEX_HOME/skills`, or `~/.codex/skills` when unset). Review any existing
installation before replacing it. Keep this repository available: the skill uses
its rules, templates, schema, and state tools.

Provide `PROJECT_ROOT`, `WORKFLOW_ROOT`, and the applicable `CODE_ROOT` directories
with your request. Workflow and code repositories must be direct children of
`PROJECT_ROOT`; artifacts live at `PROJECT_ROOT/artifacts`. You may specify
`RULES_ROOT` explicitly; otherwise use the runbook's resolution order.

Example request after providing those roots:

> Use $workflow-runner. Act as Spec Writer and draft requirements for the change
> described below. Stop at the requirements approval gate.

For Jira intake, name an issue you can access and explicitly request starting
from it. The skill reads its summary, description, and all comments before
drafting requirements. Later roles also require explicit activation.

The [skill contract](docs/workflow_runner_skill.md) defines portability and
acceptance criteria. Run `make test` to check the existing workflow-state tools;
the suite uses Python's standard library and requires no dependency downloads.

---

## Tooling Strategy: Agnostic Core, Real Integrations

The workflow is **tooling-agnostic by design**, but the MVP demo should be run against real systems to maximize impact.

### Default MVP Integrations
- **VCS:** GitLab EE (projects, branches, merge requests)
- **Ticketing/Planning:** Atlassian Jira Cloud (issues, epics, status transitions)

### Integration Mechanism
Use published **Model Context Protocol (MCP)** servers as the connector layer where available:
- GitLab MCP server for GitLab instance access (projects, issues/MRs, etc.)
- Atlassian MCP server for Jira Cloud access (issues, transitions, etc.)

The agnostic core must not depend on MCP specifically; MCP is the default adapter for the MVP.

---

## Testing and Validation Scope (Important)

Any **system level** testing performed externally to the software organization is **out of scope** for this effort.

This workflow standardizes **unit-level validation** and fast checks only.

### Validation Interface (Required)
- Validation evidence is based on explicit unit-test commands recorded per ticket (`unit_test_commands` in `artifacts/tickets/tickets.yaml`) and repeated in `artifacts/validation/validation-report.md`.
- The workflow is implementation-language-agnostic; languages/toolchains are permitted when they can meet `RULES_ROOT/TESTING.md`.

### Default Frameworks (Recommended; Required When Applicable)
- **C++:** GoogleTest (gtest)
- **Python:** `pytest`
- **Shell:** `bats` (bats-core)

### Network / Caching Constraint
Unit testing is **not performed in air-gapped environments**. The workflow may use publicly available tooling and dependencies **provided they operate within the project’s cached runtime constraints** (e.g., pinned versions, internal cache/mirror behavior, or pre-baked build images).

See: `RULES_ROOT/TESTING.md` and `dependencies/dependencies-manifest.md`.

---

## Repository Structure (MVP)

This workflow uses an artifact-first layout. Workflow artifacts live in a **dedicated `ARTIFACT_ROOT`** that is **outside** both the workflow documentation directory (`WORKFLOW_ROOT`) and any code directory (`CODE_ROOT`), and is **fixed** to live under the project root.
When connected to Jira/GitLab, these artifacts are still created locally as the **auditable record** of what the agents did and why.

### Rules Location (RULES_ROOT)

Rule documents (`WORKFLOW.md`, `POLICY.md`, `TESTING.md`, `CONTRACTS.md`) are resolved from `RULES_ROOT`.
Prefer providing `RULES_ROOT` explicitly in prompts. Continue CLI searches:
1) `WORKFLOW_ROOT/.continue/rules`
2) `$HOME/.continue/rules`
3) Framework-agnostic fallback: `WORKFLOW_ROOT/rules`

### Project Root and Artifact Root (PROJECT_ROOT / ARTIFACT_ROOT)

`PROJECT_ROOT` is the parent directory that contains all `CODE_ROOT` directories, the `WORKFLOW_ROOT`, and the fixed `ARTIFACT_ROOT`.
`ARTIFACT_ROOT` is a separate directory that contains **only workflow artifacts** (requirements, tickets, work notes, integration summaries, validation reports).

Policy (no overrides):
- `ARTIFACT_ROOT` is always `<PROJECT_ROOT>/artifacts`.
- The Spec Writer creates `<PROJECT_ROOT>/artifacts` at intake if missing and records the location in `artifacts/requirements/requirements.md`.
- Agents must not reference or write to any other artifact directory.
- All `CODE_ROOT` directories and the `WORKFLOW_ROOT` must be direct children of `PROJECT_ROOT`.

### Core Docs

- `WORKFLOW_ROOT/AGENTS.md` (roles, activation rules, prohibitions)
- `RULES_ROOT/WORKFLOW.md` (runbook and stage definitions)
- `RULES_ROOT/POLICY.md` (authority and governance)
- `RULES_ROOT/TESTING.md` (unit-level test standards)
- `RULES_ROOT/CONTRACTS.md` (non-negotiable invariants)

```
<project-root>/
├── <CODE_ROOT_1>/
├── <CODE_ROOT_2>/
├── <WORKFLOW_ROOT>/         # workflow docs (this repo)
│   ├── README.md
│   ├── templates/
│   ├── rules/
│   └── dependencies/
└── artifacts/               # ARTIFACT_ROOT (fixed location)
    ├── requirements/
    │   └── requirements.md
    ├── tickets/
    │   └── tickets.yaml
    ├── work/
    │   └── TICKET-ID/
    │       ├── implementation/
    │       ├── tests/
    │       └── notes.md
    ├── integration/
    │   └── merge-summary.md
    └── validation/
        └── validation-report.md
```

---

## Phase 1: MVP Workflow

### Purpose

Demonstrate that:
- AI can execute **non-trivial engineering tasks** within defined boundaries
- total elapsed time is reduced vs serial execution
- outputs are reviewable, mergeable, and auditable
- air-gapped and target constraints are explicitly respected where relevant
- Jira + GitLab integration produces a management-grade demo
- unit testing and validation are standardized across C++, Python, and shell

---

### Workflow Stages

#### 1. Requirements (Human-Led, AI-Assisted)

- A human provides an initial requirement (often incomplete).
- The **Spec Writer (AI)** interrogates the requirement:
  - identifies ambiguity
  - surfaces missing constraints
  - calls out target kernel/hardware implications when relevant
- The Spec Writer ensures `<PROJECT_ROOT>/artifacts` exists (creates it if missing) and records the location in the requirements artifact.
- Output: `artifacts/requirements/requirements.md`

In Phase 1, “requirements” means a **written intent artifact for a discrete slice of work**:
- For **new software / greenfield components**, write fuller requirements.
- For **existing/legacy software**, the artifact may be a **Change Brief** that documents only the intended delta and the observable acceptance criteria (it should not pretend to backfill a coherent full-system spec).

The Stage 1 artifact must explicitly state:
- functional goals
- non-goals
- target OS/kernel/hardware constraints (when applicable)
- acceptable validation scope (dev / target / simulated)
- unit-test expectations (what must be unit-testable vs what cannot)
- `ARTIFACT_ROOT` location (fixed to `<PROJECT_ROOT>/artifacts`)

Templates: `templates/requirements.template.md` (fuller) or `templates/change-brief.template.md` (legacy).

---

#### 2. Ticket Generation (AI → Jira + Local Artifact)

- Approved requirements are decomposed into tickets.
- Each ticket has:
  - clear scope
  - priority (one of: Highest, High, Medium (default), Low, Lowest)
  - code root + unit test commands (required for Ready)
  - acceptance criteria
  - dependency annotations
  - validation classification (unit-only; dev/target/sim scope)
  - a unit test plan
  - status (`Accepted` is human-only; used to unblock dependents)

Outputs:
- Local: `artifacts/tickets/tickets.yaml`
- Optional (MVP default): Create corresponding Jira issues

Template: `templates/ticket.template.md`.

---

#### 3. Work (AI Worker Runs → GitLab Branches/MRs + Local Artifacts)

- Worker runs can operate concurrently.
- Each worker run:
  - sees only selected ticket(s) + required context
  - produces code, unit tests, and notes
  - declares assumptions and limitations
- Selection Rule: scan `artifacts/tickets/tickets.yaml` from top to bottom and claim the first eligible ticket (`status=Ready`, unblocked, unclaimed).
- Each worker run begins with a ticket assignment header (Ticket ID, Branch ID, Scope, Dependencies).
- Workers do **not** merge directly.

Outputs:
- Local: `artifacts/work/TICKET-ID/`
- Optional (MVP default): each worker creates a GitLab branch and opens/updates a Merge Request referencing the Jira ticket(s)

---

#### 4. Integration

- Outputs from worker runs are assembled.
- Interface mismatches are resolved.
- A merge candidate is prepared.

Output:
- `artifacts/integration/merge-summary.md`

Integration may be performed via:
- a human integrator, or
- an AI integrator that prepares a final MR (merge still gated)

---

#### 5. Validation (AI)

Validator runs **unit-level validation only** and produces an explicit report.

Required:
- Run unit tests by executing the ticket-declared `unit_test_commands` (or explicitly justify omissions).

Output:
- `artifacts/validation/validation-report.md` (template: `templates/validation-report.template.md`)

Optional (MVP default): validation results are posted back to the Jira ticket(s) and/or GitLab MR as a comment.

---

#### 6. Merge (Human, GitLab)

- A human reviews:
  - the diff / MR(s)
  - the merge summary
  - the validation report
- Merge authority remains human-controlled in the MVP.

---

## Gates (Non-Negotiable)

The workflow enforces explicit human approval at:

1. Requirement approval  
2. Ticket approval  
3. Merge approval  
4. Acceptance / release approval  

AI may prepare artifacts and propose actions, but may not cross gates by default.

---

## Phase 2: Planned Evolution (Not in MVP)

Phase 2 builds on demonstrated reliability and introduces:

- greater agent specialization (architecture, testing, hardware, release)
- expanded capacity (additional agent roles)
- semi-autonomous orchestration and retries
- AI-assisted merge and release (opt-in)
- continuous maintenance and refactoring loops

Autonomy increases gradually and is always auditable.

---

## What This Is — and Is Not

This is **not**:
- an AI replacing engineers
- a new Git workflow
- a bet on a specific LLM or toolchain

This **is**:
- a disciplined engineering loop
- a way to turn clarity into speed
- a foundation for future autonomy without operational risk

---

## Success Criteria for the MVP

The MVP is considered successful if:
- AI completes meaningful work within defined gates
- elapsed time is reduced vs serial execution
- artifacts are understandable and reviewable
- existing Git practices are unchanged
- unit testing is standardized and enforced by the Validator via ticket-declared `unit_test_commands` (with sensible defaults for common languages)
- Jira tickets and GitLab merge requests provide an executive-visible trail of progress

---

## Status

This repository currently focuses on **Phase 1 (MVP)**.  
Phase 2 is intentionally deferred until trust is earned.
