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
export_benchmark_report = module.export_benchmark_report
find_candidate_pairs = module.find_candidate_pairs
find_candidate_pairs_from_index = module.find_candidate_pairs_from_index
load_signature_index = module.load_signature_index
minhash_signature = module.minhash_signature
normalize_text = module.normalize_text
refresh_signature_index = module.refresh_signature_index
summarize_index_refresh = module.summarize_index_refresh
save_signature_index = module.save_signature_index
benchmark_corpus = module.benchmark_corpus
build_preset_artifact_bundle = module.build_preset_artifact_bundle
write_preset_artifact_bundle = module.write_preset_artifact_bundle
write_preset_corpus = module.write_preset_corpus
_preview_text_for_bundle = module._preview_text_for_bundle
_split_glob_patterns = module._split_glob_patterns


class MinhashNearDuplicateRepoTests(unittest.TestCase):
    def test_build_shingles_uses_overlapping_windows(self) -> None:
        shingles = build_shingles("data systems design patterns", size=2)
        self.assertEqual(
            shingles,
            {"data systems", "systems design", "design patterns"},
        )

    def test_short_text_falls_back_to_single_shingle(self) -> None:
        self.assertEqual(build_shingles("distributed", size=3), {"distributed"})

    def test_char_token_mode_builds_character_shingles(self) -> None:
        self.assertEqual(build_shingles("A B C D", size=3, token_mode="char"), {"a b", " b ", "b c", " c ", "c d"})

    def test_code_token_mode_splits_operators_and_identifiers(self) -> None:
        self.assertEqual(
            normalize_text("if (score >= limit) { total += score; }", token_mode="code")[:8],
            ["if", "(", "score", ">=", "limit", ")", "{", "total"],
        )

    def test_code_token_mode_can_normalize_non_keyword_identifiers(self) -> None:
        self.assertEqual(
            normalize_text(
                "def total(values):\n    return values + offset\n",
                token_mode="code",
                normalize_identifiers=True,
            )[:8],
            ["def", "<id>", "(", "<id>", ")", ":", "return", "<id>"],
        )

    def test_code_token_mode_can_normalize_numeric_literals(self) -> None:
        self.assertEqual(
            normalize_text(
                "if retries >= 3:\n    return limit + 42\n",
                token_mode="code",
                normalize_literals=True,
            )[:10],
            ["if", "retries", ">=", "<num>", ":", "return", "limit", "+", "<num>"],
        )

    def test_code_token_mode_can_normalize_string_boolean_none_and_float_literals(self) -> None:
        self.assertEqual(
            normalize_text(
                'flag = True\nname = "Ada"\nvalue = 3.14\nfallback = None\n',
                token_mode="code",
                normalize_literals=True,
            )[:16],
            ["flag", "=", "<bool>", "name", "=", "<str>", "value", "=", "<float>", "fallback", "=", "<none>"],
        )

    def test_code_token_mode_can_normalize_scientific_notation_literals(self) -> None:
        self.assertEqual(
            normalize_text(
                'budget = 1e6\nerror = 2.5e-3\n',
                token_mode="code",
                normalize_literals=True,
            )[:8],
            ["budget", "=", "<float>", "error", "=", "<float>"],
        )

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

    def test_code_token_mode_round_trips_in_signature_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a.py").write_text("def total(values):\n    return sum(values) + 3\n", encoding="utf-8")
            (root / "b.py").write_text("def total(items):\n    return sum(items) + 42\n", encoding="utf-8")
            index = build_signature_index(
                sorted(root.glob("*.py")),
                root=root,
                glob_pattern="*.py",
                shingle_size=3,
                token_mode="code",
                normalize_identifiers=True,
                normalize_literals=True,
                num_hashes=32,
                bands=8,
                seed=4,
            )
            index_path = root / "code-index.json"
            save_signature_index(index, index_path)
            loaded = load_signature_index(index_path)
            self.assertEqual(loaded.token_mode, "code")
            self.assertTrue(loaded.normalize_identifiers)
            self.assertTrue(loaded.normalize_literals)
            reports = find_candidate_pairs_from_index(loaded, threshold=0.2)
            self.assertEqual(len(reports), 1)

    def test_summarize_index_refresh_reports_path_level_diff_without_mutation(self) -> None:
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

            b_path.write_text("alpha beta gamma delta eta\n", encoding="utf-8")
            c_path.unlink()
            d_path = root / "d.txt"
            d_path.write_text("distributed systems portfolio minhash demo\n", encoding="utf-8")

            summary = summarize_index_refresh(index, sorted(root.glob("*.txt")))

            self.assertEqual(summary["documents_seen"], 3)
            self.assertEqual(summary["reused"], 1)
            self.assertEqual(summary["updated"], 1)
            self.assertEqual(summary["added"], 1)
            self.assertEqual(summary["removed"], 1)
            self.assertEqual(summary["updated_paths"], [str(b_path)])
            self.assertEqual(summary["added_paths"], [str(d_path)])
            self.assertEqual(summary["removed_paths"], [str(c_path)])

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

    def test_code_identifier_normalization_increases_similarity_for_renamed_variables(self) -> None:
        plain = compare_texts(
            "def total(values):\n    current_total = sum(values)\n    return current_total\n",
            "def total(items):\n    running_sum = sum(items)\n    return running_sum\n",
            left_name="left.py",
            right_name="right.py",
            shingle_size=3,
            num_hashes=64,
            bands=8,
            seed=13,
            token_mode="code",
        )
        normalized = compare_texts(
            "def total(values):\n    current_total = sum(values)\n    return current_total\n",
            "def total(items):\n    running_sum = sum(items)\n    return running_sum\n",
            left_name="left.py",
            right_name="right.py",
            shingle_size=3,
            num_hashes=64,
            bands=8,
            seed=13,
            token_mode="code",
            normalize_identifiers=True,
        )
        self.assertLess(plain.exact_jaccard, normalized.exact_jaccard)
        self.assertGreater(normalized.estimated_jaccard, plain.estimated_jaccard)

    def test_code_literal_normalization_increases_similarity_for_constant_changes(self) -> None:
        plain = compare_texts(
            "def clamp(score):\n    return min(score, 100)\n",
            "def clamp(score):\n    return min(score, 255)\n",
            left_name="left.py",
            right_name="right.py",
            shingle_size=3,
            num_hashes=64,
            bands=8,
            seed=21,
            token_mode="code",
        )
        normalized = compare_texts(
            "def clamp(score):\n    return min(score, 100)\n",
            "def clamp(score):\n    return min(score, 255)\n",
            left_name="left.py",
            right_name="right.py",
            shingle_size=3,
            num_hashes=64,
            bands=8,
            seed=21,
            token_mode="code",
            normalize_literals=True,
        )
        self.assertLess(plain.exact_jaccard, normalized.exact_jaccard)
        self.assertGreater(normalized.estimated_jaccard, plain.estimated_jaccard)

    def test_code_literal_normalization_increases_similarity_for_string_boolean_and_none_changes(self) -> None:
        plain = compare_texts(
            'def configure():\n    return {"enabled": True, "label": "alpha", "limit": None, "ratio": 1.5}\n',
            'def configure():\n    return {"enabled": False, "label": "beta", "limit": None, "ratio": 2.75}\n',
            left_name="left.py",
            right_name="right.py",
            shingle_size=4,
            num_hashes=64,
            bands=8,
            seed=31,
            token_mode="code",
        )
        normalized = compare_texts(
            'def configure():\n    return {"enabled": True, "label": "alpha", "limit": None, "ratio": 1.5}\n',
            'def configure():\n    return {"enabled": False, "label": "beta", "limit": None, "ratio": 2.75}\n',
            left_name="left.py",
            right_name="right.py",
            shingle_size=4,
            num_hashes=64,
            bands=8,
            seed=31,
            token_mode="code",
            normalize_literals=True,
        )
        self.assertLess(plain.exact_jaccard, normalized.exact_jaccard)
        self.assertGreater(normalized.estimated_jaccard, plain.estimated_jaccard)

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
        self.assertIn("top_exact_pairs", payload)
        self.assertIn("top_lsh_pairs", payload)

    def test_export_benchmark_report_writes_csv_and_markdown(self) -> None:
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
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            csv_path = root / "bench.csv"
            md_path = root / "bench.md"
            export_benchmark_report(payload, csv_path)
            export_benchmark_report(payload, md_path)

            csv_text = csv_path.read_text(encoding="utf-8")
            md_text = md_path.read_text(encoding="utf-8")

            self.assertIn("metric,value", csv_text)
            self.assertIn("candidate_pairs", csv_text)
            self.assertIn("normalize_identifiers", csv_text)
            self.assertIn("normalize_literals", csv_text)
            self.assertIn("# MinHash benchmark summary", md_text)
            self.assertIn("Normalize literals", md_text)
            self.assertIn("## Top LSH matches", md_text)

    def test_export_benchmark_report_rejects_unknown_extension(self) -> None:
        payload = benchmark_corpus(
            {
                "a.txt": "alpha beta gamma delta epsilon zeta",
                "b.txt": "alpha beta gamma delta epsilon eta",
            },
            shingle_size=2,
            num_hashes=32,
            bands=8,
            threshold=0.2,
            seed=9,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "must end with"):
                export_benchmark_report(payload, Path(tmpdir) / "bench.txt")

    def test_split_glob_patterns_supports_comma_separated_values(self) -> None:
        self.assertEqual(_split_glob_patterns("*.md, *.py,*.ipynb"), ["*.md", "*.py", "*.ipynb"])

    def test_write_preset_corpus_creates_mixed_language_demo_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "preset"
            written = write_preset_corpus("mixed-markdown-code-notebook", destination)

            self.assertGreaterEqual(len(written), 5)
            self.assertTrue((destination / "README.md").exists())
            self.assertTrue((destination / "bfs_queue.py").exists())
            self.assertTrue((destination / "bfs_demo.ipynb").exists())

    def test_write_preset_corpus_creates_data_science_demo_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "data-science"
            written = write_preset_corpus("data-science-feature-pipeline", destination)

            self.assertGreaterEqual(len(written), 5)
            self.assertTrue((destination / "feature_pipeline.py").exists())
            self.assertTrue((destination / "feature_demo.ipynb").exists())

    def test_write_preset_corpus_creates_systems_demo_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "systems"
            written = write_preset_corpus("systems-churn-reconciliation", destination)

            self.assertGreaterEqual(len(written), 6)
            self.assertTrue((destination / "replica_sync.py").exists())
            self.assertTrue((destination / "lag_demo.json").exists())

    def test_write_preset_corpus_creates_web_dev_component_demo_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "web-dev"
            written = write_preset_corpus("web-dev-component-clones", destination)

            self.assertEqual(len(written), 8)
            self.assertTrue((destination / "user_stats_card.tsx").exists())
            self.assertTrue((destination / "engagement_summary_card.tsx").exists())
            self.assertTrue((destination / "card-shell.css").exists())

    def test_build_preset_artifact_bundle_reports_file_cards_and_top_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "web-dev"
            written = write_preset_corpus("web-dev-component-clones", destination)

            payload = build_preset_artifact_bundle("web-dev-component-clones", destination, written)

            self.assertEqual(payload["preset_name"], "web-dev-component-clones")
            self.assertEqual(payload["files_written"], 8)
            self.assertEqual(payload["extensions"][".tsx"], 2)
            self.assertEqual(payload["extensions"][".ts"], 2)
            self.assertGreaterEqual(len(payload["top_pairs"]), 2)
            self.assertIn("<preset-root>", payload["recommended_scan"]["command"])
            self.assertIn("dashboard_story.md", {item["path"] for item in payload["files"]})

    def test_build_preset_artifact_bundle_ignores_stray_matching_files_in_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "web-dev"
            written = write_preset_corpus("web-dev-component-clones", destination)
            stray = destination / "shadow_copy.ts"
            stray.write_text((destination / "use_user_metrics.ts").read_text(encoding="utf-8"), encoding="utf-8")

            payload = build_preset_artifact_bundle("web-dev-component-clones", destination, written)

            self.assertEqual(payload["files_written"], 8)
            self.assertEqual(payload["pairs_detected"], 2)
            self.assertNotIn("shadow_copy.ts", {item["path"] for item in payload["files"]})
            self.assertFalse(any("shadow_copy.ts" in pair["left"] or "shadow_copy.ts" in pair["right"] for pair in payload["top_pairs"]))

    def test_preview_text_for_bundle_accepts_string_notebook_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            notebook = Path(tmpdir) / "preview.ipynb"
            notebook.write_text(
                json.dumps({"cells": [{"cell_type": "code", "source": "print('hello world')"}]}),
                encoding="utf-8",
            )

            preview = _preview_text_for_bundle(notebook)

            self.assertEqual(preview, "print('hello world')")

    def test_write_preset_artifact_bundle_writes_json_markdown_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "web-dev"
            bundle_dir = Path(tmpdir) / "bundle"
            written = write_preset_corpus("web-dev-component-clones", destination)

            outputs = write_preset_artifact_bundle("web-dev-component-clones", destination, bundle_dir, written)

            summary_json = Path(outputs["summary_json"])
            summary_md = Path(outputs["summary_md"])
            gallery_html = Path(outputs["gallery_html"])
            self.assertTrue(summary_json.exists())
            self.assertTrue(summary_md.exists())
            self.assertTrue(gallery_html.exists())

            bundle_payload = json.loads(summary_json.read_text(encoding="utf-8"))
            markdown = summary_md.read_text(encoding="utf-8")
            html = gallery_html.read_text(encoding="utf-8")

            self.assertEqual(bundle_payload["preset_name"], "web-dev-component-clones")
            self.assertIn("## Top near-duplicate pairs", markdown)
            self.assertIn("Suggested scan command", markdown)
            self.assertIn("<html", html)
            self.assertIn("Top near-duplicate pairs", html)

    def test_write_preset_corpus_requires_force_when_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "preset"
            write_preset_corpus("mixed-markdown-code-notebook", destination)
            with self.assertRaises(FileExistsError):
                write_preset_corpus("mixed-markdown-code-notebook", destination)

    def test_cli_write_preset_supports_mixed_language_corpus_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "preset"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "write-preset",
                    "mixed-markdown-code-notebook",
                    str(destination),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["command"], "write-preset")
            self.assertGreaterEqual(payload["files_written"], 5)

            corpus_completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "corpus",
                    str(destination),
                    "--glob",
                    "*.md,*.py,*.ipynb",
                    "--token-mode",
                    "code",
                    "--normalize-identifiers",
                    "--normalize-literals",
                    "--shingle-size",
                    "4",
                    "--threshold",
                    "0.2",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            corpus_payload = json.loads(corpus_completed.stdout)
            self.assertEqual(corpus_payload["documents_scanned"], payload["files_written"])
            self.assertGreaterEqual(len(corpus_payload["pairs"]), 1)

    def test_cli_write_preset_supports_data_science_corpus_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "preset"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "write-preset",
                    "data-science-feature-pipeline",
                    str(destination),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertGreaterEqual(payload["files_written"], 5)

            corpus_completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "corpus",
                    str(destination),
                    "--glob",
                    "*.md,*.py,*.ipynb",
                    "--token-mode",
                    "code",
                    "--normalize-identifiers",
                    "--shingle-size",
                    "4",
                    "--threshold",
                    "0.15",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            corpus_payload = json.loads(corpus_completed.stdout)
            self.assertEqual(corpus_payload["documents_scanned"], payload["files_written"])
            self.assertGreaterEqual(len(corpus_payload["pairs"]), 1)

    def test_cli_write_preset_supports_systems_corpus_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "preset"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "write-preset",
                    "systems-churn-reconciliation",
                    str(destination),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertGreaterEqual(payload["files_written"], 6)

            corpus_completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "corpus",
                    str(destination),
                    "--glob",
                    "*.md,*.py,*.json",
                    "--token-mode",
                    "code",
                    "--normalize-identifiers",
                    "--shingle-size",
                    "3",
                    "--threshold",
                    "0.15",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            corpus_payload = json.loads(corpus_completed.stdout)
            self.assertEqual(corpus_payload["documents_scanned"], payload["files_written"])
            self.assertGreaterEqual(len(corpus_payload["pairs"]), 1)

    def test_cli_write_preset_supports_web_dev_component_corpus_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "preset"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "write-preset",
                    "web-dev-component-clones",
                    str(destination),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            self.assertGreaterEqual(payload["files_written"], 7)

            corpus_completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "corpus",
                    str(destination),
                    "--glob",
                    "*.md,*.tsx,*.ts,*.css",
                    "--token-mode",
                    "code",
                    "--normalize-identifiers",
                    "--normalize-literals",
                    "--shingle-size",
                    "4",
                    "--threshold",
                    "0.15",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            corpus_payload = json.loads(corpus_completed.stdout)
            self.assertEqual(corpus_payload["documents_scanned"], payload["files_written"])
            self.assertGreaterEqual(len(corpus_payload["pairs"]), 2)

    def test_cli_write_preset_can_emit_artifact_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "preset"
            bundle_dir = Path(tmpdir) / "bundle"
            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "write-preset",
                    "web-dev-component-clones",
                    str(destination),
                    "--artifact-bundle-dir",
                    str(bundle_dir),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            artifact_bundle = payload["artifact_bundle"]
            self.assertTrue(Path(artifact_bundle["summary_json"]).exists())
            self.assertTrue(Path(artifact_bundle["summary_md"]).exists())
            self.assertTrue(Path(artifact_bundle["gallery_html"]).exists())
            summary_payload = json.loads(Path(artifact_bundle["summary_json"]).read_text(encoding="utf-8"))
            self.assertEqual(summary_payload["preset_name"], "web-dev-component-clones")
            self.assertGreaterEqual(len(summary_payload["top_pairs"]), 2)

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

    def test_cli_compare_supports_code_token_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = Path(tmpdir) / "left.py"
            right = Path(tmpdir) / "right.py"
            left.write_text("def total(values):\n    return sum(values)\n", encoding="utf-8")
            right.write_text("def total(items):\n    return sum(items)\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "compare",
                    str(left),
                    str(right),
                    "--token-mode",
                    "code",
                    "--shingle-size",
                    "3",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["token_mode"], "code")
            self.assertGreater(payload["estimated_jaccard"], 0.3)

    def test_cli_compare_can_normalize_identifiers_for_code_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = Path(tmpdir) / "left.py"
            right = Path(tmpdir) / "right.py"
            left.write_text("def total(values):\n    current_total = sum(values)\n    return current_total\n", encoding="utf-8")
            right.write_text("def total(items):\n    running_sum = sum(items)\n    return running_sum\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "compare",
                    str(left),
                    str(right),
                    "--token-mode",
                    "code",
                    "--normalize-identifiers",
                    "--shingle-size",
                    "3",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertTrue(payload["normalize_identifiers"])
            self.assertGreater(payload["exact_jaccard"], 0.7)

    def test_cli_compare_can_normalize_literals_for_code_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            left = Path(tmpdir) / "left.py"
            right = Path(tmpdir) / "right.py"
            left.write_text("def clamp(score):\n    return min(score, 100)\n", encoding="utf-8")
            right.write_text("def clamp(score):\n    return min(score, 255)\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "compare",
                    str(left),
                    str(right),
                    "--token-mode",
                    "code",
                    "--normalize-literals",
                    "--shingle-size",
                    "3",
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertTrue(payload["normalize_literals"])
            self.assertGreater(payload["exact_jaccard"], 0.7)

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
            self.assertFalse(build_payload["normalize_identifiers"])
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

    def test_cli_refresh_index_dry_run_json_output(self) -> None:
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

            before = index_path.read_text(encoding="utf-8")
            refreshed = subprocess.run(
                ["python3", str(MODULE_PATH), "refresh-index", str(index_path), "--dry-run", "--json"],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(refreshed.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["documents_seen"], 3)
            self.assertEqual(payload["reused"], 1)
            self.assertEqual(payload["updated"], 1)
            self.assertEqual(payload["added"], 1)
            self.assertEqual(payload["removed"], 0)
            self.assertEqual(len(payload["updated_paths"]), 1)
            self.assertEqual(len(payload["added_paths"]), 1)
            self.assertEqual(index_path.read_text(encoding="utf-8"), before)

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
            self.assertFalse(payload["normalize_identifiers"])

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
            self.assertIn("top_exact_pairs", payload)
            self.assertIn("top_lsh_pairs", payload)

    def test_cli_benchmark_can_export_markdown_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "benchmark-summary.md"
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
                    "--output",
                    str(output),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["output"], str(output))
            self.assertTrue(output.exists())
            self.assertIn("# MinHash benchmark summary", output.read_text(encoding="utf-8"))

    def test_cli_benchmark_char_mode_includes_token_mode_in_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            output = root / "benchmark-summary.md"
            (root / "a.txt").write_text("abcdefg hijklmn\n", encoding="utf-8")
            (root / "b.txt").write_text("abcxefg hijklmn\n", encoding="utf-8")
            (root / "c.txt").write_text("operating systems memory allocator\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    "python3",
                    str(MODULE_PATH),
                    "benchmark",
                    str(root),
                    "--token-mode",
                    "char",
                    "--shingle-size",
                    "4",
                    "--threshold",
                    "0.2",
                    "--output",
                    str(output),
                    "--json",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["token_mode"], "char")
            self.assertIn("Token mode: char", output.read_text(encoding="utf-8"))

    def test_cli_rejects_identifier_normalization_without_code_mode(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "corpus",
                str(PROJECT_ROOT),
                "--normalize-identifiers",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires --token-mode code", completed.stderr)

    def test_cli_rejects_literal_normalization_without_code_mode(self) -> None:
        completed = subprocess.run(
            [
                "python3",
                str(MODULE_PATH),
                "corpus",
                str(PROJECT_ROOT),
                "--normalize-literals",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires --token-mode code", completed.stderr)

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
