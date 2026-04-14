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


PROJECT_DIR = Path(__file__).resolve().parent
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


if __name__ == "__main__":
    unittest.main()
