from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "projects/two-phase-commit-lab/two_phase_commit_lab.py"
SUCCESS_SCENARIO = REPO_ROOT / "projects/two-phase-commit-lab/order_success.json"
ABORT_SCENARIO = REPO_ROOT / "projects/two-phase-commit-lab/payment_validation_abort.json"
BLOCKED_SCENARIO = REPO_ROOT / "projects/two-phase-commit-lab/coordinator_crash_before_decision.json"
RECOVERY_SCENARIO = REPO_ROOT / "projects/two-phase-commit-lab/coordinator_recovery_commit.json"
SPEC = importlib.util.spec_from_file_location("two_phase_commit_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
ScenarioError = MODULE.ScenarioError
load_scenario = MODULE.load_scenario
render_markdown_report = MODULE.render_markdown_report
simulate_two_phase_commit = MODULE.simulate_two_phase_commit
validate_scenario = MODULE.validate_scenario


class TwoPhaseCommitLabTests(unittest.TestCase):
    def test_validate_rejects_duplicate_participants(self) -> None:
        scenario = {
            "title": "bad",
            "description": "duplicate names should fail",
            "transaction_id": "tx-1",
            "participants": [
                {"name": "inventory", "vote": "commit"},
                {"name": "inventory", "vote": "abort"},
            ],
        }
        with self.assertRaises(ScenarioError):
            validate_scenario(scenario)

    def test_validate_rejects_unknown_vote(self) -> None:
        scenario = {
            "title": "bad",
            "description": "unknown vote should fail",
            "transaction_id": "tx-1",
            "participants": [{"name": "inventory", "vote": "maybe"}],
        }
        with self.assertRaises(ScenarioError):
            validate_scenario(scenario)

    def test_happy_path_commits_every_prepared_participant(self) -> None:
        result = simulate_two_phase_commit(load_scenario(SUCCESS_SCENARIO))
        self.assertEqual(result.outcome, "commit")
        self.assertEqual(result.decision, "commit")
        self.assertTrue(result.decision_durable)
        self.assertEqual([item["state"] for item in result.participants], ["committed", "committed", "committed"])
        self.assertTrue(all(item["acked_decision"] for item in result.participants))
        self.assertIn("durable COMMIT decision", " ".join(result.takeaways))

    def test_abort_vote_forces_global_abort(self) -> None:
        result = simulate_two_phase_commit(load_scenario(ABORT_SCENARIO))
        self.assertEqual(result.outcome, "abort")
        self.assertEqual(result.decision, "abort")
        self.assertEqual(
            [item["state"] for item in result.participants],
            ["aborted", "aborted", "aborted"],
        )
        self.assertTrue(any("global abort" in entry for entry in result.trace))

    def test_crash_before_decision_blocks_prepared_participants(self) -> None:
        result = simulate_two_phase_commit(load_scenario(BLOCKED_SCENARIO))
        self.assertEqual(result.outcome, "blocked")
        self.assertIsNone(result.decision)
        self.assertFalse(result.decision_durable)
        self.assertTrue(all(item["state"] == "prepared" for item in result.participants))
        self.assertIn("remain blocked", result.blocking_reason)

    def test_recovery_replays_durable_commit(self) -> None:
        result = simulate_two_phase_commit(load_scenario(RECOVERY_SCENARIO))
        self.assertEqual(result.outcome, "commit")
        self.assertEqual(result.decision, "commit")
        self.assertTrue(result.decision_durable)
        self.assertEqual([item["state"] for item in result.participants], ["committed", "committed", "committed"])
        self.assertIn("replays the durable decision log", " ".join(result.trace))

    def test_markdown_report_mentions_blocking_reason(self) -> None:
        result = simulate_two_phase_commit(load_scenario(BLOCKED_SCENARIO))
        report = render_markdown_report(result)
        self.assertIn("final outcome: `blocked`", report)
        self.assertIn("blocking reason:", report)
        self.assertIn("Participant summary", report)
        self.assertIn("coordinator starts 2PC", report)

    def test_cli_json_output_and_markdown_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "order_success_report.md"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "run",
                    str(SUCCESS_SCENARIO),
                    "--markdown-out",
                    str(report_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            stdout = completed.stdout
            payload = json.loads(stdout)
            self.assertEqual(payload["outcome"], "commit")
            self.assertEqual(payload["participants"][0]["state"], "committed")
            report = report_path.read_text()
            self.assertIn("Order service happy-path commit", report)
            self.assertIn("final outcome: `commit`", report)

    def test_validate_command_succeeds_for_recovery_scenario(self) -> None:
        completed = subprocess.run(
            ["python3", str(SCRIPT), "validate", str(RECOVERY_SCENARIO)],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertIn("Recovery replays a durable commit", completed.stdout)


if __name__ == "__main__":
    unittest.main()
