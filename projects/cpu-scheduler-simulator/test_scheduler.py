import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scheduler import Process, load_processes, simulate


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


if __name__ == "__main__":
    unittest.main()
