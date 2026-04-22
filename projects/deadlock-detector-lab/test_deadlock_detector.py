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

    def test_cli_writes_wait_graph_visual_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "graph.json"
            svg_out = Path(tmpdir) / "graph.svg"
            html_out = Path(tmpdir) / "graph.html"
            payload.write_text(
                json.dumps(
                    {
                        "edges": [
                            {"from": "P1", "to": "P2"},
                            {"from": "P2", "to": "P1"},
                            {"from": "P3", "to": "P2"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "analyze-wait",
                    str(payload),
                    "--svg-out",
                    str(svg_out),
                    "--html-out",
                    str(html_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            svg = svg_out.read_text(encoding="utf-8")
            html_report = html_out.read_text(encoding="utf-8")
            self.assertIn("Deadlock wait-for graph", svg)
            self.assertIn("cycle highlighted", svg)
            self.assertIn("<svg", html_report)
            self.assertIn("P1 → P2 → P1", html_report)

    def test_cli_writes_allocation_visual_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "alloc.json"
            svg_out = Path(tmpdir) / "alloc.svg"
            html_out = Path(tmpdir) / "alloc.html"
            payload.write_text(
                json.dumps(
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
                ),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "analyze-allocations",
                    str(payload),
                    "--svg-out",
                    str(svg_out),
                    "--html-out",
                    str(html_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            svg = svg_out.read_text(encoding="utf-8")
            html_report = html_out.read_text(encoding="utf-8")
            self.assertIn("Deadlock resource-allocation view", svg)
            self.assertIn("needs 1 (short 1)", svg)
            self.assertIn("Deadlock allocation report", html_report)
            self.assertIn("printer", html_report)

    def test_cli_writes_banker_markdown_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "banker.json"
            markdown_out = Path(tmpdir) / "trace.md"
            svg_out = Path(tmpdir) / "trace.svg"
            html_out = Path(tmpdir) / "trace.html"
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
                    "--svg-out",
                    str(svg_out),
                    "--html-out",
                    str(html_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            markdown = markdown_out.read_text(encoding="utf-8")
            svg = svg_out.read_text(encoding="utf-8")
            html_report = html_out.read_text(encoding="utf-8")
            self.assertIn("# Banker's algorithm safety trace", markdown)
            self.assertIn("| Step | Chosen process | Runnable set |", markdown)
            self.assertIn("`P1`", markdown)
            self.assertIn("algorithm safety view", svg)
            self.assertIn("Trace steps", svg)
            self.assertIn("Banker's algorithm safety view", html_report)
            self.assertIn("Need matrix", html_report)

    def test_cli_writes_banker_request_markdown_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = Path(tmpdir) / "banker-request.json"
            markdown_out = Path(tmpdir) / "request-trace.md"
            svg_out = Path(tmpdir) / "request-trace.svg"
            html_out = Path(tmpdir) / "request-trace.html"
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
                    "--svg-out",
                    str(svg_out),
                    "--html-out",
                    str(html_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            markdown = markdown_out.read_text(encoding="utf-8")
            svg = svg_out.read_text(encoding="utf-8")
            html_report = html_out.read_text(encoding="utf-8")
            self.assertIn("# Banker's algorithm request trace", markdown)
            self.assertIn("- Granted: yes", markdown)
            self.assertIn("`P1`", markdown)
            self.assertIn("algorithm request trial", svg)
            self.assertIn("Decision takeaway", svg)
            self.assertIn("Banker's algorithm request trial", html_report)
            self.assertIn("Trial details", html_report)

    def test_cli_writes_detection_vs_avoidance_dashboard_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wait_payload = Path(tmpdir) / "wait.json"
            allocation_payload = Path(tmpdir) / "allocation.json"
            banker_payload = Path(tmpdir) / "banker.json"
            banker_request_payload = Path(tmpdir) / "banker-request.json"
            banker_contrast_payload = Path(tmpdir) / "banker-request-unsafe.json"
            markdown_out = Path(tmpdir) / "dashboard.md"
            html_out = Path(tmpdir) / "dashboard.html"

            wait_payload.write_text(
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
            allocation_payload.write_text(
                json.dumps(
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
                ),
                encoding="utf-8",
            )
            banker_payload.write_text(
                json.dumps(
                    {
                        "available": {"A": 1, "B": 1},
                        "allocation": {"P1": {"A": 1, "B": 0}},
                        "max": {"P1": {"A": 1, "B": 1}},
                    }
                ),
                encoding="utf-8",
            )
            banker_request_payload.write_text(
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
            banker_contrast_payload.write_text(
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
                        "process": "P0",
                        "request": {"A": 0, "B": 0, "C": 2},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "dashboard",
                    "--wait-input",
                    str(wait_payload),
                    "--allocation-input",
                    str(allocation_payload),
                    "--banker-input",
                    str(banker_payload),
                    "--banker-request-input",
                    str(banker_request_payload),
                    "--banker-contrast-input",
                    str(banker_contrast_payload),
                    "--markdown-out",
                    str(markdown_out),
                    "--html-out",
                    str(html_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            result = json.loads(completed.stdout)
            markdown = markdown_out.read_text(encoding="utf-8")
            html_report = html_out.read_text(encoding="utf-8")
            self.assertEqual(result["model"], "deadlock-detection-vs-avoidance")
            self.assertTrue(result["wait_for"]["deadlocked"])
            self.assertTrue(result["banker_request"]["granted"])
            self.assertFalse(result["banker_request_contrast"]["granted"])
            self.assertEqual(result["banker_request_delta_callout"]["shared_slack_spent"], {"C": 2})
            self.assertEqual(result["banker_request_delta_callout"]["lost_runnable_options"], ["P1"])
            self.assertGreaterEqual(len(result["key_takeaways"]), 5)
            self.assertIn("# Deadlock detection vs avoidance dashboard", markdown)
            self.assertIn("## Detection models", markdown)
            self.assertIn("Question answered: is there already a cycle among the waiting processes?", markdown)
            self.assertIn("### Banker's request trial", markdown)
            self.assertIn("### Granted vs denied request delta", markdown)
            self.assertIn("Lost runnable options: `P1`", markdown)
            self.assertIn("banker-request-unsafe.json", markdown)
            self.assertIn("Deadlock detection vs avoidance dashboard", html_report)
            self.assertIn("Wait-for graph detection", html_report)
            self.assertIn("Banker's safety analysis", html_report)
            self.assertIn("Banker's request trial", html_report)
            self.assertIn("Granted vs denied request delta", html_report)
            self.assertIn("Lost runnable options", html_report)
            self.assertIn("banker-request-unsafe.json", html_report)
            self.assertIn("algorithm safety view", html_report)
            self.assertIn("Decision takeaway", html_report)
            self.assertIn("Evaluated available vector", html_report)

    def test_cli_dashboard_supports_optional_request_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wait_payload = Path(tmpdir) / "wait.json"
            allocation_payload = Path(tmpdir) / "allocation.json"
            banker_payload = Path(tmpdir) / "banker.json"
            markdown_out = Path(tmpdir) / "dashboard.md"

            wait_payload.write_text(
                json.dumps({"edges": [{"from": "P1", "to": "P2"}, {"from": "P2", "to": "P1"}]}),
                encoding="utf-8",
            )
            allocation_payload.write_text(
                json.dumps(
                    {
                        "available": {"printer": 0, "scanner": 0},
                        "allocation": {"P1": {"printer": 1}, "P2": {"scanner": 1}},
                        "request": {"P1": {"scanner": 1}, "P2": {"printer": 1}},
                    }
                ),
                encoding="utf-8",
            )
            banker_payload.write_text(
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
                    "dashboard",
                    "--wait-input",
                    str(wait_payload),
                    "--allocation-input",
                    str(allocation_payload),
                    "--banker-input",
                    str(banker_payload),
                    "--markdown-out",
                    str(markdown_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            result = json.loads(completed.stdout)
            markdown = markdown_out.read_text(encoding="utf-8")
            self.assertIsNone(result["banker_request"])
            self.assertIsNone(result["banker_request_delta_callout"])
            self.assertNotIn("### Banker's request trial", markdown)

    def test_cli_dashboard_requires_primary_request_for_contrast(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wait_payload = Path(tmpdir) / "wait.json"
            allocation_payload = Path(tmpdir) / "allocation.json"
            banker_payload = Path(tmpdir) / "banker.json"
            banker_contrast_payload = Path(tmpdir) / "banker-request-unsafe.json"

            wait_payload.write_text(
                json.dumps({"edges": [{"from": "P1", "to": "P2"}, {"from": "P2", "to": "P1"}]}),
                encoding="utf-8",
            )
            allocation_payload.write_text(
                json.dumps(
                    {
                        "available": {"printer": 0, "scanner": 0},
                        "allocation": {"P1": {"printer": 1}, "P2": {"scanner": 1}},
                        "request": {"P1": {"scanner": 1}, "P2": {"printer": 1}},
                    }
                ),
                encoding="utf-8",
            )
            banker_payload.write_text(
                json.dumps(
                    {
                        "available": {"A": 1, "B": 1},
                        "allocation": {"P1": {"A": 1, "B": 0}},
                        "max": {"P1": {"A": 1, "B": 1}},
                    }
                ),
                encoding="utf-8",
            )
            banker_contrast_payload.write_text(
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
                        "process": "P0",
                        "request": {"A": 0, "B": 0, "C": 2},
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "dashboard",
                    "--wait-input",
                    str(wait_payload),
                    "--allocation-input",
                    str(allocation_payload),
                    "--banker-input",
                    str(banker_payload),
                    "--banker-contrast-input",
                    str(banker_contrast_payload),
                ],
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--banker-contrast-input requires --banker-request-input", completed.stderr)

    def test_cli_compares_banker_request_gallery_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_payload = Path(tmpdir) / "safe-request.json"
            unsafe_payload = Path(tmpdir) / "unsafe-request.json"
            markdown_out = Path(tmpdir) / "gallery.md"
            html_out = Path(tmpdir) / "gallery.html"

            base_state = {
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
            safe_payload.write_text(
                json.dumps({**base_state, "process": "P1", "request": {"A": 1, "B": 0, "C": 2}}),
                encoding="utf-8",
            )
            unsafe_payload.write_text(
                json.dumps({**base_state, "process": "P0", "request": {"A": 0, "B": 0, "C": 2}}),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    "projects/deadlock-detector-lab/deadlock_detector.py",
                    "compare-banker-requests",
                    str(safe_payload),
                    str(unsafe_payload),
                    "--markdown-out",
                    str(markdown_out),
                    "--html-out",
                    str(html_out),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            result = json.loads(completed.stdout)
            markdown = markdown_out.read_text(encoding="utf-8")
            html_report = html_out.read_text(encoding="utf-8")
            self.assertEqual(result["model"], "banker-request-gallery")
            self.assertEqual(result["decision_totals"], {"granted": 1, "denied": 1})
            self.assertEqual(len(result["delta_callouts"]), 1)
            self.assertEqual(result["delta_callouts"][0]["shared_slack_spent"], {"C": 2})
            self.assertEqual(result["delta_callouts"][0]["granted_only_slack_spent"], {"A": 1})
            self.assertEqual(result["delta_callouts"][0]["lost_runnable_options"], ["P1"])
            self.assertEqual(len(result["request_reports"]), 2)
            self.assertIn("# Banker's algorithm request gallery", markdown)
            self.assertIn("## Delta callouts", markdown)
            self.assertIn("runnable option P1 disappears", markdown)
            self.assertIn("safe-request.json", markdown)
            self.assertIn("unsafe-request.json", markdown)
            self.assertIn("First runnable set", markdown)
            self.assertIn("Banker's algorithm request gallery", html_report)
            self.assertIn("Delta callouts", html_report)
            self.assertIn("runnable option P1 disappears", html_report)
            self.assertIn("Comparison table", html_report)
            self.assertIn("safe-request.json", html_report)
            self.assertIn("unsafe-request.json", html_report)
            self.assertIn("First runnable set", html_report)
            self.assertIn("algorithm request trial", html_report)

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
