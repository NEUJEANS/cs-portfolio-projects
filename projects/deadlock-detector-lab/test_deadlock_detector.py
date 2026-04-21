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

from deadlock_detector import (
    analyze_allocations,
    analyze_banker_request,
    analyze_banker_state,
    analyze_wait_for_graph,
)


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

    def test_banker_safety_analysis_reports_safe_sequence(self) -> None:
        result = analyze_banker_state(
            {
                "available": {"A": 3, "B": 3, "C": 2},
                "allocation": {
                    "P0": {"A": 0, "B": 1, "C": 0},
                    "P1": {"A": 2, "B": 0, "C": 0},
                    "P2": {"A": 3, "B": 0, "C": 2},
                    "P3": {"A": 2, "B": 1, "C": 1},
                    "P4": {"A": 0, "B": 0, "C": 2},
                },
                "max": {
                    "P0": {"A": 7, "B": 5, "C": 3},
                    "P1": {"A": 3, "B": 2, "C": 2},
                    "P2": {"A": 9, "B": 0, "C": 2},
                    "P3": {"A": 2, "B": 2, "C": 2},
                    "P4": {"A": 4, "B": 3, "C": 3},
                },
            }
        )

        self.assertTrue(result.safe)
        self.assertEqual(result.safe_sequence, ["P1", "P3", "P4", "P0", "P2"])
        self.assertEqual(result.unfinished_processes, [])
        self.assertEqual(result.need["P0"], {"A": 7, "B": 4, "C": 3})
        self.assertEqual(result.trace_steps[0].process, "P1")
        self.assertEqual(result.trace_steps[0].runnable_processes, ["P1", "P3"])
        self.assertEqual(result.trace_steps[0].work_before, {"A": 3, "B": 3, "C": 2})
        self.assertEqual(result.trace_steps[0].allocation_released, {"A": 2, "B": 0, "C": 0})
        self.assertEqual(result.trace_steps[-1].work_after, {"A": 10, "B": 5, "C": 7})
        self.assertEqual(result.blocking, {})

    def test_banker_safety_analysis_reports_blocking_for_unsafe_state(self) -> None:
        result = analyze_banker_state(
            {
                "available": {"A": 0, "B": 0},
                "allocation": {
                    "P1": {"A": 1, "B": 0},
                    "P2": {"A": 0, "B": 1},
                },
                "max": {
                    "P1": {"A": 1, "B": 1},
                    "P2": {"A": 1, "B": 1},
                },
            }
        )

        self.assertFalse(result.safe)
        self.assertEqual(result.safe_sequence, [])
        self.assertEqual(result.unfinished_processes, ["P1", "P2"])
        self.assertEqual(result.blocking, {"P1": {"B": 1}, "P2": {"A": 1}})
        self.assertEqual(result.trace_steps, [])

    def test_banker_request_rejects_unsafe_transition(self) -> None:
        result = analyze_banker_request(
            {
                "available": {"A": 3, "B": 3, "C": 2},
                "allocation": {
                    "P0": {"A": 0, "B": 1, "C": 0},
                    "P1": {"A": 2, "B": 0, "C": 0},
                    "P2": {"A": 3, "B": 0, "C": 2},
                    "P3": {"A": 2, "B": 1, "C": 1},
                    "P4": {"A": 0, "B": 0, "C": 2},
                },
                "max": {
                    "P0": {"A": 7, "B": 5, "C": 3},
                    "P1": {"A": 3, "B": 2, "C": 2},
                    "P2": {"A": 9, "B": 0, "C": 2},
                    "P3": {"A": 2, "B": 2, "C": 2},
                    "P4": {"A": 4, "B": 3, "C": 3},
                },
                "process": "P0",
                "request": {"A": 0, "B": 0, "C": 2},
            }
        )

        self.assertFalse(result.granted)
        self.assertEqual(result.reason, "request would move the system into an unsafe state")
        self.assertFalse(result.safe)
        self.assertEqual(result.safe_sequence, [])
        self.assertEqual(
            result.blocking,
            {
                "P0": {"A": 4, "B": 1, "C": 1},
                "P1": {"C": 2},
                "P2": {"A": 3},
                "P3": {"C": 1},
                "P4": {"A": 1, "C": 1},
            },
        )
        self.assertEqual(result.trace_steps, [])
        self.assertEqual(result.trial_available, {"A": 3, "B": 3, "C": 0})
        self.assertEqual(result.trial_need["P0"], {"A": 7, "B": 4, "C": 1})

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

    def test_cli_supports_banker_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "banker.json"
            payload.write_text(
                json.dumps(
                    {
                        "available": {"A": 1, "B": 1},
                        "allocation": {"P1": {"A": 1, "B": 0}},
                        "max": {"P1": {"A": 1, "B": 1}},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "analyze-banker",
                    str(payload),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            result = json.loads(completed.stdout)
            self.assertTrue(result["safe"])
            self.assertEqual(result["safe_sequence"], ["P1"])
            self.assertEqual(result["trace_steps"][0]["work_before"], {"A": 1, "B": 1})

    def test_cli_writes_banker_markdown_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "banker.json"
            markdown_out = Path(tmpdir) / "trace.md"
            payload.write_text(
                json.dumps(
                    {
                        "available": {"A": 1, "B": 1},
                        "allocation": {"P1": {"A": 1, "B": 0}},
                        "max": {"P1": {"A": 1, "B": 1}},
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "analyze-banker",
                    str(payload),
                    "--markdown-out",
                    str(markdown_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            markdown = markdown_out.read_text(encoding="utf-8")
            self.assertIn("# Banker's algorithm safety trace", markdown)
            self.assertIn("| Step | Chosen process | Runnable set |", markdown)
            self.assertIn("`P1`", markdown)

    def test_cli_writes_banker_request_markdown_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "banker-request.json"
            markdown_out = Path(tmpdir) / "request-trace.md"
            payload.write_text(
                json.dumps(
                    {
                        "available": {"A": 3, "B": 3, "C": 2},
                        "allocation": {
                            "P0": {"A": 0, "B": 1, "C": 0},
                            "P1": {"A": 2, "B": 0, "C": 0},
                            "P2": {"A": 3, "B": 0, "C": 2},
                            "P3": {"A": 2, "B": 1, "C": 1},
                            "P4": {"A": 0, "B": 0, "C": 2},
                        },
                        "max": {
                            "P0": {"A": 7, "B": 5, "C": 3},
                            "P1": {"A": 3, "B": 2, "C": 2},
                            "P2": {"A": 9, "B": 0, "C": 2},
                            "P3": {"A": 2, "B": 2, "C": 2},
                            "P4": {"A": 4, "B": 3, "C": 3},
                        },
                        "process": "P1",
                        "request": {"A": 1, "B": 0, "C": 2},
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "request-banker",
                    str(payload),
                    "--markdown-out",
                    str(markdown_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            markdown = markdown_out.read_text(encoding="utf-8")
            self.assertIn("# Banker's algorithm request trace", markdown)
            self.assertIn("- Granted: yes", markdown)
            self.assertIn("`P1`", markdown)

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
