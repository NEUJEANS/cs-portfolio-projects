import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from hyperloglog import (
    HyperLogLog,
    benchmark_accuracy,
    extract_items,
    infer_input_format,
    load_hll,
    parse_int_list,
    render_benchmark_markdown,
    save_hll,
    simulate_accuracy,
)

SCRIPT = ROOT / "hyperloglog.py"


class HyperLogLogTests(unittest.TestCase):
    def test_rejects_invalid_precision(self):
        with self.assertRaises(ValueError):
            HyperLogLog(precision=3)
        with self.assertRaises(ValueError):
            HyperLogLog(precision=17)

    def test_estimate_is_reasonable_for_unique_items(self):
        sketch = HyperLogLog(precision=10)
        sketch.extend(f"item-{index}" for index in range(500))
        estimate = sketch.estimate()
        self.assertGreater(estimate, 400)
        self.assertLess(estimate, 600)

    def test_duplicates_do_not_change_registers_after_first_insert(self):
        sketch = HyperLogLog(precision=8)
        sketch.add("alpha")
        first = list(sketch.registers)
        sketch.add("alpha")
        self.assertEqual(first, sketch.registers)

    def test_merge_combines_observations(self):
        left = HyperLogLog(precision=9)
        right = HyperLogLog(precision=9)
        left.extend(f"left-{index}" for index in range(200))
        right.extend(f"right-{index}" for index in range(200))
        merged = left.merge(right)
        self.assertGreater(merged.estimate(), left.estimate())
        self.assertGreater(merged.estimate(), right.estimate())

    def test_merge_requires_matching_precision(self):
        with self.assertRaises(ValueError):
            HyperLogLog(precision=8).merge(HyperLogLog(precision=9))

    def test_save_and_load_round_trip(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            target = temp_dir / "sketch.json"
            sketch = HyperLogLog(precision=8)
            sketch.extend(["alpha", "beta", "gamma"])
            save_hll(target, sketch)
            loaded = load_hll(target)
            self.assertEqual(loaded.to_dict(), sketch.to_dict())
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_simulate_accuracy_is_deterministic(self):
        first = simulate_accuracy(precision=9, cardinality=300, trials=4, seed=11)
        second = simulate_accuracy(precision=9, cardinality=300, trials=4, seed=11)
        self.assertEqual(first, second)
        self.assertLess(first["mean_relative_error"], 0.2)

    def test_simulate_accuracy_rejects_invalid_sizes(self):
        with self.assertRaises(ValueError):
            simulate_accuracy(precision=8, cardinality=0, trials=5)
        with self.assertRaises(ValueError):
            simulate_accuracy(precision=8, cardinality=100, trials=0)

    def test_parse_int_list_rejects_non_numeric_values(self):
        self.assertEqual(parse_int_list("8, 10, 10, 12", argument_name="--precisions"), [8, 10, 12])
        with self.assertRaises(ValueError):
            parse_int_list("8,ten", argument_name="--precisions")
        with self.assertRaises(ValueError):
            parse_int_list(", ,", argument_name="--precisions")

    def test_benchmark_accuracy_is_deterministic(self):
        first = benchmark_accuracy([8, 10], [200, 2000], trials=4, seed=7)
        second = benchmark_accuracy([8, 10], [200, 2000], trials=4, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(len(first["rows"]), 4)
        self.assertEqual(first["best_by_cardinality"][0]["cardinality"], 200)

    def test_benchmark_accuracy_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            benchmark_accuracy([], [100], trials=3)
        with self.assertRaises(ValueError):
            benchmark_accuracy([8], [], trials=3)
        with self.assertRaises(ValueError):
            benchmark_accuracy([8], [0], trials=3)
        with self.assertRaises(ValueError):
            benchmark_accuracy([8], [100], trials=0)

    def test_render_benchmark_markdown_includes_tables(self):
        report = benchmark_accuracy([8], [250], trials=3, seed=5)
        markdown = render_benchmark_markdown(report)
        self.assertIn("# HyperLogLog benchmark report", markdown)
        self.assertIn("## Cardinality 250", markdown)
        self.assertIn("| precision | registers | dense bytes |", markdown)

    def test_infer_input_format_by_extension(self):
        self.assertEqual(infer_input_format(Path("users.csv"), "auto"), "csv")
        self.assertEqual(infer_input_format(Path("events.jsonl"), "auto"), "jsonl")
        self.assertEqual(infer_input_format(Path("events.ndjson"), "auto"), "jsonl")
        self.assertEqual(infer_input_format(Path("events.json"), "auto"), "json")
        self.assertEqual(infer_input_format(Path("users.txt"), "auto"), "lines")

    def test_extract_items_supports_csv_field_selection(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "events.csv"
            source.write_text("user_id,plan\nu1,free\nu2,pro\nu1,team\n,missing\n")
            items, summary = extract_items(source, input_format="auto", field="user_id")
            self.assertEqual(items, ["u1", "u2", "u1"])
            self.assertEqual(summary["input_format"], "csv")
            self.assertEqual(summary["records_read"], 4)
            self.assertEqual(summary["records_skipped"], 1)
            self.assertEqual(summary["records_missing_field"], 0)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_extract_items_supports_jsonl_nested_field_selection(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "events.jsonl"
            source.write_text(
                '{"actor": {"id": "u1"}}\n'
                '{"actor": {"id": "u2"}}\n'
                '{"actor": {"id": null}}\n'
            )
            items, summary = extract_items(source, field="actor.id")
            self.assertEqual(items, ["u1", "u2"])
            self.assertEqual(summary["input_format"], "jsonl")
            self.assertEqual(summary["records_read"], 3)
            self.assertEqual(summary["records_skipped"], 1)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_extract_items_supports_json_array_field_selection(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "events.json"
            source.write_text(json.dumps([{"event": {"visitor": {"id": 101}}}, {"event": {"visitor": {"id": 102}}}]))
            items, summary = extract_items(source, field="event.visitor.id")
            self.assertEqual(items, ["101", "102"])
            self.assertEqual(summary["input_format"], "json")
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_extract_items_requires_field_for_multicolumn_csv(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "events.csv"
            source.write_text("user_id,plan\nu1,free\n")
            with self.assertRaises(ValueError):
                extract_items(source, input_format="csv")
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_extract_items_rejects_unknown_csv_field(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "events.csv"
            source.write_text("user_id,plan\nu1,free\n")
            with self.assertRaises(ValueError):
                extract_items(source, input_format="csv", field="missing")
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_extract_items_rejects_non_scalar_field_values(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "events.jsonl"
            source.write_text('{"actor": {"tags": ["a", "b"]}}\n')
            with self.assertRaises(ValueError):
                extract_items(source, field="actor.tags")
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_extract_items_rejects_missing_json_field_when_no_records_match(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            source = temp_dir / "events.jsonl"
            source.write_text('{"actor": {"id": "u1"}}\n{"actor": {"id": "u2"}}\n')
            with self.assertRaises(ValueError):
                extract_items(source, field="event.visitor.id")
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_cli_reports_clean_error_for_unknown_csv_field(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            csv_input = temp_dir / "events.csv"
            csv_input.write_text("user_id,plan\nu1,free\n")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build",
                    "--input",
                    str(csv_input),
                    "--output",
                    str(temp_dir / "out.json"),
                    "--field",
                    "missing",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("field 'missing' not present in CSV header", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_cli_reports_clean_error_for_invalid_benchmark_precisions(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "benchmark", "--precisions", "8,ten", "--cardinalities", "200"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--precisions must contain only integers", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_build_stats_merge_simulate_and_benchmark(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            input_a = temp_dir / "a.txt"
            input_b = temp_dir / "b.txt"
            csv_input = temp_dir / "events.csv"
            jsonl_input = temp_dir / "events.jsonl"
            sketch_a = temp_dir / "a.json"
            sketch_b = temp_dir / "b.json"
            sketch_csv = temp_dir / "csv.json"
            sketch_jsonl = temp_dir / "jsonl.json"
            merged = temp_dir / "merged.json"
            benchmark_json = temp_dir / "benchmark.json"
            benchmark_md = temp_dir / "benchmark.md"
            input_a.write_text("apple\nbanana\ncarrot\n")
            input_b.write_text("banana\ndate\nelderberry\n")
            csv_input.write_text("user_id,plan\nu1,free\nu2,pro\nu1,team\n")
            jsonl_input.write_text(
                '{"event": {"visitor": {"id": "u9"}}}\n'
                '{"event": {"visitor": {"id": "u10"}}}\n'
                '{"event": {"visitor": {"id": "u9"}}}\n'
            )

            build_a = subprocess.run(
                [sys.executable, str(SCRIPT), "build", "--input", str(input_a), "--output", str(sketch_a), "--precision", "8"],
                capture_output=True,
                text=True,
                check=True,
            )
            build_b = subprocess.run(
                [sys.executable, str(SCRIPT), "build", "--input", str(input_b), "--output", str(sketch_b), "--precision", "8"],
                capture_output=True,
                text=True,
                check=True,
            )
            build_csv = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build",
                    "--input",
                    str(csv_input),
                    "--output",
                    str(sketch_csv),
                    "--precision",
                    "8",
                    "--field",
                    "user_id",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            build_jsonl = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build",
                    "--input",
                    str(jsonl_input),
                    "--output",
                    str(sketch_jsonl),
                    "--precision",
                    "8",
                    "--field",
                    "event.visitor.id",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            data_a = json.loads(build_a.stdout)
            data_b = json.loads(build_b.stdout)
            data_csv = json.loads(build_csv.stdout)
            data_jsonl = json.loads(build_jsonl.stdout)
            self.assertEqual(data_a["inserted"], 3)
            self.assertEqual(data_b["inserted"], 3)
            self.assertEqual(data_csv["input_format"], "csv")
            self.assertEqual(data_csv["records_with_values"], 3)
            self.assertEqual(data_jsonl["input_format"], "jsonl")
            self.assertEqual(data_jsonl["records_with_values"], 3)

            stats = subprocess.run(
                [sys.executable, str(SCRIPT), "stats", "--sketch", str(sketch_a)],
                capture_output=True,
                text=True,
                check=True,
            )
            stats_data = json.loads(stats.stdout)
            self.assertEqual(stats_data["precision"], 8)
            self.assertGreater(stats_data["estimate"], 0)
            self.assertIsInstance(stats_data["rounded_estimate"], int)

            merge = subprocess.run(
                [sys.executable, str(SCRIPT), "merge", "--output", str(merged), str(sketch_a), str(sketch_b)],
                capture_output=True,
                text=True,
                check=True,
            )
            merge_data = json.loads(merge.stdout)
            self.assertTrue(merged.exists())
            self.assertGreater(merge_data["estimate"], stats_data["estimate"])

            simulate = subprocess.run(
                [sys.executable, str(SCRIPT), "simulate", "--precision", "8", "--cardinality", "200", "--trials", "5", "--seed", "2"],
                capture_output=True,
                text=True,
                check=True,
            )
            simulate_data = json.loads(simulate.stdout)
            self.assertEqual(simulate_data["cardinality"], 200)
            self.assertEqual(simulate_data["trials"], 5)

            benchmark = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--precisions",
                    "8,10",
                    "--cardinalities",
                    "200,2000",
                    "--trials",
                    "4",
                    "--seed",
                    "7",
                    "--json-output",
                    str(benchmark_json),
                    "--markdown-output",
                    str(benchmark_md),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            benchmark_data = json.loads(benchmark.stdout)
            self.assertEqual(benchmark_data["precisions"], [8, 10])
            self.assertEqual(benchmark_data["cardinalities"], [200, 2000])
            self.assertEqual(len(benchmark_data["rows"]), 4)
            self.assertTrue(benchmark_json.exists())
            self.assertTrue(benchmark_md.exists())
            self.assertIn("HyperLogLog benchmark report", benchmark_md.read_text())
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
