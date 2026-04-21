#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
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
class BankerTraceStep:
    step: int
    process: str
    runnable_processes: list[str]
    work_before: dict[str, int]
    need: dict[str, int]
    allocation_released: dict[str, int]
    work_after: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "process": self.process,
            "runnable_processes": self.runnable_processes,
            "work_before": self.work_before,
            "need": self.need,
            "allocation_released": self.allocation_released,
            "work_after": self.work_after,
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
    blocking: dict[str, dict[str, int]]
    trace_steps: list[BankerTraceStep]

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
            "blocking": self.blocking,
            "trace_steps": [step.to_dict() for step in self.trace_steps],
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
    trial_available: dict[str, int] | None
    trial_allocation: dict[str, dict[str, int]] | None
    trial_need: dict[str, dict[str, int]] | None
    blocking: dict[str, dict[str, int]]
    trace_steps: list[BankerTraceStep]

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
            "trial_available": self.trial_available,
            "trial_allocation": self.trial_allocation,
            "trial_need": self.trial_need,
            "blocking": self.blocking,
            "trace_steps": [step.to_dict() for step in self.trace_steps],
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



def _resource_vector(resources: list[str], values: dict[str, int]) -> dict[str, int]:
    return {resource: int(values.get(resource, 0)) for resource in resources}



def _banker_blocking(
    resources: list[str],
    processes: list[str],
    work: dict[str, int],
    need: dict[str, dict[str, int]],
    finished: dict[str, bool],
) -> dict[str, dict[str, int]]:
    blocking: dict[str, dict[str, int]] = {}
    for process in processes:
        if finished[process]:
            continue
        shortage: dict[str, int] = {}
        for resource in resources:
            missing = int(need[process].get(resource, 0)) - int(work.get(resource, 0))
            if missing > 0:
                shortage[resource] = missing
        blocking[process] = shortage
    return blocking



def banker_safety_from_state(
    resources: list[str],
    processes: list[str],
    available: dict[str, int],
    allocation: dict[str, dict[str, int]],
    need: dict[str, dict[str, int]],
) -> BankerSafetyAnalysis:
    work = _resource_vector(resources, available)
    finished = {process: False for process in processes}
    safe_sequence: list[str] = []
    trace_steps: list[BankerTraceStep] = []

    progress = True
    while progress:
        progress = False
        for process in processes:
            if finished[process]:
                continue
            if all(int(need[process].get(resource, 0)) <= work[resource] for resource in resources):
                runnable_processes = [
                    candidate
                    for candidate in processes
                    if not finished[candidate]
                    and all(int(need[candidate].get(resource, 0)) <= work[resource] for resource in resources)
                ]
                work_before = dict(work)
                allocation_released = _resource_vector(resources, allocation.get(process, {}))
                finished[process] = True
                safe_sequence.append(process)
                for resource in resources:
                    work[resource] += allocation_released[resource]
                trace_steps.append(
                    BankerTraceStep(
                        step=len(trace_steps) + 1,
                        process=process,
                        runnable_processes=runnable_processes,
                        work_before=work_before,
                        need=_resource_vector(resources, need[process]),
                        allocation_released=allocation_released,
                        work_after=dict(work),
                    )
                )
                progress = True

    unfinished = [process for process in processes if not finished[process]]
    blocking = _banker_blocking(resources, processes, work, need, finished)
    return BankerSafetyAnalysis(
        resources=resources,
        processes=processes,
        safe=not unfinished,
        safe_sequence=safe_sequence,
        unfinished_processes=unfinished,
        need=need,
        work=work,
        blocking=blocking,
        trace_steps=trace_steps,
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
                trial_available=None,
                trial_allocation=None,
                trial_need=None,
                blocking={},
                trace_steps=[],
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
                trial_available=None,
                trial_allocation=None,
                trial_need=None,
                blocking={},
                trace_steps=[],
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
            trial_available=trial_available,
            trial_allocation=trial_allocation,
            trial_need=trial_need,
            blocking=safety.blocking,
            trace_steps=safety.trace_steps,
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
        trial_available=trial_available,
        trial_allocation=trial_allocation,
        trial_need=trial_need,
        blocking=safety.blocking,
        trace_steps=safety.trace_steps,
    )



