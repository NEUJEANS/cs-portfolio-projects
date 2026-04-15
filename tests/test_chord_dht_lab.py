from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "chord-dht-lab" / "chord_dht.py"
RING_PATH = PROJECT_ROOT / "projects" / "chord-dht-lab" / "ring.json"

spec = importlib.util.spec_from_file_location("chord_dht_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

ChordRing = module.ChordRing


class ChordDhtLabTests(unittest.TestCase):
    def test_finger_table_matches_successor_rule(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])
        alpha = ring.get_node("alpha")

        table = ring.finger_table("alpha")

        self.assertEqual(len(table), 8)
        self.assertEqual(table[0].start, (alpha.node_id + 1) % ring.ring_size)
        self.assertEqual(table[1].start, (alpha.node_id + 2) % ring.ring_size)
        for entry in table:
            owner = ring.successor_for_id(entry.start)
            self.assertEqual(entry.successor, owner.name)
            self.assertEqual(entry.successor_id, owner.node_id)

    def test_successor_list_follows_clockwise_ring_order(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        successors = ring.successor_list("alpha", count=3)

        self.assertEqual([item["name"] for item in successors], ["charlie", "delta", "echo"])
        self.assertEqual(successors[0]["id"], ring.get_node("charlie").node_id)

    def test_lookup_route_resolves_to_key_owner(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        result = ring.lookup("alpha", "compiler")
        expected_owner = ring.successor_for_id(ring.hash_identifier("compiler"))

        self.assertEqual(result.responsible_node, expected_owner.name)
        self.assertEqual(result.responsible_node_id, expected_owner.node_id)
        self.assertGreaterEqual(result.hop_count, 0)
        self.assertEqual(result.route[0], "alpha")
        self.assertLessEqual(result.hop_count, len(ring.nodes))

    def test_linear_lookup_matches_owner_with_possible_extra_hops(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        finger_result = ring.lookup("alpha", "compiler")
        linear_result = ring.linear_lookup("alpha", "compiler")

        self.assertEqual(linear_result.responsible_node, finger_result.responsible_node)
        self.assertEqual(linear_result.responsible_node_id, finger_result.responsible_node_id)
        self.assertGreaterEqual(linear_result.hop_count, finger_result.hop_count)
        self.assertEqual(linear_result.route[0], "alpha")

    def test_benchmark_summary_counts_cases_and_savings(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        benchmark = ring.benchmark_lookups(
            ["compiler", "slides"], start_nodes=["alpha", "charlie", "alpha"]
        )

        self.assertEqual(benchmark["node_count"], 5)
        self.assertEqual(len(benchmark["nodes"]), 5)
        self.assertEqual(benchmark["start_nodes"], ["alpha", "charlie"])
        self.assertEqual(benchmark["summary"]["case_count"], 4)
        self.assertEqual(len(benchmark["cases"]), 4)
        self.assertGreaterEqual(
            benchmark["summary"]["average_linear_hops"], benchmark["summary"]["average_chord_hops"]
        )
        self.assertEqual(
            benchmark["summary"]["improved_cases"]
            + benchmark["summary"]["tied_cases"]
            + benchmark["summary"]["slower_cases"],
            4,
        )

    def test_resilience_report_fails_over_to_next_replica(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.resilience_report(["compiler"], failed_nodes=["charlie"], replica_count=3)

        case = report["cases"][0]
        self.assertTrue(case["available"])
        self.assertTrue(case["degraded"])
        self.assertEqual(case["primary_owner"], "charlie")
        self.assertEqual(case["served_by"], "delta")
        self.assertEqual([item["name"] for item in case["surviving_replicas"]], ["delta", "echo"])

    def test_resilience_report_marks_unavailable_when_all_replicas_fail(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.resilience_report(
            ["compiler"],
            failed_nodes=["charlie", "delta", "echo"],
            replica_count=3,
        )

        case = report["cases"][0]
        self.assertFalse(case["available"])
        self.assertIsNone(case["served_by"])
        self.assertFalse(case["surviving_replicas"])
        self.assertEqual(report["summary"]["unavailable_cases"], 1)

    def test_join_report_identifies_only_moved_keys(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])
        keys = ["report.pdf", "slides", "internship-notes", "compiler", "final-project"]

        report = ring.join_report("foxtrot", keys)

        self.assertEqual(report["joined_node"], "foxtrot")
        moved_keys = report["moved_keys"]
        self.assertTrue(moved_keys)
        after_ring = ring.add_node("foxtrot")
        for item in moved_keys:
            self.assertEqual(item["to"], after_ring.successor_for_id(item["key_id"]).name)
            self.assertNotEqual(item["from"], item["to"])

    def test_stabilization_report_repairs_joined_node_over_multiple_rounds(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.stabilization_report(joined_node="foxtrot", rounds=8)

        self.assertEqual(report["joined_node"], "foxtrot")
        self.assertFalse(report["rounds"][0]["nodes"][-1]["successor_ok"])
        self.assertEqual(report["rounds"][0]["nodes"][-1]["matching_fingers"], 0)
        self.assertTrue(report["summary"]["fully_stabilized"])
        self.assertEqual(report["summary"]["final_finger_matches"], report["summary"]["total_fingers"])

    def test_stabilization_report_handles_failure_scenario(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.stabilization_report(failed_nodes=["echo"], rounds=8)

        self.assertEqual(report["failed_nodes"], ["echo"])
        self.assertEqual(report["target_node_count"], 4)
        self.assertTrue(report["summary"]["fully_stabilized"])
        self.assertEqual(len(report["target_nodes"]), 4)

    def test_synthetic_benchmark_payload_is_deterministic_and_unique(self) -> None:
        payload = module.build_synthetic_benchmark_payload(
            m_bits=8,
            node_count=8,
            key_count=10,
            seed=11,
            start_nodes=3,
        )

        repeated = module.build_synthetic_benchmark_payload(
            m_bits=8,
            node_count=8,
            key_count=10,
            seed=11,
            start_nodes=3,
        )

        self.assertEqual(payload["ring"]["nodes"], repeated["ring"]["nodes"])
        self.assertEqual(payload["keys"], repeated["keys"])
        self.assertEqual(payload["benchmark"]["summary"]["case_count"], 30)
        self.assertEqual(payload["generator"]["benchmark_start_node_count"], 3)
        node_ids = [item["id"] for item in payload["ring"]["nodes"]]
        self.assertEqual(len(node_ids), len(set(node_ids)))
        self.assertGreaterEqual(
            payload["benchmark"]["summary"]["average_linear_hops"],
            payload["benchmark"]["summary"]["average_chord_hops"],
        )

    def test_synthetic_benchmark_rejects_invalid_parameters(self) -> None:
        with self.assertRaisesRegex(ValueError, "m_bits"):
            module.build_synthetic_benchmark_payload(m_bits=0, node_count=4, key_count=4, seed=1)
        with self.assertRaisesRegex(ValueError, "node_count"):
            module.build_synthetic_benchmark_payload(m_bits=8, node_count=0, key_count=4, seed=1)
        with self.assertRaisesRegex(ValueError, "key_count"):
            module.build_synthetic_benchmark_payload(m_bits=8, node_count=4, key_count=0, seed=1)

    def test_load_ring_rejects_non_string_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad_ring.json"
            path.write_text(json.dumps({"m_bits": 4, "nodes": ["alpha", 7]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nodes"):
                module.load_ring(path)

    def test_graphviz_ring_export_contains_successor_edges(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        dot = ring.export_graphviz("ring")

        self.assertIn("digraph chord_ring", dot)
        self.assertIn('"alpha" -> "charlie" [label="successor"]', dot)
        self.assertIn('"echo" -> "bravo" [label="successor"]', dot)

    def test_graphviz_route_export_marks_key_and_hops(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        dot = ring.export_graphviz("route", start_node="alpha", key="compiler")

        self.assertIn("digraph chord_route", dot)
        self.assertIn('"key:compiler"', dot)
        self.assertIn('label="hop 1"', dot)
        self.assertIn('label="maps to"', dot)

    def test_graphviz_stabilization_export_contains_round_clusters(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        dot = ring.export_graphviz("stabilize", joined_node="foxtrot", rounds=3)

        self.assertIn("digraph chord_stabilization", dot)
        self.assertIn("subgraph cluster_round_0", dot)
        self.assertIn('"r0:foxtrot"', dot)
        self.assertIn('"r3:summary"', dot)

    def test_cli_demo_outputs_expected_shape(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "demo"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "demo")
        self.assertIn("finger_tables", payload)
        self.assertIn("successor_lists", payload)
        self.assertIn("lookup", payload)
        self.assertIn("resilience_preview", payload)
        self.assertIn("stabilization_preview", payload)
        self.assertIn("graphviz_preview", payload)
        self.assertIn("hop_benchmark", payload)
        self.assertEqual(payload["lookup"]["key"], "compiler")
        owners = {item["key"]: item["owner"] for item in payload["sample_assignments"]}
        self.assertEqual(payload["lookup"]["responsible_node"], owners["compiler"])

    def test_cli_route_uses_json_ring_file(self) -> None:
        completed = subprocess.run(
            ["python3", str(MODULE_PATH), "route", str(RING_PATH), "alpha", "compiler"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "route")
        self.assertEqual(payload["start_node"], "alpha")
        self.assertTrue(payload["route"])

    def test_cli_benchmark_supports_filtered_start_nodes(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "benchmark",
                str(RING_PATH),
                "compiler",
                "slides",
                "--start-node",
                "alpha",
                "--start-node",
                "charlie",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["start_nodes"], ["alpha", "charlie"])
        self.assertEqual(payload["summary"]["case_count"], 4)

    def test_cli_resilience_supports_failure_simulation(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "resilience",
                str(RING_PATH),
                "compiler",
                "slides",
                "--failed-node",
                "alpha",
                "--failed-node",
                "echo",
                "--replica-count",
                "3",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "resilience")
        self.assertEqual(payload["failed_nodes"], ["alpha", "echo"])
        self.assertEqual(payload["replica_count"], 3)
        self.assertEqual(payload["summary"]["case_count"], 2)

    def test_cli_stabilize_supports_join_and_rounds(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "stabilize",
                str(RING_PATH),
                "--joined-node",
                "foxtrot",
                "--rounds",
                "8",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "stabilize")
        self.assertEqual(payload["joined_node"], "foxtrot")
        self.assertEqual(payload["rounds_requested"], 8)
        self.assertTrue(payload["summary"]["fully_stabilized"])

    def test_cli_synth_benchmark_generates_reproducible_workload(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "synth-benchmark",
                "--m-bits",
                "9",
                "--nodes",
                "12",
                "--keys",
                "15",
                "--seed",
                "23",
                "--start-nodes",
                "4",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "synth-benchmark")
        self.assertEqual(payload["generator"]["seed"], 23)
        self.assertEqual(payload["generator"]["benchmark_start_node_count"], 4)
        self.assertEqual(len(payload["ring"]["nodes"]), 12)
        self.assertEqual(len(payload["keys"]), 15)
        self.assertEqual(payload["benchmark"]["summary"]["case_count"], 60)

    def test_cli_graphviz_route_outputs_dot_payload(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "graphviz",
                str(RING_PATH),
                "--mode",
                "route",
                "--start-node",
                "alpha",
                "--key",
                "compiler",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "graphviz")
        self.assertEqual(payload["mode"], "route")
        self.assertIn("digraph chord_route", payload["dot"])
        self.assertIn('"key:compiler"', payload["dot"])


if __name__ == "__main__":
    unittest.main()
