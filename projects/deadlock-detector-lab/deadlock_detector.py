#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class WaitForAnalysis:
    processes: list[str]
    deadlocked: bool
    cycle: list[str]
    blocked_processes: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "wait-for-graph",
            "processes": self.processes,
            "deadlocked": self.deadlocked,
            "cycle": self.cycle,
            "blocked_processes": self.blocked_processes,
        }


@dataclass(slots=True)
class AllocationAnalysis:
    resources: list[str]
    processes: list[str]
    deadlocked: bool
    finish_order: list[str]
    deadlocked_processes: list[str]
    blocking: dict[str, dict[str, int]]
    work: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "resource-allocation",
            "resources": self.resources,
            "processes": self.processes,
            "deadlocked": self.deadlocked,
            "finish_order": self.finish_order,
            "deadlocked_processes": self.deadlocked_processes,
            "blocking": self.blocking,
            "work": self.work,
        }


@dataclass(slots=True)
class BankerSafetyAnalysis:
    resources: list[str]
    processes: list[str]
    safe: bool
    safe_sequence: list[str]
    unfinished_processes: list[str]
    need: dict[str, dict[str, int]]
    work: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "banker-safety",
            "resources": self.resources,
            "processes": self.processes,
            "safe": self.safe,
            "safe_sequence": self.safe_sequence,
            "unfinished_processes": self.unfinished_processes,
            "need": self.need,
            "work": self.work,
        }


@dataclass(slots=True)
class BankerRequestAnalysis:
    process: str
    request: dict[str, int]
    granted: bool
    reason: str
    safe: bool
    safe_sequence: list[str]
    available: dict[str, int]
    allocation: dict[str, dict[str, int]]
    need: dict[str, dict[str, int]]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "banker-request",
            "process": self.process,
            "request": self.request,
            "granted": self.granted,
            "reason": self.reason,
            "safe": self.safe,
            "safe_sequence": self.safe_sequence,
            "available": self.available,
            "allocation": self.allocation,
            "need": self.need,
        }


def stable_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return sorted(ordered)


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object at the top level")
    return payload


def find_cycle(graph: dict[str, list[str]]) -> list[str]:
    visited: set[str] = set()
    stack: list[str] = []
    in_stack: set[str] = set()

    def dfs(node: str) -> list[str]:
        visited.add(node)
        stack.append(node)
        in_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            elif neighbor in in_stack:
                start = stack.index(neighbor)
                return stack[start:] + [neighbor]

        stack.pop()
        in_stack.remove(node)
        return []

    for node in sorted(graph):
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return []


def analyze_wait_for_graph(payload: dict[str, object]) -> WaitForAnalysis:
    edges = payload.get("edges")
    if not isinstance(edges, list):
        raise ValueError("wait-for graph payload must contain an 'edges' list")

    graph: dict[str, list[str]] = {}
    processes: list[str] = []
    for item in edges:
        if not isinstance(item, dict):
            raise ValueError("each edge must be an object with 'from' and 'to'")
        source = item.get("from")
        target = item.get("to")
        if not isinstance(source, str) or not isinstance(target, str):
            raise ValueError("edge endpoints must be strings")
        graph.setdefault(source, []).append(target)
        graph.setdefault(target, [])
        processes.extend([source, target])

    for node in graph:
        graph[node] = sorted(graph[node])

    cycle = find_cycle(graph)
    blocked = stable_unique(cycle[:-1]) if cycle else []
    return WaitForAnalysis(
        processes=stable_unique(processes),
        deadlocked=bool(cycle),
        cycle=cycle,
        blocked_processes=blocked,
    )


def validate_vectors(
    available: dict[str, int],
    allocation: dict[str, dict[str, int]],
    request: dict[str, dict[str, int]],
) -> tuple[list[str], list[str]]:
    resources = stable_unique(available.keys())
    processes = stable_unique(list(allocation.keys()) + list(request.keys()))

    for resource, count in available.items():
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"available count for {resource!r} must be a non-negative integer")

    for process in processes:
        alloc_map = allocation.get(process, {})
        req_map = request.get(process, {})
        if not isinstance(alloc_map, dict) or not isinstance(req_map, dict):
            raise ValueError("allocation/request entries must be objects")
        resources = stable_unique(resources + list(alloc_map.keys()) + list(req_map.keys()))
        for vector_name, vector in (("allocation", alloc_map), ("request", req_map)):
            for resource, count in vector.items():
                if not isinstance(count, int) or count < 0:
                    raise ValueError(
                        f"{vector_name} count for process {process!r} resource {resource!r} must be a non-negative integer"
                    )
    return resources, processes


