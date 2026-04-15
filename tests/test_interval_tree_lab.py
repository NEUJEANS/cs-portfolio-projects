import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

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


if __name__ == "__main__":
    unittest.main()
