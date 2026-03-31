# Workflow State Specification

This document defines the canonical workflow state for the Agentic Development Workflow.
The JSON state is the single source of truth; all views are derived outputs.

## Canonical State Location

- Default path: `<PROJECT_ROOT>/artifacts/workflow_state.json`.
- Every step must read the JSON at step start and write an updated JSON at step end.
- Views (Markdown or otherwise) are generated from JSON and are not authoritative.

## Single Source of Truth

- JSON is authoritative.
- Views must not contain facts not present in JSON.
- Agents must not rely on prose to determine state.

## Required Top-Level Keys

`workflow_state.json` must include these keys (additional keys are allowed):

- `workflow`: `{ name, version }`
- `run`: `{ run_id, status, created_at, updated_at }`
- `current`: `{ phase, stage, step, objective }`
- `progress`:
  - `completed_steps`: string[]
  - `next_steps`: array of `{ id, agent, inputs_required[], outputs_expected[] }`
    - optional: `type` in `["agent","human"]`
    - optional: `status` in `["ready","pending"]` (recommended; informational)
    - optional: `prompt` (copy/paste ready)
    - **Queue semantics:** `progress.next_steps` is an ordered queue. Only index `0` is actionable; any additional entries (`[1:]`) are **queued/pending** (for example, an “on approval” step that should run immediately after a human gate is completed).
- `artifacts`:
  - `authoritative`: array of `{ id, type, path, status, hash, produced_by, accepted_by, accepted_at }`
  - `provisional`: array of `{ id, type, path, status, produced_by }`
- `inputs`:
  - `locked`: array of `{ name, value, source }` where `source in ["human","repo","tool"]`
  - `open_questions`: array of “decision requests”:
    - required: `{ id, question, owner, blocking }`
    - optional (recommended): `status` in `["open","resolved"]`
    - optional (recommended): `default: { value, rationale }`
    - optional (recommended): `instructions` (how the human should answer in-place)
    - optional (recommended): `answer: { status, value, answered_by, answered_at, notes }`
- `quality`:
  - `checks`: array of `{ id, status, notes }` where `status in ["pass","fail","warn","na"]`
  - `risks`: array of `{ id, risk, mitigation }`
- `provenance`:
  - `last_actor`, `last_action`, `notes_for_humans`

The schema is defined in `docs/workflow_state_schema.json`.

## Optional Workspace + Repo State (Recommended)

To make stages fail-fast and reduce “wrong branch / wrong repo / uncommitted work” drift, the state file may also record:

- `workspace` (paths are usually absolute):
  - `project_root`
  - `workflow_root`
  - `artifact_root`
  - `code_roots`: mapping of `code_root` name → absolute path
- `repo_state`:
  - `expected[]`: per-repo expected `branch`/`commit` and (optionally) `dirty_allowed_paths`
  - `observed[]`: per-repo observed `branch`/`commit` and any detected `dirty_paths`

These fields are optional but schema-valid, and are intended to support deterministic “does the workspace match what this step assumes?” checks.

### Repo State Check Tool (Optional)

When `repo_state.expected[]` is populated, you can run:

- `<WORKFLOW_ROOT>/tools/workflow_state/check_repo_state artifacts/workflow_state.json`

To also capture observed state back into JSON for audit:

- `<WORKFLOW_ROOT>/tools/workflow_state/check_repo_state --write-observed artifacts/workflow_state.json`

## Authoritative vs Provisional

- Any artifact without explicit human acceptance is provisional.
- Authoritative artifacts must record acceptance:
  - `accepted_by`
  - `accepted_at`
- Provisional artifacts must not be promoted to authoritative without explicit acceptance recorded in JSON.

### Human Approval Procedure (In-Place)

To approve a produced artifact and allow the workflow to advance:

Preferred method: run `<WORKFLOW_ROOT>/tools/workflow_state/approve` and follow the interactive prompts (press ENTER to accept defaults).

1) Locate the artifact entry under `artifacts.provisional[]`.
2) Move it to `artifacts.authoritative[]`.
3) Add:
   - `accepted_by: "Full Name <email>"` (see “Human Actor Identification”),
   - `accepted_at: "<ISO-8601 UTC timestamp>"`.
4) Update `run.updated_at` and set a new `progress.next_steps[0]` (including `type` and a copy/paste `prompt`).
   - If the workflow is waiting on a **human approval gate**, you may also pre-populate `progress.next_steps[1]` with the intended “on approval” next step so the prompt is immediately available after approval. The `approve` tool advances the queue by removing the gate step.

## Human Actor Identification

When a field identifies a human actor (for example `accepted_by`, `inputs.open_questions.owner`, or `provenance.last_actor` when the actor is a human), the value must be the human's full name and email address derived from git config in this order:

