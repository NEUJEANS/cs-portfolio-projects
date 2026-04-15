from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from mapreduce import benchmark_job, execute_job, inspect_plugin, load_plugin, stable_partition


class MiniMapReduceTests(unittest.TestCase):
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
            self.assertEqual(result.output["blue"], 2)
            self.assertEqual(result.output["fish"], 2)
            self.assertEqual(result.output["red"], 2)
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
            self.assertEqual(result.output["error"], 1)
            self.assertEqual(result.output["<null>"], 1)
            self.assertEqual(result.output["<missing>"], 1)
            self.assertEqual(len(result.reducer_stats), 3)

    def test_plugin_job_supports_custom_reducer_logic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            source.write_text("Alice,5\nBob,8\nAlice,11\nBob,3\n", encoding="utf-8")

            result = execute_job(
                "plugin",
                [source],
                shard_size=2,
                reducers=2,
                plugin_path=PROJECT_DIR / "plugins_top_score.py",
            )

            self.assertEqual(result.job, "plugin-max-score")
            self.assertEqual(result.output, {"alice": 11, "bob": 8})
            self.assertIsNotNone(result.plugin)

    def test_plugin_job_supports_structured_combiner_values_and_float_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            source.write_text("Alice,5\nBob,8\nAlice,11\nBob,3\n", encoding="utf-8")

            result = execute_job(
                "plugin",
                [source],
                shard_size=2,
                reducers=2,
                plugin_path=PROJECT_DIR / "plugins_average_score.py",
            )

            self.assertEqual(result.job, "plugin-average-score")
            self.assertEqual(result.output, {"alice": 8.0, "bob": 5.5})
            self.assertIsNotNone(result.plugin)

    def test_plugin_job_rejects_non_json_serializable_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            plugin = Path(tmpdir) / "bad_plugin.py"
            source.write_text("Alice,5\n", encoding="utf-8")
            plugin.write_text(
                "def map_records(lines):\n"
                "    for line in lines:\n"
                "        if line.strip():\n"
                "            yield 'alice', {1, 2, 3}\n"
                "def reduce_key(key, values):\n"
                "    return values[0]\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "JSON-serializable"):
                execute_job("plugin", [source], shard_size=1, reducers=1, plugin_path=plugin)

    def test_load_plugin_supports_importable_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            package_dir = Path(tmpdir) / "demo_plugins"
            package_dir.mkdir()
            (package_dir / "__init__.py").write_text("", encoding="utf-8")
            (package_dir / "topscore.py").write_text(
                "JOB_NAME = 'module-max-score'\n"
                "def map_records(lines):\n"
                "    for line in lines:\n"
                "        if not line.strip():\n"
                "            continue\n"
                "        name, score = line.split(',')\n"
                "        yield name.strip().lower(), int(score)\n"
                "def combine_values(key, values):\n"
                "    return max(values)\n"
                "def reduce_key(key, values):\n"
                "    return max(values)\n",
                encoding="utf-8",
            )
            sys.path.insert(0, tmpdir)
            self.addCleanup(lambda: sys.path.remove(tmpdir))

            plugin = load_plugin("demo_plugins.topscore")

            self.assertEqual(plugin.name, "module-max-score")
            self.assertTrue(str(plugin.path).endswith("topscore.py"))

    def test_inspect_plugin_reports_callable_metadata_and_dataset_families(self) -> None:
        inspection = inspect_plugin(PROJECT_DIR / "plugins_average_score.py")

        self.assertEqual(inspection.name, "plugin-average-score")
        self.assertTrue(inspection.plugin.endswith("plugins_average_score.py"))
        self.assertEqual(inspection.available_dataset_families, ["default", "exam-cram", "project-week"])
        self.assertTrue(inspection.mapper.endswith(".map_records"))
        self.assertTrue(inspection.reducer.endswith(".reduce_key"))
        self.assertTrue(inspection.combiner and inspection.combiner.endswith(".combine_values"))
        self.assertTrue(inspection.benchmark_generator and inspection.benchmark_generator.endswith(".benchmark_records"))


    def test_load_plugin_rejects_missing_mapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_plugin = Path(tmpdir) / "bad_plugin.py"
            bad_plugin.write_text("def reduce_key(key, values):\n    return sum(values)\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "map_records"):
                load_plugin(bad_plugin)

    def test_partitioning_is_deterministic(self) -> None:
        keys = ["alpha", "beta", "gamma", "delta"]
        first = [stable_partition(key, 4) for key in keys]
        second = [stable_partition(key, 4) for key in keys]
        self.assertEqual(first, second)
        self.assertTrue(all(0 <= bucket < 4 for bucket in first))

    def test_reducer_count_changes_bucket_stats_not_aggregate_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            source.write_text("alpha beta alpha gamma beta alpha\n", encoding="utf-8")

            single = execute_job("wordcount", [source], shard_size=2, reducers=1)
            many = execute_job("wordcount", [source], shard_size=2, reducers=4)

            self.assertEqual(single.output, many.output)
            self.assertNotEqual(single.reducer_stats, many.reducer_stats)

    def test_cli_inspect_plugin_writes_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "plugin-inspect.json"

            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "inspect-plugin",
                    "--plugin",
                    "projects/mini-mapreduce-lab/plugins_average_score.py",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], "plugin-average-score")
            self.assertEqual(payload["available_dataset_families"], ["default", "exam-cram", "project-week"])
            self.assertTrue(payload["mapper"].endswith(".map_records"))
            self.assertTrue(payload["benchmark_generator"].endswith(".benchmark_records"))

    def test_benchmark_wordcount_reports_skew_metrics(self) -> None:
        result = benchmark_job("wordcount", "skewed", records=200, shard_size=25, reducers=[1, 4], seed=7)

        self.assertEqual(result.scenario, "skewed")
        self.assertEqual(result.dataset_family, "default")
        self.assertEqual(result.total_records, 200)
        self.assertEqual(result.reducers, [1, 4])
        self.assertEqual(len(result.timings_ms), 2)
        self.assertGreaterEqual(result.timings_ms[0]["skew_ratio"], 1.0)
        self.assertIn("max_reducer_records", result.timings_ms[1])

    def test_benchmark_wordcount_can_render_csv_rows(self) -> None:
        result = benchmark_job("wordcount", "balanced", records=120, shard_size=20, reducers=[1, 3], seed=5)

        csv_output = result.to_csv().strip().splitlines()

        self.assertEqual(csv_output[0], "job,plugin,scenario,dataset_family,seed,total_records,shard_size,reducers,elapsed_ms,shards,map_records,unique_keys,max_reducer_records,skew_ratio")
        self.assertEqual(len(csv_output), 3)
        self.assertTrue(csv_output[1].startswith("wordcount,,balanced,default,5,120,20,1,"))
        self.assertTrue(csv_output[2].startswith("wordcount,,balanced,default,5,120,20,3,"))

    def test_benchmark_wordcount_can_render_heatmap_csv_rows(self) -> None:
        result = benchmark_job("wordcount", "balanced", records=120, shard_size=20, reducers=[2], seed=5)

        rows = result.heatmap_to_csv().strip().splitlines()

        self.assertEqual(rows[0], "job,plugin,scenario,dataset_family,seed,reducers,shard_index,reducer,records,unique_keys")
        self.assertEqual(len(rows), 1 + (6 * 2))
        self.assertTrue(rows[1].startswith("wordcount,,balanced,default,5,2,0,"))
        self.assertTrue(any(",0," in row for row in rows[1:]))
        self.assertTrue(any(",1," in row for row in rows[1:]))

    def test_benchmark_wordcount_can_render_markdown_report(self) -> None:
        result = benchmark_job("wordcount", "balanced", records=120, shard_size=20, reducers=[2, 3], seed=5)

        report = result.to_markdown()

        self.assertIn("# Mini MapReduce benchmark report (wordcount: balanced)", report)
        self.assertIn("- Dataset family: `default`", report)
        self.assertIn("| Reducers | Elapsed (ms) | Shards | Map records | Unique keys | Max reducer records | Skew ratio |", report)
        self.assertIn("### Reducers = 2", report)
        self.assertIn("### Reducers = 3", report)
        self.assertIn("| Shard | r0 | r1 |", report)
        self.assertIn("Reducer load stddev", report)

    def test_benchmark_wordcount_can_render_html_report(self) -> None:
        result = benchmark_job("wordcount", "balanced", records=120, shard_size=20, reducers=[2, 3], seed=5)

        report = result.to_html()

        self.assertIn("<!DOCTYPE html>", report)
        self.assertIn("<h1>Mini MapReduce benchmark report (wordcount: balanced)</h1>", report)
        self.assertIn("<strong>Dataset family</strong>", report)
        self.assertIn("<h2>Reducers = 2</h2>", report)
        self.assertIn("<th>r0</th><th>r1</th>", report)
        self.assertIn("Elapsed timing chart", report)
        self.assertIn("Reducer load chart", report)
        self.assertIn("Elapsed benchmark timing by reducer count", report)
        self.assertIn("Reducer load totals for 2 reducers", report)
        self.assertIn("<svg viewBox='0 0 680 240'", report)
        self.assertIn("<svg viewBox='0 0 680 220'", report)
        self.assertIn("rgba(37, 99, 235,", report)
        self.assertIn("Reducer load stddev", report)

    def test_benchmark_wordcount_rejects_non_positive_shard_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "shard_size must be positive"):
            benchmark_job("wordcount", "balanced", records=50, shard_size=0, reducers=[1, 2])

    def test_cli_writes_json_output_with_reducer_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            output = Path(tmpdir) / "result.json"
            source.write_text("alpha beta alpha\n", encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "wordcount",
                    str(source),
                    "--reducers",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["output"], {"alpha": 2, "beta": 1})
            self.assertEqual(payload["job"], "wordcount")
            self.assertEqual(payload["reducers"], 2)
            self.assertEqual(len(payload["reducer_stats"]), 2)

    def test_cli_runs_plugin_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            output = Path(tmpdir) / "plugin.json"
            source.write_text("Alice,4\nAlice,9\nBob,3\n", encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "plugin",
                    str(source),
                    "--plugin",
                    "projects/mini-mapreduce-lab/plugins_top_score.py",
                    "--reducers",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["job"], "plugin-max-score")
            self.assertEqual(payload["output"], {"alice": 9, "bob": 3})
            self.assertTrue(payload["plugin"].endswith("plugins_top_score.py"))

    def test_cli_runs_average_plugin_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            output = Path(tmpdir) / "avg-plugin.json"
            source.write_text("Alice,4\nAlice,10\nBob,3\nBob,9\n", encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "plugin",
                    str(source),
                    "--plugin",
                    "projects/mini-mapreduce-lab/plugins_average_score.py",
                    "--reducers",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["job"], "plugin-average-score")
            self.assertEqual(payload["output"], {"alice": 7.0, "bob": 6.0})

    def test_cli_runs_module_plugin_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            output = Path(tmpdir) / "module-plugin.json"
            package_dir = Path(tmpdir) / "demo_plugins"
            package_dir.mkdir()
            (package_dir / "__init__.py").write_text("", encoding="utf-8")
            (package_dir / "topscore.py").write_text(
                "JOB_NAME = 'module-max-score'\n"
                "def map_records(lines):\n"
                "    for line in lines:\n"
                "        if not line.strip():\n"
                "            continue\n"
                "        name, score = line.split(',')\n"
                "        yield name.strip().lower(), int(score)\n"
                "def combine_values(key, values):\n"
                "    return max(values)\n"
                "def reduce_key(key, values):\n"
                "    return max(values)\n",
                encoding="utf-8",
            )
            source.write_text("Alice,4\nAlice,9\nBob,3\n", encoding="utf-8")

            env = dict(**__import__('os').environ, PYTHONPATH=f"{tmpdir}:{__import__('os').environ.get('PYTHONPATH', '')}".rstrip(':'))
            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "plugin",
                    str(source),
                    "--plugin",
                    "demo_plugins.topscore",
                    "--reducers",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
                env=env,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["job"], "module-max-score")
            self.assertEqual(payload["output"], {"alice": 9, "bob": 3})
            self.assertTrue(payload["plugin"].endswith("topscore.py"))

    def test_cli_benchmark_outputs_json_with_timings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "benchmark.json"
            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
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
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["scenario"], "balanced")
            self.assertEqual(payload["job"], "wordcount")
            self.assertEqual(payload["reducers"], [1, 3])
            self.assertEqual(len(payload["timings_ms"]), 2)
            self.assertEqual(payload["timings_ms"][0]["reducers"], 1)

    def test_cli_benchmark_can_write_csv_heatmap_markdown_and_html_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "benchmark.json"
            csv_output = Path(tmpdir) / "benchmark.csv"
            heatmap_output = Path(tmpdir) / "benchmark-heatmap.csv"
            report_output = Path(tmpdir) / "benchmark-report.md"
            html_output = Path(tmpdir) / "benchmark-report.html"
            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
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
                    "--output",
                    str(output),
                    "--csv-output",
                    str(csv_output),
                    "--heatmap-output",
                    str(heatmap_output),
                    "--report-output",
                    str(report_output),
                    "--html-output",
                    str(html_output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            rows = csv_output.read_text(encoding="utf-8").strip().splitlines()
            heatmap_rows = heatmap_output.read_text(encoding="utf-8").strip().splitlines()
            report = report_output.read_text(encoding="utf-8")
            html_report = html_output.read_text(encoding="utf-8")
            self.assertEqual(payload["reducers"], [1, 3])
            self.assertEqual(rows[0], "job,plugin,scenario,dataset_family,seed,total_records,shard_size,reducers,elapsed_ms,shards,map_records,unique_keys,max_reducer_records,skew_ratio")
            self.assertEqual(len(rows), 3)
            self.assertEqual(heatmap_rows[0], "job,plugin,scenario,dataset_family,seed,reducers,shard_index,reducer,records,unique_keys")
            self.assertGreater(len(heatmap_rows), 3)
            self.assertIn(",1,", rows[1])
            self.assertIn(",3,", rows[2])
            self.assertIn("# Mini MapReduce benchmark report (wordcount: balanced)", report)
            self.assertIn("### Reducers = 3", report)
            self.assertIn("<!DOCTYPE html>", html_report)
            self.assertIn("<h2>Reducers = 3</h2>", html_report)

    def test_benchmark_plugin_reports_plugin_metadata_and_heatmap(self) -> None:
        result = benchmark_job(
            "plugin",
            "skewed",
            records=120,
            shard_size=20,
            reducers=[2, 4],
            seed=7,
            plugin_path=PROJECT_DIR / "plugins_top_score.py",
        )

        self.assertEqual(result.job, "plugin-max-score")
        self.assertTrue(result.plugin.endswith("plugins_top_score.py"))
        self.assertEqual(result.reducers, [2, 4])
        self.assertTrue(all(row["job"] == "plugin" for row in result.heatmap_rows))
        self.assertTrue(all(row["plugin"] for row in result.heatmap_rows))

    def test_plugin_benchmark_uses_plugin_defined_generator(self) -> None:
        result = benchmark_job(
            "plugin",
            "balanced",
            records=24,
            shard_size=6,
            reducers=[2],
            seed=11,
            plugin_path=PROJECT_DIR / "plugins_average_score.py",
        )

        self.assertEqual(result.job, "plugin-average-score")
        self.assertEqual(result.dataset_family, "default")
        self.assertEqual(result.unique_keys, 12)
        self.assertTrue(result.plugin.endswith("plugins_average_score.py"))
        self.assertEqual(result.timings_ms[0]["map_records"], 24)

    def test_plugin_benchmark_supports_named_dataset_families(self) -> None:
        result = benchmark_job(
            "plugin",
            "balanced",
            records=24,
            shard_size=6,
            reducers=[2],
            seed=11,
            plugin_path=PROJECT_DIR / "plugins_average_score.py",
            dataset_family="project-week",
        )

        self.assertEqual(result.dataset_family, "project-week")
        self.assertEqual(result.unique_keys, 8)
        self.assertEqual(result.timings_ms[0]["map_records"], 24)
        self.assertTrue(all(row["dataset_family"] == "project-week" for row in result.heatmap_rows))

    def test_plugin_benchmark_surfaces_available_dataset_families_in_artifacts(self) -> None:
        result = benchmark_job(
            "plugin",
            "balanced",
            records=24,
            shard_size=6,
            reducers=[2],
            seed=11,
            plugin_path=PROJECT_DIR / "plugins_average_score.py",
            dataset_family="project-week",
        )

        self.assertEqual(result.available_dataset_families, ["default", "exam-cram", "project-week"])
        payload = json.loads(result.to_json())
        self.assertEqual(payload["available_dataset_families"], ["default", "exam-cram", "project-week"])
        report = result.to_markdown()
        html_report = result.to_html()
        self.assertIn("- Available dataset families: `default, exam-cram, project-week`", report)
        self.assertIn("<strong>Available dataset families</strong>", html_report)
        self.assertIn("default, exam-cram, project-week", html_report)

    def test_plugin_benchmark_rejects_unsupported_declared_dataset_family(self) -> None:
        with self.assertRaisesRegex(ValueError, "supported: default, exam-cram, project-week"):
            benchmark_job(
                "plugin",
                "balanced",
                records=24,
                shard_size=6,
                reducers=[2],
                seed=11,
                plugin_path=PROJECT_DIR / "plugins_average_score.py",
                dataset_family="hackathon",
            )

    def test_plugin_benchmark_rejects_invalid_generator_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = Path(tmpdir) / "bad_generator.py"
            plugin.write_text(
                "JOB_NAME = 'bad-generator'\n"
                "def map_records(lines):\n"
                "    for line in lines:\n"
                "        if line.strip():\n"
                "            yield 'x', 1\n"
                "def reduce_key(key, values):\n"
                "    return sum(values)\n"
                "def benchmark_records(scenario, records, seed):\n"
                "    return ['only-once']\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "exactly records lines"):
                benchmark_job("plugin", "balanced", records=3, shard_size=1, reducers=[1], plugin_path=plugin)

    def test_cli_benchmark_runs_plugin_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "plugin-benchmark.json"
            csv_output = Path(tmpdir) / "plugin-benchmark.csv"
            subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "benchmark",
                    "--job",
                    "plugin",
                    "--plugin",
                    "projects/mini-mapreduce-lab/plugins_top_score.py",
                    "--scenario",
                    "balanced",
                    "--records",
                    "120",
                    "--shard-size",
                    "20",
                    "--reducers",
                    "2",
                    "4",
                    "--dataset-family",
                    "project-week",
                    "--output",
                    str(output),
                    "--csv-output",
                    str(csv_output),
                ],
                check=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            rows = csv_output.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(payload["job"], "plugin-max-score")
            self.assertEqual(payload["dataset_family"], "project-week")
            self.assertTrue(payload["plugin"].endswith("plugins_top_score.py"))
            self.assertEqual(payload["reducers"], [2, 4])
            self.assertEqual(rows[0], "job,plugin,scenario,dataset_family,seed,total_records,shard_size,reducers,elapsed_ms,shards,map_records,unique_keys,max_reducer_records,skew_ratio")
            self.assertTrue(rows[1].startswith("plugin-max-score,"))

    def test_cli_benchmark_rejects_unsupported_dataset_family_cleanly(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                "projects/mini-mapreduce-lab/mapreduce.py",
                "benchmark",
                "--job",
                "plugin",
                "--plugin",
                "projects/mini-mapreduce-lab/plugins_average_score.py",
                "--scenario",
                "balanced",
                "--dataset-family",
                "hackathon",
                "--records",
                "24",
                "--shard-size",
                "6",
                "--reducers",
                "2",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[2],
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unsupported dataset_family for plugin benchmark", completed.stderr)
        self.assertIn("supported: default, exam-cram, project-week", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_benchmark_requires_plugin_for_plugin_job(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                "projects/mini-mapreduce-lab/mapreduce.py",
                "benchmark",
                "--job",
                "plugin",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parents[2],
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--plugin is required for plugin benchmarks", completed.stderr)

    def test_cli_requires_group_field_for_json_group_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "events.jsonl"
            source.write_text('{"status":"ok"}\n', encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "json-group-count",
                    str(source),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--group-field is required", completed.stderr)

    def test_cli_requires_plugin_path_for_plugin_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "scores.csv"
            source.write_text("Alice,1\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "plugin",
                    str(source),
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--plugin is required", completed.stderr)

    def test_cli_rejects_non_positive_reducers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            source.write_text("alpha\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    "projects/mini-mapreduce-lab/mapreduce.py",
                    "run",
                    "wordcount",
                    str(source),
                    "--reducers",
                    "0",
                ],
                check=False,
                capture_output=True,
                text=True,
                cwd=Path(__file__).resolve().parents[2],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--reducers must be positive", completed.stderr)

    def test_programmatic_api_rejects_non_positive_reducers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "words.txt"
            source.write_text("alpha\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "reducers must be positive"):
                execute_job("wordcount", [source], shard_size=1, reducers=0)


if __name__ == "__main__":
    unittest.main()
