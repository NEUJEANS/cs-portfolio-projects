import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scheduler import (
    Process,
    compare_algorithms,
    format_compare_markdown,
    format_compare_svg,
    format_preset_catalog,
    format_report,
    load_processes,
    resolve_workload_source,
    simulate,
)


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.workload = [
            Process("P1", arrival=0, burst=5),
            Process("P2", arrival=1, burst=3),
            Process("P3", arrival=2, burst=1),
        ]

    def test_fcfs_metrics(self):
        result = simulate(self.workload, "fcfs")
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 5),
            ("P2", 5, 8),
            ("P3", 8, 9),
        ])
        self.assertEqual(by_pid["P1"]["waiting"], 0)
        self.assertEqual(by_pid["P2"]["waiting"], 4)
        self.assertEqual(by_pid["P3"]["waiting"], 6)

    def test_sjf_prefers_shortest_available_job(self):
        result = simulate(self.workload, "sjf")
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 5),
            ("P3", 5, 6),
            ("P2", 6, 9),
        ])
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual(by_pid["P3"]["waiting"], 3)
        self.assertEqual(by_pid["P2"]["response"], 5)

    def test_srtf_preempts_on_shorter_arrival(self):
        result = simulate([
            Process("P1", arrival=0, burst=8),
            Process("P2", arrival=1, burst=4),
            Process("P3", arrival=2, burst=2),
        ], "srtf")
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 1),
            ("P2", 1, 2),
            ("P3", 2, 4),
            ("P2", 4, 7),
            ("P1", 7, 14),
        ])
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual(by_pid["P3"]["response"], 0)
        self.assertEqual(by_pid["P2"]["completion"], 7)
        self.assertEqual(by_pid["P1"]["waiting"], 6)

    def test_srtf_uses_deterministic_tie_breaking(self):
        result = simulate([
            Process("P2", arrival=0, burst=3),
            Process("P1", arrival=0, burst=3),
            Process("P3", arrival=5, burst=1),
        ], "srtf")
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 3),
            ("P2", 3, 6),
            ("P3", 6, 7),
        ])

    def test_round_robin_rotates_jobs(self):
        result = simulate(self.workload, "rr", quantum=2)
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 2),
            ("P2", 2, 4),
            ("P3", 4, 5),
            ("P1", 5, 7),
            ("P2", 7, 8),
            ("P1", 8, 9),
        ])
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual(by_pid["P2"]["completion"], 8)
        self.assertEqual(by_pid["P3"]["response"], 2)

    def test_priority_uses_lower_numbers_first(self):
        result = simulate([
            Process("P1", arrival=0, burst=4, priority=4),
            Process("P2", arrival=0, burst=2, priority=1),
            Process("P3", arrival=1, burst=1, priority=3),
        ], "priority")
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P2", 0, 2),
            ("P3", 2, 3),
            ("P1", 3, 7),
        ])
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual(by_pid["P2"]["waiting"], 0)
        self.assertEqual(by_pid["P1"]["response"], 3)

    def test_priority_aging_can_promote_long_waiting_job(self):
        workload = [
            Process("P1", arrival=0, burst=6, priority=0),
            Process("P2", arrival=0, burst=1, priority=5),
            Process("P3", arrival=4, burst=1, priority=3),
        ]
        result = simulate(workload, "priority", aging_interval=2)
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 6),
            ("P2", 6, 7),
            ("P3", 7, 8),
        ])
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual(by_pid["P2"]["waiting"], 6)
        self.assertEqual(by_pid["P3"]["waiting"], 3)

    def test_context_switch_cost_extends_wall_clock_and_waiting_time(self):
        result = simulate([
            Process("P1", arrival=0, burst=3),
            Process("P2", arrival=0, burst=2),
        ], "fcfs", context_switch_cost=1)
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 3),
            ("CS", 3, 4),
            ("P2", 4, 6),
        ])
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual(by_pid["P2"]["start"], 4)
        self.assertEqual(by_pid["P2"]["waiting"], 4)
        self.assertEqual(result["averages"]["context_switches"], 1)
        self.assertEqual(result["averages"]["context_switch_overhead_time"], 1)
        self.assertEqual(result["averages"]["scheduler_overhead_pct"], 16.67)
        self.assertEqual(result["averages"]["cpu_utilization"], 83.33)
        self.assertEqual(result["total_time"], 6)

    def test_context_switch_cost_skips_idle_gap(self):
        result = simulate([
            Process("P1", arrival=0, burst=2),
            Process("P2", arrival=5, burst=1),
        ], "fcfs", context_switch_cost=3)
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 2),
            ("IDLE", 2, 5),
            ("P2", 5, 6),
        ])
        self.assertEqual(result["averages"]["context_switches"], 0)
        self.assertEqual(result["averages"]["context_switch_overhead_time"], 0)
        self.assertEqual(result["total_time"], 6)

    def test_format_report_uses_result_context_switch_cost_by_default(self):
        result = simulate([
            Process("P1", arrival=0, burst=2),
            Process("P2", arrival=0, burst=1),
        ], "fcfs", context_switch_cost=2)
        report = format_report(result, "fcfs")
        self.assertIn("context_switch_cost=2", report)
        self.assertIn("Context-switch overhead time: 2", report)

    def test_round_robin_context_switch_cost_counts_repeated_dispatches(self):
        result = simulate([
            Process("P1", arrival=0, burst=3),
            Process("P2", arrival=0, burst=2),
        ], "rr", quantum=1, context_switch_cost=1)
        self.assertEqual([(s["pid"], s["start"], s["end"]) for s in result["timeline"]], [
            ("P1", 0, 1),
            ("CS", 1, 2),
            ("P2", 2, 3),
            ("CS", 3, 4),
            ("P1", 4, 5),
            ("CS", 5, 6),
            ("P2", 6, 7),
            ("CS", 7, 8),
            ("P1", 8, 9),
        ])
        by_pid = {row["pid"]: row for row in result["processes"]}
        self.assertEqual(by_pid["P1"]["completion"], 9)
        self.assertEqual(result["averages"]["context_switches"], 4)
        self.assertEqual(result["averages"]["context_switch_overhead_time"], 4)
        self.assertEqual(result["total_time"], 9)

    def test_idle_gap_is_tracked(self):
        result = simulate([Process("P1", 3, 2)], "fcfs")
        self.assertEqual(result["timeline"][0], {"start": 0, "end": 3, "pid": "IDLE"})
        self.assertEqual(result["timeline"][1], {"start": 3, "end": 5, "pid": "P1"})
        self.assertEqual(result["averages"]["cpu_utilization"], 40.0)
        self.assertEqual(result["averages"]["throughput"], 0.2)

    def test_round_robin_rejects_non_positive_quantum(self):
        with self.assertRaises(ValueError):
            simulate(self.workload, "rr", quantum=0)

    def test_priority_rejects_negative_aging_interval(self):
        with self.assertRaises(ValueError):
            simulate(self.workload, "priority", aging_interval=-1)

    def test_context_switch_cost_rejects_negative_value(self):
        with self.assertRaises(ValueError):
            simulate(self.workload, "fcfs", context_switch_cost=-1)

    def test_load_processes_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workload.json"
            path.write_text(json.dumps([
                {"pid": "P1", "arrival": 0, "burst": 1},
                {"pid": "P1", "arrival": 1, "burst": 2},
            ]))
            with self.assertRaises(ValueError):
                load_processes(path)

    def test_load_processes_defaults_priority_to_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workload.json"
            path.write_text(json.dumps([
                {"pid": "P1", "arrival": 0, "burst": 2},
            ]))
            [proc] = load_processes(path)
            self.assertEqual(proc.priority, 0)

    def test_resolve_workload_source_uses_preset_catalog(self):
        processes, label, preset_name, source = resolve_workload_source(None, "interactive-bursts")
        self.assertEqual(label, "interactive-bursts")
        self.assertEqual(preset_name, "interactive-bursts")
        self.assertTrue(source.endswith("artifacts/cpu-scheduler-simulator/presets/interactive-bursts.json"))
        self.assertGreaterEqual(len(processes), 3)

    def test_compare_algorithms_collects_summary_and_winners(self):
        comparison = compare_algorithms(
            [
                Process("P1", arrival=0, burst=7, priority=4),
                Process("P2", arrival=1, burst=1, priority=0),
                Process("P3", arrival=2, burst=2, priority=1),
            ],
            algorithms=["fcfs", "srtf", "rr"],
            quantum=2,
            context_switch_cost=1,
            workload_label="demo",
            workload_source="demo.json",
        )
        self.assertEqual(comparison["workload_label"], "demo")
        self.assertEqual([entry["algorithm"] for entry in comparison["algorithms"]], ["fcfs", "srtf", "rr"])
        fcfs = next(entry for entry in comparison["algorithms"] if entry["algorithm"] == "fcfs")
        srtf = next(entry for entry in comparison["algorithms"] if entry["algorithm"] == "srtf")
        self.assertGreater(fcfs["summary"]["avg_response"], srtf["summary"]["avg_response"])
        self.assertIn("srtf", comparison["winners"]["avg_response"])
        self.assertIn("experience", fcfs)
        self.assertEqual(fcfs["experience"][0]["pid"], "P1")
        self.assertIn("avg_slowdown", fcfs["summary"])
        self.assertIn("slowdown_stddev", comparison["winners"])

    def test_format_compare_markdown_mentions_takeaways(self):
        comparison = compare_algorithms(
            [Process("P1", arrival=0, burst=4), Process("P2", arrival=1, burst=1)],
            algorithms=["fcfs", "sjf"],
            workload_label="tiny",
            workload_source="tiny.json",
        )
        report = format_compare_markdown(comparison)
        self.assertIn("# CPU Scheduler Comparison — tiny", report)
        self.assertIn("## Takeaways", report)
        self.assertIn("## Fairness and slowdown snapshot", report)
        self.assertIn("## Per-process experience", report)
        self.assertIn("| Algorithm | Avg turnaround | Avg waiting | Avg response | Max wait | CPU util % | Throughput | Overhead % | Total time |", report)
        self.assertIn("| Algorithm | Avg slowdown | Max slowdown | Slowdown spread | Slowdown stddev | Waiting stddev | Most delayed process |", report)
        self.assertIn("lowest average waiting", report)
        self.assertIn("most even slowdown distribution", report)

    def test_format_compare_svg_contains_dashboard_markup(self):
        comparison = compare_algorithms(
            [Process("P1", arrival=0, burst=5), Process("P2", arrival=1, burst=1)],
            algorithms=["fcfs", "rr"],
            workload_label="tiny",
            workload_source="tiny.json",
            quantum=2,
        )
        svg = format_compare_svg(comparison)
        self.assertIn("<svg", svg)
        self.assertIn("CPU Scheduler fairness dashboard", svg)
        self.assertIn("Slowdown by process", svg)
        self.assertIn("Waiting time by process", svg)
        self.assertIn("P1", svg)

    def test_format_preset_catalog_lists_new_presets(self):
        catalog = format_preset_catalog()
        self.assertIn("interactive-bursts", catalog)
        self.assertIn("aging-pressure", catalog)

    def test_cli_json_output_for_srtf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workload.json"
            path.write_text(json.dumps([
                {"pid": "P1", "arrival": 0, "burst": 5},
                {"pid": "P2", "arrival": 1, "burst": 2},
            ]))
            completed = subprocess.run(
                ["python3", "scheduler.py", "srtf", str(path), "--json"],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["timeline"][0]["pid"], "P1")
            self.assertEqual(payload["timeline"][1]["pid"], "P2")
            self.assertIn("averages", payload)

    def test_cli_json_output_for_priority_aging(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workload.json"
            path.write_text(json.dumps([
                {"pid": "P1", "arrival": 0, "burst": 3, "priority": 0},
                {"pid": "P2", "arrival": 0, "burst": 1, "priority": 4},
            ]))
            completed = subprocess.run(
                ["python3", "scheduler.py", "priority", str(path), "--aging-interval", "2", "--json"],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["processes"][0]["priority"], 0)
            self.assertEqual(payload["timeline"][0]["pid"], "P1")
            self.assertEqual(payload["timeline"][1]["pid"], "P2")

    def test_cli_json_output_for_context_switch_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workload.json"
            path.write_text(json.dumps([
                {"pid": "P1", "arrival": 0, "burst": 2},
                {"pid": "P2", "arrival": 0, "burst": 1},
            ]))
            completed = subprocess.run(
                [
                    "python3",
                    "scheduler.py",
                    "fcfs",
                    str(path),
                    "--context-switch-cost",
                    "2",
                    "--json",
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["context_switch_cost"], 2)
            self.assertEqual(payload["timeline"][1]["pid"], "CS")
            self.assertEqual(payload["averages"]["context_switch_overhead_time"], 2)

    def test_cli_compare_json_output_for_preset(self):
        completed = subprocess.run(
            [
                "python3",
                "scheduler.py",
                "compare",
                "--preset",
                "interactive-bursts",
                "--quantum",
                "2",
                "--aging-interval",
                "2",
                "--context-switch-cost",
                "1",
                "--json",
            ],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "compare")
        self.assertEqual(payload["preset"], "interactive-bursts")
        self.assertEqual(len(payload["algorithms"]), 5)

    def test_cli_run_supports_preset_workload(self):
        completed = subprocess.run(
            [
                "python3",
                "scheduler.py",
                "rr",
                "--preset",
                "interactive-bursts",
                "--quantum",
                "2",
                "--json",
            ],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["processes"][0]["pid"], "P1")
        self.assertGreater(len(payload["timeline"]), 1)

    def test_cli_compare_writes_dashboard_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            markdown_out = base / "compare.md"
            html_out = base / "compare.html"
            svg_out = base / "compare.svg"
            json_out = base / "compare.json"
            subprocess.run(
                [
                    "python3",
                    "scheduler.py",
                    "compare",
                    "--preset",
                    "convoy-mix",
                    "--markdown-out",
                    str(markdown_out),
                    "--html-out",
                    str(html_out),
                    "--svg-out",
                    str(svg_out),
                    "--json-out",
                    str(json_out),
                ],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(markdown_out.exists())
            self.assertTrue(html_out.exists())
            self.assertTrue(svg_out.exists())
            self.assertTrue(json_out.exists())
            self.assertIn("CPU Scheduler Comparison", markdown_out.read_text())
            self.assertIn("<table>", html_out.read_text())
            self.assertIn("fairness dashboard", svg_out.read_text())
            self.assertEqual(json.loads(json_out.read_text())["mode"], "compare")


if __name__ == "__main__":
    unittest.main()
