---
name: CONTRACTS.md
title: Agentic Development Workflow Contracts (MVP)
description: This document defines the non-negotiable invariants of the Phase 1 (MVP) Agentic Development Workflow.
version: 0.1.0
---
# CONTRACTS.md

This document defines the **non-negotiable invariants** of the Phase 1 (MVP) Agentic Development Workflow.

## Human Authority and Gates

- Humans retain final authority over **requirements approval**, **ticket approval**, **merge approval**, and **acceptance/release**.
- No agent may finalize a gated action by default; agents may only **propose and prepare**.

## Artifact Primacy

- Repository artifacts are the **system of record**; conversation and external tool state are non-authoritative.
- All decisions, assumptions, and proposed external mutations must be captured in artifacts.
- When artifacts and tool state disagree, the correct behavior is to **pause and escalate**, not to guess.
- `artifacts/workflow_state.json` is the canonical workflow state; all views are derived from it and are non-authoritative.
- `artifacts/workflow_state.json` must remain schema-valid:
  - unaccepted artifacts belong in `artifacts.provisional[]`,
  - `artifacts.authoritative[]` entries must include `accepted_by` / `accepted_at` (human gate),
  - agents must not place provisional/unaccepted artifacts into `artifacts.authoritative[]`.

## Validation Scope (Unit-Level Only)

- The workflow’s validation scope is **unit tests only**.
- The workflow is **language-agnostic**: any implementation language/toolchain is permitted **if** it supports unit tests that meet the evidence requirements in `RULES_ROOT/TESTING.md`.
- Default unit-test frameworks (required when applicable):
  - **C++:** GoogleTest (gtest)
  - **Python:** pytest
  - **Shell:** bats (bats-core)
- Introducing a new primary language into a repo, or changing the unit-test framework for an existing language, is an architectural decision that must be explicitly proposed in Stage 1 requirements and approved by a human at the Stage 1 gate (and recorded in `dependencies/dependencies-manifest.md`).
- No agent may claim system/integration correctness, production readiness, or hardware correctness beyond the unit abstraction evidenced by tests.

## External System Safety (Real Systems)

- GitLab EE and Jira Cloud are treated as **real systems with real impact** when configured.
- Any external write (create/update/transition/comment/branch/MR changes) is **dry-run by default** and must not be applied without explicit stage authority and a human approval.
- Destructive or bulk external actions are never executed without an explicit, prior recorded proposal and human approval.

## Tooling Adapter Neutrality

- The workflow is **tooling-agnostic at the core**; adapters (including MCP servers) are implementation details.
- Default integrations may target GitLab EE and Jira Cloud, but the workflow must remain executable from artifacts alone.
- Phase 1 standardizes on **Continue CLI** for interactive runs, while preserving a clear path to framework-agnostic execution.

## Phase 1 Autonomy Limits

- Agents are **stateless beyond artifacts**; no hidden memory is authoritative.
- When uncertain about authority, scope, requirements, or evidence, the system must **stop and escalate**.

## Test Integrity (Acceptance Invariants)

- **Behavior-first by default:** tests primarily confirm externally observable behavior at a defined interface boundary (CLI/API/messages/files/logs/exit codes), not internal implementation structure.
- **Black-box posture:** black-box tests through stable boundaries are preferred; white-box tests are allowed only when explicitly justified and labeled as white-box.
- **Negative cases are required:** each feature includes meaningful negative cases (invalid inputs, missing files, permissions, timeouts, device-not-present, partial failures); “no exception thrown” is not sufficient evidence.
- **Anti-triviality:** vacuous assertions (“not None”, “returns True”) are prohibited unless paired with concrete behavioral assertions.
- **Simulator-as-contract:** simulators/drivers/stubs model the contract with reality; simulator changes must be treated as contract changes and require explicit human review/approval. Tests must not be “fixed” by quietly mutating simulation.
- **Stateful/hostile simulation:** when simulation exists, it models realistic state transitions and failure modes (not only happy-path return values).
- **Legacy containment:** no new `#ifdef SIMULATION` is introduced outside a designated quarantine zone (repo-defined; absent a repo definition, treat `platform/`, `hal/`, and `backend/` as the only permitted quarantine roots if present).
- **Mutation sanity (lightweight):** validation includes a minimal check that critical behavior tests would fail under a plausible break; full mutation-testing tooling is not required.
