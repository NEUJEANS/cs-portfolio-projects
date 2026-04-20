from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTOR_SCENARIO = REPO_ROOT / "projects/mvcc-isolation-lab/doctor_on_call.json"
REPEATABLE_SCENARIO = REPO_ROOT / "projects/mvcc-isolation-lab/repeatable_read_window.json"
PHANTOM_SCENARIO = REPO_ROOT / "projects/mvcc-isolation-lab/conference_room_booking_phantom.json"
SCRIPT = REPO_ROOT / "projects/mvcc-isolation-lab/mvcc_isolation_lab.py"
SPEC = importlib.util.spec_from_file_location("mvcc_isolation_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
ScenarioError = MODULE.ScenarioError
compare_scenario = MODULE.compare_scenario
load_scenario = MODULE.load_scenario
run_simulation = MODULE.run_simulation
render_timeline_svg = MODULE.render_timeline_svg
validate_scenario = MODULE.validate_scenario


class MvccIsolationLabTests(unittest.TestCase):
    def test_validate_rejects_duplicate_transaction_names(self) -> None:
        scenario = {
            "records": {"x": 1},
            "transactions": [
                {"name": "T1", "steps": [{"op": "read", "key": "x"}]},
                {"name": "T1", "steps": [{"op": "read", "key": "x"}]},
            ],
            "schedule": ["T1"],
        }
        with self.assertRaises(ScenarioError):
            validate_scenario(scenario)

    def test_validate_rejects_unknown_schedule_entry(self) -> None:
        scenario = {
            "records": {"x": 1},
            "transactions": [{"name": "T1", "steps": [{"op": "read", "key": "x"}]}],
            "schedule": ["T2"],
        }
        with self.assertRaises(ScenarioError):
            validate_scenario(scenario)

    def test_validate_rejects_scan_without_alias(self) -> None:
        scenario = {
            "records": {"capacity": 1},
            "transactions": [
                {
                    "name": "T1",
                    "steps": [{"op": "scan", "key_prefix": "booking_"}],
                }
            ],
            "schedule": ["T1"],
        }
        with self.assertRaises(ScenarioError):
            validate_scenario(scenario)

    def test_snapshot_allows_write_skew_in_doctor_scenario(self) -> None:
        result = run_simulation(load_scenario(DOCTOR_SCENARIO), "snapshot")
        self.assertEqual(result.final_state, {"alice_on_call": False, "bob_on_call": False})
        self.assertEqual([item["status"] for item in result.transactions], ["committed", "committed"])
        self.assertFalse(result.invariants[0]["ok"])

    def test_serializable_aborts_second_writer_in_doctor_scenario(self) -> None:
        result = run_simulation(load_scenario(DOCTOR_SCENARIO), "serializable")
        self.assertEqual(result.final_state, {"alice_on_call": False, "bob_on_call": True})
        self.assertEqual([item["status"] for item in result.transactions], ["committed", "aborted"])
        self.assertTrue(result.invariants[0]["ok"])
        self.assertIn("alice_on_call", result.transactions[1]["abort_reason"])

    def test_read_committed_breaks_repeatable_read_expectation(self) -> None:
        result = run_simulation(load_scenario(REPEATABLE_SCENARIO), "read-committed")
        reader, writer = result.transactions
        self.assertEqual(reader["status"], "aborted")
        self.assertEqual(writer["status"], "committed")
        self.assertEqual(result.final_state, {"inventory": 8})

    def test_snapshot_keeps_repeatable_read_stable(self) -> None:
        result = run_simulation(load_scenario(REPEATABLE_SCENARIO), "snapshot")
        reader, writer = result.transactions
        self.assertEqual(reader["status"], "committed")
        self.assertEqual(writer["status"], "committed")
        self.assertEqual(result.final_state, {"inventory": 8})
        self.assertTrue(all(item["ok"] for item in result.invariants))

    def test_serializable_repeatable_read_scenario_aborts_reader_at_validation(self) -> None:
        result = run_simulation(load_scenario(REPEATABLE_SCENARIO), "serializable")
        reader, writer = result.transactions
        self.assertEqual(reader["status"], "aborted")
        self.assertIn("inventory", reader["abort_reason"])
        self.assertEqual(writer["status"], "committed")
        self.assertEqual(result.final_state, {"inventory": 8})

    def test_read_committed_allows_predicate_phantom_double_booking(self) -> None:
        result = run_simulation(load_scenario(PHANTOM_SCENARIO), "read-committed")
        self.assertEqual([item["status"] for item in result.transactions], ["committed", "committed"])
        self.assertFalse(result.invariants[0]["ok"])
        self.assertEqual(
            result.final_state,
            {
                "booking_room101_2026-04-20T09:00_alice": "reserved",
                "booking_room101_2026-04-20T09:00_bob": "reserved",
                "room101_capacity": 1,
            },
        )

    def test_snapshot_allows_predicate_phantom_double_booking(self) -> None:
        result = run_simulation(load_scenario(PHANTOM_SCENARIO), "snapshot")
        self.assertEqual([item["status"] for item in result.transactions], ["committed", "committed"])
        self.assertFalse(result.invariants[0]["ok"])

    def test_serializable_aborts_second_booking_on_predicate_conflict(self) -> None:
        result = run_simulation(load_scenario(PHANTOM_SCENARIO), "serializable")
        self.assertEqual([item["status"] for item in result.transactions], ["committed", "aborted"])
        self.assertTrue(result.invariants[0]["ok"])
        self.assertIn("predicate conflict", result.transactions[1]["abort_reason"])
        self.assertEqual(
            result.transactions[0]["predicate_reads"],
            ['prefix=booking_room101_2026-04-20T09:00_, value="reserved"'],
        )

    def test_compare_runs_all_supported_modes(self) -> None:
        results = compare_scenario(load_scenario(DOCTOR_SCENARIO))
        self.assertEqual(set(results), {"read-committed", "snapshot", "serializable"})
        self.assertEqual(results["serializable"].final_state["bob_on_call"], True)

    def test_compare_markdown_export_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "doctor.md"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "compare",
                    str(DOCTOR_SCENARIO),
                    "--markdown-out",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertIn("MVCC isolation comparison", completed.stdout)
            report = output_path.read_text()
            self.assertIn("Doctor on-call write skew", report)
            self.assertIn("Two doctors each see coverage in their snapshot", report)
            self.assertIn("serializable", report)

    def test_run_json_output_contains_trace_and_invariants(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "run",
                str(DOCTOR_SCENARIO),
                "--isolation",
                "snapshot",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["isolation_level"], "snapshot")
        self.assertGreater(len(payload["trace"]), 0)
        self.assertEqual(payload["invariants"][0]["name"], "at_least_one_doctor_on_call")

    def test_run_json_output_includes_scan_trace_and_predicate_reads(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "run",
                str(PHANTOM_SCENARIO),
                "--isolation",
                "serializable",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        payload = json.loads(completed.stdout)
        scan_steps = [item for item in payload["trace"] if item.get("op") == "scan"]
        self.assertEqual(len(scan_steps), 2)
        self.assertEqual(scan_steps[0]["count"], 0)
        self.assertEqual(
            payload["transactions"][0]["predicate_reads"],
            ['prefix=booking_room101_2026-04-20T09:00_, value="reserved"'],
        )

    def test_render_timeline_svg_mentions_versions_and_transactions(self) -> None:
        svg = render_timeline_svg(run_simulation(load_scenario(DOCTOR_SCENARIO), "serializable"))
        self.assertIn("Doctor on-call write skew", svg)
        self.assertIn("Committed versions", svg)
        self.assertIn("alice_on_call", svg)
        self.assertIn("final version: 1", svg)
        self.assertIn('aria-labelledby="timeline-title timeline-desc"', svg)
        self.assertIn('title id="timeline-title"', svg)
        self.assertIn('desc id="timeline-desc"', svg)

    def test_run_cli_writes_timeline_svg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "snapshot_timeline.svg"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "run",
                    str(REPEATABLE_SCENARIO),
                    "--isolation",
                    "snapshot",
                    "--timeline-svg-out",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertIn("Timeline SVG:", completed.stdout)
            report = output_path.read_text()
            self.assertIn("Repeatable read window", report)
            self.assertIn("Committed versions", report)

    def test_run_json_output_includes_timeline_meta_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "snapshot_timeline.svg"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "run",
                    str(REPEATABLE_SCENARIO),
                    "--isolation",
                    "snapshot",
                    "--timeline-svg-out",
                    str(output_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["_meta"]["timeline_svg_output"], str(output_path))

    def test_compare_cli_can_emit_all_timeline_svgs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "compare",
                    str(DOCTOR_SCENARIO),
                    "--timeline-svg-dir",
                    temp_dir,
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertIn("Timeline SVGs:", completed.stdout)
            created = sorted(path.name for path in Path(temp_dir).glob("*.svg"))
            self.assertEqual(
                created,
                [
                    "doctor_on_call_read_committed_timeline.svg",
                    "doctor_on_call_serializable_timeline.svg",
                    "doctor_on_call_snapshot_timeline.svg",
                ],
            )

    def test_compare_json_output_includes_timeline_meta_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "compare",
                    str(DOCTOR_SCENARIO),
                    "--timeline-svg-dir",
                    temp_dir,
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(
                payload["_meta"]["timeline_svg_outputs"]["serializable"],
                str(Path(temp_dir) / "doctor_on_call_serializable_timeline.svg"),
            )


if __name__ == "__main__":
    unittest.main()
