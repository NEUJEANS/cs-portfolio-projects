import json
import subprocess
import sys
import unittest
from pathlib import Path

from segment_tree_lab import SegmentTree, parse_numbers, run_sample

PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "segment_tree_lab.py"


class SegmentTreeTests(unittest.TestCase):
    def test_range_query_returns_sum_min_max(self):
        tree = SegmentTree([5, 2, 8, 6, 1])
        result = tree.range_query(1, 3)
        self.assertEqual(result.total, 16)
        self.assertEqual(result.minimum, 2)
        self.assertEqual(result.maximum, 8)

    def test_lazy_range_add_updates_future_queries(self):
        tree = SegmentTree([1, 3, 5, 7, 9, 11])
        tree.range_add(1, 4, 2)
        result = tree.range_query(0, 5)
        self.assertEqual(result.total, 44)
        middle = tree.range_query(2, 4)
        self.assertEqual(middle.to_dict(), {"sum": 27, "min": 7, "max": 11})
        self.assertEqual(tree.materialize(), [1, 5, 7, 9, 11, 11])

    def test_range_set_overrides_prior_range_add_and_future_queries(self):
        tree = SegmentTree([1, 3, 5, 7, 9, 11])
        tree.range_add(1, 4, 2)
        tree.range_set(2, 4, 6)
        self.assertEqual(tree.materialize(), [1, 5, 6, 6, 6, 11])
        self.assertEqual(tree.range_query(1, 4).to_dict(), {"sum": 23, "min": 5, "max": 6})

    def test_range_add_after_range_set_accumulates(self):
        tree = SegmentTree([10, 20, 30, 40])
        tree.range_set(1, 3, 5)
        tree.range_add(2, 3, 4)
        self.assertEqual(tree.materialize(), [10, 5, 9, 9])
        self.assertEqual(tree.range_query(0, 3).to_dict(), {"sum": 33, "min": 5, "max": 10})

    def test_point_set_overwrites_single_position(self):
        tree = SegmentTree([4, 4, 4])
        tree.point_set(1, 10)
        self.assertEqual(tree.materialize(), [4, 10, 4])
        self.assertEqual(tree.range_query(0, 2).to_dict(), {"sum": 18, "min": 4, "max": 10})

    def test_invalid_ranges_raise(self):
        tree = SegmentTree([1, 2, 3])
        with self.assertRaises(ValueError):
            tree.range_query(2, 1)
        with self.assertRaises(IndexError):
            tree.range_add(0, 3, 1)
        with self.assertRaises(IndexError):
            tree.range_set(-1, 1, 5)

    def test_parse_numbers_requires_input(self):
        self.assertEqual(parse_numbers("1, 2,3"), [1, 2, 3])
        with self.assertRaises(ValueError):
            parse_numbers(" , ")

    def test_sample_json_shape(self):
        payload = json.loads(run_sample(as_json=True))
        self.assertEqual(payload["before"]["range"], [2, 6])
        self.assertEqual(payload["after_range_add"]["result"]["sum"], 37)
        self.assertEqual(payload["after_range_set"]["result"], {"sum": 33, "min": 6, "max": 9})

    def test_cli_query_command(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "query", "--numbers", "2,4,6,8", "--left", "1", "--right", "3"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["result"], {"sum": 18, "min": 4, "max": 8})

    def test_cli_range_add_command(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "range-add",
                "--numbers",
                "1,2,3,4",
                "--left",
                "1",
                "--right",
                "2",
                "--delta",
                "5",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["updated_values"], [1, 7, 8, 4])
        self.assertEqual(payload["after"]["result"], {"sum": 15, "min": 7, "max": 8})

    def test_cli_range_set_command(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "range-set",
                "--numbers",
                "2,4,6,8",
                "--left",
                "1",
                "--right",
                "3",
                "--value",
                "5",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["updated_values"], [2, 5, 5, 5])
        self.assertEqual(payload["after"]["result"], {"sum": 15, "min": 5, "max": 5})


if __name__ == "__main__":
    unittest.main()
