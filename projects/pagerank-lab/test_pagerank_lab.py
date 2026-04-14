from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from pagerank_lab import DirectedGraph, compute_pagerank


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "pagerank_lab.py"
SAMPLE = PROJECT_DIR / "sample_graph.txt"


class DirectedGraphTests(unittest.TestCase):
    def test_from_edge_list_file_rejects_invalid_line(self) -> None:
        with tempfile.NamedTemporaryFile("w+", delete=False) as handle:
            handle.write("a b c\n")
            path = Path(handle.name)
        self.addCleanup(path.unlink)
        with self.assertRaises(ValueError):
            DirectedGraph.from_edge_list_file(path)

    def test_graph_includes_sink_targets(self) -> None:
        graph = DirectedGraph.from_edges([("a", "b")])
        self.assertEqual(graph.nodes, ["a", "b"])
        self.assertEqual(graph.outgoing("b"), set())


class PageRankTests(unittest.TestCase):
    def test_scores_sum_to_one(self) -> None:
        graph = DirectedGraph.from_edge_list_file(SAMPLE)
        result = compute_pagerank(graph)
        self.assertAlmostEqual(sum(result.scores.values()), 1.0, places=9)
        self.assertTrue(result.converged)

    def test_dangling_node_retains_non_zero_rank(self) -> None:
        graph = DirectedGraph.from_edges([("a", "b"), ("b", "a"), ("c", "c")])
        result = compute_pagerank(graph)
        self.assertGreater(result.scores["c"], 0.0)
        self.assertAlmostEqual(sum(result.scores.values()), 1.0, places=9)

    def test_top_nodes_are_sorted_by_score_then_name(self) -> None:
        graph = DirectedGraph.from_edges([
            ("home", "docs"),
            ("about", "docs"),
            ("docs", "home"),
            ("blog", "docs"),
        ])
        result = compute_pagerank(graph)
        top = result.top(3)
        self.assertEqual(top[0]["node"], "docs")
        self.assertEqual(len(top), 3)

    def test_invalid_parameters_raise(self) -> None:
        graph = DirectedGraph.from_edges([("a", "b")])
        with self.assertRaises(ValueError):
            compute_pagerank(graph, damping=1.5)
        with self.assertRaises(ValueError):
            compute_pagerank(graph, max_iterations=0)
        with self.assertRaises(ValueError):
            compute_pagerank(graph, tolerance=0)


    def test_sample_graph_reports_sink_node(self) -> None:
        graph = DirectedGraph.from_edge_list_file(SAMPLE)
        self.assertEqual(graph.outgoing("sink"), set())
        result = compute_pagerank(graph)
        self.assertGreater(result.scores["sink"], 0.0)


class CliTests(unittest.TestCase):
    def test_rank_command_outputs_json(self) -> None:
        completed = subprocess.run(
            ["python3", str(SCRIPT), "rank", str(SAMPLE), "--top", "2"],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["node_count"], 6)
        self.assertEqual(len(payload["top"]), 2)
        self.assertIn("scores", payload)
        self.assertAlmostEqual(payload["score_sum"], 1.0, places=9)

    def test_inspect_command_lists_dangling_nodes(self) -> None:
        with tempfile.NamedTemporaryFile("w+", delete=False) as handle:
            handle.write("a b\n")
            path = Path(handle.name)
        self.addCleanup(path.unlink)
        completed = subprocess.run(
            ["python3", str(SCRIPT), "inspect", str(path)],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["dangling_nodes"], ["b"])


if __name__ == "__main__":
    unittest.main()
