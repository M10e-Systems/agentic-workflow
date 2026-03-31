---
name: WORKFLOW.md
title: Agentic Development Workflow Runbook (MVP)
description: This is the Phase 1 (MVP) operational runbook for the Agentic Development Workflow, defining stages, roles, and artifact management.
version: 0.1.0
---
# WORKFLOW.md

This is the **Phase 1 (MVP) operational runbook** for the Agentic Development Workflow.
It is binding alongside `RULES_ROOT/POLICY.md`, `RULES_ROOT/TESTING.md`, and the repository’s artifact layout described in `README.md`.

## Non-Negotiables (Phase 1)

- **Humans approve:** requirements, tickets, merges, acceptance/release.
- **Artifacts are authoritative:** local artifacts are the auditable record; tool state is secondary.
- **Workflow state is canonical:** `artifacts/workflow_state.json` is the single source of truth; every step reads it at start and writes an updated version at end.
- **Acceptance metadata is required:** agents must not place unaccepted artifacts in `artifacts.authoritative[]`; only human approval (prefer `tools/workflow_state/approve`) may promote artifacts from `artifacts.provisional[]` → `artifacts.authoritative[]` with `accepted_by` / `accepted_at`.
- **External writes are gated:** Jira/GitLab writes are **dry-run by default** and applied only under an explicitly authorized stage with human approval.
- **Validation is unit-level only:** evidence via ticket-declared `unit_test_commands`; no system or integration testing. Default frameworks apply when relevant (gtest/pytest/bats), but the workflow permits other languages/toolchains when `RULES_ROOT/TESTING.md` requirements are met.
- **When uncertain:** stop and escalate; do not guess.

## Terminology: “Requirements” vs “Change Intent”

For Phase 1, “requirements” means a **written intent artifact for a discrete slice of work**, not a heavyweight, exhaustive product spec.

- For **new software / greenfield components**, prefer a fuller requirements write-up (goals, non-goals, constraints, acceptance criteria).
- For **existing/legacy software**, the Stage 1 artifact may be a **Change Brief**: document the *delta* you intend to make and the observable acceptance criteria at the chosen boundary, without attempting to backfill the entire system’s requirements.

## Workspace Roots (Project, Workflow, Artifacts, Code)

This workflow is **artifact-first**. Every stage must make it explicit which directory is the “system of record” for artifacts, and which directory contains the code being changed.

### Definitions

- **`PROJECT_ROOT`**: the parent directory that contains all `CODE_ROOT` directories, the `WORKFLOW_ROOT`, and the fixed `ARTIFACT_ROOT`.
- **`WORKFLOW_ROOT`**: the directory that contains workflow docs (e.g., `AGENTS.md`, `templates/`, `rules/`); it must be under `PROJECT_ROOT`.
- **`ARTIFACT_ROOT`**: fixed to `<PROJECT_ROOT>/artifacts` and contains `requirements/`, `tickets/`, `work/`, `integration/`, and `validation/`.
- **`CODE_ROOT`**: the git repository root where implementation changes are made; it must be under `PROJECT_ROOT`.
- **`CODE_ROOTS[]`**: the set of `CODE_ROOT` directories in scope (one or more).

All `CODE_ROOT` directories and the `WORKFLOW_ROOT` must be direct children of `PROJECT_ROOT`.

`ARTIFACT_ROOT` is fixed to `<PROJECT_ROOT>/artifacts` (no overrides). The **Spec Writer** creates it at intake if missing and records the location in the requirements artifact so the user sees it immediately. Agents must not reference or write to any other artifact directory.

Artifacts are written to `artifacts/` only; code changes are made in the appropriate `CODE_ROOT`. Every artifact that refers to code must identify which `CODE_ROOT` it applies to (repo name + path), and should record branch and commit SHA when relevant.

### Required Local Layout

```
<project-root>/
  <CODE_ROOT_1>/
  <CODE_ROOT_2>/
  <WORKFLOW_ROOT>/  # workflow docs
  artifacts/        # ARTIFACT_ROOT (fixed)
```

## Rules Location (RULES_ROOT)

The workflow rule documents live under a dedicated rules root. Prefer setting `RULES_ROOT` explicitly when invoking agents.

Resolution order:
1) **Explicit `RULES_ROOT`** provided in the prompt/context.
2) **Continue CLI default search:** `WORKFLOW_ROOT/.continue/rules`, then `$HOME/.continue/rules`.
3) **Framework-agnostic fallback:** `WORKFLOW_ROOT/rules`.

`AGENTS.md` remains at `WORKFLOW_ROOT/AGENTS.md` unless explicitly relocated.

## How to Provide Context to Agents (Best Practice)

Agents are only as good as the context you give them. Provide context as **file pointers and explicit boundaries**, not long pasted code.

### Tooling Hygiene (Avoid “Wandering” Runs)

