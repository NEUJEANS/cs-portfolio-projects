from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = PROJECT_ROOT / "projects" / "karger-min-cut-lab" / "karger_min_cut.py"
SAMPLE_GRAPH_PATH = PROJECT_ROOT / "projects" / "karger-min-cut-lab" / "sample_graph.json"

spec = importlib.util.spec_from_file_location("karger_min_cut_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

Edge = module.Edge
KargerMinCutLab = module.KargerMinCutLab
UndirectedMultiGraph = module.UndirectedMultiGraph
exact_min_cut_size = module.exact_min_cut_size


class KargerMinCutLabTests(unittest.TestCase):
    def test_edge_normalization_rejects_self_loops(self) -> None:
        with self.assertRaises(ValueError):
            Edge("A", "A").normalized()

    def test_graph_validation_rejects_unknown_vertices(self) -> None:
        with self.assertRaises(ValueError):
            UndirectedMultiGraph(vertices=["A", "B"], edges=[("A", "C")])

    def test_exact_min_cut_matches_triangle_with_tail(self) -> None:
        graph = UndirectedMultiGraph(
            vertices=["A", "B", "C", "D"],
            edges=[("A", "B"), ("A", "C"), ("B", "C"), ("C", "D")],
        )
        self.assertEqual(exact_min_cut_size(graph), 1)

    def test_single_trial_returns_two_partitions_and_positive_cut(self) -> None:
        graph = UndirectedMultiGraph(
            vertices=["A", "B", "C", "D"],
            edges=[("A", "B"), ("A", "C"), ("B", "C"), ("B", "D"), ("C", "D")],
        )
        result = KargerMinCutLab(graph).run_trial(seed=3, include_trace=True)
        self.assertEqual(result["remaining_supernode_count"], 2)
        self.assertEqual(len(result["partitions"]), 2)
        self.assertGreaterEqual(result["cut_size"], 1)
        self.assertTrue(result["contractions"])

    def test_repeated_trials_can_hit_exact_min_cut(self) -> None:
        graph = module.build_sample_graph()
        exact = exact_min_cut_size(graph)
        result = KargerMinCutLab(graph).run_trials(trials=18, seed=4)
        self.assertEqual(result["best_cut_size"], exact)
        self.assertIn(exact, result["histogram"])

    def test_parallel_edges_are_preserved_during_exact_cut_count(self) -> None:
        graph = UndirectedMultiGraph(
            vertices=["A", "B", "C"],
            edges=[("A", "B"), ("A", "B"), ("B", "C"), ("A", "C")],
        )
        self.assertEqual(exact_min_cut_size(graph), 2)

    def test_cli_demo_outputs_exact_check_and_histogram(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo", "--trials", "6", "--seed", "2", "--exact-check"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["algorithm"], "karger-random-contraction")
        self.assertEqual(payload["exact_min_cut_size"], 2)
        self.assertEqual(payload["best_cut_size"], 2)
        self.assertTrue(payload["histogram"])

    def test_cli_run_uses_graph_file(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "run",
                "--graph-file",
                str(SAMPLE_GRAPH_PATH),
                "--trials",
                "10",
                "--seed",
                "11",
                "--exact-check",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["graph_summary"]["vertices"], ["A", "B", "C", "D", "E", "F"])
        self.assertGreaterEqual(payload["best_cut_size"], payload["exact_min_cut_size"])
        self.assertEqual(payload["best_cut_size"], 2)


if __name__ == "__main__":
    unittest.main()
