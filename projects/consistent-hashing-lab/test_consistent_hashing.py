import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from consistent_hashing import ConsistentHashRing, generate_keys, simulate_remap


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

    def test_adding_node_moves_only_fraction_of_keys(self):
        summary = simulate_remap(
            ["node-a", "node-b", "node-c"],
            generate_keys(2000),
            virtual_nodes=128,
            add="node-d",
        )
        self.assertGreater(summary["moved_keys"], 0)
        self.assertLess(summary["movement_ratio"], 0.45)

    def test_removing_unknown_node_raises(self):
        with self.assertRaises(ValueError):
            simulate_remap(["node-a", "node-b"], generate_keys(10), virtual_nodes=16, remove="node-z")

    def test_duplicate_node_rejected(self):
        ring = ConsistentHashRing(["node-a"], virtual_nodes=8)
        with self.assertRaises(ValueError):
            ring.add_node("node-a")

    def test_cli_report_outputs_json(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "report", "--nodes", "node-a", "node-b", "node-c", "--key-count", "1200", "--virtual-nodes", "128"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["total_keys"], 1200)
        self.assertEqual(payload["nodes"], 3)


if __name__ == "__main__":
    unittest.main()
