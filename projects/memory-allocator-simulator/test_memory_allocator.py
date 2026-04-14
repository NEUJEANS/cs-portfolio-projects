import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from memory_allocator import MemoryAllocator, run_operations


class MemoryAllocatorTests(unittest.TestCase):
    def test_first_fit_reuses_first_available_hole(self):
        allocator = MemoryAllocator(capacity=20, strategy="first-fit")
        run_operations(allocator, ["alloc:A:5", "alloc:B:7", "alloc:C:4", "free:B", "alloc:D:6"])

        allocated = {segment["allocation_id"]: segment for segment in allocator.layout() if segment["allocated"]}
        self.assertEqual(allocated["D"]["start"], 5)
        self.assertEqual(allocator.metrics()["hole_count"], 2)

    def test_best_fit_prefers_smallest_suitable_hole(self):
        allocator = MemoryAllocator(capacity=30, strategy="best-fit")
        run_operations(
            allocator,
            ["alloc:A:10", "alloc:B:6", "alloc:C:4", "alloc:D:5", "free:B", "free:D", "alloc:E:5"],
        )

        allocated = {segment["allocation_id"]: segment for segment in allocator.layout() if segment["allocated"]}
        self.assertEqual(allocated["E"]["start"], 10)

    def test_worst_fit_prefers_largest_suitable_hole(self):
        allocator = MemoryAllocator(capacity=30, strategy="worst-fit")
        run_operations(
            allocator,
            ["alloc:A:10", "alloc:B:6", "alloc:C:4", "alloc:D:5", "free:B", "free:D", "alloc:E:5"],
        )

        allocated = {segment["allocation_id"]: segment for segment in allocator.layout() if segment["allocated"]}
        self.assertEqual(allocated["E"]["start"], 20)

    def test_compaction_moves_allocations_and_reduces_fragmentation(self):
        allocator = MemoryAllocator(capacity=20, strategy="first-fit")
        run_operations(allocator, ["alloc:A:5", "alloc:B:5", "alloc:C:4", "free:B"])

        before = allocator.metrics()
        moved = allocator.compact()
        after = allocator.metrics()

        self.assertEqual(moved, [{"allocation_id": "C", "from": 10, "to": 5, "size": 4}])
        self.assertEqual(before["external_fragmentation"], 5)
        self.assertEqual(after["external_fragmentation"], 0)
        self.assertEqual(allocator.layout()[-1]["size"], 11)

    def test_duplicate_ids_and_missing_allocations_raise_errors(self):
        allocator = MemoryAllocator(capacity=8)
        allocator.allocate("A", 4)
        with self.assertRaises(ValueError):
            allocator.allocate("A", 2)
        with self.assertRaises(KeyError):
            allocator.free("missing")

    def test_invalid_strategy_fails_fast(self):
        with self.assertRaises(ValueError):
            MemoryAllocator(capacity=8, strategy="random-fit")

    def test_cli_outputs_json_summary(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "memory_allocator.py"),
                "--capacity",
                "16",
                "--strategy",
                "best-fit",
                "--op",
                "alloc:A:4",
                "--op",
                "alloc:B:6",
                "--op",
                "free:A",
                "--op",
                "compact",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["metrics"]["capacity"], 16)
        self.assertEqual(payload["metrics"]["strategy"], "best-fit")
        self.assertEqual(payload["layout"][0]["allocation_id"], "B")


if __name__ == "__main__":
    unittest.main()
