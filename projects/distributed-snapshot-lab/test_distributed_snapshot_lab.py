import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import distributed_snapshot_lab as lab
from distributed_snapshot_lab import (
    DistributedBank,
    generate_walkthrough_png_assets,
    generate_walkthrough_svg_assets,
    parse_balances,
    parse_marker_delay,
    parse_scoped_marker_delay,
    parse_script,
    parse_snapshot_spec,
    parse_snapshot_specs,
    parse_transfer,
    render_mermaid,
    render_script_walkthrough,
    render_script_walkthrough_html,
    render_snapshot_svg,
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

    def test_failed_link_blocks_send_and_deliver_until_recovery(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10})
        bank.fail_link("A", "B", reason="partition")

        with self.assertRaisesRegex(ValueError, "channel A->B is down"):
            bank.transfer("A", "B", 3, "ab-1")

        bank.recover_link("A", "B")
        bank.transfer("A", "B", 3, "ab-2")
        bank.fail_link("A", "B", reason="mid-flight")
        with self.assertRaisesRegex(ValueError, "channel A->B is down"):
            bank.deliver("A", "B")

        bank.recover_link("A", "B")
        bank.deliver("A", "B")
        self.assertEqual(bank.current_balances(), {"A": 7, "B": 13})

    def test_snapshot_records_down_links_and_skips_blocked_markers(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        bank.transfer("C", "B", 2, "cb-1")
        bank.fail_link("A", "B", reason="partition")

        result = bank.snapshot("A", marker_delay_overrides={"C->B": 2})

        self.assertTrue(result["consistent"])
        self.assertEqual(result["channel_statuses"]["A->B"], "down")
        self.assertNotIn("A->B", [marker["channel"] for marker in result["markers"]])
        self.assertEqual(result["channel_messages"]["C->B"][0]["label"], "cb-1")

    def test_script_runner_supports_link_failure_and_recovery_steps(self) -> None:
        result = run_cli_json(
            "script",
            "--balances",
            '{"A": 10, "B": 10, "C": 10}',
            "--marker-delay",
            "C->B=2",
            "--script",
            json.dumps(
                [
                    {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                    {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                    {"op": "snapshot", "snapshot_id": "partitioned", "initiator": "A"},
                    {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "healed"},
                ]
            ),
        )

        self.assertEqual(result["channel_statuses"]["A->B"], "up")
        self.assertEqual(result["snapshots"][0]["channel_statuses"]["A->B"], "down")
        self.assertEqual(result["snapshots"][0]["channel_messages"]["C->B"][0]["amount"], 2)

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

    def test_render_snapshot_svg_contains_svg_markup_and_summary(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        bank.transfer("A", "B", 3, "ab-1")
        bank.transfer("C", "B", 2, "cb-1")
        bank.fail_link("A", "B", reason="partition")
        result = bank.snapshot("A", marker_delay_overrides={"C->B": 2})
        result["snapshot_id"] = "during-partition"

        svg = render_snapshot_svg(result, bank.processes, title="Partition Heal Snapshot")

        self.assertIn("<svg", svg)
        self.assertIn("Partition Heal Snapshot", svg)
        self.assertIn("transfer 3 (ab-1)", svg)
        self.assertIn("marker t=0", svg)
        self.assertIn("Snapshot summary", svg)
        self.assertIn("consistent=True", svg)
        self.assertIn("Recorded in-flight", svg)

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

    def test_render_script_walkthrough_summarizes_partition_heal_scenario(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        result = bank.run_script(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "deliver", "sender": "A", "receiver": "B"},
                {"op": "deliver", "sender": "C", "receiver": "B"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ],
            marker_delay_overrides={"C->B": 2},
        )

        markdown = render_script_walkthrough(result, bank.processes, title="Partition Heal Walkthrough")

        self.assertIn("# Partition Heal Walkthrough", markdown)
        self.assertIn("## Timeline", markdown)
        self.assertIn("link `A->B` failed (partition)", markdown)
        self.assertIn("4. captured snapshot `during-partition` from `A`; consistent=True", markdown)
        self.assertIn("### Snapshot `during-partition` (script step 4)", markdown)
        self.assertIn("- down links: A->B", markdown)
        self.assertIn("  - `C->B`: 2 (cb-1)", markdown)
        self.assertIn("```mermaid", markdown)
        self.assertIn("LINK RECOVER (heal)", markdown)

    def test_render_script_walkthrough_html_includes_assets_and_mermaid_source(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        result = bank.run_script(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ],
            marker_delay_overrides={"C->B": 2},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "handout.html"
            svg_dir = Path(temp_dir) / "svg"
            png_dir = Path(temp_dir) / "png"
            svg_assets = generate_walkthrough_svg_assets(
                result,
                bank.processes,
                output_dir=svg_dir,
                title="Partition Heal Walkthrough",
                filename_prefix="partition-heal",
            )

            def fake_render_svg_to_png(svg_text: str, output_path: Path, *, browser_binary: str | None = None) -> Path:
                self.assertIn("<svg", svg_text)
                self.assertIsNone(browser_binary)
                output_path.write_bytes(b"png")
                return output_path

            with patch("distributed_snapshot_lab.render_svg_to_png", side_effect=fake_render_svg_to_png):
                png_assets = generate_walkthrough_png_assets(
                    result,
                    bank.processes,
                    output_dir=png_dir,
                    title="Partition Heal Walkthrough",
                    filename_prefix="partition-heal",
                )

            html = render_script_walkthrough_html(
                result,
                bank.processes,
                title="Partition Heal Walkthrough",
                svg_assets=svg_assets,
                png_assets=png_assets,
                output_path=output_path,
            )

            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("Partition Heal Walkthrough", html)
            self.assertIn("Open SVG", html)
            self.assertIn("Open PNG", html)
            self.assertIn("Mermaid source", html)
            self.assertIn("svg/partition-heal-01-during-partition.svg", html)
            self.assertIn("png/partition-heal-01-during-partition.png", html)
            self.assertIn("Remaining in-flight messages", html)

    def test_render_script_walkthrough_html_resolves_relative_asset_paths_for_absolute_output(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        result = bank.run_script(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
            ],
            marker_delay_overrides={"C->B": 2},
        )

        original_cwd = Path.cwd()
        try:
            os.chdir(PROJECT_DIR)
            with tempfile.TemporaryDirectory(dir=PROJECT_DIR) as temp_dir:
                temp_root = Path(temp_dir)
                output_path = temp_root / "handout.html"
                relative_svg_dir = temp_root.relative_to(PROJECT_DIR) / "svg"
                svg_assets = generate_walkthrough_svg_assets(
                    result,
                    bank.processes,
                    output_dir=relative_svg_dir,
                    title="Partition Heal Walkthrough",
                    filename_prefix="partition-heal",
                )

                html = render_script_walkthrough_html(
                    result,
                    bank.processes,
                    title="Partition Heal Walkthrough",
                    svg_assets=svg_assets,
                    output_path=output_path,
                )
        finally:
            os.chdir(original_cwd)

        self.assertIn("svg/partition-heal-01-during-partition.svg", html)
        self.assertNotIn(str(PROJECT_DIR), html)

    def test_generate_walkthrough_svg_assets_writes_snapshot_files(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        result = bank.run_script(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": 'during "partition"', "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ],
            marker_delay_overrides={"C->B": 2},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = Path(temp_dir) / "walkthrough.md"
            svg_dir = Path(temp_dir) / "svg"
            assets = generate_walkthrough_svg_assets(
                result,
                bank.processes,
                output_dir=svg_dir,
                title="Partition Heal Walkthrough",
                markdown_path=markdown_path,
                filename_prefix="partition-heal",
            )

            self.assertIn('during "partition"', assets)
            self.assertIn("after-heal", assets)
            self.assertEqual(assets['during "partition"']["link"], "svg/partition-heal-01-during-partition.svg")
            self.assertTrue((svg_dir / "partition-heal-01-during-partition.svg").exists())
            self.assertTrue((svg_dir / "partition-heal-02-after-heal.svg").exists())

            markdown = render_script_walkthrough(
                result,
                bank.processes,
                title="Partition Heal Walkthrough",
                svg_assets=assets,
            )
            self.assertIn(
                '- SVG asset: [partition-heal-01-during-partition.svg](svg/partition-heal-01-during-partition.svg)',
                markdown,
            )
            self.assertIn('### Snapshot `during \'partition\'` (script step 4)', markdown)

    def test_render_svg_to_png_uses_headless_browser_command(self) -> None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"></svg>'
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "snapshot.png"

            def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                self.assertEqual(cmd[0], "/usr/bin/google-chrome")
                self.assertIn("--headless", cmd)
                self.assertIn("--window-size=320,180", cmd)
                self.assertTrue(cmd[-1].startswith("file://"))
                output_path.write_bytes(b"png")
                return subprocess.CompletedProcess(cmd, 0, "", "")

            with patch("distributed_snapshot_lab.shutil.which", side_effect=lambda name: "/usr/bin/google-chrome" if name == "google-chrome" else None):
                with patch("distributed_snapshot_lab.subprocess.run", side_effect=fake_run):
                    rendered = lab.render_svg_to_png(svg, output_path)

            self.assertEqual(rendered, output_path)
            self.assertTrue(output_path.exists())

    def test_render_svg_to_png_requires_browser_on_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "snapshot.png"
            with patch("distributed_snapshot_lab.shutil.which", return_value=None):
                with self.assertRaisesRegex(ValueError, "headless browser"):
                    lab.render_svg_to_png(
                        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>',
                        output_path,
                    )

    def test_generate_walkthrough_png_assets_writes_snapshot_files(self) -> None:
        bank = DistributedBank({"A": 10, "B": 10, "C": 10})
        result = bank.run_script(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ],
            marker_delay_overrides={"C->B": 2},
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = Path(temp_dir) / "walkthrough.md"
            png_dir = Path(temp_dir) / "png"

            def fake_render_svg_to_png(svg_text: str, output_path: Path, *, browser_binary: str | None = None) -> Path:
                self.assertIn("<svg", svg_text)
                self.assertIsNone(browser_binary)
                output_path.write_bytes(b"png")
                return output_path

            with patch("distributed_snapshot_lab.render_svg_to_png", side_effect=fake_render_svg_to_png):
                assets = generate_walkthrough_png_assets(
                    result,
                    bank.processes,
                    output_dir=png_dir,
                    title="Partition Heal Walkthrough",
                    markdown_path=markdown_path,
                    filename_prefix="partition-heal",
                )

            self.assertEqual(assets["during-partition"]["link"], "png/partition-heal-01-during-partition.png")
            self.assertTrue((png_dir / "partition-heal-01-during-partition.png").exists())
            self.assertTrue((png_dir / "partition-heal-02-after-heal.png").exists())

            markdown = render_script_walkthrough(
                result,
                bank.processes,
                title="Partition Heal Walkthrough",
                png_assets=assets,
            )
            self.assertIn(
                '- PNG asset: [partition-heal-01-during-partition.png](png/partition-heal-01-during-partition.png)',
                markdown,
            )
            self.assertIn('![during-partition PNG](png/partition-heal-01-during-partition.png)', markdown)

    def test_cli_walkthrough_outputs_markdown_and_writes_file(self) -> None:
        script = json.dumps(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "walkthrough.md"
            completed = run_cli(
                "walkthrough",
                "--balances",
                '{"A": 10, "B": 10, "C": 10}',
                "--marker-delay",
                "C->B=2",
                "--script",
                script,
                "--title",
                "Partition Heal Walkthrough",
                "--output",
                str(output_path),
            )

            self.assertTrue(completed.stdout.startswith("# Partition Heal Walkthrough\n"))
            self.assertIn("```mermaid", completed.stdout)
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), completed.stdout)

    def test_cli_walkthrough_can_export_svg_assets(self) -> None:
        script = json.dumps(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "walkthrough.md"
            svg_dir = Path(temp_dir) / "svg"
            completed = run_cli(
                "walkthrough",
                "--balances",
                '{"A": 10, "B": 10, "C": 10}',
                "--marker-delay",
                "C->B=2",
                "--script",
                script,
                "--title",
                "Partition Heal Walkthrough",
                "--output",
                str(output_path),
                "--svg-dir",
                str(svg_dir),
                "--svg-prefix",
                "partition-heal",
            )

            self.assertIn("- SVG asset: [partition-heal-01-during-partition.svg](svg/partition-heal-01-during-partition.svg)", completed.stdout)
            self.assertIn("![after-heal SVG](svg/partition-heal-02-after-heal.svg)", completed.stdout)
            self.assertTrue((svg_dir / "partition-heal-01-during-partition.svg").exists())
            self.assertTrue((svg_dir / "partition-heal-02-after-heal.svg").exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), completed.stdout)

    def test_cli_walkthrough_can_export_html_handout(self) -> None:
        script = json.dumps(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "walkthrough.md"
            html_output = Path(temp_dir) / "handout.html"
            svg_dir = Path(temp_dir) / "svg"
            completed = run_cli(
                "walkthrough",
                "--balances",
                '{"A": 10, "B": 10, "C": 10}',
                "--marker-delay",
                "C->B=2",
                "--script",
                script,
                "--title",
                "Partition Heal Walkthrough",
                "--output",
                str(output_path),
                "--html-output",
                str(html_output),
                "--svg-dir",
                str(svg_dir),
                "--svg-prefix",
                "partition-heal",
            )

            html_text = html_output.read_text(encoding="utf-8")
            self.assertTrue(completed.stdout.startswith("# Partition Heal Walkthrough\n"))
            self.assertIn("<!DOCTYPE html>", html_text)
            self.assertIn("svg/partition-heal-01-during-partition.svg", html_text)
            self.assertIn("Mermaid source", html_text)
            self.assertTrue((svg_dir / "partition-heal-01-during-partition.svg").exists())

    @unittest.skipUnless(
        any(shutil.which(candidate) for candidate in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")),
        "headless browser not available",
    )
    def test_cli_walkthrough_can_export_png_assets(self) -> None:
        script = json.dumps(
            [
                {"op": "send", "sender": "A", "receiver": "B", "amount": 3, "label": "ab-1"},
                {"op": "send", "sender": "C", "receiver": "B", "amount": 2, "label": "cb-1"},
                {"op": "link-fail", "sender": "A", "receiver": "B", "reason": "partition"},
                {"op": "snapshot", "snapshot_id": "during-partition", "initiator": "A"},
                {"op": "link-recover", "sender": "A", "receiver": "B", "reason": "heal"},
                {"op": "snapshot", "snapshot_id": "after-heal", "initiator": "A"},
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "walkthrough.md"
            png_dir = Path(temp_dir) / "png"
            completed = run_cli(
                "walkthrough",
                "--balances",
                '{"A": 10, "B": 10, "C": 10}',
                "--marker-delay",
                "C->B=2",
                "--script",
                script,
                "--title",
                "Partition Heal Walkthrough",
                "--output",
                str(output_path),
                "--png-dir",
                str(png_dir),
                "--png-prefix",
                "partition-heal",
            )

            self.assertIn("- PNG asset: [partition-heal-01-during-partition.png](png/partition-heal-01-during-partition.png)", completed.stdout)
            self.assertIn("![after-heal PNG](png/partition-heal-02-after-heal.png)", completed.stdout)
            self.assertTrue((png_dir / "partition-heal-01-during-partition.png").exists())
            self.assertTrue((png_dir / "partition-heal-02-after-heal.png").exists())
            self.assertEqual(output_path.read_text(encoding="utf-8"), completed.stdout)

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