When an indexed/semantic code-discovery tool is available (for example an MCP-backed “code intel” server), prefer it for repo discovery/search over repeated filesystem traversals.

- **Such tools help, but do not enforce:** they don’t prevent the model from running `find`/`rg` repeatedly; they just make those scans unnecessary when used.
- **Prefer indexed/semantic queries first:** use the discovery tool for “where is X defined?” / “find references” / “list relevant files” rather than doing broad tree walks.
- **Budget filesystem scans:** if you must search, use `rg` (or `rg --files`) and keep broad searches to *one pass per stage*, then narrow. Avoid `find`/`os.walk` loops and rerunning the same query.
- **Stop when sufficient:** once you have enough to produce the required artifact for the stage, stop searching and write the artifact; convert remaining uncertainty into a blocker/decision request.

### Workflow Docs to Include in Context

Unless a stage explicitly says otherwise, assume every agent should have access to (and should treat as binding) these workflow documents from `RULES_ROOT` plus `WORKFLOW_ROOT/AGENTS.md`:

- `RULES_ROOT/WORKFLOW.md` (this runbook)
- `WORKFLOW_ROOT/AGENTS.md` (role definitions + prohibitions)
- `RULES_ROOT/CONTRACTS.md` (non-negotiable invariants)
- `RULES_ROOT/POLICY.md` (policy constraints)
- `RULES_ROOT/TESTING.md` (unit-level testing expectations and allowed tools)

Additional “often needed” references (provide when relevant):
- `dependencies/dependencies-manifest.md` (dependency/caching constraints)
- `templates/requirements.template.md`, `templates/change-brief.template.md`, `templates/ticket.template.md`, `templates/validation-report.template.md` (for the stage’s artifact format)

### Best-Practice Ways to Provide These Docs (Phase 1 Continue CLI Default)

Use whichever method your CLI supports; Phase 1 standardizes on Continue CLI, but these practices remain framework-agnostic to preserve portability.

1) **Path-first (preferred):** provide `WORKFLOW_ROOT` and `RULES_ROOT`, and explicitly instruct the agent to read the docs above by path before acting.

2) **Pinned/open-file context:** open the docs in the CLI UI and pass them as “pinned files” / “open tabs” context (file contents come from disk, not from pasted snippets).

3) **Context header + pointers:** include a short header in the prompt (roots, stage, objective, boundary) plus a bullet list of doc paths; avoid pasting full documents unless the agent cannot read files.

4) **Excerpt only when necessary:** paste only the minimum relevant section (with the file path and heading name) when interacting with a constrained interface; prefer pointers to the source file to prevent drift.

### Path to Automation (Phase 2+)

When moving beyond Continue CLI-driven runs, the orchestrator/runner should automatically inject the workflow docs above into every agent invocation by reading them from `RULES_ROOT` and `WORKFLOW_ROOT` at runtime (or by generating a reproducible “context pack” from those files and attaching it). This preserves “artifacts are authoritative” while removing manual steps, and keeps a clear path to framework-agnostic execution.

When invoking any agent, include:
- **Stage number + objective** (what “done” means for this stage).
- **Workspace roots**: `PROJECT_ROOT`, `WORKFLOW_ROOT`, `ARTIFACT_ROOT` (fixed to `<PROJECT_ROOT>/artifacts`), and the relevant `CODE_ROOT` or `CODE_ROOTS[]`.
- **Repo(s) in scope** (name → root path mapping; use a single entry if only one repo is in scope).
- **Boundary under test** (CLI/API/messages/files/logs/exit codes) and any target constraints (OS/kernel/hardware) if applicable.
- **Worker runs only:** start the prompt with the ticket assignment header (Ticket ID, Branch ID, Scope, Dependencies; see `AGENTS.md`).
- **Pointers**: paths to the artifacts and code entry points to read (`artifacts/requirements/requirements.md`, relevant directories/files, existing tests).

## Agent Context (What Each Role Should Receive)

This is a “minimum viable” context checklist. More context is not always better; prefer **relevance and explicit scope**.

- **All roles (baseline):** ensure access to the workflow docs listed above from `WORKFLOW_ROOT` (prefer path-first or pinned-file context), and provide `PROJECT_ROOT` so `ARTIFACT_ROOT` is unambiguous.
- **Spec Writer:** initial request, `WORKFLOW_ROOT`, in-scope repo mapping, known constraints, and pointers to existing docs/code that define current behavior.
- **Ticket Writer:** approved `artifacts/requirements/requirements.md`, repo mapping, known dependencies/handoffs, and any constraints on ticket sizing/splitting.
- **Worker:** selected ticket(s), `CODE_ROOT` for the ticket, build/test commands if known, known boundaries, explicit “do not change” areas (e.g., simulator contract unless separately gated), and the required ticket assignment header at the top of the prompt.
- **Test Steward:** ticket + test plan (`artifacts/work/TICKET-ID/notes.md`), diff/paths under test, declared boundary, and the negative-case list to audit.
- **Integrator:** worker outputs (branches/MRs/commit SHAs), interface mismatch notes, and which `CODE_ROOTS[]` are being assembled.
- **Validator:** merge candidate identifiers (branches/SHAs), exact unit test commands per `CODE_ROOT`, and the declared boundary/negative-case expectations to validate against.

