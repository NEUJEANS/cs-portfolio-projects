from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py"
SAMPLE_INPUT = REPO_ROOT / "projects/robin-hood-hashing-lab/sample_pairs.txt"
SPEC = importlib.util.spec_from_file_location("robin_hood_hashing_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
InputDataError = MODULE.InputDataError
RobinHoodHashTable = MODULE.RobinHoodHashTable
SnapshotError = MODULE.SnapshotError
load_snapshot = MODULE.load_snapshot
parse_load_factors = MODULE.parse_load_factors
parse_pairs_input = MODULE.parse_pairs_input
stable_hash = MODULE.stable_hash


def keys_for_home(capacity: int, home_slot: int, count: int) -> list[str]:
    matches: list[str] = []
    candidate = 0
    while len(matches) < count:
        key = f"home:{capacity}:{home_slot}:{candidate}"
        if stable_hash(key) % capacity == home_slot:
            matches.append(key)
        candidate += 1
    return matches


class RobinHoodHashingLabTests(unittest.TestCase):
    def test_insert_lookup_update_and_resize(self) -> None:
        table = RobinHoodHashTable(capacity=5, max_load_factor=0.6, auto_resize=True)
        inserted = []
        for index in range(4):
            result = table.put(f"key-{index}", f"value-{index}")
            inserted.append(result.action)

        self.assertEqual(inserted.count("inserted"), 4)
        self.assertGreater(table.capacity, 5)
        self.assertEqual(table.get("key-3"), "value-3")
        self.assertEqual(table.put("key-1", "updated").action, "updated")
        self.assertEqual(table.get("key-1"), "updated")

    def test_robin_hood_swap_promotes_longer_probe_chain(self) -> None:
        table = RobinHoodHashTable(capacity=7, auto_resize=False)
        home_zero_a, home_zero_b = keys_for_home(7, 0, 2)
        home_one = keys_for_home(7, 1, 1)[0]

        table.put(home_zero_a, "a")
        table.put(home_one, "b")
        result = table.put(home_zero_b, "c")

        self.assertGreater(result.swaps, 0)
        slot_one = table.slots[1]
        slot_two = table.slots[2]
        assert slot_one is not None and slot_two is not None
        self.assertEqual(slot_one.key, home_zero_b)
        self.assertEqual(slot_one.probe_distance, 1)
        self.assertEqual(slot_two.key, home_one)
        self.assertEqual(slot_two.probe_distance, 1)

    def test_backward_shift_deletion_keeps_cluster_searchable(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        keys = keys_for_home(11, 3, 4)
        for index, key in enumerate(keys):
            table.put(key, f"value-{index}")

        self.assertTrue(table.delete(keys[1]))
        self.assertIsNone(table.get(keys[1]))
        self.assertEqual(table.get(keys[2]), "value-2")
        self.assertEqual(table.get(keys[3]), "value-3")

        stats = table.stats()
        self.assertEqual(stats["size"], 3)
        self.assertEqual(stats["max_probe_distance"], 2)

    def test_snapshot_round_trip_preserves_entries(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        for index, key in enumerate(keys_for_home(11, 5, 3)):
            table.put(key, f"value-{index}")

        restored = RobinHoodHashTable.from_snapshot(table.to_snapshot())
        self.assertEqual(restored.to_snapshot(), table.to_snapshot())

    def test_snapshot_loader_rejects_gap_inside_probe_sequence(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        keys = keys_for_home(11, 6, 3)
        for index, key in enumerate(keys):
            table.put(key, f"value-{index}")

        payload = table.to_snapshot()
        payload["slots"][(stable_hash(keys[2]) % 11) + 1] = None
        with self.assertRaises(SnapshotError):
            RobinHoodHashTable.from_snapshot(payload)

    def test_snapshot_loader_rejects_non_string_payload_values(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        table.put("alpha", "1")
        payload = table.to_snapshot()
        for slot in payload["slots"]:
            if slot is not None:
                slot["value"] = 123
                break
        with self.assertRaises(SnapshotError):
            RobinHoodHashTable.from_snapshot(payload)

    def test_parse_pairs_input_supports_comments_and_both_separators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "pairs.txt"
            path.write_text("# note\nalpha,1\nbeta=2\n", encoding="utf-8")
            self.assertEqual(parse_pairs_input(path), [("alpha", "1"), ("beta", "2")])

    def test_parse_load_factors_rejects_invalid_values(self) -> None:
        with self.assertRaises(InputDataError):
            parse_load_factors("0,1.2")

    def test_cli_build_stats_export_remove_and_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot_path = tmp_path / "table.json"
            updated_snapshot_path = tmp_path / "table-updated.json"
            export_path = tmp_path / "table.csv"
            benchmark_path = tmp_path / "benchmark.csv"
            benchmark_json_path = tmp_path / "benchmark.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build",
                    "--input",
                    str(SAMPLE_INPUT),
                    "--output",
                    str(snapshot_path),
                    "--capacity",
                    "11",
                    "--pretty",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            stats = subprocess.run(
                [sys.executable, str(SCRIPT), "stats", "--snapshot", str(snapshot_path), "--pretty"],
                check=True,
                capture_output=True,
                text=True,
            )
            stats_payload = json.loads(stats.stdout)
            self.assertEqual(stats_payload["size"], 5)

            subprocess.run(
                [sys.executable, str(SCRIPT), "export", "--snapshot", str(snapshot_path), "--output", str(export_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            with export_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0], ["key", "value"])
            self.assertEqual(len(rows), 6)

            removal = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "remove",
                    "--snapshot",
                    str(snapshot_path),
                    "--output",
                    str(updated_snapshot_path),
                    "user:1002",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            removal_payload = json.loads(removal.stdout)
            self.assertTrue(removal_payload["removed"])
            updated_table = load_snapshot(updated_snapshot_path)
            self.assertIsNone(updated_table.get("user:1002"))

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--capacity",
                    "31",
                    "--load-factors",
                    "0.25,0.5",
                    "--trials",
                    "2",
                    "--seed",
                    "17",
                    "--output",
                    str(benchmark_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            with benchmark_path.open("r", encoding="utf-8", newline="") as handle:
                benchmark_rows = list(csv.DictReader(handle))
            self.assertEqual(len(benchmark_rows), 4)
            self.assertEqual({row["load_factor"] for row in benchmark_rows}, {"0.25", "0.5"})

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--capacity",
                    "31",
                    "--load-factors",
                    "0.25",
                    "--trials",
                    "1",
                    "--seed",
                    "17",
                    "--output",
                    str(benchmark_json_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            benchmark_json = json.loads(benchmark_json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(benchmark_json), 1)
            self.assertEqual(benchmark_json[0]["capacity"], 31)


if __name__ == "__main__":
    unittest.main()
