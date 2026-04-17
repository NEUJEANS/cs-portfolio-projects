from __future__ import annotations

import importlib.util
import json
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
OneBitPredictor = module.OneBitPredictor
TwoBitPredictor = module.TwoBitPredictor
build_predictor = module.build_predictor
compare_predictors = module.compare_predictors
generate_synthetic_trace = module.generate_synthetic_trace
load_trace = module.load_trace
parse_trace_line = module.parse_trace_line
simulate_trace = module.simulate_trace
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

    def test_compare_predictors_ranks_best_accuracy_first(self) -> None:
        trace = [BranchRecord(address=0x140, taken=outcome) for outcome in [True, False] * 8]
        results = compare_predictors(trace, table_size=8, history_bits=1)

        self.assertEqual(results[0].predictor, "gshare")
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

        self.assertEqual(deep_results[0].predictor, "gshare")
        self.assertGreater(deep_by_name["gshare"].accuracy, deep_by_name["two-bit"].accuracy)
        self.assertGreater(deep_by_name["gshare"].accuracy, shallow_by_name["gshare"].accuracy)

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
        self.assertEqual(payload["results"][0]["predictor"], "gshare")
        self.assertEqual(payload["total_branches"], 24)

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