## Step Output Requirements (All Stages)

Every step must produce these outputs before it is considered complete:

- Updated `artifacts/workflow_state.json` that validates against `docs/workflow_state_schema.json`.
- All produced artifacts referenced in the state file with paths and hashes (when available).
- Any new blockers recorded explicitly in JSON as `inputs.open_questions[]` “decision requests”, with:
  - a recommended `default` answer (plus rationale),
  - clear `instructions` for how the human should fill the answer in-place in `artifacts/workflow_state.json`,
  - an `answer` object stub with placeholders where practical.
- At least one `quality.checks` entry updated for the step.

Definition of Done for a Step:

- JSON validates with `tools/workflow_state/validate`.
- `run.updated_at` advances.
- `current` reflects the completed step.
- `progress.next_steps` is computed, and the first next step is copy/paste runnable:
  - if unblocked: include `progress.next_steps[0].prompt` (and set `type: "agent"`),
  - if blocked: set `run.status: "blocked"`, keep blockers in `inputs.open_questions[]`, and set `progress.next_steps[0]` to a human step (`type: "human"`) with a prompt that points the human to the exact JSON fields to fill.
  - optional (recommended): queue additional pending steps in `progress.next_steps[1:]` (for example, an “on approval” agent step behind a human gate).
- Authoritative vs provisional separation is preserved.

## Workspace/Repo Consistency (Recommended)

To reduce “wrong repo / wrong branch / uncommitted changes” drift, stages that touch code (Stages 5–6, 8–10) should record and check expected workspace/repo state in `artifacts/workflow_state.json`:

- `workspace.project_root`, `workspace.workflow_root`, `workspace.artifact_root`, `workspace.code_roots` (recommended).
- `repo_state.expected[]` with at least `code_root`, `path`, and the expected `branch`/`commit` for the repo under change (recommended).

If the observed workspace does not match the recorded expectation, stop and escalate (or update the expectation with an explicit human decision).

CI Enforcement (Required):

- Run these commands from `PROJECT_ROOT` (so `artifacts/` resolves correctly).
- `<WORKFLOW_ROOT>/tools/workflow_state/validate artifacts/workflow_state.json`
- `<WORKFLOW_ROOT>/tools/workflow_state/render md artifacts/workflow_state.json`
- `git diff --exit-code artifacts/workflow_state.md`

Additional checks (Recommended):

- `<WORKFLOW_ROOT>/tools/tickets/validate artifacts/tickets/tickets.yaml`
- `<WORKFLOW_ROOT>/tools/workflow_state/check_repo_state artifacts/workflow_state.json` (when `repo_state.expected[]` is populated)

## Human Gates (How To Record Approvals)

This workflow has explicit **human approval gates** (requirements, tickets, merge/release). In Phase 1, the human sponsor records approvals directly in `artifacts/workflow_state.json` so the next stage can proceed deterministically.

### Authoritative vs Provisional (Important)

`artifacts/workflow_state.json` distinguishes between:
- `artifacts.provisional[]`: artifacts that exist but are **not yet accepted** by a human gate (no `accepted_by` / `accepted_at`).
- `artifacts.authoritative[]`: artifacts that are **accepted** and therefore must include `accepted_by` and `accepted_at` (schema-required).

Practical rule:
- If an artifact is not yet accepted, keep it in `artifacts.provisional[]` so the approval tool can promote it later.
- Do not place unaccepted artifacts under `artifacts.authoritative[]`; the state will fail schema validation.

Preferred method (no hand-editing): run `<WORKFLOW_ROOT>/tools/workflow_state/approve` and follow the interactive prompts (press ENTER to accept defaults). The tool will:
- promote selected `artifacts.provisional[]` entries into `artifacts.authoritative[]` with `accepted_by`/`accepted_at`,
- optionally mark the gate step complete and advance `progress.next_steps`,
- validate state and regenerate `artifacts/workflow_state.md`.

When you approve an artifact:

1) Edit `artifacts/workflow_state.json`:
   - Move the artifact entry from `artifacts.provisional[]` to `artifacts.authoritative[]`.
   - Add approval metadata to the authoritative entry:
     - `accepted_by`: use `git config --global user.name` + `git config --global user.email` in the format `Full Name <email>`.
     - `accepted_at`: an ISO-8601 UTC timestamp (e.g. `2026-01-18T19:09:55Z`).
