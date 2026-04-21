from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "projects/robin-hood-hashing-lab/robin_hood_hashing_lab.py"
SAMPLE_INPUT = REPO_ROOT / "projects/robin-hood-hashing-lab/sample_pairs.txt"
SPEC = importlib.util.spec_from_file_location("robin_hood_hashing_lab", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
BenchmarkRow = MODULE.BenchmarkRow
InputDataError = MODULE.InputDataError
LinearProbingHashTable = MODULE.LinearProbingHashTable
RobinHoodHashTable = MODULE.RobinHoodHashTable
SnapshotError = MODULE.SnapshotError
load_snapshot = MODULE.load_snapshot
benchmark_delete_count = MODULE.benchmark_delete_count
parse_load_factors = MODULE.parse_load_factors
parse_pairs_input = MODULE.parse_pairs_input
parse_strategies = MODULE.parse_strategies
parse_workloads = MODULE.parse_workloads
save_benchmark = MODULE.save_benchmark
stable_hash = MODULE.stable_hash
summarize_benchmark = MODULE.summarize_benchmark
run_benchmark = MODULE.run_benchmark


def keys_for_home(capacity: int, home_slot: int, count: int) -> list[str]:
    matches: list[str] = []
    candidate = 0
    while len(matches) < count:
        key = f"home:{capacity}:{home_slot}:{candidate}"
        if stable_hash(key) % capacity == home_slot:
            matches.append(key)
        candidate += 1
    return matches


class RobinHoodHashingLabTests(unittest.TestCase):
    def test_insert_lookup_update_and_resize(self) -> None:
        table = RobinHoodHashTable(capacity=5, max_load_factor=0.6, auto_resize=True)
        inserted = []
        for index in range(4):
            result = table.put(f"key-{index}", f"value-{index}")
            inserted.append(result.action)

        self.assertEqual(inserted.count("inserted"), 4)
        self.assertGreater(table.capacity, 5)
        self.assertEqual(table.get("key-3"), "value-3")
        self.assertEqual(table.put("key-1", "updated").action, "updated")
        self.assertEqual(table.get("key-1"), "updated")

    def test_robin_hood_swap_promotes_longer_probe_chain(self) -> None:
        table = RobinHoodHashTable(capacity=7, auto_resize=False)
        home_zero_a, home_zero_b = keys_for_home(7, 0, 2)
        home_one = keys_for_home(7, 1, 1)[0]

        table.put(home_zero_a, "a")
        table.put(home_one, "b")
        result = table.put(home_zero_b, "c")

        self.assertGreater(result.swaps, 0)
        slot_one = table.slots[1]
        slot_two = table.slots[2]
        assert slot_one is not None and slot_two is not None
        self.assertEqual(slot_one.key, home_zero_b)
        self.assertEqual(slot_one.probe_distance, 1)
        self.assertEqual(slot_two.key, home_one)
        self.assertEqual(slot_two.probe_distance, 1)

    def test_backward_shift_deletion_keeps_cluster_searchable(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        keys = keys_for_home(11, 3, 4)
        for index, key in enumerate(keys):
            table.put(key, f"value-{index}")

        self.assertTrue(table.delete(keys[1]))
        self.assertIsNone(table.get(keys[1]))
        self.assertEqual(table.get(keys[2]), "value-2")
        self.assertEqual(table.get(keys[3]), "value-3")

        stats = table.stats()
        self.assertEqual(stats["size"], 3)
        self.assertEqual(stats["max_probe_distance"], 2)

    def test_linear_probing_tracks_probe_distance_dispersion(self) -> None:
        table = LinearProbingHashTable(capacity=11, auto_resize=False)
        for index, key in enumerate(keys_for_home(11, 4, 4)):
            table.put(key, f"value-{index}")

        stats = table.stats()
        self.assertEqual(stats["max_probe_distance"], 3)
        self.assertGreater(stats["probe_distance_stddev"], 0)
        self.assertEqual(stats["cluster_lengths"], [4])
        self.assertEqual(stats["probe_distance_histogram"], {0: 1, 1: 1, 2: 1, 3: 1})

    def test_linear_probing_delete_keeps_later_wrapped_keys_searchable(self) -> None:
        table = LinearProbingHashTable(capacity=17, auto_resize=False)
        home_eleven = keys_for_home(17, 11, 3)
        home_thirteen = keys_for_home(17, 13, 1)[0]

        table.put(home_eleven[0], "a")
        table.put(home_eleven[1], "b")
        table.put(home_thirteen, "c")
        table.put(home_eleven[2], "d")

        self.assertTrue(table.delete(home_eleven[1]))
        self.assertEqual(table.get(home_eleven[2]), "d")
        slot_twelve = table.slots[12]
        assert slot_twelve is not None
        self.assertEqual(slot_twelve.key, home_eleven[2])
        self.assertEqual(slot_twelve.probe_distance, 1)

    def test_snapshot_round_trip_preserves_entries(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        for index, key in enumerate(keys_for_home(11, 5, 3)):
            table.put(key, f"value-{index}")

        restored = RobinHoodHashTable.from_snapshot(table.to_snapshot())
        self.assertEqual(restored.to_snapshot(), table.to_snapshot())

    def test_snapshot_loader_rejects_gap_inside_probe_sequence(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        keys = keys_for_home(11, 6, 3)
        for index, key in enumerate(keys):
            table.put(key, f"value-{index}")

        payload = table.to_snapshot()
        payload["slots"][(stable_hash(keys[2]) % 11) + 1] = None
        with self.assertRaises(SnapshotError):
            RobinHoodHashTable.from_snapshot(payload)

    def test_snapshot_loader_rejects_non_string_payload_values(self) -> None:
        table = RobinHoodHashTable(capacity=11, auto_resize=False)
        table.put("alpha", "1")
        payload = table.to_snapshot()
        for slot in payload["slots"]:
            if slot is not None:
                slot["value"] = 123
                break
        with self.assertRaises(SnapshotError):
            RobinHoodHashTable.from_snapshot(payload)

    def test_parse_pairs_input_supports_comments_and_both_separators(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "pairs.txt"
            path.write_text("# note\nalpha,1\nbeta=2\n", encoding="utf-8")
            self.assertEqual(parse_pairs_input(path), [("alpha", "1"), ("beta", "2")])

    def test_parse_load_factors_rejects_invalid_values(self) -> None:
        with self.assertRaises(InputDataError):
            parse_load_factors("0,1.2")

    def test_parse_strategies_normalizes_aliases(self) -> None:
        self.assertEqual(parse_strategies("robin_hood, linear"), ["robin-hood", "linear-probing"])
        with self.assertRaises(InputDataError):
            parse_strategies("quadratic")

    def test_parse_workloads_normalizes_aliases(self) -> None:
        self.assertEqual(parse_workloads("fill, deleteheavy"), ["fill-only", "delete-heavy"])
        with self.assertRaises(InputDataError):
            parse_workloads("random-mix")

    def test_benchmark_delete_count_keeps_at_least_one_survivor(self) -> None:
        self.assertEqual(benchmark_delete_count(3, 0.8), 2)
        with self.assertRaises(InputDataError):
            benchmark_delete_count(1, 0.3)

    def test_benchmark_summary_includes_linear_comparison_takeaways(self) -> None:
        rows = run_benchmark(
            capacity=31,
            load_factors=[0.5],
            trials=2,
            seed=17,
            strategies=["robin-hood", "linear-probing"],
            workloads=["fill-only", "delete-heavy"],
            delete_fraction=0.3,
        )
        summary = summarize_benchmark(
            rows,
            capacity=31,
            strategies=["robin-hood", "linear-probing"],
            workloads=["fill-only", "delete-heavy"],
            trials=2,
            title="Test benchmark",
            delete_fraction=0.3,
        )
        self.assertEqual(len(summary["comparisons"]), 2)
        self.assertEqual({row["workload"] for row in summary["comparisons"]}, {"fill-only", "delete-heavy"})
        strategies = {row["strategy"] for row in summary["results"]}
        workloads = {row["workload"] for row in summary["results"]}
        self.assertEqual(strategies, {"robin-hood", "linear-probing"})
        self.assertEqual(workloads, {"fill-only", "delete-heavy"})
        delete_heavy = [row for row in summary["results"] if row["workload"] == "delete-heavy"]
        self.assertTrue(all(row["deleted_entry_count"] > 0 for row in delete_heavy))
        self.assertTrue(all(row["average_delete_probes"] > 0 for row in delete_heavy))
        self.assertTrue(all(row["probe_distance_histogram"] for row in summary["results"]))
        self.assertTrue(all(row["average_unsuccessful_lookup_probes"] > 0 for row in summary["results"]))
        self.assertTrue(all(row["unsuccessful_lookup_probe_histogram"] for row in summary["results"]))
        self.assertTrue(all("miss_winner" in row for row in summary["comparisons"]))

    def test_benchmark_summary_uses_pooled_histogram_stddev(self) -> None:
        rows = [
            BenchmarkRow(
                strategy="robin-hood",
                workload="fill-only",
                trial=1,
                load_factor=0.5,
                effective_load_factor=0.2857,
                entry_count=2,
                remaining_entry_count=2,
                deleted_entry_count=0,
                average_insert_probes=1.0,
                average_delete_probes=0.0,
                average_successful_lookup_probes=1.0,
                average_unsuccessful_lookup_probes=2.0,
                average_probe_distance=1.0,
                probe_distance_stddev=1.0,
                max_probe_distance=2,
                max_cluster_length=2,
                swap_count=0,
                probe_distance_histogram={0: 1, 2: 1},
                unsuccessful_lookup_probe_histogram={1: 1, 3: 1},
            ),
            BenchmarkRow(
                strategy="robin-hood",
                workload="fill-only",
                trial=2,
                load_factor=0.5,
                effective_load_factor=0.2857,
                entry_count=2,
                remaining_entry_count=2,
                deleted_entry_count=0,
                average_insert_probes=1.0,
                average_delete_probes=0.0,
                average_successful_lookup_probes=1.0,
                average_unsuccessful_lookup_probes=3.0,
                average_probe_distance=2.0,
                probe_distance_stddev=2.0,
                max_probe_distance=4,
                max_cluster_length=2,
                swap_count=0,
                probe_distance_histogram={0: 1, 4: 1},
                unsuccessful_lookup_probe_histogram={2: 1, 4: 1},
            ),
        ]
        summary = summarize_benchmark(
            rows,
            capacity=7,
            strategies=["robin-hood"],
            workloads=["fill-only"],
            trials=2,
            title="Robin Hood hashing benchmark summary",
            delete_fraction=0.3,
        )
        result = summary["results"][0]
        self.assertEqual(result["average_probe_distance"], 1.5)
        self.assertEqual(result["probe_distance_stddev"], 1.6583)
        self.assertEqual(result["probe_distance_histogram"][2]["distance"], 4)
        self.assertEqual(result["probe_distance_histogram"][2]["share"], 0.25)
        self.assertEqual(result["average_unsuccessful_lookup_probes"], 2.5)
        self.assertEqual(result["unsuccessful_lookup_probe_stddev"], 1.118)
        self.assertEqual(result["unsuccessful_lookup_probe_histogram"][3]["probes"], 4)
        self.assertEqual(result["unsuccessful_lookup_probe_histogram"][3]["share"], 0.25)

    def test_save_benchmark_csv_preserves_numeric_histogram_key_order(self) -> None:
        row = BenchmarkRow(
            strategy="robin-hood",
            workload="fill-only",
            trial=1,
            load_factor=0.5,
            effective_load_factor=0.5,
            entry_count=3,
            remaining_entry_count=3,
            deleted_entry_count=0,
            average_insert_probes=1.0,
            average_delete_probes=0.0,
            average_successful_lookup_probes=1.0,
            average_unsuccessful_lookup_probes=3.0,
            average_probe_distance=4.0,
            probe_distance_stddev=0.0,
            max_probe_distance=10,
            max_cluster_length=3,
            swap_count=0,
            probe_distance_histogram={0: 1, 2: 1, 10: 1},
            unsuccessful_lookup_probe_histogram={1: 1, 2: 1, 11: 1},
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "benchmark.csv"
            save_benchmark([row], path, capacity=31)
            text = path.read_text(encoding="utf-8")
        csv_row = next(csv.DictReader(text.splitlines()))
        histogram_cell = csv_row["probe_distance_histogram"]
        self.assertEqual(histogram_cell, '{"0": 1, "2": 1, "10": 1}')
        self.assertNotEqual(histogram_cell, '{"0": 1, "10": 1, "2": 1}')
        miss_histogram_cell = csv_row["unsuccessful_lookup_probe_histogram"]
        self.assertEqual(miss_histogram_cell, '{"1": 1, "2": 1, "11": 1}')
        self.assertNotEqual(miss_histogram_cell, '{"1": 1, "11": 1, "2": 1}')

    def test_cli_build_stats_export_remove_and_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot_path = tmp_path / "table.json"
            updated_snapshot_path = tmp_path / "table-updated.json"
            export_path = tmp_path / "table.csv"
            benchmark_path = tmp_path / "benchmark.csv"
            benchmark_json_path = tmp_path / "benchmark.json"
            benchmark_markdown_path = tmp_path / "benchmark.md"
            benchmark_html_path = tmp_path / "benchmark.html"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "build",
                    "--input",
                    str(SAMPLE_INPUT),
                    "--output",
                    str(snapshot_path),
                    "--capacity",
                    "11",
                    "--pretty",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            stats = subprocess.run(
                [sys.executable, str(SCRIPT), "stats", "--snapshot", str(snapshot_path), "--pretty"],
                check=True,
                capture_output=True,
                text=True,
            )
            stats_payload = json.loads(stats.stdout)
            self.assertEqual(stats_payload["size"], 5)
            self.assertIn("probe_distance_stddev", stats_payload)
            self.assertIn("probe_distance_histogram", stats_payload)

            subprocess.run(
                [sys.executable, str(SCRIPT), "export", "--snapshot", str(snapshot_path), "--output", str(export_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            with export_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(rows[0], ["key", "value"])
            self.assertEqual(len(rows), 6)

            removal = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "remove",
                    "--snapshot",
                    str(snapshot_path),
                    "--output",
                    str(updated_snapshot_path),
                    "user:1002",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            removal_payload = json.loads(removal.stdout)
            self.assertTrue(removal_payload["removed"])
            updated_table = load_snapshot(updated_snapshot_path)
            self.assertIsNone(updated_table.get("user:1002"))

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--capacity",
                    "31",
                    "--load-factors",
                    "0.25,0.5",
                    "--trials",
                    "2",
                    "--seed",
                    "17",
                    "--strategies",
                    "robin-hood,linear",
                    "--markdown-out",
                    str(benchmark_markdown_path),
                    "--html-out",
                    str(benchmark_html_path),
                    "--output",
                    str(benchmark_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            with benchmark_path.open("r", encoding="utf-8", newline="") as handle:
                benchmark_rows = list(csv.DictReader(handle))
            self.assertEqual(len(benchmark_rows), 16)
            self.assertEqual({row["load_factor"] for row in benchmark_rows}, {"0.25", "0.5"})
            self.assertEqual({row["strategy"] for row in benchmark_rows}, {"robin-hood", "linear-probing"})
            self.assertEqual({row["workload"] for row in benchmark_rows}, {"fill-only", "delete-heavy"})
            delete_heavy_rows = [row for row in benchmark_rows if row["workload"] == "delete-heavy"]
            self.assertTrue(all(float(row["average_delete_probes"]) > 0 for row in delete_heavy_rows))
            self.assertTrue(all(row["probe_distance_histogram"] for row in benchmark_rows))
            self.assertTrue(all(float(row["average_unsuccessful_lookup_probes"]) > 0 for row in benchmark_rows))
            self.assertTrue(all(row["unsuccessful_lookup_probe_histogram"] for row in benchmark_rows))
            self.assertTrue(benchmark_markdown_path.exists())
            markdown = benchmark_markdown_path.read_text(encoding="utf-8")
            self.assertIn("Headline comparisons", markdown)
            self.assertIn("Delete-heavy (30.0% removals)", markdown)
            self.assertIn("Probe-distance histograms", markdown)
            self.assertIn("Unsuccessful-lookup histograms", markdown)
            self.assertTrue(benchmark_html_path.exists())
            html = benchmark_html_path.read_text(encoding="utf-8")
            self.assertIn("Robin Hood hashing benchmark comparison with delete-heavy workloads", html)
            self.assertIn("Per-workload winners and deltas against the linear-probing baseline for both successful and unsuccessful lookups.", html)
            self.assertIn("Probe-distance histogram · Delete-heavy (30.0% removals) · requested load factor 0.25", html)
            self.assertIn("Unsuccessful-lookup histogram · Delete-heavy (30.0% removals) · requested load factor 0.25", html)

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--capacity",
                    "31",
                    "--load-factors",
                    "0.25",
                    "--trials",
                    "1",
                    "--seed",
                    "17",
                    "--output",
                    str(benchmark_json_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            benchmark_json = json.loads(benchmark_json_path.read_text(encoding="utf-8"))
            self.assertEqual(len(benchmark_json), 4)
            self.assertEqual({row["strategy"] for row in benchmark_json}, {"robin-hood", "linear-probing"})
            self.assertEqual({row["workload"] for row in benchmark_json}, {"fill-only", "delete-heavy"})
            self.assertTrue(all(row["capacity"] == 31 for row in benchmark_json))
            self.assertTrue(all("probe_distance_histogram" in row for row in benchmark_json))
            self.assertTrue(all("unsuccessful_lookup_probe_histogram" in row for row in benchmark_json))

    def test_single_strategy_reports_use_single_strategy_default_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            benchmark_json_path = tmp_path / "benchmark.json"
            benchmark_markdown_path = tmp_path / "benchmark.md"
            benchmark_html_path = tmp_path / "benchmark.html"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--capacity",
                    "31",
                    "--load-factors",
                    "0.5",
                    "--trials",
                    "1",
                    "--seed",
                    "17",
                    "--strategies",
                    "robin-hood",
                    "--markdown-out",
                    str(benchmark_markdown_path),
                    "--html-out",
                    str(benchmark_html_path),
                    "--output",
                    str(benchmark_json_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            markdown = benchmark_markdown_path.read_text(encoding="utf-8")
            self.assertTrue(markdown.startswith("# Robin Hood hashing fill vs delete-heavy benchmark summary"))
            self.assertIn("Deterministic benchmark report for Robin Hood hashing", markdown)
            self.assertIn("delete-heavy workload that removes 30.0% of keys", markdown)
            self.assertIn("unsuccessful-lookup histograms", markdown)
            self.assertNotIn("against a linear-probing baseline", markdown)

            html = benchmark_html_path.read_text(encoding="utf-8")
            self.assertIn("<title>Robin Hood hashing fill vs delete-heavy benchmark summary</title>", html)
            self.assertIn("Deterministic benchmark report for Robin Hood hashing", html)
            self.assertIn("delete-heavy workload that removes 30.0% of keys", html)
            self.assertIn("Unsuccessful lookup probe histograms", html)
            self.assertNotIn("against a linear-probing baseline", html)


if __name__ == "__main__":
    unittest.main()
