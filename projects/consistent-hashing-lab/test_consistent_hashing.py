import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from consistent_hashing import (
    ConsistentHashRing,
    benchmark_series_rows,
    benchmark_virtual_nodes,
    generate_keys,
    render_benchmark_series_markdown,
    simulate_remap,
)


SCRIPT = PROJECT_DIR / "consistent_hashing.py"


class ConsistentHashRingTests(unittest.TestCase):
    def test_assignments_are_deterministic(self):
        keys = ["alice", "bob", "carol", "dave"]
        ring_one = ConsistentHashRing(["node-a", "node-b", "node-c"], virtual_nodes=128)
        ring_two = ConsistentHashRing(["node-a", "node-b", "node-c"], virtual_nodes=128)
        self.assertEqual(ring_one.assign_keys(keys), ring_two.assign_keys(keys))

    def test_distribution_includes_all_nodes(self):
        ring = ConsistentHashRing(["node-a", "node-b", "node-c"], virtual_nodes=128)
        report = ring.load_report(generate_keys(1000))
        self.assertEqual(report["total_keys"], 1000)
        self.assertEqual(set(report["distribution"].keys()), {"node-a", "node-b", "node-c"})
        self.assertLess(report["imbalance_ratio"], 1.35)

    def test_replication_selects_distinct_nodes(self):
        ring = ConsistentHashRing(["node-a", "node-b", "node-c"], virtual_nodes=64)
        replicas = ring.get_nodes("user:42", replication_factor=3)
        self.assertEqual(len(replicas), 3)
        self.assertEqual(len(set(replicas)), 3)

    def test_replication_factor_caps_at_available_nodes(self):
        ring = ConsistentHashRing(["node-a", "node-b", "node-c"], virtual_nodes=64)
        replicas = ring.get_nodes("user:42", replication_factor=10)
        self.assertEqual(len(replicas), 3)
        report = ring.load_report(generate_keys(50), replication_factor=10)
        self.assertEqual(report["effective_replication_factor"], 3)
        self.assertEqual(report["total_replica_placements"], 150)

    def test_replication_distribution_counts_replica_placements(self):
        ring = ConsistentHashRing(["node-a", "node-b", "node-c"], virtual_nodes=128)
        report = ring.load_report(generate_keys(300), replication_factor=2)
        self.assertEqual(report["replication_factor"], 2)
        self.assertEqual(report["total_replica_placements"], 600)
        self.assertEqual(sum(report["distribution"].values()), 600)

    def test_adding_node_moves_only_fraction_of_primary_assignments(self):
        summary = simulate_remap(
            ["node-a", "node-b", "node-c"],
            generate_keys(2000),
            virtual_nodes=128,
            add="node-d",
        )
        self.assertGreater(summary["moved_keys"], 0)
        self.assertLess(summary["movement_ratio"], 0.45)

    def test_replication_remap_changes_replica_sets(self):
        summary = simulate_remap(
            ["node-a", "node-b", "node-c"],
            generate_keys(1200),
            virtual_nodes=128,
            add="node-d",
            replication_factor=2,
        )
        self.assertEqual(summary["replication_factor"], 2)
        self.assertGreater(summary["moved_keys"], 0)
        self.assertGreater(summary["replica_placement_changes"], 0)
        self.assertLess(summary["movement_ratio"], 0.8)

    def test_benchmark_virtual_nodes_reports_series(self):
        payload = benchmark_virtual_nodes(
            ["node-a", "node-b", "node-c", "node-d"],
            key_count=2000,
            virtual_node_counts=[1, 8, 64],
        )
        self.assertEqual(payload["virtual_node_counts"], [1, 8, 64])
        self.assertEqual(len(payload["series"]), 3)
        self.assertEqual(payload["best_imbalance_virtual_nodes"], 64)
        self.assertLess(payload["best_imbalance_ratio"], 1.2)

    def test_benchmark_virtual_nodes_can_include_remap_metrics(self):
        payload = benchmark_virtual_nodes(
            ["node-a", "node-b", "node-c"],
            key_count=1500,
            virtual_node_counts=[8, 64],
            add="node-d",
            replication_factor=2,
        )
        self.assertEqual(payload["topology_change"], {"action": "add", "node": "node-d"})
        for point in payload["series"]:
            self.assertGreater(point["moved_keys"], 0)
            self.assertGreater(point["replica_placement_changes"], 0)
            self.assertGreater(point["movement_ratio"], 0.0)

    def test_benchmark_series_rows_flatten_topology_and_best_metrics(self):
        payload = benchmark_virtual_nodes(
            ["node-a", "node-b", "node-c"],
            key_count=500,
            virtual_node_counts=[8, 32],
            add="node-d",
        )
        rows = benchmark_series_rows(payload)
        self.assertEqual([row["virtual_nodes"] for row in rows], [8, 32])
        self.assertTrue(all(row["topology_action"] == "add" for row in rows))
        self.assertTrue(all(row["topology_node"] == "node-d" for row in rows))
        self.assertTrue(all("best_imbalance_ratio" in row for row in rows))

    def test_render_benchmark_series_markdown_highlights_best_point(self):
        payload = benchmark_virtual_nodes(
            ["node-a", "node-b", "node-c", "node-d"],
            key_count=1200,
            virtual_node_counts=[1, 16, 128],
            add="node-e",
            replication_factor=2,
        )
        markdown = render_benchmark_series_markdown(payload)
        self.assertIn("# Consistent Hashing Virtual-Node Benchmark Report", markdown)
        self.assertIn("## Benchmark series", markdown)
        self.assertIn("| Virtual nodes | Max load | Min load | Average load |", markdown)
        self.assertIn("Topology change: add `node-e`", markdown)
        self.assertIn("## Takeaways", markdown)
        self.assertIn(str(payload["best_imbalance_virtual_nodes"]), markdown)

    def test_benchmark_deduplicates_virtual_node_counts(self):
        payload = benchmark_virtual_nodes(
            ["node-a", "node-b", "node-c"],
            key_count=100,
            virtual_node_counts=[8, 8, 32],
        )
        self.assertEqual(payload["virtual_node_counts"], [8, 32])

    def test_removing_unknown_node_raises(self):
        with self.assertRaises(ValueError):
            simulate_remap(["node-a", "node-b"], generate_keys(10), virtual_nodes=16, remove="node-z")

    def test_duplicate_node_rejected(self):
        ring = ConsistentHashRing(["node-a"], virtual_nodes=8)
        with self.assertRaises(ValueError):
            ring.add_node("node-a")

    def test_cli_report_outputs_json(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "report",
                "--nodes",
                "node-a",
                "node-b",
                "node-c",
                "--key-count",
                "1200",
                "--virtual-nodes",
                "128",
                "--replication-factor",
                "2",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["total_keys"], 1200)
        self.assertEqual(payload["nodes"], 3)
        self.assertEqual(payload["replication_factor"], 2)
        self.assertEqual(payload["effective_replication_factor"], 2)

    def test_cli_benchmark_outputs_json(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "benchmark",
                "--nodes",
                "node-a",
                "node-b",
                "node-c",
                "--key-count",
                "2000",
                "--virtual-node-counts",
                "1",
                "16",
                "128",
                "--add-node",
                "node-d",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["node_count"], 3)
        self.assertEqual(payload["virtual_node_counts"], [1, 16, 128])
        self.assertEqual(payload["topology_change"], {"action": "add", "node": "node-d"})
        self.assertIn("movement_ratio", payload["series"][0])

    def test_cli_benchmark_can_write_csv_and_markdown_exports(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            csv_path = tmp_path / "benchmark.csv"
            markdown_path = tmp_path / "benchmark.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "benchmark",
                    "--nodes",
                    "node-a",
                    "node-b",
                    "node-c",
                    "--key-count",
                    "800",
                    "--virtual-node-counts",
                    "1",
                    "8",
                    "64",
                    "--add-node",
                    "node-d",
                    "--csv-out",
                    str(csv_path),
                    "--markdown-out",
                    str(markdown_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["csv_output"], str(csv_path))
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertTrue(csv_path.exists())
            self.assertTrue(markdown_path.exists())
            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("virtual_nodes,max_load,min_load,average_load,imbalance_ratio", csv_text)
            self.assertIn("topology_action,topology_node", csv_text)
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# Consistent Hashing Virtual-Node Benchmark Report", markdown)
            self.assertIn("Topology change: add `node-d`", markdown)

    def test_cli_rejects_conflicting_benchmark_topology_changes(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "benchmark",
                "--nodes",
                "node-a",
                "node-b",
                "node-c",
                "--key-count",
                "10",
                "--virtual-node-counts",
                "8",
                "32",
                "--add-node",
                "node-d",
                "--remove-node",
                "node-a",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed with argument", result.stderr)

    def test_cli_rejects_non_positive_replication_factor(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "report",
                "--nodes",
                "node-a",
                "node-b",
                "--key-count",
                "10",
                "--replication-factor",
                "0",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("value must be positive", result.stderr)


if __name__ == "__main__":
    unittest.main()
