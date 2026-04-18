from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from html import escape as escape_html
from pathlib import Path
from textwrap import wrap
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SyncOperation:
    source: str
    target: str
    direction: str = "both"


PROJECT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class ComparisonPreset:
    name: str
    title: str
    description: str
    script_path: Path
    replicas: tuple[str, ...]
    lww_bias: str = "remove"


class ORSet:
    def __init__(
        self,
        adds: dict[str, set[str]] | None = None,
        tombstones: set[str] | None = None,
        counters: dict[str, int] | None = None,
    ) -> None:
        self.adds: dict[str, set[str]] = {
            element: set(tags)
            for element, tags in (adds or {}).items()
            if element and tags
        }
        self.tombstones: set[str] = set(tombstones or set())
        self.counters: dict[str, int] = {replica: int(value) for replica, value in (counters or {}).items()}
        self._normalize_counters_from_tags()

    def copy(self) -> "ORSet":
        return ORSet(
            adds={element: set(tags) for element, tags in self.adds.items()},
            tombstones=set(self.tombstones),
            counters=dict(self.counters),
        )

    def add(self, replica: str, element: str) -> str:
        self._validate_replica(replica)
        self._validate_element(element)
        counter = self.counters.get(replica, 0) + 1
        self.counters[replica] = counter
        tag = f"{replica}:{counter}"
        self.adds.setdefault(element, set()).add(tag)
        return tag

    def remove(self, element: str) -> list[str]:
        self._validate_element(element)
        observed = sorted(self.active_tags(element))
        self.tombstones.update(observed)
        return observed

    def active_tags(self, element: str) -> set[str]:
        self._validate_element(element)
        return set(self.adds.get(element, set()) - self.tombstones)

    def contains(self, element: str) -> bool:
        return bool(self.active_tags(element))

    def elements(self) -> list[str]:
        return sorted(element for element in self.adds if self.contains(element))

    def merge(self, other: "ORSet") -> "ORSet":
        merged_adds: dict[str, set[str]] = {
            element: set(tags) for element, tags in self.adds.items()
        }
        for element, tags in other.adds.items():
            merged_adds.setdefault(element, set()).update(tags)
        merged_counters = dict(self.counters)
        for replica, counter in other.counters.items():
            merged_counters[replica] = max(merged_counters.get(replica, 0), counter)
        merged = ORSet(
            adds=merged_adds,
            tombstones=self.tombstones | other.tombstones,
            counters=merged_counters,
        )
        merged._normalize_counters_from_tags()
        return merged

    def to_dict(self) -> dict[str, object]:
        return {
            "elements": self.elements(),
            "active_tags": {
                element: sorted(self.active_tags(element))
                for element in sorted(self.adds)
                if self.active_tags(element)
            },
            "observed_tags": {
                element: sorted(self.adds[element]) for element in sorted(self.adds)
            },
            "tombstones": sorted(self.tombstones),
            "counters": dict(sorted(self.counters.items())),
        }

    def _normalize_counters_from_tags(self) -> None:
        for replica, counter in list(self.counters.items()):
            if counter < 0:
                raise ValueError("replica counters must be non-negative")
            if counter == 0:
                self.counters.pop(replica)
        for tags in list(self.adds.values()) + [self.tombstones]:
            for tag in tags:
                replica, counter = parse_tag(tag)
                self.counters[replica] = max(self.counters.get(replica, 0), counter)

    @staticmethod
    def _validate_replica(replica: str) -> None:
        if not replica:
            raise ValueError("replica must be non-empty")

    @staticmethod
    def _validate_element(element: str) -> None:
        if not element:
            raise ValueError("element must be non-empty")


class ReplicaCluster:
    def __init__(self, replicas: Iterable[str]) -> None:
        replica_list = list(replicas)
        if not replica_list or any(not replica for replica in replica_list):
            raise ValueError("replicas must contain only non-empty names")
        if len(set(replica_list)) != len(replica_list):
            raise ValueError("replica names must be unique")
        self.replicas = tuple(sorted(replica_list))
        self.states = {replica: ORSet() for replica in self.replicas}
        self.timeline: list[dict[str, object]] = []

    def add(self, replica: str, element: str) -> str:
        state = self._state(replica)
        tag = state.add(replica, element)
        self.timeline.append(
            {
                "op": "add",
                "replica": replica,
                "element": element,
                "tag": tag,
                "state": state.to_dict(),
            }
        )
        return tag

    def remove(self, replica: str, element: str) -> list[str]:
        state = self._state(replica)
        removed_tags = state.remove(element)
        self.timeline.append(
            {
                "op": "remove",
                "replica": replica,
                "element": element,
                "removed_tags": removed_tags,
                "state": state.to_dict(),
            }
        )
        return removed_tags

    def sync(self, source: str, target: str, *, direction: str = "both") -> dict[str, object]:
        self._validate_sync_direction(direction)
        self._state(source)
        self._state(target)
        source_before = self.states[source].copy()
        target_before = self.states[target].copy()
        anti_entropy = build_sync_anti_entropy(source, target, source_before, target_before, direction=direction)
        if direction == "both":
            self.states[source] = source_before.merge(target_before)
            self.states[target] = target_before.merge(source_before)
        elif direction == "forward":
            self.states[target] = target_before.merge(source_before)
        else:
            self.states[source] = source_before.merge(target_before)

        event = {
            "op": "sync",
            "source": source,
            "target": target,
            "direction": direction,
            "source_state": self.states[source].to_dict(),
            "target_state": self.states[target].to_dict(),
            "anti_entropy": anti_entropy,
        }
        self.timeline.append(event)
        return event

    def convergence_report(self) -> dict[str, object]:
        membership = {
            replica: self.states[replica].elements()
            for replica in self.replicas
        }
        tag_views = {
            replica: self.states[replica].to_dict()["active_tags"]
            for replica in self.replicas
        }
        state_views = {
            replica: self.states[replica].to_dict()
            for replica in self.replicas
        }
        baseline_state = next(iter(state_views.values()), {})
        converged = all(view == baseline_state for view in state_views.values())
        return {
            "converged": converged,
            "membership": membership,
            "active_tags": tag_views,
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "replicas": {
                replica: self.states[replica].to_dict() for replica in self.replicas
            },
            "timeline": list(self.timeline),
            "convergence": self.convergence_report(),
        }

    def run_script(self, operations: Sequence[dict[str, object]]) -> dict[str, object]:
        for index, operation in enumerate(operations, start=1):
            op_name = str(operation.get("op", "")).strip()
            if op_name == "add":
                self.add(str(operation["replica"]), str(operation["element"]))
            elif op_name == "remove":
                self.remove(str(operation["replica"]), str(operation["element"]))
            elif op_name == "sync":
                self.sync(
                    str(operation["source"]),
                    str(operation["target"]),
                    direction=str(operation.get("direction", "both")),
                )
            else:
                raise ValueError(f"unsupported op at index {index}: {op_name or '<missing>'}")
        return self.snapshot()

    def _state(self, replica: str) -> ORSet:
        try:
            return self.states[replica]
        except KeyError as exc:
            raise ValueError(f"unknown replica: {replica}") from exc

    @staticmethod
    def _validate_sync_direction(direction: str) -> None:
        if direction not in {"both", "forward", "reverse"}:
            raise ValueError("sync direction must be one of: both, forward, reverse")


class LWWElementSet:
    def __init__(
        self,
        add_timestamps: dict[str, int] | None = None,
        remove_timestamps: dict[str, int] | None = None,
        *,
        bias: str = "remove",
    ) -> None:
        self._validate_bias(bias)
        self.bias = bias
        self.add_timestamps = {
            element: int(timestamp)
            for element, timestamp in (add_timestamps or {}).items()
            if element
        }
        self.remove_timestamps = {
            element: int(timestamp)
            for element, timestamp in (remove_timestamps or {}).items()
            if element
        }
        self._validate_timestamp_map(self.add_timestamps)
        self._validate_timestamp_map(self.remove_timestamps)

    def copy(self) -> "LWWElementSet":
        return LWWElementSet(
            add_timestamps=dict(self.add_timestamps),
            remove_timestamps=dict(self.remove_timestamps),
            bias=self.bias,
        )

    def add(self, element: str, timestamp: int) -> int:
        self._validate_element(element)
        self._validate_timestamp(timestamp)
        current = self.add_timestamps.get(element)
        if current is None or timestamp > current:
            self.add_timestamps[element] = timestamp
        return self.add_timestamps[element]

    def remove(self, element: str, timestamp: int) -> int:
        self._validate_element(element)
        self._validate_timestamp(timestamp)
        current = self.remove_timestamps.get(element)
        if current is None or timestamp > current:
            self.remove_timestamps[element] = timestamp
        return self.remove_timestamps[element]

    def contains(self, element: str) -> bool:
        self._validate_element(element)
        add_timestamp = self.add_timestamps.get(element)
        remove_timestamp = self.remove_timestamps.get(element)
        if add_timestamp is None:
            return False
        if remove_timestamp is None:
            return True
        if add_timestamp == remove_timestamp:
            return self.bias == "add"
        return add_timestamp > remove_timestamp

    def elements(self) -> list[str]:
        return sorted(
            element
            for element in set(self.add_timestamps) | set(self.remove_timestamps)
            if self.contains(element)
        )

    def merge(self, other: "LWWElementSet") -> "LWWElementSet":
        if self.bias != other.bias:
            raise ValueError("cannot merge LWW sets with different tie biases")
        merged_adds = dict(self.add_timestamps)
        for element, timestamp in other.add_timestamps.items():
            merged_adds[element] = max(merged_adds.get(element, timestamp), timestamp)
        merged_removes = dict(self.remove_timestamps)
        for element, timestamp in other.remove_timestamps.items():
            merged_removes[element] = max(merged_removes.get(element, timestamp), timestamp)
        return LWWElementSet(
            add_timestamps=merged_adds,
            remove_timestamps=merged_removes,
            bias=self.bias,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "bias": self.bias,
            "elements": self.elements(),
            "add_timestamps": dict(sorted(self.add_timestamps.items())),
            "remove_timestamps": dict(sorted(self.remove_timestamps.items())),
        }

    @staticmethod
    def _validate_element(element: str) -> None:
        if not element:
            raise ValueError("element must be non-empty")

    @staticmethod
    def _validate_timestamp(timestamp: int) -> None:
        if timestamp < 0:
            raise ValueError("timestamps must be non-negative integers")

    @staticmethod
    def _validate_bias(bias: str) -> None:
        if bias not in {"add", "remove"}:
            raise ValueError("LWW tie bias must be 'add' or 'remove'")

    @classmethod
    def _validate_timestamp_map(cls, mapping: dict[str, int]) -> None:
        for timestamp in mapping.values():
            cls._validate_timestamp(int(timestamp))


class LWWReplicaCluster:
    def __init__(self, replicas: Iterable[str], *, bias: str = "remove") -> None:
        replica_list = list(replicas)
        if not replica_list or any(not replica for replica in replica_list):
            raise ValueError("replicas must contain only non-empty names")
        if len(set(replica_list)) != len(replica_list):
            raise ValueError("replica names must be unique")
        self.replicas = tuple(sorted(replica_list))
        self.bias = bias
        self.states = {replica: LWWElementSet(bias=bias) for replica in self.replicas}
        self.timeline: list[dict[str, object]] = []

    def add(self, replica: str, element: str, timestamp: int) -> int:
        state = self._state(replica)
        effective_timestamp = state.add(element, timestamp)
        self.timeline.append(
            {
                "op": "add",
                "replica": replica,
                "element": element,
                "timestamp": effective_timestamp,
                "state": state.to_dict(),
            }
        )
        return effective_timestamp

    def remove(self, replica: str, element: str, timestamp: int) -> int:
        state = self._state(replica)
        effective_timestamp = state.remove(element, timestamp)
        self.timeline.append(
            {
                "op": "remove",
                "replica": replica,
                "element": element,
                "timestamp": effective_timestamp,
                "state": state.to_dict(),
            }
        )
        return effective_timestamp

    def sync(self, source: str, target: str, *, direction: str = "both") -> dict[str, object]:
        ReplicaCluster._validate_sync_direction(direction)
        self._state(source)
        self._state(target)
        if direction == "both":
            source_before = self.states[source].copy()
            target_before = self.states[target].copy()
            self.states[source] = source_before.merge(target_before)
            self.states[target] = target_before.merge(source_before)
        elif direction == "forward":
            self.states[target] = self.states[target].merge(self.states[source])
        else:
            self.states[source] = self.states[source].merge(self.states[target])

        event = {
            "op": "sync",
            "source": source,
            "target": target,
            "direction": direction,
            "source_state": self.states[source].to_dict(),
            "target_state": self.states[target].to_dict(),
        }
        self.timeline.append(event)
        return event

    def convergence_report(self) -> dict[str, object]:
        membership = {
            replica: self.states[replica].elements()
            for replica in self.replicas
        }
        state_views = {
            replica: self.states[replica].to_dict()
            for replica in self.replicas
        }
        baseline_state = next(iter(state_views.values()), {})
        converged = all(view == baseline_state for view in state_views.values())
        return {
            "converged": converged,
            "membership": membership,
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "bias": self.bias,
            "replicas": {
                replica: self.states[replica].to_dict() for replica in self.replicas
            },
            "timeline": list(self.timeline),
            "convergence": self.convergence_report(),
        }

    def run_script(self, operations: Sequence[dict[str, object]]) -> dict[str, object]:
        for index, operation in enumerate(operations, start=1):
            op_name = str(operation.get("op", "")).strip()
            if op_name == "add":
                self.add(
                    str(operation["replica"]),
                    str(operation["element"]),
                    logical_timestamp_from_operation(operation, fallback=index),
                )
            elif op_name == "remove":
                self.remove(
                    str(operation["replica"]),
                    str(operation["element"]),
                    logical_timestamp_from_operation(operation, fallback=index),
                )
            elif op_name == "sync":
                self.sync(
                    str(operation["source"]),
                    str(operation["target"]),
                    direction=str(operation.get("direction", "both")),
                )
            else:
                raise ValueError(f"unsupported op at index {index}: {op_name or '<missing>'}")
        return self.snapshot()

    def _state(self, replica: str) -> LWWElementSet:
        try:
            return self.states[replica]
        except KeyError as exc:
            raise ValueError(f"unknown replica: {replica}") from exc


def logical_timestamp_from_operation(operation: dict[str, object], *, fallback: int) -> int:
    value = operation.get("time", operation.get("timestamp"))
    if value is None:
        return fallback
    if isinstance(value, bool):
        raise ValueError("logical timestamps must be integers, not booleans")
    if isinstance(value, int):
        timestamp = value
    elif isinstance(value, float) and value.is_integer():
        timestamp = int(value)
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped or not stripped.lstrip("-").isdigit():
            raise ValueError(f"invalid logical timestamp: {value}")
        timestamp = int(stripped)
    else:
        raise ValueError(f"invalid logical timestamp: {value}")
    if timestamp < 0:
        raise ValueError("logical timestamps must be non-negative")
    return timestamp



def parse_tag(tag: str) -> tuple[str, int]:
    replica, separator, counter_text = tag.partition(":")
    if not separator or not replica or not counter_text.isdigit():
        raise ValueError(f"invalid OR-Set tag: {tag}")
    return replica, int(counter_text)


def load_script(path: str | Path) -> list[dict[str, object]]:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, dict):
        operations = payload.get("operations")
    else:
        operations = payload
    if not isinstance(operations, list):
        raise ValueError("script JSON must be a list of operations or an object with an operations list")
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError("each operation must be an object")
    return operations


