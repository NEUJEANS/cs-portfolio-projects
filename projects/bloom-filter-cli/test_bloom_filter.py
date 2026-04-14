import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from bloom_filter import BloomFilter, load_filter, save_filter


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

    def test_cli_build_check_and_stats(self):
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
        finally:
            for child in tmp_dir.iterdir():
                child.unlink()
            tmp_dir.rmdir()

    def test_invalid_constructor_arguments(self):
        with self.assertRaises(ValueError):
            BloomFilter(capacity=0, error_rate=0.1)
        with self.assertRaises(ValueError):
            BloomFilter(capacity=10, error_rate=1.5)


if __name__ == "__main__":
    unittest.main()
