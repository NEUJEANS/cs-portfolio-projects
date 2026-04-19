from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from page_replacement_lab import (  # noqa: E402
    ALGORITHMS,
    TRACE_BENCHMARKS,
    WORKLOAD_PRESETS,
    compare_algorithms,
    compare_wsclock_modes,
    load_trace_benchmark_reference,
    study_wsclock_modes,
    parse_dirty_page_args,
    parse_reference_args,
    simulate,
    simulate_adaptive_wsclock,
    study_frame_counts,
    summarize_trace,
    tune_wsclock_windows,
)


REFERENCE = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
SCRIPT = PROJECT_DIR / "page_replacement_lab.py"


class PageReplacementSimulationTests(unittest.TestCase):
    def test_classic_reference_fault_counts_include_wsclock(self) -> None:
        self.assertEqual(simulate("fifo", REFERENCE, 3).page_faults, 9)
        self.assertEqual(simulate("clock", REFERENCE, 3).page_faults, 9)
        self.assertEqual(simulate("aging", REFERENCE, 3).page_faults, 10)
        self.assertEqual(simulate("wsclock", REFERENCE, 3).page_faults, 10)
        self.assertEqual(simulate("lru", REFERENCE, 3).page_faults, 10)
        self.assertEqual(simulate("opt", REFERENCE, 3).page_faults, 7)

    def test_wsclock_matches_aging_and_lru_on_classic_reference_at_four_frames(self) -> None:
        self.assertEqual(simulate("aging", REFERENCE, 4).page_faults, 8)
        self.assertEqual(simulate("wsclock", REFERENCE, 4).page_faults, 8)
        self.assertEqual(simulate("aging", REFERENCE, 4).page_faults, simulate("lru", REFERENCE, 4).page_faults)
        self.assertEqual(simulate("wsclock", REFERENCE, 4).page_faults, simulate("lru", REFERENCE, 4).page_faults)

    def test_wsclock_window_override_changes_faults_on_compiler_benchmark(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["compiler-phase-shift"])
        self.assertEqual(simulate("wsclock", benchmark_reference, 5, wsclock_window=1).page_faults, 54)
        self.assertEqual(simulate("wsclock", benchmark_reference, 5, wsclock_window=5).page_faults, 52)
        self.assertEqual(simulate("wsclock", benchmark_reference, 5).page_faults, 52)

    def test_compare_algorithms_orders_all_strategies(self) -> None:
        results = compare_algorithms(REFERENCE, 4)
        self.assertEqual([result.algorithm for result in results], list(ALGORITHMS))
        self.assertEqual([result.page_faults for result in results], [10, 10, 8, 8, 8, 6])

    def test_study_detects_fifo_and_clock_regressions(self) -> None:
        study = study_frame_counts(REFERENCE, 2, 5)
        self.assertIn(
            {
                "algorithm": "fifo",
                "from_frames": 3,
                "to_frames": 4,
                "faults_before": 9,
                "faults_after": 10,
                "fault_delta": 1,
            },
            study["fifo_belady_anomalies"],
        )
        self.assertIn(
            {
                "algorithm": "clock",
                "from_frames": 3,
                "to_frames": 4,
                "faults_before": 9,
                "faults_after": 10,
                "fault_delta": 1,
            },
            study["monotonicity_violations"],
        )

    def test_study_records_wsclock_window_metadata(self) -> None:
        study = study_frame_counts(REFERENCE, 2, 4, wsclock_window=3)
        self.assertEqual(study["wsclock_window_mode"], "fixed")
        self.assertEqual(study["wsclock_window_override"], 3)
        self.assertEqual(study["wsclock_window_description"], "fixed 3 references")
        self.assertEqual([row["wsclock_window"] for row in study["frame_results"]], [3, 3, 3])

    def test_parse_reference_accepts_presets(self) -> None:
        parsed = parse_reference_args([], None, "classic-belady")
        self.assertEqual(parsed.source, "preset:classic-belady")
        self.assertEqual(parsed.reference_string, REFERENCE)

    def test_parse_reference_accepts_benchmarks(self) -> None:
        parsed = parse_reference_args([], None, None, "compiler-phase-shift")
        self.assertEqual(parsed.source, "benchmark:compiler-phase-shift")
        self.assertGreater(len(parsed.reference_string), len(REFERENCE))
        self.assertEqual(parsed.reference_string[:8], [1, 2, 3, 4, 1, 2, 5, 6])

    def test_parse_dirty_page_args_merges_flags_and_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump([6, 7, 8], handle)
            handle.flush()
            dirty_path = handle.name

        self.addCleanup(lambda: Path(dirty_path).unlink(missing_ok=True))
        parsed = parse_dirty_page_args(["4", "5", "4"], dirty_path)
        self.assertEqual(parsed, (4, 5, 6, 7, 8))

    def test_wsclock_dirty_pages_trigger_writebacks_on_compiler_benchmark(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["compiler-phase-shift"])
        result = simulate(
            "wsclock",
            benchmark_reference,
            5,
            wsclock_window=1,
            dirty_pages=[1, 2, 3, 4, 5, 6],
        )
        self.assertEqual(result.page_faults, 55)
        self.assertEqual(result.writebacks, 15)
        self.assertTrue(any(step.writebacks_scheduled for step in result.steps))

    def test_tune_wsclock_windows_prefers_frontier_window_when_writebacks_cost(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["compiler-phase-shift"])
        payload = tune_wsclock_windows(
            benchmark_reference,
            5,
            min_window=1,
            max_window=7,
            dirty_pages=[1, 2, 3, 4, 5, 6],
            writeback_penalty=1.0,
        )
        self.assertEqual(payload["recommended_window"], 7)
        self.assertEqual(payload["recommended"]["page_faults"], 52)
        self.assertEqual(payload["recommended"]["writebacks"], 0)
        self.assertEqual([entry["window"] for entry in payload["pareto_frontier"]], [7])
        self.assertIsNone(payload["auto_window_result"])

    def test_trace_summary_detects_phase_boundary_hints(self) -> None:
        payload = summarize_trace([1, 2, 1, 2, 1, 2, 7, 8, 7, 8, 7, 8], window_size=6)
        self.assertEqual(payload["first_touches"], 4)
        self.assertEqual(payload["reuses"], 8)
        self.assertEqual(payload["working_set_stats"]["max"], 4)
        self.assertEqual(payload["working_set_stats"]["final"], 2)
        self.assertEqual(payload["top_pages"][0], {"page": 1, "count": 3})
        self.assertEqual(len(payload["phase_boundaries"]), 1)
        self.assertEqual(payload["phase_boundaries"][0]["after_reference"], 6)
        self.assertEqual(payload["phase_boundaries"][0]["jaccard_similarity"], 0.0)

    def test_cli_compare_json_works_with_pages_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(REFERENCE, handle)
            handle.flush()
            page_path = handle.name

        self.addCleanup(lambda: Path(page_path).unlink(missing_ok=True))
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "3",
                "--pages-file",
                page_path,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["frame_count"], 3)
        self.assertEqual(payload["reference_string"], REFERENCE)
        self.assertEqual([result["algorithm"] for result in payload["results"]], list(ALGORITHMS))
        self.assertEqual(payload["results"][-1]["page_faults"], 7)

    def test_cli_compare_json_works_with_preset(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "3",
                "--preset",
                "classic-belady",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["reference_source"], "preset:classic-belady")
        self.assertEqual(
            [result["algorithm"] for result in payload["results"]],
            list(ALGORITHMS),
        )

    def test_cli_compare_json_works_with_benchmark(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "5",
                "--benchmark",
                "db-hotset-scan",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["reference_source"], "benchmark:db-hotset-scan")
        self.assertGreater(len(payload["reference_string"]), 40)
        self.assertEqual(payload["results"][0]["algorithm"], "fifo")
        self.assertEqual(payload["results"][2]["algorithm"], "aging")
        self.assertEqual(len(payload["results"]), len(ALGORITHMS))

    def test_cli_compare_json_supports_wsclock_window_override_on_benchmark(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "5",
                "--benchmark",
                "compiler-phase-shift",
                "--wsclock-window",
                "1",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        wsclock_result = next(result for result in payload["results"] if result["algorithm"] == "wsclock")
        self.assertEqual(payload["wsclock_window_mode"], "fixed")
        self.assertEqual(payload["wsclock_window_override"], 1)
        self.assertEqual(payload["effective_wsclock_window"], 1)
        self.assertEqual(payload["wsclock_window_description"], "fixed 1 reference")
        self.assertEqual(wsclock_result["page_faults"], 54)

    def test_cli_compare_json_reports_dirty_page_metadata_and_writebacks(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "5",
                "--benchmark",
                "compiler-phase-shift",
                "--wsclock-window",
                "1",
                "--dirty-page",
                "1",
                "--dirty-page",
                "2",
                "--dirty-page",
                "3",
                "--dirty-page",
                "4",
                "--dirty-page",
                "5",
                "--dirty-page",
                "6",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        wsclock_result = next(result for result in payload["results"] if result["algorithm"] == "wsclock")
        self.assertEqual(payload["dirty_pages"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(payload["dirty_page_count"], 6)
        self.assertEqual(payload["dirty_page_description"], "1, 2, 3, 4, 5, 6")
        self.assertEqual(wsclock_result["writebacks"], 15)
        self.assertEqual(wsclock_result["page_faults"], 55)

    def test_cli_tune_wsclock_json_recommends_window_for_dirty_workload(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "tune-wsclock",
                "--frames",
                "5",
                "--benchmark",
                "compiler-phase-shift",
                "--min-window",
                "1",
                "--max-window",
                "7",
                "--writeback-penalty",
                "1",
                "--dirty-page",
                "1",
                "--dirty-page",
                "2",
                "--dirty-page",
                "3",
                "--dirty-page",
                "4",
                "--dirty-page",
                "5",
                "--dirty-page",
                "6",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["reference_source"], "benchmark:compiler-phase-shift")
        self.assertEqual(payload["recommended_window"], 7)
        self.assertEqual(payload["recommended"]["writebacks"], 0)
        self.assertEqual(payload["candidate_window_count"], 7)
        self.assertEqual([entry["window"] for entry in payload["pareto_frontier"]], [7])

    def test_cli_tune_wsclock_writes_markdown_and_csv_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "wsclock-tuning.md"
            csv_path = Path(tmpdir) / "wsclock-tuning.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "tune-wsclock",
                    "--frames",
                    "5",
                    "--benchmark",
                    "compiler-phase-shift",
                    "--min-window",
                    "1",
                    "--max-window",
                    "7",
                    "--writeback-penalty",
                    "1",
                    "--dirty-page",
                    "1",
                    "--dirty-page",
                    "2",
                    "--dirty-page",
                    "3",
                    "--dirty-page",
                    "4",
                    "--dirty-page",
                    "5",
                    "--dirty-page",
                    "6",
                    "--markdown-out",
                    str(markdown_path),
                    "--csv-out",
                    str(csv_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            markdown = markdown_path.read_text(encoding="utf-8")
            csv_output = csv_path.read_text(encoding="utf-8")

            self.assertIn("recommended window: 7", completed.stdout)
            self.assertIn("auto window result: not evaluated", completed.stdout)
            self.assertIn("# WSClock Window Tuning Report", markdown)
            self.assertIn("The built-in auto window `10` is outside this sweep", markdown)
            self.assertIn("| τ window | Faults | Hits | Hit rate | Writebacks | Weighted score |", markdown)
            self.assertIn(
                "window,page_faults,hits,hit_rate,fault_rate,writebacks,weighted_score,frame_count,reference_source",
                csv_output,
            )
            self.assertIn("7,52,20,0.277778,0.722222,0,52.0,5,benchmark:compiler-phase-shift", csv_output)

    def test_compare_wsclock_modes_reports_tie_when_adaptive_matches_best_fixed_on_db_benchmark(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["db-hotset-scan"])
        payload = compare_wsclock_modes(
            benchmark_reference,
            5,
            min_window=1,
            max_window=10,
        )
        modes = {entry["mode"]: entry for entry in payload["modes"]}
        self.assertEqual(payload["fixed_window_sweep"]["recommended_window"], 3)
        self.assertEqual(modes["auto-fixed"]["page_faults"], 34)
        self.assertEqual(modes["tuned-fixed"]["page_faults"], 33)
        self.assertEqual(modes["adaptive-heuristic"]["page_faults"], 33)
        self.assertGreaterEqual(payload["adaptive_schedule"]["segment_count"], 2)
        self.assertEqual(payload["winner"]["mode"], "tuned-fixed")
        self.assertEqual(payload["leader_modes"], ["tuned-fixed", "adaptive-heuristic"])
        self.assertEqual(payload["best_fixed_mode"], "tuned-fixed")
        self.assertEqual(payload["adaptive_vs_best_fixed"]["status"], "tied")

    def test_compare_wsclock_modes_adaptive_wins_on_adaptive_phase_turnover_benchmark(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["adaptive-phase-turnover"])
        payload = compare_wsclock_modes(
            benchmark_reference,
            3,
            min_window=1,
            max_window=9,
            segment_length=8,
        )
        modes = {entry["mode"]: entry for entry in payload["modes"]}
        self.assertEqual(modes["auto-fixed"]["page_faults"], 14)
        self.assertEqual(modes["tuned-fixed"]["page_faults"], 14)
        self.assertEqual(modes["adaptive-heuristic"]["page_faults"], 13)
        self.assertEqual(payload["winner"]["mode"], "adaptive-heuristic")
        self.assertEqual(payload["leader_modes"], ["adaptive-heuristic"])
        self.assertEqual(payload["adaptive_vs_best_fixed"]["status"], "better")

    def test_compare_wsclock_modes_clamps_initial_adaptive_window_to_explicit_bounds(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["adaptive-phase-turnover"])
        payload = compare_wsclock_modes(
            benchmark_reference,
            3,
            min_window=1,
            max_window=4,
            segment_length=8,
        )
        first_segment = payload["adaptive_schedule"]["segments"][0]
        self.assertEqual(first_segment["window"], 4)
        self.assertEqual(payload["adaptive_schedule"]["window_range"]["max"], 4)
        self.assertIn("clamped", first_segment["reason"])

    def test_simulate_adaptive_wsclock_reduces_dirty_writebacks_on_compiler_benchmark(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["compiler-phase-shift"])
        auto_result = simulate("wsclock", benchmark_reference, 5, wsclock_window=1, dirty_pages=[1, 2, 3, 4, 5, 6])
        adaptive_result = simulate_adaptive_wsclock(
            benchmark_reference,
            5,
            dirty_pages=[1, 2, 3, 4, 5, 6],
            segment_length=10,
            max_window=10,
        )
        self.assertLessEqual(adaptive_result.page_faults, auto_result.page_faults)
        self.assertLess(adaptive_result.writebacks, auto_result.writebacks)

    def test_cli_compare_wsclock_modes_writes_markdown_and_csv_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "wsclock-modes.md"
            csv_path = Path(tmpdir) / "wsclock-modes.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "compare-wsclock-modes",
                    "--frames",
                    "3",
                    "--benchmark",
                    "adaptive-phase-turnover",
                    "--min-window",
                    "1",
                    "--max-window",
                    "9",
                    "--segment-length",
                    "8",
                    "--markdown-out",
                    str(markdown_path),
                    "--csv-out",
                    str(csv_path),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            markdown = markdown_path.read_text(encoding="utf-8")
            csv_output = csv_path.read_text(encoding="utf-8")

            self.assertEqual(payload["reference_source"], "benchmark:adaptive-phase-turnover")
            self.assertEqual(payload["winner"]["mode"], "adaptive-heuristic")
            self.assertEqual(payload["adaptive_vs_best_fixed"]["status"], "better")
            self.assertIn("# WSClock Fixed vs Adaptive Comparison", markdown)
            self.assertIn("adaptive vs best fixed: **better**", markdown)
            self.assertIn("## Adaptive segment schedule", markdown)
            self.assertIn("adaptive-heuristic", markdown)
            self.assertIn(
                "mode,kind,window_value,window_description,page_faults,hits,hit_rate,fault_rate,writebacks,weighted_score,frame_count,reference_source,segment_length,adaptive_average_window,adaptive_min_window,adaptive_max_window",
                csv_output,
            )
            self.assertIn("adaptive-heuristic,adaptive,,adaptive segments of 8 references using recent reuse p50", csv_output)

    def test_study_wsclock_modes_summarizes_adaptive_outcomes_across_frame_budgets(self) -> None:
        benchmark_reference = load_trace_benchmark_reference(TRACE_BENCHMARKS["adaptive-phase-turnover"])
        payload = study_wsclock_modes(
            benchmark_reference,
            2,
            6,
            min_window=1,
            max_window=9,
            segment_length=8,
        )
        self.assertEqual(payload["summary"]["adaptive_status_counts"], {"better": 1, "tied": 4, "worse": 0})
        self.assertEqual(payload["summary"]["adaptive_better_frames"], [3])
        self.assertEqual(payload["summary"]["best_adaptive_improvement"], {
            "frame_count": 3,
            "status": "better",
            "fault_delta": -1,
            "writeback_delta": 0,
            "score_delta": -1.0,
        })
        frame_three = next(row for row in payload["frame_results"] if row["frame_count"] == 3)
        self.assertEqual(frame_three["winner_mode"], "adaptive-heuristic")
        self.assertEqual(frame_three["modes"]["adaptive-heuristic"]["page_faults"], 13)

    def test_cli_study_wsclock_modes_writes_markdown_svg_and_csv_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "wsclock-mode-study.md"
            svg_path = Path(tmpdir) / "wsclock-mode-study.svg"
            csv_path = Path(tmpdir) / "wsclock-mode-study.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "study-wsclock-modes",
                    "--min-frames",
                    "2",
                    "--max-frames",
                    "6",
                    "--benchmark",
                    "adaptive-phase-turnover",
                    "--min-window",
                    "1",
                    "--max-window",
                    "9",
                    "--segment-length",
                    "8",
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--csv-out",
                    str(csv_path),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            markdown = markdown_path.read_text(encoding="utf-8")
            svg_output = svg_path.read_text(encoding="utf-8")
            csv_output = csv_path.read_text(encoding="utf-8")

            self.assertEqual(payload["reference_source"], "benchmark:adaptive-phase-turnover")
            self.assertEqual(payload["summary"]["adaptive_status_counts"], {"better": 1, "tied": 4, "worse": 0})
            self.assertIn("# WSClock Frame-Budget Study", markdown)
            self.assertIn("better on 1 frame budgets", markdown)
            self.assertIn("Adaptive vs fixed WSClock across frame budgets", svg_output)
            self.assertIn(
                "frame_count,winner_mode,best_fixed_mode,leader_modes,adaptive_status,adaptive_fault_delta,adaptive_writeback_delta,adaptive_score_delta,auto_window,tuned_window,adaptive_segment_length,adaptive_average_window,adaptive_min_window,adaptive_max_window,auto_faults,tuned_faults,adaptive_faults,auto_writebacks,tuned_writebacks,adaptive_writebacks,auto_weighted_score,tuned_weighted_score,adaptive_weighted_score,reference_source",
                csv_output,
            )
            self.assertIn(
                "3,adaptive-heuristic,tuned-fixed,adaptive-heuristic,better,-1,0,-1.0,6,1,8,3.666667,2,6,14,14,13,0,0,0,14.0,14.0,13.0,benchmark:adaptive-phase-turnover",
                csv_output,
            )

    def test_cli_list_presets_json_includes_known_workloads(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "list-presets", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        names = {entry["name"] for entry in payload}
        self.assertTrue(set(WORKLOAD_PRESETS).issubset(names))
        classic = next(entry for entry in payload if entry["name"] == "classic-belady")
        self.assertEqual(classic["reference_length"], len(REFERENCE))

    def test_cli_list_benchmarks_json_includes_known_workloads(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "list-benchmarks", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
        names = {entry["name"] for entry in payload}
        self.assertEqual(names, set(TRACE_BENCHMARKS))
        compiler = next(entry for entry in payload if entry["name"] == "compiler-phase-shift")
        self.assertEqual(compiler["filename"], "compiler-phase-shift.txt")
        self.assertGreater(compiler["reference_length"], len(REFERENCE))

    def test_cli_study_writes_markdown_svg_and_csv_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "study-report.md"
            svg_path = Path(tmpdir) / "study-report.svg"
            csv_path = Path(tmpdir) / "study-report.csv"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "study",
                    "--min-frames",
                    "2",
                    "--max-frames",
                    "5",
                    "--preset",
                    "classic-belady",
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--csv-out",
                    str(csv_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("fifo Belady anomalies:", completed.stdout)
            markdown = markdown_path.read_text(encoding="utf-8")
            svg = svg_path.read_text(encoding="utf-8")
            csv_output = csv_path.read_text(encoding="utf-8")

            self.assertIn("# Page Replacement Study Report", markdown)
            self.assertIn("| Frames | FIFO | CLOCK | AGING | WSCLOCK | LRU | OPT | WSClock τ | Winner |", markdown)
            self.assertIn("- WSClock window: auto (max(4, frames * 2))", markdown)
            self.assertIn("frames 3 -> 4", markdown)
            self.assertIn("<svg", svg)
            self.assertIn("Page faults vs frame count", svg)
            self.assertIn("classic-belady", svg)
            self.assertIn("WSCLOCK", svg)
            self.assertIn(
                "frames,fifo_faults,clock_faults,aging_faults,wsclock_faults,lru_faults,opt_faults,wsclock_window,wsclock_writebacks,best_algorithms,reference_source",
                csv_output,
            )
            self.assertIn("3,9,9,10,10,10,7,6,0,opt,preset:classic-belady", csv_output)

    def test_cli_gallery_writes_html_and_companion_artifacts_for_presets_and_benchmarks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "gallery"
            html_path = artifact_dir / "index.html"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "gallery",
                    "--min-frames",
                    "3",
                    "--max-frames",
                    "7",
                    "--preset",
                    "classic-belady",
                    "--benchmark",
                    "compiler-phase-shift",
                    "--artifact-dir",
                    str(artifact_dir),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("gallery workloads: 2", completed.stdout)
            html = html_path.read_text(encoding="utf-8")
            classic_json = (artifact_dir / "classic-belady-study.json").read_text(encoding="utf-8")
            benchmark_json = (artifact_dir / "compiler-phase-shift-study.json").read_text(encoding="utf-8")
            benchmark_svg = (artifact_dir / "compiler-phase-shift-study.svg").read_text(encoding="utf-8")
            benchmark_markdown = (artifact_dir / "compiler-phase-shift-study.md").read_text(encoding="utf-8")

            self.assertIn("Page Replacement Study Gallery", html)
            self.assertIn("<th>Type</th>", html)
            self.assertIn("href=\"#workload-classic-belady\"", html)
            self.assertIn("id=\"workload-compiler-phase-shift\"", html)
            self.assertIn("compiler-phase-shift-study.svg", html)
            self.assertIn(">benchmark<", html)
            self.assertIn("WSCLOCK", html)
            self.assertIn('"reference_source": "preset:classic-belady"', classic_json)
            self.assertIn('"reference_source": "benchmark:compiler-phase-shift"', benchmark_json)
            self.assertIn('"wsclock": {', benchmark_json)
            self.assertIn("page-replacement-compiler-phase-shift-title", benchmark_svg)
            self.assertIn("benchmark compiler-phase-shift", benchmark_markdown)

    def test_cli_gallery_json_reports_workload_type_and_reference_length(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "gallery"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "gallery",
                    "--min-frames",
                    "3",
                    "--max-frames",
                    "6",
                    "--benchmark",
                    "db-hotset-scan",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(len(payload["workloads"]), 1)
            workload = payload["workloads"][0]
            self.assertEqual(workload["type"], "benchmark")
            self.assertEqual(workload["workload"], "db-hotset-scan")
            self.assertGreater(workload["reference_length"], 40)
            self.assertEqual(workload["reference_source"], "benchmark:db-hotset-scan")

    def test_cli_gallery_accepts_imported_pages_file_workloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "mobile-app-session.txt"
            custom_path.write_text(
                "1 2 3 1 2 4 1 2 5 6 7 5 6 7 8 9 8 9\n",
                encoding="utf-8",
            )
            artifact_dir = Path(tmpdir) / "gallery"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "gallery",
                    "--min-frames",
                    "3",
                    "--max-frames",
                    "6",
                    "--preset",
                    "classic-belady",
                    "--pages-file",
                    str(custom_path),
                    "--artifact-dir",
                    str(artifact_dir),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            html = (artifact_dir / "index.html").read_text(encoding="utf-8")
            custom_json = json.loads((artifact_dir / "mobile-app-session-study.json").read_text(encoding="utf-8"))
            trace_summary_html = (artifact_dir / "mobile-app-session-trace-summary.html").read_text(encoding="utf-8")

            self.assertIn("gallery workloads: 2", completed.stdout)
            self.assertEqual(custom_json["reference_source"], f"pages-file:{custom_path}")
            self.assertIn("custom imported trace", html)
            self.assertIn("custom trace card", html)
            self.assertIn("mobile-app-session-trace-summary.html", html)
            self.assertIn("Page Replacement Trace Summary", trace_summary_html)
            self.assertIn(str(custom_path), trace_summary_html)

    def test_cli_gallery_json_with_only_pages_file_reports_trace_summary_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "one-off-trace.json"
            custom_path.write_text(
                json.dumps([1, 2, 3, 1, 2, 4, 5, 4, 5, 6]),
                encoding="utf-8",
            )
            artifact_dir = Path(tmpdir) / "gallery"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "gallery",
                    "--min-frames",
                    "2",
                    "--max-frames",
                    "5",
                    "--pages-file",
                    str(custom_path),
                    "--artifact-dir",
                    str(artifact_dir),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(len(payload["workloads"]), 1)
            workload = payload["workloads"][0]
            self.assertEqual(workload["type"], "custom")
            self.assertEqual(workload["workload"], "one-off-trace")
            self.assertTrue(workload["reference_source"].startswith("pages-file:"))
            self.assertEqual(workload["trace_summary_paths"]["html"], "one-off-trace-trace-summary.html")
            self.assertGreaterEqual(workload["trace_summary_phase_hint_count"], 0)

    def test_cli_trace_summary_json_writes_markdown_svg_and_html_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "trace-summary.md"
            svg_path = Path(tmpdir) / "trace-summary.svg"
            html_path = Path(tmpdir) / "trace-summary.html"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "trace-summary",
                    "--benchmark",
                    "compiler-phase-shift",
                    "--window-size",
                    "12",
                    "--markdown-out",
                    str(markdown_path),
                    "--svg-out",
                    str(svg_path),
                    "--html-out",
                    str(html_path),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            markdown = markdown_path.read_text(encoding="utf-8")
            svg = svg_path.read_text(encoding="utf-8")
            html = html_path.read_text(encoding="utf-8")

            self.assertEqual(payload["reference_source"], "benchmark:compiler-phase-shift")
            self.assertEqual(payload["window_size"], 12)
            self.assertGreaterEqual(payload["unique_pages"], 8)
            self.assertGreaterEqual(payload["reuses"], 1)
            self.assertIn("# Page Replacement Trace Summary", markdown)
            self.assertIn("## Phase-boundary hints", markdown)
            self.assertIn("benchmark compiler-phase-shift", markdown)
            self.assertIn("<svg", svg)
            self.assertIn("Trace summary card", svg)
            self.assertIn("Reuse-distance buckets", svg)
            self.assertIn("phase 2→3", svg)
            self.assertIn("Page Replacement Trace Summary", html)
            self.assertIn("Downloads: <a href=\"trace-summary.md\">Markdown</a>", html)
            self.assertIn("trace-summary.svg", html)
            self.assertIn("compiler-phase-shift", html)

    def test_cli_trace_compare_writes_side_by_side_artifacts_for_imported_traces(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left_path = Path(tmpdir) / "mobile-app-session.txt"
            right_path = Path(tmpdir) / "reporting-scan-session.txt"
            left_path.write_text(
                "1 2 3 1 2 4 1 2 5 6 7 5 6 7 8 9 8 9\n",
                encoding="utf-8",
            )
            right_path.write_text(
                "1 2 3 4 5 6 7 8 9 10 3 4 11 12 13 14 3 4 15 16 17 18 3 4\n",
                encoding="utf-8",
            )
            artifact_dir = Path(tmpdir) / "trace-compare"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "trace-compare",
                    "--min-frames",
                    "3",
                    "--max-frames",
                    "6",
                    "--pages-file",
                    str(left_path),
                    "--pages-file",
                    str(right_path),
                    "--artifact-dir",
                    str(artifact_dir),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            markdown = Path(payload["paths"]["markdown"]).read_text(encoding="utf-8")
            svg = Path(payload["paths"]["svg"]).read_text(encoding="utf-8")
            csv_output = Path(payload["paths"]["csv"]).read_text(encoding="utf-8")
            html = Path(payload["paths"]["html"]).read_text(encoding="utf-8")
            json_output = Path(payload["paths"]["json"]).read_text(encoding="utf-8")

            self.assertEqual(payload["left"]["workload"], "mobile-app-session")
            self.assertEqual(payload["right"]["workload"], "reporting-scan-session")
            self.assertTrue(payload["left"]["reference_source"].startswith("pages-file:"))
            self.assertTrue(payload["right"]["reference_source"].startswith("pages-file:"))
            self.assertIn(payload["summary"]["overall_better_average_fault_rate"], {"left", "right", "tie"})
            self.assertIn("# Page Replacement Imported Trace Comparison", markdown)
            self.assertIn("## Frame-by-frame comparison", markdown)
            self.assertIn("<svg", svg)
            self.assertIn("Imported trace comparison card", svg)
            self.assertIn(
                "frame_count,wsclock_window,algorithm,left_workload,right_workload,left_faults,right_faults",
                csv_output,
            )
            self.assertIn("Page Replacement Imported Trace Comparison", html)
            self.assertIn("Average algorithm comparison", html)
            self.assertIn("WSCLOCK", html)
            self.assertIn("Downloads:", html)
            self.assertIn("\"html_path\"", json_output)
            self.assertIn("mobile-app-session", json_output)

    def test_cli_trace_compare_requires_exactly_two_pages_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            only_path = Path(tmpdir) / "only-trace.txt"
            only_path.write_text("1 2 3 1 2 4 5 4 5 6\n", encoding="utf-8")
            artifact_dir = Path(tmpdir) / "trace-compare"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "trace-compare",
                    "--min-frames",
                    "2",
                    "--max-frames",
                    "5",
                    "--pages-file",
                    str(only_path),
                    "--artifact-dir",
                    str(artifact_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("trace-compare needs exactly two --pages-file inputs", completed.stderr)

    def test_cli_aggregate_writes_dashboard_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "aggregate"
            html_path = artifact_dir / "index.html"
            svg_path = artifact_dir / "aggregate-average-fault-rate.svg"
            csv_path = artifact_dir / "aggregate-workload-comparison.csv"
            json_path = artifact_dir / "aggregate-summary.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "aggregate",
                    "--min-frames",
                    "3",
                    "--max-frames",
                    "7",
                    "--preset",
                    "classic-belady",
                    "--benchmark",
                    "compiler-phase-shift",
                    "--artifact-dir",
                    str(artifact_dir),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            html = html_path.read_text(encoding="utf-8")
            svg = svg_path.read_text(encoding="utf-8")
            csv_output = csv_path.read_text(encoding="utf-8")

            self.assertIn("aggregate workloads: 2", completed.stdout)
            self.assertEqual(payload["summary"]["workload_count"], 2)
            self.assertEqual(payload["summary"]["benchmark_count"], 1)
            self.assertIn("Page Replacement Aggregate Dashboard", html)
            self.assertIn("aggregate-average-fault-rate.svg", html)
            self.assertIn("aggregate-summary.json", html)
            self.assertIn("Normalized average page-fault rate by workload", svg)
            self.assertIn("compiler-phase-shift", svg)
            self.assertIn(
                "type,workload,reference_source,reference_length,best_average_fault_algorithms,best_average_fault_rate_algorithms,fifo_has_anomaly,non_fifo_regression_count,wsclock_avg_writebacks,fifo_avg_faults,clock_avg_faults,aging_avg_faults,wsclock_avg_faults,lru_avg_faults,opt_avg_faults,fifo_avg_fault_rate,clock_avg_fault_rate,aging_avg_fault_rate,wsclock_avg_fault_rate,lru_avg_fault_rate,opt_avg_fault_rate",
                csv_output,
            )
            self.assertEqual({entry["workload"] for entry in payload["workloads"]}, {"classic-belady", "compiler-phase-shift"})
            self.assertIn("overall_average_fault_rates", payload["summary"])

    def test_cli_aggregate_json_reports_normalized_rates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir) / "aggregate"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "aggregate",
                    "--min-frames",
                    "3",
                    "--max-frames",
                    "6",
                    "--benchmark",
                    "db-hotset-scan",
                    "--artifact-dir",
                    str(artifact_dir),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["summary"]["workload_count"], 1)
            self.assertEqual(payload["summary"]["benchmark_count"], 1)
            self.assertEqual(payload["workloads"][0]["workload"], "db-hotset-scan")
            self.assertEqual(payload["workloads"][0]["reference_source"], "benchmark:db-hotset-scan")
            self.assertGreater(payload["workloads"][0]["average_fault_rates"]["fifo"], 0)
            self.assertIn("overall_best_rate_winners", payload["summary"])
            self.assertIn("overall_average_wsclock_writebacks", payload["summary"])


    def test_cli_aggregate_accepts_imported_pages_file_workloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "mobile-app-session.txt"
            custom_path.write_text(
                "1 2 3 1 2 4 1 2 5 6 7 5 6 7 8 9 8 9\n",
                encoding="utf-8",
            )
            artifact_dir = Path(tmpdir) / "aggregate"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "aggregate",
                    "--min-frames",
                    "3",
                    "--max-frames",
                    "6",
                    "--preset",
                    "classic-belady",
                    "--pages-file",
                    str(custom_path),
                    "--artifact-dir",
                    str(artifact_dir),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            payload = json.loads((artifact_dir / "aggregate-summary.json").read_text(encoding="utf-8"))
            html = (artifact_dir / "index.html").read_text(encoding="utf-8")
            csv_output = (artifact_dir / "aggregate-workload-comparison.csv").read_text(encoding="utf-8")

            self.assertIn("aggregate workloads: 2", completed.stdout)
            self.assertEqual(payload["summary"]["workload_count"], 2)
            self.assertEqual(payload["summary"]["benchmark_count"], 0)
            self.assertEqual(payload["summary"]["custom_count"], 1)
            custom_workload = next(entry for entry in payload["workloads"] if entry["type"] == "custom")
            self.assertEqual(custom_workload["workload"], "mobile-app-session")
            self.assertTrue(custom_workload["reference_source"].startswith("pages-file:"))
            self.assertIn("custom imported trace", html)
            self.assertIn("pages-file:", html)
            self.assertIn("custom,mobile-app-session,pages-file:", csv_output)

    def test_cli_aggregate_json_with_only_pages_file_skips_default_presets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "one-off-trace.json"
            custom_path.write_text(json.dumps([1, 2, 3, 1, 2, 4, 5, 4, 5, 6, 7, 6, 7]), encoding="utf-8")
            artifact_dir = Path(tmpdir) / "aggregate"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "aggregate",
                    "--min-frames",
                    "2",
                    "--max-frames",
                    "5",
                    "--pages-file",
                    str(custom_path),
                    "--artifact-dir",
                    str(artifact_dir),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["summary"]["workload_count"], 1)
            self.assertEqual(payload["summary"]["custom_count"], 1)
            self.assertEqual(payload["summary"]["benchmark_count"], 0)
            self.assertEqual(payload["workloads"][0]["type"], "custom")
            self.assertEqual(payload["workloads"][0]["workload"], "one-off-trace")
            self.assertTrue(payload["workloads"][0]["reference_source"].startswith("pages-file:"))

    def test_cli_rejects_missing_reference(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "simulate", "fifo", "--frames", "3"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("provide at least one --page", completed.stderr)
        self.assertIn("--benchmark", completed.stderr)

    def test_cli_rejects_mixed_preset_and_explicit_pages(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "3",
                "--preset",
                "classic-belady",
                "--page",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("use exactly one of --preset, --benchmark, or explicit --page/--pages-file input", completed.stderr)

    def test_cli_rejects_mixed_preset_and_benchmark(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "compare",
                "--frames",
                "3",
                "--preset",
                "classic-belady",
                "--benchmark",
                "compiler-phase-shift",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("use either --preset or --benchmark, not both", completed.stderr)


if __name__ == "__main__":
    unittest.main()
