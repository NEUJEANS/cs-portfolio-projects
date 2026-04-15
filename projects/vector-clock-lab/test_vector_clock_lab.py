import json
import subprocess
import sys
import unittest
from pathlib import Path

from vector_clock_lab import PartitionScenario, PartitionWrite, ReplicaStore, VectorClock, simulate_partition


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT = PROJECT_DIR / "vector_clock_lab.py"


def run_cli(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=PROJECT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


class VectorClockLabTests(unittest.TestCase):
    def test_vector_clock_compare_cases(self) -> None:
        base = VectorClock({"a": 1})
        newer = VectorClock({"a": 1, "b": 1})
        other_branch = VectorClock({"a": 2})

        self.assertEqual(base.compare(newer), "before")
        self.assertEqual(newer.compare(base), "after")
        self.assertEqual(base.compare(VectorClock({"a": 1})), "equal")
        self.assertEqual(newer.compare(other_branch), "concurrent")

    def test_write_replaces_older_version_for_same_key(self) -> None:
        store = ReplicaStore(["a", "b"])
        first = store.write("a", "profile", "draft")
        second = store.write("a", "profile", "published")

        versions = store.get_versions("profile")
        self.assertEqual(first.clock.compare(second.clock), "before")
        self.assertEqual([version.value for version in versions], ["published"])

    def test_concurrent_writes_create_conflict_versions(self) -> None:
        store = ReplicaStore(["a", "b"])
        store.write("a", "profile", "draft-a")
        store.write("b", "profile", "draft-b")

        versions = store.get_versions("profile")
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].clock.compare(versions[1].clock), "concurrent")

    def test_replicate_merges_clock_and_retains_version(self) -> None:
        source = ReplicaStore(["a", "b"])
        version = source.write("a", "profile", "draft")

        target = ReplicaStore(["a", "b"])
        target.replicate("b", "profile", version)

        self.assertEqual(target.replica_clocks["b"].to_dict(), {"a": 1})
        self.assertEqual(target.get_versions("profile")[0].value, "draft")

    def test_merge_conflicts_produces_single_causally_newer_value(self) -> None:
        store = ReplicaStore(["a", "b", "c"])
        left = store.write("a", "profile", "draft-a")
        right = store.write("b", "profile", "draft-b")

        merged = store.merge_conflicts("c", "profile")

        self.assertEqual(len(store.get_versions("profile")), 1)
        self.assertEqual(left.clock.compare(merged.clock), "before")
        self.assertEqual(right.clock.compare(merged.clock), "before")
        self.assertEqual(merged.value, "draft-a | draft-b")

    def test_partition_simulation_heals_and_merges_conflicts(self) -> None:
        store = ReplicaStore(["a", "b", "c"])
        result = simulate_partition(
            store,
            PartitionScenario(
                key="profile",
                left_partition=("a", "b"),
                right_partition=("c",),
                left_writes=(PartitionWrite("a", "draft-a"),),
                right_writes=(PartitionWrite("c", "draft-c"),),
                heal_replica="b",
            ),
        )

        self.assertTrue(result["conflict_detected"])
        self.assertEqual(len(result["versions_before_heal"]), 2)
        self.assertEqual(result["merged"]["clock"], {"a": 1, "b": 1, "c": 1})
        self.assertEqual(
            result["snapshot_after_merge"]["data"]["profile"][0]["value"],
            "draft-a | draft-c",
        )

    def test_partition_requires_full_disjoint_cover(self) -> None:
        store = ReplicaStore(["a", "b", "c"])
        with self.assertRaisesRegex(ValueError, "cover every replica exactly once"):
            simulate_partition(
                store,
                PartitionScenario(
                    key="profile",
                    left_partition=("a",),
                    right_partition=("b",),
                    left_writes=(),
                    right_writes=(),
                ),
            )

    def test_cli_compare_and_conflict_merge_flow(self) -> None:
        compare = run_cli("compare", '{"a": 1}', '{"a": 1, "b": 1}')
        self.assertEqual(compare["relation"], "before")

        conflict = run_cli(
            "conflict",
            "--replicas",
            "a",
            "b",
            "c",
            "--key",
            "essay",
            "--left-replica",
            "a",
            "--left-value",
            "draft-a",
            "--right-replica",
            "b",
            "--right-value",
            "draft-b",
            "--merge-replica",
            "c",
        )

        self.assertTrue(conflict["conflict"])
        self.assertEqual(conflict["merged"]["value"], "draft-a | draft-b")
        self.assertEqual(conflict["snapshot"]["data"]["essay"][0]["clock"], {"a": 1, "b": 1, "c": 1})

    def test_cli_partition_flow_reports_versions_before_and_after_merge(self) -> None:
        result = run_cli(
            "partition",
            "--replicas",
            "a",
            "b",
            "c",
            "--key",
            "profile",
            "--left-partition",
            "a",
            "b",
            "--right-partition",
            "c",
            "--left-write",
            "a:draft-a",
            "--right-write",
            "c:draft-c",
            "--heal-replica",
            "b",
        )

        self.assertTrue(result["conflict_detected"])
        self.assertEqual(len(result["versions_before_heal"]), 2)
        self.assertEqual(result["merged"]["replica"], "b")
        self.assertEqual(
            result["snapshot_after_merge"]["data"]["profile"][0]["clock"],
            {"a": 1, "b": 1, "c": 1},
        )

    def test_duplicate_replica_names_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "replica names must be unique"):
            ReplicaStore(["a", "a"])

    def test_invalid_merge_requires_multiple_versions(self) -> None:
        store = ReplicaStore(["a", "b"])
        store.write("a", "profile", "only-version")

        with self.assertRaisesRegex(ValueError, "need at least two conflicting versions"):
            store.merge_conflicts("b", "profile")


if __name__ == "__main__":
    unittest.main()
