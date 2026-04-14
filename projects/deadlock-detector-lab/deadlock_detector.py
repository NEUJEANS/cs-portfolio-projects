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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze deadlocks using wait-for or allocation models")
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
        else:
            parser.error("unsupported command")
            return 2
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
