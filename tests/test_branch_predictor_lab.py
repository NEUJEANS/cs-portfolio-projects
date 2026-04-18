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
estimate_predictor_state_bits = module.estimate_predictor_state_bits
format_budget_sweep_summary_table = module.format_budget_sweep_summary_table
format_sweep_summary_table = module.format_sweep_summary_table
format_table_size_alias_summary_table = module.format_table_size_alias_summary_table
generate_synthetic_trace = module.generate_synthetic_trace
load_trace = module.load_trace
parse_trace_line = module.parse_trace_line
render_budget_sweep_markdown = module.render_budget_sweep_markdown
render_budget_sweep_csv = module.render_budget_sweep_csv
render_budget_sweep_svg = module.render_budget_sweep_svg
render_table_size_alias_markdown = module.render_table_size_alias_markdown
render_table_size_alias_csv = module.render_table_size_alias_csv
render_table_size_alias_svg = module.render_table_size_alias_svg
render_comparison_markdown = module.render_comparison_markdown
render_comparison_svg = module.render_comparison_svg
render_perceptron_tuning_markdown = module.render_perceptron_tuning_markdown
render_perceptron_tuning_svg = module.render_perceptron_tuning_svg
render_sweep_markdown = module.render_sweep_markdown
render_sweep_svg = module.render_sweep_svg
run_budget_normalized_sweep = module.run_budget_normalized_sweep
run_budget_workload_sweep = module.run_budget_workload_sweep
run_perceptron_tuning_sweep = module.run_perceptron_tuning_sweep
run_table_size_alias_sweep = module.run_table_size_alias_sweep
run_workload_sweep = module.run_workload_sweep
simulate_trace = module.simulate_trace
summarize_table_aliasing = module.summarize_table_aliasing
summarize_gshare_aliasing = module.summarize_gshare_aliasing
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

    def test_gshare_alias_summary_captures_dynamic_history_collisions(self) -> None:
        trace = generate_synthetic_trace("alias-thrash", branches=48, seed=7)

        summary = summarize_gshare_aliasing(trace, table_size=16, history_bits=4)

        self.assertEqual(summary["table_size"], 16)
        self.assertEqual(summary["history_bits"], 4)
        self.assertGreaterEqual(summary["colliding_indices"], 1)
        self.assertGreaterEqual(summary["history_spread_colliding_indices"], 1)
        self.assertGreaterEqual(summary["cross_address_colliding_indices"], 1)
        top_group = summary["collision_groups"][0]
        self.assertIn("contexts", top_group)
        self.assertGreaterEqual(top_group["context_count"], 2)
        self.assertTrue(all("history_before" in context for context in top_group["contexts"]))

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
        self.assertIn("gshare_alias_summary", payload)
        self.assertEqual(payload["gshare_alias_summary"]["history_bits"], 2)

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
        gshare_alias_summary = summarize_gshare_aliasing(records, table_size=16, history_bits=2)
        results = compare_predictors(records, table_size=16, history_bits=2)

        rendered = render_comparison_markdown(
            trace_path=TRACE_PATH,
            trace_summary=trace_summary,
            alias_summary=alias_summary,
            gshare_alias_summary=gshare_alias_summary,
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
        self.assertIn("## Dynamic gshare aliasing", rendered)

    def test_render_comparison_svg_includes_expected_labels(self) -> None:
        records = load_trace(TRACE_PATH)
        trace_summary = summarize_trace(records)
        alias_summary = summarize_table_aliasing(records, table_size=16)
        gshare_alias_summary = summarize_gshare_aliasing(records, table_size=16, history_bits=2)
        results = compare_predictors(records, table_size=16, history_bits=2)

        rendered = render_comparison_svg(
            trace_path=TRACE_PATH,
            trace_summary=trace_summary,
            alias_summary=alias_summary,
            gshare_alias_summary=gshare_alias_summary,
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

    def test_run_workload_sweep_uses_profiles_and_writes_trace_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_dir = Path(tmpdir) / "sweep-traces"
            scenarios = run_workload_sweep(["loop-heavy", "alias-thrash", "perceptron-majority"], trace_dir=trace_dir)

            self.assertEqual([scenario["workload"] for scenario in scenarios], ["loop-heavy", "alias-thrash", "perceptron-majority"])
            self.assertEqual(scenarios[0]["config"]["table_size"], 8)
            self.assertEqual(scenarios[1]["alias_summary"]["conflicting_indices"], 2)
            self.assertIn("gshare_alias_summary", scenarios[1])
            self.assertGreaterEqual(scenarios[1]["gshare_alias_summary"]["history_spread_colliding_indices"], 1)
            self.assertEqual(scenarios[2]["best_predictor"], "perceptron")
            self.assertTrue((trace_dir / "loop-heavy-seed7.trace").exists())
            self.assertTrue((trace_dir / "alias-thrash-seed7.trace").exists())
            self.assertIn("perceptron-majority-target", (trace_dir / "perceptron-majority-seed13.trace").read_text(encoding="utf-8"))

    def test_render_sweep_outputs_include_overview_and_predictor_story(self) -> None:
        scenarios = run_workload_sweep(["loop-heavy", "alias-thrash", "perceptron-majority"])

        markdown = render_sweep_markdown(scenarios=scenarios)
        svg = render_sweep_svg(scenarios=scenarios)
        summary = format_sweep_summary_table(scenarios)

        self.assertIn("# Branch predictor trace-family sweep", markdown)
        self.assertIn("## Per-workload notes", markdown)
        self.assertIn("`alias-thrash`", markdown)
        self.assertIn("Dynamic gshare aliasing", markdown)
        self.assertIn("perceptron-majority", markdown)
        self.assertIn("<svg", svg)
        self.assertIn("Branch predictor trace-family sweep", svg)
        self.assertIn("Simple vs advanced", svg)
        self.assertIn("loop-heavy", summary)
        self.assertIn("perceptron", summary)

    def test_perceptron_tuning_sweep_reports_default_and_saturation_state(self) -> None:
        trace = generate_synthetic_trace("perceptron-majority", branches=96, seed=13)
        report = run_perceptron_tuning_sweep(
            trace,
            table_size=32,
            history_bits=12,
            thresholds=[19, 37],
            weight_limits=[8, 74],
        )

        self.assertEqual(report["default_threshold"], 37)
        self.assertEqual(report["default_weight_limit"], 74)
        self.assertEqual(report["config_count"], 4)
        self.assertEqual(report["best_config"], report["configs"][0])
        default_config = report["default_config"]
        assert default_config is not None
        self.assertTrue(default_config["is_default_config"])
        by_key = {(config["threshold"], config["weight_limit"]): config for config in report["configs"]}
        self.assertTrue(by_key[(19, 8)]["saturated_max_weight"])
        self.assertLessEqual(by_key[(19, 8)]["max_abs_weight"], 8)
        self.assertGreaterEqual(report["best_config"]["accuracy_percent"], default_config["accuracy_percent"])

    def test_render_perceptron_tuning_outputs_include_heatmap_story(self) -> None:
        trace_path = PROJECT_ROOT / "artifacts" / "branch-predictor-lab" / "perceptron-majority-seed13.trace"
        report = run_perceptron_tuning_sweep(
            generate_synthetic_trace("perceptron-majority", branches=96, seed=13),
            table_size=32,
            history_bits=12,
            thresholds=[19, 37, 55],
            weight_limits=[18, 74],
        )

        markdown = render_perceptron_tuning_markdown(trace_path=trace_path, report=report)
        svg = render_perceptron_tuning_svg(trace_path=trace_path, report=report)

        self.assertIn("# Branch predictor perceptron tuning sweep", markdown)
        self.assertIn("## Accuracy matrix", markdown)
        self.assertIn("default", markdown)
        self.assertIn("<svg", svg)
        self.assertIn("Perceptron tuning sweep", svg)
        self.assertIn("Top tuning configs", svg)

    def test_cli_perceptron_sweep_json_writes_markdown_and_svg(self) -> None:
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
            markdown_path = Path(tmpdir) / "perceptron-tuning-sweep.md"
            svg_path = Path(tmpdir) / "perceptron-tuning-sweep.svg"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "perceptron-sweep",
                    str(trace_path),
                    "--table-size",
                    "32",
                    "--history-bits",
                    "12",
                    "--thresholds",
                    "19",
                    "37",
                    "55",
                    "--weight-limits",
                    "18",
                    "74",
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
            self.assertEqual(payload["trace"], str(trace_path))
            self.assertEqual(payload["config_count"], 6)
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertIn("## Top configs", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("Top tuning configs", svg_path.read_text(encoding="utf-8"))

    def test_cli_sweep_json_writes_markdown_svg_and_trace_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_dir = Path(tmpdir) / "traces"
            markdown_path = Path(tmpdir) / "trace-family-sweep.md"
            svg_path = Path(tmpdir) / "trace-family-sweep.svg"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "sweep",
                    "loop-heavy",
                    "alias-thrash",
                    "perceptron-majority",
                    "--trace-dir",
                    str(trace_dir),
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
            self.assertEqual(payload["scenario_count"], 3)
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertTrue((trace_dir / "loop-heavy-seed7.trace").exists())
            self.assertTrue((trace_dir / "alias-thrash-seed7.trace").exists())
            self.assertTrue((trace_dir / "perceptron-majority-seed13.trace").exists())
            self.assertIn("## Overview", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("Simple vs advanced", svg_path.read_text(encoding="utf-8"))

    def test_estimate_predictor_state_bits_covers_simple_and_advanced_predictors(self) -> None:
        self.assertEqual(estimate_predictor_state_bits("always-taken"), 0)
        self.assertEqual(estimate_predictor_state_bits("one-bit", table_size=8), 8)
        self.assertEqual(estimate_predictor_state_bits("two-bit", table_size=8), 16)
        self.assertEqual(estimate_predictor_state_bits("local-history", table_size=8, history_bits=2), 24)
        self.assertEqual(estimate_predictor_state_bits("gshare", table_size=8, history_bits=2), 18)
        self.assertEqual(estimate_predictor_state_bits("tournament", table_size=8, history_bits=2), 58)
        self.assertEqual(
            estimate_predictor_state_bits("perceptron", table_size=8, history_bits=4, weight_limit=31),
            244,
        )

    def test_run_budget_normalized_sweep_filters_candidates_by_budget(self) -> None:
        trace = generate_synthetic_trace("perceptron-majority", branches=64, seed=13)
        report = run_budget_normalized_sweep(
            trace,
            budgets=[16, 64, 256],
            table_sizes=[2, 4, 8],
            history_bits_options=[1, 2, 4],
            weight_limits=[15, 31],
        )

        self.assertEqual(report["budgets"], [16, 64, 256])
        self.assertGreater(report["candidate_count"], 0)
        self.assertEqual(len(report["budget_reports"]), 3)
        for entry in report["budget_reports"]:
            self.assertLessEqual(entry["predictor_results"][0]["state_bits"], entry["budget_bits"])
            self.assertEqual(entry["winner_predictor"], entry["predictor_results"][0]["predictor"])
            self.assertGreaterEqual(entry["winner_accuracy_percent"], entry["best_simple_accuracy_percent"])
            self.assertGreaterEqual(entry["winner_accuracy_percent"], entry["best_advanced_accuracy_percent"])
            self.assertEqual(len({result["predictor"] for result in entry["predictor_results"]}), len(entry["predictor_results"]))

    def test_run_budget_normalized_sweep_handles_tiny_budgets_without_advanced_predictors(self) -> None:
        trace = generate_synthetic_trace("loop-heavy", branches=16, seed=7)
        report = run_budget_normalized_sweep(
            trace,
            budgets=[1],
            table_sizes=[2],
            history_bits_options=[1],
            weight_limits=[15],
        )

        self.assertEqual(report["budget_reports"][0]["winner_predictor"], "always-taken")
        self.assertEqual(report["budget_reports"][0]["runner_up_predictor"], "always-not-taken")
        self.assertIsNone(report["budget_reports"][0]["best_advanced_predictor"])
        self.assertIsNone(report["budget_reports"][0]["best_advanced_accuracy_percent"])

    def test_render_budget_sweep_outputs_include_budget_story(self) -> None:
        scenarios = run_budget_workload_sweep(
            ["loop-heavy", "perceptron-majority"],
            budgets=[32, 128],
            table_sizes=[2, 4, 8],
            history_bits_options=[1, 2, 4],
            weight_limits=[15, 31],
        )

        markdown = render_budget_sweep_markdown(scenarios=scenarios)
        csv_text = render_budget_sweep_csv(scenarios=scenarios)
        svg = render_budget_sweep_svg(scenarios=scenarios)
        summary = format_budget_sweep_summary_table(scenarios)

        self.assertIn("# Branch predictor budget-normalized sweep", markdown)
        self.assertIn("## Per-workload notes", markdown)
        self.assertIn("`32 bits`", markdown)
        self.assertIn("Portfolio usage", markdown)
        self.assertIn("workload,headline,branches,seed,trace_output,winner_sequence", csv_text)
        self.assertIn("budget_32_winner_predictor", csv_text)
        self.assertIn("perceptron-majority", csv_text)
        self.assertIn("<svg", svg)
        self.assertIn("Budget-normalized branch predictor sweep", svg)
        self.assertIn("loop-heavy", summary)
        self.assertIn("32b", summary)

    def test_cli_budget_sweep_json_writes_markdown_svg_csv_and_trace_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_dir = Path(tmpdir) / "budget-traces"
            markdown_path = Path(tmpdir) / "budget-sweep.md"
            svg_path = Path(tmpdir) / "budget-sweep.svg"
            csv_path = Path(tmpdir) / "budget-sweep.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "budget-sweep",
                    "loop-heavy",
                    "perceptron-majority",
                    "--budgets",
                    "32",
                    "128",
                    "--table-sizes",
                    "2",
                    "4",
                    "8",
                    "--history-bits-options",
                    "1",
                    "2",
                    "4",
                    "--weight-limits",
                    "15",
                    "31",
                    "--trace-dir",
                    str(trace_dir),
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--csv-out",
                    str(csv_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["scenario_count"], 2)
            self.assertEqual(payload["workloads"], ["loop-heavy", "perceptron-majority"])
            self.assertEqual(payload["trace_dir"], str(trace_dir))
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertEqual(payload["csv_output"], str(csv_path))
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertTrue((trace_dir / "loop-heavy-seed7.trace").exists())
            self.assertTrue((trace_dir / "perceptron-majority-seed13.trace").exists())
            self.assertIn("budget-normalized sweep", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("Budget-normalized branch predictor sweep", svg_path.read_text(encoding="utf-8"))
            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("budget_32_winner_predictor", csv_text)
            self.assertIn("perceptron-majority", csv_text)


    def test_run_table_size_alias_sweep_tracks_static_and_dynamic_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_dir = Path(tmpdir) / "table-size-traces"
            scenarios = run_table_size_alias_sweep(
                ["alias-thrash", "perceptron-majority"],
                table_sizes=[4, 16, 64],
                trace_dir=trace_dir,
            )

            self.assertEqual([scenario["workload"] for scenario in scenarios], ["alias-thrash", "perceptron-majority"])
            alias_rows = scenarios[0]["sweep_rows"]
            self.assertEqual([row["table_size"] for row in alias_rows], [4, 16, 64])
            self.assertGreater(alias_rows[0]["static_colliding_indices"], alias_rows[-1]["static_colliding_indices"])
            self.assertGreater(alias_rows[1]["dynamic_colliding_indices"], 0)
            self.assertGreaterEqual(alias_rows[1]["gshare_accuracy_percent"], alias_rows[1]["two_bit_accuracy_percent"])
            self.assertEqual(scenarios[1]["best_static_table_size"], 4)
            self.assertTrue((trace_dir / "alias-thrash-seed7.trace").exists())
            self.assertTrue((trace_dir / "perceptron-majority-seed13.trace").exists())

    def test_render_table_size_alias_outputs_include_collision_story(self) -> None:
        scenarios = run_table_size_alias_sweep(
            ["alias-thrash", "loop-heavy"],
            table_sizes=[4, 16, 64],
        )

        markdown = render_table_size_alias_markdown(scenarios=scenarios)
        csv_text = render_table_size_alias_csv(scenarios=scenarios)
        svg = render_table_size_alias_svg(scenarios=scenarios)
        summary = format_table_size_alias_summary_table(scenarios)

        self.assertIn("# Branch predictor alias table-size sweep", markdown)
        self.assertIn("## Per-workload notes", markdown)
        self.assertIn("`alias-thrash`", markdown)
        self.assertIn("Dynamic note", markdown)
        self.assertIn("workload,headline,branches,seed,history_bits,trace_output,table_size", csv_text)
        self.assertIn("dynamic_cross_address_colliding_indices", csv_text)
        self.assertIn("<svg", svg)
        self.assertIn("Branch predictor alias table-size sweep", svg)
        self.assertIn("loop-heavy", summary)
        self.assertIn("4e", summary)

    def test_cli_table_size_sweep_json_writes_markdown_svg_csv_and_trace_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            trace_dir = Path(tmpdir) / "table-size-traces"
            markdown_path = Path(tmpdir) / "table-size-sweep.md"
            svg_path = Path(tmpdir) / "table-size-sweep.svg"
            csv_path = Path(tmpdir) / "table-size-sweep.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "table-size-sweep",
                    "alias-thrash",
                    "perceptron-majority",
                    "--table-sizes",
                    "4",
                    "16",
                    "64",
                    "--trace-dir",
                    str(trace_dir),
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--csv-out",
                    str(csv_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["scenario_count"], 2)
            self.assertEqual(payload["workloads"], ["alias-thrash", "perceptron-majority"])
            self.assertEqual(payload["trace_dir"], str(trace_dir))
            self.assertEqual(payload["markdown_output"], str(markdown_path))
            self.assertEqual(payload["svg_output"], str(svg_path))
            self.assertEqual(payload["csv_output"], str(csv_path))
            self.assertTrue(markdown_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertTrue((trace_dir / "alias-thrash-seed7.trace").exists())
            self.assertTrue((trace_dir / "perceptron-majority-seed13.trace").exists())
            self.assertIn("alias table-size sweep", markdown_path.read_text(encoding="utf-8"))
            self.assertIn("Branch predictor alias table-size sweep", svg_path.read_text(encoding="utf-8"))
            csv_text = csv_path.read_text(encoding="utf-8")
            self.assertIn("dynamic_colliding_indices", csv_text)
            self.assertIn("perceptron-majority", csv_text)


if __name__ == "__main__":
    unittest.main()
