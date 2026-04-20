from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "graph-routing-negative-cycle-lab" / "graph_routing_lab.py"
SAMPLE_PATH = PROJECT_ROOT / "projects" / "graph-routing-negative-cycle-lab" / "sample_graph.json"
NEGATIVE_PATH = PROJECT_ROOT / "projects" / "graph-routing-negative-cycle-lab" / "negative_cycle_graph.json"
UNREACHABLE_PATH = PROJECT_ROOT / "projects" / "graph-routing-negative-cycle-lab" / "unreachable_graph.json"
ROUTE_SHIFT_PATH = PROJECT_ROOT / "projects" / "graph-routing-negative-cycle-lab" / "route_shift_graph.json"

spec = importlib.util.spec_from_file_location("graph_routing_negative_cycle_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

bellman_ford = module.bellman_ford
build_report = module.build_report
build_route_table = module.build_route_table
build_shortest_path_results = module.build_shortest_path_results
compare_reports = module.compare_reports
export_compare_html = module.export_compare_html
export_compare_markdown = module.export_compare_markdown
export_compare_svg = module.export_compare_svg
export_dot = module.export_dot
export_markdown = module.export_markdown
export_mermaid = module.export_mermaid
johnson = module.johnson
load_graph = module.load_graph
render_html_comparison = module.render_html_comparison
render_html_gallery = module.render_html_gallery
render_markdown_comparison = module.render_markdown_comparison
render_pretty = module.render_pretty
render_svg_comparison = module.render_svg_comparison
load_routing_gallery_manifest = module.load_routing_gallery_manifest
render_markdown_gallery = module.render_markdown_gallery
summarize_comparison_metrics = module.summarize_comparison_metrics


class GraphRoutingNegativeCycleLabTests(unittest.TestCase):
    def test_bellman_ford_returns_expected_distances(self) -> None:
        _, nodes, edges = load_graph(SAMPLE_PATH)
        result = bellman_ford(nodes, edges, "A")
        self.assertIsNone(result.negative_cycle)
        self.assertEqual(result.distances["A"], 0)
        self.assertEqual(result.distances["B"], 1)
        self.assertEqual(result.distances["C"], 2)
        self.assertEqual(result.distances["D"], 3)
        self.assertEqual(result.predecessors["B"], "C")
        self.assertEqual(result.predecessors["D"], "B")
        self.assertTrue(result.iterations)

    def test_bellman_ford_shortest_path_reconstruction(self) -> None:
        _, nodes, edges = load_graph(SAMPLE_PATH)
        result = bellman_ford(nodes, edges, "A")
        paths = build_shortest_path_results(result)
        self.assertEqual(paths["A"].path, ("A",))
        self.assertEqual(paths["D"].path, ("A", "C", "B", "D"))
        self.assertEqual(paths["D"].cost, 3)

    def test_bellman_ford_marks_unreachable_nodes_in_path_results(self) -> None:
        _, nodes, edges = load_graph(UNREACHABLE_PATH)
        result = bellman_ford(nodes, edges, "A")
        paths = build_shortest_path_results(result)
        self.assertEqual(paths["D"].path, ("A", "B", "C", "D"))
        self.assertEqual(paths["E"].path, tuple())
        self.assertEqual(paths["E"].cost, float("inf"))
        self.assertIsNone(result.predecessors["E"])

    def test_bellman_ford_detects_reachable_negative_cycle(self) -> None:
        _, nodes, edges = load_graph(NEGATIVE_PATH)
        result = bellman_ford(nodes, edges, "A")
        self.assertIsNotNone(result.negative_cycle)
        cycle = result.negative_cycle or ()
        self.assertGreaterEqual(len(cycle), 4)
        self.assertEqual(cycle[0], cycle[-1])
        self.assertTrue({"A", "B", "C"}.issubset(set(cycle)))

    def test_johnson_returns_all_pairs_shortest_paths(self) -> None:
        _, nodes, edges = load_graph(SAMPLE_PATH)
        result = johnson(nodes, edges)
        self.assertEqual(result.paths["A"]["D"].cost, 3)
        self.assertEqual(result.paths["A"]["D"].path, ("A", "C", "B", "D"))
        self.assertEqual(result.paths["D"]["B"].cost, 2)
        self.assertEqual(result.paths["D"]["B"].path, ("D", "A", "C", "B"))
        self.assertTrue(all(edge.weight >= 0 for edge in result.reweighted_edges))

    def test_johnson_rejects_negative_cycle_graphs(self) -> None:
        _, nodes, edges = load_graph(NEGATIVE_PATH)
        with self.assertRaisesRegex(ValueError, "negative cycle"):
            johnson(nodes, edges)

    def test_load_graph_rejects_duplicate_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(json.dumps({"nodes": ["A", "A"], "edges": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unique"):
                load_graph(path)

    def test_load_graph_rejects_unknown_edge_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(
                json.dumps({"nodes": ["A"], "edges": [{"source": "A", "target": "B", "weight": 1}]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "endpoints"):
                load_graph(path)

    def test_pretty_report_mentions_negative_cycle(self) -> None:
        graph_name, nodes, edges = load_graph(NEGATIVE_PATH)
        report = build_report(graph_name, nodes, edges, source="A", mode="bellman-ford")
        output = render_pretty(report)
        self.assertIn("Negative cycle:", output)
        self.assertIn("Bellman-Ford from A", output)
        self.assertIn("Iterations logged:", output)

    def test_pretty_report_formats_unreachable_costs_consistently(self) -> None:
        report = build_report(*load_graph(UNREACHABLE_PATH), source="A", mode="full")
        output = render_pretty(report)
        self.assertIn("- E: dist=∞ predecessor=—", output)
        self.assertIn("  E: cost=∞ path=unreachable", output)

    def test_export_mermaid_writes_shortest_path_and_cycle_styles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "routing.mmd"

            graph_name, nodes, edges = load_graph(SAMPLE_PATH)
            report = build_report(graph_name, nodes, edges, source="A", mode="bellman-ford")
            export_mermaid(report, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("flowchart LR", rendered)
            self.assertIn('A["A | dist=0"]', rendered)
            self.assertIn('C -->|"-1"| B', rendered)
            self.assertIn("class A,B,C,D shortest;", rendered)

            negative_report = build_report(*load_graph(NEGATIVE_PATH), source="A", mode="bellman-ford")
            export_mermaid(negative_report, output_path)
            rendered_negative = output_path.read_text(encoding="utf-8")
            self.assertIn("class A,B,C cycle;", rendered_negative)
            self.assertIn("%% negative cycle:", rendered_negative)
            self.assertIn('A ==>|"3"| B', rendered_negative)

    def test_export_dot_writes_graphviz_styles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "routing.dot"

            graph_name, nodes, edges = load_graph(SAMPLE_PATH)
            report = build_report(graph_name, nodes, edges, source="A", mode="bellman-ford")
            export_dot(report, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("digraph routing_demo {", rendered)
            self.assertIn("rankdir=LR;", rendered)
            self.assertIn('A [label="A\\\\ndist=0", fillcolor="#dbeafe"', rendered)
            self.assertIn('C -> B [label="-1", color="#2563eb"', rendered)
            self.assertIn('A -> B [label="4", style=dashed];', rendered)

            negative_report = build_report(*load_graph(NEGATIVE_PATH), source="A", mode="bellman-ford")
            export_dot(negative_report, output_path)
            rendered_negative = output_path.read_text(encoding="utf-8")
            self.assertIn('A [label="A\\\\ndist=', rendered_negative)
            self.assertIn('fillcolor="#fee2e2"', rendered_negative)
            self.assertIn('A -> B [label="3", color="#dc2626"', rendered_negative)
            self.assertIn("// negative cycle:", rendered_negative)

    def test_export_markdown_writes_unreachable_table_and_iteration_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "routing.md"
            report = build_report(*load_graph(UNREACHABLE_PATH), source="A", mode="full")
            export_markdown(report, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("# unreachable_demo routing report", rendered)
            self.assertIn("## Bellman-Ford from A", rendered)
            self.assertIn("| E | ∞ | — | unreachable | unreachable |", rendered)
            self.assertIn("### Iteration log", rendered)
            self.assertIn("## Johnson all-pairs shortest paths", rendered)

    def test_export_markdown_reports_negative_cycle_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "negative.md"
            report = build_report(*load_graph(NEGATIVE_PATH), source="A", mode="bellman-ford")
            export_markdown(report, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("### Reachable negative cycle", rendered)
            self.assertIn("A -> B -> C -> A", rendered)
            self.assertIn("not well-defined", rendered)

    def test_export_markdown_escapes_pipe_characters_in_cells(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "pipe_graph.json"
            graph_path.write_text(
                json.dumps(
                    {
                        "name": "pipe_demo",
                        "nodes": ["A|1", "B|2"],
                        "edges": [{"source": "A|1", "target": "B|2", "weight": 7}],
                    }
                ),
                encoding="utf-8",
            )
            output_path = Path(tmpdir) / "pipe.md"
            report = build_report(*load_graph(graph_path), source="A|1", mode="full")
            export_markdown(report, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("| A\\|1 | B\\|2 | 7 |", rendered)
            self.assertIn("| A\\|1 | 0 | — | A\\|1 | reachable |", rendered)
            self.assertIn("A\\|1 -> B\\|2", rendered)

    def test_compare_reports_highlights_cost_and_path_changes(self) -> None:
        baseline = build_report(*load_graph(SAMPLE_PATH), source="A", mode="bellman-ford")
        candidate = build_report(*load_graph(ROUTE_SHIFT_PATH), source="A", mode="bellman-ford")
        comparison = compare_reports(baseline, candidate)

        self.assertEqual(len(comparison.edge_changes), 2)
        edge_changes = {(change.source, change.target): change for change in comparison.edge_changes}
        self.assertEqual(edge_changes[("C", "B")].baseline_weight, -1)
        self.assertEqual(edge_changes[("C", "B")].candidate_weight, 3)
        self.assertEqual(edge_changes[("C", "D")].candidate_weight, 1)

        diffs = {diff.node: diff for diff in comparison.route_diffs}
        self.assertEqual(diffs["B"].changed_fields, ("cost", "predecessor", "path"))
        self.assertIn("cost 1 -> 4", diffs["B"].summary)
        self.assertIn("path: [A -> C -> B] => [A -> B]", diffs["B"].summary)
        self.assertEqual(diffs["D"].changed_fields, ("predecessor", "path"))
        self.assertIn("path changed at same cost: [A -> C -> B -> D] => [A -> C -> D]", diffs["D"].summary)
        self.assertEqual(comparison.changed_route_count, 2)
        self.assertEqual(comparison.unchanged_route_count, 2)

    def test_compare_reports_marks_presence_changes_when_candidate_adds_node(self) -> None:
        baseline = build_report(
            "baseline_graph",
            ("A", "B"),
            (module.Edge("A", "B", 1),),
            source="A",
            mode="bellman-ford",
        )
        candidate = build_report(
            "candidate_graph",
            ("A", "B", "C"),
            (module.Edge("A", "B", 1), module.Edge("B", "C", 1)),
            source="A",
            mode="bellman-ford",
        )
        comparison = compare_reports(baseline, candidate)
        diffs = {diff.node: diff for diff in comparison.route_diffs}
        self.assertEqual(diffs["C"].changed_fields, ("presence",))
        self.assertEqual(diffs["C"].summary, "node added in candidate graph")
        self.assertEqual(comparison.changed_route_count, 1)

    def test_summarize_comparison_metrics_counts_only_stable_same_cost_reroutes(self) -> None:
        stable_comparison = compare_reports(
            build_report(*load_graph(SAMPLE_PATH), source="A", mode="bellman-ford"),
            build_report(*load_graph(ROUTE_SHIFT_PATH), source="A", mode="bellman-ford"),
        )
        stable_metrics = summarize_comparison_metrics(stable_comparison)
        self.assertEqual(stable_metrics.same_cost_reroutes, 1)
        self.assertEqual(stable_metrics.cost_changes, 1)
        self.assertEqual(stable_metrics.status_changes, 0)

        incident_comparison = compare_reports(
            build_report(*load_graph(SAMPLE_PATH), source="A", mode="bellman-ford"),
            build_report(*load_graph(NEGATIVE_PATH), source="A", mode="bellman-ford"),
        )
        incident_metrics = summarize_comparison_metrics(incident_comparison)
        self.assertEqual(incident_metrics.same_cost_reroutes, 0)
        self.assertEqual(incident_metrics.status_changes, 4)

    def test_build_route_table_marks_cycle_reachable_nodes(self) -> None:
        report = build_report(*load_graph(NEGATIVE_PATH), source="A", mode="bellman-ford")
        table = build_route_table(report)
        self.assertEqual(table["A"].status, "cycle-reachable")
        self.assertEqual(table["D"].status, "cycle-reachable")

    def test_export_compare_markdown_writes_changed_route_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "route-diff.md"
            baseline = build_report(*load_graph(SAMPLE_PATH), source="A", mode="bellman-ford")
            candidate = build_report(*load_graph(ROUTE_SHIFT_PATH), source="A", mode="bellman-ford")
            comparison = compare_reports(baseline, candidate)
            export_compare_markdown(comparison, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("# routing_demo vs routing_shift_demo route diff report", rendered)
            self.assertIn("| C | B | -1 | 3 | weight-changed |", rendered)
            self.assertIn("| B | 1 | C | A -> C -> B | reachable | 4 | A | A -> B | reachable | cost, predecessor, path |", rendered)
            self.assertIn("path: [A -> C -> B] => [A -> B]", rendered)
            self.assertIn("path changed at same cost: [A -> C -> B -> D] => [A -> C -> D]", rendered)
            self.assertIn("## Route-table diff", render_markdown_comparison(comparison))

    def test_export_compare_html_writes_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "route-diff.html"
            baseline = build_report(*load_graph(SAMPLE_PATH), source="A", mode="bellman-ford")
            candidate = build_report(*load_graph(ROUTE_SHIFT_PATH), source="A", mode="bellman-ford")
            comparison = compare_reports(baseline, candidate)
            export_compare_html(comparison, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", rendered)
            self.assertIn("Graph routing route diff dashboard", rendered)
            self.assertIn("Same-cost reroutes", rendered)
            self.assertIn("Predecessor changes", rendered)
            self.assertIn("Deterministic static artifact", rendered)
            self.assertIn("cost 1 -&gt; 4; predecessor C -&gt; A; path: [A -&gt; C -&gt; B] =&gt; [A -&gt; B]", rendered)
            self.assertIn("Baseline predecessor", rendered)
            self.assertIn("Predecessor shift", rendered)
            self.assertIn("unchanged", rendered)
            self.assertIn("route-card--path", rendered)
            self.assertIn("weight-changed", rendered)
            self.assertIn("Route-table diff audit", render_html_comparison(comparison))

    def test_export_compare_svg_writes_summary_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "route-diff-card.svg"
            baseline = build_report(*load_graph(SAMPLE_PATH), source="A", mode="bellman-ford")
            candidate = build_report(*load_graph(ROUTE_SHIFT_PATH), source="A", mode="bellman-ford")
            comparison = compare_reports(baseline, candidate)
            export_compare_svg(comparison, output_path)
            rendered = output_path.read_text(encoding="utf-8")
            self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', rendered)
            self.assertIn('viewBox="0 0 1200 672"', rendered)
            self.assertIn('preserveAspectRatio="xMidYMin meet"', rendered)
            self.assertIn('<title id="svg-title">routing_demo vs routing_shift_demo route diff summary card</title>', rendered)
            self.assertIn('Same-cost reroutes', rendered)
            self.assertIn('Node B', rendered)
            self.assertIn('cost 1 → 4', rendered)
            self.assertIn('Deterministic static artifact', rendered)
            self.assertIn('Graph routing diff snapshot', render_svg_comparison(comparison))

    def test_cli_json_mode_with_compare_graph_emits_comparison_payload(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(MODULE_PATH),
                str(SAMPLE_PATH),
                "--source",
                "A",
                "--mode",
                "bellman-ford",
                "--compare-graph",
                str(ROUTE_SHIFT_PATH),
                "--format",
                "json",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["comparison"]["baseline_graph"], "routing_demo")
        self.assertEqual(payload["comparison"]["candidate_graph"], "routing_shift_demo")
        diffs = {diff["node"]: diff for diff in payload["comparison"]["route_diffs"]}
        self.assertEqual(diffs["B"]["changed_fields"], ["cost", "predecessor", "path"])

    def test_cli_can_export_compare_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cli-route-diff.md"
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    str(SAMPLE_PATH),
                    "--source",
                    "A",
                    "--mode",
                    "bellman-ford",
                    "--compare-graph",
                    str(ROUTE_SHIFT_PATH),
                    "--export-compare-markdown",
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Route-table comparison:", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertIn("## Route-table diff", output_path.read_text(encoding="utf-8"))

    def test_cli_can_export_compare_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cli-route-diff.html"
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    str(SAMPLE_PATH),
                    "--source",
                    "A",
                    "--mode",
                    "bellman-ford",
                    "--compare-graph",
                    str(ROUTE_SHIFT_PATH),
                    "--export-compare-html",
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Route-table comparison:", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertIn("Changed route highlights", output_path.read_text(encoding="utf-8"))

    def test_cli_can_export_compare_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cli-route-diff-card.svg"
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    str(SAMPLE_PATH),
                    "--source",
                    "A",
                    "--mode",
                    "bellman-ford",
                    "--compare-graph",
                    str(ROUTE_SHIFT_PATH),
                    "--export-compare-svg",
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Route-table comparison:", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertIn("route diff summary card", output_path.read_text(encoding="utf-8"))

    def test_cli_compare_markdown_requires_compare_graph(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(MODULE_PATH),
                str(SAMPLE_PATH),
                "--source",
                "A",
                "--mode",
                "bellman-ford",
                "--export-compare-markdown",
                str(PROJECT_ROOT / "docs" / "artifacts" / "should-not-exist.md"),
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--export-compare-markdown requires --compare-graph", completed.stderr)

    def test_cli_compare_html_requires_compare_graph(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(MODULE_PATH),
                str(SAMPLE_PATH),
                "--source",
                "A",
                "--mode",
                "bellman-ford",
                "--export-compare-html",
                str(PROJECT_ROOT / "docs" / "artifacts" / "should-not-exist.html"),
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--export-compare-html requires --compare-graph", completed.stderr)

    def test_cli_compare_svg_requires_compare_graph(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(MODULE_PATH),
                str(SAMPLE_PATH),
                "--source",
                "A",
                "--mode",
                "bellman-ford",
                "--export-compare-svg",
                str(PROJECT_ROOT / "docs" / "artifacts" / "should-not-exist.svg"),
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--export-compare-svg requires --compare-graph", completed.stderr)

    def test_cli_json_mode_emits_johnson_payload(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(MODULE_PATH),
                str(SAMPLE_PATH),
                "--source",
                "A",
                "--format",
                "json",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["graph"], "routing_demo")
        self.assertEqual(payload["bellman_ford"]["distances"]["D"], 3)
        self.assertEqual(payload["johnson"]["paths"]["A"]["D"]["path"], ["A", "C", "B", "D"])

    def test_cli_pretty_mode_supports_johnson_only(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(MODULE_PATH),
                str(SAMPLE_PATH),
                "--mode",
                "johnson",
                "--format",
                "pretty",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Johnson all-pairs shortest paths", completed.stdout)
        self.assertIn("[A]", completed.stdout)

    def test_cli_can_export_mermaid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cli-routing.mmd"
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    str(SAMPLE_PATH),
                    "--source",
                    "A",
                    "--mode",
                    "bellman-ford",
                    "--export-mermaid",
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Bellman-Ford from A", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertIn("shortest", output_path.read_text(encoding="utf-8"))

    def test_cli_can_export_dot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cli-routing.dot"
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    str(SAMPLE_PATH),
                    "--source",
                    "A",
                    "--mode",
                    "bellman-ford",
                    "--export-dot",
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Bellman-Ford from A", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertIn("digraph routing_demo {", output_path.read_text(encoding="utf-8"))

    def test_cli_can_export_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cli-routing.md"
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    str(UNREACHABLE_PATH),
                    "--source",
                    "A",
                    "--export-markdown",
                    str(output_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Bellman-Ford from A", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertIn("## Johnson all-pairs shortest paths", output_path.read_text(encoding="utf-8"))

    def test_load_routing_gallery_manifest_resolves_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            baseline = base_dir / "baseline.json"
            candidate = base_dir / "candidate.json"
            artifact = base_dir / "report.md"
            baseline.write_text(json.dumps({"name": "base", "nodes": ["A", "B"], "edges": [{"source": "A", "target": "B", "weight": 1}]}), encoding="utf-8")
            candidate.write_text(json.dumps({"name": "cand", "nodes": ["A", "B"], "edges": [{"source": "A", "target": "B", "weight": 2}]}), encoding="utf-8")
            artifact.write_text("# report\n", encoding="utf-8")
            manifest = base_dir / "gallery.json"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "Routing gallery",
                        "description": "Scenario bundle",
                        "scenarios": [
                            {
                                "slug": "weight-shift",
                                "title": "Weight shift",
                                "description": "Cost changes only.",
                                "baseline_graph": "baseline.json",
                                "candidate_graph": "candidate.json",
                                "source": "A",
                                "artifacts": [
                                    {
                                        "label": "Markdown report",
                                        "path": "report.md",
                                        "description": "Linked report",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            gallery = load_routing_gallery_manifest(manifest)
            self.assertEqual(gallery.title, "Routing gallery")
            self.assertEqual(len(gallery.scenarios), 1)
            self.assertEqual(gallery.scenarios[0].baseline_graph, baseline.resolve())
            self.assertEqual(gallery.scenarios[0].artifacts[0].path, artifact.resolve())

    def test_render_markdown_gallery_includes_relative_artifact_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            artifact_dir = base_dir / "artifacts"
            artifact_dir.mkdir()
            report_path = artifact_dir / "route-diff.md"
            report_path.write_text("# diff\\n", encoding="utf-8")
            manifest = base_dir / "gallery.json"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "Routing gallery",
                        "description": "Scenario bundle",
                        "scenarios": [
                            {
                                "slug": "route-shift",
                                "title": "Route shift",
                                "description": "Shows a same-cost reroute.",
                                "baseline_graph": str(SAMPLE_PATH),
                                "candidate_graph": str(ROUTE_SHIFT_PATH),
                                "source": "A",
                                "artifacts": [
                                    {
                                        "label": "Markdown report",
                                        "path": str(report_path),
                                        "description": "Changed-route report",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            gallery = load_routing_gallery_manifest(manifest)
            output_path = base_dir / "site" / "gallery.md"
            output_path.parent.mkdir()
            rendered = render_markdown_gallery(gallery, output_path=output_path)
            self.assertIn("# Routing gallery", rendered)
            self.assertIn("same-cost reroutes with path churn", rendered)
            self.assertIn("../artifacts/route-diff.md", rendered)
            self.assertIn("Route shift", rendered)

    def test_render_html_gallery_includes_relative_artifact_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            artifact_dir = base_dir / "artifacts"
            artifact_dir.mkdir()
            report_path = artifact_dir / "route-diff.md"
            report_path.write_text("# diff\n", encoding="utf-8")
            manifest = base_dir / "gallery.json"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "Routing gallery",
                        "description": "Scenario bundle",
                        "scenarios": [
                            {
                                "slug": "route-shift",
                                "title": "Route shift",
                                "description": "Shows a same-cost reroute.",
                                "baseline_graph": str(SAMPLE_PATH),
                                "candidate_graph": str(ROUTE_SHIFT_PATH),
                                "source": "A",
                                "artifacts": [
                                    {
                                        "label": "Markdown report",
                                        "path": str(report_path),
                                        "description": "Changed-route report",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            gallery = load_routing_gallery_manifest(manifest)
            output_path = base_dir / "site" / "gallery.html"
            output_path.parent.mkdir()
            rendered = render_html_gallery(gallery, output_path=output_path)
            self.assertIn('<article class="scenario-card" id="route-shift">', rendered)
            self.assertIn('../artifacts/route-diff.md', rendered)
            self.assertIn('same-cost reroutes with path churn', rendered)
            self.assertIn('href="#route-shift"', rendered)

    def test_render_markdown_gallery_does_not_label_negative_cycle_incident_as_same_cost_reroute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            report_path = base_dir / "incident.md"
            report_path.write_text("# incident\n", encoding="utf-8")
            manifest = base_dir / "gallery.json"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "Routing gallery",
                        "description": "Scenario bundle",
                        "scenarios": [
                            {
                                "slug": "negative-cycle-incident",
                                "title": "Negative cycle incident",
                                "description": "Candidate graph becomes unstable.",
                                "baseline_graph": str(SAMPLE_PATH),
                                "candidate_graph": str(NEGATIVE_PATH),
                                "source": "A",
                                "artifacts": [
                                    {
                                        "label": "Markdown report",
                                        "path": str(report_path),
                                        "description": "Incident diff",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            gallery = load_routing_gallery_manifest(manifest)
            output_path = base_dir / "site" / "gallery.md"
            output_path.parent.mkdir()
            rendered = render_markdown_gallery(gallery, output_path=output_path)
            self.assertIn("candidate introduces a reachable negative cycle", rendered)
            self.assertIn("- Same-cost reroutes: 0", rendered)

    def test_cli_can_export_gallery_markdown_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            report_path = base_dir / "route-diff.md"
            dashboard_path = base_dir / "route-diff.html"
            svg_path = base_dir / "route-diff.svg"
            report_path.write_text("# diff\n", encoding="utf-8")
            dashboard_path.write_text("<!doctype html><title>diff</title>\n", encoding="utf-8")
            svg_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>\n', encoding="utf-8")
            manifest = base_dir / "gallery.json"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "Routing gallery",
                        "description": "Scenario bundle",
                        "scenarios": [
                            {
                                "slug": "route-shift",
                                "title": "Route shift",
                                "description": "Shows a same-cost reroute.",
                                "baseline_graph": str(SAMPLE_PATH),
                                "candidate_graph": str(ROUTE_SHIFT_PATH),
                                "source": "A",
                                "artifacts": [
                                    {
                                        "label": "Markdown report",
                                        "path": str(report_path),
                                        "description": "Changed-route report",
                                    },
                                    {
                                        "label": "HTML dashboard",
                                        "path": str(dashboard_path),
                                        "description": "Dashboard artifact",
                                    },
                                    {
                                        "label": "SVG card",
                                        "path": str(svg_path),
                                        "description": "Compact summary card",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            markdown_output = base_dir / "gallery.md"
            html_output = base_dir / "gallery.html"
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    "--gallery-manifest",
                    str(manifest),
                    "--export-gallery-markdown",
                    str(markdown_output),
                    "--export-gallery-html",
                    str(html_output),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["scenario_count"], 1)
            self.assertTrue(markdown_output.exists())
            self.assertTrue(html_output.exists())
            self.assertIn("Routing gallery", markdown_output.read_text(encoding="utf-8"))
            rendered_html = html_output.read_text(encoding="utf-8")
            self.assertIn('<article class="scenario-card" id="route-shift">', rendered_html)
            self.assertIn("Route shift", rendered_html)
            self.assertIn('href="#route-shift"', rendered_html)

    def test_cli_gallery_export_requires_manifest(self) -> None:
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(MODULE_PATH),
                "--export-gallery-markdown",
                str(PROJECT_ROOT / "docs" / "artifacts" / "should-not-exist-gallery.md"),
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--export-gallery-markdown requires --gallery-manifest", completed.stderr)

    def test_cli_gallery_export_rejects_graph_argument(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            manifest = base_dir / "gallery.json"
            manifest.write_text(
                json.dumps(
                    {
                        "title": "Routing gallery",
                        "description": "Scenario bundle",
                        "scenarios": [
                            {
                                "slug": "route-shift",
                                "title": "Route shift",
                                "description": "Shows a same-cost reroute.",
                                "baseline_graph": str(SAMPLE_PATH),
                                "candidate_graph": str(ROUTE_SHIFT_PATH),
                                "source": "A",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                    str(MODULE_PATH),
                    str(SAMPLE_PATH),
                    "--gallery-manifest",
                    str(manifest),
                    "--export-gallery-html",
                    str(base_dir / "gallery.html"),
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("gallery exports do not use the graph positional argument", completed.stderr)


if __name__ == "__main__":
    unittest.main()
