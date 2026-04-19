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

spec = importlib.util.spec_from_file_location("graph_routing_negative_cycle_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

bellman_ford = module.bellman_ford
build_report = module.build_report
build_shortest_path_results = module.build_shortest_path_results
export_dot = module.export_dot
export_markdown = module.export_markdown
export_mermaid = module.export_mermaid
johnson = module.johnson
load_graph = module.load_graph
render_pretty = module.render_pretty


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


if __name__ == "__main__":
    unittest.main()
