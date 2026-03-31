import json
from typing import Any, Dict, List


def _format_value(value: Any) -> str:
    if value in (None, ""):
        return "Not set"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _is_resolved(question: Dict[str, Any]) -> bool:
    if question.get("status") == "resolved":
        return True

    answer = question.get("answer", {})
    if isinstance(answer, dict) and answer.get("status") == "resolved":
        return True

    return False


def _get_blockers(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    inputs = state.get("inputs", {})
    questions = inputs.get("open_questions", [])
    return [q for q in questions if q.get("blocking") is True and not _is_resolved(q)]


def _get_next_step(state: Dict[str, Any]) -> Dict[str, Any]:
    progress = state.get("progress", {})
    next_steps = progress.get("next_steps", [])
    return next_steps[0] if next_steps else {}


def _get_queued_next_steps(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    progress = state.get("progress", {})
    next_steps = progress.get("next_steps", [])
    if not next_steps or len(next_steps) < 2:
        return []
    return next_steps[1:]


def _get_last_accepted_artifact(state: Dict[str, Any]) -> Dict[str, Any]:
    artifacts = state.get("artifacts", {})
    authoritative = artifacts.get("authoritative", [])
    if not authoritative:
        return {}

    with_accepted_at = [a for a in authoritative if a.get("accepted_at")]
    if with_accepted_at:
        return sorted(with_accepted_at, key=lambda a: a.get("accepted_at", ""))[-1]
    return {}


def _get_authoritative_acceptance_warnings(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    artifacts = state.get("artifacts", {})
    authoritative = artifacts.get("authoritative", [])
    if not isinstance(authoritative, list) or not authoritative:
        return []

    warnings: List[Dict[str, Any]] = []
    for artifact in authoritative:
        if not isinstance(artifact, dict):
            continue
        accepted_by = artifact.get("accepted_by")
        accepted_at = artifact.get("accepted_at")
        if not accepted_by or not accepted_at:
            warnings.append(artifact)
    return warnings


def _get_quality_issues(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    quality = state.get("quality", {})
    checks = quality.get("checks", [])
    return [c for c in checks if c.get("status") in ("fail", "warn")]


def render(state: Dict[str, Any]) -> str:
    run = state.get("run", {})
    current = state.get("current", {})
    provenance = state.get("provenance", {})
    quality = state.get("quality", {})

    blockers = _get_blockers(state)
    next_step = _get_next_step(state)
    queued_next_steps = _get_queued_next_steps(state)
    last_artifact = _get_last_accepted_artifact(state)
    acceptance_warnings = _get_authoritative_acceptance_warnings(state)
    quality_issues = _get_quality_issues(state)
    risks = quality.get("risks", [])

    lines = ["# Workflow State", ""]

    lines.append("## Run")
    lines.append(f"- Run ID: {_format_value(run.get('run_id'))}")
    lines.append(f"- Status: {_format_value(run.get('status'))}")
    lines.append(f"- Updated At: {_format_value(run.get('updated_at'))}")
    lines.append("")

    if acceptance_warnings:
        lines.append("## Warnings")
        lines.append("- One or more artifacts are listed under artifacts.authoritative but are missing accepted_by/accepted_at (state will not validate).")
        for artifact in acceptance_warnings:
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"id: {_format_value(artifact.get('id'))}",
                        f"type: {_format_value(artifact.get('type'))}",
                        f"path: {_format_value(artifact.get('path'))}",
                        f"accepted_at: {_format_value(artifact.get('accepted_at'))}",
                        f"accepted_by: {_format_value(artifact.get('accepted_by'))}",
                    ]
                )
            )
        lines.append("")

    lines.append("## Current")
    lines.append(f"- Phase: {_format_value(current.get('phase'))}")
    lines.append(f"- Stage: {_format_value(current.get('stage'))}")
    lines.append(f"- Step: {_format_value(current.get('step'))}")
    lines.append(f"- Objective: {_format_value(current.get('objective'))}")
    lines.append("")

    lines.append("## Blockers")
    if not blockers:
        lines.append("- None")
    else:
        for blocker in blockers:
            question = _format_value(blocker.get("question"))
            owner = _format_value(blocker.get("owner"))
            ticket_id = blocker.get("ticket_id")
            ticket_part = f", ticket: {ticket_id}" if ticket_id else ""
            blocker_id = _format_value(blocker.get("id", "unknown"))
            default_value = _format_value((blocker.get("default") or {}).get("value"))
            answer = blocker.get("answer", {}) if isinstance(blocker.get("answer"), dict) else {}
            answer_status = _format_value(answer.get("status"))
            answer_value = _format_value(answer.get("value"))
            instructions = blocker.get("instructions")

            lines.append(f"- {blocker_id}: {question} (owner: {owner}{ticket_part})")
            if default_value != "Not set":
                lines.append(f"  - default: {default_value}")
            if answer_status != "Not set" or answer_value != "Not set":
                lines.append(f"  - answer: status={answer_status}, value={answer_value}")
            if instructions:
                lines.append("  - instructions:")
                lines.append("```text")
                lines.append(str(instructions).rstrip())
                lines.append("```")
    lines.append("")

    lines.append("## Next Step")
    if not next_step:
        lines.append("- None")
    else:
        next_type = _format_value(next_step.get("type") or "agent")
        lines.append(
            "- "
            + " | ".join(
                [
                    f"type: {next_type}",
                    f"id: {_format_value(next_step.get('id'))}",
                    f"agent: {_format_value(next_step.get('agent'))}",
                    f"inputs: {_format_value(next_step.get('inputs_required'))}",
                    f"outputs: {_format_value(next_step.get('outputs_expected'))}",
                ]
            )
        )
        next_prompt = next_step.get("prompt")
        if next_prompt:
            lines.append("- prompt:")
            lines.append("```text")
            lines.append(str(next_prompt).rstrip())
            lines.append("```")
    lines.append("")

    lines.append("## Queued Next Steps")
    if not queued_next_steps:
        lines.append("- None")
    else:
        for step in queued_next_steps:
            step_type = _format_value(step.get("type") or "agent")
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"type: {step_type}",
                        f"id: {_format_value(step.get('id'))}",
                        f"agent: {_format_value(step.get('agent'))}",
                        f"inputs: {_format_value(step.get('inputs_required'))}",
                        f"outputs: {_format_value(step.get('outputs_expected'))}",
                    ]
                )
            )
            step_prompt = step.get("prompt")
            if step_prompt:
                lines.append("  - prompt:")
                lines.append("```text")
                lines.append(str(step_prompt).rstrip())
                lines.append("```")
    lines.append("")

    lines.append("## Last Accepted Authoritative Artifact")
    if not last_artifact:
        lines.append("- None")
    else:
        lines.append(
            "- "
            + " | ".join(
                [
                    f"id: {_format_value(last_artifact.get('id'))}",
                    f"type: {_format_value(last_artifact.get('type'))}",
                    f"path: {_format_value(last_artifact.get('path'))}",
                    f"accepted_at: {_format_value(last_artifact.get('accepted_at'))}",
                    f"accepted_by: {_format_value(last_artifact.get('accepted_by'))}",
                ]
            )
        )
    lines.append("")

    lines.append("## Quality")
    lines.append("### Checks (fail/warn)")
    if not quality_issues:
        lines.append("- None")
    else:
        for check in quality_issues:
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"id: {_format_value(check.get('id'))}",
                        f"status: {_format_value(check.get('status'))}",
                        f"notes: {_format_value(check.get('notes'))}",
                    ]
                )
            )
    lines.append("### Risks")
    if not risks:
        lines.append("- None")
    else:
        for risk in risks:
            lines.append(
                "- "
                + " | ".join(
                    [
                        f"id: {_format_value(risk.get('id'))}",
                        f"risk: {_format_value(risk.get('risk'))}",
                        f"mitigation: {_format_value(risk.get('mitigation'))}",
                    ]
                )
            )
    lines.append("")

    lines.append("## Notes for Humans")
    lines.append(f"- {_format_value(provenance.get('notes_for_humans'))}")
    lines.append("")

    return "\n".join(lines)
