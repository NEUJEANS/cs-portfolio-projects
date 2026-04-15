import json
import subprocess
import sys
import unittest
from pathlib import Path

from distributed_snapshot_lab import DistributedBank, parse_balances, parse_marker_delay, parse_transfer


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "distributed_snapshot_lab.py"


def run_cli(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


class DistributedSnapshotLabTests(unittest.TestCase):
    def test_transfer_and_delivery_preserve_total_money(self) -> None:
        bank = DistributedBank({"A": 10, "B": 8, "C": 7})
        bank.transfer("A", "B", 3, "invoice")
        bank.transfer("C", "A", 2, "refund")
        self.assertEqual(bank.total_money(), 25)
        bank.deliver("A", "B")
        bank.deliver("C", "A")
        self.assertEqual(bank.current_balances(), {"A": 9, "B": 11, "C": 5})
        self.assertEqual(bank.total_money(), 25)

    def test_snapshot_captures_in_flight_messages_when_marker_is_delayed(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        bank.transfer("A", "B", 3, "ab-1")
        bank.transfer("C", "B", 2, "cb-1")

        result = bank.snapshot("A", marker_delay_overrides={"A->B": 0, "C->B": 2})

        self.assertTrue(result["consistent"])
        self.assertEqual(result["snapshot_total"], 30)
        self.assertEqual(result["channel_messages"]["C->B"][0]["label"], "cb-1")
        self.assertNotIn("A->B", result["channel_messages"])

    def test_snapshot_after_delivery_has_no_recorded_in_flight_message(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        bank.transfer("A", "B", 4, "ab-1")
        bank.deliver("A", "B")

        result = bank.snapshot("A")

        self.assertEqual(result["channel_messages"], {})
        self.assertTrue(result["consistent"])
        self.assertEqual(result["snapshot_total"], 20)

    def test_insufficient_balance_is_rejected(self) -> None:
        bank = DistributedBank({"A": 2, "B": 5})
        with self.assertRaisesRegex(ValueError, "insufficient balance"):
            bank.transfer("A", "B", 3, "too-much")

    def test_parsers_validate_cli_inputs(self) -> None:
        self.assertEqual(parse_balances('{"A": 4, "B": 6}'), {"A": 4, "B": 6})
        self.assertEqual(parse_transfer("A:B:3:rent"), ("A", "B", 3, "rent"))
        self.assertEqual(parse_marker_delay("C->B=2"), ("C->B", 2))

    def test_cli_simulation_reports_consistent_snapshot(self) -> None:
        result = run_cli(
            "simulate",
            "--balances",
            '{"A": 10, "B": 10, "C": 10}',
            "--send",
            "A:B:3:ab-1",
            "--send",
            "C:B:2:cb-1",
            "--snapshot",
            "A",
            "--marker-delay",
            "A->B=0",
            "--marker-delay",
            "C->B=2",
        )

        self.assertTrue(result["consistent"])
        self.assertEqual(result["snapshot_total"], 30)
        self.assertEqual(result["balances"], {"A": 7, "B": 13, "C": 8})
        self.assertEqual(result["channel_messages"]["C->B"][0]["amount"], 2)


    def test_unknown_marker_delay_channel_is_rejected(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        with self.assertRaisesRegex(ValueError, "unknown process"):
            bank.snapshot("A", marker_delay_overrides={"A->C": 1})

    def test_unknown_delivery_channel_fails(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        with self.assertRaisesRegex(ValueError, "no in-flight transfer"):
            bank.deliver("A", "B")


if __name__ == "__main__":
    unittest.main()
