import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from cache_simulator import CacheConfig, CacheSimulator, TraceOperation, format_summary, load_trace, simulate_trace


class CacheSimulatorTests(unittest.TestCase):
    def test_config_derives_set_count(self):
        config = CacheConfig(cache_size=64, block_size=16, associativity=2)
        self.assertEqual(config.set_count, 2)

    def test_decode_address(self):
        simulator = CacheSimulator(CacheConfig(cache_size=64, block_size=16, associativity=2))
        self.assertEqual(
            simulator.decode_address(52),
            {"block_address": 3, "set_index": 1, "tag": 1, "offset": 4},
        )

    def test_lru_eviction_is_per_set(self):
        simulator = CacheSimulator(CacheConfig(cache_size=64, block_size=16, associativity=2))
        for address in [0, 32, 0, 64]:
            simulator.access(TraceOperation("read", address))

        set_zero_tags = {line["tag"] for line in simulator.snapshot()[0]}
        self.assertEqual(set_zero_tags, {0, 2})
        self.assertEqual(simulator.stats["evictions"], 1)
        self.assertEqual(simulator.stats["hits"], 1)
        self.assertEqual(simulator.stats["misses"], 3)

    def test_write_back_defers_memory_write_until_flush(self):
        config = CacheConfig(cache_size=64, block_size=16, associativity=2, write_policy="write-back")
        result = simulate_trace([TraceOperation("write", 0), TraceOperation("write", 4)], config)
        self.assertEqual(result["stats"]["hits"], 1)
        self.assertEqual(result["stats"]["memory_reads"], 1)
        self.assertEqual(result["stats"]["memory_writes"], 1)
        self.assertFalse(result["final_sets"][0][0]["dirty"])

    def test_write_through_counts_every_write(self):
        config = CacheConfig(cache_size=64, block_size=16, associativity=2, write_policy="write-through")
        result = simulate_trace([TraceOperation("write", 0), TraceOperation("write", 4)], config)
        self.assertEqual(result["stats"]["hits"], 1)
        self.assertEqual(result["stats"]["memory_reads"], 1)
        self.assertEqual(result["stats"]["memory_writes"], 2)

    def test_load_trace_rejects_non_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "trace.json"
            trace_path.write_text(json.dumps({"bad": True}))
            with self.assertRaises(ValueError):
                load_trace(trace_path)

    def test_access_rejects_cross_block_operation(self):
        simulator = CacheSimulator(CacheConfig(cache_size=64, block_size=16, associativity=2))
        with self.assertRaises(ValueError):
            simulator.access(TraceOperation("read", 12, size=8))

    def test_summary_contains_key_metrics(self):
        config = CacheConfig(cache_size=64, block_size=16, associativity=2)
        result = simulate_trace([TraceOperation("read", 0), TraceOperation("read", 4)], config)
        summary = format_summary(result)
        self.assertIn("Hit rate: 50.0%", summary)
        self.assertIn("Memory reads: 1", summary)

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "trace.json"
            trace_path.write_text(json.dumps([
                {"op": "read", "address": 0},
                {"op": "write", "address": 16},
            ]))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_DIR / "cache_simulator.py"),
                    str(trace_path),
                    "--cache-size",
                    "64",
                    "--block-size",
                    "16",
                    "--associativity",
                    "2",
                    "--json",
                ],
                cwd=PROJECT_DIR,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["stats"]["reads"], 1)
            self.assertEqual(payload["stats"]["writes"], 1)
            self.assertEqual(payload["config"]["set_count"], 2)


if __name__ == "__main__":
    unittest.main()
