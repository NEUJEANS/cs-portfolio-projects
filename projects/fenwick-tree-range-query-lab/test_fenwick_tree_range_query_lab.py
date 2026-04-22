import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fenwick_tree_range_query_lab import (
    FenwickTree,
    RangeAddSegmentTree,
    RangeFenwick,
    generate_benchmark_operations,
    load_snapshot,
    load_values,
    render_benchmark_markdown,
    render_benchmark_svg,
    run_benchmark,
    save_snapshot,
)

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

    def test_segment_tree_matches_range_fenwick_for_mixed_updates(self):
        values = [4, 1, 7, 3, 9, 2]
        fenwick = RangeFenwick(values)
        segment_tree = RangeAddSegmentTree(values)
        operations = [
            ("range_sum", 1, 3, None),
            ("range_add", 2, 5, 4),
            ("point_set", 4, 4, 11),
            ("range_sum", 3, 6, None),
            ("range_add", 1, 6, -2),
            ("range_sum", 1, 6, None),
        ]
        for kind, left, right, amount in operations:
            if kind == "range_sum":
                self.assertEqual(fenwick.range_sum(left, right), segment_tree.range_sum(left, right))
            elif kind == "range_add":
                fenwick.range_add(left, right, amount)
                segment_tree.range_add(left, right, amount)
            else:
                fenwick.point_set(left, amount)
                segment_tree.point_set(left, amount)
        self.assertEqual(fenwick.range_sum(1, fenwick.size), segment_tree.range_sum(1, len(values)))

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

    def test_generate_benchmark_operations_validates_mix(self):
        with self.assertRaisesRegex(ValueError, "<= 1"):
            generate_benchmark_operations(
                size=8,
                operations=10,
                seed=7,
                query_ratio=0.7,
                set_ratio=0.4,
                max_range_width=4,
                value_min=0,
                value_max=10,
                delta_min=-2,
                delta_max=2,
            )

    def test_run_benchmark_verifies_consistent_results(self):
        payload = run_benchmark(
            size=32,
            operations=120,
            seed=11,
            repeats=2,
            query_ratio=0.4,
            set_ratio=0.2,
            max_range_width=8,
            value_min=0,
            value_max=25,
            delta_min=-3,
            delta_max=6,
        )
        self.assertTrue(payload["correctness_verified"])
        self.assertEqual({result["strategy"] for result in payload["strategies"]}, {"range-fenwick", "segment-tree"})
        self.assertGreater(payload["speedup"], 0)
        markdown = render_benchmark_markdown(payload)
        self.assertIn("Fenwick vs Segment Tree Benchmark", markdown)
        self.assertIn("range-fenwick", markdown)
        svg = render_benchmark_svg(payload)
        self.assertIn("<svg", svg)
        self.assertIn("Throughput comparison", svg)
        self.assertIn("segment-tree", svg)

    def test_cli_build_sum_add_set_export_and_benchmark(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "values.txt"
            snapshot = temp_dir / "snapshot.json"
            updated = temp_dir / "updated.json"
            adjusted = temp_dir / "adjusted.json"
            exported = temp_dir / "values.csv"
            benchmark_json = temp_dir / "benchmark.json"
            benchmark_csv = temp_dir / "benchmark.csv"
            benchmark_md = temp_dir / "benchmark.md"
            benchmark_svg = temp_dir / "benchmark.svg"
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

            benchmark_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--size",
                    "16",
                    "--operations",
                    "40",
                    "--repeats",
                    "1",
                    "--seed",
                    "5",
                    "--max-range-width",
                    "5",
                    "--output",
                    str(benchmark_json),
                    "--csv-output",
                    str(benchmark_csv),
                    "--markdown-output",
                    str(benchmark_md),
                    "--svg-output",
                    str(benchmark_svg),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(benchmark_result.stdout)
            self.assertTrue(payload["correctness_verified"])
            self.assertTrue(benchmark_json.exists())
            self.assertTrue(benchmark_csv.exists())
            self.assertTrue(benchmark_md.exists())
            self.assertTrue(benchmark_svg.exists())
            self.assertIn("segment-tree", benchmark_csv.read_text())
            self.assertIn("relative speedup", benchmark_md.read_text())
            self.assertIn("Per-operation latency", benchmark_svg.read_text())
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
