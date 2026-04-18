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
    TRACE_BENCHMARKS,
    WORKLOAD_PRESETS,
    compare_algorithms,
    parse_reference_args,
    simulate,
    study_frame_counts,
)


REFERENCE = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
SCRIPT = PROJECT_DIR / "page_replacement_lab.py"


class PageReplacementSimulationTests(unittest.TestCase):
    def test_classic_reference_fault_counts_include_clock(self) -> None:
        self.assertEqual(simulate("fifo", REFERENCE, 3).page_faults, 9)
        self.assertEqual(simulate("clock", REFERENCE, 3).page_faults, 9)
        self.assertEqual(simulate("lru", REFERENCE, 3).page_faults, 10)
        self.assertEqual(simulate("opt", REFERENCE, 3).page_faults, 7)

    def test_compare_algorithms_orders_all_strategies(self) -> None:
        results = compare_algorithms(REFERENCE, 4)
        self.assertEqual([result.algorithm for result in results], ["fifo", "clock", "lru", "opt"])
        self.assertEqual([result.page_faults for result in results], [10, 10, 8, 6])

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

    def test_parse_reference_accepts_presets(self) -> None:
        parsed = parse_reference_args([], None, "classic-belady")
        self.assertEqual(parsed.source, "preset:classic-belady")
        self.assertEqual(parsed.reference_string, REFERENCE)

    def test_parse_reference_accepts_benchmarks(self) -> None:
        parsed = parse_reference_args([], None, None, "compiler-phase-shift")
        self.assertEqual(parsed.source, "benchmark:compiler-phase-shift")
        self.assertGreater(len(parsed.reference_string), len(REFERENCE))
        self.assertEqual(parsed.reference_string[:8], [1, 2, 3, 4, 1, 2, 5, 6])

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
        self.assertEqual(payload["results"][1]["algorithm"], "clock")
        self.assertEqual(payload["results"][3]["page_faults"], 7)

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
            ["fifo", "clock", "lru", "opt"],
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
        self.assertEqual(len(payload["results"]), 4)

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
            self.assertIn("| Frames | FIFO | Clock | LRU | OPT | Winner |", markdown)
            self.assertIn("frames 3 -> 4", markdown)
            self.assertIn("<svg", svg)
            self.assertIn("Page faults vs frame count", svg)
            self.assertIn("classic-belady", svg)
            self.assertIn(
                "frames,fifo_faults,clock_faults,lru_faults,opt_faults,best_algorithms,reference_source",
                csv_output,
            )
            self.assertIn("3,9,9,10,7,opt,preset:classic-belady", csv_output)

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
            self.assertIn('"reference_source": "preset:classic-belady"', classic_json)
            self.assertIn('"reference_source": "benchmark:compiler-phase-shift"', benchmark_json)
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
