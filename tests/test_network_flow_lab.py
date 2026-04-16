from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "network-flow-lab" / "network_flow.py"

spec = importlib.util.spec_from_file_location("network_flow_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

Edge = module.Edge
benchmark_algorithms = module.benchmark_algorithms
generate_random_flow_graph = module.generate_random_flow_graph
load_graph = module.load_graph
load_bipartite_graph = module.load_bipartite_graph
render_flow_dot = module.render_flow_dot
render_matching_dot = module.render_matching_dot
render_flow_markdown = module.render_flow_markdown
render_matching_markdown = module.render_matching_markdown
solve_max_flow = module.solve_max_flow
derive_minimum_vertex_cover = module.derive_minimum_vertex_cover
solve_bipartite_matching = module.solve_bipartite_matching
build_flow_explanation = module.build_flow_explanation
build_matching_explanation = module.build_matching_explanation


class NetworkFlowLabTests(unittest.TestCase):
    def test_clrs_style_graph_returns_expected_max_flow(self) -> None:
        nodes = ["s", "v1", "v2", "v3", "v4", "t"]
        edges = [
            Edge("s", "v1", 16),
            Edge("s", "v2", 13),
            Edge("v1", "v2", 10),
            Edge("v2", "v1", 4),
            Edge("v1", "v3", 12),
            Edge("v3", "v2", 9),
            Edge("v2", "v4", 14),
            Edge("v4", "v3", 7),
            Edge("v3", "t", 20),
            Edge("v4", "t", 4),
        ]

        result = solve_max_flow(nodes, edges, "s", "t")

        self.assertEqual(result.max_flow, 23)
        self.assertGreaterEqual(len(result.augmenting_paths), 3)
        self.assertEqual(result.min_cut["source_side"], ["s", "v1", "v2", "v4"])
        self.assertEqual(result.min_cut["sink_side"], ["t", "v3"])
        self.assertEqual(result.algorithm, "edmonds-karp")

    def test_dinic_matches_edmonds_karp_on_same_graph(self) -> None:
        nodes = ["s", "a", "b", "c", "t"]
        edges = [
            Edge("s", "a", 10),
            Edge("s", "b", 8),
            Edge("a", "b", 3),
            Edge("a", "c", 5),
            Edge("b", "c", 10),
            Edge("a", "t", 4),
            Edge("c", "t", 11),
        ]
        ek = solve_max_flow(nodes, edges, "s", "t", algorithm="edmonds-karp")
        dinic = solve_max_flow(nodes, edges, "s", "t", algorithm="dinic")
        self.assertEqual(dinic.max_flow, ek.max_flow)
        self.assertEqual(dinic.min_cut, ek.min_cut)
        self.assertEqual(dinic.algorithm, "dinic")
        self.assertGreaterEqual(dinic.phases or 0, 1)

    def test_parallel_edges_are_aggregated(self) -> None:
        result = solve_max_flow(
            ["s", "a", "t"],
            [Edge("s", "a", 3), Edge("s", "a", 2), Edge("a", "t", 4)],
            "s",
            "t",
        )
        self.assertEqual(result.max_flow, 4)
        by_edge = {(item["source"], item["target"]): item for item in result.edge_flows}
        self.assertEqual(by_edge[("s", "a")]["capacity"], 5)
        self.assertEqual(by_edge[("s", "a")]["flow"], 4)

    def test_disconnected_graph_has_zero_flow(self) -> None:
        result = solve_max_flow(["s", "a", "t"], [Edge("s", "a", 5)], "s", "t")
        self.assertEqual(result.max_flow, 0)
        self.assertEqual(result.augmenting_paths, [])
        self.assertEqual(result.min_cut["sink_side"], ["t"])

    def test_load_graph_rejects_negative_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(
                json.dumps(
                    {
                        "nodes": ["s", "t"],
                        "source": "s",
                        "sink": "t",
                        "edges": [{"source": "s", "target": "t", "capacity": -1}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "capacity"):
                load_graph(path)

    def test_minimum_vertex_cover_matches_konig_theorem_construction(self) -> None:
        edges = [("anna", "api"), ("anna", "compiler"), ("ben", "api"), ("chloe", "compiler")]
        matches = [{"left": "anna", "right": "api"}, {"left": "chloe", "right": "compiler"}]

        cover = derive_minimum_vertex_cover(["anna", "ben", "chloe"], ["api", "compiler"], edges, matches)

        self.assertEqual(cover["left"], [])
        self.assertEqual(cover["right"], ["api", "compiler"])
        self.assertEqual(cover["size"], 2)
        self.assertEqual(cover["reachable_from_unmatched_left"]["left"], ["anna", "ben", "chloe"])
        self.assertTrue(cover["konig_theorem_check"])

    def test_bipartite_matching_returns_maximum_matching(self) -> None:
        left = ["anna", "ben", "chloe", "david"]
        right = ["api", "compiler", "database"]
        edges = [
            ("anna", "api"),
            ("anna", "compiler"),
            ("ben", "api"),
            ("ben", "database"),
            ("chloe", "compiler"),
            ("david", "database"),
        ]

        result = solve_bipartite_matching(left, right, edges, algorithm="dinic").to_dict()

        self.assertEqual(result["match_count"], 3)
        self.assertEqual(result["unmatched_left"], ["david"])
        self.assertEqual(result["unmatched_right"], [])
        matches = {(item["left"], item["right"]) for item in result["matches"]}
        self.assertEqual(matches, {("anna", "api"), ("ben", "database"), ("chloe", "compiler")})
        self.assertEqual(result["minimum_vertex_cover"]["left"], [])
        self.assertEqual(result["minimum_vertex_cover"]["right"], ["api", "compiler", "database"])
        self.assertEqual(result["minimum_vertex_cover"]["size"], 3)
        self.assertTrue(result["minimum_vertex_cover"]["konig_theorem_check"])
        self.assertEqual(result["flow"]["max_flow"], 3)
        self.assertEqual(result["flow"]["algorithm"], "dinic")

    def test_load_bipartite_graph_rejects_cross_partition_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad_matching.json"
            path.write_text(
                json.dumps(
                    {
                        "left": ["a"],
                        "right": ["1"],
                        "edges": [{"source": "1", "target": "a"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "left nodes"):
                load_bipartite_graph(path)

    def test_load_bipartite_graph_rejects_duplicate_or_reserved_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            duplicate_path = Path(tmpdir) / "duplicate_matching.json"
            duplicate_path.write_text(
                json.dumps(
                    {
                        "left": ["a", "a"],
                        "right": ["1"],
                        "edges": [{"source": "a", "target": "1"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_bipartite_graph(duplicate_path)

            reserved_path = Path(tmpdir) / "reserved_matching.json"
            reserved_path.write_text(
                json.dumps(
                    {
                        "left": ["__source__"],
                        "right": ["1"],
                        "edges": [{"source": "__source__", "target": "1"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "reserved"):
                load_bipartite_graph(reserved_path)

    def test_render_flow_dot_marks_cut_edges_and_flow_labels(self) -> None:
        result = solve_max_flow(
            ["s", "a", "b", "t"],
            [Edge("s", "a", 3), Edge("a", "t", 2), Edge("s", "b", 1), Edge("b", "t", 1)],
            "s",
            "t",
        )
        dot = render_flow_dot(result, graph_name="tiny_flow")
        self.assertIn('digraph "tiny_flow"', dot)
        self.assertIn('"a" -> "t" [label="2/2", color="crimson", penwidth=2];', dot)
        self.assertIn('"s" [style="filled", fillcolor="lightblue", peripheries=2];', dot)

    def test_render_flow_markdown_includes_certificate_details(self) -> None:
        result = solve_max_flow(
            ["s", "a", "b", "t"],
            [Edge("s", "a", 3), Edge("a", "t", 2), Edge("s", "b", 1), Edge("b", "t", 1)],
            "s",
            "t",
        )
        artifact = render_flow_markdown(result, graph_name="tiny_flow")
        self.assertIn('# Max-flow proof artifact: `tiny_flow`', artifact)
        self.assertIn('## Min-cut certificate', artifact)
        self.assertIn('`a -> t` carries `2/2`', artifact)
        self.assertIn('## Augmenting paths', artifact)

    def test_render_matching_markdown_includes_cover_details(self) -> None:
        result = solve_bipartite_matching(
            ["anna", "ben"],
            ["api", "db"],
            [("anna", "api"), ("ben", "api")],
        )
        artifact = render_matching_markdown(result, graph_name="tiny_matching")
        self.assertIn('# Bipartite matching proof artifact: `tiny_matching`', artifact)
        self.assertIn('## Minimum vertex cover', artifact)
        self.assertIn('`anna -> api`', artifact)

    def test_render_matching_dot_highlights_matches(self) -> None:
        result = solve_bipartite_matching(
            ["anna", "ben"],
            ["api", "db"],
            [("anna", "api"), ("ben", "api")],
        )
        dot = render_matching_dot(result, graph_name="tiny_matching")
        self.assertIn('digraph "tiny_matching"', dot)
        self.assertIn('"anna" -> "api" [color="forestgreen", penwidth=3, label="match"];', dot)
        self.assertIn('"api" [peripheries=2];', dot)
        self.assertIn('"db" [fillcolor="moccasin"];', dot)

    def test_flow_explanation_matches_min_cut_certificate(self) -> None:
        result = solve_max_flow(
            ["s", "a", "b", "t"],
            [Edge("s", "a", 3), Edge("a", "t", 2), Edge("s", "b", 1), Edge("b", "t", 1)],
            "s",
            "t",
        )
        explanation = build_flow_explanation(result)
        self.assertEqual(explanation["min_cut_capacity"], result.max_flow)
        self.assertTrue(explanation["max_flow_equals_min_cut_capacity"])
        self.assertTrue(explanation["cut_edges"])
        self.assertEqual(
            sum(edge["capacity"] for edge in explanation["cut_edges"]),
            result.max_flow,
        )
        self.assertTrue(all(edge["saturated"] for edge in explanation["cut_edges"]))

    def test_matching_explanation_reports_konig_certificate(self) -> None:
        result = solve_bipartite_matching(
            ["anna", "ben", "chloe", "david"],
            ["api", "compiler", "database"],
            [
                ("anna", "api"),
                ("anna", "compiler"),
                ("ben", "api"),
                ("ben", "database"),
                ("chloe", "compiler"),
                ("david", "database"),
            ],
            algorithm="dinic",
        )
        explanation = build_matching_explanation(result)
        self.assertEqual(explanation["match_count"], 3)
        self.assertEqual(explanation["minimum_vertex_cover_size"], 3)
        self.assertTrue(explanation["konig_theorem_check"])
        self.assertEqual(
            {(item["side"], item["node"]) for item in explanation["cover_vertices"]},
            {("right", "api"), ("right", "compiler"), ("right", "database")},
        )

    def test_random_graph_generator_is_reproducible_and_connected(self) -> None:
        graph_a = generate_random_flow_graph(seed=7, node_count=6, edge_probability=0.4)
        graph_b = generate_random_flow_graph(seed=7, node_count=6, edge_probability=0.4)
        self.assertEqual(graph_a, graph_b)
        nodes, edges, source, sink = graph_a
        self.assertEqual(source, "n0")
        self.assertEqual(sink, "n5")
        edge_pairs = {(edge.source, edge.target) for edge in edges}
        for i in range(len(nodes) - 1):
            self.assertIn((f"n{i}", f"n{i+1}"), edge_pairs)

    def test_benchmark_reports_matching_algorithms_and_speedup(self) -> None:
        payload = benchmark_algorithms(node_count=12, edge_probability=0.3, trials=3, seed=11)
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["algorithms"], ["edmonds-karp", "dinic"])
        self.assertEqual(len(payload["trials"]), 3)
        self.assertIn("speedup_ratio", payload["summary"])
        self.assertGreater(payload["summary"]["dinic"]["mean_phases"], 0)
        for trial in payload["trials"]:
            self.assertEqual(trial["edmonds-karp"]["max_flow"], trial["dinic"]["max_flow"])

    def test_cli_demo_outputs_json_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "demo")
        self.assertEqual(payload["max_flow"], 19)
        self.assertEqual(payload["algorithm"], "edmonds-karp")
        self.assertTrue(payload["augmenting_paths"])

    def test_cli_supports_dinic_for_demo(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo", "--algorithm", "dinic"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "demo")
        self.assertEqual(payload["algorithm"], "dinic")
        self.assertEqual(payload["max_flow"], 19)
        self.assertGreaterEqual(payload["phases"], 1)

    def test_cli_match_demo_outputs_matching_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "match-demo"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "match-demo")
        self.assertEqual(payload["match_count"], 3)
        self.assertEqual(payload["unmatched_left"], ["david"])
        self.assertIn("flow", payload)

    def test_cli_demo_can_emit_explanation_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo", "--explain"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertIn("explanation", payload)
        self.assertTrue(payload["explanation"]["max_flow_equals_min_cut_capacity"])

    def test_cli_match_demo_can_emit_explanation_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "match-demo", "--explain"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertIn("explanation", payload)
        self.assertTrue(payload["explanation"]["konig_theorem_check"])

    def test_cli_can_write_dot_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dot_path = Path(tmpdir) / "flow.dot"
            completed = subprocess.run(
                ["python3", str(MODULE_PATH), "demo", "--dot-out", str(dot_path)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "demo")
            self.assertEqual(payload["dot_output"], str(dot_path))
            self.assertTrue(dot_path.exists())
            dot = dot_path.read_text(encoding="utf-8")
            self.assertIn('digraph "sample_graph"', dot)
            self.assertIn('label="10/10"', dot)

    def test_cli_can_write_flow_markdown_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow-proof.md"
            completed = subprocess.run(
                ["python3", str(MODULE_PATH), "demo", "--markdown-out", str(output_path)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "demo")
            self.assertEqual(payload["markdown_output"], str(output_path))
            artifact = output_path.read_text(encoding="utf-8")
            self.assertIn('# Max-flow proof artifact: `sample_graph`', artifact)
            self.assertIn('## Augmenting paths', artifact)

    def test_cli_can_write_matching_markdown_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "matching-proof.md"
            completed = subprocess.run(
                ["python3", str(MODULE_PATH), "match-demo", "--markdown-out", str(output_path)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "match-demo")
            self.assertEqual(payload["markdown_output"], str(output_path))
            artifact = output_path.read_text(encoding="utf-8")
            self.assertIn('# Bipartite matching proof artifact: `sample_matching_graph`', artifact)
            self.assertIn('## Minimum vertex cover', artifact)

    def test_cli_benchmark_outputs_reproducible_summary(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "benchmark",
                "--nodes",
                "10",
                "--edge-probability",
                "0.25",
                "--trials",
                "2",
                "--seed",
                "5",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["generator"]["seed"], 5)
        self.assertEqual(len(payload["trials"]), 2)
        self.assertIn("speedup_ratio", payload["summary"])


if __name__ == "__main__":
    unittest.main()
