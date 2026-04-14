import json
import subprocess
import sys
import unittest
from pathlib import Path

from password_auditor import evaluate, format_text_report

PROJECT_DIR = Path(__file__).resolve().parent


class PasswordAuditorTests(unittest.TestCase):
    def test_weak_common_password(self):
        result = evaluate("password")
        self.assertEqual(result["rating"], "weak")
        self.assertIn("common password", result["reasons"])
        self.assertIn("too short", result["reasons"])

    def test_strong_password(self):
        result = evaluate("M0on!River!2026")
        self.assertEqual(result["rating"], "strong")
        self.assertGreaterEqual(result["score"], 7)
        self.assertEqual(result["reasons"], [])

    def test_repeated_and_sequential_patterns_are_flagged(self):
        result = evaluate("Abcd1111!!")
        self.assertEqual(result["rating"], "weak")
        self.assertIn("contains repeated characters", result["reasons"])
        self.assertIn("contains sequential keyboard/alphabet pattern", result["reasons"])

    def test_text_report_contains_actionable_sections(self):
        report = format_text_report(evaluate("password"))
        self.assertIn("Rating: weak", report)
        self.assertIn("Character sets:", report)
        self.assertIn("Suggestions:", report)

    def test_cli_json_output(self):
        completed = subprocess.run(
            [sys.executable, "password_auditor.py", "BetterPass!2026", "--json"],
            cwd=PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["rating"], "strong")
        self.assertIn("character_sets", payload)


if __name__ == "__main__":
    unittest.main()