def analyze_allocations(payload: dict[str, object]) -> AllocationAnalysis:
    available = payload.get("available")
    allocation = payload.get("allocation")
    request = payload.get("request")
    if not isinstance(available, dict) or not isinstance(allocation, dict) or not isinstance(request, dict):
        raise ValueError("allocation payload must contain object fields: available, allocation, request")

    resources, processes = validate_vectors(available, allocation, request)
    work = {resource: int(available.get(resource, 0)) for resource in resources}
    finished = {process: False for process in processes}
    finish_order: list[str] = []

    progress = True
    while progress:
        progress = False
        for process in processes:
            if finished[process]:
                continue
            needed = request.get(process, {})
            if all(int(needed.get(resource, 0)) <= work[resource] for resource in resources):
                finished[process] = True
                finish_order.append(process)
                held = allocation.get(process, {})
                for resource in resources:
                    work[resource] += int(held.get(resource, 0))
                progress = True

    deadlocked_processes = [process for process in processes if not finished[process]]
    blocking: dict[str, dict[str, int]] = {}
    for process in deadlocked_processes:
        needed = request.get(process, {})
        shortage: dict[str, int] = {}
        for resource in resources:
            missing = int(needed.get(resource, 0)) - work[resource]
            if missing > 0:
                shortage[resource] = missing
        blocking[process] = shortage

    return AllocationAnalysis(
        resources=resources,
        processes=processes,
        deadlocked=bool(deadlocked_processes),
        finish_order=finish_order,
        deadlocked_processes=deadlocked_processes,
        blocking=blocking,
        work=work,
    )


def _validate_matrix(name: str, matrix: object) -> dict[str, dict[str, int]]:
    if not isinstance(matrix, dict):
        raise ValueError(f"{name} must be an object mapping process names to resource counts")
    normalized: dict[str, dict[str, int]] = {}
    for process, vector in matrix.items():
        if not isinstance(process, str):
            raise ValueError(f"{name} process names must be strings")
        if not isinstance(vector, dict):
            raise ValueError(f"{name} entry for process {process!r} must be an object")
        normalized[process] = {}
        for resource, count in vector.items():
            if not isinstance(resource, str):
                raise ValueError(f"{name} resource names must be strings")
            if not isinstance(count, int) or count < 0:
                raise ValueError(
                    f"{name} count for process {process!r} resource {resource!r} must be a non-negative integer"
                )
            normalized[process][resource] = count
    return normalized



def _normalize_available(available: object) -> dict[str, int]:
    if not isinstance(available, dict):
        raise ValueError("available must be an object mapping resource names to counts")
    normalized: dict[str, int] = {}
    for resource, count in available.items():
        if not isinstance(resource, str):
            raise ValueError("available resource names must be strings")
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"available count for {resource!r} must be a non-negative integer")
        normalized[resource] = count
    return normalized


def validate_banker_state(
    payload: dict[str, object]
) -> tuple[list[str], list[str], dict[str, int], dict[str, dict[str, int]], dict[str, dict[str, int]]]:
    available = _normalize_available(payload.get("available"))
    allocation = _validate_matrix("allocation", payload.get("allocation"))
    maximum = _validate_matrix("max", payload.get("max"))

    processes = stable_unique(list(allocation.keys()) + list(maximum.keys()))
    resources = stable_unique(list(available.keys()))
    for process in processes:
        resources = stable_unique(resources + list(allocation.get(process, {}).keys()) + list(maximum.get(process, {}).keys()))

    need: dict[str, dict[str, int]] = {}
    for process in processes:
        need[process] = {}
        alloc_row = allocation.get(process, {})
        max_row = maximum.get(process, {})
        for resource in resources:
            alloc_value = int(alloc_row.get(resource, 0))
            max_value = int(max_row.get(resource, 0))
            if alloc_value > max_value:
                raise ValueError(
                    f"allocation for process {process!r} resource {resource!r} cannot exceed max claim"
                )
            need[process][resource] = max_value - alloc_value

    return resources, processes, available, allocation, need



def banker_safety_from_state(
    resources: list[str],
    processes: list[str],
    available: dict[str, int],
    allocation: dict[str, dict[str, int]],
    need: dict[str, dict[str, int]],
) -> BankerSafetyAnalysis:
    work = {resource: int(available.get(resource, 0)) for resource in resources}
    finished = {process: False for process in processes}
    safe_sequence: list[str] = []

    progress = True
    while progress:
        progress = False
        for process in processes:
            if finished[process]:
                continue
            if all(int(need[process].get(resource, 0)) <= work[resource] for resource in resources):
                finished[process] = True
                safe_sequence.append(process)
                for resource in resources:
                    work[resource] += int(allocation.get(process, {}).get(resource, 0))
                progress = True

    unfinished = [process for process in processes if not finished[process]]
    return BankerSafetyAnalysis(
        resources=resources,
        processes=processes,
        safe=not unfinished,
        safe_sequence=safe_sequence,
        unfinished_processes=unfinished,
        need=need,
        work=work,
    )



