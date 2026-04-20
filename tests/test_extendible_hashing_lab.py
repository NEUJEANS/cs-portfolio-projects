from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "projects/extendible-hashing-lab/extendible_hashing_lab.py"
SAMPLE_WORKLOAD = REPO_ROOT / "projects/extendible-hashing-lab/sample_workload.json"
SPEC = importlib.util.spec_from_file_location("extendible_hashing_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
ExtendibleHashTable = MODULE.ExtendibleHashTable
SnapshotError = MODULE.SnapshotError
WorkloadError = MODULE.WorkloadError
load_snapshot = MODULE.load_snapshot
run_workload = MODULE.run_workload
validate_workload = MODULE.validate_workload
stable_hash = MODULE.stable_hash


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

    def test_snapshot_round_trip_preserves_directory(self) -> None:
        table = ExtendibleHashTable(bucket_capacity=2)
        for index, key in enumerate(colliding_keys(depth=3, count=4, suffix=0)):
            table.put(key, f"payload-{index}")

        restored = ExtendibleHashTable.from_snapshot(table.to_snapshot())
        self.assertEqual(restored.to_snapshot(), table.to_snapshot())

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

    def test_cli_run_inspect_lookup_and_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot_path = tmp_path / "snapshot.json"
            report_path = tmp_path / "report.md"
            updated_snapshot_path = tmp_path / "snapshot-updated.json"

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


if __name__ == "__main__":
    unittest.main()
