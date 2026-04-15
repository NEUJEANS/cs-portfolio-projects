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

from splay_tree_lab import SplayTree


class SplayTreeBehaviorTests(unittest.TestCase):
    def test_insert_makes_latest_key_root(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7])
        self.assertEqual(tree.root.key, 7)
        inserted = tree.insert(12)
        self.assertTrue(inserted)
        self.assertEqual(tree.root.key, 12)
        self.assertEqual(tree.inorder(), [2, 4, 7, 10, 12, 15])

    def test_access_sequence_tracks_hits_and_misses(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        summary = tree.access_sequence([7, 7, 18, 99])
        self.assertEqual(summary["hits"], 3)
        self.assertEqual(summary["misses"], 1)
        self.assertEqual(summary["requested_keys"], [7, 7, 18, 99])
        self.assertGreaterEqual(summary["rotations_used"], 1)
        self.assertEqual(tree.root.key, 18)

    def test_delete_preserves_bst_order(self) -> None:
        tree = SplayTree([10, 4, 15, 2, 7, 12, 18])
        deleted = tree.delete(10)
        self.assertTrue(deleted)
        self.assertEqual(tree.inorder(), [2, 4, 7, 12, 15, 18])
        self.assertEqual(tree.size, 6)


class SplayTreeCliTests(unittest.TestCase):
    def test_build_and_access_cli(self) -> None:
        project_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot = tmp_path / "splay.json"
            build = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "build",
                    "--input",
                    str(project_dir / "sample_values.txt"),
                    "--output",
                    str(snapshot),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            build_payload = json.loads(build.stdout)
            self.assertEqual(build_payload["size"], 7)

            updated = tmp_path / "accessed.json"
            access = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "access",
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(updated),
                    "7",
                    "18",
                    "99",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            access_payload = json.loads(access.stdout)
            self.assertEqual(access_payload["hits"], 2)
            self.assertEqual(access_payload["misses"], 1)
            updated_payload = json.loads(updated.read_text())
            self.assertEqual(updated_payload["size"], 7)

    def test_insert_and_delete_cli(self) -> None:
        project_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            snapshot = tmp_path / "splay.json"
            subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "build",
                    "--input",
                    str(project_dir / "sample_values.txt"),
                    "--output",
                    str(snapshot),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            grown = tmp_path / "grown.json"
            insert = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "insert",
                    "--snapshot",
                    str(snapshot),
                    "--output",
                    str(grown),
                    "11",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertTrue(json.loads(insert.stdout)["inserted"])

            pruned = tmp_path / "pruned.json"
            delete = subprocess.run(
                [
                    "python3",
                    str(project_dir / "splay_tree_lab.py"),
                    "delete",
                    "--snapshot",
                    str(grown),
                    "--output",
                    str(pruned),
                    "4",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            delete_payload = json.loads(delete.stdout)
            self.assertTrue(delete_payload["deleted"])
            self.assertNotIn(4, delete_payload["values"])


if __name__ == "__main__":
    unittest.main()
