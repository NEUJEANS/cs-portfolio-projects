import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from wal_kv_store import WALKVStore


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "wal_kv_store.py"


def run_cli(data_dir: Path, *args: str):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--dir", str(data_dir), *args],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


class WALKVStoreTests(unittest.TestCase):
    def test_replay_recovers_latest_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = WALKVStore(tmp)
            store.set("theme", "light")
            store.set("theme", "dark")
            store.set("lang", "en")

            reloaded = WALKVStore(tmp)
            self.assertEqual(reloaded.get("theme"), "dark")
            self.assertEqual(reloaded.items(), {"lang": "en", "theme": "dark"})

    def test_delete_uses_tombstone_and_survives_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = WALKVStore(tmp)
            store.set("draft", "v1")
            store.delete("draft")

            reloaded = WALKVStore(tmp)
            self.assertIsNone(reloaded.get("draft"))
            history = reloaded.history("draft")
            self.assertEqual([record["op"] for record in history], ["set", "delete"])

    def test_checkpoint_preserves_state_and_clears_active_wal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = WALKVStore(tmp)
            store.set("a", "1")
            store.set("b", "2")
            store.delete("a")

            checkpoint = store.checkpoint()
            self.assertEqual(checkpoint["last_seq"], 3)
            self.assertEqual(store.stats()["wal_records"], 0)
            self.assertEqual(store.history("b"), [])

            reloaded = WALKVStore(tmp)
            self.assertEqual(reloaded.items(), {"b": "2"})
            self.assertEqual(reloaded.stats()["snapshot_seq"], 3)

    def test_cli_flow_covers_set_get_delete_list_and_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            set_result = run_cli(data_dir, "set", "course", "cs5100")
            self.assertEqual(set_result["value"], "cs5100")

            get_result = run_cli(data_dir, "get", "course")
            self.assertTrue(get_result["found"])
            self.assertEqual(get_result["value"], "cs5100")

            list_result = run_cli(data_dir, "list")
            self.assertEqual(list_result["items"], {"course": "cs5100"})

            delete_result = run_cli(data_dir, "delete", "course")
            self.assertTrue(delete_result["existed"])
            self.assertFalse(delete_result["found"])

            checkpoint_result = run_cli(data_dir, "checkpoint")
            self.assertEqual(checkpoint_result["keys"], 0)

    def test_invalid_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = WALKVStore(tmp)
            with self.assertRaisesRegex(ValueError, "contain no whitespace"):
                store.set("bad key", "value")

    def test_history_and_stats_reflect_mutation_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = WALKVStore(tmp)
            store.set("x", "1")
            store.set("x", "2")
            store.delete("x")

            stats = store.stats()
            self.assertEqual(stats["wal_records"], 3)
            self.assertEqual(stats["next_seq"], 4)
            self.assertEqual([entry["seq"] for entry in store.history("x")], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
