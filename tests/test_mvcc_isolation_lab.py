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
render_compare_html = MODULE.render_compare_html
render_catalog_html = MODULE.render_catalog_html
render_catalog_markdown = MODULE.render_catalog_markdown
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

    def test_strict_2pl_aborts_first_writer_in_doctor_scenario(self) -> None:
        result = run_simulation(load_scenario(DOCTOR_SCENARIO), "strict-2pl")
        self.assertEqual(result.final_state, {"alice_on_call": True, "bob_on_call": False})
        self.assertEqual([item["status"] for item in result.transactions], ["aborted", "committed"])
        self.assertTrue(result.invariants[0]["ok"])
        self.assertIn("strict-2pl write lock conflict", result.transactions[0]["abort_reason"])

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

    def test_strict_2pl_reader_preserves_repeatable_read_by_aborting_writer(self) -> None:
        result = run_simulation(load_scenario(REPEATABLE_SCENARIO), "strict-2pl")
        reader, writer = result.transactions
        self.assertEqual(reader["status"], "committed")
        self.assertEqual(writer["status"], "aborted")
        self.assertIn("strict-2pl write lock conflict", writer["abort_reason"])
        self.assertEqual(result.final_state, {"inventory": 5})
        self.assertTrue(all(item["ok"] for item in result.invariants))

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

    def test_strict_2pl_aborts_first_booking_on_predicate_lock_conflict(self) -> None:
        result = run_simulation(load_scenario(PHANTOM_SCENARIO), "strict-2pl")
        self.assertEqual([item["status"] for item in result.transactions], ["aborted", "committed"])
        self.assertTrue(result.invariants[0]["ok"])
        self.assertIn("strict-2pl predicate lock conflict", result.transactions[0]["abort_reason"])
        self.assertEqual(
            result.final_state,
            {
                "booking_room101_2026-04-20T09:00_bob": "reserved",
                "room101_capacity": 1,
            },
        )

    def test_compare_runs_all_supported_modes(self) -> None:
        results = compare_scenario(load_scenario(DOCTOR_SCENARIO))
        self.assertEqual(
            set(results),
            {"read-committed", "snapshot", "serializable", "strict-2pl"},
        )
        self.assertEqual(results["serializable"].final_state["bob_on_call"], True)
        self.assertEqual(results["strict-2pl"].final_state["alice_on_call"], True)

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
            self.assertIn("Isolation comparison", completed.stdout)
            report = output_path.read_text()
            self.assertIn("Doctor on-call write skew", report)
            self.assertIn("Two doctors each see coverage in their snapshot", report)
            self.assertIn("serializable", report)
            self.assertIn("strict-2pl", report)

    def test_render_compare_html_links_markdown_and_timelines(self) -> None:
        results = compare_scenario(load_scenario(DOCTOR_SCENARIO))
        html = render_compare_html(
            results,
            markdown_href="doctor_on_call_compare.md",
            timeline_hrefs={
                "serializable": "doctor_on_call_serializable_timeline.svg",
                "strict-2pl": "doctor_on_call_strict_2pl_timeline.svg",
            },
        )
        self.assertIn("Doctor on-call write skew", html)
        self.assertIn("Open Markdown comparison", html)
        self.assertIn("doctor_on_call_compare.md", html)
        self.assertIn("doctor_on_call_serializable_timeline.svg", html)
        self.assertIn("doctor_on_call_strict_2pl_timeline.svg", html)
        self.assertIn("Invariant-safe", html)
        self.assertIn("Anomaly visible", html)
        self.assertIn("Scenario footprint", html)
        self.assertIn("Transactions", html)
        self.assertIn("Abort causes", html)

    def test_render_compare_html_distinguishes_assertion_abort_causes(self) -> None:
        results = compare_scenario(load_scenario(REPEATABLE_SCENARIO))
        html = render_compare_html(results, markdown_href="repeatable_read_window_compare.md")
        self.assertIn("assertions 1 · conflicts 2", html)
        self.assertIn("Abort class:</strong> scenario assertion failed", html)
        self.assertIn("Abort class:</strong> validation or lock conflict", html)
        self.assertIn("Schedule ticks", html)

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
                    "doctor_on_call_strict_2pl_timeline.svg",
                ],
            )

    def test_compare_cli_can_emit_html_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            html_path = Path(temp_dir) / "doctor_dashboard.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "compare",
                    str(DOCTOR_SCENARIO),
                    "--markdown-out",
                    str(Path(temp_dir) / "doctor_compare.md"),
                    "--timeline-svg-dir",
                    temp_dir,
                    "--html-out",
                    str(html_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertIn("HTML dashboard:", completed.stdout)
            html = html_path.read_text()
            self.assertIn("doctor_compare.md", html)
            self.assertIn("doctor_on_call_serializable_timeline.svg", html)
            self.assertIn("doctor_on_call_strict_2pl_timeline.svg", html)

    def test_compare_json_output_includes_timeline_meta_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            html_path = Path(temp_dir) / "doctor_dashboard.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "compare",
                    str(DOCTOR_SCENARIO),
                    "--timeline-svg-dir",
                    temp_dir,
                    "--html-out",
                    str(html_path),
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
            self.assertEqual(
                payload["_meta"]["timeline_svg_outputs"]["strict-2pl"],
                str(Path(temp_dir) / "doctor_on_call_strict_2pl_timeline.svg"),
            )
            self.assertEqual(payload["_meta"]["html_output"], str(html_path))


    def test_render_catalog_outputs_link_summaries(self) -> None:
        entries = [
            {
                "scenario": "doctor_on_call.json",
                "scenario_stem": "doctor_on_call",
                "title": "Doctor on-call write skew",
                "description": "Two doctors each see coverage in their snapshot before writing.",
                "transaction_count": 2,
                "tick_count": 6,
                "invariant_count": 1,
                "safe_modes": 2,
                "anomaly_modes": 2,
                "aborted_transactions": 2,
                "markdown": "doctor_on_call_compare.md",
                "dashboard": "doctor_on_call_dashboard.html",
                "timelines": {
                    "serializable": "doctor_on_call_serializable_timeline.svg",
                    "strict-2pl": "doctor_on_call_strict_2pl_timeline.svg",
                },
            }
        ]
        html = render_catalog_html(entries)
        markdown = render_catalog_markdown(entries)
        self.assertIn("Scenario gallery", html)
        self.assertIn("doctor_on_call_dashboard.html", html)
        self.assertIn("doctor_on_call_serializable_timeline.svg", html)
        self.assertIn("Anomaly modes", html)
        self.assertIn("Doctor on-call write skew", markdown)
        self.assertIn("[Markdown comparison](doctor_on_call_compare.md)", markdown)
        self.assertIn("Regenerate with `python3 projects/mvcc-isolation-lab/mvcc_isolation_lab.py catalog <scenario-dir> --output-dir <artifact-dir>`", markdown)

    def test_catalog_cli_builds_landing_page_and_scenario_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "catalog",
                    str(REPO_ROOT / "projects/mvcc-isolation-lab"),
                    "--output-dir",
                    temp_dir,
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            self.assertIn("Catalog scenarios: 3", completed.stdout)
            index_html = Path(temp_dir) / "index.html"
            index_md = Path(temp_dir) / "index.md"
            self.assertTrue(index_html.exists())
            self.assertTrue(index_md.exists())
            self.assertTrue((Path(temp_dir) / "doctor_on_call_dashboard.html").exists())
            self.assertTrue((Path(temp_dir) / "repeatable_read_window_dashboard.html").exists())
            self.assertTrue((Path(temp_dir) / "conference_room_booking_phantom_dashboard.html").exists())
            html = index_html.read_text()
            self.assertIn("Doctor on-call write skew", html)
            self.assertIn("repeatable_read_window_dashboard.html", html)
            self.assertIn("conference_room_booking_phantom_strict_2pl_timeline.svg", html)
            self.assertIn("Open first dashboard", html)

    def test_catalog_json_output_reports_generated_index_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "catalog",
                    str(REPO_ROOT / "projects/mvcc-isolation-lab"),
                    "--output-dir",
                    temp_dir,
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["scenario_count"], 3)
            self.assertEqual(payload["index_html_output"], str(Path(temp_dir) / "index.html"))
            self.assertEqual(payload["index_markdown_output"], str(Path(temp_dir) / "index.md"))
            self.assertEqual(len(payload["scenarios"]), 3)
            self.assertTrue(
                any(item["scenario"] == "doctor_on_call.json" for item in payload["scenarios"])
            )


if __name__ == "__main__":
    unittest.main()