COMPARISON_PRESETS: dict[str, ComparisonPreset] = {
    "concurrent-readd": ComparisonPreset(
        name="concurrent-readd",
        title="Concurrent re-add survives in OR-Set",
        description=(
            "Replica b removes only the tag it observed, while replica c later adds the same element with a fresh tag. "
            "OR-Set keeps the new tag after sync, but remove-wins LWW drops the element because the later remove timestamp still dominates."
        ),
        script_path=PROJECT_DIR / "sample_compare_ops.json",
        replicas=("a", "b", "c"),
        lww_bias="remove",
    ),
    "unobserved-remove": ComparisonPreset(
        name="unobserved-remove",
        title="Unobserved remove cannot tombstone unseen tags",
        description=(
            "Replica c issues a remove before it has ever observed a's add. "
            "The OR-Set remove is effectively empty, but LWW still records a later remove timestamp that suppresses the earlier add once replicas merge."
        ),
        script_path=PROJECT_DIR / "presets" / "unobserved-remove.json",
        replicas=("a", "b", "c"),
        lww_bias="remove",
    ),
    "observed-remove-sync": ComparisonPreset(
        name="observed-remove-sync",
        title="Observed remove yields the same final answer",
        description=(
            "Replica b first syncs the add and then removes the element, so both models agree on the final absence. "
            "This preset is a useful control case beside the divergence-heavy scenarios."
        ),
        script_path=PROJECT_DIR / "presets" / "observed-remove-sync.json",
        replicas=("a", "b", "c"),
        lww_bias="remove",
    ),
}


def list_comparison_presets() -> list[ComparisonPreset]:
    return list(COMPARISON_PRESETS.values())


def resolve_comparison_preset(name: str) -> ComparisonPreset:
    try:
        return COMPARISON_PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(COMPARISON_PRESETS))
        raise ValueError(f"unknown comparison preset: {name}. choose from: {available}") from exc


def select_comparison_presets(selected_names: Sequence[str] | None = None) -> list[ComparisonPreset]:
    if not selected_names:
        return list_comparison_presets()
    presets: list[ComparisonPreset] = []
    seen: set[str] = set()
    for name in selected_names:
        if name in seen:
            continue
        seen.add(name)
        presets.append(resolve_comparison_preset(name))
    return presets


def comparison_preset_script_label(preset: ComparisonPreset) -> str:
    return Path(os.path.relpath(preset.script_path, PROJECT_DIR)).as_posix()


def comparison_preset_to_dict(preset: ComparisonPreset) -> dict[str, object]:
    return {
        "name": preset.name,
        "title": preset.title,
        "description": preset.description,
        "script": comparison_preset_script_label(preset),
        "replicas": list(preset.replicas),
        "lww_bias": preset.lww_bias,
    }


def format_membership_map(membership: dict[str, object]) -> str:
    parts: list[str] = []
    for replica, elements in sorted(membership.items()):
        element_list = [str(element) for element in elements]
        parts.append(f"{replica}={','.join(element_list) if element_list else '∅'}")
    return "; ".join(parts) or "∅"


def build_comparison_preset_suite(selected_names: Sequence[str] | None = None) -> dict[str, object]:
    selected = select_comparison_presets(selected_names)
    scenarios: list[dict[str, object]] = []
    divergent_count = 0
    for preset in selected:
        comparison = build_semantics_comparison(
            preset.replicas,
            load_script(preset.script_path),
            lww_bias=preset.lww_bias,
        )
        final_divergence = list(comparison["final_divergence"])
        divergent_count += 1 if final_divergence else 0
        lww_membership = {
            replica: list(dict(state)["elements"])
            for replica, state in dict(comparison["lww"]["replicas"]).items()
        }
        scenarios.append(
            {
                "name": preset.name,
                "title": preset.title,
                "description": preset.description,
                "script": comparison_preset_script_label(preset),
                "replicas": list(preset.replicas),
                "lww_bias": preset.lww_bias,
                "step_count": comparison["step_count"],
                "story": comparison["story"],
                "outcome": "diverge" if final_divergence else "align",
                "final_divergence_count": len(final_divergence),
                "final_divergence": final_divergence,
                "orset_membership": dict(comparison["orset"]["convergence"]["membership"]),
                "lww_membership": lww_membership,
            }
        )
    aligned_count = len(scenarios) - divergent_count
    story = (
        f"{divergent_count} preset(s) finish with different OR-Set vs LWW membership, while {aligned_count} preset(s) agree on the final answer. "
        "Together they make it easier to explain when observed-remove tags matter and when timestamp ordering is enough."
    )
    return {
        "preset_count": len(scenarios),
        "divergent_count": divergent_count,
        "aligned_count": aligned_count,
        "story": story,
        "presets": scenarios,
    }


def format_comparison_preset_text() -> str:
    lines = ["built-in OR-Set comparison presets:"]
    for preset in list_comparison_presets():
        lines.append(
            f"- {preset.name} ({preset.lww_bias}-wins LWW, replicas={','.join(preset.replicas)}): {preset.title}"
        )
        lines.append(f"  script: {comparison_preset_script_label(preset)}")
        lines.append(f"  {preset.description}")
    return "\n".join(lines) + "\n"


def canonical_json_text(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_bytes(value: object) -> int:
    return len(canonical_json_text(value).encode("utf-8"))


def transport_payload_from_orset(state: ORSet) -> dict[str, object]:
    return {
        "adds": {
            element: sorted(tags)
            for element, tags in sorted(state.adds.items())
            if tags
        },
        "tombstones": sorted(state.tombstones),
        "counters": dict(sorted(state.counters.items())),
    }


def transport_payload_from_state_dict(state: dict[str, object]) -> dict[str, object]:
    return {
        "adds": {
            str(element): [str(tag) for tag in tags]
            for element, tags in sorted(dict(state["observed_tags"]).items())
            if tags
        },
        "tombstones": [str(tag) for tag in state["tombstones"]],
        "counters": {str(replica): int(counter) for replica, counter in sorted(dict(state["counters"]).items())},
    }


def payload_summary(
    payload: dict[str, object],
    *,
    active_elements: Sequence[object] | None = None,
    active_tags: dict[str, Sequence[object]] | None = None,
) -> dict[str, object]:
    adds = {str(element): [str(tag) for tag in tags] for element, tags in dict(payload.get("adds", {})).items()}
    tombstones = [str(tag) for tag in payload.get("tombstones", [])]
    counters = {str(replica): int(counter) for replica, counter in dict(payload.get("counters", {})).items()}
    observed_tag_count = sum(len(tags) for tags in adds.values())
    summary: dict[str, object] = {
        "digest": hashlib.sha256(canonical_json_text(payload).encode("utf-8")).hexdigest(),
        "payload_bytes": payload_bytes(payload),
        "element_count": len(adds),
        "observed_tag_count": observed_tag_count,
        "tombstone_count": len(tombstones),
        "counter_count": len(counters),
    }
    if active_elements is not None:
        summary["active_element_count"] = len(list(active_elements))
    if active_tags is not None:
        summary["active_tag_count"] = sum(len(tags) for tags in active_tags.values())
    return summary


def digest_view_from_orset(state: ORSet) -> dict[str, object]:
    payload = transport_payload_from_orset(state)
    return payload_summary(
        payload,
        active_elements=state.elements(),
        active_tags={element: sorted(state.active_tags(element)) for element in state.adds if state.active_tags(element)},
    )


def digest_view_from_state_dict(state: dict[str, object]) -> dict[str, object]:
    payload = transport_payload_from_state_dict(state)
    return payload_summary(
        payload,
        active_elements=[str(element) for element in state["elements"]],
        active_tags={str(element): [str(tag) for tag in tags] for element, tags in dict(state["active_tags"]).items()},
    )


def delta_payload(source: ORSet, target: ORSet) -> dict[str, object]:
    missing_adds: dict[str, list[str]] = {}
    for element, tags in sorted(source.adds.items()):
        missing = sorted(tags - target.adds.get(element, set()))
        if missing:
            missing_adds[element] = missing
    counter_advancements = {
        replica: counter
        for replica, counter in sorted(source.counters.items())
        if counter > target.counters.get(replica, 0)
    }
    return {
        "adds": missing_adds,
        "tombstones": sorted(source.tombstones - target.tombstones),
        "counters": counter_advancements,
    }


def summarize_scalar_mapping(mapping: dict[str, object]) -> str:
    parts: list[str] = []
    for key in sorted(mapping):
        parts.append(f"{key}={mapping[key]}")
    return "; ".join(parts) if parts else "∅"


def summarize_delta_payload(payload: dict[str, object]) -> str:
    adds = summarize_tag_mapping({str(element): [str(tag) for tag in tags] for element, tags in dict(payload.get("adds", {})).items()})
    tombstones = ", ".join(str(tag) for tag in payload.get("tombstones", [])) or "∅"
    counters = summarize_scalar_mapping({str(replica): int(counter) for replica, counter in dict(payload.get("counters", {})).items()})
    return f"tags {adds}; tombstones {tombstones}; counters {counters}"


def build_directional_transfer(source_name: str, target_name: str, source: ORSet, target: ORSet) -> dict[str, object]:
    source_digest = digest_view_from_orset(source)
    target_digest = digest_view_from_orset(target)
    delta = delta_payload(source, target)
    delta_summary = payload_summary(delta)
    return {
        "from": source_name,
        "to": target_name,
        "from_digest": source_digest["digest"],
        "to_digest": target_digest["digest"],
        "digest_match_before": source_digest["digest"] == target_digest["digest"],
        "full_state": source_digest,
        "delta": delta_summary,
        "delta_payload": delta,
        "bytes_saved_vs_full": int(source_digest["payload_bytes"]) - int(delta_summary["payload_bytes"]),
    }


def build_sync_anti_entropy(
    source_name: str,
    target_name: str,
    source_before: ORSet,
    target_before: ORSet,
    *,
    direction: str,
) -> dict[str, object]:
    source_digest = digest_view_from_orset(source_before)
    target_digest = digest_view_from_orset(target_before)
    transfers: list[dict[str, object]] = []
    if direction in {"both", "forward"}:
        transfers.append(build_directional_transfer(source_name, target_name, source_before, target_before))
    if direction in {"both", "reverse"}:
        transfers.append(build_directional_transfer(target_name, source_name, target_before, source_before))
    full_sync_bytes = sum(int(transfer["full_state"]["payload_bytes"]) for transfer in transfers)
    delta_sync_bytes = sum(int(transfer["delta"]["payload_bytes"]) for transfer in transfers)
    return {
        "source_before": source_digest,
        "target_before": target_digest,
        "digest_match_before": source_digest["digest"] == target_digest["digest"],
        "transfers": transfers,
        "transfer_count": len(transfers),
        "full_sync_bytes": full_sync_bytes,
        "delta_sync_bytes": delta_sync_bytes,
        "bytes_saved_vs_full": full_sync_bytes - delta_sync_bytes,
    }


def summarize_tag_mapping(mapping: dict[str, Sequence[str]]) -> str:
    parts: list[str] = []
    for element in sorted(mapping):
        tags = [str(tag) for tag in mapping[element]]
        tag_text = ", ".join(tags) if tags else "∅"
        parts.append(f"{element}={tag_text}")
    return "; ".join(parts) if parts else "∅"


def summarize_state(state: dict[str, object]) -> str:
    elements = ", ".join(str(element) for element in state["elements"]) or "∅"
    active = summarize_tag_mapping(dict(state["active_tags"]))
    tombstones = ", ".join(str(tag) for tag in state["tombstones"]) or "∅"
    return f"elements {elements}; active {active}; tombstones {tombstones}"


def compact_state_note(state: dict[str, object]) -> str:
    elements = ", ".join(str(element) for element in state["elements"]) or "∅"
    active = summarize_tag_mapping(dict(state["active_tags"]))
    tombstones = ", ".join(str(tag) for tag in state["tombstones"]) or "∅"
    return f"elements={elements} | active={active} | tombstones={tombstones}"


def clone_state_view(state: dict[str, object] | None = None) -> dict[str, object]:
    source = dict(state or {})
    return {
        "elements": [str(element) for element in source.get("elements", [])],
        "active_tags": {
            str(element): [str(tag) for tag in tags]
            for element, tags in dict(source.get("active_tags") or {}).items()
        },
        "observed_tags": {
            str(element): [str(tag) for tag in tags]
            for element, tags in dict(source.get("observed_tags") or {}).items()
        },
        "tombstones": [str(tag) for tag in source.get("tombstones", [])],
        "counters": {
            str(replica): int(counter)
            for replica, counter in dict(source.get("counters") or {}).items()
        },
    }


def state_detail_rows(state: dict[str, object]) -> list[tuple[str, str]]:
    counters = ", ".join(
        f"{replica}:{counter}" for replica, counter in sorted(dict(state["counters"]).items())
    ) or "∅"
    return [
        ("Elements", ", ".join(str(element) for element in state["elements"]) or "∅"),
        ("Active tags", summarize_tag_mapping(dict(state["active_tags"]))),
        ("Observed tags", summarize_tag_mapping(dict(state["observed_tags"]))),
        ("Tombstones", ", ".join(str(tag) for tag in state["tombstones"]) or "∅"),
        ("Counters", counters),
    ]


def sanitize_mermaid_text(text: str) -> str:
    sanitized = " ".join(text.replace("`", "").replace('"', "'").split())
    return sanitized.replace(" end ", " [end] ").replace(" end", " [end]")


def mermaid_span(ids: Sequence[str]) -> str:
    if not ids:
        raise ValueError("expected at least one Mermaid actor id")
    if len(ids) == 1:
        return ids[0]
    return f"{ids[0]},{ids[-1]}"


def timeline_story(snapshot: dict[str, object]) -> str:
    first_replica = next(iter(dict(snapshot["replicas"])), None)
    if first_replica is None:
        return "No replica state recorded."
    first_state = dict(snapshot["replicas"])[first_replica]
    elements = ", ".join(str(element) for element in first_state["elements"]) or "∅"
    active = summarize_tag_mapping(dict(first_state["active_tags"]))
    tombstones = ", ".join(str(tag) for tag in first_state["tombstones"]) or "∅"
    if tombstones != "∅" and active != "∅":
        return (
            "Observed-remove story: a remove tombstones only the add-tags a replica has already observed, "
            f"so membership still survives via {active} while tombstones retain {tombstones}."
        )
    return f"Final membership {elements}; active tags {active}; tombstones {tombstones}."


def build_timeline_rows(snapshot: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for step, event in enumerate(snapshot["timeline"], start=1):
        op = str(event["op"])
        if op == "add":
            state = dict(event["state"])
            rows.append(
                {
                    "step": step,
                    "op": op,
                    "event": f"{event['replica']} adds {event['element']}",
                    "details": [
                        f"new tag: {event['tag']}",
                        compact_state_note(state),
                    ],
                }
            )
        elif op == "remove":
            state = dict(event["state"])
            removed_tags = ", ".join(str(tag) for tag in event["removed_tags"]) or "∅"
            rows.append(
                {
                    "step": step,
                    "op": op,
                    "event": f"{event['replica']} removes {event['element']}",
                    "details": [
                        f"observed tags removed: {removed_tags}",
                        compact_state_note(state),
                    ],
                }
            )
        else:
            direction = str(event["direction"])
            arrow = {"both": "↔", "forward": "→", "reverse": "←"}[direction]
            source_state = dict(event["source_state"])
            target_state = dict(event["target_state"])
            rows.append(
                {
                    "step": step,
                    "op": op,
                    "event": f"{event['source']} {arrow} {event['target']} sync ({direction})",
                    "details": [
                        f"{event['source']}: {compact_state_note(source_state)}",
                        f"{event['target']}: {compact_state_note(target_state)}",
                    ],
                }
            )
    return rows


def render_timeline_markdown(snapshot: dict[str, object], title: str) -> str:
    replicas = ", ".join(sorted(dict(snapshot["replicas"])))
    lines = [
        f"# OR-Set timeline — {title}",
        "",
        f"Replicas: {replicas}",
        "",
        f"Story: {timeline_story(snapshot)}",
        "",
        "| Step | Event | Details |",
        "| --- | --- | --- |",
    ]
    for row in build_timeline_rows(snapshot):
        detail_text = "<br>".join(str(detail).replace("|", "\\|") for detail in row["details"])
        event_text = str(row["event"]).replace("|", "\\|")
        lines.append(f"| {row['step']} | {event_text} | {detail_text} |")

    lines.extend(["", "## Final replica states", ""])
    for replica, state in dict(snapshot["replicas"]).items():
        lines.append(f"- `{replica}` — {summarize_state(dict(state))}")

    lines.extend([
        "",
        "## Convergence",
        "",
        f"- converged: `{str(snapshot['convergence']['converged']).lower()}`",
    ])
    return "\n".join(lines) + "\n"


def render_timeline_mermaid(snapshot: dict[str, object], title: str) -> str:
    replicas = list(sorted(dict(snapshot["replicas"])))
    actor_ids = {replica: f"R{index + 1}" for index, replica in enumerate(replicas)}
    span = mermaid_span([actor_ids[replica] for replica in replicas])
    lines = [
        "sequenceDiagram",
        "    autonumber",
    ]
    for replica in replicas:
        lines.append(f"    participant {actor_ids[replica]} as {sanitize_mermaid_text(replica)}")
    lines.append(f"    Note over {span}: {sanitize_mermaid_text(title)}")

    for event in snapshot["timeline"]:
        op = str(event["op"])
        if op == "add":
            actor = actor_ids[str(event["replica"])]
            lines.append(
                f"    {actor}->>{actor}: {sanitize_mermaid_text(f'add {event['element']} [{event['tag']}]')}"
            )
            state = compact_state_note(dict(event["state"]))
            lines.append(f"    Note over {actor}: {sanitize_mermaid_text(state)}")
        elif op == "remove":
            actor = actor_ids[str(event["replica"])]
            removed_tags = ", ".join(str(tag) for tag in event["removed_tags"]) or "∅"
            lines.append(
                f"    {actor}->>{actor}: {sanitize_mermaid_text(f'remove {event['element']}')}"
            )
            lines.append(
                f"    Note over {actor}: {sanitize_mermaid_text(f'removed {removed_tags}; {compact_state_note(dict(event['state']))}') }"
            )
        else:
            source = str(event["source"])
            target = str(event["target"])
            direction = str(event["direction"])
            if direction == "reverse":
                sender, receiver = actor_ids[target], actor_ids[source]
            else:
                sender, receiver = actor_ids[source], actor_ids[target]
            lines.append(
                f"    {sender}->>{receiver}: {sanitize_mermaid_text(f'sync {direction}')}"
            )
            source_note = compact_state_note(dict(event["source_state"]))
            target_note = compact_state_note(dict(event["target_state"]))
            lines.append(
                f"    Note over {actor_ids[source]},{actor_ids[target]}: {sanitize_mermaid_text(f'{source}: {source_note} || {target}: {target_note}') }"
            )

    lines.append(f"    Note over {span}: {sanitize_mermaid_text(timeline_story(snapshot))}")
    return "\n".join(lines) + "\n"


def wrap_svg_text(text: str, width: int = 70) -> list[str]:
    pieces = [piece for piece in wrap(text, width=width) if piece]
    return pieces or [text]


def render_timeline_svg(snapshot: dict[str, object], title: str) -> str:
    rows = build_timeline_rows(snapshot)
    width = 1080
    padding = 32
    content_width = width - (padding * 2)
    y = 108
    box_gap = 18
    row_blocks: list[dict[str, object]] = []
    colors = {
        "add": "#d1fae5",
        "remove": "#fee2e2",
        "sync": "#dbeafe",
        "final": "#ede9fe",
    }
    border_colors = {
        "add": "#10b981",
        "remove": "#ef4444",
        "sync": "#3b82f6",
        "final": "#8b5cf6",
    }

    for row in rows:
        detail_lines: list[str] = []
        for detail in row["details"]:
            detail_lines.extend(wrap_svg_text(str(detail), width=84))
        block_height = 56 + (len(detail_lines) * 20)
        row_blocks.append(
            {
                "row": row,
                "detail_lines": detail_lines,
                "y": y,
                "height": block_height,
            }
        )
        y += block_height + box_gap

    final_lines = wrap_svg_text(timeline_story(snapshot), width=84)
    for replica, state in dict(snapshot["replicas"]).items():
        final_lines.extend(wrap_svg_text(f"{replica}: {summarize_state(dict(state))}", width=84))
    final_height = 70 + (len(final_lines) * 20)
    total_height = y + final_height + 36

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}" role="img" aria-labelledby="title desc">',
        "  <defs>",
        "    <linearGradient id=\"timelineBg\" x1=\"0%\" x2=\"0%\" y1=\"0%\" y2=\"100%\">",
        "      <stop offset=\"0%\" stop-color=\"#0f172a\" />",
        "      <stop offset=\"100%\" stop-color=\"#111827\" />",
        "    </linearGradient>",
        "  </defs>",
        f"  <title id=\"title\">{escape_html(title)}</title>",
        f"  <desc id=\"desc\">{escape_html(timeline_story(snapshot))}</desc>",
        f'  <rect x="0" y="0" width="{width}" height="{total_height}" fill="url(#timelineBg)" rx="24" />',
        f'  <text x="{padding}" y="52" fill="#f8fafc" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="700">{escape_html(title)}</text>',
        f'  <text x="{padding}" y="82" fill="#cbd5e1" font-family="Arial, Helvetica, sans-serif" font-size="16">{escape_html("Observed-remove set timeline export")}</text>',
    ]

    for block in row_blocks:
        row = dict(block["row"])
        box_y = int(block["y"])
        box_height = int(block["height"])
        fill = colors[str(row["op"])]
        border = border_colors[str(row["op"])]
        svg.extend(
            [
                f'  <rect x="{padding}" y="{box_y}" width="{content_width}" height="{box_height}" rx="18" fill="{fill}" fill-opacity="0.95" stroke="{border}" stroke-width="2" />',
                f'  <circle cx="{padding + 28}" cy="{box_y + 28}" r="18" fill="{border}" />',
                f'  <text x="{padding + 28}" y="{box_y + 34}" text-anchor="middle" fill="#ffffff" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="700">{row["step"]}</text>',
                f'  <text x="{padding + 62}" y="{box_y + 30}" fill="#0f172a" font-family="Arial, Helvetica, sans-serif" font-size="20" font-weight="700">{escape_html(str(row["event"]))}</text>',
            ]
        )
        for index, line in enumerate(block["detail_lines"]):
            svg.append(
                f'  <text x="{padding + 62}" y="{box_y + 58 + (index * 20)}" fill="#1f2937" font-family="Arial, Helvetica, sans-serif" font-size="16">{escape_html(line)}</text>'
            )

    final_y = y
    svg.extend(
        [
            f'  <rect x="{padding}" y="{final_y}" width="{content_width}" height="{final_height}" rx="18" fill="{colors['final']}" fill-opacity="0.98" stroke="{border_colors['final']}" stroke-width="2" />',
            f'  <text x="{padding + 24}" y="{final_y + 32}" fill="#4c1d95" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="700">Final convergence</text>',
            f'  <text x="{padding + content_width - 24}" y="{final_y + 32}" text-anchor="end" fill="#312e81" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="700">converged={escape_html(str(snapshot['convergence']['converged']).lower())}</text>',
        ]
    )
    for index, line in enumerate(final_lines):
        svg.append(
            f'  <text x="{padding + 24}" y="{final_y + 64 + (index * 20)}" fill="#312e81" font-family="Arial, Helvetica, sans-serif" font-size="16">{escape_html(line)}</text>'
        )

    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def count_timeline_ops(snapshot: dict[str, object]) -> dict[str, int]:
    counts = {"add": 0, "remove": 0, "sync": 0}
    for event in snapshot["timeline"]:
        op = str(event["op"])
        counts[op] = counts.get(op, 0) + 1
    return counts


