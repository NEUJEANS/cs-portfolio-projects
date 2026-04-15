import json
import subprocess
import sys
import unittest
from pathlib import Path

from chang_roberts_leader_election import RingElectionSimulator, render_mermaid_sequence

PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "chang_roberts_leader_election.py"


def run_cli_raw(*args: str) -> str:
    completed = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=PROJECT_DIR, capture_output=True, check=True, text=True)
    return completed.stdout


def run_cli(*args: str) -> dict:
    return json.loads(run_cli_raw(*args))


class ChangRobertsLeaderElectionTests(unittest.TestCase):
    def test_elects_highest_process_id(self) -> None:
        result = RingElectionSimulator([4, 1, 7, 3]).simulate(initiator=1)
        self.assertEqual(result["leader"], 7)
        self.assertEqual(result["max_id"], 7)
        self.assertEqual(result["mode"], "single-initiator")
        self.assertTrue(any(step["action"] == "replace" for step in result["trace"]))

    def test_skips_failed_nodes_and_elects_highest_active_id(self) -> None:
        result = RingElectionSimulator([9, 2, 14, 5, 11]).simulate(initiator=2, failed=[14, 5])
        self.assertEqual(result["active_ring"], [9, 2, 11])
        self.assertEqual(result["leader"], 11)
        self.assertEqual(result["announcement_messages"], 2)

    def test_multi_initiator_lockstep_elects_same_highest_process_id(self) -> None:
        result = RingElectionSimulator([8, 3, 12, 6]).simulate_multi_initiator(initiators=[3, 6])
        self.assertEqual(result["leader"], 12)
        self.assertEqual(result["initiators"], [3, 6])
        self.assertEqual(result["mode"], "multi-initiator-lockstep")
        self.assertGreaterEqual(result["rounds"], 1)
        self.assertTrue(any(step["round"] == 1 for step in result["trace"]))

    def test_multi_initiator_can_skip_failed_nodes(self) -> None:
        result = RingElectionSimulator([20, 4, 17, 9, 15]).simulate_multi_initiator(initiators=[4, 9], failed=[17])
        self.assertEqual(result["active_ring"], [20, 4, 9, 15])
        self.assertEqual(result["leader"], 20)
        self.assertEqual(result["announcement_messages"], 3)

    def test_rejects_invalid_inputs(self) -> None:
        simulator = RingElectionSimulator([1, 2, 3])
        with self.assertRaisesRegex(ValueError, "initiator must belong to the ring"):
            simulator.simulate(initiator=99)
        with self.assertRaisesRegex(ValueError, "need at least two active nodes"):
            simulator.simulate(initiator=1, failed=[2, 3])

    def test_rejects_invalid_multi_initiator_inputs(self) -> None:
        simulator = RingElectionSimulator([5, 9, 2])
        with self.assertRaisesRegex(ValueError, "initiators must be unique"):
            simulator.simulate_multi_initiator(initiators=[5, 5])
        with self.assertRaisesRegex(ValueError, "every initiator must belong to the ring"):
            simulator.simulate_multi_initiator(initiators=[5, 42])
        with self.assertRaisesRegex(ValueError, "every initiator must be active"):
            simulator.simulate_multi_initiator(initiators=[5, 9], failed=[9])

    def test_mermaid_renderer_captures_election_and_announcement(self) -> None:
        result = RingElectionSimulator([8, 3, 12, 6]).simulate(initiator=3)
        diagram = render_mermaid_sequence(result)
        self.assertIn("sequenceDiagram", diagram)
        self.assertIn("participant P3 as 3", diagram)
        self.assertIn("election #1", diagram)
        self.assertIn("elect leader 12", diagram)
        self.assertIn("leader 12 announces victory", diagram)
        self.assertIn("announce #1: leader 12", diagram)

    def test_mermaid_renderer_mentions_multi_initiator_lockstep(self) -> None:
        result = RingElectionSimulator([8, 3, 12, 6]).simulate_multi_initiator(initiators=[3, 6])
        diagram = render_mermaid_sequence(result)
        self.assertIn("initiators=3, 6 (lockstep)", diagram)
        self.assertIn("round 1", diagram)

    def test_contention_benchmark_compares_all_initiator_counts(self) -> None:
        result = RingElectionSimulator([8, 3, 12, 6]).benchmark_contention()
        self.assertEqual(result["mode"], "contention-benchmark")
        self.assertEqual([row["initiator_count"] for row in result["rows"]], [1, 2, 3, 4])
        self.assertEqual(result["summary"]["evaluated_combinations"], 15)
        self.assertTrue(all(row["average_total_messages"] >= row["average_election_messages"] for row in result["rows"]))

    def test_cli_outputs_expected_summary(self) -> None:
        result = run_cli("--ring", "8", "3", "12", "6", "--initiator", "3")
        self.assertEqual(result["leader"], 12)
        self.assertEqual(result["election_messages"], len(result["trace"]))
        self.assertEqual(result["message_count"], result["election_messages"] + result["announcement_messages"])

    def test_cli_pretty_mode_and_failure_path(self) -> None:
        result = run_cli("--ring", "10", "4", "15", "7", "--initiator", "4", "--failed", "15", "--pretty")
        self.assertEqual(result["leader"], 10)
        self.assertEqual(result["failed"], [15])
        self.assertTrue(all(step["phase"] == "announce" for step in result["announcement_trace"]))

    def test_cli_can_embed_visualization_in_json(self) -> None:
        result = run_cli("--ring", "8", "3", "12", "6", "--initiator", "3", "--include-visualization")
        self.assertIn("visualizations", result)
        self.assertIn("mermaid_sequence", result["visualizations"])
        self.assertIn("sequenceDiagram", result["visualizations"]["mermaid_sequence"])

    def test_cli_visualization_only_mode(self) -> None:
        output = run_cli_raw("--ring", "8", "3", "12", "6", "--initiator", "3", "--visualization-only", "mermaid")
        self.assertIn("sequenceDiagram", output)
        self.assertIn("elect leader 12", output)

    def test_cli_supports_multi_initiator_mode(self) -> None:
        result = run_cli("--ring", "8", "3", "12", "6", "--initiators", "3", "6", "--include-visualization")
        self.assertEqual(result["leader"], 12)
        self.assertEqual(result["initiators"], [3, 6])
        self.assertEqual(result["mode"], "multi-initiator-lockstep")
        self.assertIn("mermaid_sequence", result["visualizations"])

    def test_cli_supports_contention_benchmark_mode(self) -> None:
        result = run_cli("--ring", "8", "3", "12", "6", "--benchmark-contention")
        self.assertEqual(result["mode"], "contention-benchmark")
        self.assertEqual(result["summary"]["best_average_initiator_count"], 1)
        self.assertEqual(result["summary"]["evaluated_combinations"], 15)


if __name__ == "__main__":
    unittest.main()
