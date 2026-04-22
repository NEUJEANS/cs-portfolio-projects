#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import textwrap
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


@dataclass(slots=True)
class BankerRequestReport:
    source: str
    analysis: BankerRequestAnalysis

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "analysis": self.analysis.to_dict(),
        }


@dataclass(slots=True)
class BankerRequestGallery:
    request_reports: list[BankerRequestReport]
    decision_totals: dict[str, int]
    highlights: list[str]
    delta_callouts: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "banker-request-gallery",
            "decision_totals": self.decision_totals,
            "highlights": self.highlights,
            "delta_callouts": self.delta_callouts,
            "request_reports": [report.to_dict() for report in self.request_reports],
        }


@dataclass(slots=True)
class DetectionAvoidanceDashboard:
    wait_for: WaitForAnalysis
    allocation: AllocationAnalysis
    banker_safety: BankerSafetyAnalysis
    banker_request: BankerRequestAnalysis | None
    banker_request_contrast: BankerRequestAnalysis | None
    banker_request_delta_callout: dict[str, object] | None
    key_takeaways: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "model": "deadlock-detection-vs-avoidance",
            "key_takeaways": self.key_takeaways,
            "wait_for": self.wait_for.to_dict(),
            "allocation": self.allocation.to_dict(),
            "banker_safety": self.banker_safety.to_dict(),
            "banker_request": self.banker_request.to_dict() if self.banker_request else None,
            "banker_request_contrast": self.banker_request_contrast.to_dict() if self.banker_request_contrast else None,
            "banker_request_delta_callout": self.banker_request_delta_callout,
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


def build_banker_request_gallery(request_reports: list[BankerRequestReport]) -> BankerRequestGallery:
    if len(request_reports) < 2:
        raise ValueError("banker request gallery needs at least two request inputs")

    granted = sum(1 for report in request_reports if report.analysis.granted)
    denied = len(request_reports) - granted
    highlights: list[str] = []

    if granted and denied:
        highlights.append(
            f"This gallery contrasts {granted} granted request{'s' if granted != 1 else ''} with {denied} denied request{'s' if denied != 1 else ''}."
        )
    elif granted:
        highlights.append("Every request in this gallery is safe to grant.")
    else:
        highlights.append("Every request in this gallery is denied before or during the safety check.")

    for report in request_reports:
        label = Path(report.source).name
        analysis = report.analysis
        request_text = _format_resource_vector(analysis.request)
        if analysis.granted:
            highlights.append(
                f"{label}: {analysis.process} requesting {request_text} stays safe with sequence {_format_process_list(analysis.safe_sequence)}."
            )
        else:
            highlights.append(
                f"{label}: {analysis.process} requesting {request_text} is denied because {analysis.reason}; the trial leaves no runnable process and blocking is {_format_blocking_summary(analysis.blocking)}."
            )

    delta_callouts = _build_banker_request_delta_callouts(request_reports)

    return BankerRequestGallery(
        request_reports=request_reports,
        decision_totals={"granted": granted, "denied": denied},
        highlights=highlights,
        delta_callouts=delta_callouts,
    )


def _build_banker_request_delta_callouts(request_reports: list[BankerRequestReport]) -> list[dict[str, object]]:
    granted_reports = [report for report in request_reports if report.analysis.granted]
    denied_reports = [report for report in request_reports if not report.analysis.granted]
    if not granted_reports or not denied_reports:
        return []

    callouts: list[dict[str, object]] = []
    for denied_report in denied_reports:
        granted_report = _select_reference_granted_report(denied_report, granted_reports)
        granted_analysis = granted_report.analysis
        denied_analysis = denied_report.analysis
        granted_label = Path(granted_report.source).name
        denied_label = Path(denied_report.source).name
        granted_available = _evaluated_available(granted_analysis)
        denied_available = _evaluated_available(denied_analysis)
        granted_consumed = _consumed_slack(_starting_available(granted_analysis), granted_available)
        denied_consumed = _consumed_slack(_starting_available(denied_analysis), denied_available)
        shared_consumed, granted_only_consumed, denied_only_consumed = _split_shared_resource_deltas(
            granted_consumed,
            denied_consumed,
        )
        granted_first_runnable = _first_runnable_processes(granted_analysis)
        denied_first_runnable = _first_runnable_processes(denied_analysis)
        lost_runnable_options = sorted(set(granted_first_runnable) - set(denied_first_runnable))

        shared_text = _format_resource_vector(shared_consumed) or "none"
        granted_only_text = _format_resource_vector(granted_only_consumed) or "none"
        denied_only_text = _format_resource_vector(denied_only_consumed) or "none"
        lost_runnable_text = _format_process_list(lost_runnable_options)
        summary_parts = [
            f"{granted_label} keeps the path grantable after spending shared slack {shared_text}",
        ]
        if granted_only_consumed:
            summary_parts.append(f"plus granted-only slack {granted_only_text}")
        summary_parts.append(
            f"and still leaves first runnable set {_format_process_list(granted_first_runnable)}"
        )
        summary_parts.append(
            f"whereas {denied_label} leaves first runnable set {_format_process_list(denied_first_runnable)}"
        )
        if denied_only_consumed:
            summary_parts.append(f"after denied-only slack {denied_only_text} disappears")
        if lost_runnable_options:
            summary_parts.append(
                f"so runnable option{'s' if len(lost_runnable_options) != 1 else ''} {lost_runnable_text} disappear{'s' if len(lost_runnable_options) == 1 else ''}"
            )
        summary_parts.append(f"and blocking becomes {_format_blocking_summary(denied_analysis.blocking)}")

        callouts.append(
            {
                "granted_source": granted_report.source,
                "denied_source": denied_report.source,
                "shared_slack_spent": shared_consumed,
                "granted_only_slack_spent": granted_only_consumed,
                "denied_only_slack_spent": denied_only_consumed,
                "granted_first_runnable": granted_first_runnable,
                "denied_first_runnable": denied_first_runnable,
                "lost_runnable_options": lost_runnable_options,
                "denied_blocking": denied_analysis.blocking,
                "summary": "; ".join(summary_parts) + ".",
            }
        )
    return callouts


def _select_reference_granted_report(
    denied_report: BankerRequestReport,
    granted_reports: list[BankerRequestReport],
) -> BankerRequestReport:
    denied_analysis = denied_report.analysis
    denied_available = _starting_available(denied_analysis)

    def score(report: BankerRequestReport) -> tuple[int, int, int]:
        granted_analysis = report.analysis
        granted_available = _starting_available(granted_analysis)
        shared_resources = len(
            set(granted_available).intersection(denied_available)
        )
        shared_processes = len(
            set(granted_analysis.allocation).intersection(denied_analysis.allocation)
        )
        distance = sum(
            abs(granted_available.get(resource, 0) - denied_available.get(resource, 0))
            for resource in stable_unique(list(granted_available) + list(denied_available))
        )
        return (shared_resources, shared_processes, -distance)

    return max(granted_reports, key=score)


def _evaluated_available(analysis: BankerRequestAnalysis) -> dict[str, int]:
    return analysis.trial_available if analysis.trial_available is not None else analysis.available


def _starting_available(analysis: BankerRequestAnalysis) -> dict[str, int]:
    if not analysis.granted:
        return analysis.available
    return {
        resource: int(analysis.available.get(resource, 0)) + int(analysis.request.get(resource, 0))
        for resource in stable_unique(list(analysis.available) + list(analysis.request))
    }


