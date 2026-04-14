from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "minhash-near-duplicate-lab" / "minhash_lab.py"

spec = importlib.util.spec_from_file_location("minhash_near_duplicate_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

build_shingles = module.build_shingles
compare_texts = module.compare_texts
estimate_jaccard = module.estimate_jaccard
exact_jaccard = module.exact_jaccard
find_candidate_pairs = module.find_candidate_pairs
minhash_signature = module.minhash_signature


class MinhashNearDuplicateRepoTests(unittest.TestCase):
    def test_build_shingles_uses_overlapping_windows(self) -> None:
        shingles = build_shingles("data systems design patterns", size=2)
        self.assertEqual(
            shingles,
            {"data systems", "systems design", "design patterns"},
        )

    def test_short_text_falls_back_to_single_shingle(self) -> None:
        self.assertEqual(build_shingles("distributed", size=3), {"distributed"})

    def test_signature_is_deterministic_for_same_seed(self) -> None:
        shingles = {"a b", "b c", "c d"}
        self.assertEqual(minhash_signature(shingles, num_hashes=16, seed=7), minhash_signature(shingles, num_hashes=16, seed=7))

    def test_exact_and_estimated_similarity_track_for_related_docs(self) -> None:
        report = compare_texts(
            "the quick brown fox jumps over the lazy dog",
            "the quick brown fox leaps over the lazy dog",
            left_name="a",
            right_name="b",
            shingle_size=2,
            num_hashes=64,
            bands=8,
            seed=11,
        )
        self.assertGreater(report.exact_jaccard, 0.45)
        self.assertGreater(report.estimated_jaccard, 0.35)
        self.assertLessEqual(abs(report.exact_jaccard - report.estimated_jaccard), 0.35)

    def test_estimate_jaccard_rejects_mismatched_signature_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "signature lengths must match"):
            estimate_jaccard([1, 2], [1])

    def test_find_candidate_pairs_surfaces_only_similar_documents(self) -> None:
        reports = find_candidate_pairs(
            {
                "a.txt": "data systems design project portfolio slice with minhash and shingles",
                "b.txt": "data systems design project portfolio slice with minhash and signatures",
                "c.txt": "garden tomatoes basil olive oil recipe for dinner",
            },
            shingle_size=2,
            num_hashes=64,
            bands=8,
            threshold=0.3,
            seed=3,
        )
        self.assertEqual(len(reports), 1)
        self.assertEqual((reports[0].left, reports[0].right), ("a.txt", "b.txt"))
        self.assertGreater(reports[0].shared_bands, 0)

    def test_find_candidate_pairs_rejects_invalid_threshold(self) -> None:
        with self.assertRaisesRegex(ValueError, "threshold must be between 0 and 1"):
            find_candidate_pairs({"a": "x", "b": "y"}, threshold=1.5)

    def test_cli_compare_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = Path(tmpdir) / "left.txt"
            right = Path(tmpdir) / "right.txt"
            left.write_text("distributed systems portfolio project with minhash shingles\n", encoding="utf-8")
            right.write_text("distributed systems portfolio demo using minhash shingles\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "compare",
                    str(left),
                    str(right),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "compare")
            self.assertIn("estimated_jaccard", payload)
            self.assertEqual(payload["bands"], 8)

    def test_cli_corpus_json_output_lists_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.txt").write_text("alpha beta gamma delta epsilon\n", encoding="utf-8")
            (root / "b.txt").write_text("alpha beta gamma delta zeta\n", encoding="utf-8")
            (root / "c.txt").write_text("music theory practice piano chords\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "corpus",
                    str(root),
                    "--threshold",
                    "0.2",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["documents_scanned"], 3)
            self.assertEqual(len(payload["pairs"]), 1)
            self.assertTrue(payload["pairs"][0]["left"].endswith("a.txt"))

    def test_cli_rejects_band_mismatch(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "corpus",
                str(PROJECT_ROOT),
                "--num-hashes",
                "10",
                "--bands",
                "3",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("divisible", completed.stderr)

    def test_exact_jaccard_handles_empty_sets(self) -> None:
        self.assertEqual(exact_jaccard(set(), set()), 1.0)


if __name__ == "__main__":
    unittest.main()
