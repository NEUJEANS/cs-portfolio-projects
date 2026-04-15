from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "network-flow-lab" / "network_flow.py"

spec = importlib.util.spec_from_file_location("network_flow_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

Edge = module.Edge
load_graph = module.load_graph
solve_max_flow = module.solve_max_flow


class NetworkFlowLabTests(unittest.TestCase):
    def test_clrs_style_graph_returns_expected_max_flow(self) -> None:
        nodes = ["s", "v1", "v2", "v3", "v4", "t"]
        edges = [
            Edge("s", "v1", 16),
            Edge("s", "v2", 13),
            Edge("v1", "v2", 10),
            Edge("v2", "v1", 4),
            Edge("v1", "v3", 12),
            Edge("v3", "v2", 9),
            Edge("v2", "v4", 14),
            Edge("v4", "v3", 7),
            Edge("v3", "t", 20),
            Edge("v4", "t", 4),
        ]

        result = solve_max_flow(nodes, edges, "s", "t")

        self.assertEqual(result.max_flow, 23)
        self.assertGreaterEqual(len(result.augmenting_paths), 3)
        self.assertEqual(result.min_cut["source_side"], ["s", "v1", "v2", "v4"])
        self.assertEqual(result.min_cut["sink_side"], ["t", "v3"])

    def test_parallel_edges_are_aggregated(self) -> None:
        result = solve_max_flow(
            ["s", "a", "t"],
            [Edge("s", "a", 3), Edge("s", "a", 2), Edge("a", "t", 4)],
            "s",
            "t",
        )
        self.assertEqual(result.max_flow, 4)
        by_edge = {(item["source"], item["target"]): item for item in result.edge_flows}
        self.assertEqual(by_edge[("s", "a")]["capacity"], 5)
        self.assertEqual(by_edge[("s", "a")]["flow"], 4)

    def test_disconnected_graph_has_zero_flow(self) -> None:
        result = solve_max_flow(["s", "a", "t"], [Edge("s", "a", 5)], "s", "t")
        self.assertEqual(result.max_flow, 0)
        self.assertEqual(result.augmenting_paths, [])
        self.assertEqual(result.min_cut["sink_side"], ["t"])

    def test_load_graph_rejects_negative_capacity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text(
                json.dumps(
                    {
                        "nodes": ["s", "t"],
                        "source": "s",
                        "sink": "t",
                        "edges": [{"source": "s", "target": "t", "capacity": -1}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "capacity"):
                load_graph(path)

    def test_cli_demo_outputs_json_payload(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "demo")
        self.assertEqual(payload["max_flow"], 19)
        self.assertTrue(payload["augmenting_paths"])


if __name__ == "__main__":
    unittest.main()