2) Update step tracking:
   - Append the gate step id to `progress.completed_steps` (e.g. `stage-2-ticket-approval`).
   - Set the next runnable step in `progress.next_steps[0]`:
     - If work should continue: `type: "agent"` and include a copy/paste `prompt`.
     - If a human decision is required: `type: "human"` and include a copy/paste `prompt` that points to exact JSON fields to edit.
   - Optional (recommended): if `progress.next_steps[0]` is a **human approval gate**, also pre-populate `progress.next_steps[1]` with the intended **“on approval”** agent step (including its copy/paste prompt). When the sponsor runs `tools/workflow_state/approve` and advances the gate, the queue shifts and the next prompt is immediately available without extra editing.
3) Update run metadata:
   - Set `run.updated_at` to “now”.
   - Set `current.*` to the next stage’s objective (or keep it at the gate if you want the state to reflect “awaiting approval”).
4) Validate and regenerate the view:
   - `<WORKFLOW_ROOT>/tools/workflow_state/validate artifacts/workflow_state.json`
   - `<WORKFLOW_ROOT>/tools/workflow_state/render md artifacts/workflow_state.json`

## Stages

### Stage 1 — Requirements Draft

- **Preconditions:** initial human requirement exists (may be incomplete); `PROJECT_ROOT` is provided.
- **Responsible agent(s):** Spec Writer (AI-assisted), Human sponsor.
- **Working directory:**
  - artifacts: `artifacts/`
  - code context: `CODE_ROOT` (if code references are required)
- **Actions performed:**
  - interrogate ambiguity and constraints (target OS/kernel/hardware if relevant),
  - define goals/non-goals and acceptance criteria,
  - for greenfield work (or when a language choice is material), propose an implementation language/toolchain and record the rationale and constraints; if introducing a new primary language into an existing repo, flag it as an architectural decision requiring explicit human approval at the Stage 1 gate,
  - define unit-level validation expectations and boundaries.
- Ensure `<PROJECT_ROOT>/artifacts` exists (create if missing) and record the location in `artifacts/requirements/requirements.md` under the `Artifact Root (ARTIFACT_ROOT)` section (this is the required communication to the workflow user).
- **Artifacts produced:** `artifacts/requirements/requirements.md` (use `templates/requirements.template.md` or `templates/change-brief.template.md` for legacy changes).
- **Human gate:** **Required** — approve `artifacts/requirements/requirements.md` before tickets are generated.
- **GitLab/Jira interaction:** read-only for context.

### Stage 2 — Ticket Drafting (Local First)

- **Preconditions:** requirements approved in Stage 1.
- **Responsible agent(s):** Ticket Writer.
- **Working directory:**
  - artifacts: `artifacts/`
  - code context: `CODE_ROOT` (if code references are required)
- **Actions performed:**
  - decompose requirements into tickets with explicit scope and acceptance criteria,
  - ensure each ticket represents exactly one discrete work item with a clear deliverable,
  - produce `artifacts/tickets/tickets.yaml` using a single canonical list order (top-to-bottom = work order), with each ticket including:
    - `priority`: one of `Highest`, `High`, `Medium` (default), `Low`, `Lowest`
    - `status`: one of `Draft`, `Ready`, `In Progress`, `Done`, `Accepted`
    - `blocked_by`: list of ticket IDs; unblocked means empty, or contains only tickets whose `status` is `Accepted`
    - `code_root` and `unit_test_commands` (required for `Ready` and beyond)
  - treat `Accepted` as a human-only status (human gate) used to unblock dependent tickets,
  - ensure each ticket’s validation classification is **unit-only**,
  - include an initial unit test plan (see Stage 4 requirements).
- **Artifacts produced:** `artifacts/tickets/tickets.yaml` (ticket content aligned to `templates/ticket.template.md`).
- **Human gate:** **Required** — approve `artifacts/tickets/tickets.yaml` and ticket scopes before any external ticket creation.
- **GitLab/Jira interaction:** read-only by default; Jira issue creation is **proposed only** unless explicitly approved (Stage 3).

### Stage 3 — Jira Synchronization (Optional Default Integration; Gated)

- **Preconditions:** tickets approved in Stage 2.
- **Responsible agent(s):** Ticket Writer.
- **Working directory:**
  - artifacts: `artifacts/`
  - code context: `CODE_ROOT` (if code references are required)
- **Actions performed:**
  - prepare a dry-run “proposed Jira actions” description (what issues to create/fields/links),
  - upon human approval, create Jira issues in Jira Cloud and record created keys back into artifacts.
- **Artifacts produced:** updated `artifacts/tickets/tickets.yaml` including Jira keys/URLs (artifact remains system of record).
- **Human gate:** **Required** — approve applying the proposed Jira write actions.

### Stage 4 — Test Plan (Before Any Implementation)

- **Preconditions:** tickets exist and are approved; selection is performed as the first action in this stage.
- **Responsible agent(s):** Worker + Test Steward (review).
- **Worker prompt requirement:** begin every Worker run (Stages 4-6) with the ticket assignment header (Ticket ID, Branch ID, Scope, Dependencies).
- **Working directory:**
  - artifacts: `artifacts/` (write `artifacts/work/TICKET-ID/notes.md`)
  - code context: the ticket’s `CODE_ROOT` for reading code/tests as needed
