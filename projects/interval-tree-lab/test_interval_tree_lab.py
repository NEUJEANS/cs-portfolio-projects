import json
import subprocess
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("interval_tree_lab.py")
sys.path.insert(0, str(MODULE_PATH.parent))

from interval_tree_lab import Interval, IntervalTree  # noqa: E402


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
