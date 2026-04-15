import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from raft_election import LogEntry, RaftElectionSimulator, Role, run_scenario


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

    def test_client_command_replicates_and_commits_on_majority(self):
        simulator = RaftElectionSimulator(
            ["n1", "n2", "n3", "n4", "n5"],
            {"n1": 3, "n2": 5, "n3": 6, "n4": 7, "n5": 8},
        )

        simulator.run(4)
        simulator.append_client_command("set x=1")
        summary = simulator.summary()

        for node in summary["nodes"].values():
            self.assertEqual(node["commit_index"], 1)
            self.assertEqual(node["log"], [{"term": 1, "command": "set x=1"}])
        self.assertTrue(any(event["event"] == "commit_advanced" for event in summary["events"]))

    def test_partitioned_followers_delay_commit_until_healed(self):
        simulator = RaftElectionSimulator(
            ["n1", "n2", "n3", "n4", "n5"],
            {"n1": 3, "n2": 5, "n3": 6, "n4": 7, "n5": 8},
        )

        simulator.run(4)
        simulator.isolate("n4")
        simulator.isolate("n5")
        simulator.append_client_command("set x=2")
        summary = simulator.summary()

        self.assertEqual(summary["nodes"]["n1"]["commit_index"], 1)
        self.assertEqual(summary["nodes"]["n4"]["commit_index"], 0)
        self.assertEqual(summary["nodes"]["n5"]["log"], [])

        simulator.heal("n4")
        simulator.heal("n5")
        simulator.run(2)
        healed_summary = simulator.summary()

        self.assertEqual(healed_summary["nodes"]["n4"]["commit_index"], 1)
        self.assertEqual(healed_summary["nodes"]["n5"]["commit_index"], 1)
        self.assertTrue(any(event["event"] == "commit_replicated" for event in healed_summary["events"]))

    def test_conflicting_follower_log_is_repaired_via_backtracking(self):
        simulator = RaftElectionSimulator(
            ["n1", "n2", "n3", "n4", "n5"],
            {"n1": 3, "n2": 5, "n3": 6, "n4": 7, "n5": 8},
        )

        simulator.run(4)
        simulator.append_client_command("set x=1")
        simulator.append_client_command("set y=2")
        simulator.isolate("n3")
        simulator.nodes["n3"].log = [LogEntry(term=1, command="set x=1"), LogEntry(term=99, command="set rogue=999")]
        simulator.nodes["n3"].commit_index = 1

        simulator.heal("n3")
        simulator.run(2)
        repaired_summary = simulator.summary()

        self.assertEqual(
            repaired_summary["nodes"]["n3"]["log"],
            [
                {"term": 1, "command": "set x=1"},
                {"term": 1, "command": "set y=2"},
            ],
        )
        self.assertEqual(repaired_summary["nodes"]["n3"]["commit_index"], 2)
        self.assertTrue(any(event["event"] == "append_rejected" for event in repaired_summary["events"]))

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

    def test_run_scenario_supports_client_write_steps(self):
        summary = run_scenario(
            {
                "nodes": ["n1", "n2", "n3"],
                "election_timeouts": {"n1": 3, "n2": 5, "n3": 7},
                "steps": [
                    {"action": "run", "ticks": 4},
                    {"action": "client-write", "command": "set theme=dark"},
                ],
            }
        )

        self.assertEqual(summary["nodes"]["n1"]["commit_index"], 1)
        self.assertEqual(summary["nodes"]["n2"]["log"][0]["command"], "set theme=dark")

    def test_run_scenario_supports_force_log_conflict_demo(self):
        summary = run_scenario(
            {
                "nodes": ["n1", "n2", "n3"],
                "election_timeouts": {"n1": 3, "n2": 5, "n3": 7},
                "steps": [
                    {"action": "run", "ticks": 4},
                    {"action": "client-write", "command": "set x=1"},
                    {"action": "client-write", "command": "set y=2"},
                    {"action": "isolate", "node": "n3"},
                    {
                        "action": "force-log",
                        "node": "n3",
                        "entries": [
                            {"term": 1, "command": "set x=1"},
                            {"term": 99, "command": "set rogue=999"},
                        ],
                        "commit_index": 1,
                    },
                    {"action": "heal", "node": "n3"},
                    {"action": "run", "ticks": 2},
                ],
            }
        )

        self.assertEqual(summary["nodes"]["n3"]["log"][-1]["command"], "set y=2")
        self.assertFalse(any(item["command"] == "set rogue=999" for item in summary["nodes"]["n3"]["log"]))
        self.assertTrue(any(event["event"] == "append_rejected" for event in summary["events"]))
        self.assertTrue(any(event["event"] == "log_forced" for event in summary["events"]))

    def test_run_scenario_validates_required_step_fields(self):
        with self.assertRaisesRegex(ValueError, "missing fields: command"):
            run_scenario(
                {
                    "nodes": ["n1", "n2", "n3"],
                    "election_timeouts": {"n1": 3, "n2": 5, "n3": 7},
                    "steps": [{"action": "client-write"}],
                }
            )


if __name__ == "__main__":
    unittest.main()
