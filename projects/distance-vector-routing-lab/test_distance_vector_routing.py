import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
MODULE_PATH = PROJECT_DIR / "distance_vector_routing.py"
sys.path.insert(0, str(PROJECT_DIR))

from distance_vector_routing import (
    FAILURE_SCENARIOS,
    benchmark_failure_modes,
    benchmark_failure_suite,
    export_diagram,
    remove_link,
    render_failure_benchmark,
    render_failure_benchmark_suite,
    render_failure_timeline,
    run_failure_simulation,
    run_outage_simulation,
    run_simulation,
)


SQUARE_TOPOLOGY = {
    "A": {"B": 1, "D": 4},
    "B": {"A": 1, "C": 2},
    "C": {"B": 2, "D": 1},
    "D": {"A": 4, "C": 1},
}

LOOP_PRONE = {
    "A": {"B": 1},
    "B": {"A": 1, "C": 1},
    "C": {"B": 1},
}


class DistanceVectorRoutingTests(unittest.TestCase):
    def test_classic_mode_converges_to_expected_shortest_paths(self):
        result = run_simulation(SQUARE_TOPOLOGY, mode="classic")
        self.assertTrue(result["converged"])
        self.assertEqual(result["topology"]["A"], {"B": 1, "D": 4})
        self.assertEqual(result["tables"]["A"]["C"], {"destination": "C", "cost": 3, "next_hop": "B"})
        self.assertEqual(result["tables"]["D"]["B"], {"destination": "B", "cost": 3, "next_hop": "C"})

    def test_split_horizon_and_poison_reverse_still_reach_shortest_paths(self):
        classic = run_simulation(LOOP_PRONE, mode="classic")
        split = run_simulation(LOOP_PRONE, mode="split-horizon")
        poison = run_simulation(LOOP_PRONE, mode="poison-reverse")
        self.assertEqual(classic["tables"]["A"]["C"]["cost"], 2)
        self.assertEqual(split["tables"]["A"]["C"]["cost"], 2)
        self.assertEqual(poison["tables"]["A"]["C"]["cost"], 2)

    def test_triggered_strategy_matches_periodic_tables_and_tracks_active_router(self):
        periodic = run_simulation(LOOP_PRONE, mode="classic", update_strategy="periodic")
        triggered = run_simulation(LOOP_PRONE, mode="classic", update_strategy="triggered")
        self.assertEqual(triggered["update_strategy"], "triggered")
        self.assertEqual(triggered["tables"], periodic["tables"])
        self.assertEqual(triggered["history"][1]["active_routers"], ["A"])
        self.assertEqual(triggered["history"][2]["active_routers"], ["B"])

    def test_link_failure_from_converged_state_shows_count_to_infinity_in_classic_mode(self):
        failure = run_failure_simulation(LOOP_PRONE, "B", "C", mode="classic", max_rounds=20)
        history = failure["after"]["history"]
        costs = [round_state["tables"]["A"]["C"]["cost"] for round_state in history]
        self.assertEqual(costs[:5], [2, 2, 4, 4, 6])
        self.assertEqual(costs[-1], 16)
        self.assertTrue(failure["after"]["converged"])

    def test_poison_reverse_prevents_count_to_infinity_escalation_after_failure(self):
        failure = run_failure_simulation(LOOP_PRONE, "B", "C", mode="poison-reverse", max_rounds=8)
        history = failure["after"]["history"]
        costs = [round_state["tables"]["A"]["C"]["cost"] for round_state in history]
        self.assertEqual(costs[:3], [2, 2, 16])
        self.assertEqual(costs[-1], 16)

    def test_silent_router_outage_aging_expires_stale_learned_routes(self):
        result = run_outage_simulation(
            LOOP_PRONE,
            mode="classic",
            update_strategy="periodic",
            silent_routers=["B"],
            route_timeout=2,
            max_rounds=4,
        )
        history = result["after"]["history"]
        self.assertEqual(history[0]["tables"]["A"]["C"]["cost"], 2)
        self.assertEqual(history[1]["tables"]["A"]["C"]["cost"], 2)
        self.assertEqual(history[1]["route_ages"]["A"]["C"], 1)
        self.assertEqual(history[2]["tables"]["A"]["C"], {"destination": "C", "cost": 16, "next_hop": None})
        self.assertEqual(history[2]["route_ages"]["A"]["C"], 2)
        self.assertEqual(history[2]["tables"]["B"]["C"]["cost"], 1)

    def test_triggered_silent_router_omits_silent_from_active_router_schedule(self):
        result = run_simulation(
            LOOP_PRONE,
            mode="classic",
            update_strategy="triggered",
            silent_routers=["B"],
            route_timeout=2,
            max_rounds=4,
        )
        self.assertEqual(result["silent_routers"], ["B"])
        self.assertEqual(result["history"][1]["active_routers"], ["A"])
        self.assertNotIn("B", result["history"][0]["active_routers"])

    def test_remove_link_rejects_missing_edge(self):
        with self.assertRaises(ValueError):
            remove_link(LOOP_PRONE, "A", "C")

    def test_simulate_failure_cli_outputs_before_and_after(self):
        payload = json.dumps(LOOP_PRONE)
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "simulate-failure",
                "--topology",
                payload,
                "--remove-link",
                "B",
                "C",
                "--mode",
                "poison-reverse",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        output = json.loads(completed.stdout)
        self.assertEqual(output["event"], {"type": "remove-link", "left": "B", "right": "C"})
        self.assertTrue(output["after"]["starts_from_converged_before_failure"])
        self.assertEqual(output["after"]["tables"]["A"]["C"]["cost"], 16)

    def test_simulate_cli_accepts_triggered_update_strategy(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "simulate",
                "--topology",
                json.dumps(LOOP_PRONE),
                "--update-strategy",
                "triggered",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        output = json.loads(completed.stdout)
        self.assertEqual(output["update_strategy"], "triggered")
        self.assertEqual(output["history"][2]["active_routers"], ["B"])
        self.assertEqual(output["tables"]["A"]["C"]["cost"], 2)

    def test_simulate_cli_accepts_route_timeout_and_silent_routers(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "simulate-outage",
                "--topology",
                json.dumps(LOOP_PRONE),
                "--silent-routers",
                "B",
                "--route-timeout",
                "2",
                "--max-rounds",
                "4",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        output = json.loads(completed.stdout)
        self.assertEqual(output["after"]["silent_routers"], ["B"])
        self.assertEqual(output["after"]["route_timeout"], 2)
        self.assertEqual(output["after"]["history"][2]["tables"]["A"]["C"]["cost"], 16)

    def test_invalid_topology_is_rejected(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "simulate",
                "--topology",
                '{"A": {"B": 1}, "B": {}}',
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("topology must be symmetric", completed.stderr)

    def test_export_topology_mermaid_contains_weighted_links(self):
        diagram = export_diagram(
            SQUARE_TOPOLOGY,
            snapshot="topology",
            diagram_format="mermaid",
            mode="classic",
            infinity=16,
            max_rounds=20,
            router=None,
        )
        self.assertIn("graph LR", diagram)
        self.assertIn("A <-->|1| B", diagram)
        self.assertIn("C <-->|1| D", diagram)

    def test_export_routes_dot_contains_router_cluster_and_next_hop(self):
        diagram = export_diagram(
            SQUARE_TOPOLOGY,
            snapshot="routes",
            diagram_format="dot",
            mode="classic",
            infinity=16,
            max_rounds=20,
            router="A",
        )
        self.assertIn("digraph DistanceVectorRoutes", diagram)
        self.assertIn('label="Router A"', diagram)
        self.assertIn('A::C', diagram)
        self.assertIn('via B', diagram)

    def test_render_failure_timeline_markdown_contains_round_rows(self):
        failure = run_failure_simulation(LOOP_PRONE, "B", "C", mode="classic", max_rounds=20)
        timeline = render_failure_timeline(failure, destination="C", diagram_format="markdown", routers=["A", "B"])
        self.assertIn("| round | A → C | B → C |", timeline)
        self.assertIn("| 2 | cost=4, via B | cost=3, via A |", timeline)
        self.assertIn("| 14 | cost=16, via unreachable | cost=15, via A |", timeline)
        self.assertIn("| 15 | cost=16, via unreachable | cost=16, via unreachable |", timeline)

    def test_timeline_includes_age_annotations_when_timeout_enabled(self):
        failure = run_failure_simulation(
            LOOP_PRONE,
            "B",
            "C",
            mode="classic",
            max_rounds=6,
            silent_routers=["C"],
            route_timeout=2,
        )
        timeline = render_failure_timeline(failure, destination="C", diagram_format="markdown", routers=["A"])
        self.assertIn("age=", timeline)

    def test_export_timeline_cli_supports_mermaid(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "export-timeline",
                "--topology",
                json.dumps(LOOP_PRONE),
                "--remove-link",
                "B",
                "C",
                "--destination",
                "C",
                "--routers",
                "A",
                "B",
                "--format",
                "mermaid",
                "--mode",
                "classic",
                "--max-rounds",
                "6",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("sequenceDiagram", completed.stdout)
        self.assertIn("participant A as A", completed.stdout)
        self.assertIn("Note over A: C cost=6 via B", completed.stdout)

    def test_failure_benchmark_compares_modes_and_strategies(self):
        benchmark = benchmark_failure_modes(
            LOOP_PRONE,
            "B",
            "C",
            router="A",
            destination="C",
            max_rounds=20,
        )
        self.assertEqual(benchmark["benchmark"], "failure-mode-comparison")
        self.assertEqual(benchmark["tracked_route"], {"router": "A", "destination": "C"})
        self.assertEqual(len(benchmark["rows"]), 6)

        rows = {(row["mode"], row["update_strategy"]): row for row in benchmark["rows"]}
        self.assertGreater(rows[("classic", "periodic")]["first_unreachable_round"], 2)
        self.assertEqual(rows[("poison-reverse", "periodic")]["first_unreachable_round"], 2)
        self.assertLess(
            rows[("poison-reverse", "periodic")]["max_finite_cost_seen"],
            rows[("classic", "periodic")]["max_finite_cost_seen"],
        )
        self.assertIn(benchmark["summary"]["fastest_reconvergence"]["update_strategy"], {"periodic", "triggered"})

    def test_render_failure_benchmark_supports_markdown_and_csv(self):
        benchmark = benchmark_failure_modes(
            LOOP_PRONE,
            "B",
            "C",
            router="A",
            destination="C",
            modes=["classic", "poison-reverse"],
            update_strategies=["periodic"],
            max_rounds=20,
        )
        markdown = render_failure_benchmark(benchmark, output_format="markdown")
        csv_text = render_failure_benchmark(benchmark, output_format="csv")
        self.assertIn("# Failure benchmark for A → C", markdown)
        self.assertIn("| classic | periodic |", markdown)
        self.assertIn("mode,update_strategy,converged", csv_text)
        self.assertNotIn("\r\n", csv_text)
        self.assertIn("poison-reverse,periodic", csv_text)

    def test_failure_benchmark_deduplicates_requested_modes_and_strategies(self):
        benchmark = benchmark_failure_modes(
            LOOP_PRONE,
            "B",
            "C",
            router="A",
            destination="C",
            modes=["classic", "classic"],
            update_strategies=["periodic", "periodic"],
            max_rounds=20,
        )
        self.assertEqual(benchmark["modes"], ["classic"])
        self.assertEqual(benchmark["update_strategies"], ["periodic"])
        self.assertEqual(len(benchmark["rows"]), 1)

    def test_benchmark_failure_cli_supports_csv(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "benchmark-failure",
                "--topology",
                json.dumps(LOOP_PRONE),
                "--remove-link",
                "B",
                "C",
                "--router",
                "A",
                "--destination",
                "C",
                "--format",
                "csv",
                "--max-rounds",
                "20",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("mode,update_strategy,converged", completed.stdout)
        self.assertIn("classic,periodic", completed.stdout)

    def test_failure_suite_uses_curated_scenarios_and_scorecard(self):
        suite = benchmark_failure_suite(
            scenario_names=["count-to-infinity-line", "square-detour"],
            max_rounds=20,
        )
        self.assertEqual(suite["suite"], "portfolio-failure-scenarios")
        self.assertEqual(suite["scenario_names"], ["count-to-infinity-line", "square-detour"])
        self.assertEqual(len(suite["scenarios"]), 2)
        self.assertEqual(len(suite["rows"]), 12)
        self.assertEqual(len(suite["scorecard"]), 6)

        first_scenario = suite["scenarios"][0]
        self.assertEqual(first_scenario["tracked_route"], {"router": "A", "destination": "C"})
        self.assertEqual(first_scenario["event"], {"type": "remove-link", "left": "B", "right": "C"})

    def test_failure_suite_rejects_unknown_scenarios(self):
        with self.assertRaises(ValueError):
            benchmark_failure_suite(scenario_names=["does-not-exist"])

    def test_render_failure_suite_supports_markdown_and_csv(self):
        suite = benchmark_failure_suite(
            scenario_names=["ring-isolation"],
            modes=["classic", "poison-reverse"],
            update_strategies=["periodic"],
            max_rounds=20,
        )
        markdown = render_failure_benchmark_suite(suite, output_format="markdown")
        csv_text = render_failure_benchmark_suite(suite, output_format="csv")
        self.assertIn("# Failure benchmark suite", markdown)
        self.assertIn("Scenario: ring-isolation", markdown)
        self.assertIn("scenario,scenario_description,removed_link", csv_text)
        self.assertNotIn("\r\n", csv_text)
        self.assertIn("ring-isolation", csv_text)

    def test_benchmark_failure_suite_cli_supports_csv(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "benchmark-failure-suite",
                "--scenarios",
                "count-to-infinity-line",
                "square-detour",
                "--format",
                "csv",
                "--max-rounds",
                "20",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("scenario,scenario_description,removed_link", completed.stdout)
        self.assertIn("count-to-infinity-line", completed.stdout)
        self.assertIn("square-detour", completed.stdout)

    def test_curated_failure_scenarios_stay_unique(self):
        self.assertEqual(sorted(FAILURE_SCENARIOS), [
            "count-to-infinity-line",
            "five-node-bypass",
            "ring-isolation",
            "square-detour",
        ])


if __name__ == "__main__":
    unittest.main()
