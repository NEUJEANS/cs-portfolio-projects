from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lsm_tree_kv import LSMTreeKV


class LSMTreeKVTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_replays_wal_and_reads_latest_values(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=10)
        store.set("course", "systems")
        store.set("topic", "storage")

        reloaded = LSMTreeKV(self.root, flush_threshold=10)
        self.assertEqual(reloaded.get("course").value, "systems")
        self.assertEqual([entry.key for entry in reloaded.list_items()], ["course", "topic"])

    def test_flush_moves_data_to_sstable(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=2)
        store.set("a", "1")
        store.set("b", "2")

        self.assertEqual(store.stats()["memtable_entries"], 0)
        self.assertEqual(store.stats()["sstable_count"], 1)
        self.assertEqual(store.get("a").value, "1")

    def test_delete_writes_tombstone_and_hides_old_values(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=2)
        store.set("a", "1")
        store.set("b", "2")
        entry, existed = store.delete("a")
        self.assertTrue(existed)
        self.assertTrue(entry.deleted)
        store.flush()

        reloaded = LSMTreeKV(self.root, flush_threshold=2)
        self.assertIsNone(reloaded.get("a"))
        self.assertEqual([entry.key for entry in reloaded.list_items()], ["b"])

    def test_compaction_merges_to_single_sstable(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=2)
        store.set("a", "1")
        store.set("b", "2")
        store.set("c", "3")
        store.set("d", "4")
        store.delete("b")
        store.flush()

        path = store.compact()

        self.assertIsNotNone(path)
        self.assertEqual(store.stats()["sstable_count"], 1)
        self.assertEqual([entry.key for entry in store.list_items()], ["a", "c", "d"])
        files = list((self.root / "sstables").glob("sstable-*.json"))
        self.assertEqual(len(files), 1)

    def test_bloom_filter_metadata_is_persisted_in_sstable(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=2, bloom_bits_per_key=12)
        store.set("alpha", "1")
        store.set("beta", "2")

        sstable_path = next((self.root / "sstables").glob("sstable-*.json"))
        payload = json.loads(sstable_path.read_text())

        bloom = payload["bloom_filter"]
        self.assertGreaterEqual(bloom["bit_count"], 24)
        self.assertGreaterEqual(bloom["hash_count"], 1)
        self.assertGreater(bloom["bits"], 0)

    def test_negative_lookup_skips_loading_sstable_when_bloom_filter_rejects_key(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=2)
        store.set("alpha", "1")
        store.set("beta", "2")

        reloaded = LSMTreeKV(self.root, flush_threshold=2)
        with mock.patch.object(reloaded, "_load_sstable", wraps=reloaded._load_sstable) as load_sstable:
            self.assertIsNone(reloaded.get("omega"))
        load_sstable.assert_not_called()

    def test_stats_report_bloom_filter_footprint(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=2)
        store.set("alpha", "1")
        store.set("beta", "2")

        stats = store.stats()
        self.assertEqual(stats["bloom_filter_count"], 1)
        self.assertGreaterEqual(stats["bloom_filter_bits"], 20)

    def test_invalid_key_returns_error_code_from_cli(self) -> None:
        result = self.run_cli("set", "bad key", "value")
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "error")

    def test_cli_round_trip(self) -> None:
        set_result = self.run_cli("set", "name", "lsm")
        self.assertEqual(set_result.returncode, 0)
        get_result = self.run_cli("get", "name")
        self.assertEqual(get_result.returncode, 0)
        payload = json.loads(get_result.stdout)
        self.assertEqual(payload["value"], "lsm")

        delete_result = self.run_cli("delete", "name")
        self.assertEqual(delete_result.returncode, 0)
        delete_payload = json.loads(delete_result.stdout)
        self.assertTrue(delete_payload["existed_before"])

    def test_compacting_only_tombstones_leaves_empty_store(self) -> None:
        store = LSMTreeKV(self.root, flush_threshold=2)
        store.set("a", "1")
        store.set("b", "2")
        store.delete("a")
        store.delete("b")

        store.compact()

        self.assertEqual(store.stats()["live_keys"], 0)
        self.assertEqual(store.stats()["sstable_count"], 0)
        self.assertEqual(list((self.root / "sstables").glob("sstable-*.json")), [])

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "lsm_tree_kv.py", "--dir", str(self.root), *args],
            cwd=Path(__file__).parent,
            text=True,
            capture_output=True,
            check=False,
        )


if __name__ == "__main__":
    unittest.main()
