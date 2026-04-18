import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from crdt_orset_lab import (
    LWWElementSet,
    ORSet,
    ReplicaCluster,
    build_anti_entropy_report,
    build_companion_links,
    build_comparison_preset_suite,
    build_replay_frames,
    build_semantics_comparison,
    list_comparison_presets,
    load_script,
    parse_tag,
    render_anti_entropy_html,
    render_anti_entropy_markdown,
    render_comparison_html,
    render_comparison_markdown,
    render_comparison_preset_suite_html,
    render_comparison_preset_suite_markdown,
    render_replay_html,
    render_timeline_html,
    render_timeline_markdown,
    render_timeline_mermaid,
    render_timeline_svg,
)


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "crdt_orset_lab.py"
PRESET_DIR = PROJECT_DIR / "presets"
SAMPLE_SCRIPT = PROJECT_DIR / "sample_ops.json"
SAMPLE_COMPARE_SCRIPT = PROJECT_DIR / "sample_compare_ops.json"


def run_cli(*args: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


class ORSetLabTests(unittest.TestCase):
    def test_add_generates_monotonic_replica_tags(self) -> None:
        state = ORSet()

        first = state.add("a", "notebook")
        second = state.add("a", "notebook")
        third = state.add("b", "notebook")

        self.assertEqual(first, "a:1")
        self.assertEqual(second, "a:2")
        self.assertEqual(third, "b:1")
        self.assertEqual(state.active_tags("notebook"), {"a:1", "a:2", "b:1"})

    def test_remove_only_tombstones_observed_tags(self) -> None:
        left = ORSet()
        right = ORSet()
        left.add("a", "draft")
        right.add("b", "draft")

        left.remove("draft")
        merged = left.merge(right)

        self.assertTrue(merged.contains("draft"))
        self.assertEqual(merged.active_tags("draft"), {"b:1"})
        self.assertEqual(merged.tombstones, {"a:1"})

    def test_merge_is_commutative_for_membership_and_tags(self) -> None:
        left = ORSet()
        right = ORSet()
        left.add("a", "draft")
        left.add("a", "slides")
        right.add("b", "draft")
        right.remove("draft")

        merged_ab = left.merge(right).to_dict()
        merged_ba = right.merge(left).to_dict()

        self.assertEqual(merged_ab, merged_ba)

    def test_cluster_bidirectional_sync_converges_replicas(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        cluster.add("a", "notebook")
        cluster.sync("a", "b")
        cluster.add("c", "notebook")
        cluster.sync("c", "a")
        cluster.remove("b", "notebook")
        cluster.sync("a", "b")
        cluster.sync("a", "c")

        snapshot = cluster.snapshot()

        self.assertTrue(snapshot["convergence"]["converged"])
        self.assertEqual(snapshot["convergence"]["membership"]["a"], ["notebook"])
        self.assertEqual(snapshot["replicas"]["a"]["active_tags"]["notebook"], ["c:1"])
        self.assertEqual(snapshot["replicas"]["b"]["tombstones"], ["a:1"])

    def test_convergence_requires_full_state_not_just_membership(self) -> None:
        cluster = ReplicaCluster(["a", "b"])
        cluster.add("a", "notebook")
        cluster.remove("a", "notebook")

        report = cluster.convergence_report()

        self.assertFalse(report["converged"])
        self.assertEqual(report["membership"]["a"], [])
        self.assertEqual(report["membership"]["b"], [])

    def test_run_script_accepts_wrapped_operations_object(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        result = cluster.run_script(load_script(SAMPLE_SCRIPT))

        self.assertTrue(result["convergence"]["converged"])
        self.assertEqual(result["convergence"]["membership"]["b"], ["notebook"])
        self.assertEqual(result["replicas"]["c"]["active_tags"]["notebook"], ["c:1"])

    def test_lww_element_set_respects_remove_wins_ordering(self) -> None:
        state = LWWElementSet(bias="remove")
        state.add("notebook", 1)
        state.remove("notebook", 3)
        state.add("notebook", 2)

        self.assertFalse(state.contains("notebook"))
        self.assertEqual(state.elements(), [])
        self.assertEqual(
            state.to_dict(),
            {
                "bias": "remove",
                "elements": [],
                "add_timestamps": {"notebook": 2},
                "remove_timestamps": {"notebook": 3},
            },
        )

    def test_build_semantics_comparison_surfaces_membership_divergence(self) -> None:
        comparison = build_semantics_comparison(
            ["a", "b", "c"],
            load_script(SAMPLE_COMPARE_SCRIPT),
        )

        divergence = comparison["final_divergence"]
        self.assertEqual(len(divergence), 1)
        self.assertEqual(divergence[0]["element"], "notebook")
        self.assertTrue(divergence[0]["orset_present"])
        self.assertFalse(divergence[0]["lww_present"])
        self.assertIn("OR-Set keeps only observed-remove tombstones", divergence[0]["why"])
        self.assertIn("diverge on notebook", comparison["story"])

    def test_render_comparison_views_include_divergence_story(self) -> None:
        comparison = build_semantics_comparison(
            ["a", "b", "c"],
            load_script(SAMPLE_COMPARE_SCRIPT),
        )

        markdown = render_comparison_markdown(comparison, "sample compare")
        html = render_comparison_html(comparison, "sample compare")

        self.assertIn("Final divergence", markdown)
        self.assertIn("OR-Set=present, LWW=absent", markdown)
        self.assertIn("OR-Set vs LWW-element-set", html)
        self.assertIn("Final divergence notes", html)
        self.assertIn("notebook", html)

    def test_list_comparison_presets_includes_control_and_divergence_cases(self) -> None:
        presets = list_comparison_presets()

        self.assertEqual([preset.name for preset in presets], [
            "concurrent-readd",
            "unobserved-remove",
            "observed-remove-sync",
        ])
        self.assertTrue(all(preset.script_path.exists() for preset in presets))
        self.assertEqual(presets[-1].script_path, PRESET_DIR / "observed-remove-sync.json")

    def test_build_comparison_preset_suite_reports_divergent_and_aligned_cases(self) -> None:
        suite = build_comparison_preset_suite()

        self.assertEqual(suite["preset_count"], 3)
        self.assertEqual(suite["divergent_count"], 2)
        self.assertEqual(suite["aligned_count"], 1)
        outcomes = {preset["name"]: preset["outcome"] for preset in suite["presets"]}
        self.assertEqual(outcomes["concurrent-readd"], "diverge")
        self.assertEqual(outcomes["unobserved-remove"], "diverge")
        self.assertEqual(outcomes["observed-remove-sync"], "align")
        observed = next(preset for preset in suite["presets"] if preset["name"] == "observed-remove-sync")
        self.assertEqual(observed["orset_membership"]["a"], [])
        self.assertEqual(observed["lww_membership"]["a"], [])

    def test_render_comparison_preset_suite_views_include_suite_story(self) -> None:
        suite = build_comparison_preset_suite(["concurrent-readd", "observed-remove-sync"])
        suite["presets"][0]["detail_bundle"] = {
            "directory": "comparison-presets/concurrent-readd",
            "bundle_index_html": "comparison-presets/concurrent-readd/index.html",
            "bundle_script": "comparison-presets/concurrent-readd/scenario-script.json",
            "bundle_zip": "comparison-presets/concurrent-readd/concurrent-readd-bundle.zip",
            "comparison_html": "comparison-presets/concurrent-readd/comparison.html",
            "timeline_html": "comparison-presets/concurrent-readd/timeline.html",
            "replay_html": "comparison-presets/concurrent-readd/replay.html",
            "anti_entropy_html": "comparison-presets/concurrent-readd/anti-entropy.html",
            "snapshot_json": "comparison-presets/concurrent-readd/orset-snapshot.json",
            "timeline_markdown": "comparison-presets/concurrent-readd/timeline.md",
            "timeline_mermaid": "comparison-presets/concurrent-readd/timeline.mmd",
            "timeline_svg": "comparison-presets/concurrent-readd/timeline.svg",
            "comparison_markdown": "comparison-presets/concurrent-readd/comparison.md",
            "comparison_json": "comparison-presets/concurrent-readd/comparison.json",
            "anti_entropy_markdown": "comparison-presets/concurrent-readd/anti-entropy.md",
            "anti_entropy_json": "comparison-presets/concurrent-readd/anti-entropy.json",
        }

        markdown = render_comparison_preset_suite_markdown(suite)
        html = render_comparison_preset_suite_html(suite)

        self.assertIn("OR-Set comparison preset suite", markdown)
        self.assertIn("concurrent-readd", markdown)
        self.assertIn("observed-remove-sync", markdown)
        self.assertIn("both models converge to the same final membership", markdown)
        self.assertIn("[bundle](comparison-presets/concurrent-readd/index.html)", markdown)
        self.assertIn("[zip](comparison-presets/concurrent-readd/concurrent-readd-bundle.zip)", markdown)
        self.assertIn("[comparison](comparison-presets/concurrent-readd/comparison.html)", markdown)
        self.assertIn("OR-Set comparison preset suite", html)
        self.assertIn("Concurrent re-add survives in OR-Set", html)
        self.assertIn("Both models reach the same final membership", html)
        self.assertIn('href="comparison-presets/concurrent-readd/index.html"', html)
        self.assertIn('href="comparison-presets/concurrent-readd/timeline.html"', html)
        self.assertIn("ZIP packet", html)
        self.assertIn("Snapshot JSON", html)

    def test_parse_tag_rejects_invalid_format(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid OR-Set tag"):
            parse_tag("broken-tag")

    def test_load_script_rejects_non_object_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "bad.json"
            script_path.write_text(json.dumps(["oops"]))
            with self.assertRaisesRegex(ValueError, "each operation must be an object"):
                load_script(script_path)

    def test_cli_run_script_reports_converged_membership(self) -> None:
        result = run_cli(
            "run-script",
            "--replicas",
            "a",
            "b",
            "c",
            "--script",
            str(SAMPLE_SCRIPT),
        )

        self.assertTrue(result["convergence"]["converged"])
        self.assertEqual(result["replicas"]["a"]["elements"], ["notebook"])
        self.assertEqual(result["replicas"]["a"]["tombstones"], ["a:1"])

    def test_cli_sync_can_apply_seed_script_then_forward_sync(self) -> None:
        result = run_cli(
            "sync",
            "--replicas",
            "a",
            "b",
            "c",
            "--seed-script",
            str(SAMPLE_SCRIPT),
            "--source",
            "a",
            "--target",
            "b",
            "--direction",
            "forward",
        )

        self.assertTrue(result["convergence"]["converged"])
        self.assertEqual(result["replicas"]["b"]["active_tags"]["notebook"], ["c:1"])

    def test_timeline_renderers_capture_observed_remove_story(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        snapshot = cluster.run_script(load_script(SAMPLE_SCRIPT))

        markdown = render_timeline_markdown(snapshot, "sample timeline")
        mermaid = render_timeline_mermaid(snapshot, "sample timeline")
        svg = render_timeline_svg(snapshot, "sample timeline")

        self.assertIn("Observed-remove story", markdown)
        self.assertIn("c:1", markdown)
        self.assertIn("sequenceDiagram", mermaid)
        self.assertIn("sync both", mermaid)
        self.assertIn("<svg", svg)
        self.assertIn("Final convergence", svg)
        self.assertIn("c:1", svg)

    def test_timeline_html_links_companion_artifacts(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        snapshot = cluster.run_script(load_script(SAMPLE_SCRIPT))
        links = build_companion_links(
            html_path=PROJECT_DIR / "artifacts" / "index.html",
            markdown_path=PROJECT_DIR / "artifacts" / "timeline.md",
            mermaid_path=PROJECT_DIR / "artifacts" / "timeline.mmd",
            svg_path=PROJECT_DIR / "artifacts" / "timeline.svg",
            json_path=PROJECT_DIR / "artifacts" / "timeline.json",
            script_path=SAMPLE_SCRIPT,
        )

        html = render_timeline_html(snapshot, "sample timeline", companion_links=links)

        self.assertIn("OR-Set artifact gallery", html)
        self.assertIn('href="../sample_ops.json"', html)
        self.assertIn('href="timeline.md"', html)
        self.assertIn('href="timeline.mmd"', html)
        self.assertIn('href="timeline.svg"', html)
        self.assertIn('href="timeline.json"', html)
        self.assertIn("Timeline steps", html)
        self.assertIn("Final replica states", html)
        self.assertIn("<svg", html)

    def test_timeline_html_marks_non_converged_summaries_as_mixed(self) -> None:
        cluster = ReplicaCluster(["a", "b"])
        cluster.add("a", "notes")

        html = render_timeline_html(cluster.snapshot(), "single add")

        self.assertIn("mixed by replica", html)
        self.assertIn("a: elements notes; active notes=a:1; tombstones ∅", html)
        self.assertIn("b: elements ∅; active ∅; tombstones ∅", html)

    def test_build_replay_frames_tracks_replica_state_and_sync_payloads(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        snapshot = cluster.run_script(load_script(SAMPLE_SCRIPT))

        frames = build_replay_frames(snapshot)

        self.assertEqual(frames[0]["label"], "Cluster starts empty")
        self.assertIsNone(frames[0]["sync_checkpoint"])
        self.assertEqual(frames[1]["replicas"]["a"]["active_tags"]["notebook"], ["a:1"])
        self.assertIsNone(frames[1]["sync_checkpoint"])
        self.assertEqual(frames[2]["anti_entropy"]["transfers"][0]["from"], "a")
        self.assertEqual(frames[2]["sync_checkpoint"], 1)
        self.assertEqual(frames[-1]["replicas"]["b"]["active_tags"]["notebook"], ["c:1"])
        self.assertEqual(frames[-1]["sync_checkpoint"], 4)
        self.assertTrue(frames[-1]["converged"])

    def test_render_replay_html_includes_scrubber_and_anti_entropy_table(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        snapshot = cluster.run_script(load_script(SAMPLE_SCRIPT))

        html = render_replay_html(
            snapshot,
            "sample replay",
            companion_links={"Timeline HTML": "timeline.html"},
        )

        self.assertIn("OR-Set replay / animation", html)
        self.assertIn('id="replay-range"', html)
        self.assertIn('id="replay-prev-sync"', html)
        self.assertIn('id="replay-next-sync"', html)
        self.assertIn('id="replay-speed"', html)
        self.assertIn('id="replay-link-list"', html)
        self.assertIn('id="replay-sync-links"', html)
        self.assertIn('id="replay-copy-exact-link"', html)
        self.assertIn('id="replay-copy-sync-link"', html)
        self.assertIn('id="replay-download-svg"', html)
        self.assertIn("Anti-entropy transfer view", html)
        self.assertIn('href="timeline.html"', html)
        self.assertIn("sync-", html)
        self.assertIn("Exact frame:", html)
        self.assertIn('aria-pressed="false"', html)
        self.assertIn('aria-live="polite" aria-atomic="true"', html)
        self.assertIn("const frames =", html)
        self.assertIn("const syncFrames =", html)
        self.assertIn("const exactStepHash =", html)
        self.assertIn("window.addEventListener('hashchange'", html)
        self.assertIn("function hashForFrame(frame)", html)
        self.assertIn("function buildCheckpointSvg(frame)", html)
        self.assertIn("navigator.clipboard.writeText", html)
        self.assertIn("URL.createObjectURL", html)
        self.assertIn("return svg.join('\\n') + '\\n';", html)
        self.assertIn("Playback speed", html)

    def test_render_replay_html_javascript_passes_node_syntax_check(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is required for generated replay JavaScript syntax checks")

        cluster = ReplicaCluster(["a", "b", "c"])
        snapshot = cluster.run_script(load_script(SAMPLE_SCRIPT))
        html = render_replay_html(snapshot, "sample replay")
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "replay.js"
            script_path.write_text(script)
            completed = subprocess.run(
                [node, "--check", str(script_path)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_cli_run_script_writes_timeline_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir) / "artifacts"
            markdown_path = artifact_dir / "timeline.md"
            mermaid_path = artifact_dir / "timeline.mmd"
            svg_path = artifact_dir / "timeline.svg"
            html_path = artifact_dir / "index.html"
            json_path = artifact_dir / "timeline.json"

            result = run_cli(
                "run-script",
                "--replicas",
                "a",
                "b",
                "c",
                "--script",
                str(SAMPLE_SCRIPT),
                "--timeline-markdown-out",
                str(markdown_path),
                "--timeline-mermaid-out",
                str(mermaid_path),
                "--timeline-svg-out",
                str(svg_path),
                "--timeline-html-out",
                str(html_path),
                "--json-out",
                str(json_path),
            )

            self.assertTrue(result["convergence"]["converged"])
            self.assertTrue(markdown_path.exists())
            self.assertTrue(mermaid_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertTrue(html_path.exists())
            self.assertTrue(json_path.exists())
            self.assertIn("OR-Set timeline", markdown_path.read_text())
            self.assertIn("sequenceDiagram", mermaid_path.read_text())
            self.assertIn("<svg", svg_path.read_text())
            html = html_path.read_text()
            self.assertIn('href="timeline.json"', html)
            self.assertIn("sample_ops.json", html)
            self.assertEqual(json.loads(json_path.read_text())["convergence"]["converged"], True)

    def test_cli_compare_script_writes_comparison_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir) / "artifacts"
            timeline_markdown_path = artifact_dir / "timeline.md"
            timeline_mermaid_path = artifact_dir / "timeline.mmd"
            timeline_svg_path = artifact_dir / "timeline.svg"
            timeline_html_path = artifact_dir / "timeline.html"
            orset_json_path = artifact_dir / "orset.json"
            comparison_markdown_path = artifact_dir / "comparison.md"
            comparison_html_path = artifact_dir / "comparison.html"
            comparison_json_path = artifact_dir / "comparison.json"

            result = run_cli(
                "compare-script",
                "--replicas",
                "a",
                "b",
                "c",
                "--script",
                str(SAMPLE_COMPARE_SCRIPT),
                "--timeline-markdown-out",
                str(timeline_markdown_path),
                "--timeline-mermaid-out",
                str(timeline_mermaid_path),
                "--timeline-svg-out",
                str(timeline_svg_path),
                "--timeline-html-out",
                str(timeline_html_path),
                "--json-out",
                str(orset_json_path),
                "--comparison-markdown-out",
                str(comparison_markdown_path),
                "--comparison-html-out",
                str(comparison_html_path),
                "--comparison-json-out",
                str(comparison_json_path),
            )

            self.assertEqual(result["final_divergence"][0]["element"], "notebook")
            self.assertTrue(timeline_markdown_path.exists())
            self.assertTrue(timeline_mermaid_path.exists())
            self.assertTrue(timeline_svg_path.exists())
            self.assertTrue(timeline_html_path.exists())
            self.assertTrue(orset_json_path.exists())
            self.assertTrue(comparison_markdown_path.exists())
            self.assertTrue(comparison_html_path.exists())
            self.assertTrue(comparison_json_path.exists())
            self.assertIn("OR-Set vs LWW-element-set comparison", comparison_markdown_path.read_text())
            comparison_html = comparison_html_path.read_text()
            self.assertIn("OR-Set vs LWW-element-set", comparison_html)
            self.assertIn('href="timeline.html"', comparison_html)
            self.assertIn('href="comparison.md"', comparison_html)
            self.assertIn("sample_compare_ops.json", comparison_html)
            comparison_json = json.loads(comparison_json_path.read_text())
            self.assertFalse(comparison_json["lww"]["convergence"]["membership"]["a"])
            self.assertEqual(comparison_json["orset"]["convergence"]["membership"]["a"], ["notebook"])

    def test_cli_list_presets_json_includes_known_scripts(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "list-presets", "--json"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual([preset["name"] for preset in payload["presets"]], [
            "concurrent-readd",
            "unobserved-remove",
            "observed-remove-sync",
        ])
        self.assertEqual(payload["presets"][1]["script"], "presets/unobserved-remove.json")

    def test_cli_compare_presets_writes_suite_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir) / "artifacts"
            markdown_path = artifact_dir / "comparison-presets.md"
            html_path = artifact_dir / "comparison-presets.html"
            json_path = artifact_dir / "comparison-presets.json"
            detail_dir = artifact_dir / "comparison-presets"

            result = run_cli(
                "compare-presets",
                "--suite-markdown-out",
                str(markdown_path),
                "--suite-html-out",
                str(html_path),
                "--suite-json-out",
                str(json_path),
                "--detail-output-dir",
                str(detail_dir),
            )

            self.assertEqual(result["preset_count"], 3)
            self.assertEqual(result["divergent_count"], 2)
            self.assertTrue(markdown_path.exists())
            self.assertTrue(html_path.exists())
            self.assertTrue(json_path.exists())
            self.assertIn("OR-Set comparison preset suite", markdown_path.read_text())
            html = html_path.read_text()
            self.assertIn("Concurrent re-add survives in OR-Set", html)
            self.assertIn("Observed remove yields the same final answer", html)
            self.assertIn('href="comparison-presets/concurrent-readd/index.html"', html)
            self.assertIn('href="comparison-presets/concurrent-readd/concurrent-readd-bundle.zip"', html)
            self.assertIn('href="comparison-presets/concurrent-readd/comparison.html"', html)
            self.assertIn('href="comparison-presets/concurrent-readd/replay.html"', html)
            payload = json.loads(json_path.read_text())
            self.assertEqual(payload["aligned_count"], 1)
            detail_bundle = next(preset for preset in payload["presets"] if preset["name"] == "concurrent-readd")["detail_bundle"]
            self.assertEqual(detail_bundle["bundle_index_html"], "comparison-presets/concurrent-readd/index.html")
            self.assertEqual(detail_bundle["bundle_zip"], "comparison-presets/concurrent-readd/concurrent-readd-bundle.zip")
            self.assertEqual(detail_bundle["bundle_script"], "comparison-presets/concurrent-readd/scenario-script.json")
            self.assertEqual(detail_bundle["comparison_html"], "comparison-presets/concurrent-readd/comparison.html")
            bundle_index = detail_dir / "concurrent-readd" / "index.html"
            self.assertTrue(bundle_index.exists())
            self.assertTrue((detail_dir / "concurrent-readd" / "scenario-script.json").exists())
            self.assertTrue((detail_dir / "concurrent-readd" / "comparison.html").exists())
            self.assertTrue((detail_dir / "concurrent-readd" / "timeline.html").exists())
            self.assertTrue((detail_dir / "concurrent-readd" / "replay.html").exists())
            self.assertTrue((detail_dir / "concurrent-readd" / "anti-entropy.html").exists())
            bundle_html = bundle_index.read_text()
            self.assertIn("portable landing page", bundle_html)
            self.assertIn('href="scenario-script.json"', bundle_html)
            self.assertIn('href="comparison.html"', bundle_html)
            self.assertIn('href="concurrent-readd-bundle.zip"', bundle_html)
            bundle_zip = detail_dir / "concurrent-readd" / "concurrent-readd-bundle.zip"
            self.assertTrue(bundle_zip.exists())
            first_bytes = bundle_zip.read_bytes()
            with zipfile.ZipFile(bundle_zip) as archive:
                self.assertEqual(
                    archive.namelist(),
                    [
                        "index.html",
                        "scenario-script.json",
                        "timeline.md",
                        "timeline.mmd",
                        "timeline.svg",
                        "timeline.html",
                        "replay.html",
                        "orset-snapshot.json",
                        "anti-entropy.md",
                        "anti-entropy.html",
                        "anti-entropy.json",
                        "comparison.md",
                        "comparison.html",
                        "comparison.json",
                    ],
                )
                self.assertTrue(all(info.date_time == (2020, 1, 1, 0, 0, 0) for info in archive.infolist()))

            rerun = run_cli(
                "compare-presets",
                "--suite-markdown-out",
                str(markdown_path),
                "--suite-html-out",
                str(html_path),
                "--suite-json-out",
                str(json_path),
                "--detail-output-dir",
                str(detail_dir),
            )
            self.assertEqual(rerun["preset_count"], 3)
            self.assertEqual(bundle_zip.read_bytes(), first_bytes)

    def test_cli_compare_presets_unknown_name_returns_parser_error(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "compare-presets", "--preset", "missing"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unknown comparison preset: missing", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_add_writes_timeline_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir) / "artifacts"
            markdown_path = artifact_dir / "add.md"
            mermaid_path = artifact_dir / "add.mmd"
            svg_path = artifact_dir / "add.svg"

            result = run_cli(
                "add",
                "--replicas",
                "a",
                "b",
                "--replica",
                "a",
                "--element",
                "notes",
                "--timeline-markdown-out",
                str(markdown_path),
                "--timeline-mermaid-out",
                str(mermaid_path),
                "--timeline-svg-out",
                str(svg_path),
            )

            self.assertEqual(result["replicas"]["a"]["active_tags"]["notes"], ["a:1"])
            self.assertTrue(markdown_path.exists())
            self.assertTrue(mermaid_path.exists())
            self.assertTrue(svg_path.exists())
            self.assertIn("single add a:notes", markdown_path.read_text())
            self.assertIn("add notes [a:1]", mermaid_path.read_text())
            self.assertIn("single add a:notes", svg_path.read_text())

    def test_sync_events_capture_anti_entropy_summary(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        snapshot = cluster.run_script(load_script(SAMPLE_SCRIPT))

        sync_event = next(event for event in snapshot["timeline"] if event["op"] == "sync")
        analysis = sync_event["anti_entropy"]

        self.assertEqual(analysis["transfer_count"], 2)
        self.assertGreater(analysis["full_sync_bytes"], 0)
        self.assertGreaterEqual(analysis["bytes_saved_vs_full"], 0)
        self.assertEqual(analysis["transfers"][0]["from"], "a")
        self.assertEqual(analysis["transfers"][0]["to"], "b")
        self.assertEqual(analysis["transfers"][0]["delta_payload"]["adds"]["notebook"], ["a:1"])

    def test_render_anti_entropy_views_include_delta_story(self) -> None:
        cluster = ReplicaCluster(["a", "b", "c"])
        snapshot = cluster.run_script(load_script(SAMPLE_SCRIPT))
        report = build_anti_entropy_report(snapshot)

        markdown = render_anti_entropy_markdown(report, "sample anti-entropy")
        html = render_anti_entropy_html(
            report,
            "sample anti-entropy",
            companion_links={"Timeline HTML": "timeline.html"},
        )

        self.assertIn("OR-Set anti-entropy report", markdown)
        self.assertIn("bytes saved vs full-state sync", markdown)
        self.assertIn("`a -> b`", markdown)
        self.assertIn("tags notebook=a:1", markdown)
        self.assertIn("OR-Set anti-entropy report", html)
        self.assertIn("Sync transfer details", html)
        self.assertIn('href="timeline.html"', html)

    def test_cli_run_script_writes_anti_entropy_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir) / "artifacts"
            timeline_html_path = artifact_dir / "timeline.html"
            anti_markdown_path = artifact_dir / "anti-entropy.md"
            anti_html_path = artifact_dir / "anti-entropy.html"
            anti_json_path = artifact_dir / "anti-entropy.json"

            result = run_cli(
                "run-script",
                "--replicas",
                "a",
                "b",
                "c",
                "--script",
                str(SAMPLE_SCRIPT),
                "--timeline-html-out",
                str(timeline_html_path),
                "--anti-entropy-markdown-out",
                str(anti_markdown_path),
                "--anti-entropy-html-out",
                str(anti_html_path),
                "--anti-entropy-json-out",
                str(anti_json_path),
            )

            self.assertTrue(result["convergence"]["converged"])
            self.assertTrue(anti_markdown_path.exists())
            self.assertTrue(anti_html_path.exists())
            self.assertTrue(anti_json_path.exists())
            self.assertIn("directional transfers", anti_markdown_path.read_text())
            anti_html = anti_html_path.read_text()
            self.assertIn('href="timeline.html"', anti_html)
            self.assertIn('href="anti-entropy.md"', anti_html)
            anti_json = json.loads(anti_json_path.read_text())
            self.assertGreaterEqual(anti_json["totals"]["bytes_saved_vs_full"], 0)
            self.assertEqual(anti_json["sync_count"], 4)

    def test_cli_run_script_writes_replay_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir) / "artifacts"
            timeline_html_path = artifact_dir / "timeline.html"
            replay_html_path = artifact_dir / "replay.html"
            anti_html_path = artifact_dir / "anti-entropy.html"

            result = run_cli(
                "run-script",
                "--replicas",
                "a",
                "b",
                "c",
                "--script",
                str(SAMPLE_SCRIPT),
                "--timeline-html-out",
                str(timeline_html_path),
                "--replay-html-out",
                str(replay_html_path),
                "--anti-entropy-html-out",
                str(anti_html_path),
            )

            self.assertTrue(result["convergence"]["converged"])
            replay_html = replay_html_path.read_text()
            self.assertIn("OR-Set replay / animation", replay_html)
            self.assertIn('href="timeline.html"', replay_html)
            self.assertIn('href="anti-entropy.html"', replay_html)
            self.assertIn('id="replay-play"', replay_html)
            self.assertIn('id="replay-copy-exact-link"', replay_html)
            self.assertIn('id="replay-download-svg"', replay_html)
            timeline_html = timeline_html_path.read_text()
            self.assertIn('href="replay.html"', timeline_html)
            anti_html = anti_html_path.read_text()
            self.assertIn('href="replay.html"', anti_html)

    def test_anti_entropy_markdown_handles_no_syncs(self) -> None:
        cluster = ReplicaCluster(["a", "b"])
        cluster.add("a", "notes")

        report = build_anti_entropy_report(cluster.snapshot())
        markdown = render_anti_entropy_markdown(report, "no sync yet")

        self.assertIn("no anti-entropy exchange yet", report["story"])
        self.assertIn("| n/a | no syncs yet | none | n/a | 0 | 0 | 0 | no transfer |", markdown)

    def test_cli_compare_script_can_link_anti_entropy_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir) / "artifacts"
            timeline_html_path = artifact_dir / "timeline.html"
            anti_markdown_path = artifact_dir / "anti-entropy.md"
            anti_html_path = artifact_dir / "anti-entropy.html"
            anti_json_path = artifact_dir / "anti-entropy.json"
            replay_html_path = artifact_dir / "replay.html"
            comparison_html_path = artifact_dir / "comparison.html"

            result = run_cli(
                "compare-script",
                "--replicas",
                "a",
                "b",
                "c",
                "--script",
                str(SAMPLE_COMPARE_SCRIPT),
                "--timeline-html-out",
                str(timeline_html_path),
                "--anti-entropy-markdown-out",
                str(anti_markdown_path),
                "--anti-entropy-html-out",
                str(anti_html_path),
                "--anti-entropy-json-out",
                str(anti_json_path),
                "--replay-html-out",
                str(replay_html_path),
                "--comparison-html-out",
                str(comparison_html_path),
            )

            self.assertEqual(result["final_divergence"][0]["element"], "notebook")
            self.assertTrue(anti_html_path.exists())
            self.assertTrue(comparison_html_path.exists())
            self.assertTrue(replay_html_path.exists())
            self.assertIn('href="anti-entropy.html"', comparison_html_path.read_text())
            self.assertIn('href="replay.html"', comparison_html_path.read_text())
            self.assertIn('href="anti-entropy.md"', anti_html_path.read_text())
            self.assertIn('href="anti-entropy.json"', anti_html_path.read_text())
            self.assertIn('href="comparison.html"', replay_html_path.read_text())

    def test_duplicate_replicas_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "replica names must be unique"):
            ReplicaCluster(["a", "a"])


if __name__ == "__main__":
    unittest.main()