1) `git config --global user.name` + `git config --global user.email`
2) `git config --system user.name` + `git config --system user.email`
3) fallback to `<username>@<hostname>`

Format: `Full Name <email>`.

## Provenance and Unknowns (Anti-Hallucination)

If information is not sourced from `human`, `repo`, or `tool`, it must be handled as one of:

- A provisional artifact entry, or
- An `inputs.open_questions` entry, or
- A provenance note explicitly marked as non-authoritative in `provenance.notes_for_humans`.

Agents must not silently fill in missing fields. If the data is unknown, it must be recorded as unknown, blocked, or provisional.

## Blocking Behavior

- If any `inputs.open_questions` has `blocking=true` and does not specify `ticket_id`, the workflow must not advance phases or stages.
- If a blocking open question specifies `ticket_id`, it blocks progress on that ticket; other tickets may proceed.
- `progress.next_steps` must be a blocker-resolution step or a human decision step while blockers exist for the current ticket.

### Human Resolution Procedure (In-Place)

Humans resolve decision requests by editing `artifacts/workflow_state.json` directly (no sidecar file):

1) Find the relevant object in `inputs.open_questions[]`.
2) Fill `answer.value` (or otherwise record the decision under `answer.*`).
3) Mark it resolved by setting:
   - `status: "resolved"` (recommended), and
   - `blocking: false`
4) Record provenance in-place:
   - `answer.answered_by: "Full Name <email>"`
   - `answer.answered_at: "<ISO-8601 timestamp>"`

After all currently-relevant blocking requests are resolved, the next agent run should re-read the JSON and continue, producing updated artifacts and a new `progress.next_steps[0].prompt`.

## “Allowed Dirty Paths” Strategy (What It Is / Why It’s Risky)

“Allowed dirty paths” is a tool-agnostic strategy for handling workflows where certain local-only artifacts may be modified during a run (for example: `build/` outputs, `.pytest_cache/`, `dist/`, or locally regenerated caches used only for validation).

- **What it is:** a whitelist of paths that are permitted to be dirty *at preflight time* without blocking the stage.
- **What it is not:** it is not permission to ignore diffs broadly, and it must not hide unexpected changes.
- **How to use safely:**
  - keep the allowlist as small as possible and stage-specific,
  - never include source paths you intend to modify as part of the deliverable (those should be clean at preflight),
  - require the agent to print/list dirty files and show they are all within the allowlist before proceeding,
  - record the allowlist (and rationale) in `repo_state.expected[].dirty_allowed_paths` so reviewers can audit what was permitted.

If in doubt, prefer a clean working tree at Stage 5 start and treat unexpected dirtiness as a blocker.

## Determinism and Ordering

- Views must be deterministic: same JSON in, same output bytes.
- No ad-hoc timestamps in views (only timestamps present in JSON).
- Array ordering is authoritative; renderers must preserve the order as stored in JSON.

## Hashing and Paths

- `artifacts.*.path` should be relative to `PROJECT_ROOT` (for example `artifacts/requirements/requirements.md`) or an absolute filesystem path.
- `artifacts.*.hash` should use a stable prefix format like `sha256:<hex>` when available.
- If a hash is not available, record an empty string and keep the artifact provisional until computed or accepted.

## View Registry

Views are implemented as modules under `tools/workflow_state/views/`.

- `render <view> <path>` loads the view module and writes `workflow_state.<view>` next to the JSON file.
- `render md` writes `workflow_state.md`.

## Markdown View (Required)

The Markdown view must render:

- Run id, status, updated_at
- Current phase/stage/step/objective
- Blockers (open questions where `blocking=true`)
- Next step (first entry in `progress.next_steps`)
- Queued next steps (any additional entries in `progress.next_steps[1:]`)
- Last accepted authoritative artifact
- Quality failures/warnings and risks
- `provenance.notes_for_humans`

No additional facts may appear in the Markdown view.

## Definition of Done for a Step

A step is considered complete only when:

- `workflow_state.json` validates against the schema.
- `run.updated_at` advances.
- `current` reflects the completed step.
- `progress.next_steps` is computed or explicitly blocked.
- Produced artifacts are referenced in JSON with paths and hashes (when available).
- Authoritative vs provisional separation is preserved.
- At least one `quality.checks` entry is updated for the step.

## Example (Excerpt)

```json
{
  "workflow": {"name": "agentic-dev", "version": "0.1.0"},
  "run": {
    "run_id": "example-2025-01-15-001",
    "status": "blocked",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "current": {
    "phase": "stage-2",
    "stage": "ticket-drafting",
    "step": "draft tickets",
    "objective": "Produce tickets.yaml from approved requirements"
  }
}
```
