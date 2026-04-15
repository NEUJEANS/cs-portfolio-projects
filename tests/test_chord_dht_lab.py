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

    def test_load_ring_rejects_non_string_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad_ring.json"
            path.write_text(json.dumps({"m_bits": 4, "nodes": ["alpha", 7]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nodes"):
                module.load_ring(path)

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


if __name__ == "__main__":
    unittest.main()