- **Actions performed (must be explicit per ticket):**
  - apply the Selection Rule: scan `artifacts/tickets/tickets.yaml` from top to bottom and claim the first eligible ticket:
    - eligible means `status=Ready`, unblocked (`blocked_by` empty or only `Accepted`), and no `claimed_by`,
    - if `code_root` or `unit_test_commands` are missing, treat the ticket as not eligible and raise an open question (do not guess),
    - if no eligible ticket exists, inform the user and stop,
  - define the **interface boundary under test** (CLI/API/messages/files/logs/exit codes),
  - declare **black-box by default** posture; label any **white-box** tests and justify why (e.g., pure function with performance-critical behavior),
  - enumerate **meaningful negative cases** (invalid inputs, missing files, permissions, timeouts, device-not-present, partial failures),
  - if simulation/stubs are used, specify the **state model** and hostile/failure transitions exercised,
  - **scope guard (important):** the Stage 4 plan must be achievable within the ticket’s stated scope and dependencies.
    - Do not require tests for endpoints/components that are explicitly assigned to later tickets and do not yet exist.
    - If a desired test requires an interface/stub that is not introduced until a later ticket, record it explicitly as **deferred coverage** and name the ticket(s) that will own the implementation + tests.
    - Only propose “pulling work forward” (e.g., introducing a shared stub/contract early) if the ticket scope is intentionally being expanded and the orchestrator/human sponsor agrees to that scope change.
  - declare whether any simulator/stub changes are anticipated; if so, mark as a **contract-change proposal** requiring a human gate,
  - declare the **legacy containment** expectation: no new `#ifdef SIMULATION` outside the quarantine zone.
- **Time/effort constraint (important):** Stage 4 is a *planning* stage. The Worker must not run long-running commands (container builds, dependency installs, full test suites) as part of the test plan draft. Use lightweight repo inspection only (e.g., `rg`, `ls`, reading docs) to identify boundaries and enumerate negative cases. Any proposed “try it and see” validation belongs in Stage 5 (implementation) or Stage 9 (validation), and should be recorded as planned commands in the notes.
- **Required follow-up (still Stage 4): Test Plan Review**
  - After the Worker writes `artifacts/work/TICKET-ID/notes.md`, the **next step is a Test Steward review of the test plan** before any Stage 5 implementation begins.
  - This is a pre-implementation gate focused on test *posture* and *negative cases*; it is not Stage 7 (which is the post-implementation test review of actual test diffs).
  - The Test Steward records pass/fail and required changes in `artifacts/work/TICKET-ID/notes.md` and updates `artifacts/workflow_state.json` with the next prompt (Stage 5 Worker implementation if acceptable; otherwise blockers).
- **Artifacts produced:** `artifacts/work/TICKET-ID/notes.md` (Test Plan section) and/or ticket description fields; the plan must exist before code changes begin.
- **Human gate:** optional (recommended) if the boundary or simulation contract is contentious; otherwise proceed to Stage 5 after Test Steward review.
- **GitLab/Jira interaction:** none required.

### Stage 5 — Implementation (Worker Runs)

- **Preconditions:** Test Plan completed (Stage 4) for each ticket.
- **Responsible agent(s):** Worker.
- **Working directory:**
  - artifacts: `artifacts/` (update `artifacts/work/TICKET-ID/notes.md`)
  - code changes: the ticket’s `CODE_ROOT`
- **Autonomy guidance:** Worker proceeds without pausing for input when acceptance criteria are clear enough to implement; record assumptions as provisional in `artifacts/work/TICKET-ID/notes.md` and `artifacts/workflow_state.json`, and only block for decisions that affect correctness, safety, or policy gates.
- **Actions performed:**
  - **Preflight (must pass before any substantive work):**
    - confirm you are operating in the correct `CODE_ROOT` for the ticket (use the ticket’s `code_root` field from `artifacts/tickets/tickets.yaml`; if multiple `CODE_ROOTS[]` exist, run git commands explicitly against the chosen repo, e.g. `git -C <CODE_ROOT> …`),
    - confirm the ticket is claimed (`status=In Progress` with `claimed_by`/`claimed_at`) before making changes,
    - confirm you are **not** on `main`/`master` (or any protected trunk branch); if you are, **stop** and create/switch to a dedicated ticket branch,
    - confirm the working tree is clean (or only contains explicitly allowed local-only artifacts for the stage); if unrelated/unknown diffs exist, **stop** and escalate,
    - record `code_root`, `branch`, starting `commit SHA`, and the exact unit test commands you intend to run in `artifacts/work/TICKET-ID/notes.md` (and mirror key identifiers in `artifacts/workflow_state.json` provenance).
  - ensure the ticket is already claimed (`status=In Progress` with `claimed_by`/`claimed_at`) before starting substantive work,
  - implement the ticket in a branch,
  - add/update unit tests per Test Plan using the project-selected framework(s), and keep the ticket’s `unit_test_commands` accurate and runnable,
  - **commit locally** (one or more commits) and record the resulting commit SHA(s) in `artifacts/work/TICKET-ID/notes.md` and (recommended) `repo_state.expected[]` in `artifacts/workflow_state.json`.
    - If the `CODE_ROOT` has **no commits yet**, the Worker must create the initial commit as part of Stage 5 (still local-only; do not push).
  - record assumptions and evidence pointers in `artifacts/work/TICKET-ID/notes.md`,
  - prepare (dry-run) MR creation/update and Jira comments as needed.
