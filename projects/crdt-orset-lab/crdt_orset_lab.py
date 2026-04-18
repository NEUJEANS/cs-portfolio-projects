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



def write_text_output(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)


def add_timeline_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeline-markdown-out")
    parser.add_argument("--timeline-mermaid-out")
    parser.add_argument("--timeline-svg-out")
    parser.add_argument("--timeline-html-out")
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


def write_timeline_outputs(args: argparse.Namespace, snapshot: dict[str, object]) -> None:
    if not any(
        [
            args.timeline_markdown_out,
            args.timeline_mermaid_out,
            args.timeline_svg_out,
            args.timeline_html_out,
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
        )
        write_text_output(
            args.timeline_html_out,
            render_timeline_html(snapshot, title, companion_links=companion_links),
        )
    write_anti_entropy_outputs(args, snapshot)


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
