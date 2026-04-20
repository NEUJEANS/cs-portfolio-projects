from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dependency_graph_planner import (
    CycleError,
    build_plan,
    build_worker_limited_schedule,
    parse_tasks,
    render_dependency_diagram,
    render_report_markdown,
    run_command,
)


class DependencyGraphPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = {
            "tasks": [
                {"name": "lint", "duration": 1, "command": "ruff check ."},
                {"name": "compile", "deps": ["lint"], "duration": 4, "command": "python -m build"},
                {"name": "unit", "deps": ["compile"], "duration": 2, "command": "pytest"},
                {"name": "package", "deps": ["compile"], "duration": 1, "command": "python -m zipapp"},
                {"name": "publish", "deps": ["unit", "package"], "duration": 1, "command": "twine upload dist/*"},
            ]
        }
        self.strategy_graph = {
            "tasks": [
                {"name": "alpha-long", "duration": 6},
                {"name": "beta-long", "duration": 6},
                {"name": "core-seed", "duration": 1},
                {"name": "core-stage-1", "deps": ["core-seed"], "duration": 4},
                {"name": "core-stage-2", "deps": ["core-stage-1"], "duration": 4},
                {"name": "ship", "deps": ["alpha-long", "beta-long", "core-stage-2"], "duration": 1},
            ]
        }
        self.resource_graph = {
            "resource_capacities": {"gpu": 1},
            "tasks": [
                {"name": "prep", "duration": 1},
                {"name": "gpu-train", "deps": ["prep"], "duration": 4, "resource_class": "gpu"},
                {"name": "gpu-eval", "deps": ["prep"], "duration": 2, "resource_class": "gpu"},
                {"name": "docs", "deps": ["prep"], "duration": 3},
                {"name": "package", "deps": ["gpu-train", "gpu-eval", "docs"], "duration": 1},
            ]
        }
        self.multi_resource_graph = {
            "resource_capacities": {"browser-lab": 2, "gpu": 1, "signing": 1},
            "tasks": [
                {"name": "prep", "duration": 1},
                {"name": "browser-matrix", "deps": ["prep"], "duration": 5, "resources": {"browser-lab": 2}},
                {"name": "gpu-train", "deps": ["prep"], "duration": 4, "resource_class": "gpu"},
                {"name": "cross-platform-cert", "deps": ["prep"], "duration": 2, "resources": {"browser-lab": 1, "gpu": 1}},
                {"name": "sign", "deps": ["cross-platform-cert"], "duration": 1, "resources": {"signing": 1}},
                {"name": "package", "deps": ["browser-matrix", "gpu-train", "sign"], "duration": 1},
            ]
        }

    def _write_benchmark_suite_files(self, tmpdir: str) -> Path:
        tmp_path = Path(tmpdir)
        (tmp_path / "sample_graph.json").write_text(json.dumps(self.graph), encoding="utf-8")
        (tmp_path / "strategy_graph.json").write_text(json.dumps(self.strategy_graph), encoding="utf-8")
        (tmp_path / "resource_graph.json").write_text(json.dumps(self.resource_graph), encoding="utf-8")
        (tmp_path / "multi_resource_graph.json").write_text(json.dumps(self.multi_resource_graph), encoding="utf-8")
        suite_path = tmp_path / "benchmark_suite.json"
        suite_path.write_text(
            json.dumps(
                {
                    "title": "Dependency graph strategy benchmark suite",
                    "scenarios": [
                        {"label": "sample-2-workers", "graph": "sample_graph.json", "worker_limit": 2},
                        {"label": "strategy-2-workers", "graph": "strategy_graph.json", "worker_limit": 2},
                        {"label": "resource-3-workers", "graph": "resource_graph.json", "worker_limit": 3},
                        {"label": "multi-resource-3-workers", "graph": "multi_resource_graph.json", "worker_limit": 3},
                        {
                            "label": "multi-resource-browser-bump",
                            "graph": "multi_resource_graph.json",
                            "worker_limit": 3,
                            "strategies": ["critical-first", "fifo"],
                            "resource_capacities": {"browser-lab": 3, "gpu": 1, "signing": 1},
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        return suite_path

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

    def test_worker_limited_schedule_is_deterministic_and_tracks_queue_delay(self) -> None:
        tasks = parse_tasks(self.graph)
        plan = build_plan(tasks)
        schedule = build_worker_limited_schedule(tasks, plan, worker_limit=1)
        self.assertEqual(schedule.makespan, 9)
        self.assertEqual(schedule.theoretical_lower_bound, 9)
        self.assertEqual(schedule.dispatch_order, ["lint", "compile", "unit", "package", "publish"])
        package_assignment = next(item for item in schedule.assignments if item.name == "package")
        self.assertEqual(package_assignment.ready_at, 5)
        self.assertEqual(package_assignment.start, 7)
        self.assertEqual(package_assignment.queue_delay, 2)

    def test_worker_limited_schedule_can_compare_ready_queue_strategies(self) -> None:
        tasks = parse_tasks(self.strategy_graph)
        plan = build_plan(tasks)
        critical_first = build_worker_limited_schedule(tasks, plan, worker_limit=2, strategy="critical-first")
        fifo = build_worker_limited_schedule(tasks, plan, worker_limit=2, strategy="fifo")
        longest_processing_time = build_worker_limited_schedule(
            tasks,
            plan,
            worker_limit=2,
            strategy="longest-processing-time",
        )

        self.assertEqual(critical_first.strategy, "critical-first")
        self.assertEqual(critical_first.makespan, 13)
        self.assertEqual(critical_first.dispatch_order[:4], ["core-seed", "alpha-long", "core-stage-1", "core-stage-2"])
        self.assertEqual(fifo.strategy, "fifo")
        self.assertEqual(fifo.makespan, 16)
        self.assertEqual(fifo.dispatch_order[:3], ["alpha-long", "beta-long", "core-seed"])
        self.assertEqual(longest_processing_time.strategy, "longest-processing-time")
        self.assertEqual(longest_processing_time.makespan, 16)
        self.assertEqual(longest_processing_time.dispatch_order[:3], ["alpha-long", "beta-long", "core-seed"])
        delayed_seed = next(item for item in fifo.assignments if item.name == "core-seed")
        self.assertEqual(delayed_seed.queue_delay, 6)


    def test_worker_limited_schedule_respects_resource_class_capacities(self) -> None:
        tasks = parse_tasks(self.resource_graph)
        plan = build_plan(tasks)
        schedule = build_worker_limited_schedule(tasks, plan, worker_limit=3, resource_capacities={"gpu": 1})

        self.assertEqual(schedule.makespan, 8)
        self.assertEqual(schedule.unlimited_makespan, 6)
        self.assertEqual(schedule.dispatch_order, ["prep", "gpu-train", "docs", "gpu-eval", "package"])
        gpu_eval = next(item for item in schedule.assignments if item.name == "gpu-eval")
        self.assertEqual(gpu_eval.ready_at, 1)
        self.assertEqual(gpu_eval.start, 5)
        self.assertEqual(gpu_eval.queue_delay, 4)
        self.assertEqual(gpu_eval.resource_class, "gpu")
        self.assertEqual(gpu_eval.resource_slot, 1)
        self.assertEqual(schedule.resource_capacities, {"gpu": 1})
        self.assertEqual(len(schedule.resource_summaries), 1)
        summary = schedule.resource_summaries[0]
        self.assertEqual(summary.resource_class, "gpu")
        self.assertEqual(summary.capacity, 1)
        self.assertEqual(summary.task_count, 2)
        self.assertEqual(summary.total_reserved_units, 6)
        self.assertEqual(summary.delayed_tasks, 1)
        self.assertEqual(summary.max_queue_delay, 4)

    def test_worker_limited_schedule_supports_multi_resource_demands(self) -> None:
        tasks = parse_tasks(self.multi_resource_graph)
        plan = build_plan(tasks)
        schedule = build_worker_limited_schedule(
            tasks,
            plan,
            worker_limit=3,
            resource_capacities={"browser-lab": 2, "gpu": 1, "signing": 1},
        )

        self.assertEqual(schedule.unlimited_makespan, 7)
        self.assertEqual(schedule.makespan, 10)
        self.assertEqual(
            schedule.dispatch_order,
            ["prep", "browser-matrix", "gpu-train", "cross-platform-cert", "sign", "package"],
        )
        cert = next(item for item in schedule.assignments if item.name == "cross-platform-cert")
        self.assertEqual(cert.ready_at, 1)
        self.assertEqual(cert.start, 6)
        self.assertEqual(cert.queue_delay, 5)
        self.assertEqual(cert.resource_demands, {"browser-lab": 1, "gpu": 1})
        self.assertEqual(cert.resource_allocations, {"browser-lab": (1,), "gpu": (1,)})
        browser_summary = next(item for item in schedule.resource_summaries if item.resource_class == "browser-lab")
        self.assertEqual(browser_summary.total_reserved_units, 12)
        self.assertEqual(browser_summary.peak_concurrent_usage, 2)
        self.assertEqual(browser_summary.delayed_tasks, 1)
        self.assertEqual(browser_summary.max_queue_delay, 5)

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
                {"name": 'deploy "prod"', "deps": ["build app"], "duration": 2},
            ]
        }
        tasks = parse_tasks(graph)
        plan = build_plan(tasks)
        mermaid = render_dependency_diagram(tasks, plan, diagram_format="mermaid")
        self.assertIn('task_0["build app<br/>d=1, slack=0"]', mermaid)
        self.assertIn('task_1["deploy &quot;prod&quot;<br/>d=2, slack=0"]', mermaid)
        self.assertIn('task_0 --> task_1', mermaid)

    def test_render_report_markdown_includes_links_timing_table_and_worker_section(self) -> None:
        tasks = parse_tasks(self.graph)
        plan = build_plan(tasks)
        schedule = build_worker_limited_schedule(tasks, plan, worker_limit=1)
        report = render_report_markdown(
            tasks,
            plan,
            source_label="projects/dependency-graph-planner/sample_graph.json",
            diagram_links=[
                ("GitHub-friendly Mermaid preview", "sample_graph_mermaid.md"),
                ("Graphviz DOT source", "sample_graph.dot"),
            ],
            worker_limited_schedule=schedule,
        )
        self.assertIn('# Dependency graph walkthrough — Sample Graph', report)
        self.assertIn('## Linked artifacts', report)
        self.assertIn('[GitHub-friendly Mermaid preview](sample_graph_mermaid.md)', report)
        self.assertIn('- Worker-limited makespan (1 worker): `9`', report)
        self.assertIn('across `1 worker`', report)
        self.assertIn('## Worker-limited comparison', report)
        self.assertIn('| package | 1 | — | — | 5 | 7 | 8 | 2 | no |', report)
        self.assertIn('| lint | 0 | — | 1 | — | 0 | 1 | 0 | 1 | 0 | yes | ruff check . |', report)
        self.assertIn('1. `lint`', report)
        self.assertIn('- Window: `0 → 1`', report)

    def test_render_report_markdown_includes_multi_worker_comparison_table(self) -> None:
        tasks = parse_tasks(self.graph)
        plan = build_plan(tasks)
        schedule = build_worker_limited_schedule(tasks, plan, worker_limit=1)
        comparison_schedules = [
            build_worker_limited_schedule(tasks, plan, worker_limit=2),
            build_worker_limited_schedule(tasks, plan, worker_limit=3),
        ]
        report = render_report_markdown(
            tasks,
            plan,
            source_label="projects/dependency-graph-planner/sample_graph.json",
            worker_limited_schedule=schedule,
            comparison_schedules=comparison_schedules,
        )
        self.assertIn('## Worker-capacity comparison', report)
        self.assertIn('compared worker caps against the unlimited baseline of `8`: `1 worker → 9, 2 workers → 8, 3 workers → 8`', report)
        self.assertIn('| 1 worker | 9 | 1 | 9 | 100.0% | 0 | 1 | 2 |', report)
        self.assertIn('| 2 workers | 8 | 0 | 8 | 56.2% | 7 | 0 | 0 |', report)
        self.assertIn('| 3 workers | 8 | 0 | 8 | 37.5% | 15 | 0 | 0 |', report)

    def test_render_report_markdown_includes_strategy_comparison_table(self) -> None:
        tasks = parse_tasks(self.strategy_graph)
        plan = build_plan(tasks)
        schedule = build_worker_limited_schedule(tasks, plan, worker_limit=2, strategy="critical-first")
        strategy_schedules = [
            build_worker_limited_schedule(tasks, plan, worker_limit=2, strategy="fifo"),
            build_worker_limited_schedule(tasks, plan, worker_limit=2, strategy="longest-processing-time"),
        ]
        report = render_report_markdown(
            tasks,
            plan,
            source_label="projects/dependency-graph-planner/strategy_graph.json",
            worker_limited_schedule=schedule,
            strategy_comparison_schedules=strategy_schedules,
        )
        self.assertIn('- Worker-limited strategy: `critical-first`', report)
        self.assertIn('compared scheduling strategies at `2 workers`: `critical-first → 13, fifo → 16, longest-processing-time → 16`', report)
        self.assertIn('## Scheduling-strategy comparison', report)
        self.assertIn('| critical-first | 13 | 3 | 0 | 1 | 6 | core-seed, alpha-long, core-stage-1, core-stage-2, beta-long, ship |', report)
        self.assertIn('| fifo | 16 | 6 | 3 | 1 | 6 | alpha-long, beta-long, core-seed, core-stage-1, core-stage-2, ship |', report)
        self.assertIn('- Strategy: `critical-first`', report)


    def test_render_report_markdown_includes_resource_class_tables_and_labels(self) -> None:
        tasks = parse_tasks(self.resource_graph)
        plan = build_plan(tasks)
        schedule = build_worker_limited_schedule(tasks, plan, worker_limit=3, resource_capacities={"gpu": 1})
        report = render_report_markdown(
            tasks,
            plan,
            source_label="projects/dependency-graph-planner/resource_graph.json",
            worker_limited_schedule=schedule,
        )
        self.assertIn('- renewable resource caps active for the constrained run: `gpu=1`', report)
        self.assertIn('### Resource-class utilization', report)
        self.assertIn('| gpu | 1 | 2 | 6 | 1 | 75.0% | 2 | 1 | 4 |', report)
        self.assertIn('- Worker 1 (`0 → 8`): prep (0→1), gpu-train (1→5) [gpu#1], gpu-eval (5→7) [gpu#1], package (7→8)', report)
        self.assertIn('| gpu-eval | 1 | gpu | gpu#1 | 1 | 5 | 7 | 4 | no |', report)
        self.assertIn('| gpu-train | 1 | prep | 4 | gpu | 1 | 5 | 1 | 5 | 0 | yes | — |', report)
        self.assertIn('- Resources: `gpu`', report)

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

    def test_run_command_schedule_json_returns_assignments(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            payload = json.loads(run_command("schedule", str(graph_path), as_json=True, worker_limit=1))
        self.assertEqual(payload["worker_limit"], 1)
        self.assertEqual(payload["strategy"], "critical-first")
        self.assertEqual(payload["makespan"], 9)
        self.assertEqual(payload["dispatch_order"], ["lint", "compile", "unit", "package", "publish"])
        self.assertEqual(payload["assignments"][3]["queue_delay"], 2)


    def test_run_command_schedule_json_accepts_resource_capacity_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "resource_graph.json"
            graph_path.write_text(json.dumps(self.resource_graph), encoding="utf-8")
            default_payload = json.loads(run_command("schedule", str(graph_path), as_json=True, worker_limit=3))
            overridden_payload = json.loads(
                run_command(
                    "schedule",
                    str(graph_path),
                    as_json=True,
                    worker_limit=3,
                    resource_capacity_overrides=["gpu=2"],
                )
            )
        self.assertEqual(default_payload["makespan"], 8)
        self.assertEqual(default_payload["resource_capacities"], {"gpu": 1})
        self.assertEqual(overridden_payload["makespan"], 6)
        self.assertEqual(overridden_payload["resource_capacities"], {"gpu": 2})
        gpu_slots = sorted(
            item["resource_slot"]
            for item in overridden_payload["assignments"]
            if item["resource_class"] == "gpu"
        )
        self.assertEqual(gpu_slots, [1, 2])


    def test_run_command_schedule_json_supports_multi_resource_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "multi_resource_graph.json"
            graph_path.write_text(json.dumps(self.multi_resource_graph), encoding="utf-8")
            default_payload = json.loads(run_command("schedule", str(graph_path), as_json=True, worker_limit=3))
            overridden_payload = json.loads(
                run_command(
                    "schedule",
                    str(graph_path),
                    as_json=True,
                    worker_limit=3,
                    resource_capacity_overrides=["browser-lab=3"],
                )
            )
        self.assertEqual(default_payload["makespan"], 10)
        self.assertEqual(overridden_payload["makespan"], 9)
        cert_default = next(item for item in default_payload["assignments"] if item["name"] == "cross-platform-cert")
        cert_override = next(item for item in overridden_payload["assignments"] if item["name"] == "cross-platform-cert")
        self.assertEqual(cert_default["resource_demands"], {"browser-lab": 1, "gpu": 1})
        self.assertEqual(cert_default["resource_allocations"], {"browser-lab": [1], "gpu": [1]})
        self.assertEqual(cert_override["start"], 5)
        self.assertEqual(cert_override["resource_allocations"], {"browser-lab": [3], "gpu": [1]})

    def test_run_command_report_json_writes_report_and_companion_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            report_path = Path(tmpdir) / "reports" / "graph_report.md"
            artifact_dir = Path(tmpdir) / "artifacts"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            payload = json.loads(
                run_command(
                    "report",
                    str(graph_path),
                    as_json=True,
                    report_markdown_out=str(report_path),
                    diagram_output_dir=str(artifact_dir),
                    worker_limit=1,
                )
            )

            written_report = report_path.read_text(encoding="utf-8")
            mermaid_preview_path = Path(payload["artifacts"]["mermaid_preview"])
            dot_path = Path(payload["artifacts"]["dot_source"])
            schedule_json_path = Path(payload["artifacts"]["worker_limited_schedule_json"])

            self.assertTrue(report_path.exists())
            self.assertTrue(mermaid_preview_path.exists())
            self.assertTrue(dot_path.exists())
            self.assertTrue(schedule_json_path.exists())
            self.assertIn('[GitHub-friendly Mermaid preview](../artifacts/graph_mermaid.md)', written_report)
            self.assertIn('[Worker-limited schedule JSON](../artifacts/graph_single_worker_schedule.json)', written_report)
            self.assertIn('## Worker-limited comparison', written_report)
            self.assertIn('```mermaid', mermaid_preview_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(schedule_json_path.read_text(encoding="utf-8"))["makespan"], 9)
            self.assertEqual(payload["report_markdown_out"], str(report_path))
            self.assertEqual(payload["worker_limited_schedule"]["makespan"], 9)
            self.assertIn('## Task timing table', payload["report_markdown"])

    def test_run_command_report_json_writes_multi_capacity_comparison_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            report_path = Path(tmpdir) / "reports" / "graph_comparison_report.md"
            artifact_dir = Path(tmpdir) / "artifacts"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            payload = json.loads(
                run_command(
                    "report",
                    str(graph_path),
                    as_json=True,
                    report_markdown_out=str(report_path),
                    diagram_output_dir=str(artifact_dir),
                    worker_limit=1,
                    compare_worker_limits=[2, 3, 1],
                )
            )

            written_report = report_path.read_text(encoding="utf-8")
            schedule_paths = payload["artifacts"]["worker_limited_schedule_jsons"]

            self.assertEqual(sorted(schedule_paths), ["1", "2", "3"])
            self.assertEqual(len(payload["worker_limited_schedule_comparisons"]), 3)
            self.assertIn('[Worker-limited schedule JSON (1 worker)](../artifacts/graph_single_worker_schedule.json)', written_report)
            self.assertIn('[Worker-limited schedule JSON (2 workers)](../artifacts/graph_2_workers_schedule.json)', written_report)
            self.assertIn('[Worker-limited schedule JSON (3 workers)](../artifacts/graph_3_workers_schedule.json)', written_report)
            self.assertIn('## Worker-capacity comparison', written_report)
            self.assertEqual(json.loads(Path(schedule_paths["2"]).read_text(encoding="utf-8"))["worker_limit"], 2)
            self.assertEqual(json.loads(Path(schedule_paths["3"]).read_text(encoding="utf-8"))["worker_limit"], 3)

    def test_run_command_report_json_writes_strategy_comparison_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "strategy_graph.json"
            report_path = Path(tmpdir) / "reports" / "strategy_report.md"
            artifact_dir = Path(tmpdir) / "artifacts"
            graph_path.write_text(json.dumps(self.strategy_graph), encoding="utf-8")
            payload = json.loads(
                run_command(
                    "report",
                    str(graph_path),
                    as_json=True,
                    report_markdown_out=str(report_path),
                    diagram_output_dir=str(artifact_dir),
                    worker_limit=2,
                    compare_strategies=["fifo", "longest-processing-time", "fifo"],
                )
            )

            written_report = report_path.read_text(encoding="utf-8")
            schedule_paths = payload["artifacts"]["worker_limited_schedule_jsons"]

            self.assertEqual(
                sorted(schedule_paths),
                ["2:critical-first", "2:fifo", "2:longest-processing-time"],
            )
            self.assertEqual(len(payload["worker_limited_strategy_comparisons"]), 3)
            self.assertIn(
                '[Worker-limited schedule JSON (2 workers, critical-first)](../artifacts/strategy_graph_2_workers_critical_first_schedule.json)',
                written_report,
            )
            self.assertIn(
                '[Worker-limited schedule JSON (2 workers, fifo)](../artifacts/strategy_graph_2_workers_fifo_schedule.json)',
                written_report,
            )
            self.assertIn(
                '[Worker-limited schedule JSON (2 workers, longest-processing-time)](../artifacts/strategy_graph_2_workers_longest_processing_time_schedule.json)',
                written_report,
            )
            self.assertIn('## Scheduling-strategy comparison', written_report)
            self.assertEqual(json.loads(Path(schedule_paths["2:fifo"]).read_text(encoding="utf-8"))["strategy"], "fifo")
            self.assertEqual(
                json.loads(Path(schedule_paths["2:longest-processing-time"]).read_text(encoding="utf-8"))["strategy"],
                "longest-processing-time",
            )

    def test_run_command_benchmark_json_writes_markdown_and_resolves_relative_graphs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            suite_path = self._write_benchmark_suite_files(tmpdir)
            report_path = Path(tmpdir) / "reports" / "benchmark_suite_report.md"
            payload = json.loads(
                run_command(
                    "benchmark",
                    str(suite_path),
                    as_json=True,
                    benchmark_markdown_out=str(report_path),
                )
            )

            self.assertEqual(payload["title"], "Dependency graph strategy benchmark suite")
            self.assertEqual(payload["scenario_count"], 5)
            self.assertTrue(report_path.exists())
            written_report = report_path.read_text(encoding="utf-8")
            self.assertIn("## Aggregate strategy scoreboard", written_report)
            self.assertIn("## Scenario — strategy-2-workers", written_report)
            self.assertIn("## Scenario — multi-resource-browser-bump", written_report)
            strategy_scenario = next(item for item in payload["scenarios"] if item["label"] == "strategy-2-workers")
            resource_scenario = next(item for item in payload["scenarios"] if item["label"] == "resource-3-workers")
            multi_resource_scenario = next(item for item in payload["scenarios"] if item["label"] == "multi-resource-3-workers")
            browser_bump_scenario = next(item for item in payload["scenarios"] if item["label"] == "multi-resource-browser-bump")
            aggregate_by_strategy = {item["strategy"]: item for item in payload["aggregates"]}
            self.assertEqual(strategy_scenario["rank_1_strategies"], ["critical-first"])
            self.assertEqual(strategy_scenario["best_makespan_strategies"], ["critical-first"])
            self.assertEqual(resource_scenario["rank_1_strategies"], ["fifo"])
            self.assertEqual(
                resource_scenario["best_makespan_strategies"],
                ["fifo", "critical-first", "longest-processing-time"],
            )
            self.assertEqual(
                multi_resource_scenario["rank_1_strategies"],
                ["critical-first", "fifo", "longest-processing-time"],
            )
            self.assertEqual(browser_bump_scenario["rank_1_strategies"], ["fifo"])
            self.assertEqual(browser_bump_scenario["best_makespan_strategies"], ["fifo"])
            self.assertEqual(browser_bump_scenario["resource_capacities"], {"browser-lab": 3, "gpu": 1, "signing": 1})
            self.assertEqual([item["strategy"] for item in browser_bump_scenario["strategy_results"]], ["fifo", "critical-first"])
            self.assertEqual(aggregate_by_strategy["critical-first"]["scenario_count"], 5)
            self.assertEqual(aggregate_by_strategy["fifo"]["scenario_count"], 5)
            self.assertEqual(aggregate_by_strategy["longest-processing-time"]["scenario_count"], 4)

    def test_run_command_benchmark_rejects_schedule_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            suite_path = self._write_benchmark_suite_files(tmpdir)
            with self.assertRaisesRegex(ValueError, "schedule/report flags are not valid on the benchmark command"):
                run_command("benchmark", str(suite_path), worker_limit=2)

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

    def test_cli_schedule_requires_worker_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "schedule",
                    str(graph_path),
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires --worker-limit", result.stderr)

    def test_cli_report_rejects_report_flags_on_non_report_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            output_path = Path(tmpdir) / "bad.md"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "plan",
                    str(graph_path),
                    "--report-markdown-out",
                    str(output_path),
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("report-specific flags require the report command", result.stderr)

    def test_cli_compare_worker_limit_requires_report_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "plan",
                    str(graph_path),
                    "--compare-worker-limit",
                    "2",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--compare-worker-limit requires the report command", result.stderr)

    def test_cli_strategy_requires_schedule_or_report_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "plan",
                    str(graph_path),
                    "--strategy",
                    "fifo",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--strategy requires the schedule or report command", result.stderr)

    def test_cli_compare_strategy_requires_report_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "schedule",
                    str(graph_path),
                    "--worker-limit",
                    "2",
                    "--compare-strategy",
                    "fifo",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--compare-strategy requires the report command", result.stderr)


    def test_cli_resource_capacity_requires_schedule_or_report_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "plan",
                    str(graph_path),
                    "--resource-capacity",
                    "gpu=2",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--resource-capacity requires the schedule or report command", result.stderr)

    def test_cli_report_compare_strategy_requires_worker_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(json.dumps(self.graph), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "projects/dependency-graph-planner/dependency_graph_planner.py",
                    "report",
                    str(graph_path),
                    "--compare-strategy",
                    "fifo",
                ],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--compare-strategy requires --worker-limit on the report command", result.stderr)

    def test_cli_validate_rejects_unknown_resource_capacity_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "graph.json"
            graph_path.write_text(
                json.dumps({"resource_capacities": {"gpu": 1}, "tasks": [{"name": "build", "duration": 1}]}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "projects/dependency-graph-planner/dependency_graph_planner.py", "validate", str(graph_path)],
                cwd=Path(__file__).resolve().parents[2],
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("resource_capacities were provided but no task declares any resources", result.stderr)

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
