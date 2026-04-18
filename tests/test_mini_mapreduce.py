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
LATENCY_PLUGIN_PATH = PROJECT_DIR / "plugins_service_latency.py"
SESSION_PLUGIN_PATH = PROJECT_DIR / "plugins_sessionization.py"
STREAMING_PLUGIN_PATH = PROJECT_DIR / "plugins_streaming_window.py"
JOIN_PLUGIN_PATH = PROJECT_DIR / "plugins_rolling_window_join.py"
WATERMARK_PLUGIN_PATH = PROJECT_DIR / "plugins_watermark_late_summary.py"

spec = importlib.util.spec_from_file_location("mini_mapreduce_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

benchmark_job = module.benchmark_job
compare_plugin_release_snapshots = module.compare_plugin_release_snapshots
diff_plugin_inspections = module.diff_plugin_inspections
discover_mini_mapreduce_docs_index = module.discover_mini_mapreduce_docs_index
execute_job = module.execute_job
inspect_plugin = module.inspect_plugin
inspect_plugins = module.inspect_plugins
humanize_docs_slug = module.humanize_docs_slug
load_plugin = module.load_plugin
load_plugin_inspection_snapshot = module.load_plugin_inspection_snapshot
plugin_display_path = module.plugin_display_path
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

    def test_plugin_job_can_emit_latency_summary_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "latency.csv"
            source.write_text("auth-gateway,120\nauth-gateway,180\nprofile-read,72\n", encoding="utf-8")

            result = execute_job("plugin", [source], shard_size=2, reducers=2, plugin_path=LATENCY_PLUGIN_PATH)

            self.assertEqual(result.job, "plugin-service-latency")
            self.assertEqual(result.output["auth-gateway"], {"count": 2, "avg_ms": 150.0, "p95_ms": 180.0, "max_ms": 180.0})
            self.assertEqual(result.output["profile-read"]["count"], 1)
            self.assertTrue(str(result.plugin).endswith("plugins_service_latency.py"))

    def test_plugin_job_can_emit_sessionization_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "sessions.csv"
            source.write_text(
                "alice,2026-04-17T08:00:00Z,home\n"
                "alice,2026-04-17T08:12:00Z,quiz\n"
                "alice,2026-04-17T08:41:00Z,editor\n"
                "alice,2026-04-17T09:20:00Z,submit\n"
                "bob,2026-04-17T08:05:00Z,home\n"
                "bob,2026-04-17T08:55:00Z,forum\n",
                encoding="utf-8",
            )

            result = execute_job("plugin", [source], shard_size=2, reducers=2, plugin_path=SESSION_PLUGIN_PATH)

            self.assertEqual(result.job, "plugin-sessionization")
            self.assertEqual(
                result.output["alice"],
                {
                    "session_count": 2,
                    "total_events": 4,
                    "avg_events_per_session": 2.0,
                    "avg_session_minutes": 20.5,
                    "longest_session_events": 3,
                    "longest_session_minutes": 41.0,
                    "first_event_at": "2026-04-17T08:00:00Z",
                    "last_event_at": "2026-04-17T09:20:00Z",
                },
            )
            self.assertEqual(result.output["bob"]["session_count"], 2)
            self.assertTrue(str(result.plugin).endswith("plugins_sessionization.py"))

    def test_plugin_job_can_emit_streaming_window_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "stream.csv"
            source.write_text(
                "turnstile-east,2026-04-17T09:01:00Z,10\n"
                "turnstile-east,2026-04-17T09:03:00Z,16\n"
                "turnstile-east,2026-04-17T09:07:00Z,22\n"
                "turnstile-east,2026-04-17T09:09:00Z,28\n"
                "camera-lobby,2026-04-17T09:02:00Z,5\n",
                encoding="utf-8",
            )

            result = execute_job(
                "plugin",
                [source],
                shard_size=2,
                reducers=2,
                plugin_path=STREAMING_PLUGIN_PATH,
            )

            self.assertEqual(result.job, "plugin-streaming-window")
            self.assertEqual(result.output["turnstile-east@2026-04-17T09:00:00Z"]["avg_value"], 13.0)
            self.assertEqual(result.output["turnstile-east@2026-04-17T09:05:00Z"]["max_value"], 28.0)
            self.assertEqual(result.output["camera-lobby@2026-04-17T09:00:00Z"]["count"], 1)
            self.assertTrue(str(result.plugin).endswith("plugins_streaming_window.py"))

    def test_plugin_job_can_emit_rolling_window_join_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "joins.csv"
            source.write_text(
                "checkout-core,left,2026-04-17T09:00:00Z,cart-update\n"
                "checkout-core,right,2026-04-17T09:01:15Z,payment-auth\n"
                "checkout-core,left,2026-04-17T09:06:00Z,cart-update\n"
                "checkout-core,right,2026-04-17T09:07:00Z,payment-auth\n"
                "checkout-core,left,2026-04-17T09:08:30Z,cart-update-pending\n"
                "checkout-core,right,2026-04-17T09:15:30Z,payment-auth-orphan\n",
                encoding="utf-8",
            )

            result = execute_job(
                "plugin",
                [source],
                shard_size=2,
                reducers=2,
                plugin_path=JOIN_PLUGIN_PATH,
            )

            self.assertEqual(result.job, "plugin-rolling-window-join")
            self.assertEqual(result.output["checkout-core"]["matched_pairs"], 2)
            self.assertEqual(result.output["checkout-core"]["unmatched_left_events"], 1)
            self.assertEqual(result.output["checkout-core"]["unmatched_right_events"], 1)
            self.assertEqual(result.output["checkout-core"]["windows"][0]["sample_pair"]["right_label"], "payment-auth")
            self.assertTrue(str(result.plugin).endswith("plugins_rolling_window_join.py"))

    def test_plugin_job_can_emit_watermark_late_event_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "late-events.csv"
            source.write_text(
                "camera-lobby,2026-04-17T09:00:00Z,2026-04-17T09:00:00Z,10\n"
                "camera-lobby,2026-04-17T09:09:00Z,2026-04-17T09:09:00Z,20\n"
                "camera-lobby,2026-04-17T09:03:00Z,2026-04-17T09:10:00Z,15\n"
                "camera-lobby,2026-04-17T09:13:00Z,2026-04-17T09:13:00Z,25\n"
                "camera-lobby,2026-04-17T09:02:00Z,2026-04-17T09:14:00Z,12\n"
                "turnstile-east,2026-04-17T09:01:00Z,2026-04-17T09:01:00Z,5\n",
                encoding="utf-8",
            )

            result = execute_job(
                "plugin",
                [source],
                shard_size=2,
                reducers=2,
                plugin_path=WATERMARK_PLUGIN_PATH,
            )

            self.assertEqual(result.job, "plugin-watermark-late-summary")
            self.assertEqual(result.output["camera-lobby"]["late_events_seen"], 2)
            self.assertEqual(result.output["camera-lobby"]["late_accepted_events"], 1)
            self.assertEqual(result.output["camera-lobby"]["dropped_late_events"], 1)
            self.assertEqual(result.output["camera-lobby"]["hottest_window_start"], "2026-04-17T09:00:00Z")
            self.assertEqual(result.output["camera-lobby"]["windows"][0]["accepted_events"], 2)
            self.assertEqual(result.output["turnstile-east"]["accepted_events"], 1)
            self.assertTrue(str(result.plugin).endswith("plugins_watermark_late_summary.py"))

    def test_load_plugin_rejects_missing_mapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_plugin = Path(tmpdir) / "bad_plugin.py"
            bad_plugin.write_text("def reduce_key(key, values):\n    return sum(values)\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "map_records"):
                load_plugin(bad_plugin)

    def test_plugin_display_path_prefers_repo_relative_paths(self) -> None:
        self.assertEqual(
            plugin_display_path(str(PROJECT_DIR / "plugins_average_score.py")),
            "projects/mini-mapreduce-lab/plugins_average_score.py",
        )

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
        self.assertEqual(first.dataset_family, second.dataset_family)
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
            self.assertEqual(payload["plugin"], "projects/mini-mapreduce-lab/plugins_top_score.py")

    def test_cli_json_group_count_benchmark_writes_expected_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "json-benchmark.json"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--job",
                    "json-group-count",
                    "--scenario",
                    "skewed",
                    "--dataset-family",
                    "deployments",
                    "--group-field",
                    "status",
                    "--records",
                    "120",
                    "--shard-size",
                    "30",
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
            self.assertEqual(payload["job"], "json-group-count")
            self.assertEqual(payload["dataset_family"], "deployments")
            self.assertEqual(payload["available_dataset_families"], ["default", "incidents", "deployments"])
            self.assertEqual(payload["reducers"], [2, 4])
            self.assertTrue(payload["heatmap_rows"])

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
            self.assertEqual(heatmap_rows[0], "job,plugin,scenario,dataset_family,seed,reducers,shard_index,reducer,records,unique_keys")

    def test_plugin_benchmark_result_includes_plugin_metadata(self) -> None:
        result = benchmark_job("plugin", "balanced", records=90, shard_size=15, reducers=[2, 3], seed=99, plugin_path=PLUGIN_PATH)

        self.assertEqual(result.job, "plugin-max-score")
        self.assertEqual(result.plugin, "projects/mini-mapreduce-lab/plugins_top_score.py")
        self.assertTrue(result.heatmap_rows)
        self.assertTrue(all(row["plugin"] == "projects/mini-mapreduce-lab/plugins_top_score.py" for row in result.heatmap_rows))

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

    def test_json_group_count_benchmark_supports_dataset_families(self) -> None:
        result = benchmark_job(
            "json-group-count",
            "balanced",
            records=24,
            shard_size=6,
            reducers=[2, 4],
            seed=11,
            dataset_family="incidents",
            group_field="status",
        )

        self.assertEqual(result.job, "json-group-count")
        self.assertEqual(result.dataset_family, "incidents")
        self.assertEqual(result.available_dataset_families, ["default", "incidents", "deployments"])
        self.assertEqual(result.unique_keys, 4)
        self.assertTrue(all(row["dataset_family"] == "incidents" for row in result.heatmap_rows))

    def test_json_group_count_benchmark_rejects_unsupported_dataset_family(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported dataset_family for json-group-count benchmark"):
            benchmark_job(
                "json-group-count",
                "skewed",
                records=24,
                shard_size=6,
                reducers=[2],
                seed=11,
                dataset_family="unknown-family",
                group_field="status",
            )

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
        self.assertEqual(result.plugin_mapper, "plugins_average_score.map_records")
        self.assertEqual(result.plugin_reducer, "plugins_average_score.reduce_key")
        self.assertEqual(result.plugin_combiner, "plugins_average_score.combine_values")
        self.assertEqual(result.plugin_benchmark_generator, "plugins_average_score.benchmark_records")
        self.assertEqual(result.plugin_benchmark_note_hook, "plugins_average_score.benchmark_notes")
        payload = json.loads(result.to_json())
        self.assertEqual(payload["available_dataset_families"], ["default", "exam-cram", "project-week"])
        self.assertIn("Studio squad baseline", " ".join(payload["benchmark_notes"]))
        self.assertEqual(payload["benchmark_note_annotations"][0]["title"], "Studio squad baseline")
        self.assertEqual(payload["benchmark_note_annotations"][0]["severity"], "info")
        self.assertEqual(payload["plugin_mapper"], "plugins_average_score.map_records")
        self.assertEqual(payload["plugin_reducer"], "plugins_average_score.reduce_key")
        self.assertEqual(payload["plugin_combiner"], "plugins_average_score.combine_values")
        self.assertEqual(payload["plugin_benchmark_generator"], "plugins_average_score.benchmark_records")
        self.assertEqual(payload["plugin_benchmark_note_hook"], "plugins_average_score.benchmark_notes")
        csv_rows = result.to_csv().strip().splitlines()
        self.assertIn('"default,exam-cram,project-week",plugins_average_score.map_records,plugins_average_score.reduce_key,plugins_average_score.combine_values,plugins_average_score.benchmark_records,plugins_average_score.benchmark_notes', csv_rows[1])
        report = result.to_markdown()
        html_report = result.to_html()
        self.assertIn("- Available dataset families: `default, exam-cram, project-week`", report)
        self.assertIn("## Dataset notes", report)
        self.assertIn("## Structured benchmark annotations", report)
        self.assertIn("Studio squad baseline", report)
        self.assertIn("<strong>Available dataset families</strong>", html_report)
        self.assertIn("<h2>Dataset notes</h2>", html_report)
        self.assertIn("<h2>Structured benchmark annotations</h2>", html_report)
        self.assertIn("Studio squad baseline", html_report)
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

    def test_plugin_latency_benchmark_reports_incident_spike_metadata(self) -> None:
        result = benchmark_job(
            "plugin",
            "skewed",
            records=48,
            shard_size=12,
            reducers=[2],
            seed=11,
            plugin_path=LATENCY_PLUGIN_PATH,
            dataset_family="incident-spike",
        )

        self.assertEqual(result.job, "plugin-service-latency")
        self.assertEqual(result.available_dataset_families, ["default", "incident-spike", "batch-window"])
        self.assertEqual(result.plugin_mapper, "plugins_service_latency.map_records")
        self.assertEqual(result.plugin_benchmark_note_hook, "plugins_service_latency.benchmark_notes")
        self.assertEqual(result.benchmark_note_annotations[0]["title"], "Auth gateway timeout storm")
        self.assertEqual(result.benchmark_note_annotations[1]["title"], "Session cache spillover")
        self.assertIn("auth-gateway", result.benchmark_note_annotations[0]["hotspot_keys"])

    def test_plugin_sessionization_benchmark_reports_launch_day_metadata(self) -> None:
        result = benchmark_job(
            "plugin",
            "skewed",
            records=48,
            shard_size=12,
            reducers=[2],
            seed=11,
            plugin_path=SESSION_PLUGIN_PATH,
            dataset_family="launch-day",
        )

        self.assertEqual(result.job, "plugin-sessionization")
        self.assertEqual(result.available_dataset_families, ["default", "exam-revision", "launch-day"])
        self.assertEqual(result.plugin_mapper, "plugins_sessionization.map_records")
        self.assertEqual(result.plugin_benchmark_note_hook, "plugins_sessionization.benchmark_notes")
        self.assertEqual(result.benchmark_note_annotations[0]["title"], "Release lead war room")
        self.assertEqual(result.benchmark_note_annotations[1]["title"], "QA desk verification loop")
        self.assertIn("release-lead", result.benchmark_note_annotations[0]["hotspot_keys"])

    def test_plugin_streaming_window_benchmark_reports_iot_burst_metadata(self) -> None:
        result = benchmark_job(
            "plugin",
            "skewed",
            records=48,
            shard_size=12,
            reducers=[2],
            seed=11,
            plugin_path=STREAMING_PLUGIN_PATH,
            dataset_family="iot-burst",
        )

        self.assertEqual(result.job, "plugin-streaming-window")
        self.assertEqual(result.available_dataset_families, ["default", "iot-burst", "live-ops"])
        self.assertEqual(result.plugin_mapper, "plugins_streaming_window.map_records")
        self.assertEqual(result.plugin_benchmark_note_hook, "plugins_streaming_window.benchmark_notes")
        self.assertEqual(result.benchmark_note_annotations[0]["title"], "Turnstile rush-hour burst")
        self.assertEqual(result.benchmark_note_annotations[1]["title"], "Lobby camera spillover")
        self.assertIn("turnstile-east@2026-04-17T09:10:00Z", result.benchmark_note_annotations[0]["hotspot_keys"])

    def test_plugin_rolling_window_join_benchmark_reports_checkout_funnel_metadata(self) -> None:
        result = benchmark_job(
            "plugin",
            "skewed",
            records=48,
            shard_size=12,
            reducers=[2],
            seed=11,
            plugin_path=JOIN_PLUGIN_PATH,
            dataset_family="checkout-funnel",
        )

        self.assertEqual(result.job, "plugin-rolling-window-join")
        self.assertEqual(result.available_dataset_families, ["default", "checkout-funnel", "incident-correlation"])
        self.assertEqual(result.plugin_mapper, "plugins_rolling_window_join.map_records")
        self.assertEqual(result.plugin_benchmark_note_hook, "plugins_rolling_window_join.benchmark_notes")
        self.assertEqual(result.benchmark_note_annotations[0]["title"], "Checkout core backlog")
        self.assertEqual(result.benchmark_note_annotations[1]["title"], "Promo retry spillover")
        self.assertIn("checkout-core", result.benchmark_note_annotations[0]["hotspot_keys"])

    def test_plugin_watermark_benchmark_reports_sensor_backfill_metadata(self) -> None:
        result = benchmark_job(
            "plugin",
            "skewed",
            records=48,
            shard_size=12,
            reducers=[2],
            seed=11,
            plugin_path=WATERMARK_PLUGIN_PATH,
            dataset_family="sensor-backfill",
        )

        self.assertEqual(result.job, "plugin-watermark-late-summary")
        self.assertEqual(result.available_dataset_families, ["default", "sensor-backfill", "live-replay"])
        self.assertEqual(result.plugin_mapper, "plugins_watermark_late_summary.map_records")
        self.assertEqual(result.plugin_benchmark_note_hook, "plugins_watermark_late_summary.benchmark_notes")
        self.assertEqual(result.benchmark_note_annotations[0]["title"], "Meter east replay storm")
        self.assertEqual(result.benchmark_note_annotations[1]["title"], "Meter west secondary lag")
        self.assertIn("meter-east", result.benchmark_note_annotations[0]["hotspot_keys"])

    def test_plugin_benchmark_supports_plugin_defined_note_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = Path(tmpdir) / "custom_notes.py"
            plugin.write_text(
                "JOB_NAME = 'custom-notes'\n"
                "BENCHMARK_DATASET_FAMILIES = ['default', 'lab']\n"
                "def map_records(lines):\n"
                "    for line in lines:\n"
                "        key, value = line.strip().split(',')\n"
                "        yield key, int(value)\n"
                "def reduce_key(key, values):\n"
                "    return sum(values)\n"
                "def benchmark_records(scenario, records, seed, dataset_family='default'):\n"
                "    hot = 'office-hours' if dataset_family == 'lab' else 'recitation'\n"
                "    return [f\"{hot if index % 3 else 'quiz'},1\" for index in range(records)]\n"
                "def benchmark_notes(scenario, dataset_family, records, seed):\n"
                "    return [{'title': 'Lab hotspot', 'detail': f'{dataset_family}:{scenario}:{records}:{seed}: hotspot=office-hours', 'severity': 'watch', 'hotspot_keys': ['office-hours'], 'takeaway': 'Use the lab family to narrate queue buildup around office-hours.'}]\n",
                encoding="utf-8",
            )

            result = benchmark_job(
                "plugin",
                "skewed",
                records=9,
                shard_size=3,
                reducers=[1],
                seed=7,
                plugin_path=plugin,
                dataset_family="lab",
            )

            self.assertEqual(result.plugin_benchmark_note_hook, "custom_notes.benchmark_notes")
            self.assertIn("Lab hotspot: lab:skewed:9:7: hotspot=office-hours", result.benchmark_notes)
            self.assertEqual(result.benchmark_note_annotations[0]["hotspot_keys"], ["office-hours"])

    def test_plugin_benchmark_rejects_invalid_note_hook_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            plugin = Path(tmpdir) / "bad_notes.py"
            plugin.write_text(
                "JOB_NAME = 'bad-notes'\n"
                "def map_records(lines):\n"
                "    for line in lines:\n"
                "        if line.strip():\n"
                "            yield 'x', 1\n"
                "def reduce_key(key, values):\n"
                "    return sum(values)\n"
                "def benchmark_records(scenario, records, seed):\n"
                "    return ['x,1' for _ in range(records)]\n"
                "def benchmark_notes(scenario):\n"
                "    return 'not-a-list'\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "plugin benchmark_notes must return a list/tuple of non-empty strings or annotation objects"):
                benchmark_job("plugin", "balanced", records=3, shard_size=1, reducers=[1], seed=5, plugin_path=plugin)

    def test_plugin_inspection_can_render_csv(self) -> None:
        result = inspect_plugin(PROJECT_DIR / "plugins_average_score.py")
        self.assertEqual(result.plugin, "projects/mini-mapreduce-lab/plugins_average_score.py")

        csv_rows = result.to_csv().strip().splitlines()
        self.assertEqual(
            csv_rows[0],
            "name,plugin,plugin_repo_commit,module_doc_summary,mapper,mapper_signature,mapper_doc_summary,mapper_source_line,mapper_source_anchor,mapper_source_url,mapper_source_commit_url,reducer,reducer_signature,reducer_doc_summary,reducer_source_line,reducer_source_anchor,reducer_source_url,reducer_source_commit_url,combiner,combiner_signature,combiner_doc_summary,combiner_source_line,combiner_source_anchor,combiner_source_url,combiner_source_commit_url,benchmark_generator,benchmark_generator_signature,benchmark_generator_doc_summary,benchmark_generator_source_line,benchmark_generator_source_anchor,benchmark_generator_source_url,benchmark_generator_source_commit_url,benchmark_note_hook,benchmark_note_hook_signature,benchmark_note_hook_doc_summary,benchmark_note_hook_source_line,benchmark_note_hook_source_anchor,benchmark_note_hook_source_url,benchmark_note_hook_source_commit_url,available_dataset_families",
        )
        self.assertIn("plugin-average-score", csv_rows[1])
        self.assertIn("Average-score analytics plugin with synthetic cohort benchmark families.", csv_rows[1])
        self.assertIn("map_records(lines)", csv_rows[1])
        self.assertIn("Emit per-student sum/count records from comma-separated score lines.", csv_rows[1])
        self.assertRegex(csv_rows[1], r",\d+,")
        self.assertIn("plugins_average_score.py#L7-L13", csv_rows[1])
        expected_commit = subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            text=True,
        ).strip()
        self.assertIn("https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13", csv_rows[1])
        self.assertIn(
            f"https://github.com/NEUJEANS/cs-portfolio-projects/blob/{expected_commit}/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13",
            csv_rows[1],
        )
        self.assertIn('"default,exam-cram,project-week"', csv_rows[1])
        self.assertIn("plugins_average_score.benchmark_notes", csv_rows[1])

    def test_plugin_inspection_diffs_capture_contract_changes(self) -> None:
        diffs = diff_plugin_inspections([
            inspect_plugin(PROJECT_DIR / "plugins_average_score.py"),
            inspect_plugin(PROJECT_DIR / "plugins_top_score.py"),
        ])

        self.assertEqual(len(diffs), 1)
        self.assertIn("name", diffs[0].changed_fields)
        self.assertIn("available_dataset_families", diffs[0].changed_fields)
        self.assertIn("benchmark_note_hook", diffs[0].changed_fields)
        self.assertEqual(diffs[0].changes["benchmark_generator_doc_summary"]["current"], None)
        self.assertEqual(diffs[0].changes["benchmark_generator_source_line"]["current"], None)
        self.assertEqual(diffs[0].changes["benchmark_note_hook"]["current"], None)

    def test_inspect_plugins_can_include_diff_payload(self) -> None:
        batch = inspect_plugins(
            [PROJECT_DIR / "plugins_average_score.py", PROJECT_DIR / "plugins_top_score.py"],
            include_diffs=True,
        )

        payload = batch.as_dict()
        self.assertEqual(payload["plugin_count"], 2)
        self.assertEqual(len(payload["diffs"]), 1)
        self.assertIn("benchmark_generator", payload["diffs"][0]["changes"])
        self.assertIn("benchmark_note_hook", payload["diffs"][0]["changes"])
        self.assertNotIn("/home/user1_admin/", batch.to_json())
        self.assertNotIn("/home/user1_admin/", batch.to_csv())

        markdown = batch.to_markdown()
        html_output = batch.to_html()
        self.assertIn("## Adjacent diffs", markdown)
        self.assertIn("plugin-average-score", markdown)
        self.assertIn("Average-score analytics plugin", markdown)
        self.assertIn("map_records(lines)", markdown)
        self.assertIn("Emit per-student sum/count records from comma-separated score lines.", markdown)
        self.assertIn("line ", markdown)
        self.assertIn("Repository commit:", markdown)
        self.assertIn("GitHub source:", markdown)
        self.assertIn("GitHub source (commit pinned):", markdown)
        self.assertIn("https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13", markdown)
        self.assertIn("<h2>Diff 1:", html_output)
        self.assertIn("map_records(lines)", html_output)
        self.assertIn("Emit per-student sum/count records from comma-separated score lines.", html_output)
        self.assertIn("line ", html_output)
        self.assertIn("Repository commit:", html_output)
        self.assertIn("GitHub source:", html_output)
        self.assertIn("GitHub source (commit pinned):", html_output)
        self.assertIn("https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13", html_output)

    def test_cli_inspect_plugin_supports_csv_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_output = Path(tmpdir) / "plugin-inspection.json"
            csv_output = Path(tmpdir) / "plugin-inspection.csv"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "inspect-plugin",
                    "--plugin",
                    str(PROJECT_DIR / "plugins_average_score.py"),
                    "--output",
                    str(json_output),
                    "--csv-output",
                    str(csv_output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.stdout, "")
            payload = json.loads(json_output.read_text(encoding="utf-8"))
            csv_rows = csv_output.read_text(encoding="utf-8").strip().splitlines()
            expected_commit = subprocess.check_output(
                ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            self.assertEqual(payload["name"], "plugin-average-score")
            self.assertEqual(payload["plugin_repo_commit"], expected_commit)
            self.assertEqual(
                payload["mapper_source_url"],
                "https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13",
            )
            self.assertEqual(
                payload["mapper_source_commit_url"],
                f"https://github.com/NEUJEANS/cs-portfolio-projects/blob/{expected_commit}/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13",
            )
            self.assertEqual(payload["benchmark_note_hook"], "plugins_average_score.benchmark_notes")
            self.assertEqual(
                csv_rows[0],
                "name,plugin,plugin_repo_commit,module_doc_summary,mapper,mapper_signature,mapper_doc_summary,mapper_source_line,mapper_source_anchor,mapper_source_url,mapper_source_commit_url,reducer,reducer_signature,reducer_doc_summary,reducer_source_line,reducer_source_anchor,reducer_source_url,reducer_source_commit_url,combiner,combiner_signature,combiner_doc_summary,combiner_source_line,combiner_source_anchor,combiner_source_url,combiner_source_commit_url,benchmark_generator,benchmark_generator_signature,benchmark_generator_doc_summary,benchmark_generator_source_line,benchmark_generator_source_anchor,benchmark_generator_source_url,benchmark_generator_source_commit_url,benchmark_note_hook,benchmark_note_hook_signature,benchmark_note_hook_doc_summary,benchmark_note_hook_source_line,benchmark_note_hook_source_anchor,benchmark_note_hook_source_url,benchmark_note_hook_source_commit_url,available_dataset_families",
            )
            self.assertIn("plugin-average-score", csv_rows[1])
            self.assertIn('"default,exam-cram,project-week"', csv_rows[1])

    def test_cli_inspect_plugin_can_emit_diff_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "plugin-diff.json"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "inspect-plugin",
                    "--plugin",
                    str(PROJECT_DIR / "plugins_average_score.py"),
                    "--plugin",
                    str(PROJECT_DIR / "plugins_top_score.py"),
                    "--diff",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["plugin_count"], 2)
            self.assertEqual(len(payload["diffs"]), 1)
            self.assertIn("name", payload["diffs"][0]["changed_fields"])

    def test_cli_inspect_plugin_can_write_markdown_and_html_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_output = Path(tmpdir) / "plugin-diff-report.md"
            html_output = Path(tmpdir) / "plugin-diff-report.html"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "inspect-plugin",
                    "--plugin",
                    str(PROJECT_DIR / "plugins_average_score.py"),
                    "--plugin",
                    str(PROJECT_DIR / "plugins_top_score.py"),
                    "--diff",
                    "--report-output",
                    str(markdown_output),
                    "--html-output",
                    str(html_output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            markdown = markdown_output.read_text(encoding="utf-8")
            html_payload = html_output.read_text(encoding="utf-8")
            self.assertIn("## Adjacent diffs", markdown)
            self.assertIn("plugin-average-score", markdown)
            self.assertIn("<h2>Diff 1:", html_payload)

    def test_load_plugin_inspection_snapshot_and_compare_release_snapshots(self) -> None:
        before_average = inspect_plugin(PROJECT_DIR / "plugins_average_score.py").as_dict()
        removed_top = inspect_plugin(PROJECT_DIR / "plugins_top_score.py").as_dict()
        after_average = dict(before_average)
        after_average["available_dataset_families"] = ["default", "exam-cram", "project-week", "capstone"]
        after_average["benchmark_note_hook"] = None
        after_average["benchmark_note_hook_signature"] = None
        after_average["benchmark_note_hook_doc_summary"] = None
        added_latency = inspect_plugin(PROJECT_DIR / "plugins_service_latency.py").as_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            before_path = Path(tmpdir) / "before.json"
            after_path = Path(tmpdir) / "after.json"
            before_path.write_text(json.dumps({"plugins": [before_average, removed_top]}, indent=2), encoding="utf-8")
            after_path.write_text(json.dumps({"plugins": [after_average, added_latency]}, indent=2), encoding="utf-8")

            before_snapshot = load_plugin_inspection_snapshot(before_path)
            after_snapshot = load_plugin_inspection_snapshot(after_path)
            comparison = compare_plugin_release_snapshots(
                before_snapshot,
                after_snapshot,
                before_label="v1 plugin catalog",
                after_label="v2 plugin catalog",
            )

        payload = comparison.as_dict()
        self.assertEqual(payload["summary"], {"added": 1, "removed": 1, "changed": 1, "unchanged": 0})
        self.assertEqual(payload["added_plugins"][0]["name"], "plugin-service-latency")
        self.assertEqual(payload["removed_plugins"][0]["name"], "plugin-max-score")
        self.assertEqual(payload["changed_plugins"][0]["name"], "plugin-average-score")
        self.assertIn("available_dataset_families", payload["changed_plugins"][0]["changed_fields"])
        self.assertIn("Benchmark note hook", payload["changed_plugins"][0]["removed_hooks"])
        self.assertEqual(payload["changed_plugins"][0]["added_dataset_families"], ["capstone"])
        self.assertIn("v1 plugin catalog", comparison.to_markdown())
        self.assertIn("plugin-service-latency", comparison.to_html())

    def test_cli_compare_plugin_releases_writes_json_markdown_and_html(self) -> None:
        before_average = inspect_plugin(PROJECT_DIR / "plugins_average_score.py").as_dict()
        after_average = dict(before_average)
        after_average["available_dataset_families"] = ["default", "exam-cram", "project-week", "capstone"]
        added_latency = inspect_plugin(PROJECT_DIR / "plugins_service_latency.py").as_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            before_path = Path(tmpdir) / "before.json"
            after_path = Path(tmpdir) / "after.json"
            json_output = Path(tmpdir) / "release-comparison.json"
            markdown_output = Path(tmpdir) / "release-comparison.md"
            html_output = Path(tmpdir) / "release-comparison.html"
            before_path.write_text(json.dumps({"plugins": [before_average]}, indent=2), encoding="utf-8")
            after_path.write_text(json.dumps({"plugins": [after_average, added_latency]}, indent=2), encoding="utf-8")

            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "compare-plugin-releases",
                    "--before",
                    str(before_path),
                    "--after",
                    str(after_path),
                    "--before-label",
                    "2026-04-17 snapshot",
                    "--after-label",
                    "2026-04-18 snapshot",
                    "--output",
                    str(json_output),
                    "--report-output",
                    str(markdown_output),
                    "--html-output",
                    str(html_output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(json_output.read_text(encoding="utf-8"))
            markdown = markdown_output.read_text(encoding="utf-8")
            html_payload = html_output.read_text(encoding="utf-8")

        self.assertEqual(payload["summary"], {"added": 1, "removed": 0, "changed": 1, "unchanged": 0})
        self.assertEqual(payload["added_plugins"][0]["name"], "plugin-service-latency")
        self.assertEqual(payload["changed_plugins"][0]["added_dataset_families"], ["capstone"])
        self.assertIn("2026-04-17 snapshot", markdown)
        self.assertIn("release comparison", html_payload.lower())
        self.assertIn("plugin-service-latency", html_payload)

    def test_compare_plugin_releases_normalizes_absolute_plugin_paths(self) -> None:
        before_average = inspect_plugin(PROJECT_DIR / "plugins_average_score.py").as_dict()
        before_average["plugin"] = str((PROJECT_DIR / "plugins_average_score.py").resolve())
        after_average = inspect_plugin(PROJECT_DIR / "plugins_average_score.py").as_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            before_path = Path(tmpdir) / "before.json"
            after_path = Path(tmpdir) / "after.json"
            before_path.write_text(json.dumps({"plugins": [before_average]}, indent=2), encoding="utf-8")
            after_path.write_text(json.dumps({"plugins": [after_average]}, indent=2), encoding="utf-8")

            comparison = compare_plugin_release_snapshots(
                load_plugin_inspection_snapshot(before_path),
                load_plugin_inspection_snapshot(after_path),
                before_label="before",
                after_label="after",
            )

        self.assertEqual(comparison.as_dict()["summary"], {"added": 0, "removed": 0, "changed": 0, "unchanged": 1})
        self.assertEqual(comparison.unchanged_plugins, ["plugin-average-score"])

    def test_cli_catalog_plugins_can_generate_dedicated_plugin_docs_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_output = Path(tmpdir) / "plugin-catalog.md"
            html_output = Path(tmpdir) / "plugin-catalog.html"
            docs_dir = Path(tmpdir) / "plugin-pages"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "catalog-plugins",
                    "--root",
                    str(PROJECT_DIR),
                    "--report-output",
                    str(markdown_output),
                    "--html-output",
                    str(html_output),
                    "--docs-dir",
                    str(docs_dir),
                ],
                check=True,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.stdout, "")
            markdown = markdown_output.read_text(encoding="utf-8")
            html_payload = html_output.read_text(encoding="utf-8")
            plugin_markdown = (docs_dir / "plugin-average-score.md").read_text(encoding="utf-8")
            plugin_html = (docs_dir / "plugin-average-score.html").read_text(encoding="utf-8")
            self.assertIn("plugin-pages/plugin-average-score.md", markdown)
            self.assertIn('href="plugin-pages/plugin-average-score.html"', html_payload)
            self.assertIn("Plugin path: `projects/mini-mapreduce-lab/plugins_average_score.py`", plugin_markdown)
            self.assertIn("projects/mini-mapreduce-lab/plugins_average_score.py", plugin_html)
            self.assertIn("Catalog index: [plugin catalog](../plugin-catalog.md)", plugin_markdown)
            self.assertIn('href="../plugin-catalog.html"', plugin_html)
            self.assertIn("Hook source excerpts", plugin_markdown)
            self.assertIn("Hook source excerpts", plugin_html)


    def test_cli_docs_index_writes_markdown_and_html_landing_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_root = Path(tmpdir) / "artifacts"
            report_prefix = artifacts_root / "project-week-report"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "catalog-plugins",
                    "--root",
                    str(PROJECT_DIR),
                    "--output",
                    str(artifacts_root / "plugin-catalog.json"),
                    "--report-output",
                    str(artifacts_root / "plugin-catalog.md"),
                    "--html-output",
                    str(artifacts_root / "plugin-catalog.html"),
                    "--docs-dir",
                    str(artifacts_root / "plugin-pages"),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--job",
                    "plugin",
                    "--plugin",
                    str(PROJECT_DIR / "plugins_average_score.py"),
                    "--scenario",
                    "skewed",
                    "--dataset-family",
                    "project-week",
                    "--records",
                    "48",
                    "--shard-size",
                    "12",
                    "--reducers",
                    "2",
                    "4",
                    "--output",
                    str(report_prefix.with_name(report_prefix.name + "-benchmark.json")),
                    "--csv-output",
                    str(report_prefix.with_name(report_prefix.name + "-benchmark.csv")),
                    "--heatmap-output",
                    str(report_prefix.with_name(report_prefix.name + "-heatmap.csv")),
                    "--report-output",
                    str(report_prefix.with_name(report_prefix.name + "-report.md")),
                    "--html-output",
                    str(report_prefix.with_name(report_prefix.name + "-report.html")),
                    "--annotation-batch-dir",
                    str(artifacts_root),
                    "--annotation-batch-prefix",
                    "project-week-batch",
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )
            before_snapshot = artifacts_root / "2026-04-17-plugin-catalog.json"
            before_snapshot.write_text(
                json.dumps(
                    {
                        "plugins": [
                            inspect_plugin(PROJECT_DIR / "plugins_average_score.py").as_dict(),
                            inspect_plugin(PROJECT_DIR / "plugins_top_score.py").as_dict(),
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "compare-plugin-releases",
                    "--before",
                    str(before_snapshot),
                    "--after",
                    str(artifacts_root / "plugin-catalog.json"),
                    "--before-label",
                    "2026-04-17 plugin snapshot",
                    "--after-label",
                    "current plugin catalog",
                    "--output",
                    str(artifacts_root / "2026-04-17-vs-current-release-comparison.json"),
                    "--report-output",
                    str(artifacts_root / "2026-04-17-vs-current-release-comparison.md"),
                    "--html-output",
                    str(artifacts_root / "2026-04-17-vs-current-release-comparison.html"),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            markdown_output = artifacts_root / "index.md"
            html_output = artifacts_root / "index.html"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "docs-index",
                    "--artifacts-root",
                    str(artifacts_root),
                    "--output",
                    str(markdown_output),
                    "--html-output",
                    str(html_output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            markdown = markdown_output.read_text(encoding="utf-8")
            html_payload = html_output.read_text(encoding="utf-8")
            self.assertIn("# Mini MapReduce docs index", markdown)
            self.assertIn("plugin-pages/plugin-average-score.html", markdown)
            self.assertIn("2026-04-17-vs-current-release-comparison.html", markdown)
            self.assertIn("project-week-report-report.html", markdown)
            self.assertIn("project-week-batch-full.html", markdown)
            self.assertIn("Mini MapReduce docs index", html_payload)
            self.assertIn("plugin-catalog.html", html_payload)
            self.assertIn("2026-04-17-vs-current-release-comparison.html", html_payload)
            self.assertIn("project-week-batch-portfolio-tight.html", html_payload)

    def test_cli_inspect_plugin_rejects_diff_with_single_plugin(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "inspect-plugin",
                "--plugin",
                str(PROJECT_DIR / "plugins_average_score.py"),
                "--diff",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("--diff requires at least two --plugin values", completed.stderr)

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
                    "--dataset-family",
                    "project-week",
                    "--output",
                    str(output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["job"], "plugin-max-score")
            self.assertEqual(payload["dataset_family"], "project-week")
            self.assertEqual(payload["plugin"], "projects/mini-mapreduce-lab/plugins_top_score.py")
            self.assertEqual(payload["reducers"], [2, 4])

    def test_cli_plugin_benchmark_can_filter_and_summarize_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "plugin-annotation-benchmark.json"
            report_output = Path(tmpdir) / "plugin-annotation-benchmark.md"
            subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--job",
                    "plugin",
                    "--plugin",
                    str(PROJECT_DIR / "plugins_average_score.py"),
                    "--scenario",
                    "skewed",
                    "--dataset-family",
                    "project-week",
                    "--records",
                    "48",
                    "--shard-size",
                    "12",
                    "--reducers",
                    "2",
                    "--annotation-severity",
                    "risk",
                    "watch",
                    "--annotation-limit",
                    "1",
                    "--annotation-overflow",
                    "summary",
                    "--output",
                    str(output),
                    "--report-output",
                    str(report_output),
                ],
                check=True,
                cwd=PROJECT_ROOT,
            )

            payload = json.loads(output.read_text(encoding="utf-8"))
            report = report_output.read_text(encoding="utf-8")
            self.assertEqual(payload["annotation_view"]["severity_filter"], ["risk", "watch"])
            self.assertEqual(payload["annotation_view"]["hidden_by_severity"], 1)
            self.assertEqual(payload["annotation_view"]["hidden_by_limit"], 1)
            self.assertTrue(payload["annotation_view"]["overflow_summary_emitted"])
            self.assertEqual(payload["benchmark_note_annotations"][1]["title"], "Collapsed reviewer callouts")
            self.assertIn("### Annotation view", report)
            self.assertIn("Collapsed reviewer callouts", report)

    def test_cli_benchmark_can_emit_annotation_batch_presets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            batch_dir = Path(tmpdir) / "batch"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    "--job",
                    "plugin",
                    "--plugin",
                    str(PROJECT_DIR / "plugins_average_score.py"),
                    "--scenario",
                    "skewed",
                    "--dataset-family",
                    "project-week",
                    "--records",
                    "48",
                    "--shard-size",
                    "12",
                    "--reducers",
                    "2",
                    "4",
                    "--annotation-batch-dir",
                    str(batch_dir),
                    "--annotation-batch-prefix",
                    "project-week-batch",
                ],
                check=True,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.stdout, "")
            manifest = json.loads((batch_dir / "project-week-batch-manifest.json").read_text(encoding="utf-8"))
            full_payload = json.loads((batch_dir / "project-week-batch-full.json").read_text(encoding="utf-8"))
            tight_payload = json.loads((batch_dir / "project-week-batch-portfolio-tight.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["output_dir"], ".")
            self.assertEqual(manifest["shared_artifacts"]["csv"], "project-week-batch-shared.csv")
            self.assertEqual(manifest["shared_artifacts"]["heatmap_csv"], "project-week-batch-shared-heatmap.csv")
            self.assertEqual([preset["name"] for preset in manifest["presets"]], ["full", "portfolio-tight"])
            self.assertEqual(full_payload["timings_ms"], tight_payload["timings_ms"])
            self.assertEqual(full_payload["heatmap_rows"], tight_payload["heatmap_rows"])
            self.assertEqual(len(full_payload["benchmark_note_annotations"]), 3)
            self.assertNotIn("annotation_view", full_payload)
            self.assertEqual(tight_payload["annotation_view"]["severity_filter"], ["risk", "watch"])
            self.assertEqual(tight_payload["annotation_view"]["hidden_by_severity"], 1)
            self.assertEqual(tight_payload["annotation_view"]["hidden_by_limit"], 1)
            self.assertTrue((batch_dir / "project-week-batch-full.md").exists())
            self.assertTrue((batch_dir / "project-week-batch-portfolio-tight.html").exists())

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
            cwd=PROJECT_ROOT,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unsupported dataset_family for plugin benchmark", completed.stderr)
        self.assertIn("supported: default, exam-cram, project-week", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

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