- **Artifacts produced (per ticket):**
  - code + tests in the `CODE_ROOT` repository (on worker branch),
  - `artifacts/work/TICKET-ID/notes.md` updates (in `artifacts/`),
  - proposed MR description and references to ticket(s).
- **Human gate:** none for local implementation; **Required** to apply external writes (Stage 6).
- **GitLab/Jira interaction:** read-only by default; any write must follow Stage 6.

### Stage 6 — GitLab/Jira Updates for Work-in-Progress (Optional; Gated)

- **Preconditions:** worker has local changes and a recorded proposed external action.
- **Responsible agent(s):** Worker.
- **Working directory:**
  - artifacts: `artifacts/` (record proposed writes and resulting links/IDs)
  - code operations: the ticket’s `CODE_ROOT` for git operations (push/MR)
- **Actions performed:**
  - propose: branch push, MR create/update, Jira comment/status updates (record locally first),
  - upon human approval, apply the proposed writes.
- **Artifacts produced:** updates to `artifacts/work/TICKET-ID/notes.md` with links (MR URL, Jira key/comment IDs), plus any artifact fields that store those references.
- **Human gate:** **Required** — approve each external write batch (especially bulk actions).

### Stage 7 — Test Review (Skeptical Gate)

- **Preconditions:** Stage 5 implementation and unit tests exist for the ticket(s).
- **Responsible agent(s):** Test Steward.
- **Working directory:**
  - artifacts: `artifacts/` (record review results)
  - code context: the relevant `CODE_ROOT` to inspect diffs/tests
- **Actions performed (reject if any fail):**
  - reject tests that **mirror implementation structure** instead of behavior at the boundary,
  - reject **vacuous assertions** unless paired with concrete behavioral checks,
  - verify **negative-case quota** is meaningful (not “no exception thrown”),
  - verify simulator/stub edits are treated as **contract changes** and are gated (no stealth “fix tests”),
  - verify simulation (when used) is **stateful/hostile** enough to exercise failure modes,
  - perform the **legacy containment check:** no new `#ifdef SIMULATION` outside the quarantine zone (repo-defined; otherwise treat `platform/`, `hal/`, `backend/` as the only allowed quarantine roots).
- **Artifacts produced:** review result recorded in `artifacts/work/TICKET-ID/notes.md` and/or MR comments (if authorized).
- **If rejected (normal case):** this is a Worker-fix loop, not a human escalation.
  - The Test Steward records a clear **Fail** result and an explicit fix list in `artifacts/work/TICKET-ID/notes.md`.
  - The Test Steward updates `artifacts/workflow_state.json` to set `progress.next_steps[0]` to a **Worker** step to fix tests/coverage for the same ticket (and may queue a Stage 7 re-review as `progress.next_steps[1]`).
  - **Scope guard:** do not fail a ticket for missing tests of functionality that does not exist yet and is assigned to other tickets. Instead, require the notes to record **deferred coverage** (what is deferred, and which ticket(s) will add the tests once the boundary exists).
  - Only use `inputs.open_questions[]` + a human next step when a human decision is actually required (e.g., waive a policy requirement for an in-scope behavior, approve a simulator/stub contract change, accept reduced evidence, or intentionally pull work forward into the current ticket).
- **Human gate:** required to accept any simulator contract change; otherwise the Test Steward’s rejection blocks progress until corrected.

### Ticket Acceptance (Per-Ticket; Human)

When a ticket’s deliverable is complete and evidence is sufficient (notes + tests + any required validation), a human may mark that ticket `Accepted` in `artifacts/tickets/tickets.yaml`. Dependent tickets treat a `blocked_by` entry as satisfied only when the referenced ticket is `Accepted`.

### Stage 8 — Integration Preparation

- **Preconditions:** tickets have passing-reviewed test posture (Stage 7) or explicit waivers approved by humans.
- **Responsible agent(s):** Integrator (human or AI-assisted).
- **Working directory:**
  - artifacts: `artifacts/` (write `artifacts/integration/merge-summary.md`)
  - code context: whichever `CODE_ROOTS[]` are being merged/rebased/assembled
