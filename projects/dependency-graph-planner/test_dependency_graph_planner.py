from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dependency_graph_planner import CycleError, build_plan, parse_tasks, render_dependency_diagram, run_command


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

    def test_render_dependency_mermaid_groups_layers_and_marks_critical_path(self) -> None:
        tasks = parse_tasks(self.graph)
        plan = build_plan(tasks)
        mermaid = render_dependency_diagram(tasks, plan, diagram_format="mermaid")
        self.assertIn('subgraph layer_2["layer 2"]', mermaid)
        self.assertIn('task_0 --> task_1', mermaid)
        self.assertIn('task_1 --> task_3', mermaid)
        self.assertIn('class task_0,task_1,task_3,task_4 critical', mermaid)
        self.assertIn('package<br/>d=1, slack=1', mermaid)

    def test_render_dependency_dot_uses_same_rank_layers_and_highlights_critical_edges(self) -> None:
        tasks = parse_tasks(self.graph)
        plan = build_plan(tasks)
        dot = render_dependency_diagram(tasks, plan, diagram_format="dot")
        self.assertIn('rank=same;', dot)
        self.assertIn('"compile" [label="compile\\nd=4, slack=0", color="firebrick", penwidth=2, peripheries=2];', dot)
        self.assertIn('"compile" -> "unit" [color="firebrick", penwidth=2];', dot)
        self.assertIn('"compile" -> "package";', dot)

    def test_render_dependency_mermaid_uses_stable_ids_for_task_names_with_punctuation(self) -> None:
        graph = {
            "tasks": [
                {"name": "build app"},
                {"name": 'deploy \"prod\"', "deps": ["build app"], "duration": 2},
            ]
        }
        tasks = parse_tasks(graph)
        plan = build_plan(tasks)
        mermaid = render_dependency_diagram(tasks, plan, diagram_format="mermaid")
        self.assertIn('task_0["build app<br/>d=1, slack=0"]', mermaid)
        self.assertIn('task_1["deploy &quot;prod&quot;<br/>d=2, slack=0"]', mermaid)
        self.assertIn('task_0 --> task_1', mermaid)

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

    def test_run_command_diagram_json_wraps_format_and_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            payload = json.loads(run_command("diagram", str(graph_path), as_json=True, diagram_format="dot"))
        self.assertEqual(payload["format"], "dot")
        self.assertIn('digraph DependencyGraph', payload["diagram"])

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

    def test_cli_diagram_output_respects_selected_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "diagram",
                    str(graph_path),
                    "--format",
                    "mermaid",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
                check=True,
            )
        self.assertIn("flowchart LR", result.stdout)
        self.assertIn('subgraph layer_3["layer 3"]', result.stdout)

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
