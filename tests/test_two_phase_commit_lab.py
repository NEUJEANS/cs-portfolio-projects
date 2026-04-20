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
SCENARIO_DIR = REPO_ROOT / "projects/two-phase-commit-lab"
SUCCESS_SCENARIO = SCENARIO_DIR / "order_success.json"
ABORT_SCENARIO = SCENARIO_DIR / "payment_validation_abort.json"
BLOCKED_SCENARIO = SCENARIO_DIR / "coordinator_crash_before_decision.json"
RECOVERY_SCENARIO = SCENARIO_DIR / "coordinator_recovery_commit.json"
PARTICIPANT_RECOVERY_SCENARIO = SCENARIO_DIR / "participant_reconnect_commit.json"
SPEC = importlib.util.spec_from_file_location("two_phase_commit_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
ScenarioError = MODULE.ScenarioError
build_catalog_entries = MODULE.build_catalog_entries
collect_scenario_paths = MODULE.collect_scenario_paths
load_scenario = MODULE.load_scenario
render_catalog_markdown = MODULE.render_catalog_markdown
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

    def test_validate_rejects_reconnect_without_missed_delivery(self) -> None:
        scenario = {
            "title": "bad",
            "description": "reconnect flag without a missed delivery should fail",
            "transaction_id": "tx-2",
            "participants": [
                {
                    "name": "inventory",
                    "vote": "commit",
                    "reconnect_after_missed_decision": True,
                }
            ],
        }
        with self.assertRaises(ScenarioError):
            validate_scenario(scenario)

    def test_validate_rejects_missed_second_phase_for_non_commit_vote(self) -> None:
        scenario = {
            "title": "bad",
            "description": "non-commit participants should not model missed decision delivery",
            "transaction_id": "tx-3",
            "participants": [
                {
                    "name": "risk",
                    "vote": "abort",
                    "second_phase_delivery": "miss",
                }
            ],
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

    def test_participant_reconnect_recovers_missed_commit(self) -> None:
        result = simulate_two_phase_commit(load_scenario(PARTICIPANT_RECOVERY_SCENARIO))
        self.assertEqual(result.outcome, "commit")
        self.assertEqual(result.decision, "commit")
        shipping = next(item for item in result.participants if item["name"] == "shipping")
        self.assertEqual(shipping["second_phase_delivery"], "miss")
        self.assertTrue(shipping["missed_second_phase_delivery"])
        self.assertTrue(shipping["recovered_after_reconnect"])
        self.assertEqual(shipping["state"], "committed")
        self.assertTrue(shipping["acked_decision"])
        self.assertIn("asks the coordinator to replay the durable decision", " ".join(result.trace))

    def test_markdown_report_mentions_blocking_reason(self) -> None:
        result = simulate_two_phase_commit(load_scenario(BLOCKED_SCENARIO))
        report = render_markdown_report(result)
        self.assertIn("final outcome: `blocked`", report)
        self.assertIn("blocking reason:", report)
        self.assertIn("Participant summary", report)
        self.assertIn("2nd-phase delivery", report)
        self.assertIn("coordinator starts 2PC", report)

    def test_collect_scenario_paths_from_directory_is_sorted(self) -> None:
        paths = collect_scenario_paths([SCENARIO_DIR])
        self.assertEqual(
            [path.name for path in paths],
            [
                "coordinator_crash_before_decision.json",
                "coordinator_recovery_commit.json",
                "order_success.json",
                "participant_reconnect_commit.json",
                "payment_validation_abort.json",
            ],
        )

    def test_render_catalog_markdown_summarizes_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            catalog_path = Path(temp_dir) / "scenario_catalog.md"
            report_dir = Path(temp_dir) / "reports"
            entries = build_catalog_entries(
                collect_scenario_paths([SCENARIO_DIR]),
                catalog_path=catalog_path,
                report_dir=report_dir,
            )
            catalog = render_catalog_markdown(entries)
            self.assertIn("# Two-phase commit scenario catalog", catalog)
            self.assertIn("- outcomes: `3 commit`, `1 abort`, `1 blocked`", catalog)
            self.assertIn("- participant reconnect recoveries: `1`", catalog)
            self.assertIn("| Scenario | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Report |", catalog)
            self.assertIn("[Order service happy-path commit](reports/order_success_report.md)", catalog)
            self.assertIn("description: Every participant votes YES and enters PREPARED", catalog)
            self.assertIn("participant reconnect recovery: `-` (no participant missed the first second-phase delivery)", catalog)
            self.assertIn("participant reconnect recovery: `1/1` recovered after missing the first second-phase delivery", catalog)
            self.assertIn("why it matters: 1 participant missed the first second-phase delivery, and 1 participant later recovered by reconnecting for the durable decision.", catalog)

    def test_catalog_command_writes_index_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir) / "reports"
            catalog_path = Path(temp_dir) / "scenario_catalog.md"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "catalog",
                    str(SCENARIO_DIR),
                    "--markdown-out",
                    str(catalog_path),
                    "--report-dir",
                    str(report_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertIn("wrote 5 scenario reports", completed.stdout)
            self.assertTrue((report_dir / "order_success_report.md").exists())
            self.assertTrue((report_dir / "coordinator_crash_before_decision_report.md").exists())
            self.assertTrue((report_dir / "participant_reconnect_commit_report.md").exists())
            catalog = catalog_path.read_text()
            self.assertIn("[report](reports/order_success_report.md)", catalog)
            self.assertIn("outcome: `blocked` with decision `none`", catalog)
            self.assertIn("Participant reconnect resolves a missed COMMIT", catalog)

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
