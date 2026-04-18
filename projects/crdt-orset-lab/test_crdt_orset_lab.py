import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crdt_orset_lab import ORSet, ReplicaCluster, load_script, parse_tag


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "crdt_orset_lab.py"
SAMPLE_SCRIPT = PROJECT_DIR / "sample_ops.json"


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

    def test_duplicate_replicas_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "replica names must be unique"):
            ReplicaCluster(["a", "a"])


if __name__ == "__main__":
    unittest.main()
