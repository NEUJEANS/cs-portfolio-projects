from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from regex_engine_lab import RegexEngine, RegexSyntaxError


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

    def test_cli_reports_syntax_errors(self) -> None:
        completed = self.run_cli("fullmatch", "[abc", "a")
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
