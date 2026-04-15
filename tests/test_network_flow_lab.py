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
load_graph = module.load_graph
load_bipartite_graph = module.load_bipartite_graph
render_flow_dot = module.render_flow_dot
render_matching_dot = module.render_matching_dot
solve_max_flow = module.solve_max_flow
solve_bipartite_matching = module.solve_bipartite_matching


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

        result = solve_bipartite_matching(left, right, edges).to_dict()

        self.assertEqual(result["match_count"], 3)
        self.assertEqual(result["unmatched_left"], ["david"])
        self.assertEqual(result["unmatched_right"], [])
        matches = {(item["left"], item["right"]) for item in result["matches"]}
        self.assertEqual(matches, {("anna", "api"), ("ben", "database"), ("chloe", "compiler")})
        self.assertEqual(result["flow"]["max_flow"], 3)

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

    def test_render_matching_dot_highlights_matches(self) -> None:
        result = solve_bipartite_matching(
            ["anna", "ben"],
            ["api", "db"],
            [("anna", "api"), ("ben", "api")],
        )
        dot = render_matching_dot(result, graph_name="tiny_matching")
        self.assertIn('digraph "tiny_matching"', dot)
        self.assertIn('"anna" -> "api" [color="forestgreen", penwidth=3, label="match"];', dot)
        self.assertIn('"db" [fillcolor="moccasin"];', dot)

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
        self.assertTrue(payload["augmenting_paths"])

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


if __name__ == "__main__":
    unittest.main()
