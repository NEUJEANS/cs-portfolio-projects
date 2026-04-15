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
build_signature_index = module.build_signature_index
compare_texts = module.compare_texts
estimate_jaccard = module.estimate_jaccard
exact_jaccard = module.exact_jaccard
find_candidate_pairs = module.find_candidate_pairs
find_candidate_pairs_from_index = module.find_candidate_pairs_from_index
load_signature_index = module.load_signature_index
minhash_signature = module.minhash_signature
refresh_signature_index = module.refresh_signature_index
save_signature_index = module.save_signature_index
benchmark_corpus = module.benchmark_corpus


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

    def test_signature_index_round_trip_preserves_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.txt").write_text("alpha beta gamma delta epsilon\n", encoding="utf-8")
            (root / "b.txt").write_text("alpha beta gamma delta zeta\n", encoding="utf-8")
            (root / "c.txt").write_text("operating systems scheduling disk arm movement\n", encoding="utf-8")
            paths = sorted(root.glob("*.txt"))

            index = build_signature_index(
                paths,
                root=root,
                glob_pattern="*.txt",
                shingle_size=2,
                num_hashes=32,
                bands=8,
                seed=5,
            )
            index_path = root / "index.json"
            save_signature_index(index, index_path)
            loaded = load_signature_index(index_path)
            reports = find_candidate_pairs_from_index(loaded, threshold=0.2)

            self.assertEqual(len(loaded.documents), 3)
            self.assertEqual(len(reports), 1)
            self.assertTrue(reports[0].left.endswith("a.txt"))
            self.assertEqual(loaded.num_hashes, 32)

    def test_refresh_signature_index_reuses_unchanged_docs_and_detects_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            a_path = root / "a.txt"
            b_path = root / "b.txt"
            c_path = root / "c.txt"
            a_path.write_text("alpha beta gamma delta epsilon\n", encoding="utf-8")
            b_path.write_text("alpha beta gamma delta zeta\n", encoding="utf-8")
            c_path.write_text("operating systems scheduling disk arm movement\n", encoding="utf-8")
            index = build_signature_index(
                sorted(root.glob("*.txt")),
                root=root,
                glob_pattern="*.txt",
                shingle_size=2,
                num_hashes=32,
                bands=8,
                seed=5,
            )

            before_docs = {document.path: document for document in index.documents}
            b_path.write_text("alpha beta gamma delta eta\n", encoding="utf-8")
            c_path.unlink()
            d_path = root / "d.txt"
            d_path.write_text("distributed systems portfolio minhash demo\n", encoding="utf-8")

            refreshed, stats = refresh_signature_index(index, sorted(root.glob("*.txt")))
            after_docs = {document.path: document for document in refreshed.documents}

            self.assertEqual(stats, {"documents_seen": 3, "reused": 1, "updated": 1, "added": 1, "removed": 1})
            self.assertEqual(after_docs[str(a_path)], before_docs[str(a_path)])
            self.assertNotEqual(after_docs[str(b_path)].content_sha256, before_docs[str(b_path)].content_sha256)
            self.assertIn(str(d_path), after_docs)
            self.assertNotIn(str(c_path), after_docs)

    def test_benchmark_reports_candidate_counts_and_timings(self) -> None:
        payload = benchmark_corpus(
            {
                "a.txt": "alpha beta gamma delta epsilon zeta",
                "b.txt": "alpha beta gamma delta epsilon eta",
                "c.txt": "distributed systems consistent hashing lab",
            },
            shingle_size=2,
            num_hashes=32,
            bands=8,
            threshold=0.2,
            seed=9,
        )
        self.assertEqual(payload["command"], "benchmark")
        self.assertEqual(payload["documents_scanned"], 3)
        self.assertIn("timings_seconds", payload)
        self.assertGreaterEqual(payload["all_pairs"], payload["candidate_pairs"])
        self.assertIn("exact_pairs_above_threshold", payload)
        self.assertIn("lsh_recall_vs_exact", payload)

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

    def test_cli_build_index_and_scan_index_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "docs"
            root.mkdir()
            (root / "a.txt").write_text("alpha beta gamma delta epsilon\n", encoding="utf-8")
            (root / "b.txt").write_text("alpha beta gamma delta zeta\n", encoding="utf-8")
            (root / "c.txt").write_text("systems programming memory allocator heap blocks\n", encoding="utf-8")
            index_path = Path(tmpdir) / "signatures.json"

            build_completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "build-index",
                    str(root),
                    str(index_path),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            build_payload = json.loads(build_completed.stdout)
            self.assertEqual(build_payload["command"], "build-index")
            self.assertEqual(build_payload["documents_indexed"], 3)
            self.assertTrue(index_path.exists())

            scan_completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "scan-index",
                    str(index_path),
                    "--threshold",
                    "0.2",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            scan_payload = json.loads(scan_completed.stdout)
            self.assertEqual(scan_payload["command"], "scan-index")
            self.assertEqual(scan_payload["documents_scanned"], 3)
            self.assertEqual(len(scan_payload["pairs"]), 1)

    def test_cli_refresh_index_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "docs"
            root.mkdir()
            (root / "a.txt").write_text("alpha beta gamma delta epsilon\n", encoding="utf-8")
            (root / "b.txt").write_text("alpha beta gamma delta zeta\n", encoding="utf-8")
            index_path = Path(tmpdir) / "signatures.json"

            subprocess.run(
                ["python3", str(MODULE_PATH), "build-index", str(root), str(index_path), "--json"],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            (root / "b.txt").write_text("alpha beta gamma delta eta\n", encoding="utf-8")
            (root / "c.txt").write_text("memory allocator slab freelist\n", encoding="utf-8")

            refreshed = subprocess.run(
                ["python3", str(MODULE_PATH), "refresh-index", str(index_path), "--json"],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(refreshed.stdout)
            self.assertEqual(payload["command"], "refresh-index")
            self.assertEqual(payload["documents_seen"], 3)
            self.assertEqual(payload["reused"], 1)
            self.assertEqual(payload["updated"], 1)
            self.assertEqual(payload["added"], 1)
            self.assertEqual(payload["removed"], 0)

    def test_cli_benchmark_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.txt").write_text("alpha beta gamma delta epsilon zeta\n", encoding="utf-8")
            (root / "b.txt").write_text("alpha beta gamma delta epsilon eta\n", encoding="utf-8")
            (root / "c.txt").write_text("network routing consistent hashing replicas\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
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
            self.assertEqual(payload["command"], "benchmark")
            self.assertEqual(payload["documents_scanned"], 3)
            self.assertIn("candidate_pairs", payload)
            self.assertIn("timings_seconds", payload)
            self.assertIn("exact_pairs_above_threshold", payload)
            self.assertIn("lsh_pairs_above_threshold", payload)

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
