from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from btree_index import BTreeIndex


SCRIPT_PATH = PROJECT_DIR / "btree_index.py"


def build_sample_tree() -> BTreeIndex:
    tree = BTreeIndex(minimum_degree=2)
    for key, value in [
        (10, "ten"),
        (20, "twenty"),
        (5, "five"),
        (6, "six"),
        (12, "twelve"),
        (30, "thirty"),
        (7, "seven"),
        (17, "seventeen"),
    ]:
        tree.insert(key, value)
    return tree


class BTreeIndexTests(unittest.TestCase):
    def test_insert_search_and_sorted_dump(self) -> None:
        tree = build_sample_tree()

        self.assertEqual(tree.search(6), "six")
        self.assertIsNone(tree.search(99))
        self.assertEqual([item["key"] for item in tree.items()], [5, 6, 7, 10, 12, 17, 20, 30])
        self.assertGreaterEqual(tree.stats()["height"], 2)

    def test_duplicate_key_updates_in_place_without_growing_count(self) -> None:
        tree = build_sample_tree()
        before = tree.stats()["items"]

        tree.insert(12, "TWELVE")

        self.assertEqual(tree.search(12), "TWELVE")
        self.assertEqual(tree.stats()["items"], before)

    def test_range_query_returns_inclusive_sorted_window(self) -> None:
        tree = build_sample_tree()

        self.assertEqual(
            tree.range_query(6, 17),
            [
                {"key": 6, "value": "six"},
                {"key": 7, "value": "seven"},
                {"key": 10, "value": "ten"},
                {"key": 12, "value": "twelve"},
                {"key": 17, "value": "seventeen"},
            ],
        )

    def test_invalid_range_is_rejected(self) -> None:
        tree = build_sample_tree()
        with self.assertRaises(ValueError):
            tree.range_query(9, 4)

    def test_delete_leaf_key_updates_sorted_items_and_count(self) -> None:
        tree = build_sample_tree()

        deleted = tree.delete(6)

        self.assertTrue(deleted)
        self.assertIsNone(tree.search(6))
        self.assertEqual([item["key"] for item in tree.items()], [5, 7, 10, 12, 17, 20, 30])
        self.assertEqual(tree.stats()["items"], 7)

    def test_delete_internal_key_uses_predecessor_or_successor_rebalancing(self) -> None:
        tree = build_sample_tree()

        deleted = tree.delete(10)

        self.assertTrue(deleted)
        self.assertIsNone(tree.search(10))
        self.assertEqual([item["key"] for item in tree.items()], [5, 6, 7, 12, 17, 20, 30])
        self.assertEqual(tree.stats()["items"], 7)

    def test_delete_missing_key_is_false_and_tree_stays_unchanged(self) -> None:
        tree = build_sample_tree()
        before = tree.items()

        deleted = tree.delete(999)

        self.assertFalse(deleted)
        self.assertEqual(tree.items(), before)
        self.assertEqual(tree.stats()["items"], 8)

    def test_repeated_deletions_can_shrink_root_back_to_leaf(self) -> None:
        tree = build_sample_tree()

        for key in [6, 7, 5, 10, 12, 17, 20]:
            self.assertTrue(tree.delete(key))

        self.assertEqual(tree.items(), [{"key": 30, "value": "thirty"}])
        self.assertTrue(tree.root.leaf)
        self.assertEqual(tree.stats()["height"], 1)
        self.assertEqual(tree.stats()["items"], 1)

    def test_cli_range_command_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset = Path(temp_dir) / "records.json"
            dataset.write_text(
                json.dumps(
                    [
                        {"key": 9, "value": "nine"},
                        {"key": 1, "value": "one"},
                        {"key": 14, "value": "fourteen"},
                        {"key": 3, "value": "three"},
                    ]
                )
            )

            completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--dataset", str(dataset), "--json", "range", "2", "10"],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(
            payload["items"],
            [
                {"key": 3, "value": "three"},
                {"key": 9, "value": "nine"},
            ],
        )
        self.assertEqual(payload["stats"]["items"], 4)

    def test_cli_delete_command_outputs_deleted_state_and_remaining_items(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset = Path(temp_dir) / "records.json"
            dataset.write_text(
                json.dumps(
                    [
                        {"key": 9, "value": "nine"},
                        {"key": 1, "value": "one"},
                        {"key": 14, "value": "fourteen"},
                        {"key": 3, "value": "three"},
                    ]
                )
            )

            completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--dataset", str(dataset), "--json", "delete", "9"],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["deleted"])
        self.assertEqual(payload["key"], 9)
        self.assertEqual(payload["stats"]["items"], 3)
        self.assertEqual(
            payload["items"],
            [
                {"key": 1, "value": "one"},
                {"key": 3, "value": "three"},
                {"key": 14, "value": "fourteen"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
