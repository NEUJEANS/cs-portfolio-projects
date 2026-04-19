from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from regex_engine_lab import (
    BenchmarkCase,
    BenchmarkSuiteError,
    RegexEngine,
    RegexSyntaxError,
    filter_benchmark_cases,
    load_benchmark_suite,
    render_benchmark_html,
    render_benchmark_markdown,
    run_benchmark_report,
)


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "regex_engine_lab.py"


class RegexEngineTests(unittest.TestCase):
    def test_fullmatch_with_literal_and_quantifiers(self) -> None:
        engine = RegexEngine("ab+c")
        self.assertTrue(engine.fullmatch("abbc"))
        self.assertFalse(engine.fullmatch("ac"))

    def test_alternation_grouping_and_search(self) -> None:
        engine = RegexEngine("(cat|dog)s?")
        result = engine.search("two dogs walked by")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["match"], "dogs")

    def test_alternation_fullmatch(self) -> None:
        engine = RegexEngine("ab|cd")
        self.assertTrue(engine.fullmatch("cd"))
        self.assertFalse(engine.fullmatch("ad"))

    def test_character_classes_and_negation(self) -> None:
        engine = RegexEngine("[^0-9][a-c]+")
        self.assertTrue(engine.fullmatch("zaac"))
        self.assertFalse(engine.fullmatch("1aac"))

    def test_dot_and_anchors(self) -> None:
        engine = RegexEngine("^a.+z$")
        self.assertTrue(engine.fullmatch("abcz"))
        self.assertFalse(engine.search("xxabczxx"))

    def test_escape_shorthand_classes_outside_brackets(self) -> None:
        self.assertTrue(RegexEngine(r"\d+\w+\s\S").fullmatch("42code X"))
        self.assertTrue(RegexEngine(r"\D+").fullmatch("code!"))
        self.assertFalse(RegexEngine(r"\D+").fullmatch("code2"))
        self.assertTrue(RegexEngine(r"\W+").fullmatch("?!"))

    def test_escape_shorthand_classes_inside_brackets(self) -> None:
        self.assertTrue(RegexEngine(r"[A-F\d]+").fullmatch("FACE2026"))
        self.assertTrue(RegexEngine(r"[\d-]+").fullmatch("2026-04-19"))
        self.assertTrue(RegexEngine(r"[^\s]+").fullmatch("tab-separated"))
        self.assertFalse(RegexEngine(r"[^\s]+").fullmatch("has space"))

    def test_empty_pattern_matches_empty_string(self) -> None:
        engine = RegexEngine("")
        self.assertTrue(engine.fullmatch(""))
        self.assertEqual(engine.search("abc"), {"matched": True, "start": 0, "end": 0, "match": ""})

    def test_explain_contains_ast_and_states(self) -> None:
        engine = RegexEngine(r"\d+[A-Z]")
        payload = engine.explain()
        self.assertEqual(payload["pattern"], r"\d+[A-Z]")
        self.assertIn("ast", payload)
        self.assertGreater(len(payload["states"]), 0)
        first_repeat_node = payload["ast"]["parts"][0]
        self.assertEqual(first_repeat_node["type"], "repeat")
        self.assertEqual(first_repeat_node["node"]["type"], "class")
        self.assertEqual(first_repeat_node["node"]["terms"][0]["chars"], "0123456789")
        self.assertTrue(any(state.get("chars") == "0123456789" for state in payload["states"]))

    def test_trace_fullmatch_reports_stepwise_state_sets(self) -> None:
        payload = RegexEngine(r"^ID-\d\d\d\d-\w+$").trace("ID-2026-demo_user", mode="fullmatch")
        self.assertTrue(payload["matched"])
        self.assertEqual(payload["mode"], "fullmatch")
        self.assertEqual(payload["steps"][0]["phase"], "start")
        consume_steps = [step for step in payload["steps"] if step["phase"] == "consume"]
        self.assertEqual(len(consume_steps), len("ID-2026-demo_user"))
        self.assertEqual(consume_steps[0]["char"], "I")
        self.assertTrue(any(transition["matched"] for transition in consume_steps[0]["transitions"]))
        self.assertEqual(payload["steps"][-1]["phase"], "final")
        self.assertTrue(payload["steps"][-1]["matched"])

    def test_trace_fullmatch_marks_early_stop_on_failure(self) -> None:
        payload = RegexEngine("ab").trace("axy", mode="fullmatch")
        self.assertFalse(payload["matched"])
        self.assertTrue(payload["stopped_early"])
        self.assertEqual(payload["steps"][-1]["phase"], "final")
        self.assertEqual(payload["steps"][-1]["position"], 2)
        self.assertEqual(payload["steps"][-1]["closure_states"], [])

    def test_trace_search_reports_attempts_and_first_match(self) -> None:
        payload = RegexEngine("(cat|dog)s?").trace("xxdogs", mode="search")
        self.assertTrue(payload["matched"])
        self.assertEqual(payload["mode"], "search")
        self.assertEqual(payload["result"]["match"], "dogs")
        self.assertEqual(payload["result"]["start"], 2)
        self.assertGreaterEqual(len(payload["attempts"]), 3)
        winning_attempt = payload["attempts"][-1]
        self.assertTrue(winning_attempt["result"]["matched"])
        self.assertEqual(winning_attempt["result"]["match"], "dogs")
        self.assertEqual(winning_attempt["steps"][0]["phase"], "start")

    def test_invalid_patterns_raise_syntax_error(self) -> None:
        with self.assertRaises(RegexSyntaxError):
            RegexEngine("(")
        with self.assertRaises(RegexSyntaxError):
            RegexEngine("[z-a]")
        with self.assertRaises(RegexSyntaxError):
            RegexEngine(r"[a-\d]")

    def test_benchmark_report_agrees_with_python_re(self) -> None:
        report = run_benchmark_report(
            [BenchmarkCase("id", r"^ID-\d\d\d\d-\w+$", "ID-2026-demo_user", tags=("demo", "anchored"))],
            iterations=3,
            warmup=0,
            suite_label="unit",
        )
        self.assertEqual(report["suite_label"], "unit")
        self.assertTrue(report["all_cases_agree"])
        self.assertEqual(report["case_count"], 1)
        self.assertEqual(report["suite_tags"], ["anchored", "demo"])
        case = report["cases"][0]
        self.assertTrue(case["agreement"])
        self.assertEqual(case["lab_result"], {"matched": True})
        self.assertEqual(case["python_result"], {"matched": True})
        self.assertIn(case["faster_engine"], {"lab", "python_re", "tie"})

    def test_render_benchmark_markdown_includes_case_table(self) -> None:
        report = run_benchmark_report(
            [BenchmarkCase("dogs", "(cat|dog)s?", "xxdogs", mode="search", tags=("demo", "search"))],
            iterations=2,
            warmup=0,
            suite_label="unit",
            applied_filters={"include_tags": ["demo"], "exclude_tags": []},
        )
        markdown = render_benchmark_markdown(report)
        self.assertIn("# Regex engine benchmark report", markdown)
        self.assertIn("| case | mode | tags | agreement |", markdown)
        self.assertIn("applied filters", markdown)
        self.assertIn("### dogs", markdown)
        self.assertIn("`search`", markdown)
        self.assertIn("demo, search", markdown)

    def test_render_benchmark_html_includes_summary_and_case_notes(self) -> None:
        report = run_benchmark_report(
            [
                BenchmarkCase("dogs", "(cat|dog)s?", "xxdogs", mode="search", tags=("demo", "search")),
                BenchmarkCase("id", r"^ID-\d+$", "ID-42", tags=("demo", "anchored")),
            ],
            iterations=2,
            warmup=0,
            suite_label="unit-dashboard",
            suite_source="suite.json",
            applied_filters={"include_tags": ["demo"], "exclude_tags": []},
        )
        html = render_benchmark_html(report)
        self.assertIn("<title>Regex engine benchmark dashboard — unit-dashboard</title>", html)
        self.assertIn("Benchmark dashboard — unit-dashboard", html)
        self.assertIn("Case-by-case table", html)
        self.assertIn("suite.json", html)
        self.assertIn("include demo", html)
        self.assertIn("<code>dogs</code>", html)
        self.assertIn("agreement: yes", html)
        self.assertIn("search · 1", html)

    def test_load_benchmark_suite_reads_named_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "suite.json"
            suite_path.write_text(
                json.dumps(
                    {
                        "suite_label": "portfolio-workload",
                        "cases": [
                            {
                                "label": "anchored-id",
                                "pattern": r"^ID-\d\d\d\d-\w+$",
                                "text": "ID-2026-demo_user",
                                "tags": ["interview-demo", "anchored"],
                            },
                            {
                                "label": "pet-search",
                                "pattern": "(cat|dog)s?",
                                "text": "xxdogs walked by",
                                "mode": "search",
                                "tags": ["interview-demo", "search"],
                            },
                        ],
                    },
                    indent=2,
                )
            )
            suite_label, cases = load_benchmark_suite(str(suite_path))

        self.assertEqual(suite_label, "portfolio-workload")
        self.assertEqual([case.label for case in cases], ["anchored-id", "pet-search"])
        self.assertEqual(cases[0].tags, ("interview-demo", "anchored"))
        self.assertEqual(cases[1].mode, "search")

    def test_load_benchmark_suite_rejects_invalid_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "suite.json"
            suite_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "label": "bad-case",
                                "pattern": "abc",
                                "text": "abc",
                                "mode": "contains",
                            }
                        ]
                    }
                )
            )
            with self.assertRaises(BenchmarkSuiteError):
                load_benchmark_suite(str(suite_path))

    def test_load_benchmark_suite_rejects_duplicate_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "suite.json"
            suite_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "label": "repeat-case",
                                "pattern": "abc",
                                "text": "abc",
                            },
                            {
                                "label": "repeat-case",
                                "pattern": "def",
                                "text": "def",
                            },
                        ]
                    }
                )
            )
            with self.assertRaises(BenchmarkSuiteError):
                load_benchmark_suite(str(suite_path))

    def test_load_benchmark_suite_rejects_duplicate_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "suite.json"
            suite_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "label": "repeat-tag-case",
                                "pattern": "abc",
                                "text": "abc",
                                "tags": ["demo", "demo"],
                            }
                        ]
                    }
                )
            )
            with self.assertRaises(BenchmarkSuiteError):
                load_benchmark_suite(str(suite_path))

    def test_filter_benchmark_cases_selects_tagged_subset(self) -> None:
        cases, filters = filter_benchmark_cases(
            [
                BenchmarkCase("id", r"^ID-\d+$", "ID-42", tags=("interview-demo", "anchored")),
                BenchmarkCase("search", "dog", "hotdog", mode="search", tags=("portfolio-batch", "search")),
                BenchmarkCase("spaces", r"^\s+$", " ", tags=("portfolio-batch", "whitespace")),
            ],
            include_tags=["portfolio-batch"],
            exclude_tags=["whitespace"],
        )
        self.assertEqual([case.label for case in cases], ["search"])
        self.assertEqual(filters, {"include_tags": ["portfolio-batch"], "exclude_tags": ["whitespace"]})

    def test_filter_benchmark_cases_normalizes_requested_tag_whitespace_and_case(self) -> None:
        cases, filters = filter_benchmark_cases(
            [
                BenchmarkCase("id", r"^ID-\d+$", "ID-42", tags=("interview-demo", "anchored")),
                BenchmarkCase("spaces", r"^\s+$", " ", tags=("portfolio-batch", "whitespace")),
            ],
            include_tags=[" Interview-Demo "],
            exclude_tags=[" whitespace "],
        )
        self.assertEqual([case.label for case in cases], ["id"])
        self.assertEqual(filters, {"include_tags": ["interview-demo"], "exclude_tags": ["whitespace"]})


class RegexEngineCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=PROJECT_DIR,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_fullmatch(self) -> None:
        completed = self.run_cli("fullmatch", "colou?r", "color")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout), {"matched": True})

    def test_cli_search(self) -> None:
        completed = self.run_cli("search", "[a-z]+", "123abc456")
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["matched"])
        self.assertEqual(payload["match"], "abc")

    def test_cli_shorthand_classes(self) -> None:
        completed = self.run_cli("search", r"\d+\s\w+", "build 2026 portfolio")
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["matched"])
        self.assertEqual(payload["match"], "2026 portfolio")

    def test_cli_explain(self) -> None:
        completed = self.run_cli("explain", "a|b")
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["pattern"], "a|b")
        self.assertIn("states", payload)

    def test_cli_trace_fullmatch(self) -> None:
        completed = self.run_cli("trace", r"^ID-\d\d\d\d-\w+$", "ID-2026-demo_user")
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "fullmatch")
        self.assertTrue(payload["matched"])
        self.assertEqual(payload["steps"][0]["phase"], "start")
        self.assertEqual(payload["steps"][-1]["phase"], "final")

    def test_cli_trace_search_mode(self) -> None:
        completed = self.run_cli("trace", "(cat|dog)s?", "xxdogs", "--mode", "search")
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["mode"], "search")
        self.assertTrue(payload["matched"])
        self.assertEqual(payload["result"]["match"], "dogs")

    def test_cli_benchmark_single_case(self) -> None:
        completed = self.run_cli(
            "benchmark",
            r"^ID-\d\d\d\d-\w+$",
            "ID-2026-demo_user",
            "--iterations",
            "3",
            "--warmup",
            "0",
            "--label",
            "id-case",
        )
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["suite_label"], "id-case")
        self.assertTrue(payload["all_cases_agree"])
        self.assertEqual(payload["cases"][0]["lab_result"], {"matched": True})

    def test_cli_benchmark_sample_suite_writes_markdown_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = Path(temp_dir) / "benchmark.md"
            json_path = Path(temp_dir) / "benchmark.json"
            html_path = Path(temp_dir) / "benchmark.html"
            completed = self.run_cli(
                "benchmark",
                "--sample-suite",
                "--iterations",
                "1",
                "--warmup",
                "0",
                "--markdown-out",
                str(markdown_path),
                "--json-out",
                str(json_path),
                "--html-out",
                str(html_path),
            )
            self.assertEqual(completed.returncode, 0)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["suite_label"], "sample-suite")
            self.assertEqual(payload["case_count"], 3)
            self.assertEqual(payload["suite_source"], "built-in defaults")
            self.assertTrue(markdown_path.exists())
            self.assertTrue(json_path.exists())
            self.assertTrue(html_path.exists())
            self.assertIn("Regex engine benchmark report", markdown_path.read_text())
            self.assertIn("Regex engine benchmark dashboard", html_path.read_text())
            written_json = json.loads(json_path.read_text())
            self.assertEqual(written_json["case_count"], 3)

    def test_cli_benchmark_suite_file_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "suite.json"
            markdown_path = Path(temp_dir) / "suite-report.md"
            json_path = Path(temp_dir) / "suite-report.json"
            suite_path.write_text(
                json.dumps(
                    {
                        "suite_label": "portfolio-workload",
                        "cases": [
                            {
                                "label": "anchored-id",
                                "pattern": r"^ID-\d\d\d\d-\w+$",
                                "text": "ID-2026-demo_user",
                                "tags": ["interview-demo", "anchored"],
                            },
                            {
                                "label": "pet-search",
                                "pattern": "(cat|dog)s?",
                                "text": "xxdogs walked by",
                                "mode": "search",
                                "tags": ["interview-demo", "search"],
                            },
                        ],
                    },
                    indent=2,
                )
            )
            completed = self.run_cli(
                "benchmark",
                "--suite-file",
                str(suite_path),
                "--iterations",
                "1",
                "--warmup",
                "0",
                "--markdown-out",
                str(markdown_path),
                "--json-out",
                str(json_path),
            )
            self.assertEqual(completed.returncode, 0)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["suite_label"], "portfolio-workload")
            self.assertEqual(payload["case_count"], 2)
            self.assertEqual(payload["suite_source"], str(suite_path))
            self.assertEqual(payload["suite_tags"], ["anchored", "interview-demo", "search"])
            self.assertEqual(payload["case_definitions"][1]["mode"], "search")
            self.assertEqual(payload["case_definitions"][1]["tags"], ["interview-demo", "search"])
            self.assertTrue(markdown_path.exists())
            self.assertTrue(json_path.exists())
            self.assertIn("suite source", markdown_path.read_text())
            written_json = json.loads(json_path.read_text())
            self.assertEqual(written_json["case_count"], 2)

    def test_cli_benchmark_suite_file_filters_by_tag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "suite.json"
            suite_path.write_text(
                json.dumps(
                    {
                        "suite_label": "portfolio-workload",
                        "cases": [
                            {
                                "label": "anchored-id",
                                "pattern": r"^ID-\d\d\d\d-\w+$",
                                "text": "ID-2026-demo_user",
                                "tags": ["interview-demo", "anchored"],
                            },
                            {
                                "label": "pet-search",
                                "pattern": "(cat|dog)s?",
                                "text": "xxdogs walked by",
                                "mode": "search",
                                "tags": ["interview-demo", "search"],
                            },
                            {
                                "label": "whitespace-fullmatch",
                                "pattern": r"^\s+$",
                                "text": " \t",
                                "tags": ["portfolio-batch", "whitespace"],
                            },
                        ],
                    },
                    indent=2,
                )
            )
            completed = self.run_cli(
                "benchmark",
                "--suite-file",
                str(suite_path),
                "--include-tag",
                "interview-demo",
                "--exclude-tag",
                "search",
                "--iterations",
                "1",
                "--warmup",
                "0",
            )
            self.assertEqual(completed.returncode, 0)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["case_count"], 1)
            self.assertEqual([case["label"] for case in payload["cases"]], ["anchored-id"])
            self.assertEqual(payload["applied_filters"], {"include_tags": ["interview-demo"], "exclude_tags": ["search"]})

    def test_cli_reports_invalid_benchmark_suite_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "broken.json"
            suite_path.write_text('{"cases": [{"label": "oops", "pattern": "abc", "text": 5}]}')
            completed = self.run_cli("benchmark", "--suite-file", str(suite_path), "--iterations", "1", "--warmup", "0")
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertIn("error", payload)

    def test_cli_reports_empty_tag_selection_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            suite_path = Path(temp_dir) / "suite.json"
            suite_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "label": "anchored-id",
                                "pattern": r"^ID-\d+$",
                                "text": "ID-42",
                                "tags": ["interview-demo"]
                            }
                        ]
                    }
                )
            )
            completed = self.run_cli(
                "benchmark",
                "--suite-file",
                str(suite_path),
                "--include-tag",
                "portfolio-batch",
                "--iterations",
                "1",
                "--warmup",
                "0",
            )
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertIn("error", payload)

    def test_cli_reports_invalid_benchmark_tag_filters(self) -> None:
        completed = self.run_cli(
            "benchmark",
            "--sample-suite",
            "--include-tag",
            "interview-demo",
            "--exclude-tag",
            "interview-demo",
            "--iterations",
            "1",
            "--warmup",
            "0",
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertIn("error", payload)

    def test_cli_reports_invalid_benchmark_pattern_errors(self) -> None:
        completed = self.run_cli("benchmark", "[abc", "a", "--iterations", "1", "--warmup", "0")
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertIn("error", payload)

    def test_cli_reports_syntax_errors(self) -> None:
        completed = self.run_cli("fullmatch", "[abc", "a")
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
