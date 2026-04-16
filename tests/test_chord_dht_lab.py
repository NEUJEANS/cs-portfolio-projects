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

    def test_stabilization_report_all_mode_repairs_every_finger_in_one_round(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.stabilization_report(joined_node="foxtrot", rounds=1, finger_repair_mode="all")

        self.assertEqual(report["finger_repair_mode"], "all")
        self.assertEqual(report["rounds"][1]["repaired_finger_slots"], list(range(ring.m_bits)))
        self.assertEqual(report["summary"]["final_finger_matches"], report["summary"]["total_fingers"])
        self.assertTrue(report["summary"]["fully_stabilized"])

    def test_stabilization_report_random_mode_is_seeded_and_requires_seed(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        with self.assertRaisesRegex(ValueError, "seed"):
            ring.stabilization_report(joined_node="foxtrot", rounds=2, finger_repair_mode="random")

        report = ring.stabilization_report(
            joined_node="foxtrot",
            rounds=3,
            finger_repair_mode="random",
            finger_repair_seed=29,
        )
        repeated = ring.stabilization_report(
            joined_node="foxtrot",
            rounds=3,
            finger_repair_mode="random",
            finger_repair_seed=29,
        )

        self.assertEqual(report["finger_repair_mode"], "random")
        self.assertEqual(report["finger_repair_seed"], 29)
        self.assertEqual(
            [round_data["repaired_finger_slots"] for round_data in report["rounds"]],
            [round_data["repaired_finger_slots"] for round_data in repeated["rounds"]],
        )
        self.assertTrue(all(len(round_data["repaired_finger_slots"]) == 1 for round_data in report["rounds"][1:]))

    def test_select_benchmark_start_nodes_supports_first_and_random_modes(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        first = module.select_benchmark_start_nodes(ring, 3, sample_mode="first")
        random_selection = module.select_benchmark_start_nodes(ring, 3, sample_mode="random", seed=19)
        repeated_random = module.select_benchmark_start_nodes(ring, 3, sample_mode="random", seed=19)

        self.assertEqual(first, [node.name for node in ring.nodes[:3]])
        self.assertEqual(random_selection, repeated_random)
        self.assertEqual(len(random_selection), 3)
        self.assertEqual(len(random_selection), len(set(random_selection)))
        self.assertNotEqual(random_selection, first)

    def test_select_benchmark_start_nodes_rejects_missing_seed_for_random_mode(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        with self.assertRaisesRegex(ValueError, "seed"):
            module.select_benchmark_start_nodes(ring, 2, sample_mode="random")

    def test_compare_benchmark_start_node_samples_summarizes_seeded_variance(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = module.compare_benchmark_start_node_samples(
            ring,
            ["compiler", "slides", "final-project"],
            sample_size=3,
            sample_seeds=[17, 29, 17],
        )

        self.assertEqual(comparison["sample_size"], 3)
        self.assertEqual(comparison["sample_seeds"], [17, 29])
        self.assertEqual(comparison["summary"]["sample_count"], 2)
        self.assertEqual(len(comparison["samples"]), 2)
        self.assertEqual(comparison["summary"]["case_count_per_sample"], 9)
        self.assertGreaterEqual(comparison["summary"]["max_total_hop_savings"], comparison["summary"]["min_total_hop_savings"])

    def test_compare_benchmark_start_node_samples_requires_seeds(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        with self.assertRaisesRegex(ValueError, "seed"):
            module.compare_benchmark_start_node_samples(ring, ["compiler"], sample_size=2, sample_seeds=[])

    def test_compare_stabilization_modes_reports_fastest_mode_and_progress(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = ring.compare_stabilization_modes(joined_node="foxtrot", rounds=3, random_seed=17)

        self.assertEqual(comparison["modes"], ["single", "all", "random"])
        self.assertEqual(comparison["summary"]["fastest_modes"], ["all"])
        self.assertEqual(comparison["summary"]["fastest_stabilized_round"], 1)
        self.assertEqual(comparison["comparison"][0]["mode"], "all")
        self.assertEqual(comparison["comparison"][0]["stabilized_round"], 1)
        self.assertEqual(comparison["comparison"][0]["final_finger_progress_ratio"], 1.0)
        self.assertIn("single", comparison["reports"])
        self.assertEqual(comparison["reports"]["random"]["finger_repair_seed"], 17)

    def test_compare_stabilization_modes_supports_filtered_mode_lists(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = ring.compare_stabilization_modes(
            failed_nodes=["echo"],
            rounds=2,
            modes=["random", "single", "random"],
            random_seed=29,
        )

        self.assertEqual(comparison["modes"], ["random", "single"])
        self.assertEqual([row["mode"] for row in comparison["comparison"]], ["random", "single"])
        self.assertEqual(comparison["reports"]["random"]["finger_repair_seed"], 29)
        self.assertEqual(comparison["failed_nodes"], ["echo"])

    def test_render_benchmark_report_markdown_contains_case_table(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        benchmark = ring.benchmark_lookups(["compiler", "slides"], start_nodes=["alpha", "charlie"])
        report = module.render_benchmark_report_markdown(benchmark)

        self.assertIn("# Chord lookup benchmark", report)
        self.assertIn("- Start nodes benchmarked: `alpha`, `charlie`", report)
        self.assertIn("| Start node | Key | Responsible node | Chord hops | Linear hops | Hop savings |", report)
        self.assertIn("`compiler`", report)

    def test_render_benchmark_report_csv_contains_machine_readable_rows(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        benchmark = ring.benchmark_lookups(["compiler"], start_nodes=["alpha"])
        report = module.render_benchmark_report_csv(benchmark)

        self.assertIn("start_node,key,key_id,responsible_node,chord_hops,linear_hops,hop_savings,chord_route,linear_route", report)
        self.assertIn("alpha,compiler", report)

    def test_render_benchmark_sample_comparison_markdown_contains_seed_rows(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = module.compare_benchmark_start_node_samples(
            ring,
            ["compiler", "slides"],
            sample_size=3,
            sample_seeds=[17, 29],
        )
        report = module.render_benchmark_sample_comparison_markdown(comparison)

        self.assertIn("# Chord benchmark sample comparison", report)
        self.assertIn("- Sample seeds: `17`, `29`", report)
        self.assertIn("| Seed | Start nodes | Avg Chord hops | Avg linear hops | Total hop savings |", report)

    def test_render_benchmark_sample_comparison_csv_contains_machine_readable_rows(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = module.compare_benchmark_start_node_samples(
            ring,
            ["compiler"],
            sample_size=2,
            sample_seeds=[17],
        )
        report = module.render_benchmark_sample_comparison_csv(comparison)

        self.assertIn("seed,start_nodes,average_chord_hops,average_linear_hops,total_hop_savings,improved_cases,tied_cases,slower_cases,case_count", report)
        self.assertIn("17,", report)

    def test_summarize_benchmark_key_variance_orders_most_sensitive_key_first(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = module.compare_benchmark_start_node_samples(
            ring,
            ["compiler", "slides", "final-project"],
            sample_size=3,
            sample_seeds=[17, 29],
        )
        variance = module.summarize_benchmark_key_variance(comparison)

        self.assertEqual(variance["summary"]["sample_count"], 2)
        self.assertEqual(variance["summary"]["key_count"], 3)
        self.assertEqual(variance["key_summaries"][0]["hop_savings_spread"], variance["summary"]["highest_hop_savings_spread"])
        self.assertIn(variance["key_summaries"][0]["key"], variance["summary"]["most_sensitive_keys"])
        self.assertGreaterEqual(variance["key_summaries"][0]["sample_count"], 2)

    def test_render_benchmark_key_variance_markdown_contains_best_and_worst_seed_rows(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = module.compare_benchmark_start_node_samples(
            ring,
            ["compiler", "slides"],
            sample_size=3,
            sample_seeds=[17, 29],
        )
        variance = module.summarize_benchmark_key_variance(comparison)
        report = module.render_benchmark_key_variance_markdown(variance)

        self.assertIn("# Chord benchmark key variance", report)
        self.assertIn("- Most sensitive key(s):", report)
        self.assertIn("| Key | Responsible node | Avg chord hops | Avg linear hops | Avg hop savings |", report)
        self.assertIn("Best seed/start", report)
        self.assertIn("Worst seed/start", report)

    def test_render_benchmark_key_variance_csv_contains_machine_readable_rows(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = module.compare_benchmark_start_node_samples(
            ring,
            ["compiler"],
            sample_size=2,
            sample_seeds=[17, 29],
        )
        variance = module.summarize_benchmark_key_variance(comparison)
        report = module.render_benchmark_key_variance_csv(variance)

        self.assertIn("key,key_id,responsible_node,sample_count,average_chord_hops,average_linear_hops,average_hop_savings", report)
        self.assertIn("compiler,", report)
        self.assertIn("best_seed_cases", report)

    def test_render_stabilization_comparison_markdown_contains_summary_table(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = ring.compare_stabilization_modes(joined_node="foxtrot", rounds=3, random_seed=17)
        report = module.render_stabilization_comparison_markdown(comparison)

        self.assertIn("# Chord stabilization comparison", report)
        self.assertIn("- Scenario joined node: `foxtrot`", report)
        self.assertIn("| Mode | Stabilized round | Final finger progress |", report)
        self.assertIn("| `all` | 1 | 100.00% |", report)

    def test_render_stabilization_comparison_csv_contains_machine_readable_rows(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        comparison = ring.compare_stabilization_modes(failed_nodes=["echo"], rounds=2, random_seed=29)
        report = module.render_stabilization_comparison_csv(comparison)

        self.assertIn("mode,stabilized_round,final_finger_progress_ratio", report)
        self.assertIn("all,0,1.000000", report)
        self.assertIn("random,0,1.000000", report)

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
        self.assertEqual(payload["generator"]["start_node_sample_mode"], "first")
        self.assertEqual(payload["generator"]["start_node_seed"], 11)
        node_ids = [item["id"] for item in payload["ring"]["nodes"]]
        self.assertEqual(len(node_ids), len(set(node_ids)))
        self.assertGreaterEqual(
            payload["benchmark"]["summary"]["average_linear_hops"],
            payload["benchmark"]["summary"]["average_chord_hops"],
        )

    def test_synthetic_benchmark_payload_supports_randomized_start_node_sampling(self) -> None:
        payload = module.build_synthetic_benchmark_payload(
            m_bits=9,
            node_count=10,
            key_count=8,
            seed=17,
            start_nodes=4,
            start_node_sample_mode="random",
            start_node_seed=91,
        )
        repeated = module.build_synthetic_benchmark_payload(
            m_bits=9,
            node_count=10,
            key_count=8,
            seed=17,
            start_nodes=4,
            start_node_sample_mode="random",
            start_node_seed=91,
        )

        self.assertEqual(payload["benchmark"]["start_nodes"], repeated["benchmark"]["start_nodes"])
        self.assertEqual(payload["generator"]["start_node_sample_mode"], "random")
        self.assertEqual(payload["generator"]["start_node_seed"], 91)
        self.assertEqual(payload["generator"]["benchmark_start_node_count"], 4)
        self.assertEqual(payload["benchmark"]["summary"]["case_count"], 32)
        self.assertEqual(len(payload["benchmark"]["start_nodes"]), 4)
        self.assertEqual(len(payload["benchmark"]["start_nodes"]), len(set(payload["benchmark"]["start_nodes"])))

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
        self.assertIn("stabilization_comparison_preview", payload)
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

    def test_cli_benchmark_export_outputs_markdown(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "benchmark-export",
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

        self.assertIn("# Chord lookup benchmark", completed.stdout)
        self.assertIn("- Start nodes benchmarked: `alpha`, `charlie`", completed.stdout)
        self.assertIn("| Start node | Key | Responsible node | Chord hops | Linear hops | Hop savings |", completed.stdout)

    def test_cli_benchmark_export_outputs_csv(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "benchmark-export",
                str(RING_PATH),
                "compiler",
                "--start-node",
                "alpha",
                "--format",
                "csv",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("start_node,key,key_id,responsible_node,chord_hops,linear_hops,hop_savings,chord_route,linear_route", completed.stdout)
        self.assertIn("alpha,compiler", completed.stdout)

    def test_cli_benchmark_sample_export_outputs_markdown(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "benchmark-sample-export",
                str(RING_PATH),
                "compiler",
                "slides",
                "--sample-size",
                "3",
                "--sample-seed",
                "17",
                "--sample-seed",
                "29",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Chord benchmark sample comparison", completed.stdout)
        self.assertIn("- Sample seeds: `17`, `29`", completed.stdout)
        self.assertIn("| Seed | Start nodes | Avg Chord hops | Avg linear hops | Total hop savings |", completed.stdout)

    def test_cli_benchmark_key_variance_export_outputs_markdown_and_csv(self) -> None:
        markdown = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "benchmark-key-variance-export",
                str(RING_PATH),
                "compiler",
                "slides",
                "--sample-size",
                "3",
                "--sample-seed",
                "17",
                "--sample-seed",
                "29",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        csv_output = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "benchmark-key-variance-export",
                str(RING_PATH),
                "compiler",
                "--sample-size",
                "2",
                "--sample-seed",
                "17",
                "--sample-seed",
                "29",
                "--format",
                "csv",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Chord benchmark key variance", markdown.stdout)
        self.assertIn("- Most sensitive key(s):", markdown.stdout)
        self.assertIn("key,key_id,responsible_node,sample_count,average_chord_hops", csv_output.stdout)
        self.assertIn("compiler,", csv_output.stdout)

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

    def test_cli_stabilize_supports_all_finger_repair_mode(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "stabilize",
                str(RING_PATH),
                "--joined-node",
                "foxtrot",
                "--rounds",
                "1",
                "--finger-repair-mode",
                "all",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "stabilize")
        self.assertEqual(payload["finger_repair_mode"], "all")
        self.assertEqual(payload["rounds"][1]["repaired_finger_slots"], list(range(payload["m_bits"])))
        self.assertTrue(payload["summary"]["fully_stabilized"])

    def test_cli_compare_stabilize_outputs_scoreboard(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "compare-stabilize",
                str(RING_PATH),
                "--joined-node",
                "foxtrot",
                "--rounds",
                "3",
                "--mode",
                "single",
                "--mode",
                "all",
                "--mode",
                "random",
                "--random-seed",
                "17",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "compare-stabilize")
        self.assertEqual(payload["modes"], ["single", "all", "random"])
        self.assertEqual(payload["summary"]["fastest_modes"], ["all"])
        self.assertEqual(payload["summary"]["fastest_stabilized_round"], 1)
        self.assertEqual(payload["comparison"][0]["mode"], "all")
        self.assertEqual(payload["reports"]["random"]["finger_repair_seed"], 17)

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
        self.assertEqual(payload["generator"]["start_node_sample_mode"], "first")
        self.assertEqual(payload["generator"]["start_node_seed"], 23)
        self.assertEqual(len(payload["ring"]["nodes"]), 12)
        self.assertEqual(len(payload["keys"]), 15)
        self.assertEqual(payload["benchmark"]["summary"]["case_count"], 60)

    def test_cli_synth_benchmark_supports_random_start_node_sampling(self) -> None:
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
                "9",
                "--seed",
                "23",
                "--start-nodes",
                "4",
                "--start-node-sample-mode",
                "random",
                "--start-node-seed",
                "101",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "synth-benchmark")
        self.assertEqual(payload["generator"]["start_node_sample_mode"], "random")
        self.assertEqual(payload["generator"]["start_node_seed"], 101)
        self.assertEqual(payload["generator"]["benchmark_start_node_count"], 4)
        self.assertEqual(payload["benchmark"]["summary"]["case_count"], 36)
        self.assertEqual(len(payload["benchmark"]["start_nodes"]), 4)
        self.assertEqual(len(payload["benchmark"]["start_nodes"]), len(set(payload["benchmark"]["start_nodes"])))

    def test_cli_compare_stabilize_export_outputs_markdown(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "compare-stabilize-export",
                str(RING_PATH),
                "--joined-node",
                "foxtrot",
                "--rounds",
                "3",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Chord stabilization comparison", completed.stdout)
        self.assertIn("| `all` | 1 | 100.00% |", completed.stdout)

    def test_cli_compare_stabilize_export_outputs_csv(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "compare-stabilize-export",
                str(RING_PATH),
                "--failed-node",
                "echo",
                "--rounds",
                "2",
                "--format",
                "csv",
                "--random-seed",
                "29",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("mode,stabilized_round,final_finger_progress_ratio", completed.stdout)
        self.assertIn("all,0,1.000000", completed.stdout)

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

    def test_cli_graphviz_stabilize_supports_random_finger_repair_mode(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "graphviz",
                str(RING_PATH),
                "--mode",
                "stabilize",
                "--joined-node",
                "foxtrot",
                "--rounds",
                "2",
                "--finger-repair-mode",
                "random",
                "--finger-repair-seed",
                "17",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "graphviz")
        self.assertEqual(payload["mode"], "stabilize")
        self.assertIn("digraph chord_stabilization", payload["dot"])
        self.assertIn('repair=', payload["dot"])
        self.assertIn('finger repair: random (seed=17)', payload["dot"])


    def test_churn_report_chains_join_and_failure_events(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.churn_report(
            [
                {"action": "join", "node": "foxtrot", "rounds": 4},
                {"action": "fail", "node": "charlie", "rounds": 3},
            ],
            rounds=2,
        )

        self.assertEqual(report["event_count"], 2)
        self.assertEqual(report["steps"][0]["action"], "join")
        self.assertEqual(report["steps"][0]["node"], "foxtrot")
        self.assertEqual(report["steps"][0]["rounds_requested"], 4)
        self.assertEqual(report["steps"][1]["action"], "fail")
        self.assertEqual(report["steps"][1]["node"], "charlie")
        ending_names = [node["name"] for node in report["ending_nodes"]]
        self.assertIn("foxtrot", ending_names)
        self.assertNotIn("charlie", ending_names)
        self.assertEqual(report["summary"]["final_node_count"], len(ending_names))

    def test_churn_report_supports_recovering_failed_original_nodes(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.churn_report(
            [
                {"action": "fail", "node": "charlie", "rounds": 2},
                {"action": "recover", "node": "charlie", "rounds": 2},
            ],
            finger_repair_mode="all",
        )

        self.assertEqual(report["event_count"], 2)
        self.assertEqual(report["summary"]["fully_stabilized_steps"], 2)
        self.assertEqual(report["steps"][1]["action"], "recover")
        self.assertEqual(report["steps"][1]["target_node_count"], 5)
        self.assertEqual([node["name"] for node in report["ending_nodes"]], [node["name"] for node in ring.list_nodes()])

    def test_churn_report_rejects_recover_for_unknown_or_live_nodes(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        with self.assertRaisesRegex(ValueError, "absent from the current ring"):
            ring.churn_report([{"action": "recover", "node": "charlie", "rounds": 2}])

        with self.assertRaisesRegex(ValueError, "original ring"):
            ring.churn_report(
                [
                    {"action": "join", "node": "foxtrot", "rounds": 2},
                    {"action": "fail", "node": "foxtrot", "rounds": 2},
                    {"action": "recover", "node": "foxtrot", "rounds": 2},
                ]
            )

    def test_load_churn_events_rejects_non_list_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad_churn.json"
            path.write_text(json.dumps({"action": "join", "node": "foxtrot"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "JSON list"):
                module.load_churn_events(path)

    def test_render_churn_report_markdown_contains_step_table(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.churn_report(
            [
                {"action": "join", "node": "foxtrot", "rounds": 4},
                {"action": "fail", "node": "charlie", "rounds": 3},
            ],
            finger_repair_mode="all",
        )
        rendered = module.render_churn_report_markdown(report)

        self.assertIn("# Chord churn summary", rendered)
        self.assertIn("- Starting nodes: `alpha`, `charlie`, `delta`, `echo`, `bravo`", rendered)
        self.assertIn("| Step | Action | Node | Rounds | Stabilized round |", rendered)
        self.assertIn("| 1 | `join` | `foxtrot` | 4 | 1 | 100.00% | 6/6 | 6/6 |", rendered)

    def test_render_churn_report_csv_contains_machine_readable_rows(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])

        report = ring.churn_report(
            [
                {"action": "fail", "node": "charlie", "rounds": 2},
                {"action": "recover", "node": "charlie", "rounds": 2},
            ],
            finger_repair_mode="all",
        )
        rendered = module.render_churn_report_csv(report)

        self.assertIn("step,action,node,rounds_requested,finger_repair_mode,stabilized_round,fully_stabilized", rendered)
        self.assertIn("1,fail,charlie,2,all,0,true,1.000000,4,4,4,32,32,4", rendered)

    def test_compare_churn_workloads_sorts_best_workload_first(self) -> None:
        ring = ChordRing(8, ["alpha", "bravo", "charlie", "delta", "echo"])
        with tempfile.TemporaryDirectory() as tmpdir:
            fast_path = Path(tmpdir) / "fast.json"
            slow_path = Path(tmpdir) / "slow.json"
            fast_path.write_text(
                json.dumps([
                    {"action": "join", "node": "foxtrot", "rounds": 1},
                    {"action": "fail", "node": "charlie", "rounds": 1},
                ]),
                encoding="utf-8",
            )
            slow_path.write_text(
                json.dumps([
                    {"action": "join", "node": "foxtrot", "rounds": 1},
                    {"action": "fail", "node": "charlie", "rounds": 1},
                    {"action": "recover", "node": "charlie", "rounds": 1},
                ]),
                encoding="utf-8",
            )

            comparison = module.compare_churn_workloads(
                ring,
                [slow_path, fast_path],
                finger_repair_mode="all",
            )

        self.assertEqual(comparison["summary"]["workload_count"], 2)
        self.assertEqual(comparison["summary"]["best_events_file"], str(fast_path))
        self.assertEqual(comparison["summary"]["best_stabilization_rate"], 1.0)
        self.assertEqual(comparison["workloads"][0]["fully_stabilized_steps"], 2)
        self.assertEqual(comparison["workloads"][1]["fully_stabilized_steps"], 3)

    def test_render_churn_comparison_markdown_and_csv_include_workloads(self) -> None:
        comparison = {
            "rounds_default": 3,
            "finger_repair_mode": "all",
            "finger_repair_seed": None,
            "workloads": [
                {
                    "events_file": "events-a.json",
                    "event_count": 2,
                    "fully_stabilized_steps": 2,
                    "partially_stabilized_steps": 0,
                    "stabilization_rate": 1.0,
                    "average_stabilized_round": 1.0,
                    "max_stabilized_round": 1,
                    "final_node_count": 5,
                    "steps": [
                        {
                            "step": 1,
                            "action": "join",
                            "node": "foxtrot",
                            "stabilized_round": 1,
                            "fully_stabilized": True,
                            "final_finger_progress_ratio": 1.0,
                        }
                    ],
                }
            ],
            "summary": {
                "best_events_file": "events-a.json",
                "best_stabilization_rate": 1.0,
                "best_fully_stabilized_steps": 2,
                "best_average_stabilized_round": 1.0,
                "workload_count": 1,
            },
        }

        markdown = module.render_churn_comparison_markdown(comparison)
        csv_output = module.render_churn_comparison_csv(comparison)

        self.assertIn("# Chord churn workload comparison", markdown)
        self.assertIn("| `events-a.json` | 2 | 2 | 100.00% | 0 | 1.0 | 1 | 5 |", markdown)
        self.assertIn("events_file,event_count,fully_stabilized_steps,partially_stabilized_steps,stabilization_rate", csv_output)
        self.assertIn("events-a.json,2,2,0,1.000000,1.0,1,5,1,join,foxtrot,1,true,1.000000", csv_output)

    def test_cli_churn_outputs_event_summary(self) -> None:
        churn_path = PROJECT_ROOT / "projects" / "chord-dht-lab" / "churn_events.json"

        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "churn",
                str(RING_PATH),
                str(churn_path),
                "--finger-repair-mode",
                "all",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "churn")
        self.assertEqual(payload["events_file"], str(churn_path))
        self.assertEqual(payload["event_count"], 3)
        self.assertEqual(payload["finger_repair_mode"], "all")
        self.assertEqual(payload["steps"][0]["action"], "join")
        self.assertEqual(payload["steps"][1]["action"], "fail")
        self.assertEqual(payload["summary"]["final_node_count"], len(payload["ending_nodes"]))

    def test_cli_churn_export_outputs_markdown(self) -> None:
        churn_path = PROJECT_ROOT / "projects" / "chord-dht-lab" / "churn_events.json"

        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "churn-export",
                str(RING_PATH),
                str(churn_path),
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("# Chord churn summary", completed.stdout)
        self.assertIn("| Step | Action | Node | Rounds | Stabilized round |", completed.stdout)

    def test_cli_churn_export_outputs_csv(self) -> None:
        churn_path = PROJECT_ROOT / "projects" / "chord-dht-lab" / "churn_events.json"

        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "churn-export",
                str(RING_PATH),
                str(churn_path),
                "--format",
                "csv",
                "--finger-repair-mode",
                "all",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("step,action,node,rounds_requested,finger_repair_mode,stabilized_round,fully_stabilized", completed.stdout)
        self.assertIn("1,join,foxtrot,4,all,1,true,1.000000", completed.stdout)

    def test_cli_churn_supports_recover_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            churn_path = Path(tmpdir) / "recover_churn.json"
            churn_path.write_text(
                json.dumps(
                    [
                        {"action": "fail", "node": "charlie", "rounds": 2},
                        {"action": "recover", "node": "charlie", "rounds": 2},
                    ]
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "churn",
                    str(RING_PATH),
                    str(churn_path),
                    "--finger-repair-mode",
                    "all",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["command"], "churn")
        self.assertEqual(payload["event_count"], 2)
        self.assertEqual([step["action"] for step in payload["steps"]], ["fail", "recover"])
        self.assertEqual(payload["summary"]["fully_stabilized_steps"], 2)

    def test_cli_churn_compare_export_outputs_markdown_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            events_a = Path(tmpdir) / "events-a.json"
            events_b = Path(tmpdir) / "events-b.json"
            events_a.write_text(
                json.dumps([
                    {"action": "join", "node": "foxtrot", "rounds": 1},
                    {"action": "fail", "node": "charlie", "rounds": 1},
                ]),
                encoding="utf-8",
            )
            events_b.write_text(
                json.dumps([
                    {"action": "fail", "node": "charlie", "rounds": 1},
                    {"action": "recover", "node": "charlie", "rounds": 1},
                ]),
                encoding="utf-8",
            )

            markdown = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "churn-compare-export",
                    str(RING_PATH),
                    str(events_a),
                    str(events_b),
                    "--finger-repair-mode",
                    "all",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            csv_output = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "churn-compare-export",
                    str(RING_PATH),
                    str(events_a),
                    str(events_b),
                    "--finger-repair-mode",
                    "all",
                    "--format",
                    "csv",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("# Chord churn workload comparison", markdown.stdout)
        self.assertIn(str(events_a), markdown.stdout)
        self.assertIn("events_file,event_count,fully_stabilized_steps", csv_output.stdout)
        self.assertIn(str(events_b), csv_output.stdout)


if __name__ == "__main__":
    unittest.main()
