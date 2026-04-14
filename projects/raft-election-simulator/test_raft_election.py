import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from raft_election import RaftElectionSimulator, Role, run_scenario


class RaftElectionSimulatorTests(unittest.TestCase):
    def test_lowest_timeout_node_becomes_leader(self):
        simulator = RaftElectionSimulator(
            ["n1", "n2", "n3", "n4", "n5"],
            {"n1": 3, "n2": 5, "n3": 6, "n4": 7, "n5": 8},
        )

        simulator.run(4)
        summary = simulator.summary()

        self.assertEqual(summary["leaders"], ["n1"])
        self.assertEqual(summary["nodes"]["n1"]["role"], Role.LEADER.value)
        self.assertTrue(any(event["event"] == "leader_elected" for event in summary["events"]))

    def test_isolated_candidate_retries_until_majority_exists(self):
        simulator = RaftElectionSimulator(
            ["n1", "n2", "n3", "n4", "n5"],
            {"n1": 3, "n2": 5, "n3": 7, "n4": 8, "n5": 9},
        )

        simulator.isolate("n1")
        simulator.run(4)
        self.assertEqual(simulator.summary()["leaders"], [])

        simulator.run(2)
        summary = simulator.summary()

        self.assertEqual(summary["leaders"], ["n2"])
        self.assertEqual(summary["nodes"]["n2"]["role"], Role.LEADER.value)
        self.assertTrue(any(event["event"] == "vote_blocked" for event in summary["events"]))

    def test_leader_steps_down_when_higher_term_node_returns(self):
        simulator = RaftElectionSimulator(
            ["n1", "n2", "n3", "n4", "n5"],
            {"n1": 3, "n2": 5, "n3": 7, "n4": 9, "n5": 11},
        )

        simulator.run(4)
        self.assertEqual(simulator.summary()["leaders"], ["n1"])

        simulator.isolate("n1")
        simulator.run(8)
        self.assertEqual(simulator.summary()["leaders"], ["n1", "n2"])

        simulator.heal("n1")
        simulator.run(2)
        summary = simulator.summary()

        self.assertEqual(summary["leaders"], ["n2"])
        self.assertEqual(summary["nodes"]["n1"]["role"], Role.FOLLOWER.value)
        self.assertTrue(any(event["event"] == "leader_stale" for event in summary["events"]))

    def test_cli_emits_json_summary(self):
        scenario = {
            "nodes": ["n1", "n2", "n3"],
            "election_timeouts": {"n1": 3, "n2": 5, "n3": 7},
            "steps": [{"action": "run", "ticks": 5}],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            scenario_path = Path(tmpdir) / "scenario.json"
            scenario_path.write_text(json.dumps(scenario))
            result = subprocess.run(
                [
                    "python3",
                    "projects/raft-election-simulator/raft_election.py",
                    "--scenario",
                    str(scenario_path),
                ],
                cwd=Path(__file__).resolve().parents[2],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(payload["leaders"], ["n1"])

    def test_run_scenario_handles_partition_recovery(self):
        summary = run_scenario(
            {
                "nodes": ["n1", "n2", "n3", "n4", "n5"],
                "election_timeouts": {"n1": 3, "n2": 5, "n3": 6, "n4": 8, "n5": 10},
                "steps": [
                    {"action": "run", "ticks": 4},
                    {"action": "isolate", "node": "n1"},
                    {"action": "run", "ticks": 8},
                    {"action": "heal", "node": "n1"},
                    {"action": "run", "ticks": 2},
                ],
            }
        )

        self.assertEqual(summary["leaders"], ["n2"])
        self.assertGreaterEqual(len(summary["events"]), 10)


if __name__ == "__main__":
    unittest.main()
