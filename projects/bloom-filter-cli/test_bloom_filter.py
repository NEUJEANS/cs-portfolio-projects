import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from bloom_filter import (
    BloomFilter,
    CountingBloomFilter,
    benchmark_filter,
    compare_artifact_sizes,
    load_filter,
    load_filter_binary,
    save_filter,
    save_filter_binary,
)


SCRIPT = ROOT / "bloom_filter.py"


class BloomFilterTests(unittest.TestCase):
    def test_parameter_calculation_is_positive(self):
        bloom = BloomFilter(capacity=1000, error_rate=0.01)
        self.assertGreater(bloom.bit_count, 0)
        self.assertGreater(bloom.hash_count, 0)
        self.assertLessEqual(bloom.hash_count, 16)

    def test_insert_and_membership_behavior(self):
        bloom = BloomFilter(capacity=20, error_rate=0.01)
        bloom.extend(["alpha", "beta", "gamma"])
        self.assertTrue(bloom.might_contain("alpha"))
        self.assertTrue(bloom.might_contain("beta"))
        self.assertIn(bloom.might_contain("not-present"), {True, False})

    def test_estimated_false_positive_rate_starts_at_zero(self):
        bloom = BloomFilter(capacity=20, error_rate=0.05)
        self.assertEqual(bloom.estimated_false_positive_rate(), 0.0)

    def test_benchmark_filter_is_deterministic_with_seed(self):
        first = benchmark_filter(capacity=200, error_rate=0.05, inserted_count=80, probe_count=200, seed=7)
        second = benchmark_filter(capacity=200, error_rate=0.05, inserted_count=80, probe_count=200, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(first["probe_count"], 200)
        self.assertEqual(first["inserted_count"], 80)
        self.assertGreaterEqual(first["observed_false_positive_rate"], 0.0)
        self.assertLessEqual(first["observed_false_positive_rate"], 1.0)

    def test_benchmark_filter_rejects_non_positive_sizes(self):
        with self.assertRaises(ValueError):
            benchmark_filter(capacity=100, error_rate=0.05, inserted_count=0, probe_count=10)
        with self.assertRaises(ValueError):
            benchmark_filter(capacity=100, error_rate=0.05, inserted_count=10, probe_count=0)

    def test_save_and_load_round_trip(self):
        tmp_dir = Path(self._testMethodName)
        tmp_dir.mkdir(exist_ok=True)
        try:
            bloom = BloomFilter(capacity=25, error_rate=0.02)
            bloom.extend(["delta", "epsilon", "zeta"])
            target = tmp_dir / "filter.json"
            save_filter(target, bloom)

            reloaded = load_filter(target)
            self.assertEqual(reloaded.to_dict(), bloom.to_dict())
            self.assertTrue(reloaded.might_contain("delta"))
        finally:
            for child in tmp_dir.iterdir():
                child.unlink()
            tmp_dir.rmdir()

    def test_standard_binary_round_trip(self):
        bloom = BloomFilter(capacity=40, error_rate=0.02)
        bloom.extend(["alpha", "beta", "gamma", "delta"])
        with tempfile.NamedTemporaryFile(suffix=".bf", delete=False) as handle:
            target = Path(handle.name)
        try:
            save_filter_binary(target, bloom)
            restored = load_filter_binary(target)
            self.assertEqual(restored.to_dict(), bloom.to_dict())
            self.assertTrue(load_filter(target).might_contain("alpha"))
        finally:
            if target.exists():
                target.unlink()

    def test_counting_filter_supports_remove_and_round_trip(self):
        counting = CountingBloomFilter(capacity=30, error_rate=0.05, counter_bits=8)
        counting.extend(["alpha", "beta", "gamma"])
        self.assertTrue(counting.might_contain("beta"))
        self.assertTrue(counting.remove("beta"))
        self.assertFalse(counting.might_contain("beta"))
        self.assertFalse(counting.remove("beta"))

        payload = counting.to_dict()
        restored = load_filter_json(payload)
        self.assertEqual(restored.to_dict(), payload)
        self.assertEqual(restored.variant, "counting")

    def test_counting_binary_round_trip(self):
        counting = CountingBloomFilter(capacity=20, error_rate=0.05, counter_bits=12)
        counting.extend(["apple", "banana", "banana", "carrot"])
        with tempfile.NamedTemporaryFile(suffix=".bf", delete=False) as handle:
            target = Path(handle.name)
        try:
            save_filter_binary(target, counting)
            restored = load_filter_binary(target)
            self.assertEqual(restored.to_dict(), counting.to_dict())
            self.assertTrue(load_filter(target).might_contain("banana"))
        finally:
            if target.exists():
                target.unlink()

    def test_counting_filter_rejects_invalid_counter_shapes(self):
        with self.assertRaises(ValueError):
            CountingBloomFilter(capacity=10, error_rate=0.1, counter_bits=0)
        with self.assertRaises(ValueError):
            CountingBloomFilter(capacity=10, error_rate=0.1, counters=[1, 2, 3])

    def test_counting_filter_detects_counter_overflow(self):
        counting = CountingBloomFilter(capacity=10, error_rate=0.1, counter_bits=1)
        counting.add("repeat-item")
        with self.assertRaises(OverflowError):
            counting.add("repeat-item")

    def test_compare_artifact_sizes_reports_counting_overhead(self):
        result = compare_artifact_sizes(capacity=100, error_rate=0.05, inserted_count=40, counter_bits=8)
        self.assertGreater(result["standard"]["json_bytes"], result["standard"]["binary_bytes"])
        self.assertGreater(result["counting"]["json_bytes"], result["counting"]["binary_bytes"])
        self.assertGreater(result["binary_overhead_ratio_counting_vs_standard"], 1.0)

    def test_cli_build_check_stats_and_benchmark(self):
        tmp_dir = Path(self._testMethodName)
        tmp_dir.mkdir(exist_ok=True)
        try:
            items_file = tmp_dir / "items.txt"
            filter_file = tmp_dir / "filter.json"
            items_file.write_text("alpha\nbeta\ngamma\n")

            build_result = subprocess.run(
                [sys.executable, str(SCRIPT), "build", "--input", str(items_file), "--output", str(filter_file), "--capacity", "10", "--error-rate", "0.05"],
                capture_output=True,
                text=True,
                check=True,
            )
            build_data = json.loads(build_result.stdout)
            self.assertEqual(build_data["inserted"], 3)
            self.assertTrue(filter_file.exists())

            check_result = subprocess.run(
                [sys.executable, str(SCRIPT), "check", "--filter", str(filter_file), "alpha", "theta"],
                capture_output=True,
                text=True,
                check=True,
            )
            check_data = json.loads(check_result.stdout)
            self.assertEqual(check_data[0], {"item": "alpha", "might_contain": True})
            self.assertEqual(check_data[1]["item"], "theta")

            stats_result = subprocess.run(
                [sys.executable, str(SCRIPT), "stats", "--filter", str(filter_file)],
                capture_output=True,
                text=True,
                check=True,
            )
            stats_data = json.loads(stats_result.stdout)
            self.assertEqual(stats_data["inserted_count"], 3)
            self.assertGreater(stats_data["set_bits"], 0)

            benchmark_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--capacity",
                    "100",
                    "--error-rate",
                    "0.05",
                    "--inserted-count",
                    "50",
                    "--probe-count",
                    "120",
                    "--seed",
                    "9",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            benchmark_data = json.loads(benchmark_result.stdout)
            self.assertEqual(benchmark_data["inserted_count"], 50)
            self.assertEqual(benchmark_data["probe_count"], 120)
            self.assertIn("observed_false_positive_rate", benchmark_data)
            self.assertIn("false_positive_count", benchmark_data)
        finally:
            for child in tmp_dir.iterdir():
                child.unlink()
            tmp_dir.rmdir()

    def test_cli_counting_build_remove_and_stats(self):
        tmp_dir = Path(self._testMethodName)
        tmp_dir.mkdir(exist_ok=True)
        try:
            items_file = tmp_dir / "items.txt"
            filter_file = tmp_dir / "counting_filter.json"
            items_file.write_text("alpha\nbeta\ngamma\n")

            build_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build-counting",
                    "--input",
                    str(items_file),
                    "--output",
                    str(filter_file),
                    "--capacity",
                    "10",
                    "--error-rate",
                    "0.05",
                    "--counter-bits",
                    "8",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            build_data = json.loads(build_result.stdout)
            self.assertEqual(build_data["variant"], "counting")
            self.assertEqual(build_data["inserted"], 3)

            remove_result = subprocess.run(
                [sys.executable, str(SCRIPT), "remove", "--filter", str(filter_file), "beta", "missing"],
                capture_output=True,
                text=True,
                check=True,
            )
            remove_data = json.loads(remove_result.stdout)
            self.assertEqual(remove_data["results"][0]["item"], "beta")
            self.assertTrue(remove_data["results"][0]["removed"])
            self.assertFalse(remove_data["results"][1]["removed"])

            stats_result = subprocess.run(
                [sys.executable, str(SCRIPT), "stats", "--filter", str(filter_file)],
                capture_output=True,
                text=True,
                check=True,
            )
            stats_data = json.loads(stats_result.stdout)
            self.assertEqual(stats_data["variant"], "counting")
            self.assertEqual(stats_data["inserted_count"], 2)
            self.assertGreaterEqual(stats_data["non_zero_counters"], 1)
        finally:
            for child in tmp_dir.iterdir():
                child.unlink()
            tmp_dir.rmdir()

    def test_cli_export_binary_and_inspect(self):
        tmp_dir = Path(self._testMethodName)
        tmp_dir.mkdir(exist_ok=True)
        try:
            items_file = tmp_dir / "items.txt"
            filter_file = tmp_dir / "filter.json"
            binary_file = tmp_dir / "filter.bf"
            items_file.write_text("alpha\nbeta\ngamma\n")
            subprocess.run(
                [sys.executable, str(SCRIPT), "build", "--input", str(items_file), "--output", str(filter_file), "--capacity", "10", "--error-rate", "0.05"],
                capture_output=True,
                text=True,
                check=True,
            )

            export_result = subprocess.run(
                [sys.executable, str(SCRIPT), "export-binary", "--filter", str(filter_file), "--output", str(binary_file)],
                capture_output=True,
                text=True,
                check=True,
            )
            export_data = json.loads(export_result.stdout)
            self.assertEqual(export_data["variant"], "standard")
            self.assertTrue(binary_file.exists())

            inspect_result = subprocess.run(
                [sys.executable, str(SCRIPT), "inspect-binary", "--filter", str(binary_file)],
                capture_output=True,
                text=True,
                check=True,
            )
            inspect_data = json.loads(inspect_result.stdout)
            self.assertEqual(inspect_data["filter"], str(binary_file))
            self.assertEqual(inspect_data["inserted_count"], 3)

            check_result = subprocess.run(
                [sys.executable, str(SCRIPT), "check", "--filter", str(binary_file), "alpha", "theta"],
                capture_output=True,
                text=True,
                check=True,
            )
            check_data = json.loads(check_result.stdout)
            self.assertTrue(check_data[0]["might_contain"])
        finally:
            for child in tmp_dir.iterdir():
                child.unlink()
            tmp_dir.rmdir()

    def test_cli_compare_sizes(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare-sizes",
                "--capacity",
                "100",
                "--error-rate",
                "0.05",
                "--inserted-count",
                "40",
                "--counter-bits",
                "8",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        self.assertIn("standard", data)
        self.assertIn("counting", data)
        self.assertGreater(data["counting"]["binary_bytes"], data["standard"]["binary_bytes"])

    def test_cli_remove_rejects_standard_filters_cleanly(self):
        tmp_dir = Path(self._testMethodName)
        tmp_dir.mkdir(exist_ok=True)
        try:
            items_file = tmp_dir / "items.txt"
            filter_file = tmp_dir / "filter.json"
            items_file.write_text("alpha\nbeta\n")
            subprocess.run(
                [sys.executable, str(SCRIPT), "build", "--input", str(items_file), "--output", str(filter_file), "--capacity", "10", "--error-rate", "0.05"],
                capture_output=True,
                text=True,
                check=True,
            )

            remove_result = subprocess.run(
                [sys.executable, str(SCRIPT), "remove", "--filter", str(filter_file), "alpha"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(remove_result.returncode, 2)
            self.assertIn("counting Bloom filter", remove_result.stderr)
        finally:
            for child in tmp_dir.iterdir():
                child.unlink()
            tmp_dir.rmdir()

    def test_invalid_constructor_arguments(self):
        with self.assertRaises(ValueError):
            BloomFilter(capacity=0, error_rate=0.1)
        with self.assertRaises(ValueError):
            BloomFilter(capacity=10, error_rate=1.5)


def load_filter_json(payload: dict):
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as handle:
        tmp_path = Path(handle.name)
        handle.write(json.dumps(payload))
    try:
        return load_filter(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