- **Actions performed:**
  - reconcile outputs and interface mismatches,
  - prepare a merge candidate (single MR or coordinated MRs),
  - summarize what is being merged and remaining risk.
- **Artifacts produced:** `artifacts/integration/merge-summary.md`.
- **Recording rule:** record the merge summary as a **provisional** artifact entry unless/until a human explicitly accepts it (often at the Stage 10 merge gate). Stage 9 may consume a provisional merge summary as input.
- **Human gate:** required before any integration MR is merged (Stage 10).
- **GitLab/Jira interaction:** read-only by default; integration MR updates are gated writes.

### Stage 9 — Validation (Unit-Level Only)

- **Preconditions:** merge candidate exists; all required unit tests are present.
- **Responsible agent(s):** Validator.
- **Working directory:**
  - artifacts: `artifacts/` (write `artifacts/validation/validation-report.md`)
  - code context: run tests in each relevant `CODE_ROOT`
- **Actions performed:**
  - run unit tests relevant to the change set by executing the ticket-declared `unit_test_commands` (or explicitly justify omissions),
  - record posture: black-box/white-box mix and justifications,
  - summarize negative-case coverage at the behavior boundary,
  - record any simulator/stub changes and their approval state,
  - repeat the legacy containment check,
  - perform a lightweight **mutation sanity check** for critical behaviors (a minimal “would this fail if behavior breaks?” step; no full mutation-testing tooling required).
- **Artifacts produced:** `artifacts/validation/validation-report.md` (use `templates/validation-report.template.md`).
- **Human gate:** required to accept validation omissions; required before any posting of results to Jira/GitLab.
- **GitLab/Jira interaction:** optional gated comments linking the validation report.

### Stage 10 — Merge (Human)

- **Preconditions:** `artifacts/integration/merge-summary.md` and `artifacts/validation/validation-report.md` exist and are up to date for the merge candidate.
- **Responsible agent(s):** Human reviewer(s) with merge authority.
- **Working directory:**
  - artifacts: `artifacts/` (record post-merge references if needed)
  - code context: merge occurs in GitLab for the relevant `CODE_ROOT`
- **Actions performed:**
  - review diffs/MR(s), merge summary, and validation report,
  - approve or reject merge,
  - merge in GitLab EE if approved.
- **Artifacts produced:** none required beyond existing reports; record final decision references (MR merge commit) in the merge summary if desired.
- **Human gate:** **Required** — merge approval is always human-controlled in Phase 1.

### Stage 11 — Acceptance / Release (Human; Out of Scope for Validation)

- **Preconditions:** merge completed; downstream system/integration testing (outside this workflow) may exist elsewhere.
- **Responsible agent(s):** Human release authority.
- **Working directory:** out of scope for this workflow (organization-defined).
- **Actions performed:** accept/reject for release based on organization process; this workflow does not extend validation scope.
- **Artifacts produced:** not defined by this workflow.
- **Human gate:** **Required**.

## Appendix A - Example Prompts

These prompts are LLM-agnostic and tool-agnostic. They are plain-text prompts validated in Continue CLI for Phase 1, and should work in other frameworks with equivalent context injection.

Use this fixed layout:
- `PROJECT_ROOT=/path/to/project-root`
- `WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>`
- `ARTIFACT_ROOT=/path/to/project-root/artifacts`
- `CODE_ROOTS`: one or more repos under `PROJECT_ROOT`

### Stage 1 - Requirements Draft

```
Stage 1 - Requirements Draft
Objective: Produce artifacts/requirements/requirements.md for the change.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
In-scope repos: repo-a (primary)[, repo-b (reference)]. Boundary: <CLI/API/messages/files/logs/exit codes>.
Initial request: <human requirement text>.
Output: artifacts/requirements/requirements.md (use templates/requirements.template.md or templates/change-brief.template.md).
Also update: artifacts/workflow_state.json.
```

### Stage 2 - Ticket Drafting (Local First)

```
Stage 2 - Ticket Drafting
Objective: Create artifacts/tickets/tickets.yaml from approved requirements.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/requirements/requirements.md.
Constraints: unit-level validation only; include test plan notes.
Ticket scope rule: each ticket must represent exactly one discrete work item with a clear deliverable.
Output: artifacts/tickets/tickets.yaml aligned to templates/ticket.template.md.
Also update: artifacts/workflow_state.json.
```

### Stage 3 - Jira Synchronization (Optional; Gated)

```
Stage 3 - Jira Sync (Dry-Run Only)
Objective: Propose Jira actions for approved tickets; do not apply changes.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/tickets/tickets.yaml.
Output: a dry-run "proposed Jira actions" record in artifacts/ and updated artifacts/tickets/tickets.yaml only if approved.
Also update: artifacts/workflow_state.json.
```

### Stage 4 - Test Plan (Before Any Implementation)

