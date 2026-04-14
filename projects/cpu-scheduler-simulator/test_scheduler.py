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

    def test_idle_gap_is_tracked(self):
        result = simulate([Process("P1", 3, 2)], "fcfs")
        self.assertEqual(result["timeline"][0], {"start": 0, "end": 3, "pid": "IDLE"})
        self.assertEqual(result["timeline"][1], {"start": 3, "end": 5, "pid": "P1"})
        self.assertEqual(result["averages"]["cpu_utilization"], 40.0)
        self.assertEqual(result["averages"]["throughput"], 0.2)

    def test_round_robin_rejects_non_positive_quantum(self):
        with self.assertRaises(ValueError):
            simulate(self.workload, "rr", quantum=0)

    def test_load_processes_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workload.json"
            path.write_text(json.dumps([
                {"pid": "P1", "arrival": 0, "burst": 1},
                {"pid": "P1", "arrival": 1, "burst": 2},
            ]))
            with self.assertRaises(ValueError):
                load_processes(path)

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workload.json"
            path.write_text(json.dumps([
                {"pid": "P1", "arrival": 0, "burst": 2},
                {"pid": "P2", "arrival": 1, "burst": 1},
            ]))
            completed = subprocess.run(
                ["python3", "scheduler.py", "rr", str(path), "--quantum", "1", "--json"],
                cwd=Path(__file__).parent,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["timeline"][0]["pid"], "P1")
            self.assertIn("averages", payload)


if __name__ == "__main__":
    unittest.main()
