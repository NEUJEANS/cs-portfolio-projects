from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dependency_graph_planner import CycleError, build_plan, parse_tasks


class DependencyGraphPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = {
            "tasks": [
                {"name": "lint", "duration": 1},
                {"name": "compile", "deps": ["lint"], "duration": 4},
                {"name": "unit", "deps": ["compile"], "duration": 2},
                {"name": "package", "deps": ["compile"], "duration": 1},
                {"name": "publish", "deps": ["unit", "package"], "duration": 1},
            ]
        }

    def test_build_plan_returns_deterministic_topological_order(self) -> None:
        plan = build_plan(parse_tasks(self.graph))
        self.assertEqual(plan.order, ["lint", "compile", "package", "unit", "publish"])
        self.assertEqual(plan.layers, [["lint"], ["compile"], ["package", "unit"], ["publish"]])

    def test_critical_path_and_slack_are_computed(self) -> None:
        plan = build_plan(parse_tasks(self.graph))
        self.assertEqual(plan.total_duration, 8)
        self.assertEqual(plan.critical_path, ["lint", "compile", "unit", "publish"])
        timings = {item.name: item for item in plan.timings}
        self.assertTrue(timings["unit"].critical)
        self.assertEqual(timings["package"].slack, 1)

    def test_unknown_dependency_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown dependencies"):
            parse_tasks({"tasks": [{"name": "deploy", "deps": ["missing"]}]})

    def test_cycle_detection_reports_path(self) -> None:
        cyclic = {
            "tasks": [
                {"name": "a", "deps": ["c"]},
                {"name": "b", "deps": ["a"]},
                {"name": "c", "deps": ["b"]},
            ]
        }
        with self.assertRaises(CycleError) as ctx:
            build_plan(parse_tasks(cyclic))
        self.assertEqual(ctx.exception.cycle, ["a", "c", "b", "a"])

    def test_topological_order_uses_global_lexical_tie_breaking(self) -> None:
        graph = {
            "tasks": [
                {"name": "setup"},
                {"name": "zeta", "deps": ["setup"]},
                {"name": "alpha", "deps": ["setup"]},
                {"name": "report", "deps": ["alpha", "zeta"]},
            ]
        }
        plan = build_plan(parse_tasks(graph))
        self.assertEqual(plan.order, ["setup", "alpha", "zeta", "report"])

    def test_cli_plan_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "projects/dependency-graph-planner/dependency_graph_planner.py", "plan", str(graph_path), "--json"],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                check=True,
            )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["critical_path"], ["lint", "compile", "unit", "publish"])
        self.assertEqual(payload["layers"][2], ["package", "unit"])

    def test_cli_validate_fails_for_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps({"tasks": [{"name": "build", "duration": 0}]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "projects/dependency-graph-planner/dependency_graph_planner.py", "validate", str(graph_path)],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("positive integer duration", result.stderr)


if __name__ == "__main__":
    unittest.main()
