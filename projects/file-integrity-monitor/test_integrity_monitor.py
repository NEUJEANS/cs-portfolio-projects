import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from integrity_monitor import build_manifest, diff_snapshots, format_text_report, should_include

SCRIPT = Path(__file__).with_name("integrity_monitor.py")


class IntegrityMonitorTests(unittest.TestCase):
    def test_detect_added_removed_and_changed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("hello")
            (root / "b.txt").write_text("keep")
            old = build_manifest(root)

            (root / "a.txt").write_text("bye")
            (root / "b.txt").unlink()
            (root / "c.txt").write_text("new")
            new = build_manifest(root)

            diff = diff_snapshots(old, new)
            self.assertEqual(diff["changed"], ["a.txt"])
            self.assertEqual(diff["removed"], ["b.txt"])
            self.assertEqual(diff["added"], ["c.txt"])
            self.assertEqual(
                diff["summary"],
                {"added": 1, "removed": 1, "changed": 1, "unchanged": 0, "has_changes": True},
            )

    def test_ignore_patterns_exclude_matching_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "keep.txt").write_text("keep")
            (root / "skip.log").write_text("skip")

            manifest = build_manifest(root, ignore_patterns=["*.log"])
            self.assertIn("keep.txt", manifest["files"])
            self.assertNotIn("skip.log", manifest["files"])
            self.assertTrue(should_include("nested/data.txt", ["*.log"]))
            self.assertFalse(should_include("skip.log", ["*.log"]))

    def test_text_report_contains_summary_and_sections(self):
        diff = {
            "added": ["new.txt"],
            "removed": ["old.txt"],
            "changed": ["config.json"],
            "unchanged": ["same.txt"],
            "summary": {"added": 1, "removed": 1, "changed": 1, "unchanged": 1, "has_changes": True},
        }
        report = format_text_report(diff)
        self.assertIn("Integrity diff summary", report)
        self.assertIn("ADDED", report)
        self.assertIn("config.json", report)

    def test_legacy_snapshot_format_remains_supported(self):
        old = {"a.txt": "oldhash"}
        new = {"a.txt": "newhash", "b.txt": "same"}
        diff = diff_snapshots(old, new)
        self.assertEqual(diff["changed"], ["a.txt"])
        self.assertEqual(diff["added"], ["b.txt"])

    def test_cli_scan_output_and_diff_text_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "snapshots" / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")
            (data_path / "ignore.tmp").write_text("tmp")

            scan = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "scan",
                    str(data_path),
                    "--ignore",
                    "*.tmp",
                    "--output",
                    str(baseline_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = json.loads(scan.stdout)
            self.assertEqual(manifest["algorithm"], "sha256")
            self.assertEqual(manifest["file_count"], 1)
            self.assertTrue(baseline_path.exists())

            (data_path / "alpha.txt").write_text("updated")
            (data_path / "beta.txt").write_text("beta")

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--format",
                    "text",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("changed: 1", diff.stdout)
            self.assertIn("added: 1", diff.stdout)
            self.assertIn("beta.txt", diff.stdout)


if __name__ == "__main__":
    unittest.main()
