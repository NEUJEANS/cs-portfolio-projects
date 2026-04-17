from __future__ import annotations

import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "branch-predictor-lab" / "branch_predictor.py"
TRACE_PATH = PROJECT_ROOT / "projects" / "branch-predictor-lab" / "sample_trace.txt"

spec = importlib.util.spec_from_file_location("branch_predictor_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

BranchRecord = module.BranchRecord
GSharePredictor = module.GSharePredictor
LocalHistoryPredictor = module.LocalHistoryPredictor
OneBitPredictor = module.OneBitPredictor
PerceptronPredictor = module.PerceptronPredictor
TournamentPredictor = module.TournamentPredictor
TwoBitPredictor = module.TwoBitPredictor
build_predictor = module.build_predictor
compare_predictors = module.compare_predictors
generate_synthetic_trace = module.generate_synthetic_trace
load_trace = module.load_trace
parse_trace_line = module.parse_trace_line
render_comparison_markdown = module.render_comparison_markdown
render_comparison_svg = module.render_comparison_svg
simulate_trace = module.simulate_trace
summarize_table_aliasing = module.summarize_table_aliasing
summarize_trace = module.summarize_trace


class BranchPredictorLabTests(unittest.TestCase):
    def test_parse_trace_line_supports_comments_target_and_label(self) -> None:
        record = parse_trace_line("0x204 T 0x260 cache-hit # branch comment", 7)
        assert record is not None
        self.assertEqual(record.address, 0x204)
        self.assertTrue(record.taken)
        self.assertEqual(record.target, 0x260)
        self.assertEqual(record.label, "cache-hit")
        self.assertEqual(record.line_number, 7)

    def test_load_trace_rejects_empty_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty_trace.txt"
            path.write_text("# only comments\n\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "did not contain"):
                load_trace(path)

    def test_two_bit_beats_one_bit_on_loop_exit_pattern(self) -> None:
        trace = [BranchRecord(address=0x100, taken=outcome) for outcome in [True, True, True, True, False] * 2]

        one_bit = simulate_trace(trace, OneBitPredictor(table_size=8))
        two_bit = simulate_trace(trace, TwoBitPredictor(table_size=8))

        self.assertEqual(one_bit.mispredictions, 4)
        self.assertEqual(two_bit.mispredictions, 2)
        self.assertGreater(two_bit.accuracy, one_bit.accuracy)

    def test_gshare_learns_alternating_same_pc_pattern(self) -> None:
        trace = [BranchRecord(address=0x140, taken=outcome) for outcome in [True, False] * 8]

        bimodal = simulate_trace(trace, TwoBitPredictor(table_size=8))
        gshare = simulate_trace(trace, GSharePredictor(table_size=8, history_bits=1))

        self.assertEqual(bimodal.mispredictions, 8)
        self.assertEqual(gshare.mispredictions, 1)
        self.assertGreater(gshare.accuracy, bimodal.accuracy)
        self.assertEqual(gshare.final_state["final_history"], "0")

    def test_local_history_learns_alternating_same_pc_pattern(self) -> None:
        trace = [BranchRecord(address=0x140, taken=outcome) for outcome in [True, False] * 8]

        bimodal = simulate_trace(trace, TwoBitPredictor(table_size=8))
        local_history = simulate_trace(trace, LocalHistoryPredictor(table_size=8, history_bits=1))
        gshare = simulate_trace(trace, GSharePredictor(table_size=8, history_bits=1))

        self.assertEqual(local_history.mispredictions, 1)
        self.assertEqual(local_history.mispredictions, gshare.mispredictions)
        self.assertGreater(local_history.accuracy, bimodal.accuracy)

    def test_tournament_matches_best_component_on_alternating_single_pc_pattern(self) -> None:
        trace = [BranchRecord(address=0x140, taken=outcome) for outcome in [True, False] * 32]

        tournament = simulate_trace(trace, TournamentPredictor(table_size=8, history_bits=1))
        local_history = simulate_trace(trace, LocalHistoryPredictor(table_size=8, history_bits=1))
        gshare = simulate_trace(trace, GSharePredictor(table_size=8, history_bits=1))
        bimodal = simulate_trace(trace, TwoBitPredictor(table_size=8))

        self.assertEqual(tournament.mispredictions, local_history.mispredictions)
        self.assertEqual(tournament.mispredictions, gshare.mispredictions)
        self.assertGreater(tournament.accuracy, bimodal.accuracy)

    def test_tournament_chooser_can_shift_toward_global_history(self) -> None:
        rng = random.Random(7)
        trace: list[BranchRecord] = []
        for _ in range(200):
            driver_taken = rng.random() < 0.5
            trace.append(BranchRecord(address=0x340, taken=driver_taken))
            trace.append(BranchRecord(address=0x380, taken=driver_taken))

        tournament = simulate_trace(trace, TournamentPredictor(table_size=8, history_bits=4))
        local_history = simulate_trace(trace, LocalHistoryPredictor(table_size=8, history_bits=4))
        gshare = simulate_trace(trace, GSharePredictor(table_size=8, history_bits=4))

        self.assertGreater(gshare.accuracy, local_history.accuracy)
        self.assertGreater(tournament.accuracy, local_history.accuracy)
        self.assertGreaterEqual(tournament.final_state["trained_entries"], 1)
        self.assertGreaterEqual(tournament.final_state["gshare_favored_entries"], 1)

    def test_compare_predictors_ranks_best_accuracy_first(self) -> None:
        trace = [BranchRecord(address=0x140, taken=outcome) for outcome in [True, False] * 8]
        results = compare_predictors(trace, table_size=8, history_bits=1)

        self.assertIn(results[0].predictor, {"gshare", "local-history", "tournament"})
        self.assertLessEqual(results[-1].accuracy, results[1].accuracy)
        self.assertIn(results[-1].predictor, {"always-not-taken", "one-bit"})

    def test_build_predictor_rejects_non_power_of_two_table_size(self) -> None:
        with self.assertRaisesRegex(ValueError, "power of two"):
            build_predictor("two-bit", table_size=12, history_bits=2)

    def test_generate_loop_heavy_trace_exposes_repeat_exit_pattern(self) -> None:
        trace = generate_synthetic_trace("loop-heavy", branches=12, seed=99)

        self.assertEqual(len(trace), 12)
        self.assertEqual([record.taken for record in trace[:5]], [True, True, True, True, False])
        self.assertEqual(trace[0].label, "outer-loop-backedge")
        self.assertEqual(trace[4].label, "outer-loop-exit")
        summary = summarize_trace(trace)
        self.assertGreater(summary["taken_branches"], summary["not_taken_branches"])
        self.assertGreaterEqual(summary["unique_addresses"], 2)

    def test_generate_random_biased_trace_is_seed_reproducible(self) -> None:
        left = generate_synthetic_trace("random-biased", branches=16, seed=11)
        right = generate_synthetic_trace("random-biased", branches=16, seed=11)
        other = generate_synthetic_trace("random-biased", branches=16, seed=12)

        self.assertEqual(left, right)
        self.assertNotEqual(left, other)

    def test_tournament_style_trace_rewards_deeper_history(self) -> None:
        trace = generate_synthetic_trace("tournament-style", branches=48, seed=5)
        shallow_results = compare_predictors(trace, table_size=16, history_bits=1)
        deep_results = compare_predictors(trace, table_size=16, history_bits=4)
        shallow_by_name = {result.predictor: result for result in shallow_results}
        deep_by_name = {result.predictor: result for result in deep_results}

        self.assertEqual(deep_results[0].predictor, "perceptron")
        self.assertGreater(deep_by_name["gshare"].accuracy, deep_by_name["two-bit"].accuracy)
        self.assertGreater(deep_by_name["gshare"].accuracy, shallow_by_name["gshare"].accuracy)
        self.assertGreater(deep_by_name["perceptron"].accuracy, shallow_by_name["perceptron"].accuracy)

    def test_generate_alias_thrash_trace_creates_conflicting_collision_groups(self) -> None:
        trace = generate_synthetic_trace("alias-thrash", branches=24, seed=7)
        summary = summarize_table_aliasing(trace, table_size=16)

        self.assertEqual(len(trace), 24)
        self.assertGreaterEqual(summary["colliding_indices"], 2)
        self.assertGreaterEqual(summary["conflicting_indices"], 2)
        top_group = summary["collision_groups"][0]
        addresses = {entry["address"] for entry in top_group["addresses"]}
        self.assertTrue({"0x100", "0x140"}.issubset(addresses) or {"0x110", "0x150"}.issubset(addresses))
        dominant_outcomes = {entry["dominant_outcome"] for entry in top_group["addresses"]}
        self.assertIn("taken", dominant_outcomes)
        self.assertIn("not-taken", dominant_outcomes)

    def test_alias_thrash_trace_improves_with_larger_table(self) -> None:
        trace = generate_synthetic_trace("alias-thrash", branches=64, seed=7)
        small = compare_predictors(trace, table_size=16, history_bits=4)
        large = compare_predictors(trace, table_size=32, history_bits=4)
        small_by_name = {result.predictor: result for result in small}
        large_by_name = {result.predictor: result for result in large}

        self.assertGreater(large_by_name["two-bit"].accuracy, small_by_name["two-bit"].accuracy)
        self.assertGreater(large_by_name["one-bit"].accuracy, small_by_name["one-bit"].accuracy)

    def test_generate_perceptron_majority_trace_is_seed_reproducible(self) -> None:
        left = generate_synthetic_trace("perceptron-majority", branches=24, seed=13)
        right = generate_synthetic_trace("perceptron-majority", branches=24, seed=13)
        other = generate_synthetic_trace("perceptron-majority", branches=24, seed=14)

        self.assertEqual(left, right)
        self.assertNotEqual(left, other)
        self.assertTrue(all(record.address == 0x480 for record in left))
        self.assertTrue(all(record.label == "perceptron-majority-target" for record in left))

    def test_perceptron_learns_linearly_separable_history_pattern(self) -> None:
        trace = generate_synthetic_trace("perceptron-majority", branches=128, seed=13)

        perceptron = simulate_trace(trace, PerceptronPredictor(table_size=32, history_bits=12))
        gshare = simulate_trace(trace, GSharePredictor(table_size=32, history_bits=12))
        two_bit = simulate_trace(trace, TwoBitPredictor(table_size=32))

        self.assertGreater(perceptron.accuracy, 0.9)
        self.assertGreater(perceptron.accuracy, gshare.accuracy)
        self.assertGreater(perceptron.accuracy, two_bit.accuracy)
        self.assertGreaterEqual(perceptron.final_state["trained_perceptrons"], 1)
        self.assertGreater(perceptron.final_state["non_zero_weights"], 0)

    def test_cli_simulate_perceptron_json_includes_weight_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "perceptron-majority.trace"
            trace_path.write_text(
                "\n".join(
                    "0x480 T 0x4b0 perceptron-majority-target" if record.taken else "0x480 N 0x484 perceptron-majority-target"
                    for record in generate_synthetic_trace("perceptron-majority", branches=48, seed=13)
                )
                + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "simulate",
                    str(trace_path),
                    "--predictor",
                    "perceptron",
                    "--table-size",
                    "32",
                    "--history-bits",
                    "12",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["predictor"], "perceptron")
        self.assertEqual(payload["final_state"]["history_bits"], 12)
        self.assertIn("threshold", payload["final_state"])
        self.assertIn("weight_limit", payload["final_state"])
        self.assertGreater(payload["final_state"]["non_zero_weights"], 0)

    def test_cli_compare_json_emits_best_predictor(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "compare",
                str(TRACE_PATH),
                "--table-size",
                "16",
                "--history-bits",
                "2",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["trace"], str(TRACE_PATH))
        self.assertEqual(payload["best_predictor"], payload["results"][0]["predictor"])
        self.assertEqual(payload["results"][0]["predictor"], "local-history")
        self.assertEqual(payload["total_branches"], 24)
        self.assertIn("alias_summary", payload)
        self.assertEqual(payload["alias_summary"]["table_size"], 16)

    def test_cli_simulate_local_history_json_includes_snapshot(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "simulate",
                str(TRACE_PATH),
                "--predictor",
                "local-history",
                "--table-size",
                "16",
                "--history-bits",
                "2",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["predictor"], "local-history")
        self.assertEqual(payload["final_state"]["history_bits"], 2)
        self.assertGreaterEqual(payload["final_state"]["active_histories"], 1)
        self.assertIn("trained_patterns", payload["final_state"])

    def test_cli_simulate_tournament_json_exposes_chooser_snapshot(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "simulate",
                str(TRACE_PATH),
                "--predictor",
                "tournament",
                "--table-size",
                "16",
                "--history-bits",
                "2",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["predictor"], "tournament")
        self.assertEqual(payload["final_state"]["history_bits"], 2)
        self.assertIn("chooser_table", payload["final_state"])
        self.assertIn("local_predictor", payload["final_state"])
        self.assertIn("global_predictor", payload["final_state"])
        chooser_total = sum(payload["final_state"]["chooser_table"].values())
        self.assertEqual(chooser_total, 16)

    def test_render_comparison_markdown_includes_rankings_and_talking_points(self) -> None:
        records = load_trace(TRACE_PATH)
        trace_summary = summarize_trace(records)
        alias_summary = summarize_table_aliasing(records, table_size=16)
        results = compare_predictors(records, table_size=16, history_bits=2)

        rendered = render_comparison_markdown(
            trace_path=TRACE_PATH,
            trace_summary=trace_summary,
            alias_summary=alias_summary,
            results=results,
            table_size=16,
            history_bits=2,
        )

        self.assertIn("# Branch predictor comparison card: `sample_trace`", rendered)
        self.assertIn("## Ranking", rendered)
        self.assertIn("`local-history`", rendered)
        self.assertIn("## Portfolio talking points", rendered)
        self.assertIn("Two-bit vs one-bit", rendered)
        self.assertIn("## Table aliasing", rendered)

    def test_render_comparison_svg_includes_expected_labels(self) -> None:
        records = load_trace(TRACE_PATH)
        trace_summary = summarize_trace(records)
        alias_summary = summarize_table_aliasing(records, table_size=16)
        results = compare_predictors(records, table_size=16, history_bits=2)

        rendered = render_comparison_svg(
            trace_path=TRACE_PATH,
            trace_summary=trace_summary,
            alias_summary=alias_summary,
            results=results,
            table_size=16,
            history_bits=2,
        )

        self.assertIn("<svg", rendered)
        self.assertIn("Branch predictor comparison card", rendered)
        self.assertIn("Accuracy ranking", rendered)
        self.assertIn("local-history", rendered)
        self.assertIn("Worst predictor", rendered)

    def test_cli_compare_json_writes_markdown_and_svg_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "branch-predictor-card.md"
            svg_path = Path(tmpdir) / "branch-predictor-card.svg"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "compare",
                    str(TRACE_PATH),
                    "--table-size",
                    "16",
                    "--history-bits",
                    "2",
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["best_predictor"], "local-history")
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertIn("## Ranking", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("Accuracy ranking", svg_path.read_text(encoding="utf-8"))

    def test_cli_generate_json_writes_trace_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "generated.trace"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "generate",
                    "tournament-style",
                    "--branches",
                    "12",
                    "--seed",
                    "3",
                    "--output",
                    str(output_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["workload"], "tournament-style")
            self.assertEqual(payload["total_branches"], 12)
            self.assertEqual(payload["output"], str(output_path))
            self.assertTrue(output_path.exists())
            written_lines = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(written_lines), 12)
            self.assertEqual(len(payload["records"]), 12)
            self.assertIn("history-follower", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
