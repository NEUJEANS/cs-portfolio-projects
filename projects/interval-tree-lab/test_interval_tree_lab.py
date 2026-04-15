import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("interval_tree_lab.py")
sys.path.insert(0, str(MODULE_PATH.parent))

from interval_tree_lab import Interval, IntervalTree, benchmark_overlap_series, render_benchmark_series_csv  # noqa: E402


class IntervalTreeLabTests(unittest.TestCase):
    def test_delete_leaf_interval(self) -> None:
        tree = IntervalTree.from_pairs(
            [
                (0, 3, "warmup"),
                (5, 8, "backup"),
                (6, 10, "deploy"),
                (15, 23, "analytics"),
            ]
        )

        deleted = tree.delete(Interval(0, 3, "warmup"))

        self.assertTrue(deleted)
        self.assertEqual(tree.size, 3)
        self.assertEqual(
            tree.inorder(),
            [
                Interval(5, 8, "backup"),
                Interval(6, 10, "deploy"),
                Interval(15, 23, "analytics"),
            ],
        )
        self.assertEqual(tree.root.max_end if tree.root else None, 23)
        self.assertEqual(tree.find_overlaps(Interval(0, 3)), [])
        self.assertEqual(tree.validate(), (True, []))

    def test_delete_interval_with_one_child(self) -> None:
        tree = IntervalTree.from_pairs(
            [
                (5, 8, "backup"),
                (6, 10, "deploy"),
                (7, 9, "qa"),
                (15, 23, "analytics"),
            ]
        )

        deleted = tree.delete(Interval(15, 23, "analytics"))

        self.assertTrue(deleted)
        self.assertEqual(tree.size, 3)
        self.assertNotIn(Interval(15, 23, "analytics"), tree.inorder())
        self.assertEqual(tree.validate(), (True, []))

    def test_delete_interval_with_two_children_uses_successor(self) -> None:
        tree = IntervalTree.from_pairs(
            [
                (0, 3, "warmup"),
                (5, 8, "backup"),
                (6, 10, "deploy"),
                (8, 9, "qa"),
                (15, 23, "analytics"),
                (16, 21, "report"),
                (17, 19, "alerts"),
            ]
        )

        deleted = tree.delete(Interval(8, 9, "qa"))

        self.assertTrue(deleted)
        self.assertEqual(tree.size, 6)
        self.assertNotIn(Interval(8, 9, "qa"), tree.inorder())
        self.assertEqual(tree.find_overlaps(Interval(8, 18)), tree.naive_find_overlaps(Interval(8, 18)))
        self.assertEqual(tree.validate(), (True, []))

    def test_delete_missing_interval_is_noop(self) -> None:
        tree = IntervalTree.from_pairs(
            [
                (0, 3, "warmup"),
                (5, 8, "backup"),
                (6, 10, "deploy"),
            ]
        )
        before = tree.inorder()

        deleted = tree.delete(Interval(9, 12, "missing"))

        self.assertFalse(deleted)
        self.assertEqual(tree.size, 3)
        self.assertEqual(tree.inorder(), before)
        self.assertEqual(tree.validate(), (True, []))

    def test_benchmark_series_rows_stay_valid(self) -> None:
        rows = benchmark_overlap_series(
            interval_counts=[8, 16],
            query_count=6,
            seed=13,
            start_max=40,
            width_max=5,
            query_width_max=6,
        )

        self.assertEqual([row["interval_count"] for row in rows], [8, 16])
        self.assertEqual([row["seed"] for row in rows], [13, 14])
        self.assertTrue(all(row["same_results"] for row in rows))
        self.assertTrue(all(row["valid"] for row in rows))

    def test_render_benchmark_series_csv_has_expected_columns(self) -> None:
        csv_text = render_benchmark_series_csv(
            [
                {
                    "interval_count": 8,
                    "query_count": 6,
                    "seed": 13,
                    "tree_height": 4,
                    "tree_average_ms": 0.001,
                    "naive_average_ms": 0.003,
                    "speedup_vs_naive": 3.0,
                    "average_nodes_visited": 2.5,
                    "worst_nodes_visited": 4,
                    "average_visit_ratio": 0.312,
                    "same_results": True,
                    "valid": True,
                }
            ]
        )

        lines = csv_text.strip().splitlines()
        self.assertEqual(
            lines[0],
            "interval_count,query_count,seed,tree_height,tree_average_ms,naive_average_ms,speedup_vs_naive,average_nodes_visited,worst_nodes_visited,average_visit_ratio,same_results,valid",
        )
        self.assertEqual(lines[1], "8,6,13,4,0.001,0.003,3.0,2.5,4,0.312,true,true")

    def test_cli_benchmark_series_writes_json_and_csv_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "interval-benchmark-series.json"
            csv_path = Path(tmpdir) / "interval-benchmark-series.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "benchmark-series",
                    "--interval-counts",
                    "8,16",
                    "--queries",
                    "6",
                    "--seed",
                    "13",
                    "--start-max",
                    "40",
                    "--width-max",
                    "5",
                    "--query-width-max",
                    "6",
                    "--output-json",
                    str(json_path),
                    "--output-csv",
                    str(csv_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "benchmark-series")
            self.assertEqual(payload["interval_counts"], [8, 16])
            self.assertEqual(payload["json_artifact"], str(json_path))
            self.assertEqual(payload["csv_artifact"], str(csv_path))
            self.assertEqual(len(payload["rows"]), 2)
            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertIn("interval_count,query_count,seed", csv_path.read_text(encoding="utf-8"))
            stored_payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(stored_payload["interval_counts"], [8, 16])

    def test_cli_delete_reports_updated_tree(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "delete",
                "8-9:qa",
                "0-3:warmup",
                "5-8:backup",
                "6-10:deploy",
                "8-9:qa",
                "15-23:analytics",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["deleted"])
        self.assertEqual(payload["size"], 4)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["interval"], {"start": 8, "end": 9, "label": "qa"})
        self.assertNotIn({"start": 8, "end": 9, "label": "qa"}, payload["inorder"])


if __name__ == "__main__":
    unittest.main()
