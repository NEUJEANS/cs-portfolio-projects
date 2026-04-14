import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from skip_list_kv import SkipList, build_skip_list, load_pairs


class SkipListTests(unittest.TestCase):
    def test_put_get_update_delete(self) -> None:
        store = SkipList(seed=3)
        self.assertTrue(store.put("gamma", 3))
        self.assertTrue(store.put("alpha", 1))
        self.assertFalse(store.put("alpha", 10))
        self.assertEqual(store.get("alpha"), 10)
        self.assertTrue(store.delete("gamma"))
        self.assertFalse(store.delete("gamma"))
        self.assertEqual(store.items(), [("alpha", 10)])

    def test_range_query_returns_sorted_slice(self) -> None:
        store = build_skip_list([
            ("apple", 1),
            ("banana", 2),
            ("carrot", 3),
            ("date", 4),
        ], seed=5)
        self.assertEqual(store.range_query("banana", "date"), [
            ("banana", 2),
            ("carrot", 3),
            ("date", 4),
        ])

    def test_stats_report_height_distribution(self) -> None:
        store = build_skip_list([(f"k{i}", i) for i in range(10)], seed=7, max_level=6)
        stats = store.stats()
        self.assertEqual(stats["length"], 10)
        self.assertGreaterEqual(stats["active_levels"], 1)
        self.assertEqual(sum(stats["nodes_per_height"].values()), 10)

    def test_load_pairs_requires_json_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text('{"key": "x"}')
            with self.assertRaises(ValueError):
                load_pairs(path)


class SkipListCliTests(unittest.TestCase):
    def _write_fixture(self, path: Path) -> None:
        path.write_text(json.dumps([
            {"key": "alpha", "value": 1},
            {"key": "beta", "value": 2},
            {"key": "delta", "value": 4},
        ]))

    def test_cli_range_outputs_expected_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            self._write_fixture(path)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skip_list_kv.py"),
                    str(path),
                    "range",
                    "--start",
                    "alpha",
                    "--stop",
                    "beta",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual([row["key"] for row in payload], ["alpha", "beta"])

    def test_cli_put_persist_writes_sorted_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data.json"
            self._write_fixture(path)
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skip_list_kv.py"),
                    str(path),
                    "put",
                    "charlie",
                    '{"score": 3}',
                    "--persist",
                ],
                check=True,
            )
            payload = json.loads(path.read_text())
            self.assertEqual([row["key"] for row in payload], ["alpha", "beta", "charlie", "delta"])
            self.assertEqual(payload[2]["value"], {"score": 3})


if __name__ == "__main__":
    unittest.main()
