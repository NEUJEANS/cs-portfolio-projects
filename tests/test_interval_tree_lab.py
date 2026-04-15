import importlib.util
import json
import pathlib
import tempfile
import subprocess
import sys
import unittest
from unittest import mock

MODULE_PATH = pathlib.Path("projects/interval-tree-lab/interval_tree_lab.py")
spec = importlib.util.spec_from_file_location("interval_tree_lab", MODULE_PATH)
interval_tree_lab = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = interval_tree_lab
spec.loader.exec_module(interval_tree_lab)

Interval = interval_tree_lab.Interval
IntervalTree = interval_tree_lab.IntervalTree
benchmark_overlap_queries = interval_tree_lab.benchmark_overlap_queries
parse_interval_spec = interval_tree_lab.parse_interval_spec
render_query_trace_artifact = interval_tree_lab.render_query_trace_artifact


class IntervalTreeLabTests(unittest.TestCase):
    def test_build_balanced_tree_and_validate(self) -> None:
        tree = IntervalTree(
            [
                Interval(15, 23, "analytics"),
                Interval(5, 8, "backup"),
                Interval(17, 19, "alerts"),
                Interval(6, 10, "deploy"),
                Interval(8, 9, "qa"),
            ]
        )
        valid, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.inorder(), sorted(tree.inorder()))
        self.assertEqual(tree.root.max_end, 23)
        self.assertLessEqual(tree.height(), 3)

    def test_find_any_and_all_overlaps(self) -> None:
        tree = IntervalTree(
            [
                Interval(0, 3, "warmup"),
                Interval(5, 8, "backup"),
                Interval(6, 10, "deploy"),
                Interval(8, 9, "qa"),
                Interval(15, 23, "analytics"),
                Interval(17, 19, "alerts"),
            ]
        )
        query = Interval(7, 18)
        any_hit = tree.find_any_overlap(query)
        self.assertIsNotNone(any_hit)
        overlaps = tree.find_overlaps(query)
        self.assertEqual(
            [interval.label for interval in overlaps],
            ["backup", "deploy", "qa", "analytics", "alerts"],
        )

    def test_query_stats_match_naive_scan_and_show_pruning(self) -> None:
        intervals = [
            Interval(0, 2, "a"),
            Interval(4, 5, "b"),
            Interval(7, 9, "c"),
            Interval(12, 14, "d"),
            Interval(15, 18, "e"),
            Interval(21, 24, "f"),
            Interval(30, 33, "g"),
        ]
        tree = IntervalTree(intervals)
        query = Interval(13, 16, "query")
        hits, stats = tree.find_overlaps_with_stats(query)
        self.assertEqual(hits, tree.naive_find_overlaps(query))
        self.assertLess(stats.nodes_visited, len(intervals))
        self.assertEqual([interval.label for interval in hits], ["d", "e"])

    def test_point_query_and_insert_reject_duplicate(self) -> None:
        tree = IntervalTree([Interval(25, 30, "etl"), Interval(26, 26, "ping")])
        self.assertTrue(tree.insert(Interval(19, 20, "maintenance")))
        self.assertFalse(tree.insert(Interval(19, 20, "maintenance")))
        hits = tree.find_point(26)
        self.assertEqual([interval.label for interval in hits], ["etl", "ping"])
        valid, errors = tree.validate()
        self.assertTrue(valid, errors)

    def test_parse_interval_spec(self) -> None:
        parsed = parse_interval_spec("5-8:backup")
        self.assertEqual(parsed, Interval(5, 8, "backup"))
        without_label = parse_interval_spec("3-3")
        self.assertEqual(without_label, Interval(3, 3, None))
        with self.assertRaises(ValueError):
            parse_interval_spec("9-4:broken")

    def test_benchmark_summary_reports_matching_results(self) -> None:
        summary = benchmark_overlap_queries(
            interval_count=120,
            query_count=40,
            seed=11,
            start_max=400,
            width_max=15,
            query_width_max=20,
        )
        self.assertTrue(summary["same_results"])
        self.assertEqual(summary["interval_count"], 120)
        self.assertEqual(summary["query_count"], 40)
        self.assertIsNotNone(summary["sample_query"])
        self.assertEqual(summary["sample_tree_hits"], summary["sample_naive_hits"])
        self.assertLessEqual(summary["average_visit_ratio"], 1.0)

    def test_cli_overlap_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "projects/interval-tree-lab/interval_tree_lab.py",
                "overlap",
                "7-18",
                "0-3:warmup",
                "5-8:backup",
                "6-10:deploy",
                "15-23:analytics",
                "17-19:alerts",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["query"], {"start": 7, "end": 18})
        self.assertGreater(payload["query_stats"]["nodes_visited"], 0)
        self.assertEqual(
            [entry.get("label") for entry in payload["all_overlaps"]],
            ["backup", "deploy", "analytics", "alerts"],
        )

    def test_cli_benchmark_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "projects/interval-tree-lab/interval_tree_lab.py",
                "benchmark",
                "--intervals",
                "150",
                "--queries",
                "30",
                "--seed",
                "5",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "benchmark")
        self.assertTrue(payload["same_results"])
        self.assertEqual(payload["interval_count"], 150)
        self.assertEqual(payload["query_count"], 30)
        self.assertIn("tree_height", payload)
        self.assertNotIn("inorder", payload)
        self.assertLessEqual(payload["worst_nodes_visited"], payload["interval_count"])

    def test_cli_benchmark_rejects_non_positive_counts(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "projects/interval-tree-lab/interval_tree_lab.py",
                "benchmark",
                "--intervals",
                "0",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--intervals must be positive", completed.stderr)

    def test_export_query_trace_dot_marks_pruned_and_overlap_edges(self) -> None:
        tree = IntervalTree(
            [
                Interval(0, 3, "warmup"),
                Interval(5, 8, "backup"),
                Interval(6, 10, "deploy"),
                Interval(15, 23, "analytics"),
                Interval(17, 19, "alerts"),
            ]
        )
        dot = tree.export_query_trace_dot(Interval(7, 18, "query"))
        self.assertIn('digraph interval_tree_query_trace', dot)
        self.assertIn('pruned: left.max_end < query.start', dot)
        self.assertIn('search right', dot)
        self.assertIn('label="overlap"', dot)

    def test_render_query_trace_artifact_writes_dot_file(self) -> None:
        dot = IntervalTree([Interval(1, 3, "a")]).export_query_trace_dot(Interval(2, 2, "q"))
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir) / "trace.dot"
            written = render_query_trace_artifact(dot_text=dot, output_path=target, artifact_format="dot")
            self.assertEqual(written, target)
            self.assertEqual(target.read_text(encoding="utf-8"), dot)

    def test_render_query_trace_artifact_requires_graphviz_for_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(interval_tree_lab.shutil, "which", return_value=None):
            target = pathlib.Path(tmpdir) / "trace.svg"
            with self.assertRaisesRegex(ValueError, "Graphviz 'dot' is required"):
                render_query_trace_artifact(dot_text="digraph g {}", output_path=target, artifact_format="svg")

    def test_cli_trace_output_includes_dot_and_hits(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "projects/interval-tree-lab/interval_tree_lab.py",
                "trace",
                "7-18",
                "0-3:warmup",
                "5-8:backup",
                "6-10:deploy",
                "15-23:analytics",
                "17-19:alerts",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "trace")
        self.assertEqual(
            [entry.get("label") for entry in payload["all_overlaps"]],
            ["backup", "deploy", "analytics", "alerts"],
        )
        self.assertIn('digraph interval_tree_query_trace', payload["query_trace_dot"])
        self.assertIn('pruned: left.max_end < query.start', payload["query_trace_dot"])

    def test_cli_trace_can_write_dot_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            target = pathlib.Path(tmpdir) / "trace.dot"
            completed = subprocess.run(
                [
                    sys.executable,
                    "projects/interval-tree-lab/interval_tree_lab.py",
                    "trace",
                    "7-18",
                    "0-3:warmup",
                    "5-8:backup",
                    "6-10:deploy",
                    "15-23:analytics",
                    "17-19:alerts",
                    "--output",
                    str(target),
                    "--format",
                    "dot",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["artifact"], {"path": str(target), "format": "dot"})
            self.assertTrue(target.exists())
            self.assertIn('digraph interval_tree_query_trace', target.read_text(encoding="utf-8"))

    def test_cli_trace_rejects_format_without_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "projects/interval-tree-lab/interval_tree_lab.py",
                "trace",
                "7-18",
                "0-3:warmup",
                "5-8:backup",
                "--format",
                "svg",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--format only applies when --output is provided", completed.stderr)


if __name__ == "__main__":
    unittest.main()
