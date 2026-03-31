---
name: TESTING.md
title: Testing Standard (MVP)
description: This document defines the unit-test evidence standard (language-agnostic), default unit test frameworks, and minimum validation behaviors required by the Agentic Development Workflow MVP.
version: 0.1.0
---
# Testing Standard (MVP)

This document defines the **unit-test evidence standard** (language-agnostic) plus **default unit test frameworks** and the **minimum validation behaviors** required by the Agentic Development Workflow MVP.

## Scope

- **In scope:** unit tests + fast checks that run during development/CI.
- **Out of scope:** system-level / integration testing infrastructure and execution.

The Validator agent must be able to run the unit tests described here and produce an `artifacts/validation/validation-report.md` that clearly states what was executed and what was not.

## Validation Interface and Defaults (Required)

The workflow is **implementation-language-agnostic**. What is fixed is the **evidence standard** required for validation.

### Validation Interface (Required)

For any language/toolchain used in a `CODE_ROOT`:
- Unit tests must be runnable via explicit commands recorded in `artifacts/tickets/tickets.yaml` (`unit_test_commands`) and repeated in `artifacts/validation/validation-report.md`.
- Commands must be deterministic and must fail with a non-zero exit code on test failure.
- Tests must avoid external network calls by default (unless explicitly scoped/approved and recorded).

### Default Frameworks (Recommended; Required When Applicable)

For repos that use these languages, the default unit-test frameworks are:
- **C++:** GoogleTest (gtest)
- **Python:** `pytest`
- **Shell scripting:** `bats` (bats-core)

These defaults are not exclusive. If a project uses other languages (e.g., Go/Rust/Java/JavaScript), select an appropriate unit-test framework for that ecosystem and record it (plus install/pinning details) in `dependencies/dependencies-manifest.md`.

### Introducing a New Language or Test Framework (Guardrailed)

Introducing a new primary implementation language into a repo, or replacing the unit-test framework, is treated as an architectural decision:
- Propose it explicitly in Stage 1 requirements (rationale + constraints + toolchain plan).
- Require human approval at the Stage 1 gate.
- Record dependency sourcing and version pinning in `dependencies/dependencies-manifest.md`.

## Network and Caching Constraint

Unit testing is **not performed in air-gapped environments**. Dependencies may be fetched from public sources **only if** they operate within the project's cached runtime expectations.

Practically, this means:
- pin versions where reasonable,
- document how dependencies are satisfied (internal cache/mirror, vendoring, or pre-baked image),
- avoid “latest” and unbounded installers.

The authoritative record is `dependencies/dependencies-manifest.md`.

## C++ (GoogleTest)

### Recommended layout (example)
- Source: `src/...`
- Tests: `tests/cpp/...`
- Test binaries: produced by your build system (CMake recommended but not required)

### Minimum expectations
- A `ctest`-compatible target or a documented way to run the gtest binaries.
- Tests are fast and deterministic.
- Any kernel/hardware coupling must be mocked or abstracted at the unit level when feasible.

### Examples of acceptable “unit” scope
- parsing/formatting
- business logic
- boundary conditions
- error handling
- wrappers around kernel/hardware interfaces using fakes/mocks

## Python (`pytest`)

### Recommended layout (example)
- Source: `src/...` or package directory
- Tests: `tests/python/...` or `tests/...`

### Minimum expectations
- `pytest -q` runs successfully locally/CI with documented prerequisites.
- Tests avoid external network calls by default (unless explicitly scoped and approved).

## Shell (`bats`)

### Recommended layout (example)
- Scripts: `scripts/...`
- Tests: `tests/shell/...`

### Minimum expectations
- `bats tests/shell` (or equivalent) runs in a clean environment.
- Scripts should be written for testability (functions, dependency injection via env vars, etc.) where practical.

## Validator Behavior (Required)

Validator must:
1. Run unit tests for the change set by executing the ticket-declared `unit_test_commands` (or explicitly justify omissions).
2. Capture results (pass/fail + summary).
3. Produce a `artifacts/validation/validation-report.md` including:
   - what ran (commands)
   - where it ran (env)
   - what didn’t run and why
   - links/references to artifacts (logs, MR, Jira ticket)

Template: `templates/validation-report.template.md`.

## Optional Fast Checks (Recommended)

These are recommended but not required for the MVP:
- Shell: `shellcheck` (high value)
- Python: `ruff` (fast lint) or `flake8`
- Other languages: equivalent lint/format tooling appropriate to the chosen toolchain
- C++: formatting/lint as appropriate to the repo

If enabled, they should be recorded in the validation report.
