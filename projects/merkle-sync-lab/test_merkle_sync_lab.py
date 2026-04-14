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
build_copy_plan = merkle_sync_lab.build_copy_plan
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

    def test_copy_plan_reports_directory_creation_copy_update_and_delete(self) -> None:
        with tempfile.TemporaryDirectory() as source_tmp, tempfile.TemporaryDirectory() as target_tmp:
            source = Path(source_tmp)
            target = Path(target_tmp)
            (source / "docs").mkdir()
            (source / "docs" / "guide.txt").write_text("guide", encoding="utf-8")
            (source / "same.txt").write_text("same", encoding="utf-8")
            (source / "shared.txt").write_text("new value", encoding="utf-8")
            (target / "same.txt").write_text("same", encoding="utf-8")
            (target / "shared.txt").write_text("old value", encoding="utf-8")
            (target / "stale.txt").write_text("remove me", encoding="utf-8")

            plan = build_copy_plan(build_manifest(source), build_manifest(target))
            operations = [(entry["op"], entry["path"]) for entry in plan["operations"]]

            self.assertEqual(
                operations,
                [
                    ("mkdir", "docs"),
                    ("copy", "docs/guide.txt"),
                    ("update", "shared.txt"),
                    ("delete", "stale.txt"),
                ],
            )
            self.assertEqual(plan["mkdir_count"], 1)
            self.assertEqual(plan["copy_count"], 1)
            self.assertEqual(plan["update_count"], 1)
            self.assertEqual(plan["delete_count"], 1)
            self.assertEqual(plan["bytes_to_copy"], len("guide"))
            self.assertEqual(plan["bytes_to_update"], len("new value"))

    def test_cli_build_diff_and_plan_json(self) -> None:
        with tempfile.TemporaryDirectory() as source_tmp, tempfile.TemporaryDirectory() as target_tmp, tempfile.TemporaryDirectory() as out_tmp:
            source = Path(source_tmp)
            target = Path(target_tmp)
            out = Path(out_tmp)
            (source / "nested").mkdir()
            (source / "nested" / "data.txt").write_text("same", encoding="utf-8")
            (target / "nested").mkdir()
            (target / "nested" / "data.txt").write_text("same", encoding="utf-8")
            manifest_path = out / "manifest.json"

            subprocess.run(
                [
                    "python3",
                    "projects/merkle-sync-lab/merkle_sync_lab.py",
                    "build",
                    str(source),
                    "--output",
                    str(manifest_path),
                ],
                check=True,
            )
            diff_result = subprocess.run(
                [
                    "python3",
                    "projects/merkle-sync-lab/merkle_sync_lab.py",
                    "diff",
                    str(manifest_path),
                    str(target),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            diff_payload = json.loads(diff_result.stdout)
            self.assertTrue(diff_payload["is_identical"])
            self.assertEqual(diff_payload["changed"], [])

            (target / "nested" / "data.txt").write_text("changed", encoding="utf-8")
            plan_result = subprocess.run(
                [
                    "python3",
                    "projects/merkle-sync-lab/merkle_sync_lab.py",
                    "plan",
                    str(manifest_path),
                    str(target),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(plan_result.stdout)
            self.assertEqual(payload["mkdir_count"], 0)
            self.assertEqual(payload["copy_count"], 0)
            self.assertEqual(payload["update_count"], 1)
            self.assertEqual(payload["delete_count"], 0)
            self.assertEqual(payload["operations"][0]["op"], "update")
            self.assertEqual(payload["operations"][0]["path"], "nested/data.txt")


if __name__ == "__main__":
    unittest.main()
