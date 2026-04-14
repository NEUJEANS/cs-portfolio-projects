import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("union_find_network.py")
sys.path.insert(0, str(MODULE_PATH.parent))

from union_find_network import UnionFindNetwork  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
