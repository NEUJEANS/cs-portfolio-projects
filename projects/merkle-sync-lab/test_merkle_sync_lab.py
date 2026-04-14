from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("merkle_sync_lab.py")
SPEC = importlib.util.spec_from_file_location("merkle_sync_lab", MODULE_PATH)
merkle_sync_lab = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = merkle_sync_lab
SPEC.loader.exec_module(merkle_sync_lab)
build_manifest = merkle_sync_lab.build_manifest
summarize_diff = merkle_sync_lab.summarize_diff


class MerkleSyncLabTests(unittest.TestCase):
    def test_manifest_is_stable_for_same_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "a.txt").write_text("hello\n", encoding="utf-8")
            (root / "docs" / "b.txt").write_text("world\n", encoding="utf-8")

            manifest_one = build_manifest(root)
            manifest_two = build_manifest(root)

            self.assertEqual(manifest_one["root_digest"], manifest_two["root_digest"])
            self.assertEqual(manifest_one["files"], manifest_two["files"])

    def test_diff_reports_added_removed_and_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as left_tmp, tempfile.TemporaryDirectory() as right_tmp:
            left = Path(left_tmp)
            right = Path(right_tmp)
            (left / "src").mkdir()
            (right / "src").mkdir()
            (left / "src" / "shared.txt").write_text("v1", encoding="utf-8")
            (right / "src" / "shared.txt").write_text("v2", encoding="utf-8")
            (left / "only-left.txt").write_text("left", encoding="utf-8")
            (right / "only-right.txt").write_text("right", encoding="utf-8")

            summary = summarize_diff(build_manifest(left), build_manifest(right))

            self.assertEqual(summary["changed"], ["src/shared.txt"])
            self.assertEqual(summary["added"], ["only-right.txt"])
            self.assertEqual(summary["removed"], ["only-left.txt"])
            self.assertIn(".", summary["changed_directories"])
            self.assertIn("src", summary["changed_directories"])
            self.assertFalse(summary["is_identical"])

    def test_manifest_ignores_cache_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app").mkdir()
            (root / "app" / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "junk.pyc").write_bytes(b"compiled")

            manifest = build_manifest(root)
            recorded_paths = [entry["path"] for entry in manifest["files"]]

            self.assertEqual(recorded_paths, ["app/main.py"])

    def test_cli_build_and_diff_json(self) -> None:
        with tempfile.TemporaryDirectory() as left_tmp, tempfile.TemporaryDirectory() as right_tmp, tempfile.TemporaryDirectory() as out_tmp:
            left = Path(left_tmp)
            right = Path(right_tmp)
            out = Path(out_tmp)
            (left / "data.txt").write_text("same", encoding="utf-8")
            (right / "data.txt").write_text("same", encoding="utf-8")
            manifest_path = out / "manifest.json"

            subprocess.run(
                [
                    "python3",
                    "projects/merkle-sync-lab/merkle_sync_lab.py",
                    "build",
                    str(left),
                    "--output",
                    str(manifest_path),
                ],
                check=True,
            )
            result = subprocess.run(
                [
                    "python3",
                    "projects/merkle-sync-lab/merkle_sync_lab.py",
                    "diff",
                    str(manifest_path),
                    str(right),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(result.stdout)
            self.assertTrue(payload["is_identical"])
            self.assertEqual(payload["added"], [])
            self.assertEqual(payload["removed"], [])
            self.assertEqual(payload["changed"], [])


if __name__ == "__main__":
    unittest.main()
