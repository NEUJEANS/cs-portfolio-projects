import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
MODULE_PATH = PROJECT_DIR / "distance_vector_routing.py"
sys.path.insert(0, str(PROJECT_DIR))

from distance_vector_routing import remove_link, run_simulation


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

    def test_link_failure_marks_unreachable_destinations(self):
        broken = remove_link(LOOP_PRONE, "B", "C")
        result = run_simulation(broken, mode="poison-reverse", infinity=16)
        self.assertEqual(result["history"][0]["changed"], False)
        self.assertEqual(result["tables"]["A"]["C"], {"destination": "C", "cost": 16, "next_hop": None})
        self.assertEqual(result["tables"]["B"]["C"], {"destination": "C", "cost": 16, "next_hop": None})

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
        self.assertEqual(output["after"]["tables"]["A"]["C"]["cost"], 16)

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


if __name__ == "__main__":
    unittest.main()
