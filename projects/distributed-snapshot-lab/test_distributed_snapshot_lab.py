import json
import subprocess
import sys
import unittest
from pathlib import Path

from distributed_snapshot_lab import (
    DistributedBank,
    parse_balances,
    parse_marker_delay,
    parse_scoped_marker_delay,
    parse_script,
    parse_snapshot_spec,
    parse_snapshot_specs,
    parse_transfer,
    render_mermaid,
)


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "distributed_snapshot_lab.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )


def run_cli_json(*args: str) -> dict:
    return json.loads(run_cli(*args).stdout)


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

    def test_failed_receiver_blocks_delivery_until_recovery(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        bank.transfer("A", "B", 4, "salary")
        bank.fail_process("B", reason="maintenance")

        with self.assertRaisesRegex(ValueError, "process B is down"):
            bank.deliver("A", "B")

        bank.recover_process("B")
        bank.deliver("A", "B")
        self.assertEqual(bank.current_balances(), {"A": 6, "B": 14})
        self.assertEqual(bank.total_money(), 20)

    def test_send_to_failed_receiver_stays_queued_until_recovery(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        bank.fail_process("B")
        bank.transfer("A", "B", 4, "queued")

        self.assertEqual(bank.total_money(), 20)
        self.assertEqual(len(bank.in_flight[bank.channel_name("A", "B")]), 1)
        with self.assertRaisesRegex(ValueError, "process B is down"):
            bank.deliver("A", "B")

    def test_failed_process_cannot_send_or_start_snapshot(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        bank.fail_process("A")

        with self.assertRaisesRegex(ValueError, "process A is down"):
            bank.transfer("A", "B", 1, "oops")
        with self.assertRaisesRegex(ValueError, "process A is down"):
            bank.snapshot("A")

    def test_snapshot_records_process_statuses(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        bank.transfer("A", "B", 3, "ab-1")
        bank.fail_process("C", reason="reboot")

        result = bank.snapshot("A", marker_delay_overrides={"A->B": 0, "C->B": 2})

        self.assertEqual(result["process_statuses"], {"A": "up", "B": "up", "C": "down"})
        self.assertTrue(result["consistent"])

    def test_parsers_validate_cli_inputs(self) -> None:
        self.assertEqual(parse_balances('{"A": 4, "B": 6}'), {"A": 4, "B": 6})
        self.assertEqual(parse_transfer("A:B:3:rent"), ("A", "B", 3, "rent"))
        self.assertEqual(parse_marker_delay("C->B=2"), ("C->B", 2))
        self.assertEqual(parse_snapshot_spec("blue:A"), ("blue", "A"))
        self.assertEqual(parse_snapshot_specs(["blue:A", "green:C"]), {"blue": "A", "green": "C"})
        self.assertEqual(parse_scoped_marker_delay("blue:C->B=2"), ("blue", "C->B", 2))
        self.assertEqual(
            parse_script('[{"op": "fail", "process": "B"}, {"op": "snapshot", "initiator": "A"}]'),
            [{"op": "fail", "process": "B"}, {"op": "snapshot", "initiator": "A"}],
        )

    def test_cli_simulation_reports_consistent_snapshot(self) -> None:
        result = run_cli_json(
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

    def test_cli_simulation_supports_failure_and_recovery_flags(self) -> None:
        result = run_cli_json(
            "simulate",
            "--balances",
            '{"A": 10, "B": 10}',
            "--send",
            "A:B:4:salary",
            "--fail",
            "B",
            "--recover",
            "B",
            "--deliver",
            "A:B",
            "--snapshot",
            "A",
        )

        self.assertEqual(result["process_statuses"], {"A": "up", "B": "up"})
        self.assertEqual(result["channel_messages"], {})
        self.assertTrue(result["consistent"])

    def test_concurrent_snapshots_keep_named_results_separate(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        bank.transfer("A", "B", 3, "ab-1")
        bank.transfer("C", "B", 2, "cb-1")

        result = bank.concurrent_snapshots(
            {"blue": "A", "green": "C"},
            marker_delay_overrides={
                "blue": {"A->B": 0, "C->B": 2},
                "green": {"C->B": 0, "A->B": 2},
            },
        )

        self.assertTrue(result["all_consistent"])
        self.assertEqual(result["snapshots"]["blue"]["channel_messages"]["C->B"][0]["label"], "cb-1")
        self.assertEqual(result["snapshots"]["green"]["channel_messages"]["A->B"][0]["label"], "ab-1")
        self.assertEqual(result["snapshots"]["blue"]["snapshot_id"], "blue")
        self.assertEqual(result["snapshots"]["green"]["snapshot_id"], "green")

    def test_cli_concurrent_snapshot_reports_multiple_snapshot_ids(self) -> None:
        result = run_cli_json(
            "concurrent",
            "--balances",
            '{"A": 10, "B": 10, "C": 10}',
            "--send",
            "A:B:3:ab-1",
            "--send",
            "C:B:2:cb-1",
            "--snapshot",
            "blue:A",
            "--snapshot",
            "green:C",
            "--marker-delay",
            "blue:A->B=0",
            "--marker-delay",
            "blue:C->B=2",
            "--marker-delay",
            "green:C->B=0",
            "--marker-delay",
            "green:A->B=2",
        )

        self.assertTrue(result["all_consistent"])
        self.assertIn("blue", result["snapshots"])
        self.assertIn("green", result["snapshots"])
        self.assertEqual(result["snapshots"]["blue"]["channel_messages"]["C->B"][0]["amount"], 2)
        self.assertEqual(result["snapshots"]["green"]["channel_messages"]["A->B"][0]["amount"], 3)

    def test_script_runner_supports_failure_recovery_and_snapshot_steps(self) -> None:
        result = run_cli_json(
            "script",
            "--balances",
            '{"A": 10, "B": 10, "C": 10}',
            "--marker-delay",
            "C->B=2",
            "--script",
            json.dumps(
                [
                    {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                    {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                    {"op": "fail", "process": "B", "reason": "reboot"},
                    {"op": "snapshot", "snapshot_id": "during-outage", "initiator": "A"},
                    {"op": "recover", "process": "B"},
                    {"op": "deliver", "sender": "A", "receiver": "B"},
                    {"op": "deliver", "sender": "C", "receiver": "B"},
                    {"op": "snapshot", "snapshot_id": "after-recovery", "initiator": "A"},
                ]
            ),
        )

        self.assertEqual([snap["snapshot_id"] for snap in result["snapshots"]], ["during-outage", "after-recovery"])
        self.assertEqual(result["snapshots"][0]["process_statuses"]["B"], "down")
        self.assertEqual(result["snapshots"][1]["process_statuses"]["B"], "up")
        self.assertEqual(result["balances"], {"A": 7, "B": 15, "C": 8})
        self.assertEqual(result["in_flight"], {})
        self.assertEqual(result["system_total"], 30)

    def test_mermaid_render_contains_markers_balances_statuses_and_channel_state(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        bank.transfer("A", "B", 3, "ab-1")
        bank.transfer("C", "B", 2, "cb-1")
        bank.fail_process("C", reason="maintenance")
        result = bank.snapshot("A", marker_delay_overrides={"A->B": 0, "C->B": 2})
        result["snapshot_id"] = "blue"

        diagram = render_mermaid(result, bank.processes)

        self.assertIn("sequenceDiagram", diagram)
        self.assertIn("participant A", diagram)
        self.assertIn("A->>B: transfer 3 (ab-1)", diagram)
        self.assertIn("A-->>B: marker t=0", diagram)
        self.assertIn("Note over C: FAIL (maintenance)", diagram)
        self.assertIn("Note over A: blue starts", diagram)
        self.assertIn("Note over A,B,C: snapshot balances A=7, B=13, C=8", diagram)
        self.assertIn("Note over A,B,C: process status A=up, B=up, C=down", diagram)
        self.assertIn("Note over C,B: recorded in-flight on C->B 2 (cb-1)", diagram)

    def test_cli_mermaid_output_switches_format(self) -> None:
        completed = run_cli(
            "simulate",
            "--balances",
            '{"A": 10, "B": 10}',
            "--send",
            "A:B:4:salary",
            "--snapshot",
            "A",
            "--output",
            "mermaid",
        )

        self.assertTrue(completed.stdout.startswith("sequenceDiagram\n"))
        self.assertNotIn('"balances"', completed.stdout)
        self.assertIn("snapshot starts", completed.stdout)

    def test_unknown_marker_delay_channel_is_rejected(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        with self.assertRaisesRegex(ValueError, "unknown process"):
            bank.snapshot("A", marker_delay_overrides={"A->C": 1})

    def test_concurrent_snapshot_requires_non_empty_snapshot_ids(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        with self.assertRaisesRegex(ValueError, "non-empty"):
            bank.concurrent_snapshots({"   ": "A"})

    def test_duplicate_snapshot_ids_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate snapshot id"):
            parse_snapshot_specs(["blue:A", "blue:C"])

    def test_unknown_scoped_marker_delay_snapshot_is_rejected_by_cli(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "concurrent",
                "--balances",
                '{"A": 10, "B": 10}',
                "--snapshot",
                "blue:A",
                "--marker-delay",
                "green:A->B=1",
            ],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unknown snapshot id", completed.stderr)

    def test_unknown_delivery_channel_fails(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        with self.assertRaisesRegex(ValueError, "no in-flight transfer"):
            bank.deliver("A", "B")


if __name__ == "__main__":
    unittest.main()
