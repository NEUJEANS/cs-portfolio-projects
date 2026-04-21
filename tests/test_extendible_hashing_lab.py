from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "projects/extendible-hashing-lab/extendible_hashing_lab.py"
SAMPLE_WORKLOAD = REPO_ROOT / "projects/extendible-hashing-lab/sample_workload.json"
BENCHMARK_SUITE = REPO_ROOT / "projects/extendible-hashing-lab/benchmark_suite.json"
SPEC = importlib.util.spec_from_file_location("extendible_hashing_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
BenchmarkError = MODULE.BenchmarkError
ExtendibleHashTable = MODULE.ExtendibleHashTable
LinearProbingHashTable = MODULE.LinearProbingHashTable
SnapshotError = MODULE.SnapshotError
WorkloadError = MODULE.WorkloadError
load_snapshot = MODULE.load_snapshot
render_benchmark_dashboard_html = MODULE.render_benchmark_dashboard_html
render_visualization_html = MODULE.render_visualization_html
render_visualization_svg = MODULE.render_visualization_svg
run_benchmark_suite = MODULE.run_benchmark_suite
run_workload = MODULE.run_workload
stable_hash = MODULE.stable_hash
summarize_benchmark_trials = MODULE.summarize_benchmark_trials
validate_benchmark_suite = MODULE.validate_benchmark_suite
validate_workload = MODULE.validate_workload


def colliding_keys(depth: int, count: int, suffix: int = 0) -> list[str]:
    mask = (1 << depth) - 1 if depth else 0
    found: list[str] = []
    index = 0
    while len(found) < count:
        candidate = f"collision:{depth}:{suffix}:{index}"
        if stable_hash(candidate) & mask == suffix:
            found.append(candidate)
        index += 1
    return found


def linear_collision_keys(capacity: int, count: int, slot: int = 0) -> list[str]:
    found: list[str] = []
    index = 0
    while len(found) < count:
        candidate = f"linear:{capacity}:{slot}:{index}"
        if stable_hash(f"linear-probing::{candidate}") % capacity == slot:
            found.append(candidate)
        index += 1
    return found


class ExtendibleHashingLabTests(unittest.TestCase):
    def test_insert_lookup_and_directory_growth(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        keys = colliding_keys(depth=2, count=3, suffix=0)
        for index, key in enumerate(keys):
            table.put(key, f"value-{index}")

        self.assertGreaterEqual(table.global_depth, 2)
        self.assertGreaterEqual(len(table.buckets), 2)
        for index, key in enumerate(keys):
            self.assertEqual(table.get(key), f"value-{index}")

        stats = table.stats()
        self.assertEqual(stats["entry_count"], 3)
        self.assertTrue(any(bucket["local_depth"] >= 2 for bucket in stats["buckets"]))

    def test_update_and_delete_round_trip(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        table.put("alpha", "1")
        table.put("beta", "2")
        self.assertEqual(table.put("alpha", "10"), "updated")
        self.assertEqual(table.get("alpha"), "10")
        self.assertTrue(table.delete("beta"))
        self.assertFalse(table.delete("beta"))
        self.assertIsNone(table.get("beta"))

    def test_linear_probing_reuses_tombstone_slots(self) -> None:
        table = LinearProbingHashTable(capacity=4, max_load_factor=0.95, max_tombstone_ratio=0.9)
        alpha, beta, gamma = linear_collision_keys(capacity=4, count=3, slot=0)
        table.put(alpha, "1")
        table.put(beta, "2")
        table.put(gamma, "3")

        self.assertTrue(table.delete(beta))
        self.assertEqual(table.stats()["tombstones"], 1)
        self.assertEqual(table.put(beta, "2b"), "inserted")
        self.assertEqual(table.get(beta), "2b")
        stats = table.stats()
        self.assertEqual(stats["tombstones"], 0)
        self.assertEqual(stats["size"], 3)
        self.assertGreaterEqual(stats["max_probe_count"], 2)

    def test_delete_merges_buddy_bucket_and_shrinks_directory(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        suffix_zero_keys = colliding_keys(depth=1, count=2, suffix=0)
        suffix_one_key = colliding_keys(depth=1, count=1, suffix=1)[0]

        table.put(suffix_zero_keys[0], "a")
        table.put(suffix_one_key, "b")
        table.put(suffix_zero_keys[1], "c")
        self.assertEqual(table.global_depth, 1)
        self.assertEqual(len(table.buckets), 2)

        self.assertTrue(table.delete(suffix_one_key))
        self.assertEqual(table.global_depth, 0)
        self.assertEqual(len(table.buckets), 1)
        only_bucket = next(iter(table.buckets.values()))
        self.assertEqual(only_bucket.local_depth, 0)
        self.assertEqual(only_bucket.entries, {suffix_zero_keys[0]: "a", suffix_zero_keys[1]: "c"})

    def test_delete_can_cascade_merges_across_multiple_levels(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        suffix_zero_keys = colliding_keys(depth=2, count=2, suffix=0)
        suffix_one_key = colliding_keys(depth=2, count=1, suffix=1)[0]
        suffix_two_key = colliding_keys(depth=2, count=1, suffix=2)[0]

        table.put(suffix_zero_keys[0], "zero-a")
        table.put(suffix_one_key, "one")
        table.put(suffix_zero_keys[1], "zero-b")
        table.put(suffix_two_key, "two")

        self.assertEqual(table.global_depth, 2)
        self.assertEqual(len(table.buckets), 3)

        self.assertTrue(table.delete(suffix_two_key))
        self.assertEqual(table.global_depth, 1)
        self.assertEqual(len(table.buckets), 2)
        self.assertEqual(table.get(suffix_zero_keys[0]), "zero-a")
        self.assertEqual(table.get(suffix_zero_keys[1]), "zero-b")
        self.assertEqual(table.get(suffix_one_key), "one")

        self.assertTrue(table.delete(suffix_one_key))
        self.assertEqual(table.global_depth, 0)
        self.assertEqual(len(table.buckets), 1)
        self.assertEqual(table.get(suffix_zero_keys[0]), "zero-a")
        self.assertEqual(table.get(suffix_zero_keys[1]), "zero-b")

    def test_delete_does_not_merge_when_buddy_depth_differs(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        suffix_zero_keys = colliding_keys(depth=2, count=2, suffix=0)
        suffix_one_key = colliding_keys(depth=2, count=1, suffix=1)[0]
        suffix_two_key = colliding_keys(depth=2, count=1, suffix=2)[0]

        table.put(suffix_zero_keys[0], "zero-a")
        table.put(suffix_one_key, "one")
        table.put(suffix_zero_keys[1], "zero-b")
        table.put(suffix_two_key, "two")

        self.assertTrue(table.delete(suffix_one_key))
        self.assertEqual(table.global_depth, 2)
        self.assertEqual(len(table.buckets), 3)
        self.assertEqual(table.get(suffix_zero_keys[0]), "zero-a")
        self.assertEqual(table.get(suffix_zero_keys[1]), "zero-b")
        self.assertEqual(table.get(suffix_two_key), "two")

    def test_snapshot_round_trip_preserves_directory(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        for index, key in enumerate(colliding_keys(depth=3, count=4, suffix=0)):
            table.put(key, f"payload-{index}")

        restored = ExtendibleHashTable.from_snapshot(table.to_snapshot())
        self.assertEqual(restored.to_snapshot(), table.to_snapshot())

    def test_snapshot_round_trip_preserves_merged_directory_state(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        suffix_zero_keys = colliding_keys(depth=2, count=2, suffix=0)
        suffix_one_key = colliding_keys(depth=2, count=1, suffix=1)[0]
        suffix_two_key = colliding_keys(depth=2, count=1, suffix=2)[0]

        table.put(suffix_zero_keys[0], "zero-a")
        table.put(suffix_one_key, "one")
        table.put(suffix_zero_keys[1], "zero-b")
        table.put(suffix_two_key, "two")
        table.delete(suffix_two_key)

        restored = ExtendibleHashTable.from_snapshot(table.to_snapshot())
        self.assertEqual(restored.to_snapshot(), table.to_snapshot())
        self.assertEqual(restored.global_depth, 1)

    def test_snapshot_loader_rejects_unknown_bucket_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "bad.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "bucket_capacity": 2,
                        "global_depth": 1,
                        "next_bucket_id": 1,
                        "directory": [0, 99],
                        "buckets": [
                            {"bucket_id": 0, "local_depth": 1, "entries": []},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SnapshotError):
                load_snapshot(snapshot_path)

    def test_snapshot_loader_rejects_bucket_alias_count_mismatch_after_merge(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        suffix_zero_keys = colliding_keys(depth=1, count=2, suffix=0)
        suffix_one_key = colliding_keys(depth=1, count=1, suffix=1)[0]

        table.put(suffix_zero_keys[0], "zero-a")
        table.put(suffix_one_key, "one")
        table.put(suffix_zero_keys[1], "zero-b")

        payload = table.to_snapshot()
        payload["directory"] = [0, 0]

        with self.assertRaises(SnapshotError):
            ExtendibleHashTable.from_snapshot(payload)

    def test_snapshot_loader_rejects_duplicate_bucket_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "duplicate-buckets.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "bucket_capacity": 2,
                        "global_depth": 1,
                        "next_bucket_id": 2,
                        "directory": [0, 0],
                        "buckets": [
                            {"bucket_id": 0, "local_depth": 0, "entries": []},
                            {"bucket_id": 0, "local_depth": 0, "entries": []},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SnapshotError):
                load_snapshot(snapshot_path)

    def test_snapshot_loader_rejects_key_routed_to_wrong_bucket(self) -> None:
        wrong_bucket_key = colliding_keys(depth=1, count=1, suffix=1)[0]
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "misrouted-key.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "bucket_capacity": 2,
                        "global_depth": 1,
                        "next_bucket_id": 3,
                        "directory": [0, 1],
                        "buckets": [
                            {"bucket_id": 0, "local_depth": 1, "entries": [{"key": wrong_bucket_key, "value": "1"}]},
                            {"bucket_id": 1, "local_depth": 1, "entries": []},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SnapshotError):
                load_snapshot(snapshot_path)

    def test_snapshot_loader_rejects_non_advancing_next_bucket_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = Path(tmp_dir) / "next-bucket-id.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "bucket_capacity": 2,
                        "global_depth": 1,
                        "next_bucket_id": 1,
                        "directory": [0, 1],
                        "buckets": [
                            {"bucket_id": 0, "local_depth": 1, "entries": []},
                            {"bucket_id": 1, "local_depth": 1, "entries": []},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(SnapshotError):
                load_snapshot(snapshot_path)

    def test_validate_workload_rejects_put_without_value(self) -> None:
        with self.assertRaises(WorkloadError):
            validate_workload({"bucket_capacity": 2, "operations": [{"op": "put", "key": "x"}]})

    def test_run_workload_records_history(self) -> None:
        payload = {
            "bucket_capacity": 2,
            "operations": [
                {"op": "put", "key": "alpha", "value": "1"},
                {"op": "get", "key": "alpha"},
                {"op": "delete", "key": "alpha"},
            ],
        }
        result = run_workload(payload)
        self.assertEqual([item.outcome for item in result.history], ["inserted", "found:1", "deleted"])
        self.assertIsNone(result.table.get("alpha"))

    def test_run_workload_records_directory_shrink_after_deletes(self) -> None:
        suffix_zero_keys = colliding_keys(depth=2, count=2, suffix=0)
        suffix_one_key = colliding_keys(depth=2, count=1, suffix=1)[0]
        suffix_two_key = colliding_keys(depth=2, count=1, suffix=2)[0]
        payload = {
            "bucket_capacity": 2,
            "operations": [
                {"op": "put", "key": suffix_zero_keys[0], "value": "zero-a"},
                {"op": "put", "key": suffix_one_key, "value": "one"},
                {"op": "put", "key": suffix_zero_keys[1], "value": "zero-b"},
                {"op": "put", "key": suffix_two_key, "value": "two"},
                {"op": "delete", "key": suffix_two_key},
                {"op": "delete", "key": suffix_one_key},
            ],
        }
        result = run_workload(payload)
        self.assertEqual([item.global_depth for item in result.history], [0, 0, 1, 2, 1, 0])
        self.assertEqual([item.bucket_count for item in result.history], [1, 1, 2, 3, 2, 1])
        self.assertEqual(result.table.global_depth, 0)

    def test_run_workload_captures_visualization_snapshots_and_events(self) -> None:
        payload = json.loads(SAMPLE_WORKLOAD.read_text(encoding="utf-8"))
        result = run_workload(payload)
        self.assertEqual(len(result.history), len(payload["operations"]))
        split_steps = [item.step for item in result.history if item.split_delta]
        self.assertTrue(split_steps)
        self.assertTrue(all(item.snapshot for item in result.history))
        self.assertEqual(result.history[-1].snapshot["stats"]["entry_count"], result.table.stats()["entry_count"])

    def test_render_visualization_outputs_include_aliasing_story(self) -> None:
        payload = json.loads(SAMPLE_WORKLOAD.read_text(encoding="utf-8"))
        result = run_workload(payload)
        svg = render_visualization_svg("Sample aliasing trace", result.table, result.history, source_label=str(SAMPLE_WORKLOAD))
        html = render_visualization_html("Sample aliasing trace", result.table, result.history, source_label=str(SAMPLE_WORKLOAD))
        self.assertIn("<svg", svg)
        self.assertIn("Directory aliases", svg)
        self.assertIn("Bucket state", svg)
        self.assertIn("splits", svg)
        self.assertIn("aria-labelledby=\"viz-title-", svg)
        self.assertIn("<title id=\"viz-title-", svg)
        self.assertIn("<desc id=\"viz-desc-", svg)
        self.assertIn("<g><title>Step 1 · PUT user:1001", svg)
        self.assertIn("<g><title> 0 · 0 · B0 · user:1001", svg)
        self.assertIn("<section class=\"visual\">", html)
        self.assertIn("Step 1", html)
        self.assertIn("Directory aliases", html)
        self.assertIn("aria-labelledby=\"viz-title-", html)

    def test_validate_benchmark_suite_rejects_duplicate_names(self) -> None:
        with self.assertRaises(BenchmarkError):
            validate_benchmark_suite(
                {
                    "scenarios": [
                        {"name": "dup", "operations": [{"op": "put", "key": "alpha", "value": "1"}]},
                        {"name": "dup", "operations": [{"op": "get", "key": "alpha"}]},
                    ]
                }
            )

    def test_validate_benchmark_suite_rejects_btree_key_collisions(self) -> None:
        with mock.patch.object(MODULE, "benchmark_btree_key", side_effect=[42, 42]):
            with self.assertRaises(BenchmarkError):
                validate_benchmark_suite(
                    {
                        "scenarios": [
                            {
                                "name": "collision-check",
                                "operations": [
                                    {"op": "put", "key": "alpha", "value": "1"},
                                    {"op": "put", "key": "beta", "value": "2"},
                                ],
                            }
                        ]
                    }
                )

    def test_run_benchmark_suite_returns_comparison_metrics(self) -> None:
        summary = run_benchmark_suite(json.loads(BENCHMARK_SUITE.read_text(encoding="utf-8")))
        self.assertEqual(summary["scenario_count"], 3)
        self.assertEqual(summary["trials"], 3)
        self.assertEqual(summary["btree_minimum_degree"], 2)
        self.assertEqual(summary["btree_page_size"], 512)
        self.assertEqual(summary["btree_value_bytes"], 32)
        scenario_names = [row["name"] for row in summary["results"]]
        self.assertEqual(
            scenario_names,
            [
                "directory-friendly-read-heavy",
                "split-pressure-growth",
                "delete-heavy-churn",
            ],
        )
        self.assertTrue(all(row["validation"]["final_state_match"] for row in summary["results"]))
        self.assertEqual(summary["linear_capacity"], 8)
        self.assertAlmostEqual(summary["linear_max_load_factor"], 0.75)
        self.assertAlmostEqual(summary["linear_max_tombstone_ratio"], 0.25)
        self.assertTrue(all(row["extendible"]["split_count"] >= 0 for row in summary["results"]))
        self.assertTrue(all(row["extendible"]["directory_growth_count"] >= 0 for row in summary["results"]))
        self.assertTrue(all(row["linear"]["average_probe_count"] >= 1 for row in summary["results"]))
        self.assertTrue(all(row["linear"]["final_capacity"] >= summary["linear_capacity"] for row in summary["results"]))
        self.assertTrue(all(row["cuckoo"]["average_rehash_count"] >= 0 for row in summary["results"]))
        self.assertTrue(all(row["btree"]["final_height"] >= 1 for row in summary["results"]))
        self.assertTrue(all(row["btree"]["paged_file_bytes"] > 0 for row in summary["results"]))

    def test_summarize_benchmark_trials_rejects_inconsistent_linear_metrics(self) -> None:
        scenario = {
            "name": "nondeterministic-linear",
            "description": "synthetic inconsistent benchmark rows",
            "operations": [{"op": "put", "key": "alpha", "value": "1"}],
        }
        trial_rows = [
            {
                "trial": 1,
                "operation_mix": {
                    "puts": 1,
                    "insertions": 1,
                    "updates": 0,
                    "gets": 0,
                    "get_hits": 0,
                    "get_misses": 0,
                    "deletes": 0,
                    "delete_hits": 0,
                    "delete_misses": 0,
                },
                "final_entry_count": 1,
                "extendible": {
                    "final_global_depth": 0,
                    "peak_global_depth": 0,
                    "final_bucket_count": 1,
                    "peak_bucket_count": 1,
                    "peak_directory_slots": 1,
                    "load_factor": 0.5,
                    "split_count": 0,
                    "merge_count": 0,
                    "directory_growth_count": 0,
                    "directory_shrink_count": 0,
                },
                "linear": {
                    "initial_capacity": 8,
                    "max_load_factor": 0.75,
                    "max_tombstone_ratio": 0.25,
                    "final_capacity": 8,
                    "final_load_factor": 0.125,
                    "occupied_load_factor": 0.125,
                    "tombstone_count": 0,
                    "resize_count": 0,
                    "average_probe_count": 1.0,
                    "max_probe_count": 1,
                    "rebuild_probe_count": 0,
                },
                "cuckoo": {
                    "final_capacity": 7,
                    "load_factor": 0.1429,
                    "rehash_count": 0,
                    "displacement_count": 0,
                    "empty_slots": 6,
                },
                "btree": {
                    "minimum_degree": 2,
                    "page_size": 512,
                    "value_bytes": 32,
                    "final_height": 1,
                    "peak_height": 1,
                    "final_node_count": 1,
                    "peak_node_count": 1,
                    "root_keys": 1,
                    "page_padding_bytes": 440,
                    "paged_file_bytes": 541,
                },
            },
            {
                "trial": 2,
                "operation_mix": {
                    "puts": 1,
                    "insertions": 1,
                    "updates": 0,
                    "gets": 0,
                    "get_hits": 0,
                    "get_misses": 0,
                    "deletes": 0,
                    "delete_hits": 0,
                    "delete_misses": 0,
                },
                "final_entry_count": 1,
                "extendible": {
                    "final_global_depth": 0,
                    "peak_global_depth": 0,
                    "final_bucket_count": 1,
                    "peak_bucket_count": 1,
                    "peak_directory_slots": 1,
                    "load_factor": 0.5,
                    "split_count": 0,
                    "merge_count": 0,
                    "directory_growth_count": 0,
                    "directory_shrink_count": 0,
                },
                "linear": {
                    "initial_capacity": 8,
                    "max_load_factor": 0.75,
                    "max_tombstone_ratio": 0.25,
                    "final_capacity": 16,
                    "final_load_factor": 0.0625,
                    "occupied_load_factor": 0.0625,
                    "tombstone_count": 0,
                    "resize_count": 1,
                    "average_probe_count": 2.0,
                    "max_probe_count": 2,
                    "rebuild_probe_count": 1,
                },
                "cuckoo": {
                    "final_capacity": 7,
                    "load_factor": 0.1429,
                    "rehash_count": 0,
                    "displacement_count": 0,
                    "empty_slots": 6,
                },
                "btree": {
                    "minimum_degree": 2,
                    "page_size": 512,
                    "value_bytes": 32,
                    "final_height": 1,
                    "peak_height": 1,
                    "final_node_count": 1,
                    "peak_node_count": 1,
                    "root_keys": 1,
                    "page_padding_bytes": 440,
                    "paged_file_bytes": 541,
                },
            },
        ]
        with self.assertRaises(BenchmarkError):
            summarize_benchmark_trials(scenario, trial_rows)

    def test_summarize_benchmark_trials_rejects_inconsistent_extendible_metrics(self) -> None:
        scenario = {
            "name": "nondeterministic-extendible",
            "description": "synthetic inconsistent benchmark rows",
            "operations": [{"op": "put", "key": "alpha", "value": "1"}],
        }
        linear = {
            "initial_capacity": 8,
            "max_load_factor": 0.75,
            "max_tombstone_ratio": 0.25,
            "final_capacity": 8,
            "final_load_factor": 0.125,
            "occupied_load_factor": 0.125,
            "tombstone_count": 0,
            "resize_count": 0,
            "average_probe_count": 1.0,
            "max_probe_count": 1,
            "rebuild_probe_count": 0,
        }
        trial_rows = [
            {
                "trial": 1,
                "operation_mix": {
                    "puts": 1,
                    "insertions": 1,
                    "updates": 0,
                    "gets": 0,
                    "get_hits": 0,
                    "get_misses": 0,
                    "deletes": 0,
                    "delete_hits": 0,
                    "delete_misses": 0,
                },
                "final_entry_count": 1,
                "extendible": {
                    "final_global_depth": 0,
                    "peak_global_depth": 0,
                    "final_bucket_count": 1,
                    "peak_bucket_count": 1,
                    "peak_directory_slots": 1,
                    "load_factor": 0.5,
                    "split_count": 0,
                    "merge_count": 0,
                    "directory_growth_count": 0,
                    "directory_shrink_count": 0,
                },
                "linear": dict(linear),
                "cuckoo": {
                    "final_capacity": 7,
                    "load_factor": 0.1429,
                    "rehash_count": 0,
                    "displacement_count": 0,
                    "empty_slots": 6,
                },
                "btree": {
                    "minimum_degree": 2,
                    "page_size": 512,
                    "value_bytes": 32,
                    "final_height": 1,
                    "peak_height": 1,
                    "final_node_count": 1,
                    "peak_node_count": 1,
                    "root_keys": 1,
                    "page_padding_bytes": 440,
                    "paged_file_bytes": 541,
                },
            },
            {
                "trial": 2,
                "operation_mix": {
                    "puts": 1,
                    "insertions": 1,
                    "updates": 0,
                    "gets": 0,
                    "get_hits": 0,
                    "get_misses": 0,
                    "deletes": 0,
                    "delete_hits": 0,
                    "delete_misses": 0,
                },
                "final_entry_count": 1,
                "extendible": {
                    "final_global_depth": 1,
                    "peak_global_depth": 1,
                    "final_bucket_count": 2,
                    "peak_bucket_count": 2,
                    "peak_directory_slots": 2,
                    "load_factor": 0.25,
                    "split_count": 1,
                    "merge_count": 0,
                    "directory_growth_count": 1,
                    "directory_shrink_count": 0,
                },
                "linear": dict(linear),
                "cuckoo": {
                    "final_capacity": 7,
                    "load_factor": 0.1429,
                    "rehash_count": 0,
                    "displacement_count": 0,
                    "empty_slots": 6,
                },
                "btree": {
                    "minimum_degree": 2,
                    "page_size": 512,
                    "value_bytes": 32,
                    "final_height": 1,
                    "peak_height": 1,
                    "final_node_count": 1,
                    "peak_node_count": 1,
                    "root_keys": 1,
                    "page_padding_bytes": 440,
                    "paged_file_bytes": 541,
                },
            },
        ]
        with self.assertRaises(BenchmarkError):
            summarize_benchmark_trials(scenario, trial_rows)

    def test_summarize_benchmark_trials_rejects_inconsistent_btree_metrics(self) -> None:
        scenario = {
            "name": "nondeterministic-btree",
            "description": "synthetic inconsistent benchmark rows",
            "operations": [{"op": "put", "key": "alpha", "value": "1"}],
        }
        linear = {
            "initial_capacity": 8,
            "max_load_factor": 0.75,
            "max_tombstone_ratio": 0.25,
            "final_capacity": 8,
            "final_load_factor": 0.125,
            "occupied_load_factor": 0.125,
            "tombstone_count": 0,
            "resize_count": 0,
            "average_probe_count": 1.0,
            "max_probe_count": 1,
            "rebuild_probe_count": 0,
        }
        trial_rows = [
            {
                "trial": 1,
                "operation_mix": {
                    "puts": 1,
                    "insertions": 1,
                    "updates": 0,
                    "gets": 0,
                    "get_hits": 0,
                    "get_misses": 0,
                    "deletes": 0,
                    "delete_hits": 0,
                    "delete_misses": 0,
                },
                "final_entry_count": 1,
                "extendible": {
                    "final_global_depth": 0,
                    "peak_global_depth": 0,
                    "final_bucket_count": 1,
                    "peak_bucket_count": 1,
                    "peak_directory_slots": 1,
                    "load_factor": 0.5,
                    "split_count": 0,
                    "merge_count": 0,
                    "directory_growth_count": 0,
                    "directory_shrink_count": 0,
                },
                "linear": dict(linear),
                "cuckoo": {
                    "final_capacity": 7,
                    "load_factor": 0.1429,
                    "rehash_count": 0,
                    "displacement_count": 0,
                    "empty_slots": 6,
                },
                "btree": {
                    "minimum_degree": 2,
                    "page_size": 512,
                    "value_bytes": 32,
                    "final_height": 1,
                    "peak_height": 1,
                    "final_node_count": 1,
                    "peak_node_count": 1,
                    "root_keys": 1,
                    "page_padding_bytes": 440,
                    "paged_file_bytes": 541,
                },
            },
            {
                "trial": 2,
                "operation_mix": {
                    "puts": 1,
                    "insertions": 1,
                    "updates": 0,
                    "gets": 0,
                    "get_hits": 0,
                    "get_misses": 0,
                    "deletes": 0,
                    "delete_hits": 0,
                    "delete_misses": 0,
                },
                "final_entry_count": 1,
                "extendible": {
                    "final_global_depth": 0,
                    "peak_global_depth": 0,
                    "final_bucket_count": 1,
                    "peak_bucket_count": 1,
                    "peak_directory_slots": 1,
                    "load_factor": 0.5,
                    "split_count": 0,
                    "merge_count": 0,
                    "directory_growth_count": 0,
                    "directory_shrink_count": 0,
                },
                "linear": dict(linear),
                "cuckoo": {
                    "final_capacity": 7,
                    "load_factor": 0.1429,
                    "rehash_count": 0,
                    "displacement_count": 0,
                    "empty_slots": 6,
                },
                "btree": {
                    "minimum_degree": 2,
                    "page_size": 512,
                    "value_bytes": 32,
                    "final_height": 2,
                    "peak_height": 2,
                    "final_node_count": 3,
                    "peak_node_count": 3,
                    "root_keys": 1,
                    "page_padding_bytes": 440,
                    "paged_file_bytes": 1565,
                },
            },
        ]
        with self.assertRaises(BenchmarkError):
            summarize_benchmark_trials(scenario, trial_rows)

    def test_render_benchmark_dashboard_html_uses_accessible_tables_and_escaped_content(self) -> None:
        summary = run_benchmark_suite(json.loads(BENCHMARK_SUITE.read_text(encoding="utf-8")))
        html = render_benchmark_dashboard_html(
            "Extendible hashing <dashboard>",
            summary,
            suite_source='projects/extendible-hashing-lab/benchmark_suite.json?x=<unsafe>',
        )
        self.assertIn('<title>Extendible hashing &lt;dashboard&gt;</title>', html)
        self.assertIn('Scenario scoreboard with the headline metrics', html)
        self.assertIn('<thead>', html)
        self.assertIn('<tbody>', html)
        self.assertIn('directory-friendly-read-heavy', html)
        self.assertIn('B-tree page baseline', html)
        self.assertIn('benchmark_suite.json?x=&lt;unsafe&gt;', html)
        self.assertNotIn('benchmark_suite.json?x=<unsafe>', html)
        self.assertIn('metric-bar', html)

    def test_cli_run_inspect_lookup_delete_and_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot_path = tmp_path / "snapshot.json"
            report_path = tmp_path / "report.md"
            updated_snapshot_path = tmp_path / "snapshot-updated.json"
            benchmark_json = tmp_path / "benchmark.json"
            benchmark_md = tmp_path / "benchmark.md"
            benchmark_html = tmp_path / "benchmark.html"
            benchmark_csv = tmp_path / "benchmark.csv"
            visualize_svg = tmp_path / "trace.svg"
            visualize_html = tmp_path / "trace.html"

            run_process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "run",
                    "--input",
                    str(SAMPLE_WORKLOAD),
                    "--output",
                    str(snapshot_path),
                    "--report",
                    str(report_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(snapshot_path.exists())
            self.assertTrue(report_path.exists())
            self.assertIn('"bucket_count"', run_process.stdout)

            inspect_process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "inspect",
                    "--snapshot",
                    str(snapshot_path),
                    "--format",
                    "markdown",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("## Directory", inspect_process.stdout)

            lookup_process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "lookup",
                    "--snapshot",
                    str(snapshot_path),
                    "user:1009",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("user:1009:", lookup_process.stdout)

            delete_process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "delete",
                    "--snapshot",
                    str(snapshot_path),
                    "--output",
                    str(updated_snapshot_path),
                    "user:1041",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("deleted", delete_process.stdout)
            self.assertTrue(updated_snapshot_path.exists())
            self.assertIsNotNone(load_snapshot(updated_snapshot_path))

            benchmark_title = "Extendible hashing vs cuckoo hashing and B-tree benchmark comparison"
            benchmark_process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--input",
                    str(BENCHMARK_SUITE),
                    "--json-out",
                    str(benchmark_json),
                    "--markdown-out",
                    str(benchmark_md),
                    "--html-out",
                    str(benchmark_html),
                    "--csv-out",
                    str(benchmark_csv),
                    "--title",
                    benchmark_title,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(benchmark_json.exists())
            self.assertTrue(benchmark_md.exists())
            self.assertTrue(benchmark_html.exists())
            self.assertTrue(benchmark_csv.exists())
            self.assertIn('"scenario_count": 3', benchmark_process.stdout)
            self.assertIn('"btree_page_size": 512', benchmark_process.stdout)
            self.assertIn(benchmark_title, benchmark_process.stdout)
            benchmark_md_text = benchmark_md.read_text(encoding="utf-8")
            self.assertIn(benchmark_title, benchmark_md_text)
            self.assertIn("directory-friendly-read-heavy", benchmark_md_text)
            self.assertIn("Linear probing baseline", benchmark_md_text)
            self.assertIn("B-tree page baseline", benchmark_md_text)
            benchmark_json_payload = json.loads(benchmark_json.read_text(encoding="utf-8"))
            self.assertEqual(benchmark_json_payload["title"], benchmark_title)
            benchmark_html_text = benchmark_html.read_text(encoding="utf-8")
            self.assertIn(benchmark_title, benchmark_html_text)
            self.assertIn("Scenario scoreboard", benchmark_html_text)
            self.assertIn("directory-friendly-read-heavy", benchmark_html_text)
            self.assertIn("Linear probing baseline", benchmark_html_text)
            benchmark_csv_text = benchmark_csv.read_text(encoding="utf-8")
            self.assertIn("linear_average_probe_count", benchmark_csv_text)
            self.assertIn("btree_paged_file_bytes", benchmark_csv_text)
            self.assertNotIn("\r", benchmark_csv_text)

            visualize_process = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "visualize",
                    "--input",
                    str(SAMPLE_WORKLOAD),
                    "--svg-out",
                    str(visualize_svg),
                    "--html-out",
                    str(visualize_html),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(visualize_svg.exists())
            self.assertTrue(visualize_html.exists())
            self.assertIn('"steps": 7', visualize_process.stdout)
            self.assertIn("Directory aliases", visualize_svg.read_text(encoding="utf-8"))
            self.assertIn("Step 1", visualize_html.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
