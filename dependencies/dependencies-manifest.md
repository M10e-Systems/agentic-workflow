# Dependencies Manifest (MVP)

This document records the dependencies needed to run unit tests and validation in the MVP workflow.

## Policy
- Unit testing/validation is not air-gapped.
- Publicly available dependencies are allowed **if** they operate within the project's cached runtime practices.
- Avoid unpinned “latest”. Prefer pinned versions or pre-baked images/runners.

## Default Test Frameworks (Recommended; Required When Applicable)
- C++: GoogleTest (gtest)
  - Source: <internal cache/mirror or vendored approach>
  - Version: <pin or policy>
- Python: pytest
  - Source: <internal cache/mirror or pip cache policy>
  - Version: <pin or policy>
- Shell: bats (bats-core)
  - Source: <internal cache/mirror or vendored approach>
  - Version: <pin or policy>

## Project-Defined Languages / Toolchains

Use this section when the project selects additional implementation languages/toolchains (including future languages). Each entry must make validation reproducible and compatible with cached runtime practices.

- <Language/toolchain>: <unit test framework/tooling>
  - Source: <internal cache/mirror/vendored/pre-baked image>
  - Version: <pin or policy>
  - Notes: <how tests are invoked; where `unit_test_commands` are recorded>

## Optional Fast Checks (Recommended)
- ShellCheck
  - Source:
  - Version:
- Ruff (or Flake8)
  - Source:
  - Version:

## Runtime Notes
- Cached runtime behavior:
  - <describe how dependencies are cached/satisfied in your environment>
- CI runner / build image expectations:
  - <describe base image or environment assumptions>
