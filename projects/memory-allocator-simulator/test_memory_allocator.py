import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from memory_allocator import MemoryAllocator, render_layout_ascii, run_operations


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

        self.assertEqual(moved, [{"allocation_id": "C", "from": 10, "to": 5, "size": 4, "requested_size": 4}])
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

    def test_timeline_capture_renders_each_step(self):
        allocator = MemoryAllocator(capacity=8, strategy="first-fit")
        payload = run_operations(
            allocator,
            ["alloc:A:3", "alloc:B:2", "free:A"],
            include_timeline=True,
            timeline_width=8,
        )

        self.assertEqual(
            [entry["render"] for entry in payload["timeline"]],
            ["........", "AAA.....", "AAABB...", "...BB..."],
        )
        self.assertIn("| 3 | `free:A` | `...BB...` | 2 | 2 | 0 | 6 | 2 |", payload["timeline_markdown"])

    def test_render_layout_ascii_scales_large_capacity(self):
        layout = [
            {"start": 0, "end": 32, "size": 32, "allocated": True, "allocation_id": "alpha"},
            {"start": 32, "end": 96, "size": 64, "allocated": False, "allocation_id": None},
            {"start": 96, "end": 128, "size": 32, "allocated": True, "allocation_id": "beta"},
        ]
        rendered = render_layout_ascii(layout, capacity=128, width=8)
        self.assertEqual(rendered, "AA....BB")

    def test_alignment_rounds_size_and_tracks_internal_fragmentation(self):
        allocator = MemoryAllocator(capacity=24, strategy="first-fit", alignment=4)
        allocator.allocate("A", 5)
        allocator.allocate("B", 3)

        layout = [segment for segment in allocator.layout() if segment["allocated"]]
        metrics = allocator.metrics()
        self.assertEqual(layout[0]["size"], 8)
        self.assertEqual(layout[0]["requested_size"], 5)
        self.assertEqual(layout[0]["internal_fragmentation"], 3)
        self.assertEqual(layout[1]["size"], 4)
        self.assertEqual(metrics["requested_bytes"], 8)
        self.assertEqual(metrics["allocated_bytes"], 12)
        self.assertEqual(metrics["internal_fragmentation"], 4)
        self.assertEqual(metrics["payload_utilization"], round(8 / 24, 4))

    def test_compaction_preserves_alignment_metadata(self):
        allocator = MemoryAllocator(capacity=24, strategy="first-fit", alignment=4)
        run_operations(allocator, ["alloc:A:5", "alloc:B:4", "free:A", "alloc:C:3"])
        moved = allocator.compact()
        layout = [segment for segment in allocator.layout() if segment["allocated"]]

        self.assertEqual(moved, [{"allocation_id": "B", "from": 8, "to": 4, "size": 4, "requested_size": 4}])
        self.assertEqual(layout[0]["allocation_id"], "C")
        self.assertEqual(layout[0]["requested_size"], 3)
        self.assertEqual(layout[0]["internal_fragmentation"], 1)
        self.assertEqual(layout[1]["allocation_id"], "B")


    def test_load_trace_accepts_object_defaults(self):
        trace_path = PROJECT_DIR / "test_trace.json"
        trace_path.write_text(
            json.dumps(
                {
                    "capacity": 18,
                    "strategy": "worst-fit",
                    "alignment": 2,
                    "timeline": True,
                    "timeline_width": 18,
                    "operations": ["alloc:A:5", "alloc:B:3", "free:A"],
                }
            )
        )
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_DIR / "memory_allocator.py"),
                    "--trace-in",
                    str(trace_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            trace_path.unlink(missing_ok=True)

        payload = json.loads(result.stdout)
        self.assertEqual(payload["metrics"]["capacity"], 18)
        self.assertEqual(payload["metrics"]["strategy"], "worst-fit")
        self.assertEqual(payload["metrics"]["alignment"], 2)
        self.assertEqual(payload["timeline"][-1]["render"], "......BBBB........")

    def test_cli_trace_out_writes_replayable_bundle(self):
        trace_path = PROJECT_DIR / "exported_trace.json"
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_DIR / "memory_allocator.py"),
                    "--capacity",
                    "20",
                    "--strategy",
                    "best-fit",
                    "--alignment",
                    "4",
                    "--op",
                    "alloc:A:5",
                    "--op",
                    "alloc:B:6",
                    "--trace-out",
                    str(trace_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            trace_payload = json.loads(trace_path.read_text())
        finally:
            trace_path.unlink(missing_ok=True)

        self.assertEqual(trace_payload["capacity"], 20)
        self.assertEqual(trace_payload["strategy"], "best-fit")
        self.assertEqual(trace_payload["alignment"], 4)
        self.assertEqual(trace_payload["operations"], ["alloc:A:5", "alloc:B:6"])

    def test_cli_rejects_non_positive_timeline_width(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "memory_allocator.py"),
                "--capacity",
                "16",
                "--timeline-width",
                "0",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--timeline-width must be positive", result.stderr)

    def test_cli_outputs_json_summary(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "memory_allocator.py"),
                "--capacity",
                "16",
                "--strategy",
                "best-fit",
                "--alignment",
                "4",
                "--op",
                "alloc:A:4",
                "--op",
                "alloc:B:6",
                "--op",
                "free:A",
                "--op",
                "compact",
                "--timeline",
                "--timeline-width",
                "16",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["metrics"]["capacity"], 16)
        self.assertEqual(payload["metrics"]["strategy"], "best-fit")
        self.assertEqual(payload["metrics"]["alignment"], 4)
        self.assertEqual(payload["metrics"]["requested_bytes"], 6)
        self.assertEqual(payload["metrics"]["allocated_bytes"], 8)
        self.assertEqual(payload["metrics"]["internal_fragmentation"], 2)
        self.assertEqual(payload["layout"][0]["allocation_id"], "B")
        self.assertEqual(payload["layout"][0]["requested_size"], 6)
        self.assertEqual(payload["timeline"][0]["render"], "................")
        self.assertIn("Alignment: 4 byte(s)", payload["timeline_markdown"])


if __name__ == "__main__":
    unittest.main()
