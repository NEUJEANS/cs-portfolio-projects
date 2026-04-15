import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from avl_tree_lab import AVLTree, build_tree


SCRIPT = PROJECT_DIR / "avl_tree_lab.py"


class AVLTreeLabTests(unittest.TestCase):
    def test_ll_rotation_rebalances_tree(self) -> None:
        tree = build_tree([30, 20, 10])
        self.assertEqual(tree.preorder(), [20, 10, 30])
        self.assertTrue(tree.validate()["is_valid"])

    def test_rr_rotation_rebalances_tree(self) -> None:
        tree = build_tree([10, 20, 30])
        self.assertEqual(tree.preorder(), [20, 10, 30])
        self.assertTrue(tree.validate()["is_valid"])

    def test_lr_rotation_rebalances_tree(self) -> None:
        tree = build_tree([30, 10, 20], trace=True)
        self.assertEqual(tree.preorder(), [20, 10, 30])
        self.assertTrue(any("left-right rotation" in event for event in tree.events))

    def test_rl_rotation_rebalances_tree(self) -> None:
        tree = build_tree([10, 30, 20], trace=True)
        self.assertEqual(tree.preorder(), [20, 10, 30])
        self.assertTrue(any("right-left rotation" in event for event in tree.events))

    def test_delete_root_with_two_children_keeps_tree_valid(self) -> None:
        tree = build_tree([20, 10, 30, 5, 15, 25, 35, 27])
        tree.delete(20)
        self.assertEqual(tree.inorder(), [5, 10, 15, 25, 27, 30, 35])
        self.assertTrue(tree.validate()["is_valid"])

    def test_rank_and_select_queries(self) -> None:
        tree = build_tree([40, 10, 60, 5, 20, 50, 70])
        self.assertEqual(tree.rank(50), 4)
        self.assertEqual(tree.select(0), 5)
        self.assertEqual(tree.select(4), 50)

    def test_duplicate_insert_is_rejected(self) -> None:
        tree = AVLTree()
        tree.insert(10)
        with self.assertRaises(ValueError):
            tree.insert(10)

    def test_missing_delete_raises_key_error(self) -> None:
        tree = build_tree([1, 2, 3])
        with self.assertRaises(KeyError):
            tree.delete(9)

    def test_validation_catches_manual_corruption(self) -> None:
        tree = build_tree([10, 20, 30])
        assert tree.root is not None
        tree.root.height = 99
        report = tree.validate()
        self.assertFalse(report["is_valid"])
        self.assertTrue(any("height mismatch" in issue for issue in report["issues"]))

    def test_cli_delete_outputs_valid_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "delete", "20", "20", "10", "30", "25", "40", "22", "--trace"],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["deleted"], 20)
        self.assertTrue(payload["validation"]["is_valid"])
        self.assertTrue(payload["trace"])
        self.assertTrue(any("successor" in event for event in payload["trace"]))

    def test_cli_error_is_reported_as_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "select", "99", "1", "2", "3"],
            cwd=PROJECT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
