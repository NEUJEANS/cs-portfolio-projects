from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
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
generate_dense_flow_graph = module.generate_dense_flow_graph
generate_layered_flow_graph = module.generate_layered_flow_graph
load_graph = module.load_graph
load_bipartite_graph = module.load_bipartite_graph
load_weighted_assignment_graph = module.load_weighted_assignment_graph
load_costed_flow_graph = module.load_costed_flow_graph
render_flow_dot = module.render_flow_dot
render_matching_dot = module.render_matching_dot
render_flow_markdown = module.render_flow_markdown
render_flow_svg = module.render_flow_svg
render_matching_markdown = module.render_matching_markdown
render_matching_svg = module.render_matching_svg
render_assignment_dot = module.render_assignment_dot
render_assignment_markdown = module.render_assignment_markdown
render_assignment_svg = module.render_assignment_svg
render_assignment_diagram_svg = module.render_assignment_diagram_svg
render_assignment_artifact_html = module.render_assignment_artifact_html
render_min_cost_flow_dot = module.render_min_cost_flow_dot
render_min_cost_flow_markdown = module.render_min_cost_flow_markdown
render_min_cost_flow_svg = module.render_min_cost_flow_svg
render_min_cost_flow_diagram_svg = module.render_min_cost_flow_diagram_svg
render_min_cost_flow_artifact_html = module.render_min_cost_flow_artifact_html
render_artifact_gallery_html = module.render_artifact_gallery_html
render_benchmark_gallery_html = module.render_benchmark_gallery_html
render_benchmark_markdown = module.render_benchmark_markdown
render_benchmark_svg = module.render_benchmark_svg
solve_max_flow = module.solve_max_flow
solve_min_cost_max_flow = module.solve_min_cost_max_flow
derive_minimum_vertex_cover = module.derive_minimum_vertex_cover
solve_bipartite_matching = module.solve_bipartite_matching
solve_weighted_assignment = module.solve_weighted_assignment
build_flow_explanation = module.build_flow_explanation
build_matching_explanation = module.build_matching_explanation
build_assignment_explanation = module.build_assignment_explanation
build_min_cost_flow_explanation = module.build_min_cost_flow_explanation
build_flow_replay_reference = module.build_flow_replay_reference


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

    def test_render_flow_svg_includes_certificate_sections_and_valid_xml(self) -> None:
        result = solve_max_flow(
            ["s", "a", "b", "t"],
            [Edge("s", "a", 3), Edge("a", "t", 2), Edge("s", "b", 1), Edge("b", "t", 1)],
            "s",
            "t",
            algorithm="dinic",
        )
        svg = render_flow_svg(result, graph_name="tiny_flow")
        self.assertIn("<svg", svg)
        self.assertIn("Max-flow proof card", svg)
        self.assertIn("Min-cut partition", svg)
        self.assertIn("Augmenting paths", svg)
        self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

    def test_render_matching_svg_includes_certificate_sections_and_valid_xml(self) -> None:
        result = solve_bipartite_matching(
            ["anna", "ben", "chloe"],
            ["api", "compiler"],
            [("anna", "api"), ("ben", "api"), ("chloe", "compiler")],
            algorithm="dinic",
        )
        svg = render_matching_svg(result, graph_name="tiny_matching")
        self.assertIn("<svg", svg)
        self.assertIn("Bipartite matching proof card", svg)
        self.assertIn("Recovered minimum vertex cover", svg)
        self.assertIn("Certificate summary", svg)
        self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

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

    def test_load_weighted_assignment_graph_rejects_duplicate_pairs_and_negative_costs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            duplicate_path = Path(tmpdir) / "duplicate_assignment.json"
            duplicate_path.write_text(
                json.dumps(
                    {
                        "left": ["anna"],
                        "right": ["api"],
                        "edges": [
                            {"source": "anna", "target": "api", "cost": 3},
                            {"source": "anna", "target": "api", "cost": 4},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "must not repeat"):
                load_weighted_assignment_graph(duplicate_path)

            negative_path = Path(tmpdir) / "negative_assignment.json"
            negative_path.write_text(
                json.dumps(
                    {
                        "left": ["anna"],
                        "right": ["api"],
                        "edges": [{"source": "anna", "target": "api", "cost": -1}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "non-negative"):
                load_weighted_assignment_graph(negative_path)

    def test_load_weighted_assignment_graph_rejects_reserved_and_cross_partition_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            reserved_path = Path(tmpdir) / "reserved_assignment.json"
            reserved_path.write_text(
                json.dumps(
                    {
                        "left": ["__assignment_source__"],
                        "right": ["api"],
                        "edges": [{"source": "__assignment_source__", "target": "api", "cost": 1}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "reserved"):
                load_weighted_assignment_graph(reserved_path)

            cross_partition_path = Path(tmpdir) / "cross_partition_assignment.json"
            cross_partition_path.write_text(
                json.dumps(
                    {
                        "left": ["anna"],
                        "right": ["api"],
                        "edges": [{"source": "api", "target": "anna", "cost": 1}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "left nodes"):
                load_weighted_assignment_graph(cross_partition_path)

    def test_min_cost_flow_prefers_lower_total_cost_assignment_paths(self) -> None:
        left = ["anna", "ben"]
        right = ["api", "db"]
        edges = [
            ("anna", "api", 4),
            ("anna", "db", 1),
            ("ben", "api", 2),
            ("ben", "db", 6),
        ]

        result = solve_weighted_assignment(left, right, edges).to_dict()

        self.assertEqual(result["assignment_count"], 2)
        self.assertEqual(result["total_cost"], 3)
        self.assertEqual(
            {(item["left"], item["right"], item["cost"]) for item in result["assignments"]},
            {("anna", "db", 1), ("ben", "api", 2)},
        )
        self.assertTrue(result["covers_smaller_partition"])
        self.assertEqual(result["flow"]["total_flow"], 2)
        self.assertEqual(result["flow"]["algorithm"], "successive-shortest-path")

    def test_weighted_assignment_reports_partial_coverage_when_graph_is_incomplete(self) -> None:
        result = solve_weighted_assignment(
            ["anna", "ben", "chloe"],
            ["api", "db"],
            [
                ("anna", "api", 2),
                ("ben", "api", 1),
                ("chloe", "db", 3),
            ],
        ).to_dict()

        self.assertEqual(result["assignment_count"], 2)
        self.assertEqual(result["total_cost"], 4)
        self.assertEqual(result["unmatched_left"], ["anna"])
        self.assertEqual(result["unmatched_right"], [])
        self.assertTrue(result["covers_smaller_partition"])

    def test_assignment_explanation_reports_cost_consistency(self) -> None:
        result = solve_weighted_assignment(
            ["anna", "ben"],
            ["api", "db"],
            [
                ("anna", "api", 4),
                ("anna", "db", 1),
                ("ben", "api", 2),
                ("ben", "db", 6),
            ],
        )
        explanation = build_assignment_explanation(result)
        self.assertEqual(explanation["assignment_count"], 2)
        self.assertEqual(explanation["total_cost"], 3)
        self.assertTrue(explanation["cost_matches_flow_total"])
        self.assertEqual(explanation["average_cost"], 1.5)

    def test_render_assignment_markdown_includes_selected_pairs(self) -> None:
        result = solve_weighted_assignment(
            ["anna", "ben"],
            ["api", "db"],
            [
                ("anna", "api", 4),
                ("anna", "db", 1),
                ("ben", "api", 2),
                ("ben", "db", 6),
            ],
        )
        artifact = render_assignment_markdown(result, graph_name="weighted_assignment")
        self.assertIn('# Weighted assignment proof artifact: `weighted_assignment`', artifact)
        self.assertIn('## Selected assignments', artifact)
        self.assertIn('`anna -> db` with cost `1`', artifact)
        self.assertIn('`source -> anna -> db -> sink`', artifact)
        self.assertNotIn('__assignment_source__', artifact)
        self.assertNotIn('__assignment_sink__', artifact)

    def test_render_assignment_svg_includes_certificate_sections_and_valid_xml(self) -> None:
        result = solve_weighted_assignment(
            ["anna", "ben"],
            ["api", "db"],
            [
                ("anna", "api", 4),
                ("anna", "db", 1),
                ("ben", "api", 2),
                ("ben", "db", 6),
            ],
        )
        svg = render_assignment_svg(result, graph_name="weighted_assignment")
        self.assertIn("<svg", svg)
        self.assertIn("Weighted assignment proof card", svg)
        self.assertIn("Min-cost-flow certificate", svg)
        self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

    def test_render_assignment_diagram_svg_highlights_selected_pairs_and_valid_xml(self) -> None:
        result = solve_weighted_assignment(
            ["anna", "ben", "chloe"],
            ["api", "db"],
            [
                ("anna", "api", 6),
                ("anna", "db", 1),
                ("ben", "api", 2),
                ("chloe", "db", 4),
            ],
        )
        svg = render_assignment_diagram_svg(result, graph_name="weighted_assignment")
        self.assertIn("<svg", svg)
        self.assertIn("Weighted assignment diagram", svg)
        self.assertIn("selected @ 1", svg)
        self.assertIn("0/1", svg)
        self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

    def test_render_assignment_artifact_html_embeds_diagram_and_proof(self) -> None:
        result = solve_weighted_assignment(
            ["anna", "ben"],
            ["api", "db"],
            [
                ("anna", "api", 4),
                ("anna", "db", 1),
                ("ben", "api", 2),
                ("ben", "db", 6),
            ],
        )
        html = render_assignment_artifact_html(
            result,
            graph_name="weighted_assignment",
            companion_links={"dot": "assignment.dot", "markdown": "assignment-proof.md", "svg": "assignment-proof.svg", "json": "assignment-result.json"},
        )
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Weighted assignment artifact page", html)
        self.assertIn("DOT-style assignment diagram", html)
        self.assertIn("Weighted assignment proof card", html)
        self.assertIn('href="assignment.dot"', html)
        self.assertIn('href="assignment-proof.md"', html)
        self.assertIn('href="assignment-proof.svg"', html)
        self.assertIn('href="assignment-result.json"', html)
        self.assertIn('id="assignment-diagram-title"', html)
        self.assertIn('id="assignment-proof-title"', html)
        self.assertNotIn('id="title"', html)
        self.assertNotIn('id="desc"', html)

    def test_build_flow_replay_reference_normalizes_core_flow_fields(self) -> None:
        payload = {
            "algorithm": "dinic",
            "source": "s",
            "sink": "t",
            "max_flow": 5,
            "min_cut": {"source_side": ["b", "s", "a"], "sink_side": ["t", "c"]},
            "edge_flows": [
                {"source": "b", "target": "t", "capacity": 3, "flow": 2, "ignored": True},
                {"source": "s", "target": "a", "capacity": 4, "flow": 4},
                {"source": "a", "target": "t", "capacity": 4, "flow": 3},
            ],
            "command": "python3 network_flow.py demo --json-out /tmp/out.json",
            "html_output": "/tmp/showcase.html",
        }

        reference = build_flow_replay_reference(payload)

        self.assertEqual(reference["algorithm"], "dinic")
        self.assertEqual(reference["source"], "s")
        self.assertEqual(reference["sink"], "t")
        self.assertEqual(reference["max_flow"], 5)
        self.assertEqual(reference["min_cut"]["source_side"], ["a", "b", "s"])
        self.assertEqual(reference["min_cut"]["sink_side"], ["c", "t"])
        self.assertEqual(
            reference["edge_flows"],
            [
                {"source": "a", "target": "t", "capacity": 4, "flow": 3},
                {"source": "b", "target": "t", "capacity": 3, "flow": 2},
                {"source": "s", "target": "a", "capacity": 4, "flow": 4},
            ],
        )
        self.assertNotIn("command", reference)


    def test_render_assignment_dot_includes_ranked_partitions_and_selected_costs(self) -> None:
        result = solve_weighted_assignment(
            ["anna", "ben", "chloe"],
            ["api", "db"],
            [
                ("anna", "api", 6),
                ("anna", "db", 1),
                ("ben", "api", 2),
                ("chloe", "db", 4),
            ],
        )
        dot = render_assignment_dot(result, graph_name="weighted_assignment")
        self.assertIn('digraph "weighted_assignment"', dot)
        self.assertIn('label="assignment count=2, cost=3, full_coverage=True";', dot)
        self.assertIn('subgraph "cluster_left_partition" {', dot)
        self.assertIn('rank="same";', dot)
        self.assertIn('"anna" -> "db" [label="selected @ 1", color="forestgreen", penwidth=3];', dot)
        self.assertIn('"source" -> "chloe" [style="dashed", color="gray80", label="0/1"];', dot)

    def test_load_costed_flow_graph_rejects_negative_cost_and_bad_target_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            negative_cost_path = Path(tmpdir) / "negative_cost_flow.json"
            negative_cost_path.write_text(
                json.dumps(
                    {
                        "nodes": ["s", "t"],
                        "source": "s",
                        "sink": "t",
                        "edges": [{"source": "s", "target": "t", "capacity": 1, "cost": -1}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "cost must be non-negative"):
                load_costed_flow_graph(negative_cost_path)

            bad_target_path = Path(tmpdir) / "bad_target_flow.json"
            bad_target_path.write_text(
                json.dumps(
                    {
                        "nodes": ["s", "t"],
                        "source": "s",
                        "sink": "t",
                        "target_flow": -1,
                        "edges": [{"source": "s", "target": "t", "capacity": 1, "cost": 2}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "target_flow"):
                load_costed_flow_graph(bad_target_path)

    def test_min_cost_flow_respects_target_flow_on_generic_graph(self) -> None:
        nodes = ["s", "a", "b", "c", "t"]
        edges = [
            module.WeightedEdge("s", "a", 2, 0),
            module.WeightedEdge("s", "b", 1, 0),
            module.WeightedEdge("a", "b", 1, 1),
            module.WeightedEdge("a", "c", 1, 2),
            module.WeightedEdge("a", "t", 1, 7),
            module.WeightedEdge("b", "c", 1, 1),
            module.WeightedEdge("b", "t", 1, 3),
            module.WeightedEdge("c", "t", 2, 1),
        ]

        result = solve_min_cost_max_flow(nodes, edges, "s", "t", target_flow=2)

        self.assertEqual(result.total_flow, 2)
        self.assertEqual(result.total_cost, 5)
        explanation = build_min_cost_flow_explanation(result, target_flow=2)
        self.assertTrue(explanation["target_reached"])
        self.assertTrue(explanation["cost_matches_used_edges"])
        self.assertEqual(explanation["average_cost_per_unit"], 2.5)

    def test_render_min_cost_flow_dot_includes_cost_labels_and_highlights_positive_flow(self) -> None:
        result = solve_min_cost_max_flow(
            ["s", "a", "t"],
            [
                module.WeightedEdge("s", "a", 2, 0),
                module.WeightedEdge("a", "t", 2, 3),
            ],
            "s",
            "t",
            target_flow=2,
        )

        dot = render_min_cost_flow_dot(result, graph_name="tiny_cost_flow", target_flow=2)
        self.assertIn('digraph "tiny_cost_flow"', dot)
        self.assertIn('label="min-cost flow=2, cost=6, target=2, reached=True";', dot)
        self.assertIn('"s" [fillcolor="lightblue", peripheries=2];', dot)
        self.assertIn('"a" -> "t" [label="2/2 @ 3", color="forestgreen", penwidth=3];', dot)

    def test_render_min_cost_flow_markdown_and_svg_include_certificate_details(self) -> None:
        result = solve_min_cost_max_flow(
            ["s", "a", "t"],
            [
                module.WeightedEdge("s", "a", 2, 0),
                module.WeightedEdge("a", "t", 2, 3),
            ],
            "s",
            "t",
            target_flow=2,
        )

        markdown = render_min_cost_flow_markdown(result, graph_name="tiny_cost_flow", target_flow=2)
        self.assertIn('# Min-cost flow proof artifact: `tiny_cost_flow`', markdown)
        self.assertIn('## Edges carrying flow', markdown)
        self.assertIn('## Augmenting paths', markdown)

        svg = render_min_cost_flow_svg(result, graph_name="tiny_cost_flow", target_flow=2)
        self.assertIn("<svg", svg)
        self.assertIn("Min-cost flow proof card", svg)
        self.assertIn("Residual-path certificate", svg)
        self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

    def test_render_min_cost_flow_diagram_svg_highlights_positive_edges_and_valid_xml(self) -> None:
        result = solve_min_cost_max_flow(
            ["s", "a", "b", "t"],
            [
                module.WeightedEdge("s", "a", 1, 0),
                module.WeightedEdge("s", "b", 1, 0),
                module.WeightedEdge("a", "t", 1, 2),
                module.WeightedEdge("b", "t", 1, 5),
            ],
            "s",
            "t",
            target_flow=1,
        )
        svg = render_min_cost_flow_diagram_svg(result, graph_name="tiny_cost_flow", target_flow=1)
        self.assertIn("<svg", svg)
        self.assertIn("Generic min-cost-flow diagram", svg)
        self.assertIn("1/1 @ 2", svg)
        self.assertIn("green edge = shipped path segment", svg)
        self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

    def test_render_min_cost_flow_artifact_html_embeds_diagram_and_proof(self) -> None:
        result = solve_min_cost_max_flow(
            ["s", "a", "t"],
            [
                module.WeightedEdge("s", "a", 2, 0),
                module.WeightedEdge("a", "t", 2, 3),
            ],
            "s",
            "t",
            target_flow=2,
        )
        html = render_min_cost_flow_artifact_html(
            result,
            graph_name="tiny_cost_flow",
            target_flow=2,
            companion_links={"dot": "cost-flow.dot", "markdown": "cost-flow-proof.md", "svg": "cost-flow-proof.svg", "json": "cost-flow-result.json"},
        )
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Generic min-cost-flow artifact page", html)
        self.assertIn("DOT-style shipping/routing diagram", html)
        self.assertIn("Min-cost flow proof card", html)
        self.assertIn('href="cost-flow.dot"', html)
        self.assertIn('href="cost-flow-proof.md"', html)
        self.assertIn('href="cost-flow-proof.svg"', html)
        self.assertIn('href="cost-flow-result.json"', html)
        self.assertIn('id="cost-diagram-title"', html)
        self.assertIn('id="cost-proof-title"', html)
        self.assertNotIn('id="title"', html)
        self.assertNotIn('id="desc"', html)
        self.assertIn('<code>s -&gt; a -&gt; t</code>', html)
        self.assertNotIn('&amp;gt;', html)

    def test_render_artifact_gallery_html_links_assignment_and_cost_pages(self) -> None:
        html = render_artifact_gallery_html(
            assignment_page="sample-assignment-artifact-page.html",
            assignment_proof_svg="sample-assignment-proof.svg",
            assignment_markdown="sample-assignment-proof.md",
            assignment_dot="sample-assignment.dot",
            assignment_json="sample-assignment-result.json",
            cost_page="sample-cost-flow-artifact-page.html",
            cost_proof_svg="sample-cost-flow-proof.svg",
            cost_markdown="sample-cost-flow-proof.md",
            cost_dot="sample-cost-flow.dot",
            cost_json="sample-cost-flow-result.json",
        )
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Network-flow lab artifact gallery", html)
        self.assertIn('href="sample-assignment-artifact-page.html"', html)
        self.assertIn('href="sample-cost-flow-artifact-page.html"', html)
        self.assertIn('href="sample-assignment-proof.svg"', html)
        self.assertIn('href="sample-assignment-result.json"', html)
        self.assertIn('href="sample-cost-flow.dot"', html)
        self.assertIn('href="sample-cost-flow-result.json"', html)
        self.assertIn('iframe src="sample-assignment-artifact-page.html"', html)
        self.assertIn('iframe src="sample-cost-flow-artifact-page.html"', html)

    def test_cli_assign_demo_outputs_assignment_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "assign-demo", "--explain"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "assign-demo")
        self.assertEqual(payload["assignment_count"], 3)
        self.assertEqual(payload["total_cost"], 12)
        self.assertTrue(payload["covers_smaller_partition"])
        self.assertIn("explanation", payload)
        self.assertTrue(payload["explanation"]["cost_matches_flow_total"])

    def test_cli_assign_demo_can_write_dot_markdown_and_svg_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dot_path = Path(tmpdir) / "assignment.dot"
            markdown_path = Path(tmpdir) / "assignment-proof.md"
            svg_path = Path(tmpdir) / "assignment-proof.svg"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "assign-demo",
                    "--dot-out",
                    str(dot_path),
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["dot_output"], str(dot_path))
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertTrue(dot_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertIn('digraph "sample_assignment_graph"', dot_path.read_text(encoding="utf-8"))
            self.assertIn("Weighted assignment proof artifact", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("Weighted assignment proof card", svg_path.read_text(encoding="utf-8"))

    def test_cli_assign_demo_can_write_self_contained_html_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dot_path = Path(tmpdir) / "assignment.dot"
            markdown_path = Path(tmpdir) / "assignment-proof.md"
            svg_path = Path(tmpdir) / "assignment-proof.svg"
            html_path = Path(tmpdir) / "assignment-artifact-page.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "assign-demo",
                    "--dot-out",
                    str(dot_path),
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["html_output"], str(html_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Weighted assignment artifact page", html)
            self.assertIn("DOT-style assignment diagram", html)
            self.assertIn("Weighted assignment proof card", html)
            self.assertIn('href="assignment.dot"', html)
            self.assertIn('href="assignment-proof.md"', html)
            self.assertIn('href="assignment-proof.svg"', html)

    def test_cli_assign_demo_html_output_works_without_companion_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "assignment-artifact-page.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "assign-demo",
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["html_output"], str(html_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Weighted assignment artifact page", html)
            self.assertIn("self-contained", html)
            self.assertNotIn('href="assignment.dot"', html)

    def test_cli_cost_demo_outputs_min_cost_flow_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "cost-demo", "--explain"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "cost-demo")
        self.assertEqual(payload["target_flow"], 2)
        self.assertTrue(payload["target_reached"])
        self.assertEqual(payload["total_flow"], 2)
        self.assertEqual(payload["total_cost"], 5)
        self.assertIn("explanation", payload)
        self.assertTrue(payload["explanation"]["cost_matches_used_edges"])

    def test_cli_cost_demo_can_write_dot_markdown_and_svg_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dot_path = Path(tmpdir) / "cost-flow.dot"
            markdown_path = Path(tmpdir) / "cost-flow-proof.md"
            svg_path = Path(tmpdir) / "cost-flow-proof.svg"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "cost-demo",
                    "--dot-out",
                    str(dot_path),
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["dot_output"], str(dot_path))
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertTrue(dot_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertIn('digraph "sample_cost_flow_graph"', dot_path.read_text(encoding="utf-8"))
            self.assertIn("Min-cost flow proof artifact", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("Min-cost flow proof card", svg_path.read_text(encoding="utf-8"))

    def test_cli_cost_demo_can_write_self_contained_html_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dot_path = Path(tmpdir) / "cost-flow.dot"
            markdown_path = Path(tmpdir) / "cost-flow-proof.md"
            svg_path = Path(tmpdir) / "cost-flow-proof.svg"
            html_path = Path(tmpdir) / "cost-flow-artifact-page.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "cost-demo",
                    "--dot-out",
                    str(dot_path),
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["html_output"], str(html_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Generic min-cost-flow artifact page", html)
            self.assertIn("DOT-style shipping/routing diagram", html)
            self.assertIn("Min-cost flow proof card", html)
            self.assertIn('href="cost-flow.dot"', html)
            self.assertIn('href="cost-flow-proof.md"', html)
            self.assertIn('href="cost-flow-proof.svg"', html)

    def test_cli_cost_demo_html_output_works_without_companion_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "cost-flow-artifact-page.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "cost-demo",
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["html_output"], str(html_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Generic min-cost-flow artifact page", html)
            self.assertIn("self-contained", html)
            self.assertNotIn('href="cost-flow.dot"', html)

    def test_cli_gallery_demo_writes_bundled_artifact_gallery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            for name in [
                "sample-assignment-artifact-page.html",
                "sample-assignment-proof.svg",
                "sample-assignment-proof.md",
                "sample-assignment.dot",
                "sample-assignment-result.json",
                "sample-cost-flow-artifact-page.html",
                "sample-cost-flow-proof.svg",
                "sample-cost-flow-proof.md",
                "sample-cost-flow.dot",
                "sample-cost-flow-result.json",
            ]:
                (artifact_dir / name).write_text(f"placeholder for {name}\n", encoding="utf-8")

            html_path = artifact_dir / "artifact-gallery.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "gallery-demo",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["html_output"], str(html_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Network-flow lab artifact gallery", html)
            self.assertIn('href="sample-assignment-artifact-page.html"', html)
            self.assertIn('href="sample-cost-flow-proof.svg"', html)
            self.assertIn('href="sample-cost-flow-result.json"', html)
            self.assertIn('iframe src="sample-cost-flow-artifact-page.html"', html)

    def test_cli_gallery_demo_requires_existing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            html_path = artifact_dir / "artifact-gallery.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "gallery-demo",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("gallery-demo requires the bundled assignment/cost-flow artifacts to exist first", completed.stderr)

    def test_cli_benchmark_gallery_demo_writes_bundled_benchmark_gallery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            for name in [
                "benchmark-dag-report.svg",
                "benchmark-dag-report.md",
                "benchmark-dag-report.json",
                "benchmark-dense-report.svg",
                "benchmark-dense-report.md",
                "benchmark-dense-report.json",
                "benchmark-layered-report.svg",
                "benchmark-layered-report.md",
                "benchmark-layered-report.json",
                "artifact-gallery.html",
            ]:
                (artifact_dir / name).write_text(f"placeholder for {name}\n", encoding="utf-8")

            html_path = artifact_dir / "benchmark-gallery.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark-gallery-demo",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["html_output"], str(html_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Network-flow lab benchmark gallery", html)
            self.assertIn('href="benchmark-dag-report.svg"', html)
            self.assertIn('href="benchmark-dag-report.json"', html)
            self.assertIn('href="benchmark-layered-report.md"', html)
            self.assertIn('href="artifact-gallery.html"', html)
            self.assertIn('<img src="benchmark-dense-report.svg"', html)

    def test_cli_benchmark_gallery_demo_requires_existing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            html_path = artifact_dir / "benchmark-gallery.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark-gallery-demo",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("benchmark-gallery-demo requires the bundled benchmark markdown/svg artifacts to exist first", completed.stderr)

    def test_cli_showcase_demo_writes_filterable_showcase(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            for name in [
                "artifact-gallery.html",
                "benchmark-gallery.html",
                "sample-flow-proof.svg",
                "sample-flow-proof.md",
                "sample-flow-result.json",
                "sample-matching-proof.svg",
                "sample-matching-proof.md",
                "sample-matching-result.json",
                "sample-assignment-artifact-page.html",
                "sample-assignment-proof.svg",
                "sample-assignment-proof.md",
                "sample-assignment.dot",
                "sample-assignment-result.json",
                "sample-cost-flow-artifact-page.html",
                "sample-cost-flow-proof.svg",
                "sample-cost-flow-proof.md",
                "sample-cost-flow.dot",
                "sample-cost-flow-result.json",
                "benchmark-dag-report.svg",
                "benchmark-dag-report.md",
                "benchmark-dag-report.json",
                "benchmark-dense-report.svg",
                "benchmark-dense-report.md",
                "benchmark-dense-report.json",
                "benchmark-layered-report.svg",
                "benchmark-layered-report.md",
                "benchmark-layered-report.json",
            ]:
                (artifact_dir / name).write_text(f"placeholder for {name}\\n", encoding="utf-8")

            html_path = artifact_dir / "showcase.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "showcase-demo",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["html_output"], str(html_path))
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Network-flow lab showcase", html)
            self.assertIn('data-filter="html"', html)
            self.assertIn('data-filter="json"', html)
            self.assertIn('href="artifact-gallery.html"', html)
            self.assertIn('href="sample-assignment.dot"', html)
            self.assertIn('href="sample-assignment-result.json"', html)
            self.assertIn('iframe src="sample-cost-flow-artifact-page.html"', html)
            self.assertIn('img src="benchmark-layered-report.svg"', html)
            self.assertIn('Replay the bundled sample graph', html)
            self.assertIn('Compare against committed artifact', html)
            self.assertIn('network-flow-showcase-input.json', html)
            self.assertIn('sample-flow-result.json', html)

    def test_cli_showcase_demo_requires_existing_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            html_path = artifact_dir / "showcase.html"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "showcase-demo",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--html-out",
                    str(html_path),
                ],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("showcase-demo requires the bundled galleries and proof/report artifacts to exist first", completed.stderr)

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

    def test_dense_graph_generator_includes_backward_residual_edges(self) -> None:
        graph_a = generate_dense_flow_graph(seed=9, node_count=6, edge_probability=0.7)
        graph_b = generate_dense_flow_graph(seed=9, node_count=6, edge_probability=0.7)
        self.assertEqual(graph_a, graph_b)
        nodes, edges, source, sink = graph_a
        self.assertEqual((source, sink), ("n0", "n5"))
        edge_pairs = {(edge.source, edge.target) for edge in edges}
        self.assertIn(("n2", "n1"), edge_pairs)
        self.assertIn(("n4", "n3"), edge_pairs)
        self.assertIn(("n1", "n5"), edge_pairs)
        self.assertIn(("n0", "n4"), edge_pairs)
        self.assertEqual(nodes, [f"n{i}" for i in range(6)])

    def test_layered_graph_generator_builds_dense_adjacent_layers(self) -> None:
        nodes, edges, source, sink = generate_layered_flow_graph(seed=5, node_count=8, edge_probability=0.25)
        self.assertEqual((source, sink), ("n0", "n7"))
        edge_pairs = {(edge.source, edge.target) for edge in edges}
        for node in ["n1", "n2", "n3"]:
            self.assertIn(("n0", node), edge_pairs)
        for left in ["n1", "n2", "n3"]:
            for right in ["n4", "n5", "n6"]:
                self.assertIn((left, right), edge_pairs)
        for node in ["n4", "n5", "n6"]:
            self.assertIn((node, "n7"), edge_pairs)
        self.assertEqual(nodes, [f"n{i}" for i in range(8)])

    def test_benchmark_reports_matching_algorithms_and_speedup(self) -> None:
        payload = benchmark_algorithms(node_count=12, edge_probability=0.3, trials=3, seed=11)
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["algorithms"], ["edmonds-karp", "dinic"])
        self.assertEqual(payload["generator"]["graph_family"], "dag")
        self.assertEqual(len(payload["trials"]), 3)
        self.assertIn("speedup_ratio", payload["summary"])
        self.assertGreater(payload["summary"]["dinic"]["mean_phases"], 0)
        for trial in payload["trials"]:
            self.assertEqual(trial["edmonds-karp"]["max_flow"], trial["dinic"]["max_flow"])
            self.assertEqual(trial["graph_family"], "dag")

    def test_benchmark_accepts_dense_graph_family(self) -> None:
        payload = benchmark_algorithms(
            node_count=10,
            edge_probability=0.35,
            trials=2,
            seed=4,
            graph_family="dense",
        )
        self.assertEqual(payload["generator"]["graph_family"], "dense")
        self.assertEqual(len(payload["trials"]), 2)
        self.assertTrue(all(trial["graph_family"] == "dense" for trial in payload["trials"]))
        self.assertTrue(all(trial["edge_density"] > 0 for trial in payload["trials"]))

    def test_render_benchmark_markdown_includes_setup_and_trial_table(self) -> None:
        payload = benchmark_algorithms(
            node_count=10,
            edge_probability=0.25,
            trials=2,
            seed=3,
            graph_family="layered",
        )
        artifact = render_benchmark_markdown(payload)
        self.assertIn("# Network-flow benchmark report card", artifact)
        self.assertIn("- Graph family: `layered`", artifact)
        self.assertIn("## Trial table", artifact)
        self.assertIn("| Trial | Seed | Edges | Density | Max flow |", artifact)
        self.assertIn("## Portfolio talking points", artifact)

    def test_render_benchmark_svg_includes_labels_and_valid_xml(self) -> None:
        payload = benchmark_algorithms(
            node_count=10,
            edge_probability=0.25,
            trials=2,
            seed=3,
            graph_family="dense",
        )
        svg = render_benchmark_svg(payload)
        self.assertIn("<svg", svg)
        self.assertIn("Network-flow benchmark report card", svg)
        self.assertIn("Elapsed time (mean ms)", svg)
        self.assertIn("Augmenting paths (mean)", svg)
        self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

    def test_benchmark_rejects_too_few_nodes_for_layered_family(self) -> None:
        with self.assertRaisesRegex(ValueError, "layered benchmark family requires at least 6 nodes"):
            benchmark_algorithms(
                node_count=5,
                edge_probability=0.25,
                trials=1,
                seed=2,
                graph_family="layered",
            )

    def test_cli_benchmark_reports_family_node_requirement_cleanly(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "benchmark",
                "--graph-family",
                "layered",
                "--nodes",
                "4",
                "--trials",
                "1",
                "--seed",
                "1",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--graph-family layered requires --nodes >= 6", completed.stderr)

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

    def test_cli_can_write_flow_svg_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow-proof.svg"
            completed = subprocess.run(
                ["python3", str(MODULE_PATH), "demo", "--svg-out", str(output_path)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "demo")
            self.assertEqual(payload["svg_output"], str(output_path))
            svg = output_path.read_text(encoding="utf-8")
            self.assertIn("Max-flow proof card", svg)
            self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

    def test_cli_demo_can_write_portable_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flow-result.json"
            completed = subprocess.run(
                ["python3", str(MODULE_PATH), "demo", "--json-out", str(output_path)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "demo")
            self.assertEqual(payload["json_output"], str(output_path))
            saved = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["json_output"], "flow-result.json")
            self.assertFalse(saved["graph"].startswith("/"))
            self.assertTrue(saved["graph"].endswith("projects/network-flow-lab/sample_graph.json"))

    def test_cli_can_write_matching_svg_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "matching-proof.svg"
            completed = subprocess.run(
                ["python3", str(MODULE_PATH), "match-demo", "--svg-out", str(output_path)],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "match-demo")
            self.assertEqual(payload["svg_output"], str(output_path))
            svg = output_path.read_text(encoding="utf-8")
            self.assertIn("Bipartite matching proof card", svg)
            self.assertEqual(ET.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")

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
                "--graph-family",
                "layered",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["generator"]["seed"], 5)
        self.assertEqual(payload["generator"]["graph_family"], "layered")
        self.assertEqual(len(payload["trials"]), 2)
        self.assertTrue(all(trial["graph_family"] == "layered" for trial in payload["trials"]))
        self.assertIn("speedup_ratio", payload["summary"])

    def test_cli_benchmark_can_write_markdown_and_svg_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "benchmark-report.md"
            svg_path = Path(tmpdir) / "benchmark-report.svg"
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
                    "--graph-family",
                    "dense",
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertIn("# Network-flow benchmark report card", markdown_path.read_text(encoding="utf-8"))
            svg_text = svg_path.read_text(encoding="utf-8")
            self.assertIn("Network-flow benchmark report card", svg_text)
            self.assertEqual(ET.fromstring(svg_text).tag, "{http://www.w3.org/2000/svg}svg")

    def test_cli_benchmark_can_write_portable_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "benchmark-report.json"
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
                    "--graph-family",
                    "dense",
                    "--json-out",
                    str(json_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["json_output"], str(json_path))
            saved = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["json_output"], "benchmark-report.json")
            self.assertEqual(saved["generator"]["graph_family"], "dense")
            self.assertEqual(len(saved["trials"]), 2)


if __name__ == "__main__":
    unittest.main()
