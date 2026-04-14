from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = PROJECT_ROOT / "projects" / "mini-mapreduce-lab"
MODULE_PATH = PROJECT_DIR / "mapreduce.py"

spec = importlib.util.spec_from_file_location("mini_mapreduce_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

benchmark_wordcount = module.benchmark_wordcount
execute_job = module.execute_job
stable_partition = module.stable_partition


class MiniMapReduceRepoTests(unittest.TestCase):
    def test_wordcount_across_multiple_shards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            a = Path(tmpdir) / "a.txt"
            b = Path(tmpdir) / "b.txt"
            a.write_text("Red fish blue fish\nred bird\n", encoding="utf-8")
            b.write_text("blue bird bird\n", encoding="utf-8")

            result = execute_job("wordcount", [a, b], shard_size=2, reducers=2)

            self.assertEqual(result.shard_count, 2)
            self.assertEqual(result.reducers, 2)
            self.assertEqual(result.output["bird"], 3)
            self.assertEqual(sum(item["records"] for item in result.reducer_stats), 9)

    def test_json_group_count_handles_missing_and_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = Path(tmpdir) / "events.jsonl"
            data.write_text(
                "\n".join(
                    [
                        '{"status":"ok"}',
                        '{"status":"ok"}',
                        '{"status":null}',
                        '{"other":1}',
                        '{"status":"error"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = execute_job("json-group-count", [data], shard_size=2, group_field="status", reducers=3)
            self.assertEqual(result.output["ok"], 2)
            self.assertEqual(result.output["<missing>"], 1)
            self.assertEqual(len(result.reducer_stats), 3)

    def test_partitioning_is_deterministic(self) -> None:
        keys = ["alpha", "beta", "gamma", "delta"]
        self.assertEqual([stable_partition(key, 4) for key in keys], [stable_partition(key, 4) for key in keys])

    def test_reducer_count_changes_bucket_stats_not_aggregate_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            source.write_text("alpha beta alpha gamma beta alpha\n", encoding="utf-8")

            single = execute_job("wordcount", [source], shard_size=2, reducers=1)
            many = execute_job("wordcount", [source], shard_size=2, reducers=4)

            self.assertEqual(single.output, many.output)
            self.assertNotEqual(single.reducer_stats, many.reducer_stats)

    def test_benchmark_result_is_deterministic_for_same_seed(self) -> None:
        first = benchmark_wordcount("balanced", records=90, shard_size=15, reducers=[1, 3], seed=99)
        second = benchmark_wordcount("balanced", records=90, shard_size=15, reducers=[1, 3], seed=99)

        self.assertEqual(first.scenario, second.scenario)
        self.assertEqual(first.total_records, second.total_records)
        self.assertEqual(first.unique_keys, second.unique_keys)
        self.assertEqual([row["reducers"] for row in first.timings_ms], [1, 3])
        self.assertEqual(
            [(row["reducers"], row["map_records"], row["unique_keys"]) for row in first.timings_ms],
            [(row["reducers"], row["map_records"], row["unique_keys"]) for row in second.timings_ms],
        )

    def test_benchmark_rejects_non_positive_shard_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "shard_size must be positive"):
            benchmark_wordcount("skewed", records=100, shard_size=0, reducers=[1, 2])

    def test_cli_writes_json_output_with_reducer_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            output = Path(tmpdir) / "result.json"
            source.write_text("alpha beta alpha\n", encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "run",
                    "wordcount",
                    str(source),
                    "--reducers",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["reducers"], 2)
            self.assertEqual(len(payload["reducer_stats"]), 2)

    def test_cli_benchmark_writes_timing_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "benchmark.json"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--scenario",
                    "skewed",
                    "--records",
                    "150",
                    "--shard-size",
                    "30",
                    "--reducers",
                    "1",
                    "2",
                    "4",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["scenario"], "skewed")
            self.assertEqual(payload["reducers"], [1, 2, 4])
            self.assertEqual(len(payload["timings_ms"]), 3)
            self.assertIn("skew_ratio", payload["timings_ms"][2])

    def test_programmatic_api_rejects_non_positive_reducers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            source.write_text("alpha\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "reducers must be positive"):
                execute_job("wordcount", [source], shard_size=1, reducers=0)


if __name__ == "__main__":
    unittest.main()