def analyze_banker_state(payload: dict[str, object]) -> BankerSafetyAnalysis:
    resources, processes, available, allocation, need = validate_banker_state(payload)
    return banker_safety_from_state(resources, processes, available, allocation, need)



def analyze_banker_request(payload: dict[str, object]) -> BankerRequestAnalysis:
    resources, processes, available, allocation, need = validate_banker_state(payload)
    process = payload.get("process")
    request_payload = payload.get("request")
    if not isinstance(process, str):
        raise ValueError("request payload must contain a string 'process' field")
    if process not in processes:
        raise ValueError(f"unknown process {process!r} in banker request")
    if not isinstance(request_payload, dict):
        raise ValueError("request payload must contain an object 'request' field")

    request: dict[str, int] = {}
    for resource, count in request_payload.items():
        if not isinstance(resource, str):
            raise ValueError("request resource names must be strings")
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"request count for resource {resource!r} must be a non-negative integer")
        request[resource] = count

    for resource in resources:
        requested = int(request.get(resource, 0))
        if requested > int(need[process].get(resource, 0)):
            return BankerRequestAnalysis(
                process=process,
                request=request,
                granted=False,
                reason="request exceeds declared remaining need",
                safe=False,
                safe_sequence=[],
                available=available,
                allocation=allocation,
                need=need,
            )
        if requested > int(available.get(resource, 0)):
            return BankerRequestAnalysis(
                process=process,
                request=request,
                granted=False,
                reason="request exceeds currently available resources",
                safe=False,
                safe_sequence=[],
                available=available,
                allocation=allocation,
                need=need,
            )

    trial_available = dict(available)
    trial_allocation = {name: dict(v) for name, v in allocation.items()}
    trial_need = {name: dict(v) for name, v in need.items()}
    for resource in resources:
        requested = int(request.get(resource, 0))
        trial_available[resource] = int(trial_available.get(resource, 0)) - requested
        trial_allocation.setdefault(process, {})[resource] = int(trial_allocation.get(process, {}).get(resource, 0)) + requested
        trial_need[process][resource] = int(trial_need[process].get(resource, 0)) - requested

    safety = banker_safety_from_state(resources, processes, trial_available, trial_allocation, trial_need)
    if not safety.safe:
        return BankerRequestAnalysis(
            process=process,
            request=request,
            granted=False,
            reason="request would move the system into an unsafe state",
            safe=False,
            safe_sequence=safety.safe_sequence,
            available=available,
            allocation=allocation,
            need=need,
        )

    return BankerRequestAnalysis(
        process=process,
        request=request,
        granted=True,
        reason="request can be granted safely",
        safe=True,
        safe_sequence=safety.safe_sequence,
        available=trial_available,
        allocation=trial_allocation,
        need=trial_need,
    )



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze deadlocks using wait-for, allocation, or Banker's algorithm models")
    subparsers = parser.add_subparsers(dest="command", required=True)

    wait_parser = subparsers.add_parser("analyze-wait", help="analyze a wait-for graph from JSON")
    wait_parser.add_argument("input", help="path to JSON file containing an 'edges' array")

    alloc_parser = subparsers.add_parser(
        "analyze-allocations",
        help="analyze an allocation/request state from JSON",
    )
    alloc_parser.add_argument(
        "input",
        help="path to JSON file containing available/allocation/request objects",
    )

    banker_parser = subparsers.add_parser(
        "analyze-banker",
        help="analyze a Banker's algorithm state from JSON",
    )
    banker_parser.add_argument(
        "input",
        help="path to JSON file containing available/allocation/max objects",
    )

    banker_request_parser = subparsers.add_parser(
        "request-banker",
        help="evaluate a Banker's algorithm resource request from JSON",
    )
    banker_request_parser.add_argument(
        "input",
        help="path to JSON file containing available/allocation/max/process/request objects",
    )

    return parser



def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = load_json(Path(args.input))
        if args.command == "analyze-wait":
            result = analyze_wait_for_graph(payload).to_dict()
        elif args.command == "analyze-allocations":
            result = analyze_allocations(payload).to_dict()
        elif args.command == "analyze-banker":
            result = analyze_banker_state(payload).to_dict()
        elif args.command == "request-banker":
            result = analyze_banker_request(payload).to_dict()
        else:
            parser.error("unsupported command")
            return 2
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