def _consumed_slack(
    before: dict[str, int],
    after: dict[str, int],
) -> dict[str, int]:
    consumed: dict[str, int] = {}
    for resource in stable_unique(list(before) + list(after)):
        delta = before.get(resource, 0) - after.get(resource, 0)
        if delta > 0:
            consumed[resource] = delta
    return consumed


def _split_shared_resource_deltas(
    granted_consumed: dict[str, int],
    denied_consumed: dict[str, int],
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    shared: dict[str, int] = {}
    granted_only: dict[str, int] = {}
    denied_only: dict[str, int] = {}
    for resource in stable_unique(list(granted_consumed) + list(denied_consumed)):
        granted_value = granted_consumed.get(resource, 0)
        denied_value = denied_consumed.get(resource, 0)
        common = min(granted_value, denied_value)
        if common > 0:
            shared[resource] = common
        if granted_value > common:
            granted_only[resource] = granted_value - common
        if denied_value > common:
            denied_only[resource] = denied_value - common
    return shared, granted_only, denied_only


def _first_runnable_processes(analysis: BankerRequestAnalysis) -> list[str]:
    if not analysis.trace_steps:
        return []
    return analysis.trace_steps[0].runnable_processes


def build_detection_avoidance_dashboard(
    wait_for: WaitForAnalysis,
    allocation: AllocationAnalysis,
    banker_safety: BankerSafetyAnalysis,
    banker_request: BankerRequestAnalysis | None,
    banker_request_contrast: BankerRequestAnalysis | None = None,
    banker_request_source: str | None = None,
    banker_request_contrast_source: str | None = None,
) -> DetectionAvoidanceDashboard:
    wait_takeaway = (
        f"Wait-for detection finds a concrete cycle among {', '.join(wait_for.blocked_processes)}."
        if wait_for.deadlocked and wait_for.blocked_processes
        else "Wait-for detection does not find a cycle in this process-only view."
    )
    allocation_takeaway = (
        "Resource-allocation detection still leaves "
        + ", ".join(allocation.deadlocked_processes)
        + (
            f" blocked after only {', '.join(allocation.finish_order)} can finish."
            if allocation.finish_order
            else " blocked with no runnable finish order."
        )
        if allocation.deadlocked and allocation.deadlocked_processes
        else "Resource-allocation detection finds a safe finish order once currently runnable processes release what they hold."
    )
    banker_takeaway = (
        f"Banker's avoidance keeps the system safe with sequence {', '.join(banker_safety.safe_sequence)}."
        if banker_safety.safe
        else "Banker's safety check shows the state is already unsafe, so avoidance would reject further risky moves."
    )
    takeaways = [wait_takeaway, allocation_takeaway, banker_takeaway]
    banker_request_delta_callout: dict[str, object] | None = None
    if banker_request is not None:
        request_text = _format_resource_vector(banker_request.request)
        request_sequence = _format_process_list(banker_request.safe_sequence)
        takeaways.append(
            (
                f"The sample request from {banker_request.process} ({request_text}) is granted and still leaves safe sequence {request_sequence}."
                if banker_request.granted
                else f"The sample request from {banker_request.process} ({request_text}) is denied because {banker_request.reason}."
            )
        )
    if banker_request is not None and banker_request_contrast is not None:
        request_reports = [
            BankerRequestReport(
                source=banker_request_source or "banker-request-primary.json",
                analysis=banker_request,
            ),
            BankerRequestReport(
                source=banker_request_contrast_source or "banker-request-contrast.json",
                analysis=banker_request_contrast,
            ),
        ]
        delta_callouts = _build_banker_request_delta_callouts(request_reports)
        if delta_callouts:
            banker_request_delta_callout = delta_callouts[0]
            takeaways.append(str(banker_request_delta_callout["summary"]))
    return DetectionAvoidanceDashboard(
        wait_for=wait_for,
        allocation=allocation,
        banker_safety=banker_safety,
        banker_request=banker_request,
        banker_request_contrast=banker_request_contrast,
        banker_request_delta_callout=banker_request_delta_callout,
        key_takeaways=takeaways,
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


def _wrap_svg_lines(text: str, max_chars: int = 44) -> list[str]:
    raw_lines = text.splitlines() or [text]
    wrapped: list[str] = []
    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(
            textwrap.wrap(
                line,
                width=max_chars,
                break_long_words=False,
                break_on_hyphens=False,
            )
            or [line]
        )
    return wrapped or [""]


def _svg_multiline_text(
    x: float,
    y: float,
    lines: list[str],
    class_name: str = "tiny",
    anchor: str = "start",
    line_height: float = 18.0,
) -> str:
    rendered: list[str] = []
    current_y = y
    for line in lines:
        if line:
            rendered.append(_svg_text(x, current_y, line, class_name, anchor=anchor))
        current_y += line_height
    return "\n".join(rendered)


def _svg_panel(
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body_lines: list[str],
    *,
    tone_class: str = "panel",
    body_class: str = "tiny",
) -> str:
    body = _svg_multiline_text(x + 14, y + 50, body_lines, body_class, anchor="start", line_height=17.0)
    return "\n".join(
        [
            f'<rect class="{tone_class}" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="18" />',
            _svg_text(x + 14, y + 28, title, "section-title", anchor="start"),
            body,
        ]
    )


def _svg_metric_card(x: float, y: float, width: float, height: float, label: str, value: str) -> str:
    lines = _wrap_svg_lines(value, max(14, min(28, int((width - 28) / 7))))
    body = _svg_multiline_text(x + 14, y + 52, lines, "metric-value", anchor="start", line_height=19.0)
    return "\n".join(
        [
            f'<rect class="metric-card" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" rx="18" />',
            _svg_text(x + 14, y + 28, label, "section-title", anchor="start"),
            body,
        ]
    )


def _trace_step_card_lines(step: BankerTraceStep) -> list[str]:
    return [
        f"Runnable: {_format_process_list(step.runnable_processes)}",
        f"Work before: {_format_resource_vector(step.work_before)}",
        f"Need: {_format_resource_vector(step.need)}",
        f"Release: {_format_resource_vector(step.allocation_released)}",
        f"Work after: {_format_resource_vector(step.work_after)}",
    ]


def _trace_step_card_height(step: BankerTraceStep, width: float) -> float:
    max_chars = max(28, min(72, int((width - 28) / 6.7)))
    line_count = sum(len(_wrap_svg_lines(line, max_chars)) for line in _trace_step_card_lines(step))
    return 54.0 + line_count * 17.0 + 14.0


def render_banker_safety_svg(analysis: BankerSafetyAnalysis, source_label: str) -> str:
    diagram_id = _svg_id(f"banker-safety-{source_label}")
    width = 1120.0
    outer_x = 24.0
    outer_y = 24.0
    inner_width = width - 48.0
    metric_gap = 14.0
    metric_width = (inner_width - metric_gap * 3) / 4
    metric_height = 92.0
    summary_y = 112.0
    need_lines = [
        f"{process}: {_format_resource_vector(analysis.need[process]) or 'none'}"
        for process in analysis.processes
    ]
    blocking_lines = _wrap_svg_lines(
        _format_blocking_summary(analysis.blocking)
        if analysis.blocking
        else "No blocking shortages remain in the current state.",
        48,
    )
    note_lines = _wrap_svg_lines(
        "Question answered: is the current state safe before any new request is granted?",
        42,
    )
    left_panel_height = 66.0 + len(need_lines) * 17.0
    right_panel_body_lines = note_lines + [""] + ["Blocking summary:"] + blocking_lines
    right_panel_height = 66.0 + len(right_panel_body_lines) * 17.0
    detail_height = max(left_panel_height, right_panel_height)
    detail_y = summary_y + metric_height + 20.0
    trace_y = detail_y + detail_height + 20.0
    trace_card_width = inner_width
    trace_cards: list[tuple[BankerTraceStep | None, float]] = []
    if analysis.trace_steps:
        for step in analysis.trace_steps:
            trace_cards.append((step, _trace_step_card_height(step, trace_card_width)))
    else:
        trace_cards.append((None, 112.0))

    trace_total_height = sum(height for _, height in trace_cards) + max(len(trace_cards) - 1, 0) * 14.0
    height = trace_y + trace_total_height + 48.0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="{diagram_id}-title {diagram_id}-desc">',
        f'  <title id="{diagram_id}-title">Banker\'s algorithm safety visualization for {html.escape(source_label)}</title>',
        f'  <desc id="{diagram_id}-desc">A static summary of the Banker\'s algorithm safety state, including the safe sequence and per-step work evolution.</desc>',
        '  <style>',
        '    .bg { fill: #f8fafc; }',
        '    .card { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.5; }',
        '    .metric-card { fill: #eff6ff; stroke: #bfdbfe; stroke-width: 1.2; }',
        '    .panel { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.2; }',
        '    .accent-panel { fill: #f8fafc; stroke: #cbd5e1; stroke-width: 1.2; }',
        '    .trace-card { fill: #fff7ed; stroke: #fdba74; stroke-width: 1.2; }',
        '    .label { fill: #0f172a; font-family: Arial, sans-serif; font-size: 16px; font-weight: 700; }',
        '    .section-title { fill: #0f172a; font-family: Arial, sans-serif; font-size: 13px; font-weight: 700; }',
        '    .muted { fill: #475569; font-family: Arial, sans-serif; font-size: 13px; }',
        '    .tiny { fill: #475569; font-family: Arial, sans-serif; font-size: 12px; }',
        '    .metric-value { fill: #0f172a; font-family: Arial, sans-serif; font-size: 16px; font-weight: 700; }',
        '  </style>',
        f'  <rect class="bg" x="0" y="0" width="{width:.0f}" height="{height:.0f}" rx="24" />',
        f'  <rect class="card" x="{outer_x:.0f}" y="{outer_y:.0f}" width="{width - 48:.0f}" height="{height - 48:.0f}" rx="20" />',
        _svg_text(52, 58, "Banker's algorithm safety view", "label", anchor="start"),
        _svg_text(52, 82, f"Source: {source_label}", "muted", anchor="start"),
        _svg_text(width - 52, 58, "safe state" if analysis.safe else "unsafe state", "muted", anchor="end"),
        _svg_metric_card(outer_x + 18, summary_y, metric_width, metric_height, "State", "safe" if analysis.safe else "unsafe"),
        _svg_metric_card(
            outer_x + 18 + (metric_width + metric_gap),
            summary_y,
            metric_width,
            metric_height,
            "Safe sequence",
            _format_process_list(analysis.safe_sequence),
        ),
        _svg_metric_card(
            outer_x + 18 + (metric_width + metric_gap) * 2,
            summary_y,
            metric_width,
            metric_height,
            "Final work",
            _format_resource_vector(analysis.work) or "none",
        ),
        _svg_metric_card(
            outer_x + 18 + (metric_width + metric_gap) * 3,
            summary_y,
            metric_width,
            metric_height,
            "Unfinished",
            _format_process_list(analysis.unfinished_processes),
        ),
        _svg_panel(outer_x + 18, detail_y, 360.0, detail_height, "Need matrix", need_lines, tone_class="panel"),
        _svg_panel(
            outer_x + 392,
            detail_y,
            width - outer_x - 392 - 42,
            detail_height,
            "Safety takeaway",
            right_panel_body_lines,
            tone_class="accent-panel",
        ),
        _svg_text(outer_x + 18, trace_y - 10, "Trace steps", "section-title", anchor="start"),
    ]

    current_y = trace_y
    for step, card_height in trace_cards:
        x = outer_x + 18
        if step is None:
            parts.append(
                _svg_panel(
                    x,
                    current_y,
                    trace_card_width,
                    card_height,
                    "No runnable step",
                    ["No process can finish with the current work vector."],
                    tone_class="trace-card",
                )
            )
        else:
            max_chars = max(28, min(72, int((trace_card_width - 28) / 6.7)))
            body_lines: list[str] = []
            for line in _trace_step_card_lines(step):
                body_lines.extend(_wrap_svg_lines(line, max_chars))
            parts.append(
                _svg_panel(
                    x,
                    current_y,
                    trace_card_width,
                    card_height,
                    f"Step {step.step}: run {step.process}",
                    body_lines,
                    tone_class="trace-card",
                )
            )
        current_y += card_height + 14.0

    parts.append("</svg>")
    return "\n".join(parts)


def render_banker_safety_html(analysis: BankerSafetyAnalysis, source_label: str) -> str:
    svg = render_banker_safety_svg(analysis, source_label).strip()
    need_rows = "\n".join(
        f"<tr><td><code>{html.escape(process)}</code></td><td><code>{html.escape(_format_resource_vector(analysis.need[process]) or 'none')}</code></td></tr>"
        for process in analysis.processes
    )
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Banker's algorithm safety view</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 32px 24px 56px; }}
    .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 18px; padding: 20px; margin-top: 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .metric {{ background: #eff6ff; border-radius: 14px; padding: 14px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }}
    code {{ font-family: \"SFMono-Regular\", Consolas, monospace; font-size: 0.95em; }}
    .table-wrap {{ overflow-x: auto; }}
    svg {{ width: 100%; height: auto; display: block; }}
  </style>
</head>
<body>
  <main>
    <section class=\"card\">
      <h1>Banker's algorithm safety view</h1>
      <p>This artifact answers whether the current state is safe before any new request is granted.</p>
      <div class=\"grid\">
        <div class=\"metric\"><strong>Source</strong><br /><code>{html.escape(source_label)}</code></div>
        <div class=\"metric\"><strong>State</strong><br />{'safe' if analysis.safe else 'unsafe'}</div>
        <div class=\"metric\"><strong>Safe sequence</strong><br /><code>{html.escape(_format_process_list(analysis.safe_sequence))}</code></div>
        <div class=\"metric\"><strong>Final work</strong><br /><code>{html.escape(_format_resource_vector(analysis.work) or 'none')}</code></div>
      </div>
    </section>

    <section class=\"card\">{svg}</section>

    <section class=\"card\">
      <h2>Need matrix</h2>
      <div class=\"table-wrap\">
        <table>
          <thead><tr><th>Process</th><th>Remaining need</th></tr></thead>
          <tbody>{need_rows}</tbody>
        </table>
      </div>
      <p><strong>Blocking summary:</strong> <code>{html.escape(_format_blocking_summary(analysis.blocking))}</code></p>
      <div class=\"table-wrap\">{_render_trace_steps_html_table(analysis.trace_steps)}</div>
    </section>
  </main>
</body>
</html>
"""


def render_banker_request_svg(analysis: BankerRequestAnalysis, source_label: str) -> str:
    diagram_id = _svg_id(f"banker-request-{source_label}")
    width = 1120.0
    outer_x = 24.0
    outer_y = 24.0
    inner_width = width - 48.0
    metric_gap = 14.0
    metric_width = (inner_width - metric_gap * 3) / 4
    metric_height = 92.0
    summary_y = 112.0
    detail_y = summary_y + metric_height + 20.0
    request_lines = _wrap_svg_lines(f"Process {analysis.process}: {_format_resource_vector(analysis.request)}", 40)
    reason_lines = _wrap_svg_lines(analysis.reason, 48)
    blocking_lines = _wrap_svg_lines(
        _format_blocking_summary(analysis.blocking)
        if analysis.blocking
        else "No blocking shortages remain after the evaluated trial.",
        48,
    )
    left_panel_height = 66.0 + len(request_lines) * 17.0
    right_panel_body_lines = (
        _wrap_svg_lines("Question answered: can this request be granted while keeping the system safe?", 48)
        + [""]
        + ["Reason:"]
        + reason_lines
        + [""]
        + ["Blocking summary:"]
        + blocking_lines
    )
    right_panel_height = 66.0 + len(right_panel_body_lines) * 17.0
    detail_height = max(left_panel_height, right_panel_height)
    trace_y = detail_y + detail_height + 20.0
    trace_card_width = inner_width
    trace_cards: list[tuple[BankerTraceStep | None, float]] = []
    if analysis.trace_steps:
        for step in analysis.trace_steps:
            trace_cards.append((step, _trace_step_card_height(step, trace_card_width)))
    else:
        trace_cards.append((None, 112.0))

    trace_total_height = sum(height for _, height in trace_cards) + max(len(trace_cards) - 1, 0) * 14.0
    height = trace_y + trace_total_height + 48.0
    evaluated_available = analysis.trial_available if analysis.trial_available is not None else analysis.available
    available_label = "Trial available" if analysis.trial_available is not None else "Current available"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="{diagram_id}-title {diagram_id}-desc">',
        f'  <title id="{diagram_id}-title">Banker\'s algorithm request visualization for {html.escape(source_label)}</title>',
        f'  <desc id="{diagram_id}-desc">A static summary of the evaluated Banker\'s algorithm request, including the trial decision and per-step work evolution.</desc>',
        '  <style>',
        '    .bg { fill: #f8fafc; }',
        '    .card { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.5; }',
        '    .metric-card { fill: #ecfeff; stroke: #a5f3fc; stroke-width: 1.2; }',
        '    .panel { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1.2; }',
        '    .accent-panel { fill: #f8fafc; stroke: #cbd5e1; stroke-width: 1.2; }',
        '    .trace-card { fill: #fefce8; stroke: #fde68a; stroke-width: 1.2; }',
        '    .label { fill: #0f172a; font-family: Arial, sans-serif; font-size: 16px; font-weight: 700; }',
        '    .section-title { fill: #0f172a; font-family: Arial, sans-serif; font-size: 13px; font-weight: 700; }',
        '    .muted { fill: #475569; font-family: Arial, sans-serif; font-size: 13px; }',
        '    .tiny { fill: #475569; font-family: Arial, sans-serif; font-size: 12px; }',
        '    .metric-value { fill: #0f172a; font-family: Arial, sans-serif; font-size: 16px; font-weight: 700; }',
        '  </style>',
        f'  <rect class="bg" x="0" y="0" width="{width:.0f}" height="{height:.0f}" rx="24" />',
        f'  <rect class="card" x="{outer_x:.0f}" y="{outer_y:.0f}" width="{width - 48:.0f}" height="{height - 48:.0f}" rx="20" />',
        _svg_text(52, 58, "Banker's algorithm request trial", "label", anchor="start"),
        _svg_text(52, 82, f"Source: {source_label}", "muted", anchor="start"),
        _svg_text(width - 52, 58, "granted" if analysis.granted else "denied", "muted", anchor="end"),
        _svg_metric_card(outer_x + 18, summary_y, metric_width, metric_height, "Decision", "granted" if analysis.granted else "denied"),
        _svg_metric_card(
            outer_x + 18 + (metric_width + metric_gap),
            summary_y,
            metric_width,
            metric_height,
            "Safe after trial",
            "yes" if analysis.safe else "no",
        ),
        _svg_metric_card(
            outer_x + 18 + (metric_width + metric_gap) * 2,
            summary_y,
            metric_width,
            metric_height,
            "Safe sequence",
            _format_process_list(analysis.safe_sequence),
        ),
        _svg_metric_card(
            outer_x + 18 + (metric_width + metric_gap) * 3,
            summary_y,
            metric_width,
            metric_height,
            available_label,
            _format_resource_vector(evaluated_available) or "none",
        ),
        _svg_panel(outer_x + 18, detail_y, 360.0, detail_height, "Request", request_lines, tone_class="panel"),
        _svg_panel(
            outer_x + 392,
            detail_y,
            width - outer_x - 392 - 42,
            detail_height,
            "Decision takeaway",
            right_panel_body_lines,
            tone_class="accent-panel",
        ),
        _svg_text(outer_x + 18, trace_y - 10, "Trial safety trace", "section-title", anchor="start"),
    ]

    current_y = trace_y
    for step, card_height in trace_cards:
        x = outer_x + 18
        if step is None:
            parts.append(
                _svg_panel(
                    x,
                    current_y,
                    trace_card_width,
                    card_height,
                    "No runnable step",
                    ["No process can finish after applying the trial request."],
                    tone_class="trace-card",
                )
            )
        else:
            max_chars = max(28, min(72, int((trace_card_width - 28) / 6.7)))
            body_lines: list[str] = []
            for line in _trace_step_card_lines(step):
                body_lines.extend(_wrap_svg_lines(line, max_chars))
            parts.append(
                _svg_panel(
                    x,
                    current_y,
                    trace_card_width,
                    card_height,
                    f"Step {step.step}: run {step.process}",
                    body_lines,
                    tone_class="trace-card",
                )
            )
        current_y += card_height + 14.0

    parts.append("</svg>")
    return "\n".join(parts)


def render_banker_request_html(analysis: BankerRequestAnalysis, source_label: str) -> str:
    svg = render_banker_request_svg(analysis, source_label).strip()
    evaluated_available = analysis.trial_available if analysis.trial_available is not None else analysis.available
    available_label = "Trial available vector" if analysis.trial_available is not None else "Current available vector"
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Banker's algorithm request trial</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1240px; margin: 0 auto; padding: 32px 24px 56px; }}
    .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 18px; padding: 20px; margin-top: 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .metric {{ background: #ecfeff; border-radius: 14px; padding: 14px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }}
    code {{ font-family: \"SFMono-Regular\", Consolas, monospace; font-size: 0.95em; }}
    .table-wrap {{ overflow-x: auto; }}
    svg {{ width: 100%; height: auto; display: block; }}
  </style>
</head>
<body>
  <main>
    <section class=\"card\">
      <h1>Banker's algorithm request trial</h1>
      <p>This artifact answers whether one concrete request should be granted while keeping the system safe.</p>
      <div class=\"grid\">
        <div class=\"metric\"><strong>Source</strong><br /><code>{html.escape(source_label)}</code></div>
        <div class=\"metric\"><strong>Process</strong><br /><code>{html.escape(analysis.process)}</code></div>
        <div class=\"metric\"><strong>Request</strong><br /><code>{html.escape(_format_resource_vector(analysis.request))}</code></div>
        <div class=\"metric\"><strong>Decision</strong><br />{'granted' if analysis.granted else 'denied'}</div>
      </div>
    </section>

    <section class=\"card\">{svg}</section>

    <section class=\"card\">
      <h2>Trial details</h2>
      <p><strong>Reason:</strong> {html.escape(analysis.reason)}</p>
      <p><strong>Safe sequence:</strong> <code>{html.escape(_format_process_list(analysis.safe_sequence))}</code></p>
      <p><strong>{available_label}:</strong> <code>{html.escape(_format_resource_vector(evaluated_available) or 'none')}</code></p>
      <p><strong>Blocking summary:</strong> <code>{html.escape(_format_blocking_summary(analysis.blocking))}</code></p>
      <div class=\"table-wrap\">{_render_trace_steps_html_table(analysis.trace_steps)}</div>
    </section>
  </main>
</body>
</html>
"""


def render_banker_request_gallery_markdown(gallery: BankerRequestGallery) -> str:
    lines = [
        "# Banker's algorithm request gallery",
        "",
        f"- Request count: {len(gallery.request_reports)}",
        f"- Granted: {gallery.decision_totals['granted']}",
        f"- Denied: {gallery.decision_totals['denied']}",
        "",
        "## Highlights",
        "",
    ]
    lines.extend(f"- {highlight}" for highlight in gallery.highlights)
    if gallery.delta_callouts:
        lines.extend(["", "## Delta callouts", ""])
        lines.extend(f"- {callout['summary']}" for callout in gallery.delta_callouts)
    lines.extend(
        [
            "",
            "## Request comparison",
            "",
            "| Source | Process | Request | Decision | First runnable set | Safe sequence | Evaluated available | Blocking |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for report in gallery.request_reports:
        analysis = report.analysis
        evaluated_available = analysis.trial_available if analysis.trial_available is not None else analysis.available
        lines.append(
            f"| `{Path(report.source).name}` | `{analysis.process}` | `{_format_resource_vector(analysis.request)}` | {'granted' if analysis.granted else 'denied'} | `{_first_runnable_set(analysis)}` | `{_format_process_list(analysis.safe_sequence)}` | `{_format_resource_vector(evaluated_available)}` | `{_format_blocking_summary(analysis.blocking)}` |"
        )
    return "\n".join(lines) + "\n"


def render_banker_request_gallery_html(gallery: BankerRequestGallery) -> str:
    request_cards: list[str] = []
    for report in gallery.request_reports:
        analysis = report.analysis
        evaluated_available = analysis.trial_available if analysis.trial_available is not None else analysis.available
        label = Path(report.source).name
        svg = render_banker_request_svg(analysis, report.source).strip()
        request_cards.append(
            f"""
      <section class=\"card request-card {'granted' if analysis.granted else 'denied'}\">
        <h2>{html.escape(label)}</h2>
        <p><strong>Decision:</strong> {'granted' if analysis.granted else 'denied'}</p>
        <p><strong>Process:</strong> <code>{html.escape(analysis.process)}</code></p>
        <p><strong>Request:</strong> <code>{html.escape(_format_resource_vector(analysis.request))}</code></p>
        <p><strong>Reason:</strong> {html.escape(analysis.reason)}</p>
        <p><strong>First runnable set:</strong> <code>{html.escape(_first_runnable_set(analysis))}</code></p>
        <p><strong>Safe sequence:</strong> <code>{html.escape(_format_process_list(analysis.safe_sequence))}</code></p>
        <p><strong>Evaluated available:</strong> <code>{html.escape(_format_resource_vector(evaluated_available))}</code></p>
        <p><strong>Blocking:</strong> <code>{html.escape(_format_blocking_summary(analysis.blocking))}</code></p>
        {svg}
      </section>
""".rstrip()
        )

    request_rows = "\n".join(
        "<tr>"
        f"<td><code>{html.escape(Path(report.source).name)}</code></td>"
        f"<td><code>{html.escape(report.analysis.process)}</code></td>"
        f"<td><code>{html.escape(_format_resource_vector(report.analysis.request))}</code></td>"
        f"<td>{'granted' if report.analysis.granted else 'denied'}</td>"
        f"<td><code>{html.escape(_first_runnable_set(report.analysis))}</code></td>"
        f"<td><code>{html.escape(_format_process_list(report.analysis.safe_sequence))}</code></td>"
        f"<td><code>{html.escape(_format_resource_vector(report.analysis.trial_available if report.analysis.trial_available is not None else report.analysis.available))}</code></td>"
        f"<td><code>{html.escape(_format_blocking_summary(report.analysis.blocking))}</code></td>"
        "</tr>"
        for report in gallery.request_reports
    )
    highlight_items = "\n".join(f"<li>{html.escape(highlight)}</li>" for highlight in gallery.highlights)
    delta_items = "\n".join(
        f"<li>{html.escape(str(callout['summary']))}</li>" for callout in gallery.delta_callouts
    )
    delta_section = (
        f"""<section class=\"card\">
      <h2>Delta callouts</h2>
      <p>This section focuses on what immediate slack and runnable options disappear when a safe request turns into an unsafe one.</p>
      <ul>{delta_items}</ul>
    </section>
""".rstrip()
        if gallery.delta_callouts
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Banker's algorithm request gallery</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1380px; margin: 0 auto; padding: 32px 24px 56px; }}
    .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 18px; padding: 20px; margin-top: 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .request-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(620px, 1fr)); gap: 20px; align-items: start; }}
    .metric {{ background: #eff6ff; border-radius: 14px; padding: 14px; }}
    .request-card.granted {{ border-color: #86efac; }}
    .request-card.denied {{ border-color: #fca5a5; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }}
    code {{ font-family: \"SFMono-Regular\", Consolas, monospace; font-size: 0.95em; }}
    .table-wrap {{ overflow-x: auto; }}
    svg {{ width: 100%; height: auto; display: block; margin-top: 16px; }}
  </style>
</head>
<body>
  <main>
    <section class=\"card\">
      <h1>Banker's algorithm request gallery</h1>
      <p>This gallery compares multiple request trials side by side so granted and denied paths can be explained in one glance.</p>
      <div class=\"grid\">
        <div class=\"metric\"><strong>Requests</strong><br />{len(gallery.request_reports)}</div>
        <div class=\"metric\"><strong>Granted</strong><br />{gallery.decision_totals['granted']}</div>
        <div class=\"metric\"><strong>Denied</strong><br />{gallery.decision_totals['denied']}</div>
      </div>
      <h2>Highlights</h2>
      <ul>{highlight_items}</ul>
    </section>{f'\n\n    {delta_section}' if delta_section else ''}

    <section class=\"card\">
      <h2>Comparison table</h2>
      <div class=\"table-wrap\">
        <table>
          <thead><tr><th>Source</th><th>Process</th><th>Request</th><th>Decision</th><th>First runnable set</th><th>Safe sequence</th><th>Evaluated available</th><th>Blocking</th></tr></thead>
          <tbody>{request_rows}</tbody>
        </table>
      </div>
    </section>

    <section class=\"request-grid\">
      {' '.join(request_cards)}
    </section>
  </main>
</body>
</html>
"""


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


def _format_process_list(processes: list[str]) -> str:
    return ", ".join(processes) if processes else "none"


def _format_blocking_summary(blocking: dict[str, dict[str, int]]) -> str:
    if not blocking:
        return "none"
    parts: list[str] = []
    for process, shortage in blocking.items():
        shortage_text = _format_resource_vector(shortage) if shortage else "none"
        parts.append(f"{process}: {shortage_text}")
    return "; ".join(parts)


def _first_runnable_set(analysis: BankerRequestAnalysis) -> str:
    if not analysis.trace_steps:
        return "none"
    return _format_process_list(analysis.trace_steps[0].runnable_processes)


def _render_trace_steps_html_table(steps: list[BankerTraceStep]) -> str:
    if not steps:
        return "<p>No runnable trace steps were found for this state.</p>"
    rows = "\n".join(
        "<tr>"
        f"<td>{step.step}</td>"
        f"<td><code>{html.escape(step.process)}</code></td>"
        f"<td><code>{html.escape(_format_process_list(step.runnable_processes))}</code></td>"
        f"<td><code>{html.escape(_format_resource_vector(step.work_before))}</code></td>"
        f"<td><code>{html.escape(_format_resource_vector(step.need))}</code></td>"
        f"<td><code>{html.escape(_format_resource_vector(step.allocation_released))}</code></td>"
        f"<td><code>{html.escape(_format_resource_vector(step.work_after))}</code></td>"
        "</tr>"
        for step in steps
    )
    return (
        "<table>"
        "<thead><tr><th>Step</th><th>Chosen process</th><th>Runnable set</th><th>Work before</th><th>Remaining need</th><th>Allocation released</th><th>Work after</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def render_detection_avoidance_markdown(
    dashboard: DetectionAvoidanceDashboard,
    wait_source: str,
    allocation_source: str,
    banker_source: str,
    banker_request_source: str | None,
    banker_request_contrast_source: str | None,
) -> str:
    lines = [
        "# Deadlock detection vs avoidance dashboard",
        "",
        f"- Wait-for graph source: `{wait_source}`",
        f"- Allocation snapshot source: `{allocation_source}`",
        f"- Banker's safety source: `{banker_source}`",
    ]
    if banker_request_source:
        lines.append(f"- Banker's request source: `{banker_request_source}`")
    if banker_request_contrast_source:
        lines.append(f"- Banker's contrast request source: `{banker_request_contrast_source}`")
    lines.extend(["", "## Key takeaways", ""])
    lines.extend(f"- {takeaway}" for takeaway in dashboard.key_takeaways)
    lines.extend(
        [
            "",
            "## Detection models",
            "",
            "### Wait-for graph",
            "- Question answered: is there already a cycle among the waiting processes?",
            f"- Deadlocked: {'yes' if dashboard.wait_for.deadlocked else 'no'}",
            f"- Cycle: `{ ' -> '.join(dashboard.wait_for.cycle) if dashboard.wait_for.cycle else 'none' }`",
            f"- Blocked processes: `{_format_process_list(dashboard.wait_for.blocked_processes)}`",
            "",
            "### Resource-allocation snapshot",
            "- Question answered: can the current work vector still finish anyone and free resources?",
            f"- Deadlocked: {'yes' if dashboard.allocation.deadlocked else 'no'}",
            f"- Finish order: `{_format_process_list(dashboard.allocation.finish_order)}`",
            f"- Deadlocked processes: `{_format_process_list(dashboard.allocation.deadlocked_processes)}`",
            f"- Blocking summary: `{_format_blocking_summary(dashboard.allocation.blocking)}`",
            "",
            "## Avoidance model",
            "",
            "### Banker's safety check",
            "- Question answered: is the current state safe before any new request is granted?",
            f"- Safe: {'yes' if dashboard.banker_safety.safe else 'no'}",
            f"- Safe sequence: `{_format_process_list(dashboard.banker_safety.safe_sequence)}`",
            f"- Final work: `{_format_resource_vector(dashboard.banker_safety.work)}`",
            f"- Blocking summary: `{_format_blocking_summary(dashboard.banker_safety.blocking)}`",
            "",
            "| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if dashboard.banker_safety.trace_steps:
        for step in dashboard.banker_safety.trace_steps:
            lines.append(
                f"| {step.step} | `{step.process}` | `{_format_process_list(step.runnable_processes)}` | `{_format_resource_vector(step.work_before)}` | `{_format_resource_vector(step.need)}` | `{_format_resource_vector(step.allocation_released)}` | `{_format_resource_vector(step.work_after)}` |"
            )
    else:
        lines.append("| 0 | none | none | n/a | n/a | n/a | n/a |")

    if dashboard.banker_request is not None:
        request = dashboard.banker_request
        lines.extend(
            [
                "",
                "### Banker's request trial",
                "- Question answered: should this new request be granted while keeping the system safe?",
                f"- Process: `{request.process}`",
                f"- Request: `{_format_resource_vector(request.request)}`",
                f"- Granted: {'yes' if request.granted else 'no'}",
                f"- Reason: {request.reason}",
                f"- Safe after trial: {'yes' if request.safe else 'no'}",
                f"- Safe sequence: `{_format_process_list(request.safe_sequence)}`",
                f"- Evaluated available vector: `{_format_resource_vector(request.trial_available if request.trial_available is not None else request.available)}`",
                f"- Blocking summary: `{_format_blocking_summary(request.blocking)}`",
                "",
                "| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        if request.trace_steps:
            for step in request.trace_steps:
                lines.append(
                    f"| {step.step} | `{step.process}` | `{_format_process_list(step.runnable_processes)}` | `{_format_resource_vector(step.work_before)}` | `{_format_resource_vector(step.need)}` | `{_format_resource_vector(step.allocation_released)}` | `{_format_resource_vector(step.work_after)}` |"
                )
        else:
            lines.append("| 0 | none | none | n/a | n/a | n/a | n/a |")

    if dashboard.banker_request_delta_callout is not None:
        callout = dashboard.banker_request_delta_callout
        lines.extend(
            [
                "",
                "### Granted vs denied request delta",
                "- Question answered: what immediate slack and runnable options disappear between the safe and unsafe request paths?",
                f"- Reference granted request: `{Path(str(callout['granted_source'])).name}`",
                f"- Contrast denied request: `{Path(str(callout['denied_source'])).name}`",
                f"- Shared slack spent: `{_format_resource_vector(callout['shared_slack_spent']) or 'none'}`",
                f"- Granted-only slack spent: `{_format_resource_vector(callout['granted_only_slack_spent']) or 'none'}`",
                f"- Denied-only slack spent: `{_format_resource_vector(callout['denied_only_slack_spent']) or 'none'}`",
                f"- Granted first runnable set: `{_format_process_list(callout['granted_first_runnable'])}`",
                f"- Denied first runnable set: `{_format_process_list(callout['denied_first_runnable'])}`",
                f"- Lost runnable options: `{_format_process_list(callout['lost_runnable_options'])}`",
                f"- Denied blocking: `{_format_blocking_summary(callout['denied_blocking'])}`",
                f"- Summary: {callout['summary']}",
            ]
        )

    return "\n".join(lines) + "\n"


def render_detection_avoidance_html(
    dashboard: DetectionAvoidanceDashboard,
    wait_source: str,
    allocation_source: str,
    banker_source: str,
    banker_request_source: str | None,
    banker_request_contrast_source: str | None,
    wait_edges: list[tuple[str, str]],
    allocation_available: dict[str, int],
    allocation_map: dict[str, dict[str, int]],
    request_map: dict[str, dict[str, int]],
) -> str:
    wait_svg = render_wait_graph_svg(dashboard.wait_for, wait_source, wait_edges).strip()
    allocation_svg = render_allocation_svg(
        dashboard.allocation,
        allocation_source,
        allocation_available,
        allocation_map,
        request_map,
    ).strip()
    banker_svg = render_banker_safety_svg(dashboard.banker_safety, banker_source).strip()
    takeaway_items = "\n".join(f"<li>{html.escape(takeaway)}</li>" for takeaway in dashboard.key_takeaways)
    request_metric = (
        f"<div class=\"metric\"><strong>Sample request</strong><br />{'granted' if dashboard.banker_request.granted else 'denied'}</div>"
        if dashboard.banker_request is not None
        else ""
    )
    banker_request_section = ""
    if dashboard.banker_request is not None:
        request = dashboard.banker_request
        banker_request_svg = render_banker_request_svg(request, banker_request_source or "banker-request")
        banker_request_delta_section = ""
        if dashboard.banker_request_delta_callout is not None:
            callout = dashboard.banker_request_delta_callout
            banker_request_delta_section = f"""
        <section class=\"card\">
          <h3>Granted vs denied request delta</h3>
          <p><strong>Question answered:</strong> what immediate slack and runnable options disappear between the safe and unsafe request paths?</p>
          <div class=\"grid compact-grid\">
            <div class=\"metric\"><strong>Reference granted request</strong><br /><code>{html.escape(Path(str(callout['granted_source'])).name)}</code></div>
            <div class=\"metric\"><strong>Contrast denied request</strong><br /><code>{html.escape(Path(str(callout['denied_source'])).name)}</code></div>
            <div class=\"metric\"><strong>Shared slack spent</strong><br /><code>{html.escape(_format_resource_vector(callout['shared_slack_spent']) or 'none')}</code></div>
            <div class=\"metric\"><strong>Granted-only slack spent</strong><br /><code>{html.escape(_format_resource_vector(callout['granted_only_slack_spent']) or 'none')}</code></div>
            <div class=\"metric\"><strong>Denied-only slack spent</strong><br /><code>{html.escape(_format_resource_vector(callout['denied_only_slack_spent']) or 'none')}</code></div>
            <div class=\"metric\"><strong>Lost runnable options</strong><br /><code>{html.escape(_format_process_list(callout['lost_runnable_options']))}</code></div>
          </div>
          <p><strong>Granted first runnable set:</strong> <code>{html.escape(_format_process_list(callout['granted_first_runnable']))}</code></p>
          <p><strong>Denied first runnable set:</strong> <code>{html.escape(_format_process_list(callout['denied_first_runnable']))}</code></p>
          <p><strong>Denied blocking:</strong> <code>{html.escape(_format_blocking_summary(callout['denied_blocking']))}</code></p>
          <p><strong>Summary:</strong> {html.escape(str(callout['summary']))}</p>
        </section>
""".strip()
        banker_request_section = f"""
      <section class="card">
        <h2>Banker's request trial</h2>
        <p>Source: <code>{html.escape(banker_request_source or 'n/a')}</code></p>
        {f'<p>Contrast source: <code>{html.escape(banker_request_contrast_source)}</code></p>' if banker_request_contrast_source else ''}
        <p><strong>Question answered:</strong> should this new request be granted while keeping the system safe?</p>
        <div class="grid compact-grid">
          <div class="metric"><strong>Process</strong><br /><code>{html.escape(request.process)}</code></div>
          <div class="metric"><strong>Request</strong><br /><code>{html.escape(_format_resource_vector(request.request))}</code></div>
          <div class="metric"><strong>Granted</strong><br />{'yes' if request.granted else 'no'}</div>
          <div class="metric"><strong>Safe after trial</strong><br />{'yes' if request.safe else 'no'}</div>
        </div>
        <p><strong>Reason:</strong> {html.escape(request.reason)}</p>
        <p><strong>Safe sequence:</strong> <code>{html.escape(_format_process_list(request.safe_sequence))}</code></p>
        <p><strong>Evaluated available vector:</strong> <code>{html.escape(_format_resource_vector(request.trial_available if request.trial_available is not None else request.available))}</code></p>
        <p><strong>Blocking summary:</strong> <code>{html.escape(_format_blocking_summary(request.blocking))}</code></p>
        {banker_request_svg}
        <div class="table-wrap">{_render_trace_steps_html_table(request.trace_steps)}</div>
{banker_request_delta_section}
      </section>
"""
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Deadlock detection vs avoidance dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1320px; margin: 0 auto; padding: 32px 24px 56px; }}
    h1, h2, h3 {{ margin-top: 0; }}
    .card {{ background: #fff; border: 1px solid #cbd5e1; border-radius: 18px; padding: 20px; margin-top: 20px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .compact-grid {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    .split {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 20px; align-items: start; }}
    .metric {{ background: #eff6ff; border-radius: 14px; padding: 14px; }}
    .tag {{ display: inline-block; margin-right: 8px; margin-bottom: 8px; padding: 6px 10px; border-radius: 999px; background: #e2e8f0; color: #334155; font-size: 13px; }}
    ul {{ margin: 12px 0 0 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }}
    code {{ font-family: "SFMono-Regular", Consolas, monospace; font-size: 0.95em; }}
    .table-wrap {{ overflow-x: auto; }}
    .source-list code {{ word-break: break-all; }}
  </style>
</head>
<body>
  <main>
    <section class="card">
      <h1>Deadlock detection vs avoidance dashboard</h1>
      <p>This portfolio report contrasts two detection views, wait-for graphs and resource-allocation progress, with one avoidance view based on Banker's algorithm.</p>
      <div class="grid">
        <div class="metric"><strong>Wait-for graph</strong><br />{'deadlocked' if dashboard.wait_for.deadlocked else 'clear'}</div>
        <div class="metric"><strong>Allocation snapshot</strong><br />{'deadlocked' if dashboard.allocation.deadlocked else 'safe'}</div>
        <div class="metric"><strong>Banker safety</strong><br />{'safe' if dashboard.banker_safety.safe else 'unsafe'}</div>
        {request_metric}
      </div>
      <div class="card source-list">
        <h2>Inputs</h2>
        <p><span class="tag">wait-for</span><code>{html.escape(wait_source)}</code></p>
        <p><span class="tag">allocation</span><code>{html.escape(allocation_source)}</code></p>
        <p><span class="tag">banker safety</span><code>{html.escape(banker_source)}</code></p>
        {f'<p><span class="tag">banker request</span><code>{html.escape(banker_request_source)}</code></p>' if banker_request_source else ''}
        {f'<p><span class="tag">banker contrast</span><code>{html.escape(banker_request_contrast_source)}</code></p>' if banker_request_contrast_source else ''}
      </div>
      <h2>Key takeaways</h2>
      <ul>{takeaway_items}</ul>
    </section>

    <section class="split">
      <article class="card">
        <h2>Wait-for graph detection</h2>
        <p><strong>Question answered:</strong> is there already a cycle among the waiting processes?</p>
        <p><strong>Cycle:</strong> <code>{html.escape(' -> '.join(dashboard.wait_for.cycle) if dashboard.wait_for.cycle else 'none')}</code></p>
        <p><strong>Blocked processes:</strong> <code>{html.escape(_format_process_list(dashboard.wait_for.blocked_processes))}</code></p>
        {wait_svg}
      </article>

      <article class="card">
        <h2>Resource-allocation detection</h2>
        <p><strong>Question answered:</strong> can the current work vector still finish anyone and free resources?</p>
        <p><strong>Finish order:</strong> <code>{html.escape(_format_process_list(dashboard.allocation.finish_order))}</code></p>
        <p><strong>Deadlocked processes:</strong> <code>{html.escape(_format_process_list(dashboard.allocation.deadlocked_processes))}</code></p>
        <p><strong>Blocking summary:</strong> <code>{html.escape(_format_blocking_summary(dashboard.allocation.blocking))}</code></p>
        {allocation_svg}
      </article>
    </section>

    <section class="split">
      <section class="card">
        <h2>Banker's safety analysis</h2>
        <p><strong>Question answered:</strong> is the current state safe before any new request is granted?</p>
        <p><strong>Safe:</strong> {'yes' if dashboard.banker_safety.safe else 'no'}</p>
        <p><strong>Safe sequence:</strong> <code>{html.escape(_format_process_list(dashboard.banker_safety.safe_sequence))}</code></p>
        <p><strong>Final work:</strong> <code>{html.escape(_format_resource_vector(dashboard.banker_safety.work))}</code></p>
        <p><strong>Blocking summary:</strong> <code>{html.escape(_format_blocking_summary(dashboard.banker_safety.blocking))}</code></p>
        {banker_svg}
        <div class="table-wrap">{_render_trace_steps_html_table(dashboard.banker_safety.trace_steps)}</div>
      </section>
{banker_request_section}
    </section>
  </main>
</body>
</html>
"""



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
    banker_parser.add_argument(
        "--svg-out",
        help="optional path for a static Banker's safety SVG export",
    )
    banker_parser.add_argument(
        "--html-out",
        help="optional path for a static Banker's safety HTML export",
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
    banker_request_parser.add_argument(
        "--svg-out",
        help="optional path for a static Banker's request SVG export",
    )
    banker_request_parser.add_argument(
        "--html-out",
        help="optional path for a static Banker's request HTML export",
    )

    banker_request_gallery_parser = subparsers.add_parser(
        "compare-banker-requests",
        help="compare multiple Banker's algorithm request trials side by side",
    )
    banker_request_gallery_parser.add_argument(
        "inputs",
        nargs="+",
        help="two or more Banker's request JSON files to compare",
    )
    banker_request_gallery_parser.add_argument(
        "--markdown-out",
        help="optional path for a side-by-side Banker's request gallery markdown export",
    )
    banker_request_gallery_parser.add_argument(
        "--html-out",
        help="optional path for a side-by-side Banker's request gallery HTML export",
    )

    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="build a combined deadlock detection vs avoidance dashboard from sample inputs",
    )
    dashboard_parser.add_argument("--wait-input", required=True, help="path to a wait-for graph JSON file")
    dashboard_parser.add_argument(
        "--allocation-input",
        required=True,
        help="path to an allocation/request snapshot JSON file",
    )
    dashboard_parser.add_argument(
        "--banker-input",
        required=True,
        help="path to a Banker's safety-state JSON file",
    )
    dashboard_parser.add_argument(
        "--banker-request-input",
        help="optional path to a Banker's request JSON file to include in the dashboard",
    )
    dashboard_parser.add_argument(
        "--banker-contrast-input",
        help="optional path to a second Banker's request JSON file for a granted-vs-denied dashboard delta callout",
    )
    dashboard_parser.add_argument(
        "--markdown-out",
        help="optional path for a combined Markdown dashboard export",
    )
    dashboard_parser.add_argument(
        "--html-out",
        help="optional path for a combined HTML dashboard export",
    )

    return parser



def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        markdown: str | None = None
        svg: str | None = None
        html_report: str | None = None
        if args.command == "analyze-wait":
            payload = load_json(Path(args.input))
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
            payload = load_json(Path(args.input))
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
            payload = load_json(Path(args.input))
            analysis = analyze_banker_state(payload)
            result = analysis.to_dict()
            if getattr(args, "markdown_out", None):
                markdown = render_banker_safety_markdown(analysis, args.input)
            if getattr(args, "svg_out", None):
                svg = render_banker_safety_svg(analysis, args.input)
            if getattr(args, "html_out", None):
                html_report = render_banker_safety_html(analysis, args.input)
        elif args.command == "request-banker":
            payload = load_json(Path(args.input))
            analysis = analyze_banker_request(payload)
            result = analysis.to_dict()
            if getattr(args, "markdown_out", None):
                markdown = render_banker_request_markdown(analysis, args.input)
            if getattr(args, "svg_out", None):
                svg = render_banker_request_svg(analysis, args.input)
            if getattr(args, "html_out", None):
                html_report = render_banker_request_html(analysis, args.input)
        elif args.command == "compare-banker-requests":
            request_reports: list[BankerRequestReport] = []
            for input_path in args.inputs:
                payload = load_json(Path(input_path))
                request_reports.append(
                    BankerRequestReport(
                        source=input_path,
                        analysis=analyze_banker_request(payload),
                    )
                )
            gallery = build_banker_request_gallery(request_reports)
            result = gallery.to_dict()
            if getattr(args, "markdown_out", None):
                markdown = render_banker_request_gallery_markdown(gallery)
            if getattr(args, "html_out", None):
                html_report = render_banker_request_gallery_html(gallery)
        elif args.command == "dashboard":
            if getattr(args, "banker_contrast_input", None) and not getattr(args, "banker_request_input", None):
                raise ValueError("--banker-contrast-input requires --banker-request-input")
            wait_payload = load_json(Path(args.wait_input))
            allocation_payload = load_json(Path(args.allocation_input))
            banker_payload = load_json(Path(args.banker_input))
            banker_request_payload = (
                load_json(Path(args.banker_request_input)) if getattr(args, "banker_request_input", None) else None
            )
            banker_contrast_payload = (
                load_json(Path(args.banker_contrast_input)) if getattr(args, "banker_contrast_input", None) else None
            )

            wait_analysis = analyze_wait_for_graph(wait_payload)
            allocation_analysis = analyze_allocations(allocation_payload)
            banker_analysis = analyze_banker_state(banker_payload)
            banker_request_analysis = (
                analyze_banker_request(banker_request_payload) if banker_request_payload is not None else None
            )
            banker_contrast_analysis = (
                analyze_banker_request(banker_contrast_payload) if banker_contrast_payload is not None else None
            )
            dashboard = build_detection_avoidance_dashboard(
                wait_analysis,
                allocation_analysis,
                banker_analysis,
                banker_request_analysis,
                banker_contrast_analysis,
                getattr(args, "banker_request_input", None),
                getattr(args, "banker_contrast_input", None),
            )
            result = dashboard.to_dict()
            wait_edges = [
                (str(item["from"]), str(item["to"]))
                for item in wait_payload.get("edges", [])
                if isinstance(item, dict) and isinstance(item.get("from"), str) and isinstance(item.get("to"), str)
            ]
            allocation_available = allocation_payload.get("available")
            allocation_map = allocation_payload.get("allocation")
            request_map = allocation_payload.get("request")
            if getattr(args, "markdown_out", None):
                markdown = render_detection_avoidance_markdown(
                    dashboard,
                    args.wait_input,
                    args.allocation_input,
                    args.banker_input,
                    getattr(args, "banker_request_input", None),
                    getattr(args, "banker_contrast_input", None),
                )
            if (
                getattr(args, "html_out", None)
                and isinstance(allocation_available, dict)
                and isinstance(allocation_map, dict)
                and isinstance(request_map, dict)
            ):
                html_report = render_detection_avoidance_html(
                    dashboard,
                    args.wait_input,
                    args.allocation_input,
                    args.banker_input,
                    getattr(args, "banker_request_input", None),
                    getattr(args, "banker_contrast_input", None),
                    wait_edges,
                    allocation_available,
                    allocation_map,
                    request_map,
                )
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