def _format_resource_vector(values: dict[str, int]) -> str:
    return ", ".join(f"{resource}={count}" for resource, count in values.items())


def _svg_id(label: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "-" for character in label)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "diagram"


def _edge_marker(stroke: str) -> str:
    if stroke == "#2563eb":
        return "url(#arrow-blue)"
    if stroke == "#dc2626":
        return "url(#arrow-red)"
    if stroke == "#d97706":
        return "url(#arrow-amber)"
    return "url(#arrow-slate)"


def _svg_defs() -> str:
    return """
  <defs>
    <marker id="arrow-slate" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
    </marker>
    <marker id="arrow-blue" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#2563eb" />
    </marker>
    <marker id="arrow-red" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#dc2626" />
    </marker>
    <marker id="arrow-amber" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#d97706" />
    </marker>
  </defs>
""".strip("\n")


def _svg_text(x: float, y: float, text: str, class_name: str = "label", anchor: str = "middle") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" class="{class_name}">{html.escape(text)}</text>'
    )


def render_wait_graph_svg(analysis: WaitForAnalysis, source_label: str, edges: list[tuple[str, str]]) -> str:
    diagram_id = _svg_id(f"wait-{source_label}")
    node_count = max(len(analysis.processes), 1)
    radius = max(110.0, 34.0 * node_count)
    width = max(760.0, radius * 2 + 240.0)
    height = max(560.0, radius * 2 + 240.0)
    center_x = width / 2
    center_y = height / 2
    node_radius = 30.0
    positions: dict[str, tuple[float, float]] = {}
    for index, process in enumerate(analysis.processes):
        angle = (-math.pi / 2) + (2 * math.pi * index / node_count)
        positions[process] = (
            center_x + radius * math.cos(angle),
            center_y + radius * math.sin(angle),
        )

    cycle_edges = {
        (analysis.cycle[index], analysis.cycle[index + 1])
        for index in range(len(analysis.cycle) - 1)
    }
    blocked_set = set(analysis.blocked_processes)
    edge_set = set(edges)
    order_lookup = {process: index for index, process in enumerate(analysis.processes)}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="{diagram_id}-title {diagram_id}-desc">',
        f'  <title id="{diagram_id}-title">Wait-for graph visualization for {html.escape(source_label)}</title>',
        f'  <desc id="{diagram_id}-desc">Processes arranged in a ring, with deadlocked cycle edges highlighted in red.</desc>',
        '  <style>',
        '    .bg { fill: #f8fafc; }',
        '    .card { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.5; }',
        '    .label { fill: #0f172a; font-family: Arial, sans-serif; font-size: 15px; }',
        '    .muted { fill: #475569; font-family: Arial, sans-serif; font-size: 13px; }',
        '    .tiny { fill: #475569; font-family: Arial, sans-serif; font-size: 12px; }',
        '  </style>',
        _svg_defs(),
        f'  <rect class="bg" x="0" y="0" width="{width:.0f}" height="{height:.0f}" rx="24" />',
        f'  <rect class="card" x="24" y="24" width="{width - 48:.0f}" height="{height - 48:.0f}" rx="20" />',
        _svg_text(52, 58, "Deadlock wait-for graph", "label", anchor="start"),
        _svg_text(52, 82, f"Source: {source_label}", "muted", anchor="start"),
        _svg_text(width - 52, 58, "cycle highlighted" if analysis.deadlocked else "no cycle found", "muted", anchor="end"),
    ]

    for source, target in edges:
        start_x, start_y = positions[source]
        end_x, end_y = positions[target]
        delta_x = end_x - start_x
        delta_y = end_y - start_y
        distance = math.hypot(delta_x, delta_y) or 1.0
        ux = delta_x / distance
        uy = delta_y / distance
        line_start_x = start_x + ux * node_radius
        line_start_y = start_y + uy * node_radius
        line_end_x = end_x - ux * node_radius
        line_end_y = end_y - uy * node_radius
        stroke = "#dc2626" if (source, target) in cycle_edges else "#475569"
        stroke_width = 3 if (source, target) in cycle_edges else 2
        if source == target:
            loop_dx = 34.0
            loop_dy = 46.0
            path = (
                f'M {start_x:.1f} {start_y - node_radius:.1f} '
                f'C {start_x + loop_dx:.1f} {start_y - node_radius - loop_dy:.1f}, '
                f'{start_x - loop_dx:.1f} {start_y - node_radius - loop_dy:.1f}, '
                f'{start_x:.1f} {start_y - node_radius:.1f}'
            )
            parts.append(
                f'  <path d="{path}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" marker-end="{_edge_marker(stroke)}" />'
            )
        elif (target, source) in edge_set:
            normal_x = -uy
            normal_y = ux
            sign = 1 if order_lookup[source] < order_lookup[target] else -1
            control_x = (start_x + end_x) / 2 + normal_x * 52.0 * sign
            control_y = (start_y + end_y) / 2 + normal_y * 52.0 * sign
            path = (
                f'M {line_start_x:.1f} {line_start_y:.1f} '
                f'Q {control_x:.1f} {control_y:.1f} {line_end_x:.1f} {line_end_y:.1f}'
            )
            parts.append(
                f'  <path d="{path}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" marker-end="{_edge_marker(stroke)}" />'
            )
        else:
            parts.append(
                "  "
                + f'<line x1="{line_start_x:.1f}" y1="{line_start_y:.1f}" x2="{line_end_x:.1f}" y2="{line_end_y:.1f}" '
                + f'stroke="{stroke}" stroke-width="{stroke_width}" marker-end="{_edge_marker(stroke)}" />'
            )

    for process in analysis.processes:
        x, y = positions[process]
        fill = "#fee2e2" if process in blocked_set else "#dbeafe"
        stroke = "#b91c1c" if process in blocked_set else "#1d4ed8"
        parts.append(
            f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="{node_radius:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="2.5" />'
        )
        parts.append(_svg_text(x, y + 5, process))

    legend_y = height - 88
    parts.extend(
        [
            f'  <rect x="52" y="{legend_y:.1f}" width="18" height="18" rx="5" fill="#fee2e2" stroke="#b91c1c" stroke-width="2" />',
            _svg_text(80, legend_y + 14, "blocked process", "tiny", anchor="start"),
            f'  <line x1="220" y1="{legend_y + 9:.1f}" x2="254" y2="{legend_y + 9:.1f}" stroke="#dc2626" stroke-width="3" marker-end="url(#arrow-red)" />',
            _svg_text(264, legend_y + 14, "cycle edge", "tiny", anchor="start"),
            f'  <line x1="360" y1="{legend_y + 9:.1f}" x2="394" y2="{legend_y + 9:.1f}" stroke="#475569" stroke-width="2" marker-end="url(#arrow-slate)" />',
            _svg_text(404, legend_y + 14, "waiting edge", "tiny", anchor="start"),
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_wait_graph_html(analysis: WaitForAnalysis, source_label: str, edges: list[tuple[str, str]]) -> str:
    svg = render_wait_graph_svg(analysis, source_label, edges).strip()
    edge_rows = "\n".join(
        f"<tr><td>{html.escape(source)}</td><td>{html.escape(target)}</td><td>{'cycle' if (source, target) in {(analysis.cycle[index], analysis.cycle[index + 1]) for index in range(len(analysis.cycle) - 1)} else 'waiting'}</td></tr>"
        for source, target in edges
    )
    blocked_summary = ", ".join(analysis.blocked_processes) if analysis.blocked_processes else "none"
    cycle_summary = " → ".join(analysis.cycle) if analysis.cycle else "none"
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Deadlock wait-for graph report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px 48px; }}
    .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 18px; padding: 20px; margin-top: 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .metric {{ background: #eff6ff; border-radius: 14px; padding: 14px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; }}
    th {{ font-size: 13px; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }}
    .danger {{ color: #b91c1c; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <h1>Deadlock wait-for graph report</h1>
    <p>Source: <code>{html.escape(source_label)}</code></p>
    <section class=\"grid\">
      <div class=\"metric\"><strong>Deadlocked</strong><br />{'yes' if analysis.deadlocked else 'no'}</div>
      <div class=\"metric\"><strong>Cycle</strong><br />{html.escape(cycle_summary)}</div>
      <div class=\"metric\"><strong>Blocked processes</strong><br />{html.escape(blocked_summary)}</div>
    </section>
    <section class=\"card\">{svg}</section>
    <section class=\"card\">
      <h2>Wait edges</h2>
      <table>
        <thead><tr><th>From</th><th>To</th><th>Status</th></tr></thead>
        <tbody>{edge_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def render_allocation_svg(
    analysis: AllocationAnalysis,
    source_label: str,
    available: dict[str, int],
    allocation: dict[str, dict[str, int]],
    request: dict[str, dict[str, int]],
) -> str:
    diagram_id = _svg_id(f"allocation-{source_label}")
    row_count = max(len(analysis.processes), len(analysis.resources), 1)
    width = 980.0
    height = max(520.0, 220.0 + row_count * 88.0)
    proc_x = 220.0
    res_x = 760.0
    top_y = 150.0
    gap_y = 80.0 if row_count == 1 else min(96.0, (height - 230.0) / max(row_count - 1, 1))
    process_positions = {
        process: (proc_x, top_y + index * gap_y) for index, process in enumerate(analysis.processes)
    }
    resource_positions = {
        resource: (res_x, top_y + index * gap_y) for index, resource in enumerate(analysis.resources)
    }
    blocked_set = set(analysis.deadlocked_processes)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="{diagram_id}-title {diagram_id}-desc">',
        f'  <title id="{diagram_id}-title">Resource allocation visualization for {html.escape(source_label)}</title>',
        f'  <desc id="{diagram_id}-desc">Processes on the left, resources on the right, with held edges from resources to processes and request edges from processes to resources.</desc>',
        '  <style>',
        '    .bg { fill: #f8fafc; }',
        '    .card { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.5; }',
        '    .label { fill: #0f172a; font-family: Arial, sans-serif; font-size: 15px; }',
        '    .muted { fill: #475569; font-family: Arial, sans-serif; font-size: 13px; }',
        '    .tiny { fill: #475569; font-family: Arial, sans-serif; font-size: 12px; }',
        '  </style>',
        _svg_defs(),
        f'  <rect class="bg" x="0" y="0" width="{width:.0f}" height="{height:.0f}" rx="24" />',
        f'  <rect class="card" x="24" y="24" width="{width - 48:.0f}" height="{height - 48:.0f}" rx="20" />',
        _svg_text(52, 58, "Deadlock resource-allocation view", "label", anchor="start"),
        _svg_text(52, 82, f"Source: {source_label}", "muted", anchor="start"),
        _svg_text(width - 52, 58, "deadlock detected" if analysis.deadlocked else "safe finish order found", "muted", anchor="end"),
        _svg_text(proc_x, 112, "Processes", "muted"),
        _svg_text(res_x, 112, "Resources", "muted"),
    ]

    for resource in analysis.resources:
        resource_x, resource_y = resource_positions[resource]
        for process in analysis.processes:
            held = int(allocation.get(process, {}).get(resource, 0))
            if held <= 0:
                continue
            process_x, process_y = process_positions[process]
            stroke = "#2563eb"
            parts.append(
                f'  <line x1="{resource_x - 34:.1f}" y1="{resource_y:.1f}" x2="{process_x + 58:.1f}" y2="{process_y:.1f}" stroke="{stroke}" stroke-width="2.5" marker-end="{_edge_marker(stroke)}" />'
            )
            label_x = (resource_x + process_x) / 2 + 10
            label_y = (resource_y + process_y) / 2 - 8
            parts.append(_svg_text(label_x, label_y, f"held {held}", "tiny"))

    for process in analysis.processes:
        process_x, process_y = process_positions[process]
        for resource in analysis.resources:
            needed = int(request.get(process, {}).get(resource, 0))
            if needed <= 0:
                continue
            resource_x, resource_y = resource_positions[resource]
            is_blocking = resource in analysis.blocking.get(process, {})
            stroke = "#dc2626" if is_blocking else "#d97706"
            dash = "6 5" if is_blocking else "5 5"
            parts.append(
                f'  <line x1="{process_x + 58:.1f}" y1="{process_y:.1f}" x2="{resource_x - 34:.1f}" y2="{resource_y:.1f}" stroke="{stroke}" stroke-width="2.5" stroke-dasharray="{dash}" marker-end="{_edge_marker(stroke)}" />'
            )
            label_x = (resource_x + process_x) / 2 - 8
            label_y = (resource_y + process_y) / 2 + (24 if resource_y >= process_y else -12)
            label = f"needs {needed}"
            if is_blocking:
                label += f" (short {analysis.blocking[process][resource]})"
            parts.append(_svg_text(label_x, label_y, label, "tiny"))

    for process in analysis.processes:
        x, y = process_positions[process]
        fill = "#fee2e2" if process in blocked_set else "#dbeafe"
        stroke = "#b91c1c" if process in blocked_set else "#1d4ed8"
        parts.append(
            f'  <rect x="{x - 58:.1f}" y="{y - 24:.1f}" width="116" height="48" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="2.5" />'
        )
        parts.append(_svg_text(x, y + 5, process))

    for resource in analysis.resources:
        x, y = resource_positions[resource]
        fill = "#fef3c7" if int(available.get(resource, 0)) == 0 else "#dcfce7"
        stroke = "#d97706" if int(available.get(resource, 0)) == 0 else "#16a34a"
        parts.append(
            f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="30" fill="{fill}" stroke="{stroke}" stroke-width="2.5" />'
        )
        parts.append(_svg_text(x, y + 3, resource))
        parts.append(_svg_text(x, y + 47, f"available {int(available.get(resource, 0))}", "tiny"))

    finish_summary = ", ".join(analysis.finish_order) if analysis.finish_order else "none"
    parts.extend(
        [
            _svg_text(52, height - 96, f"Finish order: {finish_summary}", "tiny", anchor="start"),
            _svg_text(52, height - 74, f"Deadlocked processes: {', '.join(analysis.deadlocked_processes) if analysis.deadlocked_processes else 'none'}", "tiny", anchor="start"),
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_allocation_html(
    analysis: AllocationAnalysis,
    source_label: str,
    available: dict[str, int],
    allocation: dict[str, dict[str, int]],
    request: dict[str, dict[str, int]],
) -> str:
    svg = render_allocation_svg(analysis, source_label, available, allocation, request).strip()
    blocking_rows = "\n".join(
        f"<tr><td>{html.escape(process)}</td><td>{html.escape(_format_resource_vector(shortage) or 'none')}</td></tr>"
        for process, shortage in analysis.blocking.items()
    ) or "<tr><td colspan=\"2\">none</td></tr>"
    resource_rows = "\n".join(
        f"<tr><td>{html.escape(resource)}</td><td>{int(available.get(resource, 0))}</td></tr>"
        for resource in analysis.resources
    )
    finish_summary = ", ".join(analysis.finish_order) if analysis.finish_order else "none"
    deadlocked_summary = ", ".join(analysis.deadlocked_processes) if analysis.deadlocked_processes else "none"
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Deadlock allocation report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1160px; margin: 0 auto; padding: 32px 24px 48px; }}
    .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 18px; padding: 20px; margin-top: 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .metric {{ background: #eff6ff; border-radius: 14px; padding: 14px; }}
    .tables {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ font-size: 13px; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }}
  </style>
</head>
<body>
  <main>
    <h1>Deadlock allocation report</h1>
    <p>Source: <code>{html.escape(source_label)}</code></p>
    <section class=\"grid\">
      <div class=\"metric\"><strong>Deadlocked</strong><br />{'yes' if analysis.deadlocked else 'no'}</div>
      <div class=\"metric\"><strong>Finish order</strong><br />{html.escape(finish_summary)}</div>
      <div class=\"metric\"><strong>Deadlocked processes</strong><br />{html.escape(deadlocked_summary)}</div>
    </section>
    <section class=\"card\">{svg}</section>
    <section class=\"tables\">
      <div class=\"card\">
        <h2>Available resources</h2>
        <table>
          <thead><tr><th>Resource</th><th>Available</th></tr></thead>
          <tbody>{resource_rows}</tbody>
        </table>
      </div>
      <div class=\"card\">
        <h2>Blocking summary</h2>
        <table>
          <thead><tr><th>Process</th><th>Shortage</th></tr></thead>
          <tbody>{blocking_rows}</tbody>
        </table>
      </div>
    </section>
  </main>
</body>
</html>
"""


def _write_optional_text(path_text: str | None, content: str | None) -> None:
    if not path_text or content is None:
        return
    path = Path(path_text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")



def render_banker_safety_markdown(analysis: BankerSafetyAnalysis, source_label: str) -> str:
    lines = [
        "# Banker's algorithm safety trace",
        "",
        f"- Source: `{source_label}`",
        f"- Safe: {'yes' if analysis.safe else 'no'}",
        f"- Safe sequence: `{', '.join(analysis.safe_sequence)}`" if analysis.safe_sequence else "- Safe sequence: none",
        f"- Final work: `{_format_resource_vector(analysis.work)}`",
    ]
    if analysis.unfinished_processes:
        lines.append(f"- Unfinished processes: `{', '.join(analysis.unfinished_processes)}`")
    if analysis.blocking:
        blocking_parts = []
        for process, shortage in analysis.blocking.items():
            blocking_parts.append(f"`{process}` needs {_format_resource_vector(shortage)}")
        lines.append(f"- Blocking summary: {'; '.join(blocking_parts)}")
    lines.extend(
        [
            "",
            "## Safety trace steps",
            "",
            "| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for step in analysis.trace_steps:
        lines.append(
            f"| {step.step} | `{step.process}` | `{', '.join(step.runnable_processes)}` | `{_format_resource_vector(step.work_before)}` | `{_format_resource_vector(step.need)}` | `{_format_resource_vector(step.allocation_released)}` | `{_format_resource_vector(step.work_after)}` |"
        )
    if not analysis.trace_steps:
        lines.append("| 0 | none | none | n/a | n/a | n/a | n/a |")
    return "\n".join(lines) + "\n"



def render_banker_request_markdown(analysis: BankerRequestAnalysis, source_label: str) -> str:
    lines = [
        "# Banker's algorithm request trace",
        "",
        f"- Source: `{source_label}`",
        f"- Process: `{analysis.process}`",
        f"- Request: `{_format_resource_vector(analysis.request)}`",
        f"- Granted: {'yes' if analysis.granted else 'no'}",
        f"- Reason: {analysis.reason}",
        f"- Safe after trial: {'yes' if analysis.safe else 'no'}",
        f"- Safe sequence: `{', '.join(analysis.safe_sequence)}`" if analysis.safe_sequence else "- Safe sequence: none",
    ]
    trial_available = analysis.trial_available if analysis.trial_available is not None else analysis.available
    lines.append(f"- Evaluated available vector: `{_format_resource_vector(trial_available)}`")
    if analysis.blocking:
        blocking_parts = []
        for process, shortage in analysis.blocking.items():
            blocking_parts.append(f"`{process}` needs {_format_resource_vector(shortage)}")
        lines.append(f"- Blocking summary: {'; '.join(blocking_parts)}")
    lines.extend(
        [
            "",
            "## Trial safety trace",
            "",
            "| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for step in analysis.trace_steps:
        lines.append(
            f"| {step.step} | `{step.process}` | `{', '.join(step.runnable_processes)}` | `{_format_resource_vector(step.work_before)}` | `{_format_resource_vector(step.need)}` | `{_format_resource_vector(step.allocation_released)}` | `{_format_resource_vector(step.work_after)}` |"
        )
    if not analysis.trace_steps:
        lines.append("| 0 | none | none | n/a | n/a | n/a | n/a |")
    return "\n".join(lines) + "\n"



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze deadlocks using wait-for, allocation, or Banker's algorithm models")
    subparsers = parser.add_subparsers(dest="command", required=True)

    wait_parser = subparsers.add_parser("analyze-wait", help="analyze a wait-for graph from JSON")
    wait_parser.add_argument("input", help="path to JSON file containing an 'edges' array")
    wait_parser.add_argument(
        "--svg-out",
        help="optional path for a wait-for graph SVG export",
    )
    wait_parser.add_argument(
        "--html-out",
        help="optional path for a wait-for graph HTML export",
    )

    alloc_parser = subparsers.add_parser(
        "analyze-allocations",
        help="analyze an allocation/request state from JSON",
    )
    alloc_parser.add_argument(
        "input",
        help="path to JSON file containing available/allocation/request objects",
    )
    alloc_parser.add_argument(
        "--svg-out",
        help="optional path for a resource-allocation SVG export",
    )
    alloc_parser.add_argument(
        "--html-out",
        help="optional path for a resource-allocation HTML export",
    )

    banker_parser = subparsers.add_parser(
        "analyze-banker",
        help="analyze a Banker's algorithm state from JSON",
    )
    banker_parser.add_argument(
        "input",
        help="path to JSON file containing available/allocation/max objects",
    )
    banker_parser.add_argument(
        "--markdown-out",
        help="optional path for a step-by-step Banker's safety trace markdown export",
    )

    banker_request_parser = subparsers.add_parser(
        "request-banker",
        help="evaluate a Banker's algorithm resource request from JSON",
    )
    banker_request_parser.add_argument(
        "input",
        help="path to JSON file containing available/allocation/max/process/request objects",
    )
    banker_request_parser.add_argument(
        "--markdown-out",
        help="optional path for a Banker's request evaluation markdown trace export",
    )

    return parser



def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        payload = load_json(Path(args.input))
        markdown: str | None = None
        svg: str | None = None
        html_report: str | None = None
        if args.command == "analyze-wait":
            analysis = analyze_wait_for_graph(payload)
            result = analysis.to_dict()
            edges = [
                (str(item["from"]), str(item["to"]))
                for item in payload.get("edges", [])
                if isinstance(item, dict) and isinstance(item.get("from"), str) and isinstance(item.get("to"), str)
            ]
            if getattr(args, "svg_out", None):
                svg = render_wait_graph_svg(analysis, args.input, edges)
            if getattr(args, "html_out", None):
                html_report = render_wait_graph_html(analysis, args.input, edges)
        elif args.command == "analyze-allocations":
            analysis = analyze_allocations(payload)
            result = analysis.to_dict()
            available = payload.get("available")
            allocation = payload.get("allocation")
            request = payload.get("request")
            if isinstance(available, dict) and isinstance(allocation, dict) and isinstance(request, dict):
                if getattr(args, "svg_out", None):
                    svg = render_allocation_svg(analysis, args.input, available, allocation, request)
                if getattr(args, "html_out", None):
                    html_report = render_allocation_html(analysis, args.input, available, allocation, request)
        elif args.command == "analyze-banker":
            analysis = analyze_banker_state(payload)
            result = analysis.to_dict()
            if getattr(args, "markdown_out", None):
                markdown = render_banker_safety_markdown(analysis, args.input)
        elif args.command == "request-banker":
            analysis = analyze_banker_request(payload)
            result = analysis.to_dict()
            if getattr(args, "markdown_out", None):
                markdown = render_banker_request_markdown(analysis, args.input)
        else:
            parser.error("unsupported command")
            return 2

        _write_optional_text(getattr(args, "markdown_out", None), markdown)
        _write_optional_text(getattr(args, "svg_out", None), svg)
        _write_optional_text(getattr(args, "html_out", None), html_report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
