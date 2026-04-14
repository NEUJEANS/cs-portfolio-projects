import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from hyperloglog import HyperLogLog, load_hll, save_hll, simulate_accuracy

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

    def test_cli_build_stats_merge_and_simulate(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            input_a = temp_dir / "a.txt"
            input_b = temp_dir / "b.txt"
            sketch_a = temp_dir / "a.json"
            sketch_b = temp_dir / "b.json"
            merged = temp_dir / "merged.json"
            input_a.write_text("apple\nbanana\ncarrot\n")
            input_b.write_text("banana\ndate\nelderberry\n")

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
            data_a = json.loads(build_a.stdout)
            data_b = json.loads(build_b.stdout)
            self.assertEqual(data_a["inserted"], 3)
            self.assertEqual(data_b["inserted"], 3)

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
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
