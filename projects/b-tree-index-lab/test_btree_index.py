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

    def test_bulk_load_sorted_builds_searchable_tree(self) -> None:
        records = [
            {"key": 1, "value": "one"},
            {"key": 3, "value": "three"},
            {"key": 5, "value": "five"},
            {"key": 7, "value": "seven"},
            {"key": 9, "value": "nine"},
            {"key": 11, "value": "eleven"},
            {"key": 13, "value": "thirteen"},
        ]

        tree = BTreeIndex.bulk_load_sorted(records, minimum_degree=2)

        self.assertEqual(tree.items(), records)
        self.assertEqual(tree.search(11), "eleven")
        self.assertEqual(tree.stats()["items"], len(records))
        self.assertGreaterEqual(tree.stats()["height"], 2)

    def test_bulk_load_sorted_rejects_duplicate_or_unsorted_keys(self) -> None:
        with self.assertRaises(ValueError):
            BTreeIndex.bulk_load_sorted(
                [
                    {"key": 1, "value": "one"},
                    {"key": 1, "value": "duplicate"},
                ]
            )

        with self.assertRaises(ValueError):
            BTreeIndex.bulk_load_sorted(
                [
                    {"key": 2, "value": "two"},
                    {"key": 1, "value": "one"},
                ]
            )

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

    def test_floor_and_ceil_return_exact_match_when_present(self) -> None:
        tree = build_sample_tree()

        self.assertEqual(tree.floor_item(12), {"key": 12, "value": "twelve"})
        self.assertEqual(tree.ceil_item(12), {"key": 12, "value": "twelve"})

    def test_floor_and_ceil_return_neighboring_keys_for_gaps(self) -> None:
        tree = build_sample_tree()

        self.assertEqual(tree.floor_item(13), {"key": 12, "value": "twelve"})
        self.assertEqual(tree.ceil_item(13), {"key": 17, "value": "seventeen"})
        self.assertEqual(
            tree.neighbors(13),
            {
                "key": 13,
                "floor": {"key": 12, "value": "twelve"},
                "ceil": {"key": 17, "value": "seventeen"},
            },
        )

    def test_floor_and_ceil_handle_out_of_range_keys(self) -> None:
        tree = build_sample_tree()

        self.assertIsNone(tree.floor_item(1))
        self.assertIsNone(tree.ceil_item(99))

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

    def test_serialization_round_trip_restores_items_and_stats(self) -> None:
        tree = build_sample_tree()

        restored = BTreeIndex.from_dict(tree.to_dict())

        self.assertEqual(restored.items(), tree.items())
        self.assertEqual(restored.stats(), tree.stats())
        self.assertEqual(restored.search(17), "seventeen")

    def test_load_rejects_invalid_serialized_tree(self) -> None:
        payload = {
            "minimum_degree": 2,
            "item_count": 2,
            "root": {
                "leaf": False,
                "keys": [10],
                "values": ["ten"],
                "children": [
                    {"leaf": True, "keys": [5, 7], "values": ["five", "seven"]},
                    {"leaf": True, "keys": [], "values": []},
                ],
            },
        }

        with self.assertRaises(ValueError):
            BTreeIndex.from_dict(payload)

    def test_load_rejects_child_keys_that_cross_parent_separator_bounds(self) -> None:
        payload = {
            "minimum_degree": 2,
            "item_count": 3,
            "root": {
                "leaf": False,
                "keys": [10],
                "values": ["ten"],
                "children": [
                    {"leaf": True, "keys": [5], "values": ["five"]},
                    {"leaf": True, "keys": [8], "values": ["eight"]},
                ],
            },
        }

        with self.assertRaises(ValueError):
            BTreeIndex.from_dict(payload)

    def test_benchmark_builds_reports_bulk_load_vs_insert_timings(self) -> None:
        records = [
            {"key": key, "value": f"value-{key}"}
            for key in range(1, 41)
        ]

        benchmark = BTreeIndex.benchmark_builds(records, minimum_degree=3, repeats=2)

        self.assertEqual(benchmark["dataset_items"], 40)
        self.assertEqual(benchmark["minimum_degree"], 3)
        self.assertEqual(benchmark["repeats"], 2)
        self.assertEqual(len(benchmark["baseline_insert"]["runs_ms"]), 2)
        self.assertEqual(len(benchmark["bulk_load"]["runs_ms"]), 2)
        self.assertEqual(benchmark["baseline_insert"]["stats"]["items"], 40)
        self.assertEqual(benchmark["bulk_load"]["stats"]["items"], 40)
        self.assertGreater(benchmark["baseline_insert"]["avg_ms"], 0)
        self.assertGreater(benchmark["bulk_load"]["avg_ms"], 0)
        self.assertIsInstance(benchmark["speedup_vs_insert"], float)

    def test_benchmark_builds_requires_sorted_unique_records_and_positive_repeats(self) -> None:
        with self.assertRaises(ValueError):
            BTreeIndex.benchmark_builds([
                {"key": 2, "value": "two"},
                {"key": 1, "value": "one"},
            ])

        with self.assertRaises(ValueError):
            BTreeIndex.benchmark_builds([
                {"key": 1, "value": "one"},
                {"key": 1, "value": "duplicate"},
            ])

        with self.assertRaises(ValueError):
            BTreeIndex.benchmark_builds([
                {"key": 1, "value": "one"},
                {"key": 2, "value": "two"},
            ], repeats=0)

    def test_cli_bulk_load_flag_builds_from_sorted_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset = Path(temp_dir) / "sorted_records.json"
            dataset.write_text(
                json.dumps(
                    [
                        {"key": 2, "value": "two"},
                        {"key": 4, "value": "four"},
                        {"key": 6, "value": "six"},
                        {"key": 8, "value": "eight"},
                        {"key": 10, "value": "ten"},
                    ]
                )
            )

            completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--dataset", str(dataset), "--bulk-load", "--json", "stats"],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["stats"]["items"], 5)
        self.assertGreaterEqual(payload["stats"]["height"], 2)

    def test_cli_benchmark_build_command_returns_timing_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dataset = Path(temp_dir) / "sorted_records.json"
            dataset.write_text(
                json.dumps(
                    [
                        {"key": key, "value": f"value-{key}"}
                        for key in range(2, 22, 2)
                    ]
                )
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--dataset",
                    str(dataset),
                    "--benchmark-repeats",
                    "2",
                    "--json",
                    "benchmark-build",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

        payload = json.loads(completed.stdout)["benchmark"]
        self.assertEqual(payload["dataset_items"], 10)
        self.assertEqual(payload["repeats"], 2)
        self.assertEqual(payload["baseline_insert"]["stats"]["items"], 10)
        self.assertEqual(payload["bulk_load"]["stats"]["items"], 10)
        self.assertIn("speedup_vs_insert", payload)

    def test_cli_bulk_load_requires_dataset(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--bulk-load", "stats"],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--bulk-load requires --dataset", completed.stderr)

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

    def test_cli_neighbors_command_reports_floor_and_ceil(self) -> None:
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
                [sys.executable, str(SCRIPT_PATH), "--dataset", str(dataset), "--json", "neighbors", "8"],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["key"], 8)
        self.assertEqual(payload["floor"], {"key": 3, "value": "three"})
        self.assertEqual(payload["ceil"], {"key": 9, "value": "nine"})

    def test_cli_floor_command_returns_null_when_no_lower_key_exists(self) -> None:
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
                [sys.executable, str(SCRIPT_PATH), "--dataset", str(dataset), "--json", "floor", "0"],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload, {"key": 0, "item": None})

    def test_cli_save_and_tree_file_search_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            dataset = temp_path / "records.json"
            tree_file = temp_path / "tree.json"
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

            save_completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--dataset", str(dataset), "--json", "save", str(tree_file)],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )
            search_completed = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--tree-file", str(tree_file), "--json", "search", "14"],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )

        save_payload = json.loads(save_completed.stdout)
        search_payload = json.loads(search_completed.stdout)
        self.assertEqual(save_payload["saved"], str(tree_file))
        self.assertEqual(save_payload["stats"]["items"], 4)
        self.assertEqual(search_payload, {"key": 14, "value": "fourteen"})


if __name__ == "__main__":
    unittest.main()
