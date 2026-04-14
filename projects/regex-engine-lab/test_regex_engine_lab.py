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

    def test_empty_pattern_matches_empty_string(self) -> None:
        engine = RegexEngine("")
        self.assertTrue(engine.fullmatch(""))
        self.assertEqual(engine.search("abc"), {"matched": True, "start": 0, "end": 0, "match": ""})

    def test_explain_contains_ast_and_states(self) -> None:
        engine = RegexEngine("ab|cd")
        payload = engine.explain()
        self.assertEqual(payload["pattern"], "ab|cd")
        self.assertIn("ast", payload)
        self.assertGreater(len(payload["states"]), 0)

    def test_invalid_patterns_raise_syntax_error(self) -> None:
        with self.assertRaises(RegexSyntaxError):
            RegexEngine("(")
        with self.assertRaises(RegexSyntaxError):
            RegexEngine("[z-a]")


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

    def test_cli_explain(self) -> None:
        completed = self.run_cli("explain", "a|b")
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["pattern"], "a|b")
        self.assertIn("states", payload)

    def test_cli_reports_syntax_errors(self) -> None:
        completed = self.run_cli("fullmatch", "[abc", "a")
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertIn("error", payload)


if __name__ == "__main__":
    unittest.main()
