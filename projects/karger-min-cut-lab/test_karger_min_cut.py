from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
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
benchmark_graph_families = module.benchmark_graph_families
build_barbell_graph = module.build_barbell_graph
build_complete_graph = module.build_complete_graph
build_cycle_graph = module.build_cycle_graph
build_erdos_renyi_graph = module.build_erdos_renyi_graph
build_trace_dot = module.build_trace_dot
exact_min_cut_size = module.exact_min_cut_size
is_connected = module.is_connected
write_trace_dot_snapshots = module.write_trace_dot_snapshots


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

    def test_graph_family_builders_have_expected_min_cuts(self) -> None:
        self.assertEqual(exact_min_cut_size(build_cycle_graph(5)), 2)
        self.assertEqual(exact_min_cut_size(build_complete_graph(5)), 4)
        self.assertEqual(exact_min_cut_size(build_barbell_graph(4)), 1)

    def test_random_graph_builder_returns_connected_graph(self) -> None:
        graph = build_erdos_renyi_graph(vertex_count=6, edge_probability=0.4, seed=7)
        self.assertTrue(is_connected(graph))
        self.assertGreaterEqual(len(graph.edges), len(graph.vertices) - 1)

    def test_benchmark_graph_families_reports_exact_hits(self) -> None:
        payload = benchmark_graph_families(
            families=["cycle", "complete"],
            sizes=[4],
            trials=10,
            instances_per_size=1,
            seed=5,
        )
        self.assertEqual(payload["benchmark"]["total_instances"], 2)
        self.assertEqual(len(payload["rows"]), 2)
        self.assertEqual({row["family"] for row in payload["rows"]}, {"cycle", "complete"})
        self.assertTrue(all("hit_exact_cut" in row for row in payload["rows"]))
        self.assertEqual(len(payload["family_summary"]), 2)

    def test_trace_dot_builder_renders_parallel_edges(self) -> None:
        graph = module.build_sample_graph()
        payload = KargerMinCutLab(graph).run_trials(trials=2, seed=4, include_trace=True)
        payload["graph_summary"] = {"vertices": graph.vertices, "edge_count": len(graph.edges)}
        payload["input_edges"] = [list(edge) for edge in graph.edges]
        dot_text = build_trace_dot(payload, step=0)
        self.assertIn('graph KargerTrace {', dot_text)
        self.assertIn('label="Karger trace step 0"', dot_text)
        self.assertIn('penwidth=', dot_text)

    def test_trace_dot_writer_emits_one_file_per_step(self) -> None:
        graph = module.build_sample_graph()
        payload = KargerMinCutLab(graph).run_trials(trials=1, seed=3, include_trace=True)
        payload["graph_summary"] = {"vertices": graph.vertices, "edge_count": len(graph.edges)}
        payload["input_edges"] = [list(edge) for edge in graph.edges]
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_trace_dot_snapshots(Path(tmpdir), payload)
            self.assertEqual(len(paths), len(payload["trial_results"][0]["contractions"]) + 1)
            self.assertTrue(paths[0].exists())
            self.assertIn('step-00.dot', str(paths[0]))
            self.assertIn('Karger trace step 1', paths[1].read_text())

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

    def test_cli_run_requires_graph_file(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "run"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--graph-file is required", completed.stderr)

    def test_cli_benchmark_writes_json_and_csv_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "benchmark.json"
            csv_path = Path(tmpdir) / "benchmark.csv"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--families",
                    "cycle,barbell",
                    "--sizes",
                    "4",
                    "--instances-per-size",
                    "1",
                    "--trials",
                    "8",
                    "--seed",
                    "3",
                    "--output-json",
                    str(json_path),
                    "--output-csv",
                    str(csv_path),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["benchmark"]["total_instances"], 2)
            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())
            csv_text = csv_path.read_text()
            self.assertIn("family,size_parameter", csv_text)
            self.assertIn("barbell", csv_text)

    def test_cli_trace_dot_dir_writes_snapshot_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_dir = Path(tmpdir) / "trace"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "demo",
                    "--trials",
                    "2",
                    "--seed",
                    "4",
                    "--trace-dot-dir",
                    str(trace_dir),
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertTrue(payload["trace_dot_files"])
            self.assertTrue(trace_dir.exists())
            self.assertIn("step-00.dot", payload["trace_dot_files"][0])
            self.assertIn("Karger trace step 0", Path(payload["trace_dot_files"][0]).read_text())


if __name__ == "__main__":
    unittest.main()
