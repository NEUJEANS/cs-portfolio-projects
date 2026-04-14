from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from deadlock_detector import analyze_allocations, analyze_wait_for_graph


class DeadlockDetectorTests(unittest.TestCase):
    def test_wait_for_graph_reports_cycle(self) -> None:
        result = analyze_wait_for_graph(
            {
                "edges": [
                    {"from": "P1", "to": "P2"},
                    {"from": "P2", "to": "P3"},
                    {"from": "P3", "to": "P1"},
                ]
            }
        )

        self.assertTrue(result.deadlocked)
        self.assertEqual(result.cycle, ["P1", "P2", "P3", "P1"])
        self.assertEqual(result.blocked_processes, ["P1", "P2", "P3"])

    def test_wait_for_graph_handles_non_deadlocked_state(self) -> None:
        result = analyze_wait_for_graph(
            {
                "edges": [
                    {"from": "P1", "to": "P2"},
                    {"from": "P3", "to": "P2"},
                ]
            }
        )

        self.assertFalse(result.deadlocked)
        self.assertEqual(result.cycle, [])
        self.assertEqual(result.blocked_processes, [])

    def test_allocation_analysis_detects_safe_finish_order(self) -> None:
        result = analyze_allocations(
            {
                "available": {"printer": 1, "scanner": 0},
                "allocation": {
                    "P1": {"scanner": 1},
                    "P2": {"printer": 1},
                },
                "request": {
                    "P1": {"printer": 1},
                    "P2": {"scanner": 1},
                },
            }
        )

        self.assertFalse(result.deadlocked)
        self.assertEqual(result.finish_order, ["P1", "P2"])
        self.assertEqual(result.deadlocked_processes, [])

    def test_allocation_analysis_detects_deadlock_and_blocking(self) -> None:
        result = analyze_allocations(
            {
                "available": {"printer": 0, "scanner": 0},
                "allocation": {
                    "P1": {"printer": 1},
                    "P2": {"scanner": 1},
                },
                "request": {
                    "P1": {"scanner": 1},
                    "P2": {"printer": 1},
                },
            }
        )

        self.assertTrue(result.deadlocked)
        self.assertEqual(result.deadlocked_processes, ["P1", "P2"])
        self.assertEqual(result.blocking["P1"], {"scanner": 1})
        self.assertEqual(result.blocking["P2"], {"printer": 1})

    def test_cli_outputs_json_for_wait_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "graph.json"
            payload.write_text(
                json.dumps(
                    {
                        "edges": [
                            {"from": "P1", "to": "P2"},
                            {"from": "P2", "to": "P1"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "analyze-wait",
                    str(payload),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            result = json.loads(completed.stdout)
            self.assertTrue(result["deadlocked"])
            self.assertEqual(result["cycle"], ["P1", "P2", "P1"])

    def test_cli_rejects_negative_resource_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "alloc.json"
            payload.write_text(
                json.dumps(
                    {
                        "available": {"printer": -1},
                        "allocation": {},
                        "request": {},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "analyze-allocations",
                    str(payload),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("must be a non-negative integer", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)

    def test_cli_rejects_non_object_json_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "graph.json"
            payload.write_text("[]", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "analyze-wait",
                    str(payload),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("input JSON must be an object", completed.stderr)


if __name__ == "__main__":
    unittest.main()
