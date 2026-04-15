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
    build_svg_chart,
    generate_random_edges,
    graph_path_exists,
    load_chart_source,
    load_edges_from_csv,
    parse_benchmark_series,
    recompute_graph_stats,
    run_benchmark,
    run_benchmark_series,
    run_csv_import,
    run_recompute_comparison,
    write_benchmark_series_csv,
    write_comparison_markdown,
    write_json_report,
    write_svg_chart,
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
            script_path.write_text(json.dumps(operations), encoding="utf-8")
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

    def test_recompute_comparison_matches_union_find_stats(self):
        comparison = run_recompute_comparison(nodes=18, edges=36, seed=5, checkpoint_every=9)
        self.assertEqual(comparison["mode"], "connectivity-comparison")
        self.assertEqual(comparison["checkpoint_every"], 9)
        self.assertTrue(comparison["summary"]["same_largest_component"])
        self.assertTrue(comparison["summary"]["same_component_count"])
        self.assertGreater(comparison["summary"]["speedup_vs_recompute"], 0)
        self.assertEqual(len(comparison["union_find"]["checkpoints"]), 4)
        self.assertEqual(len(comparison["recompute_baseline"]["checkpoints"]), 4)

        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--compare-recompute",
                "--benchmark-nodes",
                "18",
                "--benchmark-edges",
                "36",
                "--benchmark-seed",
                "5",
                "--comparison-checkpoint-every",
                "9",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "connectivity-comparison")
        self.assertEqual(payload["summary"]["same_component_count"], True)

    def test_recompute_graph_stats_and_edge_generation(self):
        adjacency = {
            "a": {"b", "c"},
            "b": {"a", "c"},
            "c": {"b", "a"},
            "d": set(),
        }
        stats = recompute_graph_stats(adjacency)
        self.assertEqual(stats["components"], 2)
        self.assertEqual(stats["largest_component"], 3)
        self.assertEqual(stats["cyclic_components"], 1)
        self.assertTrue(graph_path_exists(adjacency, "a", "c"))
        self.assertFalse(graph_path_exists(adjacency, "a", "d"))

        edges = generate_random_edges(nodes=6, edges=5, seed=17)
        self.assertEqual(edges, generate_random_edges(nodes=6, edges=5, seed=17))
        self.assertEqual(len(edges), 5)

    def test_chart_rendering_from_supported_modes(self):
        benchmark_series = {
            "mode": "benchmark-series",
            "summary": {"median_edges_per_second": 222.5},
            "runs": [
                {"edges_requested": 10, "edges_per_second": 100.0, "stats": {"largest_component": 4}},
                {"edges_requested": 20, "edges_per_second": 200.0, "stats": {"largest_component": 8}},
                {"edges_requested": 30, "edges_per_second": 300.0, "stats": {"largest_component": 12}},
            ],
        }
        benchmark_svg = build_svg_chart(benchmark_series, title="Benchmark demo")
        self.assertIn("<svg", benchmark_svg)
        self.assertIn("Benchmark demo", benchmark_svg)
        self.assertIn("largest connected component", benchmark_svg)
        self.assertIn("Largest component size", benchmark_svg)
        self.assertIn("Throughput", benchmark_svg)

        csv_import = {
            "mode": "csv-import",
            "cycle_edges": 1,
            "snapshots": [
                {"edge_index": 1, "stats": {"largest_component": 2}},
                {"edge_index": 3, "stats": {"largest_component": 3}},
                {"edge_index": 5, "stats": {"largest_component": 5}},
            ],
        }
        import_svg = build_svg_chart(csv_import)
        self.assertIn("component growth", import_svg)
        self.assertIn("Largest component size", import_svg)

        comparison_svg = build_svg_chart(
            {
                "mode": "connectivity-comparison",
                "summary": {"speedup_vs_recompute": 4.2},
                "union_find": {
                    "checkpoints": [
                        {"edge_index": 10, "elapsed_ms": 1.0},
                        {"edge_index": 20, "elapsed_ms": 2.0},
                    ]
                },
                "recompute_baseline": {
                    "checkpoints": [
                        {"edge_index": 10, "elapsed_ms": 3.0},
                        {"edge_index": 20, "elapsed_ms": 8.0},
                    ]
                },
            },
            title="Comparison demo",
        )
        self.assertIn("Comparison demo", comparison_svg)
        self.assertIn("Union-Find", comparison_svg)
        self.assertIn("BFS recompute", comparison_svg)

    def test_refresh_artifacts_helper_and_chart_source_loading(self):
        series = run_benchmark_series(nodes=24, edge_counts=[20, 40, 80], seed=13)
        comparison = run_recompute_comparison(nodes=20, edges=40, seed=13, checkpoint_every=10)
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            json_path = tmpdir_path / "benchmark.json"
            csv_path = tmpdir_path / "benchmark.csv"
            svg_path = tmpdir_path / "benchmark.svg"
            comparison_json = tmpdir_path / "comparison.json"
            comparison_svg = tmpdir_path / "comparison.svg"
            comparison_md = tmpdir_path / "comparison.md"
            cli_comparison_md = tmpdir_path / "comparison-cli.md"
            write_json_report(series, json_path)
            write_benchmark_series_csv(series, csv_path)
            write_json_report(comparison, comparison_json)

            json_payload = load_chart_source(json_path)
            csv_payload = load_chart_source(csv_path)
            comparison_payload = load_chart_source(comparison_json)

            helper_dir = tmpdir_path / "helper"
            helper_dir.mkdir()
            helper_cli = helper_dir / "union_find_network.py"
            helper_refresh = helper_dir / "refresh_artifacts.py"
            helper_cli.write_text(MODULE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            helper_refresh.write_text((MODULE_PATH.parent / "refresh_artifacts.py").read_text(encoding="utf-8"), encoding="utf-8")
            benchmark_fixture = helper_dir / "sample_benchmark_report.json"
            comparison_fixture = helper_dir / "sample_recompute_comparison.json"
            benchmark_fixture.write_text(json.dumps(series, indent=2), encoding="utf-8")
            comparison_fixture.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
            subprocess.run([sys.executable, str(helper_refresh)], check=True, cwd=MODULE_PATH.parent.parent.parent)
            self.assertTrue((helper_dir / "sample_benchmark_report.svg").exists())
            self.assertTrue((helper_dir / "sample_recompute_comparison.svg").exists())
            self.assertTrue((helper_dir / "sample_recompute_summary.md").exists())
            self.assertEqual(json_payload["mode"], "benchmark-series")
            self.assertEqual(csv_payload["mode"], "benchmark-series-csv")
            self.assertEqual(len(csv_payload["runs"]), 3)
            self.assertEqual(comparison_payload["mode"], "connectivity-comparison")

            write_svg_chart(json_payload, svg_path, title="Rendered from JSON")
            svg_text = svg_path.read_text(encoding="utf-8")
            self.assertIn("Rendered from JSON", svg_text)
            self.assertIn("<polyline", svg_text)

            write_svg_chart(comparison_payload, comparison_svg, title="Rendered comparison")
            comparison_text = comparison_svg.read_text(encoding="utf-8")
            self.assertIn("Rendered comparison", comparison_text)
            self.assertIn("Union-Find", comparison_text)

            write_comparison_markdown(comparison_payload, comparison_md)
            markdown_text = comparison_md.read_text(encoding="utf-8")
            self.assertIn("Union-Find vs BFS recomputation summary", markdown_text)
            self.assertIn("Measured speedup", markdown_text)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--chart-input",
                    str(csv_path),
                    "--output-chart",
                    str(svg_path),
                    "--chart-title",
                    "CLI SVG",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            markdown_completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--chart-input",
                    str(comparison_json),
                    "--output-markdown",
                    str(cli_comparison_md),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["mode"], "benchmark-series-csv")
            self.assertEqual(payload["chart_output"], str(svg_path))
            markdown_payload = json.loads(markdown_completed.stdout)
            self.assertEqual(markdown_payload["mode"], "connectivity-comparison")
            self.assertEqual(markdown_payload["markdown_output"], str(cli_comparison_md))
            self.assertTrue(cli_comparison_md.exists())
            self.assertIn("Portfolio-ready takeaway", cli_comparison_md.read_text(encoding="utf-8"))

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

            chart_path = Path(tmpdir) / "chart.svg"
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--output-chart", str(chart_path)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--output-chart requires", completed.stderr)

            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--chart-title", "Oops"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--chart-title requires", completed.stderr)

            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--output-markdown", str(Path(tmpdir) / "summary.md")],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--output-markdown requires", completed.stderr)

            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--compare-recompute", "--comparison-checkpoint-every", "-1"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("--comparison-checkpoint-every must be zero or a positive integer", completed.stderr)


if __name__ == "__main__":
    unittest.main()
