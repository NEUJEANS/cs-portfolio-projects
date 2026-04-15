from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "red-black-tree-lab" / "red_black_tree.py"

spec = importlib.util.spec_from_file_location("red_black_tree_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

BLACK = module.BLACK
build_tree = module.build_tree


class RedBlackTreeLabTests(unittest.TestCase):
    def test_sorted_insertions_stay_valid_and_balanced(self) -> None:
        tree = build_tree([10, 20, 30, 40, 50, 60, 70])
        valid, black_height, errors = tree.validate()
        self.assertTrue(valid, errors)
        self.assertEqual(tree.root.key, 20)
        self.assertEqual(tree.root.color, BLACK)
        self.assertEqual(tree.inorder(), [10, 20, 30, 40, 50, 60, 70])
        self.assertLessEqual(tree.height(), 4)
        self.assertGreaterEqual(black_height, 2)

    def test_duplicate_insertions_are_rejected_without_size_growth(self) -> None:
        tree = build_tree([7, 3, 18, 10])
        self.assertFalse(tree.insert(10))
        self.assertEqual(tree.size, 4)
        valid, _, errors = tree.validate()
        self.assertTrue(valid, errors)

    def test_contains_queries_existing_and_missing_keys(self) -> None:
        tree = build_tree([11, 2, 14, 1, 7, 15, 5, 8])
        self.assertTrue(tree.contains(7))
        self.assertTrue(tree.contains(15))
        self.assertFalse(tree.contains(6))

    def test_summary_reports_validation_state(self) -> None:
        tree = build_tree([41, 38, 31, 12, 19, 8])
        summary = tree.summary()
        self.assertTrue(summary["valid"], summary["errors"])
        self.assertEqual(summary["root"]["color"], BLACK)
        self.assertEqual(summary["inorder"], [8, 12, 19, 31, 38, 41])

    def test_validate_catches_parent_pointer_corruption(self) -> None:
        tree = build_tree([10, 5, 15])
        tree.root.left.parent = None
        valid, _, errors = tree.validate()
        self.assertFalse(valid)
        self.assertTrue(any("parent pointer mismatch" in error for error in errors))

    def test_cli_demo_outputs_expected_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "demo")
        self.assertTrue(payload["valid"], payload["errors"])
        self.assertEqual(payload["contains"], {"8": True, "15": False})

    def test_cli_contains_command_respects_query(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "contains", "25", "10", "20", "30", "15", "25", "5"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "contains")
        self.assertEqual(payload["query"], 25)
        self.assertTrue(payload["found"])
        self.assertTrue(payload["valid"], payload["errors"])


if __name__ == "__main__":
    unittest.main()