```
Stage 4 - Test Plan
Objective: Write artifacts/work/TICKET-ID/notes.md test plan for the selected ticket.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Selection Rule: scan `artifacts/tickets/tickets.yaml` from top to bottom and claim the first eligible ticket (`status=Ready`, unblocked, unclaimed).
Read artifacts/tickets/tickets.yaml.
Constraint: planning only — do not run long-running builds/installs/full test suites in this stage; record proposed commands instead.
Output: artifacts/work/TICKET-ID/notes.md (Test Plan section).
Also update: artifacts/workflow_state.json.
```

### Stop / Redirect (Human Watchdog)

If a run is taking too long or feels off-track, stop it and run this prompt to regain control:

```
Stop and summarize.

State the current objective (1 sentence), what you have established as facts (bullet list with sources/files), what you have tried (commands/paths), and the next 3 concrete steps. If you are stuck, convert the uncertainty into an `inputs.open_questions[]` decision request (with a default and in-place instructions) and stop.
```

### Stage 4b - Test Plan Review (Test Steward; Before Implementation)

```
Stage 4b - Test Plan Review
Objective: Review the Stage 4 test plan in artifacts/work/TICKET-ID/notes.md and record pass/fail before Stage 5 implementation begins.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/work/TICKET-ID/notes.md and artifacts/tickets/tickets.yaml.
Record pass/fail and required changes in artifacts/work/TICKET-ID/notes.md.
Also update: artifacts/workflow_state.json.
```

### Stage 5 - Implementation (Worker Runs)

```
Stage 5 - Implementation
Objective: Implement the selected ticket with tests and update artifacts/work/TICKET-ID/notes.md.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/work/TICKET-ID/notes.md and artifacts/tickets/tickets.yaml.
Before starting substantive work, ensure the ticket is already claimed (status In Progress with claimed_by/claimed_at) as part of the Selection Rule.
Implement code and tests in the relevant CODE_ROOT; update artifacts/work/TICKET-ID/notes.md with assumptions/evidence.
Output: code + tests + updated artifacts/work/TICKET-ID/notes.md.
Also update: artifacts/workflow_state.json.
```

### Stage 6 - GitLab/Jira Updates for Work-in-Progress (Optional; Gated)

```
Stage 6 - External Updates (Dry-Run)
Objective: Record proposed external writes in artifacts/work/TICKET-ID/notes.md.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/work/TICKET-ID/notes.md.
Record proposed external writes in artifacts/work/TICKET-ID/notes.md.
Also update: artifacts/workflow_state.json.
```

### Stage 7 - Test Review (Skeptical Gate)

```
Stage 7 - Test Review
Objective: Review tests and record results in artifacts/work/TICKET-ID/notes.md.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/work/TICKET-ID/notes.md and test diffs.
Record pass/fail review in artifacts/work/TICKET-ID/notes.md.
Also update: artifacts/workflow_state.json.
```

### Stage 8 - Integration Preparation

```
Stage 8 - Integration Preparation
Objective: Reconcile outputs and write artifacts/integration/merge-summary.md.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/work/**/notes.md and branch/MR info.
Use CODE_ROOTS for diffs/SHAs; record summary in artifacts/integration/merge-summary.md.
Update artifacts/workflow_state.json:
- Add/refresh an entry for artifacts/integration/merge-summary.md under artifacts.provisional[] (not authoritative unless already accepted).
- Keep progress.next_steps[0] runnable (usually Stage 9 - Validation), and optionally queue a Stage 10 human merge step behind it.
```

### Stage 9 - Validation (Unit-Level Only)

```
Stage 9 - Validation
Objective: Run unit tests and produce artifacts/validation/validation-report.md.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/integration/merge-summary.md and artifacts/work/**/notes.md.
Output: artifacts/validation/validation-report.md.
Also update: artifacts/workflow_state.json.
```

### Stage 10 - Merge (Human)

```
Stage 10 - Merge (Human)
Objective: Merge in GitLab after approval.
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/integration/merge-summary.md and artifacts/validation/validation-report.md.
If approved, merge in GitLab and record merge commit in artifacts/integration/merge-summary.md.
Also update: artifacts/workflow_state.json.
```

### Stage 11 - Acceptance / Release (Human)

```
Stage 11 - Acceptance / Release (Human)
Objective: Accept or reject for release (outside this workflow).
Workspace: PROJECT_ROOT=/path/to/project-root
WORKFLOW_ROOT=/path/to/project-root/<WORKFLOW_ROOT>
ARTIFACT_ROOT=/path/to/project-root/artifacts
CODE_ROOTS: repo-a=/path/to/project-root/repo-a[, repo-b=/path/to/project-root/repo-b]
Rules: RULES_ROOT=/path/to/rules
Read workflow docs from RULES_ROOT and WORKFLOW_ROOT/AGENTS.md.
Read artifacts/integration/merge-summary.md and artifacts/validation/validation-report.md.
Also update: artifacts/workflow_state.json when acceptance decisions are recorded.
```
