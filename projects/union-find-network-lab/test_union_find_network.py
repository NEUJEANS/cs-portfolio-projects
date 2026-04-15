import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("union_find_network.py")
sys.path.insert(0, str(MODULE_PATH.parent))

from union_find_network import (  # noqa: E402
    UnionFindNetwork,
    load_edges_from_csv,
    parse_benchmark_series,
    run_benchmark,
    run_benchmark_series,
    run_csv_import,
    write_benchmark_series_csv,
    write_json_report,
)


class UnionFindNetworkTests(unittest.TestCase):
    def test_union_and_connected_components(self):
        network = UnionFindNetwork()
        network.union("a", "b")
        network.union("b", "c")
        self.assertTrue(network.connected("a", "c"))
        self.assertFalse(network.connected("a", "z"))
        summary = network.component_summary("b")
        self.assertEqual(summary["size"], 3)
        self.assertEqual(summary["edges"], 2)
        self.assertFalse(summary["has_cycle"])

    def test_cycle_detection_counts_extra_edges(self):
        network = UnionFindNetwork()
        first = network.union("svc-a", "svc-b")
        second = network.union("svc-b", "svc-c")
        third = network.union("svc-a", "svc-c")
        self.assertTrue(first.merged)
        self.assertTrue(second.merged)
        self.assertFalse(third.merged)
        self.assertTrue(third.created_cycle)
        summary = network.component_summary("svc-a")
        self.assertTrue(summary["has_cycle"])
        self.assertEqual(summary["edges"], 3)

    def test_stats_and_component_sorting(self):
        network = UnionFindNetwork()
        for left, right in [("1", "2"), ("2", "3"), ("x", "y")]:
            network.union(left, right)
        stats = network.stats()
        self.assertEqual(stats["nodes"], 5)
        self.assertEqual(stats["components"], 2)
        self.assertEqual(stats["largest_component"], 3)
        components = network.components()
        self.assertEqual(components[0]["size"], 3)
        self.assertEqual(components[1]["size"], 2)

    def test_script_runner_and_cli_json_output(self):
        operations = [
            {"op": "union", "args": ["api", "worker"]},
            {"op": "union", "args": ["worker", "db"]},
            {"op": "connected", "args": ["api", "db"]},
            {"op": "component", "args": ["api"]},
            {"op": "stats"},
        ]
        network = UnionFindNetwork()
        results = network.run_script(operations)
        self.assertTrue(results[2]["connected"])
        self.assertEqual(results[3]["summary"]["members"], ["api", "db", "worker"])

        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "ops.json"
            script_path.write_text(json.dumps(operations))
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--script", str(script_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["stats"]["nodes"], 3)
        self.assertEqual(payload["stats"]["components"], 1)
        self.assertEqual(payload["components"][0]["members"], ["api", "db", "worker"])

    def test_csv_import_helpers_and_snapshots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "edges.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["source", "target"])
                writer.writerow(["api", "worker"])
                writer.writerow(["worker", "db"])
                writer.writerow(["db", "api"])

            edges = load_edges_from_csv(csv_path)
            self.assertEqual(edges[0], ("api", "worker"))

            imported = run_csv_import(csv_path, snapshot_every=2)
            self.assertEqual(imported["edges_processed"], 3)
            self.assertEqual(imported["cycle_edges"], 1)
            self.assertEqual(imported["stats"]["components"], 1)
            self.assertEqual(imported["snapshots"][0]["edge_index"], 2)
            self.assertEqual(imported["snapshots"][-1]["edge_index"], 3)

            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--edges-csv", str(csv_path), "--snapshot-every", "2"],
                check=True,
                capture_output=True,
                text=True,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "csv-import")
        self.assertEqual(payload["components"][0]["members"], ["api", "db", "worker"])

    def test_benchmark_cli_output_is_reproducible(self):
        result = run_benchmark(nodes=20, edges=40, seed=11)
        self.assertEqual(result["mode"], "benchmark")
        self.assertEqual(result["nodes_requested"], 20)
        self.assertEqual(result["edges_requested"], 40)
        self.assertGreaterEqual(result["stats"]["nodes"], 2)

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--benchmark",
                "--benchmark-nodes",
                "20",
                "--benchmark-edges",
                "40",
                "--benchmark-seed",
                "11",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["seed"], 11)
        self.assertEqual(payload["stats"]["nodes"], result["stats"]["nodes"])
        self.assertEqual(payload["stats"]["successful_unions"], result["stats"]["successful_unions"])

    def test_benchmark_series_and_export_helpers(self):
        series = run_benchmark_series(nodes=24, edge_counts=[20, 40, 80], seed=13)
        self.assertEqual(series["mode"], "benchmark-series")
        self.assertEqual(series["edge_counts"], [20, 40, 80])
        self.assertEqual(len(series["runs"]), 3)
        self.assertIn("median_edges_per_second", series["summary"])

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "reports" / "union_find_benchmark.json"
            csv_path = Path(tmpdir) / "reports" / "union_find_benchmark.csv"
            write_json_report(series, json_path)
            write_benchmark_series_csv(series, csv_path)

            saved_json = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_json["mode"], "benchmark-series")

            with csv_path.open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["seed"], "13")
            self.assertEqual(rows[-1]["edges_requested"], "80")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--benchmark-series",
                    "20,40,80",
                    "--benchmark-nodes",
                    "24",
                    "--benchmark-seed",
                    "13",
                    "--output-json",
                    str(json_path),
                    "--output-csv",
                    str(csv_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "benchmark-series")
        self.assertEqual(payload["edge_counts"], [20, 40, 80])
        self.assertEqual(payload["runs"][-1]["edges_requested"], 80)
        self.assertIn("median_edges_per_second", payload["summary"])

    def test_parse_benchmark_series_validation(self):
        self.assertEqual(parse_benchmark_series("10, 20,30"), [10, 20, 30])
        with self.assertRaisesRegex(ValueError, "comma-separated list"):
            parse_benchmark_series("ten,20")
        with self.assertRaisesRegex(ValueError, "positive integers"):
            parse_benchmark_series("0,20")

    def test_invalid_script_operation_raises(self):
        network = UnionFindNetwork()
        with self.assertRaisesRegex(ValueError, "unsupported operation"):
            network.run_script([{"op": "explode", "args": []}])

    def test_malformed_script_input_raises(self):
        network = UnionFindNetwork()
        with self.assertRaisesRegex(ValueError, "operations must be a list"):
            network.run_script({"op": "union", "args": ["a", "b"]})  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "'op' field"):
            network.run_script([{"args": ["a", "b"]}])
        with self.assertRaisesRegex(ValueError, "args must be a list"):
            network.run_script([{"op": "union", "args": "a,b"}])

    def test_invalid_csv_and_mode_arguments_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_csv = Path(tmpdir) / "bad.csv"
            bad_csv.write_text("left,right\na,b\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source,target"):
                load_edges_from_csv(bad_csv)

        completed = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--benchmark", "--script", str(MODULE_PATH)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("choose only one", completed.stderr)

        completed = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--output-csv", "bench.csv"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires --benchmark-series", completed.stderr)


if __name__ == "__main__":
    unittest.main()
