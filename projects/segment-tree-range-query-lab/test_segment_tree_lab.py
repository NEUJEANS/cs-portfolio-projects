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

    def test_parse_numbers_requires_input(self):
        self.assertEqual(parse_numbers("1, 2,3"), [1, 2, 3])
        with self.assertRaises(ValueError):
            parse_numbers(" , ")

    def test_sample_json_shape(self):
        payload = json.loads(run_sample(as_json=True))
        self.assertEqual(payload["before"]["range"], [2, 6])
        self.assertEqual(payload["after_range_add"]["result"]["sum"], 37)

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


if __name__ == "__main__":
    unittest.main()
