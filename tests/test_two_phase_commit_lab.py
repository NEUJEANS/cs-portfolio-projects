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
PARTIAL_DELIVERY_BLOCKED_SCENARIO = (
    SCENARIO_DIR / "coordinator_crash_partial_commit_delivery.json"
)
ABORT_BLOCKED_SCENARIO = SCENARIO_DIR / "coordinator_crash_durable_abort.json"
RECOVERY_SCENARIO = SCENARIO_DIR / "coordinator_recovery_commit.json"
PARTICIPANT_RECOVERY_SCENARIO = SCENARIO_DIR / "participant_reconnect_commit.json"
SPEC = importlib.util.spec_from_file_location("two_phase_commit_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
ScenarioError = MODULE.ScenarioError
build_catalog_entries = MODULE.build_catalog_entries
build_peer_termination_resolution = MODULE.build_peer_termination_resolution
build_protocol_comparison = MODULE.build_protocol_comparison
collect_scenario_paths = MODULE.collect_scenario_paths
load_scenario = MODULE.load_scenario
render_catalog_markdown = MODULE.render_catalog_markdown
render_comparison_html = MODULE.render_comparison_html
render_comparison_markdown = MODULE.render_comparison_markdown
render_incident_response_html = MODULE.render_incident_response_html
render_markdown_report = MODULE.render_markdown_report
render_termination_resolution_markdown = MODULE.render_termination_resolution_markdown
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

    def test_validate_rejects_partial_deliveries_without_after_decision_crash(self) -> None:
        scenario = {
            "title": "bad",
            "description": "partial delivery metadata should be tied to post-log crashes",
            "transaction_id": "tx-4",
            "participants": [
                {"name": "inventory", "vote": "commit"},
                {"name": "billing", "vote": "commit"},
            ],
            "failures": {
                "coordinator_crash": "before-decision",
                "decision_deliveries_before_crash": 1,
            },
        }
        with self.assertRaises(ScenarioError):
            validate_scenario(scenario)

    def test_validate_rejects_too_many_pre_crash_deliveries(self) -> None:
        scenario = {
            "title": "bad",
            "description": "cannot deliver to more prepared peers than exist",
            "transaction_id": "tx-5",
            "participants": [
                {"name": "inventory", "vote": "commit"},
                {"name": "billing", "vote": "abort"},
            ],
            "failures": {
                "coordinator_crash": "after-decision-log",
                "decision_deliveries_before_crash": 2,
            },
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
        self.assertIsNone(result.termination_hint_summary)

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
        self.assertEqual(result.termination_hint_summary, "wait: all prepared peers are still uncertain")

    def test_partial_commit_delivery_exposes_peer_visible_termination_hint(self) -> None:
        result = simulate_two_phase_commit(load_scenario(PARTIAL_DELIVERY_BLOCKED_SCENARIO))
        self.assertEqual(result.outcome, "blocked")
        self.assertEqual(result.decision, "commit")
        self.assertTrue(result.decision_durable)
        inventory = next(item for item in result.participants if item["name"] == "inventory")
        billing = next(item for item in result.participants if item["name"] == "billing")
        shipping = next(item for item in result.participants if item["name"] == "shipping")
        self.assertEqual(inventory["state"], "committed")
        self.assertTrue(inventory["acked_decision"])
        self.assertEqual(billing["state"], "prepared")
        self.assertEqual(shipping["state"], "prepared")
        self.assertEqual(result.failures["successful_decision_deliveries_before_crash"], 1)
        self.assertEqual(result.termination_hint_summary, "COMMIT visible via inventory")
        self.assertIn("relay it to billing and shipping", " ".join(result.termination_hints))

    def test_pre_crash_missed_delivery_does_not_count_as_successful_delivery(self) -> None:
        scenario = validate_scenario(
            {
                "title": "Crash after missed commit fanout",
                "description": "Both prepared peers miss the first COMMIT before the coordinator crashes.",
                "transaction_id": "tx-missed-1",
                "participants": [
                    {
                        "name": "inventory",
                        "vote": "commit",
                        "second_phase_delivery": "miss",
                    },
                    {
                        "name": "billing",
                        "vote": "commit",
                        "second_phase_delivery": "miss",
                    },
                ],
                "failures": {
                    "coordinator_crash": "after-decision-log",
                    "decision_deliveries_before_crash": 1,
                },
            }
        )
        result = simulate_two_phase_commit(scenario)
        self.assertEqual(result.outcome, "blocked")
        self.assertEqual(result.decision, "commit")
        self.assertEqual(result.failures["decision_deliveries_before_crash"], 1)
        self.assertEqual(result.failures["successful_decision_deliveries_before_crash"], 0)
        self.assertEqual(
            result.termination_hint_summary,
            "wait: durable COMMIT exists but no peer can prove it yet",
        )

    def test_peer_termination_resolution_commits_after_partial_delivery_block(self) -> None:
        result = build_peer_termination_resolution(
            load_scenario(PARTIAL_DELIVERY_BLOCKED_SCENARIO)
        )
        self.assertEqual(result.baseline_outcome, "blocked")
        self.assertEqual(result.baseline_decision, "commit")
        self.assertEqual(result.resolution_outcome, "commit")
        self.assertEqual(result.resolved_decision, "commit")
        self.assertEqual(result.unresolved_participants, [])
        billing = next(item for item in result.participants if item.participant == "billing")
        shipping = next(item for item in result.participants if item.participant == "shipping")
        self.assertEqual(billing.final_state, "committed")
        self.assertEqual(shipping.final_state, "committed")
        self.assertTrue(all(item.resolved for item in result.participants))
        self.assertIn("learns COMMIT", " ".join(result.trace))

    def test_peer_termination_resolution_stays_blocked_without_decisive_peer(self) -> None:
        result = build_peer_termination_resolution(load_scenario(BLOCKED_SCENARIO))
        self.assertEqual(result.baseline_outcome, "blocked")
        self.assertEqual(result.resolution_outcome, "still-blocked")
        self.assertEqual(result.resolved_decision, None)
        self.assertEqual(sorted(result.unresolved_participants), ["billing", "inventory", "shipping"])
        self.assertTrue(
            any(
                not item.resolved and item.final_state == "prepared"
                for item in result.participants
            )
        )

    def test_blocked_abort_exposes_safe_peer_resolution_hint(self) -> None:
        result = simulate_two_phase_commit(load_scenario(ABORT_BLOCKED_SCENARIO))
        self.assertEqual(result.outcome, "blocked")
        self.assertEqual(result.decision, "abort")
        self.assertTrue(result.decision_durable)
        self.assertEqual(result.termination_hint_summary, "ABORT safe via risk")
        self.assertIn("never reached PREPARED", " ".join(result.termination_hints))

    def test_peer_termination_resolution_aborts_via_non_prepared_peer(self) -> None:
        result = build_peer_termination_resolution(load_scenario(ABORT_BLOCKED_SCENARIO))
        self.assertEqual(result.baseline_outcome, "blocked")
        self.assertEqual(result.baseline_decision, "abort")
        self.assertEqual(result.resolution_outcome, "abort")
        self.assertEqual(result.resolved_decision, "abort")
        self.assertEqual(result.unresolved_participants, [])
        inventory = next(item for item in result.participants if item.participant == "inventory")
        billing = next(item for item in result.participants if item.participant == "billing")
        self.assertEqual(inventory.final_state, "aborted")
        self.assertEqual(billing.final_state, "aborted")
        self.assertIn("proves ABORT safely", " ".join(result.trace))

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

    def test_markdown_report_mentions_blocking_reason_and_termination_hints(self) -> None:
        result = simulate_two_phase_commit(load_scenario(PARTIAL_DELIVERY_BLOCKED_SCENARIO))
        report = render_markdown_report(result)
        self.assertIn("final outcome: `blocked`", report)
        self.assertIn("blocking reason:", report)
        self.assertIn("termination hint summary: COMMIT visible via inventory", report)
        self.assertIn("## Termination protocol hints", report)
        self.assertIn("inventory already knows `COMMIT`", report)

    def test_collect_scenario_paths_from_directory_is_sorted(self) -> None:
        paths = collect_scenario_paths([SCENARIO_DIR])
        self.assertEqual(
            [path.name for path in paths],
            [
                "coordinator_crash_before_decision.json",
                "coordinator_crash_durable_abort.json",
                "coordinator_crash_partial_commit_delivery.json",
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
            self.assertIn("- outcomes: `3 commit`, `1 abort`, `3 blocked`", catalog)
            self.assertIn("- participant reconnect recoveries: `1`", catalog)
            self.assertIn("- blocked scenarios with actionable peer hints: `2`", catalog)
            self.assertIn("- scenarios with protocol-comparison dashboards: `0`", catalog)
            self.assertIn("- scenarios with peer-termination walkthroughs: `0`", catalog)
            self.assertIn("| Scenario | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Termination hint | Report | Compare | Termination |", catalog)
            self.assertIn("[Coordinator crash after one COMMIT delivery](reports/coordinator_crash_partial_commit_delivery_report.md)", catalog)
            self.assertIn("termination hint: COMMIT visible via inventory", catalog)
            self.assertIn("termination hint: ABORT safe via risk", catalog)
            self.assertIn("blocked does not always mean blind waiting: COMMIT visible via inventory.", catalog)

    def test_catalog_detects_related_compare_and_termination_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            catalog_path = Path(temp_dir) / "scenario_catalog.md"
            report_dir = Path(temp_dir) / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            (report_dir / "coordinator_crash_partial_commit_delivery_protocol_compare.html").write_text("<html></html>")
            (report_dir / "coordinator_crash_partial_commit_delivery_protocol_compare.md").write_text("# compare")
            (report_dir / "coordinator_crash_partial_commit_delivery_termination.md").write_text("# termination")
            entries = build_catalog_entries(
                [PARTIAL_DELIVERY_BLOCKED_SCENARIO],
                catalog_path=catalog_path,
                report_dir=report_dir,
            )
            catalog = render_catalog_markdown(entries)
            self.assertIn("- scenarios with protocol-comparison dashboards: `1`", catalog)
            self.assertIn("- scenarios with peer-termination walkthroughs: `1`", catalog)
            self.assertIn("[html](reports/coordinator_crash_partial_commit_delivery_protocol_compare.html)", catalog)
            self.assertIn("[md](reports/coordinator_crash_partial_commit_delivery_protocol_compare.md)", catalog)
            self.assertIn("[md](reports/coordinator_crash_partial_commit_delivery_termination.md)", catalog)
            self.assertIn("related artifacts: [report](reports/coordinator_crash_partial_commit_delivery_report.md) / [compare html](reports/coordinator_crash_partial_commit_delivery_protocol_compare.html) / [compare md](reports/coordinator_crash_partial_commit_delivery_protocol_compare.md) / [termination md](reports/coordinator_crash_partial_commit_delivery_termination.md)", catalog)

    def test_incident_response_dashboard_groups_blocked_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            catalog_path = Path(temp_dir) / "scenario_catalog.md"
            report_dir = Path(temp_dir) / "reports"
            entries = build_catalog_entries(
                collect_scenario_paths([SCENARIO_DIR]),
                catalog_path=catalog_path,
                report_dir=report_dir,
            )
            dashboard = render_incident_response_html(
                entries,
                catalog_markdown_path="scenario_catalog.md",
            )
            self.assertIn("Blocked-case triage at a glance", dashboard)
            self.assertIn("Recovery-required / still blocked", dashboard)
            self.assertIn("Peer-visible COMMIT evidence", dashboard)
            self.assertIn("Safe-ABORT evidence", dashboard)
            self.assertIn("Coordinator crash before durable decision", dashboard)
            self.assertIn("Coordinator crash after one COMMIT delivery", dashboard)
            self.assertIn("Coordinator crash after durable ABORT", dashboard)
            self.assertIn('href="scenario_catalog.md"', dashboard)
            self.assertIn('href="reports/coordinator_crash_before_decision_report.md"', dashboard)
            self.assertIn('href="reports/coordinator_crash_partial_commit_delivery_report.md"', dashboard)
            self.assertIn('href="reports/coordinator_crash_durable_abort_report.md"', dashboard)

    def test_catalog_command_writes_index_and_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_dir = Path(temp_dir) / "reports"
            catalog_path = Path(temp_dir) / "scenario_catalog.md"
            dashboard_path = Path(temp_dir) / "incident_response_dashboard.html"
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
            self.assertIn("wrote 7 scenario reports", completed.stdout)
            self.assertIn("wrote incident-response dashboard", completed.stdout)
            self.assertTrue(dashboard_path.exists())
            self.assertTrue((report_dir / "order_success_report.md").exists())
            self.assertTrue((report_dir / "coordinator_crash_before_decision_report.md").exists())
            self.assertTrue((report_dir / "coordinator_crash_durable_abort_report.md").exists())
            self.assertTrue((report_dir / "coordinator_crash_partial_commit_delivery_report.md").exists())
            self.assertTrue((report_dir / "participant_reconnect_commit_report.md").exists())
            catalog = catalog_path.read_text()
            dashboard = dashboard_path.read_text()
            self.assertIn("[incident-response dashboard](incident_response_dashboard.html)", catalog)
            self.assertIn("[report](reports/order_success_report.md)", catalog)
            self.assertIn("outcome: `blocked` with decision `commit`", catalog)
            self.assertIn("outcome: `blocked` with decision `abort`", catalog)
            self.assertIn("termination hint: COMMIT visible via inventory", catalog)
            self.assertIn("termination hint: ABORT safe via risk", catalog)
            self.assertIn("Peer-visible COMMIT evidence", dashboard)
            self.assertIn("Safe-ABORT evidence", dashboard)

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
            self.assertIsNone(payload["termination_hint_summary"])
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

    def test_protocol_comparison_calls_out_blocking_vs_saga_pause(self) -> None:
        comparison = build_protocol_comparison(load_scenario(BLOCKED_SCENARIO))
        self.assertEqual(comparison.scenario_snapshot["two_phase_outcome"], "blocked")
        self.assertEqual([item.protocol for item in comparison.comparisons], ["2PC", "Saga (orchestrated)"])
        two_pc = comparison.comparisons[0]
        saga = comparison.comparisons[1]
        self.assertEqual(two_pc.outcome, "blocked")
        self.assertIn("PREPARED participants", two_pc.blocking_behavior)
        self.assertEqual(saga.outcome, "paused-not-blocked")
        self.assertIn("do not sit on PREPARED locks", saga.blocking_behavior)

    def test_protocol_comparison_snapshot_tracks_peer_visible_commit_hints(self) -> None:
        comparison = build_protocol_comparison(load_scenario(PARTIAL_DELIVERY_BLOCKED_SCENARIO))
        snapshot = comparison.scenario_snapshot
        self.assertEqual(snapshot["two_phase_outcome"], "blocked")
        self.assertEqual(snapshot["successful_decision_deliveries_before_crash"], 1)
        self.assertEqual(snapshot["acked_decision_count"], 1)
        self.assertEqual(snapshot["acked_decision_participants"], ["inventory"])
        self.assertEqual(snapshot["termination_hint_summary"], "COMMIT visible via inventory")
        self.assertTrue(
            any(
                "peer-assisted incident-response story rather than pure blind waiting" in entry
                for entry in comparison.interview_takeaways
            )
        )

    def test_comparison_markdown_mentions_protocol_contrast(self) -> None:
        comparison = build_protocol_comparison(load_scenario(BLOCKED_SCENARIO))
        report = render_comparison_markdown(comparison)
        self.assertIn("# Coordinator crash before durable decision protocol comparison", report)
        self.assertIn("## Protocol contrast", report)
        self.assertIn("| 2PC | `blocked` |", report)
        self.assertIn("| Saga (orchestrated) | `paused-not-blocked` |", report)
        self.assertIn("resumable workflow state instead of coordinator-driven prepared-lock blocking", report)

    def test_comparison_markdown_exposes_peer_visible_commit_details(self) -> None:
        comparison = build_protocol_comparison(load_scenario(PARTIAL_DELIVERY_BLOCKED_SCENARIO))
        report = render_comparison_markdown(comparison)
        self.assertIn("participants that learned the final 2PC decision: `1` (inventory)", report)
        self.assertIn("successful second-phase deliveries before the crash: `1`", report)
        self.assertIn("termination hint in the 2PC baseline: COMMIT visible via inventory", report)
        self.assertIn("ask an informed peer instead of inventing a local outcome", report)

    def test_comparison_html_dashboard_surfaces_snapshot_and_takeaways(self) -> None:
        comparison = build_protocol_comparison(load_scenario(PARTIAL_DELIVERY_BLOCKED_SCENARIO))
        report = render_comparison_html(comparison)
        self.assertIn('<!doctype html>', report.lower())
        self.assertIn('Protocol comparison dashboard', report)
        self.assertIn('COMMIT visible via inventory', report)
        self.assertIn('inventory already knows the final 2PC outcome.', report)
        self.assertIn('paused-not-blocked', report)
        self.assertIn('peer-assisted incident-response story rather than pure blind waiting', report)

    def test_termination_resolution_markdown_tracks_peer_actions(self) -> None:
        resolution = build_peer_termination_resolution(
            load_scenario(PARTIAL_DELIVERY_BLOCKED_SCENARIO)
        )
        report = render_termination_resolution_markdown(resolution)
        self.assertIn("# Coordinator crash after one COMMIT delivery peer-to-peer termination resolution", report)
        self.assertIn("- baseline outcome: `blocked`", report)
        self.assertIn("- resolution outcome: `commit`", report)
        self.assertIn("ask inventory for the final decision", report)
        self.assertIn("learns COMMIT", report)

    def test_compare_command_writes_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "comparison.md"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "compare",
                    str(BLOCKED_SCENARIO),
                    "--markdown-out",
                    str(report_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["scenario_snapshot"]["two_phase_outcome"], "blocked")
            self.assertEqual(len(payload["comparisons"]), 2)
            self.assertEqual(payload["comparisons"][1]["protocol"], "Saga (orchestrated)")
            report = report_path.read_text()
            self.assertIn("## Interview takeaways", report)
            self.assertIn("Saga (orchestrated)", report)

    def test_compare_command_writes_markdown_html_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / 'comparison.md'
            html_path = Path(temp_dir) / 'comparison.html'
            completed = subprocess.run(
                [
                    'python3',
                    str(SCRIPT),
                    'compare',
                    str(PARTIAL_DELIVERY_BLOCKED_SCENARIO),
                    '--markdown-out',
                    str(report_path),
                    '--html-out',
                    str(html_path),
                    '--json',
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['scenario_snapshot']['termination_hint_summary'], 'COMMIT visible via inventory')
            html = html_path.read_text()
            self.assertIn('Protocol comparison dashboard', html)
            self.assertIn('Coordinator crash after one COMMIT delivery', html)
            self.assertIn('COMMIT visible via inventory', html)
            self.assertIn('inventory already knows the final 2PC outcome.', html)
            self.assertTrue(report_path.exists())

    def test_terminate_command_writes_markdown_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "termination.md"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "terminate",
                    str(PARTIAL_DELIVERY_BLOCKED_SCENARIO),
                    "--markdown-out",
                    str(report_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["baseline_outcome"], "blocked")
            self.assertEqual(payload["resolution_outcome"], "commit")
            report = report_path.read_text()
            self.assertIn("## Participant actions", report)
            self.assertIn("resolved decision: `commit`", report)

    def test_terminate_command_summary_mentions_resolved_decision(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "terminate",
                str(PARTIAL_DELIVERY_BLOCKED_SCENARIO),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertIn("peer_resolution=commit", completed.stdout)
        self.assertIn("resolved_decision=commit", completed.stdout)


if __name__ == "__main__":
    unittest.main()