def build_companion_links(
    *,
    html_path: str | Path,
    markdown_path: str | Path | None = None,
    mermaid_path: str | Path | None = None,
    svg_path: str | Path | None = None,
    json_path: str | Path | None = None,
    script_path: str | Path | None = None,
    anti_entropy_markdown_path: str | Path | None = None,
    anti_entropy_html_path: str | Path | None = None,
    anti_entropy_json_path: str | Path | None = None,
    replay_html_path: str | Path | None = None,
) -> dict[str, str]:
    base_dir = Path(html_path).parent
    output_links: dict[str, str] = {}
    for label, target in (
        ("Scenario script", script_path),
        ("Markdown timeline", markdown_path),
        ("Mermaid source", mermaid_path),
        ("SVG card", svg_path),
        ("JSON snapshot", json_path),
        ("Anti-entropy Markdown", anti_entropy_markdown_path),
        ("Anti-entropy HTML", anti_entropy_html_path),
        ("Anti-entropy JSON", anti_entropy_json_path),
        ("Replay HTML", replay_html_path),
    ):
        if target is None:
            continue
        relative = os.path.relpath(Path(target), base_dir)
        output_links[label] = Path(relative).as_posix()
    return output_links


def render_timeline_html(
    snapshot: dict[str, object],
    title: str,
    *,
    companion_links: dict[str, str] | None = None,
) -> str:
    replica_states = {replica: dict(state) for replica, state in dict(snapshot["replicas"]).items()}
    replicas = sorted(replica_states)
    replica_count = len(replicas)
    step_count = len(snapshot["timeline"])
    counts = count_timeline_ops(snapshot)
    element_views = {tuple(state["elements"]) for state in replica_states.values()}
    tombstone_views = {tuple(state["tombstones"]) for state in replica_states.values()}
    if not replica_states:
        final_elements = "∅"
        tombstones = "∅"
    else:
        final_elements = ", ".join(next(iter(element_views))) if len(element_views) == 1 else "mixed by replica"
        tombstones = ", ".join(next(iter(tombstone_views))) if len(tombstone_views) == 1 else "mixed by replica"
        if not final_elements:
            final_elements = "∅"
        if not tombstones:
            tombstones = "∅"
    inline_svg = render_timeline_svg(snapshot, title)
    rows = build_timeline_rows(snapshot)
    final_states_html = "".join(
        f'<li><strong><code>{escape_html(replica)}</code></strong><span>{escape_html(summarize_state(state))}</span></li>'
        for replica, state in replica_states.items()
    )
    timeline_rows_html = "".join(
        "<tr>"
        f"<td>{row['step']}</td>"
        f"<td>{escape_html(str(row['event']))}</td>"
        f"<td>{''.join(f'<div>{escape_html(str(detail))}</div>' for detail in row['details'])}</td>"
        "</tr>"
        for row in rows
    )
    companion_links_html = "".join(
        f'<li><a href="{escape_html(path)}">{escape_html(label)}</a></li>'
        for label, path in (companion_links or {}).items()
    )
    if not companion_links_html:
        companion_links_html = "<li>This HTML page is self-contained, but companion file links appear when you export Markdown, Mermaid, SVG, JSON, or anti-entropy outputs alongside it.</li>"

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OR-Set artifact gallery — {escape_html(title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --panel-alt: #eef2ff;
        --border: #d7dde8;
        --text: #0f172a;
        --muted: #475569;
        --accent: #2563eb;
        --ok-bg: #dcfce7;
        --ok-text: #166534;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1380px; margin: 0 auto; padding: 32px 20px 64px; }}
      a {{ color: var(--accent); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p {{ color: var(--muted); max-width: 980px; }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0 0; padding: 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; }}
      .summary-grid strong {{ display: block; font-size: 1.35rem; margin-bottom: 6px; }}
      .layout {{ display: grid; gap: 24px; grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.9fr); align-items: start; }}
      .panel {{ padding: 22px; }}
      .panel h2, .panel h3 {{ margin-top: 0; }}
      .artifact-links {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      .artifact-links li + li, .replica-list li + li {{ margin-top: 10px; }}
      .preview {{ margin: 0; overflow-x: auto; }}
      .preview svg {{ width: 100%; height: auto; min-width: 720px; display: block; border-radius: 20px; }}
      .replica-list {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      .replica-list strong {{ color: var(--text); display: block; margin-bottom: 4px; }}
      .replica-list span {{ display: block; line-height: 1.5; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      .story {{ padding: 14px 16px; border-radius: 18px; background: #eff6ff; border: 1px solid #bfdbfe; color: #1e3a8a; }}
      .status-ok {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: var(--ok-bg); color: var(--ok-text); font-weight: 700; }}
      @media (max-width: 1020px) {{
        .layout {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>OR-Set artifact gallery</h1>
        <p>This page packages the screenshot-ready OR-Set timeline card with the exact companion files that explain the same run in Markdown, Mermaid, SVG, and JSON. It is meant to make the observed-remove story quick to inspect in a browser while still leaving the raw machine-readable state one click away.</p>
        <p class="story">{escape_html(timeline_story(snapshot))}</p>
        <ul class="summary-grid">
          <li><strong>{replica_count}</strong> replicas ({escape_html(', '.join(replicas) or 'none')})</li>
          <li><strong>{step_count}</strong> timeline steps</li>
          <li><strong>{counts['add']}/{counts['remove']}/{counts['sync']}</strong> add/remove/sync ops</li>
          <li><strong>{escape_html(final_elements)}</strong> final membership</li>
          <li><strong>{escape_html(tombstones)}</strong> final tombstones</li>
          <li><strong><span class="status-ok">converged = {escape_html(str(snapshot['convergence']['converged']).lower())}</span></strong> full replica-state equality</li>
        </ul>
      </section>
      <section class="layout">
        <article class="panel">
          <h2>{escape_html(title)}</h2>
          <figure class="preview">
{inline_svg}
          </figure>
        </article>
        <aside class="panel">
          <h2>Companion artifacts</h2>
          <ul class="artifact-links">{companion_links_html}</ul>
          <h3>Final replica states</h3>
          <ul class="replica-list">{final_states_html}</ul>
        </aside>
      </section>
      <section class="panel" style="margin-top: 24px;">
        <h2>Timeline steps</h2>
        <table>
          <thead>
            <tr><th>Step</th><th>Event</th><th>Details</th></tr>
          </thead>
          <tbody>{timeline_rows_html}</tbody>
        </table>
      </section>
    </main>
  </body>
</html>
'''


def build_replay_frames(snapshot: dict[str, object]) -> list[dict[str, object]]:
    replicas = sorted(dict(snapshot["replicas"]))
    current_states = {replica: clone_state_view() for replica in replicas}
    timeline_rows = build_timeline_rows(snapshot)
    sync_rows_by_step = {
        int(row["step"]): row for row in build_anti_entropy_report(snapshot)["sync_rows"]
    }

    def converged(states: dict[str, dict[str, object]]) -> bool:
        signatures = {json.dumps(state, sort_keys=True) for state in states.values()}
        return len(signatures) <= 1

    frames = [
        {
            "step": 0,
            "op": "initial",
            "sync_checkpoint": None,
            "label": "Cluster starts empty",
            "details": [
                "No operations have run yet.",
                "Use the slider, sync-jump buttons, or play button to scrub through adds, removes, and sync steps.",
            ],
            "focus_replicas": [],
            "replicas": {replica: clone_state_view(state) for replica, state in current_states.items()},
            "converged": converged(current_states),
            "anti_entropy": {
                "summary": "No anti-entropy transfer yet — this is the pre-script baseline.",
                "transfers": [],
            },
        }
    ]

    sync_checkpoint_number = 0
    for step, event in enumerate(snapshot["timeline"], start=1):
        op = str(event["op"])
        focus_replicas: list[str]
        sync_checkpoint: int | None = None
        if op in {"add", "remove"}:
            replica = str(event["replica"])
            current_states[replica] = clone_state_view(dict(event["state"]))
            focus_replicas = [replica]
            anti_entropy = {
                "summary": "Local mutation only — no anti-entropy transfer happens until a sync step.",
                "transfers": [],
            }
        else:
            sync_checkpoint_number += 1
            sync_checkpoint = sync_checkpoint_number
            source = str(event["source"])
            target = str(event["target"])
            current_states[source] = clone_state_view(dict(event["source_state"]))
            current_states[target] = clone_state_view(dict(event["target_state"]))
            focus_replicas = [source, target]
            row = sync_rows_by_step.get(step)
            if row:
                transfers = [
                    {
                        "from": str(transfer["from"]),
                        "to": str(transfer["to"]),
                        "digest_pair": f"{str(transfer['from_digest'])[:12]}… vs {str(transfer['to_digest'])[:12]}…",
                        "full_bytes": int(transfer["full_state"]["payload_bytes"]),
                        "delta_bytes": int(transfer["delta"]["payload_bytes"]),
                        "saved": int(transfer["bytes_saved_vs_full"]),
                        "delta_payload": summarize_delta_payload(dict(transfer["delta_payload"])),
                    }
                    for transfer in row["transfers"]
                ]
                anti_entropy = {
                    "summary": (
                        f"{row['transfer_count']} directional transfer(s), {row['delta_sync_bytes']} delta byte(s), "
                        f"saving {row['bytes_saved_vs_full']} vs full-state sync."
                    ),
                    "transfers": transfers,
                }
            else:
                anti_entropy = {
                    "summary": "Sync step recorded without anti-entropy metadata.",
                    "transfers": [],
                }
        frame = {
            "step": step,
            "op": op,
            "sync_checkpoint": sync_checkpoint,
            "label": str(timeline_rows[step - 1]["event"]),
            "details": [str(detail) for detail in timeline_rows[step - 1]["details"]],
            "focus_replicas": focus_replicas,
            "replicas": {replica: clone_state_view(state) for replica, state in current_states.items()},
            "converged": converged(current_states),
            "anti_entropy": anti_entropy,
        }
        frames.append(frame)
    return frames


def render_replay_html(
    snapshot: dict[str, object],
    title: str,
    *,
    companion_links: dict[str, str] | None = None,
) -> str:
    replicas = sorted(dict(snapshot["replicas"]))
    counts = count_timeline_ops(snapshot)
    frames = build_replay_frames(snapshot)
    frame_count = max(len(frames) - 1, 0)
    final_converged = bool(snapshot["convergence"]["converged"])
    companion_links_html = "".join(
        f'<li><a href="{escape_html(path)}">{escape_html(label)}</a></li>'
        for label, path in (companion_links or {}).items()
    )
    if not companion_links_html:
        companion_links_html = "<li>This replay page is self-contained, but companion file links appear when you export the timeline, anti-entropy, or comparison artifacts alongside it.</li>"
    frames_json = json.dumps(frames, sort_keys=True).replace("</", "<\\/")
    title_json = json.dumps(title).replace("</", "<\\/")
    story_json = json.dumps(timeline_story(snapshot)).replace("</", "<\\/")

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OR-Set replay — {escape_html(title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --panel-alt: #eef2ff;
        --border: #d7dde8;
        --text: #0f172a;
        --muted: #475569;
        --accent: #2563eb;
        --accent-soft: #dbeafe;
        --warn: #92400e;
        --warn-bg: #ffedd5;
        --ok: #166534;
        --ok-bg: #dcfce7;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1420px; margin: 0 auto; padding: 32px 20px 64px; }}
      a {{ color: var(--accent); }}
      button, input, select {{ font: inherit; }}
      button {{ cursor: pointer; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p {{ color: var(--muted); max-width: 980px; }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0 0; padding: 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; }}
      .summary-grid strong {{ display: block; font-size: 1.35rem; margin-bottom: 6px; }}
      .layout {{ display: grid; gap: 24px; grid-template-columns: minmax(0, 1.25fr) minmax(320px, 0.9fr); align-items: start; }}
      .panel {{ padding: 22px; }}
      .panel h2, .panel h3 {{ margin-top: 0; }}
      .controls {{ display: grid; gap: 16px; }}
      .step-meta {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 12px; }}
      .status-pill {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; font-weight: 700; }}
      .status-pill.ok {{ background: var(--ok-bg); color: var(--ok); }}
      .status-pill.warn {{ background: var(--warn-bg); color: var(--warn); }}
      .button-row {{ display: flex; flex-wrap: wrap; gap: 10px; }}
      .button-row button {{ border: 1px solid #bfdbfe; background: var(--accent-soft); color: var(--accent); border-radius: 999px; padding: 10px 16px; font-weight: 700; }}
      .button-row button:disabled {{ opacity: 0.55; cursor: default; }}
      .slider-grid {{ display: grid; gap: 16px; grid-template-columns: minmax(0, 1fr) minmax(220px, 280px); align-items: end; }}
      .slider-wrap {{ display: grid; gap: 8px; }}
      .slider-wrap label, .inline-control label {{ font-weight: 700; }}
      .inline-control {{ display: grid; gap: 8px; }}
      .inline-control select {{ border: 1px solid var(--border); border-radius: 14px; padding: 10px 12px; background: var(--panel); color: var(--text); }}
      .sync-jump-note {{ margin-top: 8px; color: var(--muted); }}
      .link-list-note {{ margin: 0 0 12px; color: var(--muted); }}
      .action-note {{ margin: 12px 0 0; color: var(--muted); }}
      .action-note.ok {{ color: var(--ok); }}
      .action-note.warn {{ color: var(--warn); }}
      input[type=range] {{ width: 100%; }}
      .detail-list, .artifact-links, .transfer-list, .checkpoint-list {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      .detail-list li + li, .artifact-links li + li, .transfer-list li + li, .checkpoint-list li + li {{ margin-top: 8px; }}
      .replica-grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }}
      .replica-card {{ border: 1px solid var(--border); border-radius: 20px; padding: 16px; background: #f8fafc; }}
      .replica-card.focus {{ border-color: #60a5fa; box-shadow: inset 0 0 0 1px #bfdbfe; background: #eff6ff; }}
      .replica-card h3 {{ margin: 0 0 10px; display: flex; justify-content: space-between; gap: 12px; align-items: center; }}
      .replica-card dl {{ margin: 0; display: grid; gap: 10px; }}
      .replica-card dt {{ font-size: 0.85rem; font-weight: 700; color: var(--muted); }}
      .replica-card dd {{ margin: 3px 0 0; font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; white-space: pre-wrap; word-break: break-word; }}
      .anti-grid {{ display: grid; gap: 18px; grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr); align-items: start; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      .sr-only {{ position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }}
      .note {{ padding: 14px 16px; border-radius: 18px; background: #eff6ff; border: 1px solid #bfdbfe; color: #1e3a8a; }}
      @media (max-width: 1080px) {{
        .layout, .anti-grid, .slider-grid {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>OR-Set replay / animation</h1>
        <p>This replay page turns the OR-Set timeline into a stepper you can scrub in a browser. It keeps the anti-entropy notes beside the replica states so a reviewer can see both the semantic change and the payload-cost story on the same screen, now with sync-jump shortcuts, adjustable playback speed, and hash-based deep links that can open directly on a chosen replay or sync checkpoint.</p>
        <p class="note">{escape_html(timeline_story(snapshot))}</p>
        <ul class="summary-grid">
          <li><strong>{len(replicas)}</strong> replicas ({escape_html(', '.join(replicas) or 'none')})</li>
          <li><strong>{len(snapshot['timeline'])}</strong> timeline steps</li>
          <li><strong>{counts['add']}/{counts['remove']}/{counts['sync']}</strong> add/remove/sync ops</li>
          <li><strong>{frame_count}</strong> replayable steps</li>
          <li><strong>{'true' if final_converged else 'false'}</strong> final convergence</li>
          <li><strong>{escape_html(title)}</strong> scenario</li>
        </ul>
      </section>
      <section class="layout">
        <article class="panel controls">
          <div class="step-meta">
            <div>
              <h2 id="replay-step-heading" style="margin-bottom: 6px;">Initial state</h2>
              <div id="replay-step-label" class="note">Cluster starts empty.</div>
            </div>
            <div id="replay-status" class="status-pill ok">state converged</div>
          </div>
          <div class="button-row">
            <button type="button" id="replay-prev">← Prev</button>
            <button type="button" id="replay-prev-sync">↺ Prev sync</button>
            <button type="button" id="replay-play" aria-pressed="false">▶ Play</button>
            <button type="button" id="replay-next-sync">Next sync ↻</button>
            <button type="button" id="replay-next">Next →</button>
          </div>
          <div class="slider-grid">
            <div class="slider-wrap">
              <label for="replay-range">Replay step</label>
              <input type="range" id="replay-range" min="0" max="{frame_count}" step="1" value="0" />
              <div id="replay-step-counter" style="color: var(--muted);">Step 0 of {frame_count}</div>
              <div id="replay-sync-note" class="sync-jump-note">Jump-to-sync buttons stay disabled until the script reaches a sync step.</div>
            </div>
            <div class="inline-control">
              <label for="replay-speed">Playback speed</label>
              <select id="replay-speed">
                <option value="2200">Slow walkthrough · 0.75×</option>
                <option value="1600" selected>Normal classroom pace · 1×</option>
                <option value="950">Fast recap · 1.7×</option>
                <option value="550">Sprint to next sync · 2.9×</option>
              </select>
            </div>
          </div>
          <div>
            <h3>What changed on this step?</h3>
            <ul id="replay-details" class="detail-list"></ul>
          </div>
          <div>
            <h3>Deep links</h3>
            <p id="replay-link-note" class="link-list-note">Open this artifact with a hash such as <code>#step-3</code> or <code>#sync-2</code> to jump directly to a chosen checkpoint.</p>
            <ul id="replay-link-list" class="artifact-links"></ul>
          </div>
          <div>
            <h3>Checkpoint actions</h3>
            <div class="button-row">
              <button type="button" id="replay-copy-exact-link">Copy exact link</button>
              <button type="button" id="replay-copy-sync-link">Copy sync link</button>
              <button type="button" id="replay-download-svg">Download SVG card</button>
            </div>
            <p id="replay-action-note" class="action-note">Copy the exact frame link on any step, use the stable sync link on sync checkpoints, or download the current checkpoint as a standalone SVG card.</p>
          </div>
          <div>
            <h3>Sync checkpoint links</h3>
            <ul id="replay-sync-links" class="checkpoint-list"></ul>
          </div>
          <div>
            <h3>Companion artifacts</h3>
            <ul class="artifact-links">{companion_links_html}</ul>
          </div>
        </article>
        <aside class="panel">
          <h2>Replica states after this step</h2>
          <div id="replica-grid" class="replica-grid"></div>
        </aside>
      </section>
      <section class="panel" style="margin-top: 24px;">
        <h2>Anti-entropy transfer view</h2>
        <div class="anti-grid">
          <div>
            <p id="anti-summary" class="note">No anti-entropy transfer yet — this is the pre-script baseline.</p>
            <ul id="transfer-list" class="transfer-list"></ul>
          </div>
          <div>
            <table>
              <thead>
                <tr><th>Transfer</th><th>Digests before</th><th>Full bytes</th><th>Delta bytes</th><th>Saved</th><th>Delta payload</th></tr>
              </thead>
              <tbody id="transfer-table-body">
                <tr><td colspan="6">No sync transfer on this step.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
      <p id="replay-announce" class="sr-only" aria-live="polite" aria-atomic="true"></p>
    </main>
    <script>
      const frames = {frames_json};
      const scenarioTitle = {title_json};
      const scenarioStory = {story_json};
      const stepHeading = document.getElementById('replay-step-heading');
      const stepLabel = document.getElementById('replay-step-label');
      const stepCounter = document.getElementById('replay-step-counter');
      const statusPill = document.getElementById('replay-status');
      const detailList = document.getElementById('replay-details');
      const linkNote = document.getElementById('replay-link-note');
      const linkList = document.getElementById('replay-link-list');
      const syncLinkList = document.getElementById('replay-sync-links');
      const replicaGrid = document.getElementById('replica-grid');
      const antiSummary = document.getElementById('anti-summary');
      const transferList = document.getElementById('transfer-list');
      const transferTableBody = document.getElementById('transfer-table-body');
      const range = document.getElementById('replay-range');
      const prevButton = document.getElementById('replay-prev');
      const prevSyncButton = document.getElementById('replay-prev-sync');
      const playButton = document.getElementById('replay-play');
      const nextSyncButton = document.getElementById('replay-next-sync');
      const nextButton = document.getElementById('replay-next');
      const copyExactButton = document.getElementById('replay-copy-exact-link');
      const copySyncButton = document.getElementById('replay-copy-sync-link');
      const downloadSvgButton = document.getElementById('replay-download-svg');
      const speedSelect = document.getElementById('replay-speed');
      const syncNote = document.getElementById('replay-sync-note');
      const actionNote = document.getElementById('replay-action-note');
      const announce = document.getElementById('replay-announce');
      const syncFrames = frames.filter((frame) => frame.sync_checkpoint !== null);
      const syncFrameIndexes = syncFrames.map((frame) => frame.step);

      let frameIndex = 0;
      let playTimer = null;

      function stopPlayback() {{
        if (playTimer !== null) {{
          window.clearTimeout(playTimer);
          playTimer = null;
        }}
        playButton.textContent = '▶ Play';
        playButton.setAttribute('aria-pressed', 'false');
      }}

      function playbackDelayMs() {{
        return Number(speedSelect.value || 1600);
      }}

      function schedulePlaybackTick() {{
        if (frameIndex >= frames.length - 1) {{
          stopPlayback();
          return;
        }}
        playTimer = window.setTimeout(() => {{
          renderFrame(frameIndex + 1);
          schedulePlaybackTick();
        }}, playbackDelayMs());
      }}

      function startPlayback() {{
        stopPlayback();
        if (frameIndex >= frames.length - 1) {{
          renderFrame(0);
        }}
        playButton.textContent = '❚❚ Pause';
        playButton.setAttribute('aria-pressed', 'true');
        schedulePlaybackTick();
      }}

      function findNextSyncIndex(fromIndex) {{
        return syncFrameIndexes.find((syncIndex) => syncIndex > fromIndex) ?? null;
      }}

      function findPreviousSyncIndex(fromIndex) {{
        for (let index = syncFrameIndexes.length - 1; index >= 0; index -= 1) {{
          if (syncFrameIndexes[index] < fromIndex) {{
            return syncFrameIndexes[index];
          }}
        }}
        return null;
      }}

      function hashForFrame(frame) {{
        if (frame.sync_checkpoint !== null) {{
          return `sync-${{frame.sync_checkpoint}}`;
        }}
        return `step-${{frame.step}}`;
      }}

      function absoluteUrlForHash(hash) {{
        const url = new URL(window.location.href);
        url.hash = hash;
        return url.toString();
      }}

      function indexFromHash(hash) {{
        const value = String(hash || '').replace(/^#/, '').trim().toLowerCase();
        if (!value) {{
          return 0;
        }}
        if (/^step-\\d+$/.test(value)) {{
          const step = Number(value.slice(5));
          return Number.isFinite(step) ? Math.max(0, Math.min(frames.length - 1, step)) : 0;
        }}
        if (/^sync-\\d+$/.test(value)) {{
          const checkpoint = Number(value.slice(5));
          const match = syncFrames.find((frame) => frame.sync_checkpoint === checkpoint);
          return match ? match.step : 0;
        }}
        return 0;
      }}

      function updateUrlHash(frame) {{
        const hash = `#${{hashForFrame(frame)}}`;
        if (window.location.hash === hash) {{
          return;
        }}
        if (window.history && typeof window.history.replaceState === 'function') {{
          const url = new URL(window.location.href);
          url.hash = hash;
          window.history.replaceState(null, '', url);
          return;
        }}
        window.location.hash = hash;
      }}

      function renderDeepLinks(frame) {{
        const currentHash = hashForFrame(frame);
        const exactStepHash = `step-${{frame.step}}`;
        const items = [
          `<li><strong>Exact frame:</strong> <a href="#${{exactStepHash}}"><code>${{absoluteUrlForHash(exactStepHash)}}</code></a></li>`,
        ];
        if (frame.sync_checkpoint !== null) {{
          const syncHash = `sync-${{frame.sync_checkpoint}}`;
          items.push(`<li><strong>Stable sync checkpoint:</strong> <a href="#${{syncHash}}"><code>${{absoluteUrlForHash(syncHash)}}</code></a></li>`);
        }} else if (syncFrames.length) {{
          const nextSync = findNextSyncIndex(frame.step);
          if (nextSync !== null) {{
            const nextFrame = frames[nextSync];
            items.push(`<li><strong>Nearest forward sync:</strong> <a href="#sync-${{nextFrame.sync_checkpoint}}"><code>${{absoluteUrlForHash(`sync-${{nextFrame.sync_checkpoint}}`)}}</code></a></li>`);
          }}
        }}
        linkList.innerHTML = items.join('');
        linkNote.innerHTML = `Open this artifact with <code>#step-N</code> or <code>#sync-N</code>. The current canonical hash is <code>#${{currentHash}}</code>.`;
        syncLinkList.innerHTML = syncFrames.length
          ? syncFrames.map((syncFrame) => {{
              const active = syncFrame.step === frame.step ? ' <strong>(current)</strong>' : '';
              return `<li><a href="#sync-${{syncFrame.sync_checkpoint}}">Sync ${{syncFrame.sync_checkpoint}} · step ${{syncFrame.step}}</a> — ${{syncFrame.label}}${{active}}</li>`;
            }}).join('')
          : '<li>No sync checkpoints available in this scenario.</li>';
      }}

      function renderReplicaCards(frame) {{
        replicaGrid.innerHTML = Object.entries(frame.replicas).map(([replica, state]) => {{
          const focused = frame.focus_replicas.includes(replica) ? ' focus' : '';
          const rows = [
            ['Elements', (state.elements || []).join(', ') || '∅'],
            ['Active tags', Object.entries(state.active_tags || {{}}).map(([element, tags]) => `${{element}}=${{tags.join(', ') || '∅'}}`).join('; ') || '∅'],
            ['Observed tags', Object.entries(state.observed_tags || {{}}).map(([element, tags]) => `${{element}}=${{tags.join(', ') || '∅'}}`).join('; ') || '∅'],
            ['Tombstones', (state.tombstones || []).join(', ') || '∅'],
            ['Counters', Object.entries(state.counters || {{}}).map(([name, count]) => `${{name}}:${{count}}`).join(', ') || '∅'],
          ];
          const body = rows.map(([label, value]) => `<div><dt>${{label}}</dt><dd>${{value}}</dd></div>`).join('');
          return `<section class="replica-card${{focused}}"><h3><span><code>${{replica}}</code></span><span>${{focused ? 'focus' : 'stable'}}</span></h3><dl>${{body}}</dl></section>`;
        }}).join('');
      }}

      function escapeSvgText(value) {{
        return String(value ?? '')
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;');
      }}

      function wrapSvgText(text, width = 88) {{
        const words = String(text ?? '').split(/\\s+/).filter(Boolean);
        if (!words.length) {{
          return [''];
        }}
        const lines = [];
        let current = words[0];
        for (const word of words.slice(1)) {{
          if (`${{current}} ${{word}}`.length <= width) {{
            current = `${{current}} ${{word}}`;
          }} else {{
            lines.push(current);
            current = word;
          }}
        }}
        lines.push(current);
        return lines;
      }}

      function summarizeTagMap(mapping) {{
        const entries = Object.entries(mapping || {{}});
        return entries.length
          ? entries.map(([element, tags]) => `${{element}}=${{(tags || []).join(', ') || '∅'}}`).join('; ')
          : '∅';
      }}

      function summarizeCounters(counters) {{
        const entries = Object.entries(counters || {{}});
        return entries.length ? entries.map(([replica, counter]) => `${{replica}}:${{counter}}`).join(', ') : '∅';
      }}

      function summarizeReplicaState(replica, state) {{
        return `${{replica}}: elements=${{(state.elements || []).join(', ') || '∅'}} | active=${{summarizeTagMap(state.active_tags)}} | observed=${{summarizeTagMap(state.observed_tags)}} | tombstones=${{(state.tombstones || []).join(', ') || '∅'}} | counters=${{summarizeCounters(state.counters)}}`;
      }}

      function pushWrappedLines(lines, text, width = 88) {{
        for (const line of wrapSvgText(text, width)) {{
          lines.push(line);
        }}
      }}

      function slugifyFilePart(value) {{
        return String(value || 'crdt-orset-checkpoint')
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-+|-+$/g, '') || 'crdt-orset-checkpoint';
      }}

      function fileNameForFrame(frame) {{
        const suffix = frame.sync_checkpoint !== null ? `sync-${{frame.sync_checkpoint}}` : `step-${{frame.step}}`;
        return `${{slugifyFilePart(scenarioTitle)}}-${{suffix}}.svg`;
      }}

      function setActionNote(message, kind = '') {{
        actionNote.textContent = message;
        actionNote.className = `action-note${{kind ? ` ${{kind}}` : ''}}`;
      }}

      async function copyText(text) {{
        if (window.isSecureContext && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {{
          await navigator.clipboard.writeText(text);
          return;
        }}
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.setAttribute('readonly', 'readonly');
        textArea.style.position = 'fixed';
        textArea.style.top = '-1000px';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        const succeeded = document.execCommand('copy');
        document.body.removeChild(textArea);
        if (!succeeded) {{
          throw new Error('Copy command was rejected by the browser.');
        }}
      }}

      function downloadTextFile(text, fileName, mimeType) {{
        const blob = new Blob([text], {{ type: mimeType }});
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }}

      function buildCheckpointSvg(frame) {{
        const width = 1280;
        const padding = 40;
        const contentWidth = width - (padding * 2);
        const lineHeight = 24;
        const sections = [];

        const eventLines = [];
        pushWrappedLines(eventLines, frame.label, 92);
        for (const detail of frame.details || []) {{
          pushWrappedLines(eventLines, `• ${{detail}}`, 92);
        }}

        const replicaLines = Object.entries(frame.replicas || {{}}).flatMap(([replica, state]) => wrapSvgText(summarizeReplicaState(replica, state), 92));
        const transferLines = [];
        pushWrappedLines(transferLines, (frame.anti_entropy && frame.anti_entropy.summary) || 'No anti-entropy transfer on this step.', 92);
        for (const transfer of (frame.anti_entropy && frame.anti_entropy.transfers) || []) {{
          pushWrappedLines(transferLines, `${{transfer.from}} → ${{transfer.to}} · delta ${{transfer.delta_bytes}} byte(s) · saved ${{transfer.saved}} · ${{transfer.delta_payload}}`, 92);
        }}
        const linkLines = [
          `Exact link: ${{absoluteUrlForHash(`step-${{frame.step}}`)}}`,
          frame.sync_checkpoint !== null
            ? `Stable sync link: ${{absoluteUrlForHash(`sync-${{frame.sync_checkpoint}}`)}}`
            : 'Stable sync link: unavailable on non-sync frames (use the exact frame URL).',
        ];

        sections.push({{
          title: `Step ${{frame.step}} summary`,
          fill: '#dbeafe',
          border: '#3b82f6',
          titleColor: '#1d4ed8',
          textColor: '#0f172a',
          lines: eventLines,
        }});
        sections.push({{
          title: 'Replica states',
          fill: '#ecfeff',
          border: '#0891b2',
          titleColor: '#0f766e',
          textColor: '#0f172a',
          lines: replicaLines.length ? replicaLines : ['No replica state captured.'],
        }});
        sections.push({{
          title: 'Anti-entropy view',
          fill: '#ede9fe',
          border: '#7c3aed',
          titleColor: '#5b21b6',
          textColor: '#312e81',
          lines: transferLines,
        }});
        sections.push({{
          title: 'Deep links',
          fill: '#dcfce7',
          border: '#16a34a',
          titleColor: '#166534',
          textColor: '#14532d',
          lines: linkLines.flatMap((line) => wrapSvgText(line, 92)),
        }});

        let y = 176;
        const sectionGap = 20;
        const sectionBoxes = sections.map((section) => {{
          const height = 58 + (section.lines.length * lineHeight);
          const box = {{ ...section, y, height }};
          y += height + sectionGap;
          return box;
        }});
        const totalHeight = y + 36;
        const currentHash = frame.sync_checkpoint !== null ? `sync-${{frame.sync_checkpoint}}` : `step-${{frame.step}}`;
        const focusSummary = (frame.focus_replicas || []).length ? `focus replicas: ${{frame.focus_replicas.join(', ')}}` : 'focus replicas: none';
        const checkpointBadge = frame.sync_checkpoint !== null
          ? `sync checkpoint #${{frame.sync_checkpoint}}`
          : 'exact frame checkpoint';
        const svg = [
          `<svg xmlns="http://www.w3.org/2000/svg" width="${{width}}" height="${{totalHeight}}" viewBox="0 0 ${{width}} ${{totalHeight}}" role="img" aria-labelledby="title desc">`,
          '<defs>',
          '<linearGradient id="checkpointBg" x1="0%" x2="0%" y1="0%" y2="100%">',
          '<stop offset="0%" stop-color="#0f172a" />',
          '<stop offset="100%" stop-color="#111827" />',
          '</linearGradient>',
          '</defs>',
          `<title id="title">${{escapeSvgText(`OR-Set replay checkpoint — ${{scenarioTitle}} — step ${{frame.step}}`)}}</title>`,
          `<desc id="desc">${{escapeSvgText(`${{scenarioStory}} Current checkpoint hash: #${{currentHash}}.`)}}</desc>`,
          `<rect x="0" y="0" width="${{width}}" height="${{totalHeight}}" rx="28" fill="url(#checkpointBg)" />`,
          `<text x="${{padding}}" y="58" fill="#f8fafc" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="700">${{escapeSvgText('OR-Set replay checkpoint export')}}</text>`,
          `<text x="${{padding}}" y="92" fill="#cbd5e1" font-family="Arial, Helvetica, sans-serif" font-size="20">${{escapeSvgText(scenarioTitle)}}</text>`,
          `<text x="${{padding}}" y="122" fill="#bfdbfe" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="700">${{escapeSvgText(`Step ${{frame.step}} · ${{checkpointBadge}} · ${{frame.converged ? 'converged' : 'diverged'}}`)}}</text>`,
          `<text x="${{padding}}" y="148" fill="#94a3b8" font-family="Arial, Helvetica, sans-serif" font-size="16">${{escapeSvgText(`${{focusSummary}} · hash #${{currentHash}}`)}}</text>`,
        ];

        for (const section of sectionBoxes) {{
          svg.push(`<rect x="${{padding}}" y="${{section.y}}" width="${{contentWidth}}" height="${{section.height}}" rx="22" fill="${{section.fill}}" fill-opacity="0.97" stroke="${{section.border}}" stroke-width="2" />`);
          svg.push(`<text x="${{padding + 24}}" y="${{section.y + 34}}" fill="${{section.titleColor}}" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="700">${{escapeSvgText(section.title)}}</text>`);
          section.lines.forEach((line, index) => {{
            svg.push(`<text x="${{padding + 24}}" y="${{section.y + 68 + (index * lineHeight)}}" fill="${{section.textColor}}" font-family="Arial, Helvetica, sans-serif" font-size="18">${{escapeSvgText(line)}}</text>`);
          }});
        }}
        svg.push('</svg>');
        return svg.join('\\n') + '\\n';
      }}

      function renderTransfers(frame) {{
        const transfers = (frame.anti_entropy && frame.anti_entropy.transfers) || [];
        antiSummary.textContent = frame.anti_entropy ? frame.anti_entropy.summary : 'No anti-entropy transfer on this step.';
        transferList.innerHTML = transfers.length
          ? transfers.map((transfer) => `<li><strong>${{transfer.from}} → ${{transfer.to}}</strong> — ${{transfer.delta_bytes}} delta bytes, saved ${{transfer.saved}} byte(s).</li>`).join('')
          : '<li>No sync transfer on this step.</li>';
        transferTableBody.innerHTML = transfers.length
          ? transfers.map((transfer) => `<tr><td><code>${{transfer.from}} → ${{transfer.to}}</code></td><td><code>${{transfer.digest_pair}}</code></td><td>${{transfer.full_bytes}}</td><td>${{transfer.delta_bytes}}</td><td>${{transfer.saved}}</td><td>${{transfer.delta_payload}}</td></tr>`).join('')
          : '<tr><td colspan="6">No sync transfer on this step.</td></tr>';
      }}

      function renderFrame(index, options = {{}}) {{
        frameIndex = index;
        const frame = frames[index];
        const updateHash = options.updateHash !== false;
        range.value = String(index);
        const heading = index === 0 ? 'Initial state' : `Step ${{frame.step}}`;
        const previousSync = findPreviousSyncIndex(index);
        const nextSync = findNextSyncIndex(index);
        const syncPosition = syncFrameIndexes.indexOf(index);
        stepHeading.textContent = heading;
        stepLabel.textContent = frame.label;
        stepCounter.textContent = `Step ${{index}} of ${{frames.length - 1}}`;
        statusPill.textContent = frame.converged ? 'state converged' : 'state diverged';
        statusPill.className = `status-pill ${{frame.converged ? 'ok' : 'warn'}}`;
        detailList.innerHTML = frame.details.map((detail) => `<li>${{detail}}</li>`).join('');
        renderDeepLinks(frame);
        renderReplicaCards(frame);
        renderTransfers(frame);
        prevButton.disabled = index === 0;
        nextButton.disabled = index === frames.length - 1;
        prevSyncButton.disabled = previousSync === null;
        nextSyncButton.disabled = nextSync === null;
        copySyncButton.disabled = frame.sync_checkpoint === null;
        copySyncButton.textContent = frame.sync_checkpoint === null ? 'Copy sync link' : `Copy sync #${{frame.sync_checkpoint}} link`;
        setActionNote(
          frame.sync_checkpoint === null
            ? 'Copy the exact frame link on any step, or download this checkpoint as an SVG card. Stable sync links activate only on sync steps.'
            : `Copy the exact frame link, share stable sync #${{frame.sync_checkpoint}}, or download this checkpoint as an SVG card.`,
        );
        if (!syncFrameIndexes.length) {{
          syncNote.textContent = 'This scenario has no sync steps yet, so jump-to-sync stays disabled.';
        }} else if (frame.op === 'sync' && syncPosition >= 0) {{
          syncNote.textContent = `On sync step ${{index}} (checkpoint #${{frame.sync_checkpoint}}, ${{syncPosition + 1}} of ${{syncFrameIndexes.length}} sync checkpoints).`;
        }} else if (nextSync !== null) {{
          const nextFrame = frames[nextSync];
          syncNote.textContent = `Next sync checkpoint: step ${{nextSync}} (#${{nextFrame.sync_checkpoint}}). Previous sync: ${{previousSync === null ? 'none yet' : `step ${{previousSync}}`}}.`;
        }} else {{
          syncNote.textContent = previousSync === null
            ? 'No sync checkpoints appear in this scenario yet.'
            : `No later sync steps remain. Last sync checkpoint: step ${{previousSync}}.`;
        }}
        announce.textContent = `${{heading}} — ${{frame.label}}`;
        if (updateHash) {{
          updateUrlHash(frame);
        }}
      }}

      prevButton.addEventListener('click', () => {{
        stopPlayback();
        renderFrame(Math.max(0, frameIndex - 1));
      }});
      prevSyncButton.addEventListener('click', () => {{
        stopPlayback();
        const previousSync = findPreviousSyncIndex(frameIndex);
        if (previousSync !== null) {{
          renderFrame(previousSync);
        }}
      }});
      nextButton.addEventListener('click', () => {{
        stopPlayback();
        renderFrame(Math.min(frames.length - 1, frameIndex + 1));
      }});
      nextSyncButton.addEventListener('click', () => {{
        stopPlayback();
        const nextSync = findNextSyncIndex(frameIndex);
        if (nextSync !== null) {{
          renderFrame(nextSync);
        }}
      }});
      copyExactButton.addEventListener('click', async () => {{
        const frame = frames[frameIndex];
        try {{
          await copyText(absoluteUrlForHash(`step-${{frame.step}}`));
          setActionNote(`Copied exact frame link for step ${{frame.step}}.`, 'ok');
        }} catch (error) {{
          setActionNote(`Could not copy the exact frame link automatically: ${{error.message}}`, 'warn');
        }}
      }});
      copySyncButton.addEventListener('click', async () => {{
        const frame = frames[frameIndex];
        if (frame.sync_checkpoint === null) {{
          setActionNote('Stable sync links are only available on sync checkpoints. Copy the exact frame link instead.', 'warn');
          return;
        }}
        try {{
          await copyText(absoluteUrlForHash(`sync-${{frame.sync_checkpoint}}`));
          setActionNote(`Copied stable sync link #${{frame.sync_checkpoint}}.`, 'ok');
        }} catch (error) {{
          setActionNote(`Could not copy the stable sync link automatically: ${{error.message}}`, 'warn');
        }}
      }});
      downloadSvgButton.addEventListener('click', () => {{
        const frame = frames[frameIndex];
        downloadTextFile(buildCheckpointSvg(frame), fileNameForFrame(frame), 'image/svg+xml;charset=utf-8');
        setActionNote(`Downloaded ${{fileNameForFrame(frame)}} for the current checkpoint.`, 'ok');
      }});
      playButton.addEventListener('click', () => {{
        if (playTimer !== null) {{
          stopPlayback();
          return;
        }}
        startPlayback();
      }});
      speedSelect.addEventListener('change', () => {{
        if (playTimer !== null) {{
          startPlayback();
        }}
      }});
      range.addEventListener('input', (event) => {{
        stopPlayback();
        renderFrame(Number(event.target.value));
      }});
      window.addEventListener('hashchange', () => {{
        stopPlayback();
        renderFrame(indexFromHash(window.location.hash), {{ updateHash: false }});
      }});
      renderFrame(indexFromHash(window.location.hash), {{ updateHash: false }});
    </script>
  </body>
</html>
'''


def anti_entropy_story(report: dict[str, object]) -> str:
    sync_rows = list(report["sync_rows"])
    if not sync_rows:
        return (
            "This run has no anti-entropy exchange yet, so the digest view only shows each replica's current OR-Set payload footprint. "
            "Add a sync step to compare full-state shipping against delta-state transfer size."
        )
    totals = dict(report["totals"])
    largest = max(sync_rows, key=lambda row: int(row["delta_sync_bytes"]))
    largest_bytes = int(largest["delta_sync_bytes"])
    return (
        f"Across {totals['transfer_count']} directional sync transfer(s), shipping whole OR-Set states would cost {totals['full_sync_bytes']} byte(s), "
        f"while delta-state transfer needs {totals['delta_sync_bytes']} byte(s), saving {totals['bytes_saved_vs_full']} byte(s). "
        f"The largest sync delta in this run is step {largest['step']} at {largest_bytes} byte(s)."
    )


def build_anti_entropy_report(snapshot: dict[str, object]) -> dict[str, object]:
    replica_digests = {
        replica: digest_view_from_state_dict(dict(state))
        for replica, state in dict(snapshot["replicas"]).items()
    }
    sync_rows: list[dict[str, object]] = []
    transfer_count = 0
    total_full_bytes = 0
    total_delta_bytes = 0
    for step, event in enumerate(snapshot["timeline"], start=1):
        if str(event["op"]) != "sync":
            continue
        analysis = dict(event.get("anti_entropy") or {})
        if not analysis:
            continue
        direction = str(event["direction"])
        arrow = {"both": "↔", "forward": "→", "reverse": "←"}[direction]
        row = {
            "step": step,
            "event": f"{event['source']} {arrow} {event['target']} sync ({direction})",
            **analysis,
        }
        sync_rows.append(row)
        transfer_count += int(analysis.get("transfer_count", 0))
        total_full_bytes += int(analysis.get("full_sync_bytes", 0))
        total_delta_bytes += int(analysis.get("delta_sync_bytes", 0))
    report = {
        "replicas": sorted(dict(snapshot["replicas"])),
        "step_count": len(snapshot["timeline"]),
        "sync_count": len(sync_rows),
        "final_replica_digests": replica_digests,
        "sync_rows": sync_rows,
        "totals": {
            "transfer_count": transfer_count,
            "full_sync_bytes": total_full_bytes,
            "delta_sync_bytes": total_delta_bytes,
            "bytes_saved_vs_full": total_full_bytes - total_delta_bytes,
        },
    }
    report["story"] = anti_entropy_story(report)
    return report


def render_anti_entropy_markdown(report: dict[str, object], title: str) -> str:
    lines = [
        f"# OR-Set anti-entropy report — {title}",
        "",
        f"Replicas: {', '.join(report['replicas'])}",
        "",
        f"Story: {report['story']}",
        "",
        "## Totals",
        "",
        f"- sync steps: `{report['sync_count']}`",
        f"- directional transfers: `{report['totals']['transfer_count']}`",
        f"- full-state bytes: `{report['totals']['full_sync_bytes']}`",
        f"- delta-state bytes: `{report['totals']['delta_sync_bytes']}`",
        f"- bytes saved vs full-state sync: `{report['totals']['bytes_saved_vs_full']}`",
        "",
        "## Final replica digests",
        "",
    ]
    for replica, digest in report["final_replica_digests"].items():
        lines.append(
            f"- `{replica}` — digest `{digest['digest'][:16]}`…, payload `{digest['payload_bytes']}` bytes, observed tags `{digest['observed_tag_count']}`, tombstones `{digest['tombstone_count']}`, counters `{digest['counter_count']}`"
        )
    lines.extend([
        "",
        "## Sync transfer details",
        "",
        "| Step | Event | Transfer | Digests before | Full bytes | Delta bytes | Saved | Delta payload |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    if not report["sync_rows"]:
        lines.append("| n/a | no syncs yet | none | n/a | 0 | 0 | 0 | no transfer |")
        return "\n".join(lines) + "\n"
    for row in report["sync_rows"]:
        transfers = list(row["transfers"])
        if not transfers:
            lines.append(f"| {row['step']} | {row['event']} | none | n/a | 0 | 0 | 0 | no transfer |")
            continue
        for transfer in transfers:
            digest_pair = f"{transfer['from_digest'][:12]}… vs {transfer['to_digest'][:12]}…"
            delta_text = summarize_delta_payload(dict(transfer["delta_payload"]))
            event_text = str(row["event"]).replace("|", "\\|")
            delta_text = delta_text.replace("|", "\\|")
            lines.append(
                f"| {row['step']} | {event_text} | `{transfer['from']} -> {transfer['to']}` | `{digest_pair}` | {transfer['full_state']['payload_bytes']} | {transfer['delta']['payload_bytes']} | {transfer['bytes_saved_vs_full']} | {delta_text} |"
            )
    return "\n".join(lines) + "\n"


def render_anti_entropy_html(
    report: dict[str, object],
    title: str,
    *,
    companion_links: dict[str, str] | None = None,
) -> str:
    digest_cards = "".join(
        f'<li><strong><code>{escape_html(replica)}</code></strong>'
        f'<span>digest {escape_html(str(digest["digest"])[:16])}…</span>'
        f'<span>{escape_html(str(digest["payload_bytes"]))} bytes · observed tags {escape_html(str(digest["observed_tag_count"]))} · tombstones {escape_html(str(digest["tombstone_count"]))} · counters {escape_html(str(digest["counter_count"]))}</span></li>'
        for replica, digest in report["final_replica_digests"].items()
    )
    transfer_rows_html = "".join(
        "<tr>"
        f"<td>{row['step']}</td>"
        f"<td>{escape_html(str(row['event']))}</td>"
        f"<td>{escape_html(f'{transfer['from']} -> {transfer['to']}')}</td>"
        f"<td><code>{escape_html(str(transfer['from_digest'])[:12])}…</code><br /><code>{escape_html(str(transfer['to_digest'])[:12])}…</code></td>"
        f"<td>{transfer['full_state']['payload_bytes']}</td>"
        f"<td>{transfer['delta']['payload_bytes']}</td>"
        f"<td>{transfer['bytes_saved_vs_full']}</td>"
        f"<td>{escape_html(summarize_delta_payload(dict(transfer['delta_payload'])))}</td>"
        "</tr>"
        for row in report["sync_rows"]
        for transfer in row["transfers"]
    )
    if not transfer_rows_html:
        transfer_rows_html = '<tr><td colspan="8">No sync steps yet — this report is ready once the scenario includes anti-entropy traffic.</td></tr>'
    companion_links_html = "".join(
        f'<li><a href="{escape_html(path)}">{escape_html(label)}</a></li>'
        for label, path in (companion_links or {}).items()
    )
    if not companion_links_html:
        companion_links_html = "<li>This anti-entropy page is self-contained. Export Markdown/JSON or the timeline gallery alongside it to add companion links.</li>"
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OR-Set anti-entropy report — {escape_html(title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --panel-alt: #eef2ff;
        --border: #d7dde8;
        --text: #0f172a;
        --muted: #475569;
        --accent: #2563eb;
        --good: #166534;
        --good-bg: #dcfce7;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1440px; margin: 0 auto; padding: 32px 20px 64px; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .story {{ padding: 14px 16px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; color: #3730a3; }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0 0; padding: 0; }}
      .summary-grid li {{ list-style: none; padding: 16px 18px; border-radius: 18px; background: #f8fbff; border: 1px solid #dbeafe; }}
      .summary-grid strong {{ display: block; font-size: 1.3rem; margin-bottom: 6px; }}
      .layout {{ display: grid; gap: 24px; grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr); align-items: start; }}
      .panel {{ padding: 22px; }}
      .panel h2, .panel h3 {{ margin-top: 0; }}
      .digest-list, .artifact-links {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      .digest-list li + li, .artifact-links li + li {{ margin-top: 10px; }}
      .digest-list strong {{ color: var(--text); display: block; margin-bottom: 4px; }}
      .digest-list span {{ display: block; line-height: 1.5; }}
      .callout {{ padding: 14px 16px; border-radius: 18px; background: var(--good-bg); color: var(--good); line-height: 1.5; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
      a {{ color: var(--accent); }}
      @media (max-width: 1080px) {{ .layout {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>OR-Set anti-entropy report</h1>
        <p>This view turns the same scripted CRDT run into a merge-cost story: digest summaries show how large each replica state is, while per-sync delta payloads show how much data actually needs to move when replicas reconcile.</p>
        <p class="story">{escape_html(str(report['story']))}</p>
        <ul class="summary-grid">
          <li><strong>{report['sync_count']}</strong> sync steps</li>
          <li><strong>{report['totals']['transfer_count']}</strong> directional transfers</li>
          <li><strong>{report['totals']['full_sync_bytes']}</strong> full-state bytes</li>
          <li><strong>{report['totals']['delta_sync_bytes']}</strong> delta-state bytes</li>
          <li><strong>{report['totals']['bytes_saved_vs_full']}</strong> bytes saved</li>
        </ul>
      </section>
      <section class="layout">
        <article class="panel">
          <h2>{escape_html(title)}</h2>
          <div class="callout"><strong>Digest view:</strong> compare replica state fingerprints before a sync. <strong>Delta view:</strong> send only the missing tags, tombstones, and counter advances instead of the whole OR-Set payload.</div>
          <h3 style="margin-top: 18px;">Final replica digests</h3>
          <ul class="digest-list">{digest_cards}</ul>
        </article>
        <aside class="panel">
          <h2>Companion artifacts</h2>
          <ul class="artifact-links">{companion_links_html}</ul>
        </aside>
      </section>
      <section class="panel" style="margin-top: 24px;">
        <h2>Sync transfer details</h2>
        <table>
          <thead>
            <tr><th>Step</th><th>Event</th><th>Transfer</th><th>Digests before</th><th>Full bytes</th><th>Delta bytes</th><th>Saved</th><th>Delta payload</th></tr>
          </thead>
          <tbody>{transfer_rows_html}</tbody>
        </table>
      </section>
    </main>
  </body>
</html>
'''


def anti_entropy_title_from_args(args: argparse.Namespace) -> str:
    return timeline_title_from_args(args)


def write_anti_entropy_outputs(args: argparse.Namespace, snapshot: dict[str, object]) -> None:
    if not any(
        [
            args.anti_entropy_markdown_out,
            args.anti_entropy_html_out,
            args.anti_entropy_json_out,
        ]
    ):
        return
    report = build_anti_entropy_report(snapshot)
    title = anti_entropy_title_from_args(args)
    if args.anti_entropy_json_out:
        write_text_output(args.anti_entropy_json_out, json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.anti_entropy_markdown_out:
        write_text_output(args.anti_entropy_markdown_out, render_anti_entropy_markdown(report, title))
    if args.anti_entropy_html_out:
        base_dir = Path(args.anti_entropy_html_out).parent
        companion_links: dict[str, str] = {}
        for label, target in (
            ("Scenario script", getattr(args, "script", None) if getattr(args, "command", None) in {"run-script", "compare-script"} else None),
            ("Timeline gallery", args.timeline_html_out),
            ("Timeline Markdown", args.timeline_markdown_out),
            ("Timeline Mermaid", args.timeline_mermaid_out),
            ("Timeline SVG", args.timeline_svg_out),
            ("Timeline JSON", args.json_out),
            ("Replay HTML", args.replay_html_out),
            ("Anti-entropy Markdown", args.anti_entropy_markdown_out),
            ("Anti-entropy JSON", args.anti_entropy_json_out),
        ):
            if not target:
                continue
            relative = os.path.relpath(Path(target), base_dir)
            companion_links[label] = Path(relative).as_posix()
        write_text_output(
            args.anti_entropy_html_out,
            render_anti_entropy_html(report, title, companion_links=companion_links),
        )


def summarize_timestamp_mapping(mapping: dict[str, object]) -> str:
    parts: list[str] = []
    for element in sorted(mapping):
        parts.append(f"{element}={mapping[element]}")
    return "; ".join(parts) if parts else "∅"


def summarize_lww_state(state: dict[str, object]) -> str:
    elements = ", ".join(str(element) for element in state["elements"]) or "∅"
    adds = summarize_timestamp_mapping(dict(state["add_timestamps"]))
    removes = summarize_timestamp_mapping(dict(state["remove_timestamps"]))
    return f"elements {elements}; add_ts {adds}; remove_ts {removes}; bias {state['bias']}"


def compact_lww_state_note(state: dict[str, object]) -> str:
    elements = ", ".join(str(element) for element in state["elements"]) or "∅"
    adds = summarize_timestamp_mapping(dict(state["add_timestamps"]))
    removes = summarize_timestamp_mapping(dict(state["remove_timestamps"]))
    return f"elements={elements} | add_ts={adds} | remove_ts={removes} | bias={state['bias']}"


def format_optional_timestamp(value: object) -> str:
    return "∅" if value is None else str(value)


def membership_elements_for_states(orset_state: dict[str, object], lww_state: dict[str, object]) -> list[str]:
    return sorted(
        set(orset_state["elements"])
        | set(dict(orset_state["observed_tags"]))
        | set(lww_state["elements"])
        | set(dict(lww_state["add_timestamps"]))
        | set(dict(lww_state["remove_timestamps"]))
    )


def describe_replica_divergence(replica: str, orset_state: dict[str, object], lww_state: dict[str, object]) -> list[str]:
    details: list[str] = []
    active_tags = dict(orset_state["active_tags"])
    add_timestamps = dict(lww_state["add_timestamps"])
    remove_timestamps = dict(lww_state["remove_timestamps"])
    for element in membership_elements_for_states(orset_state, lww_state):
        orset_present = element in orset_state["elements"]
        lww_present = element in lww_state["elements"]
        if orset_present == lww_present:
            continue
        tags = ", ".join(str(tag) for tag in active_tags.get(element, [])) or "∅"
        details.append(
            f"{replica}:{element} OR-Set={'present' if orset_present else 'absent'} via tags {tags}; "
            f"LWW={'present' if lww_present else 'absent'} with add={format_optional_timestamp(add_timestamps.get(element))}, "
            f"remove={format_optional_timestamp(remove_timestamps.get(element))}, bias={lww_state['bias']}"
        )
    return details or [f"{replica}: membership matches"]


def build_comparison_rows(orset_snapshot: dict[str, object], lww_snapshot: dict[str, object]) -> list[dict[str, object]]:
    orset_timeline = list(orset_snapshot["timeline"])
    lww_timeline = list(lww_snapshot["timeline"])
    if len(orset_timeline) != len(lww_timeline):
        raise ValueError("OR-Set and LWW timelines must have the same length for comparison")
    rows: list[dict[str, object]] = []
    for step, (orset_event, lww_event) in enumerate(zip(orset_timeline, lww_timeline), start=1):
        op = str(orset_event["op"])
        if op == "add":
            replica = str(orset_event["replica"])
            orset_state = dict(orset_event["state"])
            lww_state = dict(lww_event["state"])
            rows.append(
                {
                    "step": step,
                    "event": f"{replica} adds {orset_event['element']} @ t={lww_event['timestamp']}",
                    "orset": compact_state_note(orset_state),
                    "lww": compact_lww_state_note(lww_state),
                    "divergence": describe_replica_divergence(replica, orset_state, lww_state),
                }
            )
        elif op == "remove":
            replica = str(orset_event["replica"])
            orset_state = dict(orset_event["state"])
            lww_state = dict(lww_event["state"])
            rows.append(
                {
                    "step": step,
                    "event": f"{replica} removes {orset_event['element']} @ t={lww_event['timestamp']}",
                    "orset": compact_state_note(orset_state),
                    "lww": compact_lww_state_note(lww_state),
                    "divergence": describe_replica_divergence(replica, orset_state, lww_state),
                }
            )
        else:
            source = str(orset_event["source"])
            target = str(orset_event["target"])
            direction = str(orset_event["direction"])
            arrow = {"both": "↔", "forward": "→", "reverse": "←"}[direction]
            orset_source = dict(orset_event["source_state"])
            orset_target = dict(orset_event["target_state"])
            lww_source = dict(lww_event["source_state"])
            lww_target = dict(lww_event["target_state"])
            rows.append(
                {
                    "step": step,
                    "event": f"{source} {arrow} {target} sync ({direction})",
                    "orset": f"{source}: {compact_state_note(orset_source)} || {target}: {compact_state_note(orset_target)}",
                    "lww": f"{source}: {compact_lww_state_note(lww_source)} || {target}: {compact_lww_state_note(lww_target)}",
                    "divergence": describe_replica_divergence(source, orset_source, lww_source)
                    + describe_replica_divergence(target, orset_target, lww_target),
                }
            )
    return rows


def build_final_divergence(orset_snapshot: dict[str, object], lww_snapshot: dict[str, object]) -> list[dict[str, object]]:
    if not orset_snapshot["replicas"] or not lww_snapshot["replicas"]:
        return []
    first_replica = next(iter(dict(orset_snapshot["replicas"])))
    orset_state = dict(dict(orset_snapshot["replicas"])[first_replica])
    lww_state = dict(dict(lww_snapshot["replicas"])[first_replica])
    active_tags = dict(orset_state["active_tags"])
    add_timestamps = dict(lww_state["add_timestamps"])
    remove_timestamps = dict(lww_state["remove_timestamps"])
    divergences: list[dict[str, object]] = []
    for element in membership_elements_for_states(orset_state, lww_state):
        orset_present = element in orset_state["elements"]
        lww_present = element in lww_state["elements"]
        if orset_present == lww_present:
            continue
        tags = [str(tag) for tag in active_tags.get(element, [])]
        add_timestamp = add_timestamps.get(element)
        remove_timestamp = remove_timestamps.get(element)
        divergences.append(
            {
                "element": element,
                "orset_present": orset_present,
                "lww_present": lww_present,
                "orset_active_tags": tags,
                "orset_tombstones": list(orset_state["tombstones"]),
                "lww_add_timestamp": add_timestamp,
                "lww_remove_timestamp": remove_timestamp,
                "why": (
                    f"OR-Set keeps only observed-remove tombstones, so active tags {', '.join(tags) or '∅'} can survive. "
                    f"LWW compares add={format_optional_timestamp(add_timestamp)} vs remove={format_optional_timestamp(remove_timestamp)} "
                    f"with {lww_state['bias']}-wins ties."
                ),
            }
        )
    return divergences


def comparison_story(final_divergence: list[dict[str, object]], lww_bias: str) -> str:
    if not final_divergence:
        return (
            "This script converges to the same final membership in both models; the comparison is still useful for showing "
            "that OR-Set tracks tags while LWW relies on timestamp ordering."
        )
    first = final_divergence[0]
    return (
        f"The final states diverge on {first['element']}: OR-Set leaves it "
        f"{'present' if first['orset_present'] else 'absent'} because the remove only tombstoned observed tags, "
        f"while LWW leaves it {'present' if first['lww_present'] else 'absent'} after comparing add={format_optional_timestamp(first['lww_add_timestamp'])} "
        f"and remove={format_optional_timestamp(first['lww_remove_timestamp'])} under {lww_bias}-wins ties."
    )


def build_semantics_comparison(
    replicas: Sequence[str],
    operations: Sequence[dict[str, object]],
    *,
    lww_bias: str = "remove",
) -> dict[str, object]:
    orset_cluster = ReplicaCluster(replicas)
    lww_cluster = LWWReplicaCluster(replicas, bias=lww_bias)
    orset_snapshot = orset_cluster.run_script(operations)
    lww_snapshot = lww_cluster.run_script(operations)
    final_divergence = build_final_divergence(orset_snapshot, lww_snapshot)
    return {
        "replicas": list(sorted(replicas)),
        "step_count": len(operations),
        "lww_bias": lww_bias,
        "comparison_rows": build_comparison_rows(orset_snapshot, lww_snapshot),
        "final_divergence": final_divergence,
        "story": comparison_story(final_divergence, lww_bias),
        "orset": orset_snapshot,
        "lww": lww_snapshot,
    }


def render_comparison_markdown(comparison: dict[str, object], title: str) -> str:
    lines = [
        f"# OR-Set vs LWW-element-set comparison — {title}",
        "",
        f"Replicas: {', '.join(comparison['replicas'])}",
        f"LWW tie bias: `{comparison['lww_bias']}`",
        "",
        f"Story: {comparison['story']}",
        "",
    ]
    final_divergence = list(comparison["final_divergence"])
    if final_divergence:
        lines.append("## Final divergence")
        lines.append("")
        for item in final_divergence:
            lines.append(
                f"- `{item['element']}` — OR-Set={'present' if item['orset_present'] else 'absent'}, "
                f"LWW={'present' if item['lww_present'] else 'absent'}; {item['why']}"
            )
        lines.append("")

    lines.extend([
        "## Step-by-step comparison",
        "",
        "| Step | Event | OR-Set view | LWW view | Divergence |",
        "| --- | --- | --- | --- | --- |",
    ])
    for row in comparison["comparison_rows"]:
        divergence_text = "<br>".join(str(detail).replace("|", "\\|") for detail in row["divergence"])
        event_text = str(row["event"]).replace("|", "\\|")
        orset_text = str(row["orset"]).replace("|", "\\|")
        lww_text = str(row["lww"]).replace("|", "\\|")
        lines.append(f"| {row['step']} | {event_text} | {orset_text} | {lww_text} | {divergence_text} |")

    lines.extend(["", "## Final OR-Set states", ""])
    for replica, state in dict(comparison["orset"]["replicas"]).items():
        lines.append(f"- `{replica}` — {summarize_state(dict(state))}")

    lines.extend(["", "## Final LWW states", ""])
    for replica, state in dict(comparison["lww"]["replicas"]).items():
        lines.append(f"- `{replica}` — {summarize_lww_state(dict(state))}")

    return "\n".join(lines) + "\n"


def render_comparison_html(
    comparison: dict[str, object],
    title: str,
    *,
    companion_links: dict[str, str] | None = None,
) -> str:
    final_divergence = list(comparison["final_divergence"])
    divergence_html = "".join(
        f'<li><strong><code>{escape_html(str(item["element"]))}</code></strong><span>{escape_html(str(item["why"]))}</span></li>'
        for item in final_divergence
    )
    if not divergence_html:
        divergence_html = "<li><strong>No final membership divergence</strong><span>The value-level outcome matches, but the two models still track different metadata.</span></li>"
    companion_links_html = "".join(
        f'<li><a href="{escape_html(path)}">{escape_html(label)}</a></li>'
        for label, path in (companion_links or {}).items()
    )
    if not companion_links_html:
        companion_links_html = "<li>This comparison page is self-contained. Pass comparison/timeline output flags to generate linked companion artifacts.</li>"
    orset_states_html = "".join(
        f'<li><strong><code>{escape_html(replica)}</code></strong><span>{escape_html(summarize_state(dict(state)))}</span></li>'
        for replica, state in dict(comparison["orset"]["replicas"]).items()
    )
    lww_states_html = "".join(
        f'<li><strong><code>{escape_html(replica)}</code></strong><span>{escape_html(summarize_lww_state(dict(state)))}</span></li>'
        for replica, state in dict(comparison["lww"]["replicas"]).items()
    )
    rows_html = "".join(
        "<tr>"
        f"<td>{row['step']}</td>"
        f"<td>{escape_html(str(row['event']))}</td>"
        f"<td>{escape_html(str(row['orset']))}</td>"
        f"<td>{escape_html(str(row['lww']))}</td>"
        f"<td>{''.join(f'<div>{escape_html(str(detail))}</div>' for detail in row['divergence'])}</td>"
        "</tr>"
        for row in comparison["comparison_rows"]
    )
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OR-Set vs LWW-element-set — {escape_html(title)}</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --panel-alt: #eff6ff;
        --border: #d7dde8;
        --text: #0f172a;
        --muted: #475569;
        --accent: #2563eb;
        --good: #166534;
        --good-bg: #dcfce7;
        --warn: #9a3412;
        --warn-bg: #ffedd5;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1440px; margin: 0 auto; padding: 32px 20px 64px; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .story {{ padding: 14px 16px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #bfdbfe; color: #1e3a8a; }}
      .summary-grid, .state-grid {{ display: grid; gap: 16px; }}
      .summary-grid {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); padding: 0; margin: 24px 0 0; }}
      .summary-grid li {{ list-style: none; padding: 16px 18px; border-radius: 18px; background: #f8fbff; border: 1px solid #dbeafe; }}
      .summary-grid strong {{ display: block; font-size: 1.3rem; margin-bottom: 6px; }}
      .layout {{ display: grid; gap: 24px; grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr); align-items: start; }}
      .panel {{ padding: 22px; }}
      .panel h2, .panel h3 {{ margin-top: 0; }}
      .artifact-links, .replica-list {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      .artifact-links li + li, .replica-list li + li {{ margin-top: 10px; }}
      .replica-list strong {{ color: var(--text); display: block; margin-bottom: 4px; }}
      .replica-list span {{ display: block; line-height: 1.5; }}
      .state-grid {{ grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
      .callout {{ padding: 14px 16px; border-radius: 18px; line-height: 1.5; }}
      .callout.good {{ background: var(--good-bg); color: var(--good); }}
      .callout.warn {{ background: var(--warn-bg); color: var(--warn); }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
      a {{ color: var(--accent); }}
      @media (max-width: 1080px) {{ .layout {{ grid-template-columns: 1fr; }} }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>OR-Set vs LWW-element-set</h1>
        <p>This page compares the same scripted history under tag-based observed-remove semantics and timestamp-based last-write-wins semantics. It is meant to make the conflict-resolution trade-off visible without reading raw JSON first.</p>
        <p class="story">{escape_html(str(comparison['story']))}</p>
        <ul class="summary-grid">
          <li><strong>{len(comparison['replicas'])}</strong> replicas ({escape_html(', '.join(comparison['replicas']) or 'none')})</li>
          <li><strong>{comparison['step_count']}</strong> scripted steps</li>
          <li><strong>{escape_html(str(comparison['lww_bias']))}</strong> LWW tie bias</li>
          <li><strong>{len(final_divergence)}</strong> final divergent element(s)</li>
        </ul>
      </section>
      <section class="layout">
        <article class="panel">
          <h2>Why the models diverge</h2>
          <div class="callout good"><strong>OR-Set:</strong> removes only the add-tags a replica has already observed, so a concurrent/new tag can survive later sync.</div>
          <div class="callout warn" style="margin-top: 12px;"><strong>LWW-element-set:</strong> resolves add/remove conflicts by timestamp ordering; when timestamps tie, the configured bias decides the winner.</div>
          <h3 style="margin-top: 18px;">Final divergence notes</h3>
          <ul class="replica-list">{divergence_html}</ul>
        </article>
        <aside class="panel">
          <h2>Companion artifacts</h2>
          <ul class="artifact-links">{companion_links_html}</ul>
        </aside>
      </section>
      <section class="panel" style="margin-top: 24px;">
        <h2>Final states</h2>
        <div class="state-grid">
          <section>
            <h3>OR-Set replicas</h3>
            <ul class="replica-list">{orset_states_html}</ul>
          </section>
          <section>
            <h3>LWW replicas</h3>
            <ul class="replica-list">{lww_states_html}</ul>
          </section>
        </div>
      </section>
      <section class="panel" style="margin-top: 24px;">
        <h2>Step-by-step comparison</h2>
        <table>
          <thead>
            <tr><th>Step</th><th>Event</th><th>OR-Set</th><th>LWW</th><th>Divergence</th></tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
      </section>
    </main>
  </body>
</html>
'''


def add_comparison_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--comparison-markdown-out")
    parser.add_argument("--comparison-html-out")
    parser.add_argument("--comparison-json-out")


def comparison_title_from_args(args: argparse.Namespace) -> str:
    return f"script {Path(args.script).name}"


def write_comparison_outputs(args: argparse.Namespace, comparison: dict[str, object]) -> None:
    if not any(
        [
            args.comparison_markdown_out,
            args.comparison_html_out,
            args.comparison_json_out,
        ]
    ):
        return

    title = comparison_title_from_args(args)
    if args.comparison_json_out:
        write_text_output(args.comparison_json_out, json.dumps(comparison, indent=2, sort_keys=True) + "\n")
    if args.comparison_markdown_out:
        write_text_output(args.comparison_markdown_out, render_comparison_markdown(comparison, title))
    if args.comparison_html_out:
        base_dir = Path(args.comparison_html_out).parent
        companion_links: dict[str, str] = {}
        for label, target in (
            ("Scenario script", args.script),
            ("OR-Set gallery", args.timeline_html_out),
            ("OR-Set replay", args.replay_html_out),
            ("OR-Set Markdown timeline", args.timeline_markdown_out),
            ("OR-Set Mermaid source", args.timeline_mermaid_out),
            ("OR-Set SVG card", args.timeline_svg_out),
            ("OR-Set JSON snapshot", args.json_out),
            ("OR-Set anti-entropy Markdown", args.anti_entropy_markdown_out),
            ("OR-Set anti-entropy HTML", args.anti_entropy_html_out),
            ("OR-Set anti-entropy JSON", args.anti_entropy_json_out),
            ("Comparison Markdown", args.comparison_markdown_out),
            ("Comparison JSON", args.comparison_json_out),
        ):
            if not target:
                continue
            relative = os.path.relpath(Path(target), base_dir)
            companion_links[label] = Path(relative).as_posix()
        write_text_output(
            args.comparison_html_out,
            render_comparison_html(comparison, title, companion_links=companion_links),
        )


def render_comparison_preset_suite_markdown(suite: dict[str, object]) -> str:
    lines = [
        "# OR-Set comparison preset suite",
        "",
        str(suite["story"]),
        "",
        "| Preset | Outcome | OR-Set final membership | LWW final membership | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for preset in suite["presets"]:
        lines.append(
            f"| `{preset['name']}` | {preset['outcome']} | {format_membership_map(dict(preset['orset_membership']))} | "
            f"{format_membership_map(dict(preset['lww_membership']))} | {str(preset['story']).replace('|', '\\|')} |"
        )
    lines.extend(["", "## Scenario notes", ""])
    for preset in suite["presets"]:
        lines.append(f"### {preset['title']} (`{preset['name']}`)")
        lines.append("")
        lines.append(f"- script: `{preset['script']}`")
        lines.append(f"- LWW tie bias: `{preset['lww_bias']}`")
        lines.append(f"- description: {preset['description']}")
        lines.append(f"- story: {preset['story']}")
        lines.append(f"- OR-Set final membership: {format_membership_map(dict(preset['orset_membership']))}")
        lines.append(f"- LWW final membership: {format_membership_map(dict(preset['lww_membership']))}")
        final_divergence = list(preset["final_divergence"])
        if final_divergence:
            lines.append("- divergence notes:")
            for item in final_divergence:
                lines.append(
                    f"  - `{item['element']}` — OR-Set={'present' if item['orset_present'] else 'absent'}, "
                    f"LWW={'present' if item['lww_present'] else 'absent'}; {item['why']}"
                )
        else:
            lines.append("- divergence notes: none; both models converge to the same final membership here.")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_comparison_preset_suite_html(suite: dict[str, object]) -> str:
    cards_html = "".join(
        "<article class=\"card\">"
        f"<h2>{escape_html(str(preset['title']))}</h2>"
        f"<p class=\"eyebrow\"><code>{escape_html(str(preset['name']))}</code> · {escape_html(str(preset['outcome']))} · {preset['step_count']} step(s)</p>"
        f"<p>{escape_html(str(preset['description']))}</p>"
        f"<p class=\"story\">{escape_html(str(preset['story']))}</p>"
        f"<ul class=\"meta\"><li><strong>script</strong><span><code>{escape_html(str(preset['script']))}</code></span></li><li><strong>LWW tie bias</strong><span><code>{escape_html(str(preset['lww_bias']))}</code></span></li><li><strong>OR-Set</strong><span>{escape_html(format_membership_map(dict(preset['orset_membership'])))}</span></li><li><strong>LWW</strong><span>{escape_html(format_membership_map(dict(preset['lww_membership'])))}</span></li></ul>"
        + (
            "<ul class=\"divergence\">"
            + "".join(
                f"<li><strong><code>{escape_html(str(item['element']))}</code></strong><span>{escape_html(str(item['why']))}</span></li>"
                for item in preset['final_divergence']
            )
            + "</ul>"
            if preset['final_divergence']
            else "<p class=\"aligned\">Both models reach the same final membership in this control case.</p>"
        )
        + "</article>"
        for preset in suite["presets"]
    )
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OR-Set comparison preset suite</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --panel-alt: #eff6ff;
        --border: #d7dde8;
        --text: #0f172a;
        --muted: #475569;
        --accent: #2563eb;
        --good: #166534;
        --good-bg: #dcfce7;
        --warn: #9a3412;
        --warn-bg: #ffedd5;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1440px; margin: 0 auto; padding: 32px 20px 64px; }}
      .hero, .card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .summary-grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); padding: 0; margin: 24px 0 0; }}
      .summary-grid li {{ list-style: none; padding: 16px 18px; border-radius: 18px; background: #f8fbff; border: 1px solid #dbeafe; }}
      .summary-grid strong {{ display: block; font-size: 1.3rem; margin-bottom: 6px; }}
      .cards {{ display: grid; gap: 20px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
      .card {{ padding: 22px; }}
      .eyebrow {{ color: var(--muted); margin-top: -4px; }}
      .story {{ padding: 12px 14px; border-radius: 16px; background: var(--panel-alt); border: 1px solid #dbeafe; color: #1e3a8a; line-height: 1.5; }}
      .meta, .divergence {{ list-style: none; padding: 0; margin: 16px 0 0; }}
      .meta li, .divergence li {{ display: grid; gap: 6px; padding: 10px 0; border-top: 1px solid var(--border); }}
      .meta strong, .divergence strong {{ color: var(--text); }}
      .meta span, .divergence span {{ color: var(--muted); line-height: 1.5; }}
      .aligned {{ margin: 16px 0 0; padding: 12px 14px; border-radius: 16px; background: var(--good-bg); color: var(--good); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>OR-Set comparison preset suite</h1>
        <p>This gallery packages multiple OR-Set vs LWW-element-set scenarios into one reviewable artifact so a portfolio reviewer can see both divergence-heavy cases and a control case without opening each script manually.</p>
        <p class="story">{escape_html(str(suite['story']))}</p>
        <ul class="summary-grid">
          <li><strong>{suite['preset_count']}</strong> canned scenario(s)</li>
          <li><strong>{suite['divergent_count']}</strong> divergent final outcomes</li>
          <li><strong>{suite['aligned_count']}</strong> aligned control case(s)</li>
        </ul>
      </section>
      <section class="cards">
        {cards_html}
      </section>
    </main>
  </body>
</html>
'''


def write_comparison_preset_suite_outputs(args: argparse.Namespace, suite: dict[str, object]) -> None:
    if getattr(args, "suite_json_out", None):
        write_text_output(args.suite_json_out, json.dumps(suite, indent=2, sort_keys=True) + "\n")
    if getattr(args, "suite_markdown_out", None):
        write_text_output(args.suite_markdown_out, render_comparison_preset_suite_markdown(suite))
    if getattr(args, "suite_html_out", None):
        write_text_output(args.suite_html_out, render_comparison_preset_suite_html(suite))


def write_text_output(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)


def add_timeline_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeline-markdown-out")
    parser.add_argument("--timeline-mermaid-out")
    parser.add_argument("--timeline-svg-out")
    parser.add_argument("--timeline-html-out")
    parser.add_argument("--replay-html-out")
    parser.add_argument("--json-out")
    parser.add_argument("--anti-entropy-markdown-out")
    parser.add_argument("--anti-entropy-html-out")
    parser.add_argument("--anti-entropy-json-out")


def timeline_title_from_args(args: argparse.Namespace) -> str:
    if args.command in {"run-script", "compare-script"}:
        return f"script {Path(args.script).name}"
    if args.command == "add":
        return f"single add {args.replica}:{args.element}"
    if args.command == "remove":
        return f"remove flow {args.replica}:{args.element}"
    return f"sync flow {args.source} {args.direction} {args.target}"


def write_replay_output(args: argparse.Namespace, snapshot: dict[str, object], title: str) -> None:
    if not args.replay_html_out:
        return
    companion_links = build_companion_links(
        html_path=args.replay_html_out,
        markdown_path=args.timeline_markdown_out,
        mermaid_path=args.timeline_mermaid_out,
        svg_path=args.timeline_svg_out,
        json_path=args.json_out,
        script_path=args.script if getattr(args, "command", None) in {"run-script", "compare-script"} else None,
        anti_entropy_markdown_path=args.anti_entropy_markdown_out,
        anti_entropy_html_path=args.anti_entropy_html_out,
        anti_entropy_json_path=args.anti_entropy_json_out,
    )
    base_dir = Path(args.replay_html_out).parent
    if getattr(args, "timeline_html_out", None):
        companion_links["Timeline gallery"] = Path(os.path.relpath(Path(args.timeline_html_out), base_dir)).as_posix()
    if getattr(args, "comparison_html_out", None):
        for label, target in (
            ("Comparison HTML", args.comparison_html_out),
            ("Comparison Markdown", getattr(args, "comparison_markdown_out", None)),
            ("Comparison JSON", getattr(args, "comparison_json_out", None)),
        ):
            if target:
                companion_links[label] = Path(os.path.relpath(Path(target), base_dir)).as_posix()
    write_text_output(args.replay_html_out, render_replay_html(snapshot, title, companion_links=companion_links))


def write_timeline_outputs(args: argparse.Namespace, snapshot: dict[str, object]) -> None:
    if not any(
        [
            args.timeline_markdown_out,
            args.timeline_mermaid_out,
            args.timeline_svg_out,
            args.timeline_html_out,
            args.replay_html_out,
            args.json_out,
            args.anti_entropy_markdown_out,
            args.anti_entropy_html_out,
            args.anti_entropy_json_out,
        ]
    ):
        return

    title = timeline_title_from_args(args)
    if args.json_out:
        write_text_output(args.json_out, json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    if args.timeline_markdown_out:
        write_text_output(args.timeline_markdown_out, render_timeline_markdown(snapshot, title))
    if args.timeline_mermaid_out:
        write_text_output(args.timeline_mermaid_out, render_timeline_mermaid(snapshot, title))
    if args.timeline_svg_out:
        write_text_output(args.timeline_svg_out, render_timeline_svg(snapshot, title))
    if args.timeline_html_out:
        companion_links = build_companion_links(
            html_path=args.timeline_html_out,
            markdown_path=args.timeline_markdown_out,
            mermaid_path=args.timeline_mermaid_out,
            svg_path=args.timeline_svg_out,
            json_path=args.json_out,
            script_path=args.script if getattr(args, "command", None) in {"run-script", "compare-script"} else None,
            anti_entropy_markdown_path=args.anti_entropy_markdown_out,
            anti_entropy_html_path=args.anti_entropy_html_out,
            anti_entropy_json_path=args.anti_entropy_json_out,
            replay_html_path=args.replay_html_out,
        )
        write_text_output(
            args.timeline_html_out,
            render_timeline_html(snapshot, title, companion_links=companion_links),
        )
    write_anti_entropy_outputs(args, snapshot)
    write_replay_output(args, snapshot, title)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Observed-remove set CRDT lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_script = subparsers.add_parser("run-script", help="run a JSON operation script across replicas")
    run_script.add_argument("--replicas", nargs="+", required=True)
    run_script.add_argument("--script", required=True)
    add_timeline_output_arguments(run_script)

    compare_script = subparsers.add_parser(
        "compare-script",
        help="compare the same JSON operation script under OR-Set and LWW-element-set semantics",
    )
    compare_script.add_argument("--replicas", nargs="+", required=True)
    compare_script.add_argument("--script", required=True)
    compare_script.add_argument("--lww-bias", choices=["add", "remove"], default="remove")
    add_timeline_output_arguments(compare_script)
    add_comparison_output_arguments(compare_script)

    preset_list = subparsers.add_parser(
        "list-presets",
        help="list built-in OR-Set vs LWW comparison presets",
    )
    preset_list.add_argument("--json", action="store_true")

    compare_presets = subparsers.add_parser(
        "compare-presets",
        help="run the built-in OR-Set comparison presets and summarize the outcomes",
    )
    compare_presets.add_argument(
        "--preset",
        dest="presets",
        action="append",
        help="repeat to run only selected built-in presets; defaults to all presets",
    )
    compare_presets.add_argument("--suite-markdown-out")
    compare_presets.add_argument("--suite-html-out")
    compare_presets.add_argument("--suite-json-out")

    add = subparsers.add_parser("add", help="apply one add on a fresh cluster")
    add.add_argument("--replicas", nargs="+", required=True)
    add.add_argument("--replica", required=True)
    add.add_argument("--element", required=True)
    add_timeline_output_arguments(add)

    remove = subparsers.add_parser("remove", help="sync optional seed state, then remove an observed element")
    remove.add_argument("--replicas", nargs="+", required=True)
    remove.add_argument("--seed-script")
    remove.add_argument("--replica", required=True)
    remove.add_argument("--element", required=True)
    add_timeline_output_arguments(remove)

    sync = subparsers.add_parser("sync", help="sync two replicas on a fresh or seeded cluster")
    sync.add_argument("--replicas", nargs="+", required=True)
    sync.add_argument("--seed-script")
    sync.add_argument("--source", required=True)
    sync.add_argument("--target", required=True)
    sync.add_argument("--direction", choices=["both", "forward", "reverse"], default="both")
    add_timeline_output_arguments(sync)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-presets":
        presets = [comparison_preset_to_dict(preset) for preset in list_comparison_presets()]
        if args.json:
            print(json.dumps({"presets": presets}, indent=2, sort_keys=True))
        else:
            print(format_comparison_preset_text(), end="")
        return 0

    if args.command == "compare-presets":
        try:
            suite = build_comparison_preset_suite(args.presets)
        except ValueError as exc:
            parser.error(str(exc))
        write_comparison_preset_suite_outputs(args, suite)
        print(json.dumps(suite, indent=2, sort_keys=True))
        return 0

    if args.command == "compare-script":
        comparison = build_semantics_comparison(
            args.replicas,
            load_script(args.script),
            lww_bias=args.lww_bias,
        )
        write_timeline_outputs(args, dict(comparison["orset"]))
        write_comparison_outputs(args, comparison)
        print(json.dumps(comparison, indent=2, sort_keys=True))
        return 0

    cluster = ReplicaCluster(args.replicas)

    if args.command == "run-script":
        result = cluster.run_script(load_script(args.script))
    elif args.command == "add":
        cluster.add(args.replica, args.element)
        result = cluster.snapshot()
    elif args.command == "remove":
        if args.seed_script:
            cluster.run_script(load_script(args.seed_script))
        cluster.remove(args.replica, args.element)
        result = cluster.snapshot()
    else:
        if args.seed_script:
            cluster.run_script(load_script(args.seed_script))
        cluster.sync(args.source, args.target, direction=args.direction)
        result = cluster.snapshot()

    write_timeline_outputs(args, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
