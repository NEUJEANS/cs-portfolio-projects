import json
import subprocess
import sys
import unittest
from pathlib import Path

from chang_roberts_leader_election import RingElectionSimulator

PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "chang_roberts_leader_election.py"


def run_cli(*args: str) -> dict:
    completed = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=PROJECT_DIR, capture_output=True, check=True, text=True)
    return json.loads(completed.stdout)


class ChangRobertsLeaderElectionTests(unittest.TestCase):
    def test_elects_highest_process_id(self) -> None:
        result = RingElectionSimulator([4, 1, 7, 3]).simulate(initiator=1)
        self.assertEqual(result["leader"], 7)
        self.assertEqual(result["max_id"], 7)
        self.assertTrue(any(step["action"] == "replace" for step in result["trace"]))

    def test_skips_failed_nodes_and_elects_highest_active_id(self) -> None:
        result = RingElectionSimulator([9, 2, 14, 5, 11]).simulate(initiator=2, failed=[14, 5])
        self.assertEqual(result["active_ring"], [9, 2, 11])
        self.assertEqual(result["leader"], 11)
        self.assertEqual(result["announcement_messages"], 2)

    def test_rejects_invalid_inputs(self) -> None:
        simulator = RingElectionSimulator([1, 2, 3])
        with self.assertRaisesRegex(ValueError, "initiator must belong to the ring"):
            simulator.simulate(initiator=99)
        with self.assertRaisesRegex(ValueError, "need at least two active nodes"):
            simulator.simulate(initiator=1, failed=[2, 3])

    def test_rejects_failed_initiator_and_unknown_failed_id(self) -> None:
        simulator = RingElectionSimulator([5, 9, 2])
        with self.assertRaisesRegex(ValueError, "initiator must be active"):
            simulator.simulate(initiator=9, failed=[9])
        with self.assertRaisesRegex(ValueError, "failed ids must belong to the ring"):
            simulator.simulate(initiator=5, failed=[42])

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


if __name__ == "__main__":
    unittest.main()
