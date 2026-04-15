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
PLUGIN_PATH = PROJECT_DIR / "plugins_top_score.py"

spec = importlib.util.spec_from_file_location("mini_mapreduce_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

benchmark_job = module.benchmark_job
execute_job = module.execute_job
load_plugin = module.load_plugin
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

    def test_plugin_job_supports_custom_reducer_logic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            source.write_text("Alice,5\nBob,8\nAlice,11\nBob,3\n", encoding="utf-8")

            result = execute_job("plugin", [source], shard_size=2, reducers=2, plugin_path=PLUGIN_PATH)

            self.assertEqual(result.job, "plugin-max-score")
            self.assertEqual(result.output, {"alice": 11, "bob": 8})
            self.assertTrue(str(result.plugin).endswith("plugins_top_score.py"))

    def test_load_plugin_rejects_missing_mapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_plugin = Path(tmpdir) / "bad_plugin.py"
            bad_plugin.write_text("def reduce_key(key, values):\n    return sum(values)\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "map_records"):
                load_plugin(bad_plugin)

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
        first = benchmark_job("wordcount", "balanced", records=90, shard_size=15, reducers=[1, 3], seed=99)
        second = benchmark_job("wordcount", "balanced", records=90, shard_size=15, reducers=[1, 3], seed=99)

        self.assertEqual(first.scenario, second.scenario)
        self.assertEqual(first.total_records, second.total_records)
        self.assertEqual(first.unique_keys, second.unique_keys)
        self.assertEqual([row["reducers"] for row in first.timings_ms], [1, 3])
        self.assertEqual(
            [(row["reducers"], row["map_records"], row["unique_keys"]) for row in first.timings_ms],
            [(row["reducers"], row["map_records"], row["unique_keys"]) for row in second.timings_ms],
        )
        self.assertEqual(first.heatmap_rows, second.heatmap_rows)

    def test_benchmark_rejects_non_positive_shard_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "shard_size must be positive"):
            benchmark_job("wordcount", "skewed", records=100, shard_size=0, reducers=[1, 2])

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

    def test_cli_plugin_writes_expected_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            output = Path(tmpdir) / "plugin.json"
            source.write_text("Alice,4\nAlice,9\nBob,3\n", encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "run",
                    "plugin",
                    str(source),
                    "--plugin",
                    str(PLUGIN_PATH),
                    "--reducers",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["job"], "plugin-max-score")
            self.assertEqual(payload["output"], {"alice": 9, "bob": 3})

    def test_cli_benchmark_writes_timing_and_heatmap_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "benchmark.json"
            heatmap_output = Path(tmpdir) / "benchmark-heatmap.csv"
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
                    "--heatmap-output",
                    str(heatmap_output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            heatmap_rows = heatmap_output.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(payload["scenario"], "skewed")
            self.assertEqual(payload["job"], "wordcount")
            self.assertEqual(payload["reducers"], [1, 2, 4])
            self.assertEqual(len(payload["timings_ms"]), 3)
            self.assertIn("skew_ratio", payload["timings_ms"][2])
            self.assertTrue(payload["heatmap_rows"])
            self.assertEqual(heatmap_rows[0], "job,plugin,scenario,seed,reducers,shard_index,reducer,records,unique_keys")

    def test_plugin_benchmark_result_includes_plugin_metadata(self) -> None:
        result = benchmark_job("plugin", "balanced", records=90, shard_size=15, reducers=[2, 3], seed=99, plugin_path=PLUGIN_PATH)

        self.assertEqual(result.job, "plugin-max-score")
        self.assertTrue(result.plugin.endswith("plugins_top_score.py"))
        self.assertTrue(result.heatmap_rows)
        self.assertTrue(all(row["plugin"] for row in result.heatmap_rows))

    def test_cli_plugin_benchmark_writes_expected_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "plugin-benchmark.json"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--job",
                    "plugin",
                    "--plugin",
                    str(PLUGIN_PATH),
                    "--scenario",
                    "balanced",
                    "--records",
                    "120",
                    "--shard-size",
                    "20",
                    "--reducers",
                    "2",
                    "4",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["job"], "plugin-max-score")
            self.assertTrue(payload["plugin"].endswith("plugins_top_score.py"))
            self.assertEqual(payload["reducers"], [2, 4])

    def test_cli_benchmark_html_report_contains_svg_charts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            html_output = Path(tmpdir) / "benchmark-report.html"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--scenario",
                    "balanced",
                    "--records",
                    "120",
                    "--shard-size",
                    "20",
                    "--reducers",
                    "1",
                    "3",
                    "--html-output",
                    str(html_output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            report = html_output.read_text(encoding="utf-8")
            self.assertIn("Elapsed timing chart", report)
            self.assertIn("Reducer load chart", report)
            self.assertIn("Elapsed benchmark timing by reducer count", report)
            self.assertIn("Reducer load totals for 3 reducers", report)
            self.assertIn("<svg viewBox='0 0 680 240'", report)
            self.assertIn("<svg viewBox='0 0 680 220'", report)

    def test_programmatic_api_rejects_non_positive_reducers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            source.write_text("alpha\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "reducers must be positive"):
                execute_job("wordcount", [source], shard_size=1, reducers=0)


if __name__ == "__main__":
    unittest.main()
