# Workflow Runner Skill Contract

## Purpose and scope

Package the workflow-runner skill at `skills/workflow-runner/` for use with
this repository's accelerated agentic engineering workflow. The repository's
`AGENTS.md`, resolved rule documents, and workflow-state specification remain
the design authority; the skill does not change roles, gates, or validation scope.

## Portability and privacy

- Include `SKILL.md` and `agents/openai.yaml` with normal automatic discovery.
- Use configured workspace roots and project-relative artifact paths. Include
  no private filesystem paths, hostnames, credentials, actual issue keys,
  personal preferences, or organization-specific operating conventions.
- Reuse repository templates, schema, and state tools. Use `validate` and
  `render md` for step completion; do not depend on a separate finalizer.
- Jira quick start is optional read-only intake through an available configured
  connector or CLI. It must not require a particular account or tool installation.
- Preserve explicit role activation and human-only acceptance. A generic kickoff
  request must not silently grant a role or approval.

## Acceptance and validation

- Document installation, workspace roots, and an explicit-role invocation in README.
- Retain role outputs, deterministic ticket selection, state updates, provisional
  artifacts, unit-level evidence limits, and external-write gates.
- Validate skill metadata, review the complete addition for private content, check
  referenced repository tools/templates exist, and run the existing unit suite.
- Provide `make test` using the existing standard-library test runner, without
  introducing third-party dependencies or network calls.
