import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crdt_orset_lab import (
    LWWElementSet,
    ORSet,
    ReplicaCluster,
    build_anti_entropy_report,
    build_companion_links,
    build_semantics_comparison,
    load_script,
    parse_tag,
    render_anti_entropy_html,
    render_anti_entropy_markdown,
    render_comparison_html,
    render_comparison_markdown,
    render_timeline_html,
    render_timeline_markdown,
    render_timeline_mermaid,
    render_timeline_svg,
)


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "crdt_orset_lab.py"
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
                "--comparison-html-out",
                str(comparison_html_path),
            )

            self.assertEqual(result["final_divergence"][0]["element"], "notebook")
            self.assertTrue(anti_html_path.exists())
            self.assertTrue(comparison_html_path.exists())
            self.assertIn('href="anti-entropy.html"', comparison_html_path.read_text())
            self.assertIn('href="anti-entropy.md"', anti_html_path.read_text())
            self.assertIn('href="anti-entropy.json"', anti_html_path.read_text())

    def test_duplicate_replicas_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "replica names must be unique"):
            ReplicaCluster(["a", "a"])


if __name__ == "__main__":
    unittest.main()
