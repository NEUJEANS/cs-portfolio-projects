import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from cuckoo_hashing_lab import CuckooHashTable, load_pairs, load_snapshot, parse_pair, save_snapshot

SCRIPT = ROOT / "cuckoo_hashing_lab.py"


class CuckooHashingLabTests(unittest.TestCase):
    def test_parse_pair_supports_csv_equals_and_key_only(self):
        self.assertEqual(parse_pair("alpha,1"), ("alpha", "1"))
        self.assertEqual(parse_pair("beta=2"), ("beta", "2"))
        self.assertEqual(parse_pair("gamma"), ("gamma", "gamma"))

    def test_insert_lookup_update_and_remove(self):
        table = CuckooHashTable(capacity=5, max_displacements=8)
        table.insert("alpha", "1")
        table.insert("beta", "2")
        table.insert("alpha", "3")
        self.assertEqual(table.get("alpha"), "3")
        self.assertTrue(table.remove("alpha"))
        self.assertIsNone(table.get("alpha"))
        self.assertFalse(table.remove("missing"))

    def test_rehash_preserves_all_entries(self):
        table = CuckooHashTable(capacity=3, max_displacements=1)
        for index in range(15):
            table.insert(f"key-{index}", f"value-{index}")
        self.assertGreaterEqual(table.rehash_count, 1)
        for index in range(15):
            self.assertEqual(table.get(f"key-{index}"), f"value-{index}")

    def test_snapshot_round_trip(self):
        table = CuckooHashTable(capacity=7)
        table.extend([("alpha", "1"), ("beta", "2"), ("gamma", "3")])
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            snapshot = temp_dir / "table.json"
            save_snapshot(snapshot, table)
            loaded = load_snapshot(snapshot)
            self.assertEqual(loaded.items(), table.items())
            self.assertEqual(loaded.stats()["size"], 3)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_load_pairs_skips_comments_and_blanks(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "pairs.txt"
            source.write_text("# comment\nalpha,1\n\n beta=2\n")
            self.assertEqual(load_pairs(source), [("alpha", "1"), ("beta", "2")])
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_invalid_snapshot_is_rejected(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            snapshot = temp_dir / "bad.json"
            snapshot.write_text(json.dumps({
                "capacity": 3,
                "max_displacements": 1,
                "entries": [{"key": "a", "value": "1"}, {"key": "b", "value": "2"}, {"key": "c", "value": "3"}, {"key": "d", "value": "4"}],
            }))
            with self.assertRaises(ValueError):
                load_snapshot(snapshot)

            duplicate_snapshot = temp_dir / "duplicate.json"
            duplicate_snapshot.write_text(json.dumps({
                "capacity": 7,
                "entries": [{"key": "dup", "value": "1"}, {"key": "dup", "value": "2"}],
            }))
            with self.assertRaises(ValueError):
                load_snapshot(duplicate_snapshot)

            negative_counter_snapshot = temp_dir / "negative-counter.json"
            negative_counter_snapshot.write_text(json.dumps({
                "capacity": 7,
                "rehash_count": -1,
                "entries": [{"key": "alpha", "value": "1"}],
            }))
            with self.assertRaises(ValueError):
                load_snapshot(negative_counter_snapshot)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_cli_build_stats_lookup_remove_and_export(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "pairs.txt"
            snapshot = temp_dir / "table.json"
            updated = temp_dir / "updated.json"
            exported = temp_dir / "pairs.csv"
            source.write_text("alpha,1\nbeta,2\ngamma,3\ndelta,4\n")

            build = subprocess.run(
                [sys.executable, str(SCRIPT), "build", "--input", str(source), "--output", str(snapshot), "--capacity", "3", "--max-displacements", "1"],
                capture_output=True,
                text=True,
                check=True,
            )
            build_data = json.loads(build.stdout)
            self.assertEqual(build_data["inserted"], 4)
            self.assertGreaterEqual(build_data["rehash_count"], 1)

            stats = subprocess.run(
                [sys.executable, str(SCRIPT), "stats", "--snapshot", str(snapshot)],
                capture_output=True,
                text=True,
                check=True,
            )
            stats_data = json.loads(stats.stdout)
            self.assertEqual(stats_data["size"], 4)
            self.assertEqual(len(stats_data["items"]), 4)

            lookup = subprocess.run(
                [sys.executable, str(SCRIPT), "lookup", "--snapshot", str(snapshot), "gamma"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(json.loads(lookup.stdout)["found"])

            remove = subprocess.run(
                [sys.executable, str(SCRIPT), "remove", "--snapshot", str(snapshot), "--output", str(updated), "beta"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(json.loads(remove.stdout)["removed"])

            export = subprocess.run(
                [sys.executable, str(SCRIPT), "export", "--snapshot", str(updated), "--output", str(exported)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(export.stdout)["exported"], 3)
            self.assertIn("alpha,1", exported.read_text())
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
