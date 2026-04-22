import json
import subprocess
import sys
import tempfile
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
        self.assertEqual(tree.root.subtree_size, 7)

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

    def test_validation_catches_subtree_size_corruption(self) -> None:
        tree = build_tree([10, 20, 30])
        assert tree.root is not None
        tree.root.subtree_size = 99
        report = tree.validate()
        self.assertFalse(report["is_valid"])
        self.assertTrue(any("subtree_size mismatch" in issue for issue in report["issues"]))

    def test_to_dot_includes_height_size_balance_and_nil_leaves(self) -> None:
        tree = build_tree([30, 20, 10, 25, 40])
        dot = tree.to_dot()
        self.assertIn("digraph AVLTree {", dot)
        self.assertIn('label="20\\nh=3\\nsize=5\\nb=-1"', dot)
        self.assertIn('label="NIL"', dot)

    def test_to_dot_can_omit_nil_leaves(self) -> None:
        tree = build_tree([30, 20, 10, 25, 40])
        dot = tree.to_dot(include_nil=False)
        self.assertNotIn('label="NIL"', dot)

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

    def test_cli_dot_outputs_graphviz_payload_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "tree.dot"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "dot",
                    "30",
                    "20",
                    "10",
                    "25",
                    "40",
                    "--output",
                    str(output_path),
                ],
                cwd=PROJECT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command"], "dot")
            self.assertTrue(payload["validation"]["is_valid"])
            self.assertTrue(payload["include_nil"])
            self.assertEqual(payload["output"], str(output_path))
            self.assertIn("digraph AVLTree {", output_path.read_text(encoding="utf-8"))

    def test_cli_explain_trace_build_returns_markdown_walkthrough(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "explain-trace", "build", "30", "20", "10", "25", "40"],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["command"], "explain-trace")
        self.assertEqual(payload["operation"], "build")
        self.assertIn("# AVL Tree Trace Walkthrough (build)", payload["markdown"])
        self.assertIn("### Initial DOT", payload["markdown"])
        self.assertIn("### Final DOT", payload["markdown"])
        self.assertIn("digraph AVLTree {", payload["initial_dot"])
        self.assertIn("digraph AVLTree {", payload["final_dot"])

    def test_cli_explain_trace_delete_writes_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "delete-trace.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "explain-trace",
                    "delete",
                    "20",
                    "10",
                    "30",
                    "5",
                    "15",
                    "25",
                    "35",
                    "--query",
                    "10",
                    "--output",
                    str(output_path),
                ],
                cwd=PROJECT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["operation"], "delete")
            self.assertEqual(payload["deleted"], 10)
            self.assertEqual(payload["query"], 10)
            self.assertEqual(payload["output"], str(output_path))
            markdown = output_path.read_text(encoding="utf-8")
            self.assertIn("delete query: `10`", markdown)
            self.assertIn("## Event-by-event explanation", markdown)
            self.assertIn("delete key 10", markdown)
            self.assertIn("### Final DOT", markdown)

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
