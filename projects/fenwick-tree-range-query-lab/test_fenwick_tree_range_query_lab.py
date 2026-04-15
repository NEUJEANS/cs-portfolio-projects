import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fenwick_tree_range_query_lab import FenwickTree, RangeFenwick, load_snapshot, load_values, save_snapshot

SCRIPT = ROOT / "fenwick_tree_range_query_lab.py"


class FenwickTreeRangeQueryLabTests(unittest.TestCase):
    def test_fenwick_prefix_sums_match_source_values(self):
        values = [3, 1, 4, 1, 5, 9]
        tree = FenwickTree.from_values(values)
        self.assertEqual(tree.prefix_sum(3), 8)
        self.assertEqual(tree.prefix_sum(6), sum(values))

    def test_range_add_point_set_and_queries(self):
        lab = RangeFenwick([2, 4, 6, 8, 10])
        self.assertEqual(lab.range_sum(2, 4), 18)
        lab.range_add(2, 5, 3)
        self.assertEqual(lab.values, [2, 7, 9, 11, 13])
        self.assertEqual(lab.range_sum(1, 5), 42)
        lab.point_set(3, 20)
        self.assertEqual(lab.point_query(3), 20)
        self.assertEqual(lab.range_sum(2, 4), 38)

    def test_snapshot_round_trip(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            snapshot = temp_dir / "lab.json"
            original = RangeFenwick([1, 2, 3, 4])
            original.range_add(1, 3, 2)
            save_snapshot(snapshot, original)
            loaded = load_snapshot(snapshot)
            self.assertEqual(loaded.values, [3, 4, 5, 4])
            self.assertEqual(loaded.range_sum(1, 4), 16)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_load_values_skips_comments(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "values.txt"
            source.write_text("# comment\n5\n\n8\n13\n")
            self.assertEqual(load_values(source), [5, 8, 13])
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_invalid_snapshot_rejected(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            bad = temp_dir / "bad.json"
            bad.write_text(json.dumps({"values": [1, True, 3]}))
            with self.assertRaises(ValueError):
                load_snapshot(bad)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_invalid_input_line_reports_line_number(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "values.txt"
            source.write_text("1\nnope\n3\n")
            with self.assertRaisesRegex(ValueError, "line 2"):
                load_values(source)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_cli_build_sum_add_set_and_export(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "values.txt"
            snapshot = temp_dir / "snapshot.json"
            updated = temp_dir / "updated.json"
            adjusted = temp_dir / "adjusted.json"
            exported = temp_dir / "values.csv"
            source.write_text("2\n4\n6\n8\n")

            build = subprocess.run(
                [sys.executable, str(SCRIPT), "build", "--input", str(source), "--output", str(snapshot)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(build.stdout)["total"], 20)

            summed = subprocess.run(
                [sys.executable, str(SCRIPT), "sum", "--snapshot", str(snapshot), "2", "4"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(summed.stdout)["sum"], 18)

            added = subprocess.run(
                [sys.executable, str(SCRIPT), "add", "--snapshot", str(snapshot), "--output", str(updated), "2", "4", "5"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(added.stdout)["values"], [2, 9, 11, 13])

            set_value = subprocess.run(
                [sys.executable, str(SCRIPT), "set", "--snapshot", str(updated), "--output", str(adjusted), "1", "7"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(set_value.stdout)["values"], [7, 9, 11, 13])

            exported_result = subprocess.run(
                [sys.executable, str(SCRIPT), "export", "--snapshot", str(adjusted), "--output", str(exported)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(exported_result.stdout)["rows"], 4)
            self.assertIn("4,13,40", exported.read_text())
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
