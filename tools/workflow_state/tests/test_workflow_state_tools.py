import importlib.machinery
import importlib.util
import os
import sys
import tempfile
import unittest
from unittest import mock


class WorkflowStateToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow_state_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        sys.path.insert(0, cls.workflow_state_dir)

        approve_path = os.path.join(cls.workflow_state_dir, "approve")
        loader = importlib.machinery.SourceFileLoader("approve_tool", approve_path)
        spec = importlib.util.spec_from_loader("approve_tool", loader)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to create module spec for approve tool at {approve_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.approve = module

        from views import md as md_view  # noqa: E402

        cls.md_view = md_view

    def test_md_renders_queued_next_steps(self) -> None:
        state = {
            "workflow": {"name": "agentic-dev", "version": "0.1.0"},
            "run": {
                "run_id": "test-001",
                "status": "blocked",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
            "current": {"phase": "stage-1", "stage": "requirements-draft", "step": "draft", "objective": "test"},
            "progress": {
                "completed_steps": [],
                "next_steps": [
                    {
                        "id": "stage-1-requirements-approval",
                        "agent": "Human sponsor",
                        "type": "human",
                        "inputs_required": ["artifacts/requirements/requirements.md"],
                        "outputs_expected": ["approval recorded in workflow_state.json"],
                        "prompt": "Run approve tool",
                    },
                    {
                        "id": "stage-2-ticket-drafting",
                        "agent": "Ticket Writer",
                        "type": "agent",
                        "inputs_required": ["artifacts/workflow_state.json"],
                        "outputs_expected": ["artifacts/tickets/tickets.yaml"],
                        "prompt": "Act as Ticket Writer",
                    },
                ],
            },
            "artifacts": {"authoritative": [], "provisional": []},
            "inputs": {"locked": [], "open_questions": []},
            "quality": {"checks": [], "risks": []},
            "provenance": {"last_actor": "tester", "last_action": "test", "notes_for_humans": "n/a"},
        }

        output = self.md_view.render(state)
        self.assertIn("## Queued Next Steps", output)
        self.assertIn("stage-2-ticket-drafting", output)
        self.assertIn("Act as Ticket Writer", output)

    def test_approve_suggest_next_step_accepts_dotted_gate_id(self) -> None:
        suggestion = self.approve._suggest_next_step("stage-1.requirements-approval")
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion["id"], "stage-2-ticket-drafting")

    def test_approve_suggest_next_step_accepts_stage2_tickets_alias(self) -> None:
        suggestion = self.approve._suggest_next_step("stage-2.tickets-approval")
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion["id"], "stage-4-test-plan")

    def test_approve_infers_gate_from_approved_artifacts(self) -> None:
        gate_id = self.approve._infer_gate_step_id_from_approved_artifacts(
            [{"id": "requirements-001", "type": "requirements", "path": "artifacts/requirements/requirements.md"}]
        )
        self.assertEqual(gate_id, "stage-1-requirements-approval")

    def test_approve_repairs_open_questions_for_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = tmpdir
            artifacts_dir = os.path.join(project_root, "artifacts")
            tickets_dir = os.path.join(artifacts_dir, "tickets")
            os.makedirs(tickets_dir, exist_ok=True)

            tickets_path = os.path.join(tickets_dir, "tickets.yaml")
            with open(tickets_path, "w", encoding="utf-8") as handle:
                handle.write("tickets: []\n")

            state_path = os.path.join(artifacts_dir, "workflow_state.json")
            state = {
                "workflow": {"name": "agentic-dev", "version": "0.1.0"},
                "run": {
                    "run_id": "test-approve-001",
                    "status": "blocked",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                },
                "current": {"phase": "stage-2", "stage": "tickets", "step": "gate", "objective": "test"},
                "progress": {
                    "completed_steps": [],
                    "next_steps": [
                        {
                            "id": "stage-2.tickets-approval",
                            "agent": "human",
                            "type": "human",
                            "inputs_required": ["artifacts/tickets/tickets.yaml", "artifacts/workflow_state.json"],
                            "outputs_expected": ["artifacts/workflow_state.json"],
                            "prompt": "Approve tickets",
                        },
                        {
                            "id": "stage-3.jira-sync",
                            "agent": "ticket-writer",
                            "type": "agent",
                            "status": "pending",
                            "inputs_required": ["artifacts/tickets/tickets.yaml", "artifacts/workflow_state.json"],
                            "outputs_expected": ["artifacts/tickets/tickets.yaml", "artifacts/workflow_state.json"],
                            "prompt": "Do Jira sync (dry-run)",
                        },
                    ],
                },
                "artifacts": {
                    "authoritative": [],
                    "provisional": [
                        {
                            "id": "tickets-001",
                            "type": "tickets",
                            "path": "artifacts/tickets/tickets.yaml",
                            "status": "draft",
                            "produced_by": "ticket-writer",
                        }
                    ],
                },
                "inputs": {
                    "locked": [],
                    # Missing required schema keys owner/blocking/status.
                    "open_questions": [
                        {
                            "id": "approval-1",
                            "title": "Approve tickets.yaml",
                            "question": "Approve artifacts/tickets/tickets.yaml?",
                            "answer": {"value": None},
                        }
                    ],
                },
                "quality": {"checks": [], "risks": []},
                "provenance": {"last_actor": "tester", "last_action": "seed", "notes_for_humans": "n/a"},
            }
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            import json

            with open(state_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2)
                handle.write("\n")

            inputs = iter(
                [
                    state_path,  # Workflow state path
                    "",  # Select artifact(s) (default 1)
                    "",  # accepted_by (default)
                    "",  # accepted_at (default)
                    "",  # Mark gate step completed (default Y)
                ]
            )

            with mock.patch("builtins.input", side_effect=lambda _: next(inputs)):
                rc = self.approve.main(["approve"])
            self.assertEqual(rc, 0)

            with open(state_path, "r", encoding="utf-8") as handle:
                repaired = json.load(handle)
            oq = repaired["inputs"]["open_questions"][0]
            self.assertIn("owner", oq)
            self.assertIsInstance(oq.get("blocking"), bool)
            self.assertEqual(oq.get("status"), "resolved")
            self.assertFalse(oq.get("blocking"))

    def test_approve_can_accept_stale_authoritative_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = tmpdir
            artifacts_dir = os.path.join(project_root, "artifacts")
            os.makedirs(artifacts_dir, exist_ok=True)

            merge_dir = os.path.join(artifacts_dir, "integration")
            os.makedirs(merge_dir, exist_ok=True)
            merge_summary_path = os.path.join(merge_dir, "merge-summary.md")
            with open(merge_summary_path, "w", encoding="utf-8") as handle:
                handle.write("# Merge Summary\n")

            state_path = os.path.join(artifacts_dir, "workflow_state.json")
            state = {
                "workflow": {"name": "agentic-dev", "version": "0.1.0"},
                "run": {
                    "run_id": "test-approve-002",
                    "status": "in_progress",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                },
                "current": {"phase": "stage-8", "stage": "integration", "step": "prep", "objective": "test"},
                "progress": {"completed_steps": [], "next_steps": []},
                "artifacts": {
                    "authoritative": [
                        {
                            "id": "integration-001",
                            "type": "integration-summary",
                            "path": "artifacts/integration/merge-summary.md",
                            "status": "draft",
                            "produced_by": "integrator",
                            "hash": "",
                        }
                    ],
                    "provisional": [],
                },
                "inputs": {"locked": [], "open_questions": []},
                "quality": {"checks": [], "risks": []},
                "provenance": {"last_actor": "tester", "last_action": "seed", "notes_for_humans": "n/a"},
            }

            import json

            with open(state_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2)
                handle.write("\n")

            inputs = iter(
                [
                    state_path,  # Workflow state path
                    "",  # Approve stale authoritative in place? (default Y)
                    "",  # Select artifact(s) (default 1)
                    "",  # accepted_by (default)
                    "",  # accepted_at (default)
                ]
            )

            with mock.patch("builtins.input", side_effect=lambda _: next(inputs)):
                rc = self.approve.main(["approve"])
            self.assertEqual(rc, 0)

            with open(state_path, "r", encoding="utf-8") as handle:
                repaired = json.load(handle)

            auth = repaired["artifacts"]["authoritative"]
            self.assertEqual(len(auth), 1, "Should not duplicate already-authoritative artifacts")
            self.assertTrue(auth[0].get("accepted_by"))
            self.assertTrue(auth[0].get("accepted_at"))


if __name__ == "__main__":
    unittest.main()
