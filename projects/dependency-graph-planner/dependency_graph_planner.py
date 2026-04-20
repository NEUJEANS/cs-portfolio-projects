#!/usr/bin/env python3
"""Plan and inspect dependency graphs for build or project workflows."""

from __future__ import annotations

import argparse
import csv
import heapq
import io
import json
import os
import random
from dataclasses import dataclass, field
from html import escape as _html_escape
from pathlib import Path
from typing import Any, Sequence


DEFAULT_SCHEDULE_STRATEGY = "critical-first"
SCHEDULE_STRATEGIES = ("critical-first", "fifo", "longest-processing-time")
SYNTHETIC_GENERATORS = ("ci", "release", "data-pipeline", "stress")
DEFAULT_GENERATOR_WIDTH = 3
DEFAULT_GENERATOR_SEED = 13


class GraphValidationError(ValueError):
    """Raised when the manifest is structurally invalid."""


class CycleError(ValueError):
    """Raised when dependency constraints form a cycle."""

    def __init__(self, cycle: Sequence[str]):
        rendered = " -> ".join(cycle)
        super().__init__(f"cycle detected: {rendered}")
        self.cycle = list(cycle)


@dataclass(frozen=True)
class Task:
    name: str
    deps: tuple[str, ...]
    duration: int = 1
    command: str | None = None
    resource_class: str | None = None
    resource_demands: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskTiming:
    name: str
    duration: int
    earliest_start: int
    earliest_finish: int
    latest_start: int
    latest_finish: int
    slack: int
    critical: bool


@dataclass(frozen=True)
class PlanResult:
    order: list[str]
    layers: list[list[str]]
    total_duration: int
    timings: list[TaskTiming]
    critical_path: list[str]


@dataclass(frozen=True)
class ScheduledTask:
    name: str
    worker: int
    ready_at: int
    start: int
    finish: int
    queue_delay: int
    duration: int
    critical: bool
    resource_class: str | None = None
    resource_slot: int | None = None
    resource_demands: dict[str, int] = field(default_factory=dict)
    resource_allocations: dict[str, tuple[int, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class ResourceClassSummary:
    resource_class: str
    capacity: int
    task_count: int
    total_reserved_units: int
    peak_concurrent_usage: int
    utilization: float
    idle_capacity: int
    delayed_tasks: int
    max_queue_delay: int


@dataclass(frozen=True)
class WorkerLimitedSchedule:
    worker_limit: int
    strategy: str
    makespan: int
    unlimited_makespan: int
    total_work: int
    theoretical_lower_bound: int
    idle_capacity: int
    utilization: float
    dispatch_order: list[str]
    assignments: list[ScheduledTask]
    worker_timelines: list[list[ScheduledTask]]
    resource_capacities: dict[str, int]
    resource_summaries: list[ResourceClassSummary]


@dataclass(frozen=True)
class BenchmarkScenario:
    label: str
    graph_label: str
    graph_path: str
    worker_limit: int
    strategies: tuple[str, ...]
    resource_capacity_overrides: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkStrategyResult:
    strategy: str
    makespan: int
    delta_vs_unlimited: int
    delta_vs_critical_path_lower_bound: int
    ratio_vs_critical_path_lower_bound: float
    delta_vs_best: int
    total_queue_delay: int
    max_queue_delay: int
    utilization: float
    idle_capacity: int
    dispatch_order: list[str]
    rank: int
    tied_best_makespan: bool


@dataclass(frozen=True)
class BenchmarkScenarioResult:
    label: str
    graph_label: str
    graph_path: str
    worker_limit: int
    task_count: int
    unlimited_makespan: int
    critical_path_lower_bound: int
    resource_capacities: dict[str, int]
    strategy_results: list[BenchmarkStrategyResult]
    best_makespan: int
    best_makespan_strategies: list[str]
    rank_1_strategies: list[str]


@dataclass(frozen=True)
class BenchmarkStrategyAggregate:
    strategy: str
    scenario_count: int
    rank_1_finishes: int
    best_makespan_finishes: int
    average_makespan: float
    average_delta_vs_critical_path_lower_bound: float
    average_ratio_vs_critical_path_lower_bound: float
    average_delta_vs_best: float
    average_total_queue_delay: float
    average_max_queue_delay: float
    average_utilization: float


@dataclass(frozen=True)
class BenchmarkSuiteResult:
    title: str
    source_label: str
    scenarios: list[BenchmarkScenarioResult]
    aggregates: list[BenchmarkStrategyAggregate]


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GraphValidationError("manifest must be a JSON object")
    return data


def parse_manifest_metadata(data: dict[str, Any]) -> dict[str, str]:
    raw_metadata = data.get("metadata", {})
    if raw_metadata in (None, {}):
        return {}
    if not isinstance(raw_metadata, dict):
        raise GraphValidationError("metadata must be a JSON object")

    metadata: dict[str, str] = {}
    raw_title = raw_metadata.get("title")
    if raw_title is not None:
        if not isinstance(raw_title, str) or not raw_title.strip():
            raise GraphValidationError("metadata.title must be a non-empty string when provided")
        metadata["title"] = raw_title.strip()

    raw_description = raw_metadata.get("description")
    if raw_description is not None:
        if not isinstance(raw_description, str) or not raw_description.strip():
            raise GraphValidationError("metadata.description must be a non-empty string when provided")
        metadata["description"] = raw_description.strip()

    return metadata


def _parse_task_resource_demands(entry: dict[str, Any], name: str) -> tuple[str | None, dict[str, int]]:
    resource_class = entry.get("resource_class")
    if resource_class is not None:
        if not isinstance(resource_class, str) or not resource_class.strip():
            raise GraphValidationError(f"task {name!r} has an invalid resource_class")
        resource_class = resource_class.strip()

    raw_resources = entry.get("resources", {})
    if raw_resources in (None, {}):
        resource_demands: dict[str, int] = {}
    else:
        if not isinstance(raw_resources, dict):
            raise GraphValidationError(f"task {name!r} has invalid resources")
        resource_demands = {}
        for raw_label, raw_amount in raw_resources.items():
            if not isinstance(raw_label, str) or not raw_label.strip():
                raise GraphValidationError(f"task {name!r} has invalid resources")
            if not isinstance(raw_amount, int) or raw_amount <= 0:
                raise GraphValidationError(f"task {name!r} has invalid resources")
            label = raw_label.strip()
            if label in resource_demands:
                raise GraphValidationError(f"task {name!r} repeats resource {label!r}")
            resource_demands[label] = raw_amount
        resource_demands = dict(sorted(resource_demands.items()))

    if resource_class is not None:
        if resource_class in resource_demands:
            raise GraphValidationError(
                f"task {name!r} repeats resource_class {resource_class!r} inside resources"
            )
        resource_demands = dict(resource_demands)
        resource_demands[resource_class] = 1
        resource_demands = dict(sorted(resource_demands.items()))

    normalized_resource_class = resource_class
    if normalized_resource_class is None and len(resource_demands) == 1:
        normalized_resource_class = next(iter(resource_demands))

    return normalized_resource_class, resource_demands


def parse_tasks(data: dict) -> dict[str, Task]:
    parse_manifest_metadata(data)
    raw_tasks = data.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise GraphValidationError("manifest must include a non-empty tasks list")

    tasks: dict[str, Task] = {}
    for entry in raw_tasks:
        if not isinstance(entry, dict):
            raise GraphValidationError("each task must be a JSON object")
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            raise GraphValidationError("each task needs a non-empty string name")
        deps = entry.get("deps", [])
        if not isinstance(deps, list) or any(not isinstance(dep, str) or not dep.strip() for dep in deps):
            raise GraphValidationError(f"task {name!r} has an invalid deps list")
        duration = entry.get("duration", 1)
        if not isinstance(duration, int) or duration <= 0:
            raise GraphValidationError(f"task {name!r} must have a positive integer duration")
        command = entry.get("command")
        if command is not None and not isinstance(command, str):
            raise GraphValidationError(f"task {name!r} has a non-string command")
        resource_class, resource_demands = _parse_task_resource_demands(entry, name)
        if name in tasks:
            raise GraphValidationError(f"duplicate task name: {name}")
        deduped_deps = tuple(dict.fromkeys(dep.strip() for dep in deps))
        tasks[name] = Task(
            name=name,
            deps=deduped_deps,
            duration=duration,
            command=command,
            resource_class=resource_class,
            resource_demands=resource_demands,
        )

    unknown = sorted({dep for task in tasks.values() for dep in task.deps if dep not in tasks})
    if unknown:
        raise GraphValidationError(f"unknown dependencies referenced: {', '.join(unknown)}")
    return tasks


def parse_resource_capacities(data: dict) -> dict[str, int]:
    raw_capacities = data.get("resource_capacities", {})
    if raw_capacities in (None, {}):
        return {}
    if not isinstance(raw_capacities, dict):
        raise GraphValidationError("resource_capacities must be a JSON object")

    capacities: dict[str, int] = {}
    for raw_name, raw_capacity in raw_capacities.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise GraphValidationError("resource_capacities keys must be non-empty strings")
        if not isinstance(raw_capacity, int) or raw_capacity <= 0:
            raise GraphValidationError(f"resource_capacities[{raw_name!r}] must be a positive integer")
        capacities[raw_name.strip()] = raw_capacity
    return dict(sorted(capacities.items()))


def _task_resource_classes(tasks: dict[str, Task]) -> list[str]:
    return sorted({resource_class for task in tasks.values() for resource_class in task.resource_demands})


def validate_manifest_resource_capacities(tasks: dict[str, Task], resource_capacities: dict[str, int]) -> None:
    declared_classes = set(_task_resource_classes(tasks))
    if not declared_classes and resource_capacities:
        raise GraphValidationError("resource_capacities were provided but no task declares any resources")
    unknown = sorted(set(resource_capacities) - declared_classes)
    if unknown:
        raise GraphValidationError(
            f"resource_capacities reference unknown resource classes: {', '.join(unknown)}"
        )


def parse_resource_capacity_overrides(values: Sequence[str] | None) -> dict[str, int]:
    capacities: dict[str, int] = {}
    for raw_value in values or ():
        name, separator, raw_capacity = raw_value.partition("=")
        resource_class = name.strip()
        if separator != "=" or not resource_class or not raw_capacity.strip():
            raise ValueError("--resource-capacity must use class=count")
        try:
            capacity = int(raw_capacity.strip())
        except ValueError as exc:
            raise ValueError(f"invalid resource capacity in {raw_value!r}") from exc
        if capacity <= 0:
            raise ValueError(f"resource capacity for {resource_class!r} must be positive")
        capacities[resource_class] = capacity
    return capacities


def resolve_resource_capacities(
    tasks: dict[str, Task],
    manifest_resource_capacities: dict[str, int],
    resource_capacity_overrides: Sequence[str] | None = None,
) -> dict[str, int]:
    required_classes = set(_task_resource_classes(tasks))
    overrides = parse_resource_capacity_overrides(resource_capacity_overrides)
    combined = dict(manifest_resource_capacities)
    combined.update(overrides)

    if not required_classes:
        if combined:
            raise ValueError("resource capacities were provided but no task declares any resources")
        return {}

    unknown = sorted(set(combined) - required_classes)
    if unknown:
        raise ValueError(f"resource capacities reference unknown resource classes: {', '.join(unknown)}")

    missing = sorted(required_classes - set(combined))
    if missing:
        raise ValueError(f"missing resource capacities for resource classes: {', '.join(missing)}")

    return {name: combined[name] for name in sorted(required_classes)}


def _parse_benchmark_strategies(raw_value: Any, *, label: str) -> tuple[str, ...]:
    if raw_value in (None, []):
        return SCHEDULE_STRATEGIES
    if not isinstance(raw_value, list) or not raw_value:
        raise GraphValidationError(
            f"benchmark scenario {label!r} strategies must be a non-empty list when provided"
        )

    ordered: list[str] = []
    seen: set[str] = set()
    for raw_strategy in raw_value:
        if not isinstance(raw_strategy, str):
            raise GraphValidationError(f"benchmark scenario {label!r} has an invalid strategy")
        try:
            strategy = _resolve_schedule_strategy(raw_strategy)
        except ValueError as exc:
            raise GraphValidationError(f"benchmark scenario {label!r} has an invalid strategy") from exc
        if strategy in seen:
            continue
        seen.add(strategy)
        ordered.append(strategy)
    return tuple(ordered)


def _parse_inline_resource_capacities(raw_value: Any, *, label: str) -> dict[str, int]:
    if raw_value in (None, {}):
        return {}
    if not isinstance(raw_value, dict):
        raise GraphValidationError(f"benchmark scenario {label!r} resource_capacities must be a JSON object")

    capacities: dict[str, int] = {}
    for raw_name, raw_capacity in raw_value.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise GraphValidationError(
                f"benchmark scenario {label!r} resource_capacities keys must be non-empty strings"
            )
        if not isinstance(raw_capacity, int) or raw_capacity <= 0:
            raise GraphValidationError(
                f"benchmark scenario {label!r} resource_capacities[{raw_name!r}] must be a positive integer"
            )
        capacities[raw_name.strip()] = raw_capacity
    return dict(sorted(capacities.items()))


def load_benchmark_suite(
    path: str | Path,
    *,
    explicit_title: str | None = None,
) -> tuple[str, list[BenchmarkScenario]]:
    suite_data = load_manifest(path)
    raw_title = suite_data.get("title")
    if raw_title is not None and (not isinstance(raw_title, str) or not raw_title.strip()):
        raise GraphValidationError("benchmark suite title must be a non-empty string when provided")

    raw_scenarios = suite_data.get("scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise GraphValidationError("benchmark suite must include a non-empty scenarios list")

    suite_path = Path(path)
    suite_dir = suite_path.parent
    scenarios: list[BenchmarkScenario] = []
    seen_labels: set[str] = set()
    for index, entry in enumerate(raw_scenarios, start=1):
        if not isinstance(entry, dict):
            raise GraphValidationError(f"benchmark scenario {index} must be a JSON object")

        label = entry.get("label")
        if not isinstance(label, str) or not label.strip():
            raise GraphValidationError(f"benchmark scenario {index} needs a non-empty string label")
        label = label.strip()
        if label in seen_labels:
            raise GraphValidationError(f"duplicate benchmark scenario label: {label}")
        seen_labels.add(label)

        graph_label = entry.get("graph")
        if not isinstance(graph_label, str) or not graph_label.strip():
            raise GraphValidationError(f"benchmark scenario {label!r} needs a non-empty string graph")
        graph_label = graph_label.strip()
        graph_path = Path(graph_label)
        if not graph_path.is_absolute():
            graph_path = (suite_dir / graph_path).resolve()

        worker_limit = entry.get("worker_limit")
        if not isinstance(worker_limit, int) or worker_limit <= 0:
            raise GraphValidationError(
                f"benchmark scenario {label!r} must have a positive integer worker_limit"
            )

        scenarios.append(
            BenchmarkScenario(
                label=label,
                graph_label=graph_label,
                graph_path=str(graph_path),
                worker_limit=worker_limit,
                strategies=_parse_benchmark_strategies(entry.get("strategies"), label=label),
                resource_capacity_overrides=_parse_inline_resource_capacities(
                    entry.get("resource_capacities"),
                    label=label,
                ),
            )
        )

    return (
        build_benchmark_title(
            source_label=str(path),
            explicit_title=explicit_title or (raw_title.strip() if isinstance(raw_title, str) else None),
        ),
        scenarios,
    )


def _benchmark_result_sort_key(item: BenchmarkStrategyResult) -> tuple[int, int, int, int]:
    return (
        item.makespan,
        item.total_queue_delay,
        item.max_queue_delay,
        SCHEDULE_STRATEGIES.index(item.strategy),
    )


def _benchmark_rank_key(item: BenchmarkStrategyResult) -> tuple[int, int, int]:
    return (item.makespan, item.total_queue_delay, item.max_queue_delay)


def _average(values: Sequence[float]) -> float:
    return 0.0 if not values else sum(values) / len(values)


def build_benchmark_suite_result(
    suite_path: str | Path,
    *,
    title: str | None = None,
) -> BenchmarkSuiteResult:
    resolved_title, scenarios = load_benchmark_suite(suite_path, explicit_title=title)
    scenario_results: list[BenchmarkScenarioResult] = []

    for scenario in scenarios:
        manifest = load_manifest(scenario.graph_path)
        tasks = parse_tasks(manifest)
        manifest_resource_capacities = parse_resource_capacities(manifest)
        validate_manifest_resource_capacities(tasks, manifest_resource_capacities)
        plan = build_plan(tasks)
        override_flags = [
            f"{resource_class}={capacity}"
            for resource_class, capacity in scenario.resource_capacity_overrides.items()
        ]
        resolved_resource_capacities = resolve_resource_capacities(
            tasks,
            manifest_resource_capacities,
            override_flags,
        )

        strategy_results: list[BenchmarkStrategyResult] = []
        raw_results: list[tuple[str, WorkerLimitedSchedule]] = []
        for strategy in scenario.strategies:
            schedule = build_worker_limited_schedule(
                tasks,
                plan,
                worker_limit=scenario.worker_limit,
                strategy=strategy,
                resource_capacities=resolved_resource_capacities,
            )
            raw_results.append((strategy, schedule))

        best_makespan = min(schedule.makespan for _, schedule in raw_results)
        critical_path_lower_bound = plan.total_duration
        provisional_results: list[BenchmarkStrategyResult] = []
        for strategy, schedule in raw_results:
            delayed = [item.queue_delay for item in schedule.assignments if item.queue_delay > 0]
            provisional_results.append(
                BenchmarkStrategyResult(
                    strategy=strategy,
                    makespan=schedule.makespan,
                    delta_vs_unlimited=schedule.makespan - schedule.unlimited_makespan,
                    delta_vs_critical_path_lower_bound=schedule.makespan - critical_path_lower_bound,
                    ratio_vs_critical_path_lower_bound=(schedule.makespan / critical_path_lower_bound)
                    if critical_path_lower_bound
                    else 0.0,
                    delta_vs_best=schedule.makespan - best_makespan,
                    total_queue_delay=sum(item.queue_delay for item in schedule.assignments),
                    max_queue_delay=max(delayed, default=0),
                    utilization=schedule.utilization,
                    idle_capacity=schedule.idle_capacity,
                    dispatch_order=list(schedule.dispatch_order),
                    rank=0,
                    tied_best_makespan=schedule.makespan == best_makespan,
                )
            )

        sorted_results = sorted(provisional_results, key=_benchmark_result_sort_key)
        ranked_results: list[BenchmarkStrategyResult] = []
        current_rank = 0
        previous_rank_key: tuple[int, int, int] | None = None
        for item in sorted_results:
            rank_key = _benchmark_rank_key(item)
            if rank_key != previous_rank_key:
                current_rank += 1
                previous_rank_key = rank_key
            ranked_results.append(
                BenchmarkStrategyResult(
                    strategy=item.strategy,
                    makespan=item.makespan,
                    delta_vs_unlimited=item.delta_vs_unlimited,
                    delta_vs_critical_path_lower_bound=item.delta_vs_critical_path_lower_bound,
                    ratio_vs_critical_path_lower_bound=item.ratio_vs_critical_path_lower_bound,
                    delta_vs_best=item.delta_vs_best,
                    total_queue_delay=item.total_queue_delay,
                    max_queue_delay=item.max_queue_delay,
                    utilization=item.utilization,
                    idle_capacity=item.idle_capacity,
                    dispatch_order=item.dispatch_order,
                    rank=current_rank,
                    tied_best_makespan=item.tied_best_makespan,
                )
            )

        scenario_results.append(
            BenchmarkScenarioResult(
                label=scenario.label,
                graph_label=scenario.graph_label,
                graph_path=scenario.graph_path,
                worker_limit=scenario.worker_limit,
                task_count=len(tasks),
                unlimited_makespan=plan.total_duration,
                critical_path_lower_bound=critical_path_lower_bound,
                resource_capacities=resolved_resource_capacities,
                strategy_results=ranked_results,
                best_makespan=best_makespan,
                best_makespan_strategies=[
                    item.strategy for item in ranked_results if item.tied_best_makespan
                ],
                rank_1_strategies=[item.strategy for item in ranked_results if item.rank == 1],
            )
        )

    aggregate_lookup: dict[str, list[BenchmarkStrategyResult]] = {strategy: [] for strategy in SCHEDULE_STRATEGIES}
    for scenario_result in scenario_results:
        for item in scenario_result.strategy_results:
            aggregate_lookup[item.strategy].append(item)

    aggregates: list[BenchmarkStrategyAggregate] = []
    for strategy in SCHEDULE_STRATEGIES:
        items = aggregate_lookup[strategy]
        if not items:
            continue
        aggregates.append(
            BenchmarkStrategyAggregate(
                strategy=strategy,
                scenario_count=len(items),
                rank_1_finishes=sum(1 for item in items if item.rank == 1),
                best_makespan_finishes=sum(1 for item in items if item.tied_best_makespan),
                average_makespan=_average([float(item.makespan) for item in items]),
                average_delta_vs_critical_path_lower_bound=_average([float(item.delta_vs_critical_path_lower_bound) for item in items]),
                average_ratio_vs_critical_path_lower_bound=_average([item.ratio_vs_critical_path_lower_bound for item in items]),
                average_delta_vs_best=_average([float(item.delta_vs_best) for item in items]),
                average_total_queue_delay=_average([float(item.total_queue_delay) for item in items]),
                average_max_queue_delay=_average([float(item.max_queue_delay) for item in items]),
                average_utilization=_average([item.utilization for item in items]),
            )
        )

    aggregates.sort(
        key=lambda item: (
            -item.rank_1_finishes,
            -item.best_makespan_finishes,
            item.average_delta_vs_best,
            item.average_makespan,
            SCHEDULE_STRATEGIES.index(item.strategy),
        )
    )
    return BenchmarkSuiteResult(
        title=resolved_title,
        source_label=_display_path_label(suite_path),
        scenarios=scenario_results,
        aggregates=aggregates,
    )


def build_dependents(tasks: dict[str, Task]) -> dict[str, list[str]]:
    dependents = {name: [] for name in tasks}
    for task in tasks.values():
        for dep in task.deps:
            dependents[dep].append(task.name)
    for names in dependents.values():
        names.sort()
    return dependents


def topological_order(tasks: dict[str, Task]) -> list[str]:
    in_degree = {name: len(task.deps) for name, task in tasks.items()}
    queue = [name for name, degree in in_degree.items() if degree == 0]
    heapq.heapify(queue)
    dependents = build_dependents(tasks)
    order: list[str] = []

    while queue:
        current = heapq.heappop(queue)
        order.append(current)
        for dependent in dependents[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                heapq.heappush(queue, dependent)

    if len(order) != len(tasks):
        raise CycleError(find_cycle(tasks))
    return order


def find_cycle(tasks: dict[str, Task]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            start = stack.index(node)
            return stack[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        stack.append(node)
        for dep in tasks[node].deps:
            cycle = visit(dep)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for name in sorted(tasks):
        cycle = visit(name)
        if cycle:
            return cycle
    return []


def build_layers(tasks: dict[str, Task], order: Sequence[str]) -> list[list[str]]:
    level: dict[str, int] = {}
    for name in order:
        deps = tasks[name].deps
        level[name] = 0 if not deps else max(level[dep] + 1 for dep in deps)
    max_level = max(level.values(), default=-1)
    return [sorted(name for name, task_level in level.items() if task_level == idx) for idx in range(max_level + 1)]


def compute_timings(tasks: dict[str, Task], order: Sequence[str]) -> tuple[list[TaskTiming], int, list[str]]:
    dependents = build_dependents(tasks)
    earliest_start: dict[str, int] = {}
    earliest_finish: dict[str, int] = {}

    for name in order:
        start = max((earliest_finish[dep] for dep in tasks[name].deps), default=0)
        earliest_start[name] = start
        earliest_finish[name] = start + tasks[name].duration

    total_duration = max(earliest_finish.values(), default=0)
    latest_finish: dict[str, int] = {}
    latest_start: dict[str, int] = {}

    for name in reversed(order):
        finish = min((latest_start[child] for child in dependents[name]), default=total_duration)
        latest_finish[name] = finish
        latest_start[name] = finish - tasks[name].duration

    timings = []
    slack_by_name: dict[str, int] = {}
    for name in order:
        slack = latest_start[name] - earliest_start[name]
        slack_by_name[name] = slack
        timings.append(
            TaskTiming(
                name=name,
                duration=tasks[name].duration,
                earliest_start=earliest_start[name],
                earliest_finish=earliest_finish[name],
                latest_start=latest_start[name],
                latest_finish=latest_finish[name],
                slack=slack,
                critical=slack == 0,
            )
        )

    critical_path = _extract_critical_path(
        tasks,
        order,
        dependents,
        earliest_start,
        earliest_finish,
        total_duration,
        slack_by_name,
    )
    return timings, total_duration, critical_path


def _extract_critical_path(
    tasks: dict[str, Task],
    order: Sequence[str],
    dependents: dict[str, list[str]],
    earliest_start: dict[str, int],
    earliest_finish: dict[str, int],
    total_duration: int,
    slack_by_name: dict[str, int],
) -> list[str]:
    critical_nodes = {name for name in order if slack_by_name[name] == 0}
    roots = [name for name in order if not tasks[name].deps and name in critical_nodes]
    candidates: list[list[str]] = []

    def walk(node: str, path: list[str]) -> None:
        path = path + [node]
        next_nodes = [
            child
            for child in dependents[node]
            if child in critical_nodes and earliest_start[child] == earliest_finish[node]
        ]
        if not next_nodes:
            if earliest_finish[node] == total_duration:
                candidates.append(path)
            return
        for child in sorted(next_nodes):
            walk(child, path)

    for root in roots:
        walk(root, [])

    if not candidates:
        return []
    candidates.sort(key=lambda path: (-len(path), tuple(path)))
    return candidates[0]


def _resolve_schedule_strategy(strategy: str | None) -> str:
    resolved = strategy or DEFAULT_SCHEDULE_STRATEGY
    if resolved not in SCHEDULE_STRATEGIES:
        raise ValueError(
            f"unsupported schedule strategy: {resolved} (choose from {', '.join(SCHEDULE_STRATEGIES)})"
        )
    return resolved


def _schedule_priority(
    *,
    strategy: str,
    timing: TaskTiming,
    order_index: int,
    ready_at: int,
    ready_sequence: int,
) -> tuple[Any, ...]:
    if strategy == "critical-first":
        return (
            0 if timing.critical else 1,
            timing.slack,
            -timing.duration,
            ready_at,
            order_index,
            ready_sequence,
        )
    if strategy == "fifo":
        return (ready_at, ready_sequence, order_index)
    if strategy == "longest-processing-time":
        return (-timing.duration, ready_at, timing.slack, ready_sequence, order_index)
    raise ValueError(f"unsupported schedule strategy: {strategy}")


def build_plan(tasks: dict[str, Task]) -> PlanResult:
    order = topological_order(tasks)
    layers = build_layers(tasks, order)
    timings, total_duration, critical_path = compute_timings(tasks, order)
    return PlanResult(order=order, layers=layers, total_duration=total_duration, timings=timings, critical_path=critical_path)


def build_worker_limited_schedule(
    tasks: dict[str, Task],
    plan: PlanResult,
    *,
    worker_limit: int,
    strategy: str = DEFAULT_SCHEDULE_STRATEGY,
    resource_capacities: dict[str, int] | None = None,
) -> WorkerLimitedSchedule:
    if worker_limit <= 0:
        raise ValueError("--worker-limit must be a positive integer")
    resolved_strategy = _resolve_schedule_strategy(strategy)
    resolved_resource_capacities = dict(sorted((resource_capacities or {}).items()))

    required_resource_classes = set(_task_resource_classes(tasks))
    if required_resource_classes:
        missing = sorted(required_resource_classes - set(resolved_resource_capacities))
        if missing:
            raise ValueError(f"missing resource capacities for resource classes: {', '.join(missing)}")
        unknown = sorted(set(resolved_resource_capacities) - required_resource_classes)
        if unknown:
            raise ValueError(f"resource capacities reference unknown resource classes: {', '.join(unknown)}")
    elif resolved_resource_capacities:
        raise ValueError("resource capacities were provided but no task declares any resources")

    timings_by_name = {timing.name: timing for timing in plan.timings}
    order_index = {name: index for index, name in enumerate(plan.order)}
    dependents = build_dependents(tasks)
    remaining_deps = {name: len(task.deps) for name, task in tasks.items()}
    finish_times: dict[str, int] = {}
    ready_at: dict[str, int] = {name: 0 for name, count in remaining_deps.items() if count == 0}
    ready_queue: list[tuple[Any, ...]] = []
    ready_sequence = 0

    def push_ready(name: str) -> None:
        nonlocal ready_sequence
        ready_sequence += 1
        timing = timings_by_name[name]
        priority = _schedule_priority(
            strategy=resolved_strategy,
            timing=timing,
            order_index=order_index[name],
            ready_at=ready_at.get(name, 0),
            ready_sequence=ready_sequence,
        )
        heapq.heappush(ready_queue, (*priority, name))

    for name in plan.order:
        if remaining_deps[name] == 0:
            push_ready(name)

    available_workers = list(range(1, worker_limit + 1))
    heapq.heapify(available_workers)
    available_resource_slots = {
        resource_class: list(range(1, capacity + 1))
        for resource_class, capacity in resolved_resource_capacities.items()
    }
    for slots in available_resource_slots.values():
        heapq.heapify(slots)

    running: list[tuple[int, int, int, str, dict[str, tuple[int, ...]]]] = []
    assignments: list[ScheduledTask] = []
    dispatch_order: list[str] = []
    current_time = 0

    def task_can_start(name: str) -> bool:
        return all(
            len(available_resource_slots[resource_class]) >= demand
            for resource_class, demand in tasks[name].resource_demands.items()
        )

    def allocate_resources(name: str) -> dict[str, tuple[int, ...]]:
        allocations: dict[str, tuple[int, ...]] = {}
        for resource_class, demand in tasks[name].resource_demands.items():
            slots = tuple(heapq.heappop(available_resource_slots[resource_class]) for _ in range(demand))
            allocations[resource_class] = slots
        return allocations

    while ready_queue or running:
        while ready_queue and available_workers:
            deferred: list[tuple[Any, ...]] = []
            selected_name: str | None = None
            while ready_queue:
                *priority, candidate = heapq.heappop(ready_queue)
                if task_can_start(candidate):
                    selected_name = candidate
                    break
                deferred.append((*priority, candidate))
            for item in deferred:
                heapq.heappush(ready_queue, item)
            if selected_name is None:
                break

            worker = heapq.heappop(available_workers)
            resource_allocations = allocate_resources(selected_name)
            legacy_resource_class = None
            legacy_resource_slot = None
            if len(resource_allocations) == 1:
                legacy_resource_class, slots = next(iter(resource_allocations.items()))
                if len(slots) == 1:
                    legacy_resource_slot = slots[0]
            start = current_time
            finish = start + tasks[selected_name].duration
            ready_time = ready_at.get(selected_name, current_time)
            assignments.append(
                ScheduledTask(
                    name=selected_name,
                    worker=worker,
                    ready_at=ready_time,
                    start=start,
                    finish=finish,
                    queue_delay=start - ready_time,
                    duration=tasks[selected_name].duration,
                    critical=timings_by_name[selected_name].critical,
                    resource_class=legacy_resource_class,
                    resource_slot=legacy_resource_slot,
                    resource_demands=dict(tasks[selected_name].resource_demands),
                    resource_allocations=resource_allocations,
                )
            )
            dispatch_order.append(selected_name)
            heapq.heappush(running, (finish, worker, order_index[selected_name], selected_name, resource_allocations))

        if not running:
            if ready_queue:
                blocked = sorted({item[-1] for item in ready_queue})
                raise ValueError(
                    "resource-constrained schedule deadlocked before completion; check resource capacities for "
                    + ", ".join(blocked)
                )
            break

        current_time = running[0][0]
        completed: list[tuple[str, dict[str, tuple[int, ...]]]] = []
        while running and running[0][0] == current_time:
            _, worker, _, name, resource_allocations = heapq.heappop(running)
            finish_times[name] = current_time
            heapq.heappush(available_workers, worker)
            for resource_class, slots in resource_allocations.items():
                for slot in slots:
                    heapq.heappush(available_resource_slots[resource_class], slot)
            completed.append((name, resource_allocations))

        for finished_name, _ in sorted(completed, key=lambda item: order_index[item[0]]):
            for dependent in dependents[finished_name]:
                remaining_deps[dependent] -= 1
                if remaining_deps[dependent] == 0:
                    ready_at[dependent] = max((finish_times[dep] for dep in tasks[dependent].deps), default=current_time)
                    push_ready(dependent)

    worker_timelines = [[] for _ in range(worker_limit)]
    for assignment in assignments:
        worker_timelines[assignment.worker - 1].append(assignment)
    for timeline in worker_timelines:
        timeline.sort(key=lambda item: (item.start, item.finish, item.name))

    total_work = sum(task.duration for task in tasks.values())
    makespan = max((assignment.finish for assignment in assignments), default=0)
    theoretical_lower_bound = max(plan.total_duration, (total_work + worker_limit - 1) // worker_limit)
    idle_capacity = max(0, makespan * worker_limit - total_work)
    utilization = 0.0 if makespan == 0 else total_work / (makespan * worker_limit)

    resource_summaries: list[ResourceClassSummary] = []
    if resolved_resource_capacities:
        for resource_class, capacity in resolved_resource_capacities.items():
            class_assignments = [item for item in assignments if resource_class in item.resource_allocations]
            total_reserved_units = sum(
                item.duration * len(item.resource_allocations[resource_class]) for item in class_assignments
            )
            class_idle_capacity = max(0, makespan * capacity - total_reserved_units)
            class_utilization = 0.0 if makespan == 0 else total_reserved_units / (makespan * capacity)
            delayed = [item for item in class_assignments if item.queue_delay > 0]
            events: list[tuple[int, int]] = []
            for item in class_assignments:
                amount = len(item.resource_allocations[resource_class])
                events.append((item.start, amount))
                events.append((item.finish, -amount))
            usage = 0
            peak_concurrent_usage = 0
            for _, delta in sorted(events, key=lambda item: (item[0], 0 if item[1] < 0 else 1, item[1])):
                usage += delta
                peak_concurrent_usage = max(peak_concurrent_usage, usage)
            resource_summaries.append(
                ResourceClassSummary(
                    resource_class=resource_class,
                    capacity=capacity,
                    task_count=len(class_assignments),
                    total_reserved_units=total_reserved_units,
                    peak_concurrent_usage=peak_concurrent_usage,
                    utilization=class_utilization,
                    idle_capacity=class_idle_capacity,
                    delayed_tasks=len(delayed),
                    max_queue_delay=max((item.queue_delay for item in delayed), default=0),
                )
            )

    return WorkerLimitedSchedule(
        worker_limit=worker_limit,
        strategy=resolved_strategy,
        makespan=makespan,
        unlimited_makespan=plan.total_duration,
        total_work=total_work,
        theoretical_lower_bound=theoretical_lower_bound,
        idle_capacity=idle_capacity,
        utilization=utilization,
        dispatch_order=dispatch_order,
        assignments=assignments,
        worker_timelines=worker_timelines,
        resource_capacities=resolved_resource_capacities,
        resource_summaries=resource_summaries,
    )


def plan_to_dict(plan: PlanResult) -> dict:
    return {
        "order": plan.order,
        "layers": plan.layers,
        "total_duration": plan.total_duration,
        "critical_path": plan.critical_path,
        "timings": [
            {
                "name": item.name,
                "duration": item.duration,
                "earliest_start": item.earliest_start,
                "earliest_finish": item.earliest_finish,
                "latest_start": item.latest_start,
                "latest_finish": item.latest_finish,
                "slack": item.slack,
                "critical": item.critical,
            }
            for item in plan.timings
        ],
    }


def schedule_to_dict(schedule: WorkerLimitedSchedule) -> dict:
    return {
        "worker_limit": schedule.worker_limit,
        "strategy": schedule.strategy,
        "makespan": schedule.makespan,
        "unlimited_makespan": schedule.unlimited_makespan,
        "theoretical_lower_bound": schedule.theoretical_lower_bound,
        "total_work": schedule.total_work,
        "idle_capacity": schedule.idle_capacity,
        "utilization": round(schedule.utilization, 6),
        "resource_capacities": schedule.resource_capacities,
        "resource_summaries": [
            {
                "resource_class": item.resource_class,
                "capacity": item.capacity,
                "task_count": item.task_count,
                "total_reserved_units": item.total_reserved_units,
                "peak_concurrent_usage": item.peak_concurrent_usage,
                "utilization": round(item.utilization, 6),
                "idle_capacity": item.idle_capacity,
                "delayed_tasks": item.delayed_tasks,
                "max_queue_delay": item.max_queue_delay,
            }
            for item in schedule.resource_summaries
        ],
        "dispatch_order": schedule.dispatch_order,
        "assignments": [
            {
                "name": item.name,
                "worker": item.worker,
                "ready_at": item.ready_at,
                "start": item.start,
                "finish": item.finish,
                "queue_delay": item.queue_delay,
                "duration": item.duration,
                "critical": item.critical,
                "resource_class": item.resource_class,
                "resource_slot": item.resource_slot,
                "resource_demands": item.resource_demands,
                "resource_allocations": {
                    resource_class: list(slots)
                    for resource_class, slots in item.resource_allocations.items()
                },
            }
            for item in schedule.assignments
        ],
        "worker_timelines": [
            [
                {
                    "name": item.name,
                    "start": item.start,
                    "finish": item.finish,
                    "queue_delay": item.queue_delay,
                    "critical": item.critical,
                    "resource_class": item.resource_class,
                    "resource_slot": item.resource_slot,
                    "resource_demands": item.resource_demands,
                    "resource_allocations": {
                        resource_class: list(slots)
                        for resource_class, slots in item.resource_allocations.items()
                    },
                }
                for item in timeline
            ]
            for timeline in schedule.worker_timelines
        ],
    }


def _format_resource_demands(resource_demands: dict[str, int], *, empty: str = "") -> str:
    if not resource_demands:
        return empty
    rendered: list[str] = []
    for resource_class, demand in resource_demands.items():
        rendered.append(resource_class if demand == 1 else f"{resource_class}×{demand}")
    return ", ".join(rendered)


def _format_resource_allocations(resource_allocations: dict[str, tuple[int, ...]], *, empty: str = "") -> str:
    if not resource_allocations:
        return empty
    rendered: list[str] = []
    for resource_class, slots in resource_allocations.items():
        if len(slots) == 1:
            rendered.append(f"{resource_class}#{slots[0]}")
        else:
            rendered.append(f"{resource_class}#{{{','.join(str(slot) for slot in slots)}}}")
    return " + ".join(rendered)


def _format_assignment_resource(item: ScheduledTask) -> str:
    rendered = _format_resource_allocations(item.resource_allocations)
    return f" [{rendered}]" if rendered else ""


def _render_text_plan(plan: PlanResult) -> str:
    lines = [
        f"topological order: {', '.join(plan.order)}",
        f"parallel layers: {' | '.join(', '.join(layer) for layer in plan.layers)}",
        f"estimated makespan: {plan.total_duration}",
        f"critical path: {', '.join(plan.critical_path) if plan.critical_path else '(none)'}",
        "timings:",
    ]
    for item in plan.timings:
        flag = "critical" if item.critical else f"slack={item.slack}"
        lines.append(
            f"- {item.name}: duration={item.duration}, ES={item.earliest_start}, EF={item.earliest_finish}, "
            f"LS={item.latest_start}, LF={item.latest_finish}, {flag}"
        )
    return "\n".join(lines)


def _render_text_schedule(schedule: WorkerLimitedSchedule) -> str:
    lines = [
        (
            f"worker-limited schedule: workers={schedule.worker_limit}, strategy={schedule.strategy}, makespan={schedule.makespan}, "
            f"unlimited={schedule.unlimited_makespan}, lower_bound={schedule.theoretical_lower_bound}"
        ),
        (
            f"capacity utilization: {schedule.utilization * 100:.1f}% "
            f"(idle capacity={schedule.idle_capacity})"
        ),
        f"dispatch order: {', '.join(schedule.dispatch_order)}",
    ]
    if schedule.resource_capacities:
        rendered_caps = ", ".join(
            f"{resource_class}={capacity}" for resource_class, capacity in schedule.resource_capacities.items()
        )
        lines.append(f"resource capacities: {rendered_caps}")
    lines.append("worker timelines:")
    for index, timeline in enumerate(schedule.worker_timelines, start=1):
        if not timeline:
            lines.append(f"- worker {index}: (idle)")
            continue
        rendered = ", ".join(
            f"{item.name} [{item.start}→{item.finish}]{_format_assignment_resource(item)}" for item in timeline
        )
        lines.append(f"- worker {index}: {rendered}")

    if schedule.resource_summaries:
        lines.append("resource-class usage:")
        for item in schedule.resource_summaries:
            lines.append(
                f"- {item.resource_class}: capacity={item.capacity}, tasks={item.task_count}, "
                f"reserved={item.total_reserved_units}, peak={item.peak_concurrent_usage}, "
                f"utilization={item.utilization * 100:.1f}%, idle={item.idle_capacity}, "
                f"delayed={item.delayed_tasks}, max_queue_delay={item.max_queue_delay}"
            )

    delayed = [item for item in schedule.assignments if item.queue_delay > 0]
    if delayed:
        lines.append("queue delays:")
        for item in delayed:
            lines.append(
                f"- {item.name}: ready={item.ready_at}, start={item.start}, delay={item.queue_delay}, worker={item.worker}, resources={_format_resource_allocations(item.resource_allocations, empty='—')}"
            )
    return "\n".join(lines)


def _quote_dot(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return '"' + escaped + '"'


def _escape_mermaid(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;").replace("\n", "<br/>")


def _diagram_label(task: Task, timing: TaskTiming) -> str:
    lines = [timing.name, f"d={timing.duration}, slack={timing.slack}"]
    rendered_resources = _format_resource_demands(task.resource_demands)
    if rendered_resources:
        lines.append(f"resources={rendered_resources}")
    return "\n".join(lines)


def render_dependency_diagram(tasks: dict[str, Task], plan: PlanResult, *, diagram_format: str) -> str:
    timings = {timing.name: timing for timing in plan.timings}
    critical_nodes = set(plan.critical_path)
    critical_edges = set(zip(plan.critical_path, plan.critical_path[1:]))

    if diagram_format == "mermaid":
        node_ids = {name: f"task_{index}" for index, name in enumerate(plan.order)}
        lines = [
            "flowchart LR",
            f"  %% makespan={plan.total_duration}",
            f"  %% critical_path={','.join(plan.critical_path)}",
            "  classDef critical fill:#fee2e2,stroke:#b91c1c,stroke-width:2px",
        ]
        for layer_index, layer in enumerate(plan.layers):
            lines.append(f'  subgraph layer_{layer_index}["layer {layer_index}"]')
            for name in layer:
                label = _escape_mermaid(_diagram_label(tasks[name], timings[name]))
                lines.append(f'    {node_ids[name]}["{label}"]')
            lines.append("  end")
        for name in plan.order:
            for dep in tasks[name].deps:
                lines.append(f"  {node_ids[dep]} --> {node_ids[name]}")
        if critical_nodes:
            lines.append("  class " + ",".join(node_ids[name] for name in plan.critical_path) + " critical")
        return "\n".join(lines)

    if diagram_format != "dot":
        raise ValueError("diagram_format must be 'mermaid' or 'dot'")

    lines = [
        "digraph DependencyGraph {",
        "  rankdir=LR;",
        f"  label={_quote_dot(f'Dependency graph (makespan={plan.total_duration})')};",
        "  labelloc=t;",
        '  node [shape=box, style="rounded", fontname="Helvetica"];',
        '  edge [fontname="Helvetica"];',
    ]
    for layer_index, layer in enumerate(plan.layers):
        lines.append(f"  subgraph layer_{layer_index} {{")
        lines.append("    rank=same;")
        for name in layer:
            attributes = [f"label={_quote_dot(_diagram_label(tasks[name], timings[name]))}"]
            if name in critical_nodes:
                attributes.extend(['color="firebrick"', "penwidth=2", "peripheries=2"])
            lines.append(f"    {_quote_dot(name)} [{', '.join(attributes)}];")
        lines.append("  }")
    for name in plan.order:
        for dep in tasks[name].deps:
            edge_attributes = []
            if (dep, name) in critical_edges:
                edge_attributes.extend(['color="firebrick"', "penwidth=2"])
            attribute_suffix = f" [{', '.join(edge_attributes)}]" if edge_attributes else ""
            lines.append(f"  {_quote_dot(dep)} -> {_quote_dot(name)}{attribute_suffix};")
    lines.append("}")
    return "\n".join(lines)


def _markdown_code(value: object) -> str:
    return f"`{str(value).replace('`', '\\`')}`"


def _escape_markdown_table_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br/>")


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _truncate_display(value: str, *, limit: int = 22) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _build_schedule_artifact_filename(
    stem: str,
    schedule: WorkerLimitedSchedule,
    *,
    include_strategy_in_key: bool,
) -> str:
    filename = f"{stem}_{_worker_limit_slug(schedule.worker_limit)}"
    if include_strategy_in_key or schedule.strategy != DEFAULT_SCHEDULE_STRATEGY:
        filename += f"_{_strategy_slug(schedule.strategy)}"
    return filename


def _parse_schedule_artifact_entries(schedule_paths: dict[str, str]) -> list[tuple[str, int, str | None, str]]:
    parsed_schedule_paths: list[tuple[str, int, str | None, str]] = []
    for raw_key, path in schedule_paths.items():
        if ":" in raw_key:
            raw_limit, strategy = raw_key.split(":", maxsplit=1)
            parsed_schedule_paths.append((raw_key, int(raw_limit), strategy, path))
        else:
            parsed_schedule_paths.append((raw_key, int(raw_key), None, path))
    parsed_schedule_paths.sort(
        key=lambda item: (item[1], SCHEDULE_STRATEGIES.index(item[2]) if item[2] else -1)
    )
    return parsed_schedule_paths


def _stable_svg_color(value: str) -> tuple[str, str]:
    palette = [
        ("#dbeafe", "#1d4ed8"),
        ("#dcfce7", "#15803d"),
        ("#fef3c7", "#b45309"),
        ("#ede9fe", "#6d28d9"),
        ("#fae8ff", "#a21caf"),
        ("#cffafe", "#0f766e"),
        ("#fee2e2", "#b91c1c"),
        ("#e0f2fe", "#0369a1"),
    ]
    index = sum((idx + 1) * ord(char) for idx, char in enumerate(value)) % len(palette)
    return palette[index]


def render_schedule_timeline_svg(schedule: WorkerLimitedSchedule, *, title: str) -> str:
    title_id = "schedule-title"
    desc_id = "schedule-desc"
    width = 1280
    chart_left = 190
    chart_right = width - 40
    chart_width = chart_right - chart_left
    chart_top = 150
    lane_height = 52
    lane_gap = 18
    bar_height = 30
    makespan = max(schedule.makespan, 1)
    tick_step = max(1, (makespan + 11) // 12)
    unit_width = chart_width / makespan
    resource_section_height = 34 + 22 * len(schedule.resource_summaries) if schedule.resource_summaries else 0
    chart_bottom = chart_top + len(schedule.worker_timelines) * (lane_height + lane_gap) - lane_gap
    footer_top = chart_bottom + 34
    height = footer_top + 110 + resource_section_height

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
        f'  <title id="{title_id}">{_html_escape(title)}</title>',
        (
            f'  <desc id="{desc_id}">Worker timeline for {_html_escape(title)} '
            f'with {_html_escape(_format_worker_limit_label(schedule.worker_limit))}, '
            f'strategy {_html_escape(_format_schedule_strategy_label(schedule.strategy))}, and makespan {schedule.makespan}.</desc>'
        ),
        '  <rect width="100%" height="100%" fill="#f8fafc" />',
        f'  <rect x="20" y="20" width="{width - 40}" height="{height - 40}" rx="28" fill="#ffffff" stroke="#d7dde8" stroke-width="2" />',
        f'  <text x="48" y="62" font-size="30" font-weight="700" fill="#0f172a">{_html_escape(title)}</text>',
        (
            '  <text x="48" y="92" font-size="16" fill="#475569">'
            f'{_html_escape(_format_worker_limit_label(schedule.worker_limit))} · '
            f'{_html_escape(_format_schedule_strategy_label(schedule.strategy))} · '
            f'makespan {schedule.makespan} · utilization {_format_percent(schedule.utilization)} · '
            f'idle capacity {schedule.idle_capacity}</text>'
        ),
        (
            '  <text x="48" y="118" font-size="14" fill="#64748b">'
            f'Unlimited bound {schedule.unlimited_makespan} · theoretical lower bound {schedule.theoretical_lower_bound} · '
            f'dispatch order {_html_escape(", ".join(schedule.dispatch_order))}</text>'
        ),
        f'  <line x1="{chart_left}" y1="{chart_top - 12}" x2="{chart_left}" y2="{chart_bottom + 8}" stroke="#0f172a" stroke-width="2" />',
        f'  <line x1="{chart_left}" y1="{chart_bottom + 8}" x2="{chart_right}" y2="{chart_bottom + 8}" stroke="#0f172a" stroke-width="2" />',
    ]

    ticks = list(range(0, makespan + 1, tick_step))
    if ticks[-1] != makespan:
        ticks.append(makespan)
    for tick in ticks:
        x = chart_left + tick * unit_width
        lines.append(
            f'  <line x1="{x:.2f}" y1="{chart_top - 12}" x2="{x:.2f}" y2="{chart_bottom + 8}" stroke="#dbe4f0" stroke-width="1" />'
        )
        lines.append(
            f'  <text x="{x:.2f}" y="{chart_top - 20}" font-size="13" text-anchor="middle" fill="#64748b">{tick}</text>'
        )

    for index, timeline in enumerate(schedule.worker_timelines, start=1):
        lane_y = chart_top + (index - 1) * (lane_height + lane_gap)
        bar_y = lane_y + (lane_height - bar_height) / 2
        lines.append(
            f'  <rect x="32" y="{lane_y}" width="{width - 64}" height="{lane_height}" rx="16" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1" />'
        )
        lines.append(
            f'  <text x="56" y="{lane_y + 31}" font-size="15" font-weight="600" fill="#0f172a">Worker {index}</text>'
        )
        if not timeline:
            lines.append(
                f'  <text x="{chart_left + 16}" y="{lane_y + 31}" font-size="14" fill="#94a3b8">idle for entire schedule</text>'
            )
            continue
        for item in timeline:
            fill, stroke = ("#fee2e2", "#b91c1c") if item.critical else _stable_svg_color(item.name)
            x = chart_left + item.start * unit_width
            width_value = max((item.finish - item.start) * unit_width, 14)
            label = _truncate_display(item.name, limit=24)
            queue_suffix = f"; queue delay {item.queue_delay}" if item.queue_delay else ""
            resource_text = _format_resource_allocations(item.resource_allocations)
            resource_suffix = f"; resources {resource_text}" if resource_text else ""
            lines.extend(
                [
                    '  <g>',
                    f'    <title>{_html_escape(item.name)} — worker {item.worker}, {item.start}→{item.finish}, duration {item.duration}{queue_suffix}{resource_suffix}</title>',
                    (
                        f'    <rect x="{x:.2f}" y="{bar_y:.2f}" width="{width_value:.2f}" height="{bar_height}" '
                        f'rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2" />'
                    ),
                ]
            )
            if width_value >= 74:
                lines.append(
                    f'    <text x="{x + 8:.2f}" y="{bar_y + 19:.2f}" font-size="13" fill="#0f172a">{_html_escape(label)}</text>'
                )
            else:
                lines.append(
                    f'    <text x="{x + width_value + 6:.2f}" y="{bar_y + 19:.2f}" font-size="12" fill="#475569">{_html_escape(label)}</text>'
                )
            lines.append('  </g>')
            if item.queue_delay:
                lines.append(
                    f'  <text x="{x + width_value / 2:.2f}" y="{bar_y + bar_height + 14:.2f}" font-size="11" text-anchor="middle" fill="#b45309">delay {item.queue_delay}</text>'
                )

    summary_y = footer_top
    lines.extend(
        [
            f'  <rect x="40" y="{summary_y}" width="{width - 80}" height="76" rx="22" fill="#eef2ff" stroke="#c7d2fe" stroke-width="1.5" />',
            f'  <text x="64" y="{summary_y + 28}" font-size="18" font-weight="700" fill="#312e81">Schedule summary</text>',
            (
                f'  <text x="64" y="{summary_y + 54}" font-size="14" fill="#4338ca">'
                f'Critical tasks are highlighted in red. Worker lanes show deterministic dispatch over {_html_escape(_format_worker_limit_label(schedule.worker_limit))}.</text>'
            ),
        ]
    )
    if schedule.resource_capacities:
        rendered_caps = ", ".join(
            f"{resource_class}={capacity}" for resource_class, capacity in schedule.resource_capacities.items()
        )
        lines.append(
            f'  <text x="64" y="{summary_y + 76}" font-size="13" fill="#475569">Renewable resource caps: {_html_escape(rendered_caps)}</text>'
        )
    else:
        lines.append(
            f'  <text x="64" y="{summary_y + 76}" font-size="13" fill="#475569">No renewable resource caps were required for this schedule.</text>'
        )

    if schedule.resource_summaries:
        resource_y = summary_y + 110
        lines.append(
            f'  <text x="48" y="{resource_y}" font-size="18" font-weight="700" fill="#0f172a">Resource utilization</text>'
        )
        for offset, item in enumerate(schedule.resource_summaries, start=1):
            y = resource_y + offset * 22
            lines.append(
                f'  <text x="64" y="{y}" font-size="13" fill="#475569">{_html_escape(item.resource_class)}: capacity {item.capacity}, peak {item.peak_concurrent_usage}, utilization {_format_percent(item.utilization)}, delayed tasks {item.delayed_tasks}, max queue delay {item.max_queue_delay}</text>'
            )

    lines.append('</svg>')
    return "\n".join(lines)


def _humanize_stem(value: str) -> str:
    return value.replace("-", " ").replace("_", " ").strip() or value


def _pluralize(value: int, singular: str, plural: str | None = None) -> str:
    resolved_plural = plural or f"{singular}s"
    return singular if value == 1 else resolved_plural


def _worker_limit_slug(worker_limit: int) -> str:
    return "single_worker" if worker_limit == 1 else f"{worker_limit}_workers"


def _format_worker_limit_label(worker_limit: int) -> str:
    return f"{worker_limit} {_pluralize(worker_limit, 'worker')}"


def _format_schedule_strategy_label(strategy: str) -> str:
    return strategy


def _strategy_dispatch_blurb(strategy: str) -> str:
    if strategy == "critical-first":
        return "critical-first, low-slack, longer-duration tie-breaking"
    if strategy == "fifo":
        return "FIFO ready-queue order"
    if strategy == "longest-processing-time":
        return "longest-processing-time-first ready-queue ordering"
    return strategy


def _strategy_slug(strategy: str) -> str:
    return strategy.replace("-", "_")


def _collect_report_worker_limits(
    *,
    worker_limit: int | None,
    compare_worker_limits: Sequence[int] | None = None,
) -> list[int]:
    ordered: list[int] = []
    if worker_limit is not None:
        ordered.append(worker_limit)
    if compare_worker_limits:
        ordered.extend(compare_worker_limits)

    unique: list[int] = []
    seen: set[int] = set()
    for limit in ordered:
        if limit in seen:
            continue
        seen.add(limit)
        unique.append(limit)
    return sorted(unique)


def _collect_report_strategies(
    *,
    strategy: str | None,
    compare_strategies: Sequence[str] | None = None,
) -> list[str]:
    ordered = [_resolve_schedule_strategy(strategy)]
    if compare_strategies:
        ordered.extend(_resolve_schedule_strategy(item) for item in compare_strategies)

    unique: list[str] = []
    seen: set[str] = set()
    for item in ordered:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _ordered_report_comparison_schedules(
    *,
    worker_limited_schedule: WorkerLimitedSchedule | None,
    comparison_schedules: Sequence[WorkerLimitedSchedule] | None,
) -> list[WorkerLimitedSchedule]:
    comparison_schedule_lookup = {schedule.worker_limit: schedule for schedule in comparison_schedules or ()}
    if worker_limited_schedule is not None:
        comparison_schedule_lookup.setdefault(worker_limited_schedule.worker_limit, worker_limited_schedule)
    return [comparison_schedule_lookup[limit] for limit in sorted(comparison_schedule_lookup)]


def _ordered_report_strategy_schedules(
    *,
    worker_limited_schedule: WorkerLimitedSchedule | None,
    strategy_comparison_schedules: Sequence[WorkerLimitedSchedule] | None,
) -> list[WorkerLimitedSchedule]:
    ordered: list[WorkerLimitedSchedule] = []
    seen_strategies: set[str] = set()
    if worker_limited_schedule is not None:
        ordered.append(worker_limited_schedule)
        seen_strategies.add(worker_limited_schedule.strategy)
    for schedule in strategy_comparison_schedules or ():
        if schedule.strategy in seen_strategies:
            continue
        ordered.append(schedule)
        seen_strategies.add(schedule.strategy)
    return ordered


def _display_path_label(path: str | Path) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        return candidate.as_posix()
    try:
        return candidate.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return candidate.as_posix()



def build_report_title(
    *,
    source_label: str,
    explicit_title: str | None = None,
    manifest_title: str | None = None,
) -> str:
    if explicit_title:
        return explicit_title
    if manifest_title:
        return manifest_title
    display_name = _humanize_stem(Path(source_label).stem).title()
    return f"Dependency graph walkthrough — {display_name}"


def build_report_description(*, source_label: str, manifest_description: str | None = None) -> str:
    if manifest_description:
        return manifest_description
    display_name = _humanize_stem(Path(source_label).stem).title()
    return (
        f"Recruiter-friendly walkthrough of {display_name}'s dependency graph, critical path, "
        "and constrained scheduling evidence."
    )


def build_benchmark_title(*, source_label: str, explicit_title: str | None = None) -> str:
    if explicit_title:
        return explicit_title
    display_name = _humanize_stem(Path(source_label).stem).title()
    return f"Dependency graph benchmark suite — {display_name}"


def render_mermaid_wrapper(diagram: str, *, source_label: str) -> str:
    title = f"Dependency graph — {_humanize_stem(Path(source_label).stem).title()}"
    return f"# {title}\n\n```mermaid\n{diagram}\n```\n"


def _relative_markdown_link(target_path: str | Path, *, from_path: str | Path) -> str:
    return Path(os.path.relpath(Path(target_path), start=Path(from_path).parent)).as_posix()


def _write_text(path: str | Path, content: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_report_supporting_artifacts(
    tasks: dict[str, Task],
    plan: PlanResult,
    *,
    graph_path: str | Path,
    output_dir: str | Path,
    worker_limited_schedule: WorkerLimitedSchedule | None = None,
    comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
    strategy_comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(graph_path).stem

    mermaid_path = output_dir / f"{stem}.mmd"
    dot_path = output_dir / f"{stem}.dot"
    mermaid_preview_path = output_dir / f"{stem}_mermaid.md"

    mermaid_diagram = render_dependency_diagram(tasks, plan, diagram_format="mermaid")
    dot_diagram = render_dependency_diagram(tasks, plan, diagram_format="dot")

    _write_text(mermaid_path, mermaid_diagram + "\n")
    _write_text(dot_path, dot_diagram + "\n")
    _write_text(mermaid_preview_path, render_mermaid_wrapper(mermaid_diagram, source_label=str(graph_path)))

    artifacts: dict[str, Any] = {
        "mermaid_source": str(mermaid_path),
        "mermaid_preview": str(mermaid_preview_path),
        "dot_source": str(dot_path),
    }

    schedule_lookup: dict[tuple[int, str], WorkerLimitedSchedule] = {}
    for schedule in comparison_schedules or ():
        schedule_lookup[(schedule.worker_limit, schedule.strategy)] = schedule
    for schedule in strategy_comparison_schedules or ():
        schedule_lookup[(schedule.worker_limit, schedule.strategy)] = schedule
    if worker_limited_schedule is not None:
        schedule_lookup[(worker_limited_schedule.worker_limit, worker_limited_schedule.strategy)] = worker_limited_schedule

    if schedule_lookup:
        schedule_paths: dict[str, str] = {}
        schedule_svg_paths: dict[str, str] = {}
        include_strategy_in_key = len({schedule.strategy for schedule in schedule_lookup.values()}) > 1 or any(
            schedule.strategy != DEFAULT_SCHEDULE_STRATEGY for schedule in schedule_lookup.values()
        )
        ordered_schedules = sorted(
            schedule_lookup.values(),
            key=lambda item: (item.worker_limit, SCHEDULE_STRATEGIES.index(item.strategy), item.dispatch_order),
        )
        base_title = _humanize_stem(stem).title()
        for schedule in ordered_schedules:
            key = (
                f"{schedule.worker_limit}:{schedule.strategy}"
                if include_strategy_in_key
                else str(schedule.worker_limit)
            )
            filename = _build_schedule_artifact_filename(
                stem,
                schedule,
                include_strategy_in_key=include_strategy_in_key,
            )
            schedule_json_path = output_dir / f"{filename}_schedule.json"
            schedule_svg_path = output_dir / f"{filename}_schedule.svg"
            _write_text(schedule_json_path, json.dumps(schedule_to_dict(schedule), indent=2) + "\n")
            _write_text(
                schedule_svg_path,
                render_schedule_timeline_svg(
                    schedule,
                    title=(
                        f"Dependency graph schedule — {base_title} — "
                        f"{_format_worker_limit_label(schedule.worker_limit)} — "
                        f"{_format_schedule_strategy_label(schedule.strategy)}"
                    ),
                ),
            )
            schedule_paths[key] = str(schedule_json_path)
            schedule_svg_paths[key] = str(schedule_svg_path)
        artifacts["worker_limited_schedule_jsons"] = schedule_paths
        artifacts["worker_limited_schedule_svgs"] = schedule_svg_paths
        if worker_limited_schedule is not None:
            primary_key = (
                f"{worker_limited_schedule.worker_limit}:{worker_limited_schedule.strategy}"
                if include_strategy_in_key
                else str(worker_limited_schedule.worker_limit)
            )
            artifacts["worker_limited_schedule_json"] = schedule_paths[primary_key]
            artifacts["worker_limited_schedule_svg"] = schedule_svg_paths[primary_key]
        elif len(schedule_paths) == 1:
            artifacts["worker_limited_schedule_json"] = next(iter(schedule_paths.values()))
            artifacts["worker_limited_schedule_svg"] = next(iter(schedule_svg_paths.values()))

    return artifacts

def render_report_markdown(
    tasks: dict[str, Task],
    plan: PlanResult,
    *,
    source_label: str,
    title: str | None = None,
    manifest_title: str | None = None,
    manifest_description: str | None = None,
    diagram_links: Sequence[tuple[str, str]] | None = None,
    worker_limited_schedule: WorkerLimitedSchedule | None = None,
    comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
    strategy_comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
) -> str:
    resolved_title = build_report_title(
        source_label=source_label,
        explicit_title=title,
        manifest_title=manifest_title,
    )
    resolved_description = build_report_description(
        source_label=source_label,
        manifest_description=manifest_description,
    )
    timings_by_name = {timing.name: timing for timing in plan.timings}
    layer_by_name = {name: index for index, layer in enumerate(plan.layers) for name in layer}
    total_slack = sum(item.slack for item in plan.timings if not item.critical)
    widest_layer_index, widest_layer = max(
        enumerate(plan.layers),
        key=lambda item: (len(item[1]), -item[0]),
        default=(0, []),
    )
    critical_path_rendered = " -> ".join(plan.critical_path) if plan.critical_path else "(none)"
    ordered_comparison_schedules = _ordered_report_comparison_schedules(
        worker_limited_schedule=worker_limited_schedule,
        comparison_schedules=comparison_schedules,
    )
    ordered_strategy_schedules = _ordered_report_strategy_schedules(
        worker_limited_schedule=worker_limited_schedule,
        strategy_comparison_schedules=strategy_comparison_schedules,
    )

    lines = [f"# {resolved_title}", "", resolved_description, ""]
    lines.extend(
        [
            f"- Source manifest: {_markdown_code(source_label)}",
            f"- Task count: {_markdown_code(len(tasks))}",
            f"- Parallel layers: {_markdown_code(len(plan.layers))}",
            f"- Estimated makespan: {_markdown_code(plan.total_duration)}",
            f"- Critical path: {_markdown_code(critical_path_rendered)}",
        ]
    )

    if worker_limited_schedule:
        lines.append(
            f"- Worker-limited makespan ({_format_worker_limit_label(worker_limited_schedule.worker_limit)}): {_markdown_code(worker_limited_schedule.makespan)}"
        )
        lines.append(
            f"- Worker-limited strategy: {_markdown_code(_format_schedule_strategy_label(worker_limited_schedule.strategy))}"
        )
    elif ordered_comparison_schedules:
        labels = ", ".join(_markdown_code(_format_worker_limit_label(schedule.worker_limit)) for schedule in ordered_comparison_schedules)
        lines.append(f"- Worker-cap comparison set: {labels}")

    if diagram_links:
        lines.extend(["", "## Linked artifacts", ""])
        for label, target in diagram_links:
            lines.append(f"- [{label}]({target})")

    lines.extend(
        [
            "",
            "## Portfolio summary",
            "",
            f"- deterministic ready-queue ordering keeps the plan stable: {_markdown_code(', '.join(plan.order))}",
            (
                f"- widest parallel layer: {_markdown_code(f'layer {widest_layer_index}')} with "
                f"{_markdown_code(len(widest_layer))} task(s)"
                + (
                    ": " + ", ".join(_markdown_code(name) for name in widest_layer)
                    if widest_layer
                    else ""
                )
            ),
            f"- non-critical slack budget available for schedule tradeoffs: {_markdown_code(total_slack)} time units",
        ]
    )

    if worker_limited_schedule:
        delayed = [item for item in worker_limited_schedule.assignments if item.queue_delay > 0]
        most_delayed = max(
            delayed,
            key=lambda item: (item.queue_delay, item.duration, item.name),
            default=None,
        )
        delta = worker_limited_schedule.makespan - worker_limited_schedule.unlimited_makespan
        lines.extend(
            [
                (
                    f"- worker-limited dispatch uses {_strategy_dispatch_blurb(worker_limited_schedule.strategy)} across "
                    f"{_markdown_code(_format_worker_limit_label(worker_limited_schedule.worker_limit))}"
                ),
                (
                    f"- worker cap increases makespan by {_markdown_code(delta)} time unit(s) "
                    f"over the unlimited-layer bound of {_markdown_code(worker_limited_schedule.unlimited_makespan)}"
                ),
                (
                    f"- utilization under the worker cap: {_markdown_code(f'{worker_limited_schedule.utilization * 100:.1f}%')} "
                    f"with {_markdown_code(worker_limited_schedule.idle_capacity)} idle worker-time unit(s)"
                ),
            ]
        )
        if most_delayed:
            rendered_delay_resources = _format_resource_allocations(most_delayed.resource_allocations)
            resource_suffix = f" on {_markdown_code(rendered_delay_resources)}" if rendered_delay_resources else ""
            lines.append(
                f"- biggest queue delay: {_markdown_code(most_delayed.name)} waited {_markdown_code(most_delayed.queue_delay)} time unit(s) after becoming ready{resource_suffix}"
            )
        if worker_limited_schedule.resource_capacities:
            rendered_caps = ", ".join(
                f"{name}={capacity}" for name, capacity in worker_limited_schedule.resource_capacities.items()
            )
            lines.append(
                f"- renewable resource caps active for the constrained run: {_markdown_code(rendered_caps)}"
            )

    if ordered_comparison_schedules:
        comparison_summary = ", ".join(
            f"{_format_worker_limit_label(schedule.worker_limit)} → {schedule.makespan}"
            for schedule in ordered_comparison_schedules
        )
        lines.append(
            f"- compared worker caps against the unlimited baseline of {_markdown_code(plan.total_duration)}: {_markdown_code(comparison_summary)}"
        )

    if len(ordered_strategy_schedules) > 1:
        strategy_summary = ", ".join(
            f"{_format_schedule_strategy_label(schedule.strategy)} → {schedule.makespan}"
            for schedule in ordered_strategy_schedules
        )
        lines.append(
            f"- compared scheduling strategies at {_markdown_code(_format_worker_limit_label(ordered_strategy_schedules[0].worker_limit))}: {_markdown_code(strategy_summary)}"
        )

    lines.extend(
        [
            "",
            "## Parallel layer windows",
            "",
        ]
    )

    for index, layer in enumerate(plan.layers):
        if not layer:
            lines.append(f"- Layer {index}: no tasks")
            continue
        starts = [timings_by_name[name].earliest_start for name in layer]
        finishes = [timings_by_name[name].earliest_finish for name in layer]
        rendered_tasks = ", ".join(_markdown_code(name) for name in layer)
        lines.append(
            f"- Layer {index} ({_markdown_code(min(starts))} → {_markdown_code(max(finishes))}): {rendered_tasks}"
        )

    if ordered_comparison_schedules:
        lines.extend(
            [
                "",
                "## Worker-capacity comparison",
                "",
                "| Worker limit | Makespan | Δ vs unlimited | Lower bound | Utilization | Idle capacity | Delayed tasks | Max queue delay |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for schedule in ordered_comparison_schedules:
            delayed = [item for item in schedule.assignments if item.queue_delay > 0]
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_markdown_table_cell(_format_worker_limit_label(schedule.worker_limit)),
                        str(schedule.makespan),
                        str(schedule.makespan - schedule.unlimited_makespan),
                        str(schedule.theoretical_lower_bound),
                        f"{schedule.utilization * 100:.1f}%",
                        str(schedule.idle_capacity),
                        str(len(delayed)),
                        str(max((item.queue_delay for item in delayed), default=0)),
                    ]
                )
                + " |"
            )

    if len(ordered_strategy_schedules) > 1:
        baseline_makespan = ordered_strategy_schedules[0].makespan
        lines.extend(
            [
                "",
                "## Scheduling-strategy comparison",
                "",
                "| Strategy | Makespan | Δ vs unlimited | Δ vs primary strategy | Delayed tasks | Max queue delay | Dispatch order |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for schedule in ordered_strategy_schedules:
            delayed = [item for item in schedule.assignments if item.queue_delay > 0]
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_markdown_table_cell(_format_schedule_strategy_label(schedule.strategy)),
                        str(schedule.makespan),
                        str(schedule.makespan - schedule.unlimited_makespan),
                        str(schedule.makespan - baseline_makespan),
                        str(len(delayed)),
                        str(max((item.queue_delay for item in delayed), default=0)),
                        _escape_markdown_table_cell(", ".join(schedule.dispatch_order)),
                    ]
                )
                + " |"
            )

    if worker_limited_schedule:
        lines.extend(
            [
                "",
                "## Worker-limited comparison",
                "",
                f"- Worker limit: {_markdown_code(worker_limited_schedule.worker_limit)}",
                f"- Strategy: {_markdown_code(_format_schedule_strategy_label(worker_limited_schedule.strategy))}",
                f"- Total work: {_markdown_code(worker_limited_schedule.total_work)}",
                f"- Theoretical lower bound: {_markdown_code(worker_limited_schedule.theoretical_lower_bound)}",
                f"- Unlimited layered makespan: {_markdown_code(worker_limited_schedule.unlimited_makespan)}",
                f"- Worker-limited makespan: {_markdown_code(worker_limited_schedule.makespan)}",
                f"- Dispatch order: {_markdown_code(', '.join(worker_limited_schedule.dispatch_order))}",
                "",
                "### Worker timelines",
                "",
            ]
        )
        for index, timeline in enumerate(worker_limited_schedule.worker_timelines, start=1):
            if not timeline:
                lines.append(f"- Worker {index}: {_markdown_code('idle for the full run')}")
                continue
            window = f"{timeline[0].start} → {timeline[-1].finish}"
            tasks_rendered = ", ".join(
                f"{item.name} ({item.start}→{item.finish}){_format_assignment_resource(item)}" for item in timeline
            )
            lines.append(
                f"- Worker {index} ({_markdown_code(window)}): {tasks_rendered}"
            )

        if worker_limited_schedule.resource_summaries:
            lines.extend(
                [
                    "",
                    "### Resource-class utilization",
                    "",
                    "| Resource class | Capacity | Tasks | Reserved units | Peak concurrent usage | Utilization | Idle capacity | Delayed tasks | Max queue delay |",
                    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
                ]
            )
            for item in worker_limited_schedule.resource_summaries:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _escape_markdown_table_cell(item.resource_class),
                            str(item.capacity),
                            str(item.task_count),
                            str(item.total_reserved_units),
                            str(item.peak_concurrent_usage),
                            f"{item.utilization * 100:.1f}%",
                            str(item.idle_capacity),
                            str(item.delayed_tasks),
                            str(item.max_queue_delay),
                        ]
                    )
                    + " |"
                )

        lines.extend(
            [
                "",
                "### Worker-limited task table",
                "",
                "| Task | Worker | Resource demands | Resource allocations | Ready at | Start | Finish | Queue delay | Critical |",
                "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for item in worker_limited_schedule.assignments:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_markdown_table_cell(item.name),
                        str(item.worker),
                        _escape_markdown_table_cell(_format_resource_demands(item.resource_demands, empty="—")),
                        _escape_markdown_table_cell(_format_resource_allocations(item.resource_allocations, empty="—")),
                        str(item.ready_at),
                        str(item.start),
                        str(item.finish),
                        str(item.queue_delay),
                        "yes" if item.critical else "no",
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Task timing table",
            "",
            "| Task | Layer | Depends on | Duration | Resources | ES | EF | LS | LF | Slack | Critical | Command |",
            "| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for name in plan.order:
        task = tasks[name]
        timing = timings_by_name[name]
        deps = ", ".join(task.deps) if task.deps else "—"
        command = task.command or "—"
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_markdown_table_cell(name),
                    str(layer_by_name[name]),
                    _escape_markdown_table_cell(deps),
                    str(task.duration),
                    _escape_markdown_table_cell(_format_resource_demands(task.resource_demands, empty="—")),
                    str(timing.earliest_start),
                    str(timing.earliest_finish),
                    str(timing.latest_start),
                    str(timing.latest_finish),
                    str(timing.slack),
                    "yes" if timing.critical else "no",
                    _escape_markdown_table_cell(command),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Deterministic execution order", ""])
    for index, name in enumerate(plan.order, start=1):
        task = tasks[name]
        timing = timings_by_name[name]
        deps = ", ".join(_markdown_code(dep) for dep in task.deps) if task.deps else _markdown_code("ready at start")
        command = _markdown_code(task.command) if task.command else _markdown_code("documentation only")
        lines.extend(
            [
                f"{index}. {_markdown_code(name)}",
                f"   - Dependencies: {deps}",
                f"   - Window: {_markdown_code(f'{timing.earliest_start} → {timing.earliest_finish}')}",
                f"   - Slack: {_markdown_code(timing.slack)}",
                f"   - Resources: {_markdown_code(_format_resource_demands(task.resource_demands, empty='generic worker'))}",
                f"   - Command: {command}",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def render_report_dashboard_html(
    tasks: dict[str, Task],
    plan: PlanResult,
    *,
    source_label: str,
    html_output_path: str,
    title: str | None = None,
    manifest_title: str | None = None,
    manifest_description: str | None = None,
    report_markdown_out: str | None = None,
    artifacts: dict[str, Any] | None = None,
    worker_limited_schedule: WorkerLimitedSchedule | None = None,
    comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
    strategy_comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
) -> str:
    resolved_title = build_report_title(
        source_label=source_label,
        explicit_title=title,
        manifest_title=manifest_title,
    )
    resolved_description = build_report_description(
        source_label=source_label,
        manifest_description=manifest_description,
    )
    artifacts = artifacts or {}
    critical_path_text = " → ".join(plan.critical_path) if plan.critical_path else "(none)"
    ordered_comparison_schedules = _ordered_report_comparison_schedules(
        worker_limited_schedule=worker_limited_schedule,
        comparison_schedules=comparison_schedules,
    )
    ordered_strategy_schedules = _ordered_report_strategy_schedules(
        worker_limited_schedule=worker_limited_schedule,
        strategy_comparison_schedules=strategy_comparison_schedules,
    )

    summary_cards = [
        ("Tasks", str(len(tasks))),
        ("Parallel layers", str(len(plan.layers))),
        ("Unlimited makespan", str(plan.total_duration)),
        ("Critical path", critical_path_text),
    ]
    if worker_limited_schedule is not None:
        summary_cards.extend(
            [
                ("Worker cap", _format_worker_limit_label(worker_limited_schedule.worker_limit)),
                ("Constrained makespan", str(worker_limited_schedule.makespan)),
                ("Strategy", _format_schedule_strategy_label(worker_limited_schedule.strategy)),
                ("Utilization", _format_percent(worker_limited_schedule.utilization)),
            ]
        )
    elif ordered_comparison_schedules:
        summary_cards.append(("Compared worker caps", str(len(ordered_comparison_schedules))))

    summary_html = "".join(
        f'<li><strong>{_html_escape(value)}</strong>{_html_escape(label)}</li>' for label, value in summary_cards
    )

    artifact_rows: list[str] = []
    if report_markdown_out:
        href = _relative_markdown_link(report_markdown_out, from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">Markdown walkthrough</a><span class="muted"><code>{_html_escape(Path(report_markdown_out).name)}</code></span></li>'
        )
    if artifacts.get("mermaid_preview"):
        href = _relative_markdown_link(artifacts["mermaid_preview"], from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">GitHub-friendly Mermaid preview</a><span class="muted"><code>{_html_escape(Path(artifacts["mermaid_preview"]).name)}</code></span></li>'
        )
    if artifacts.get("mermaid_source"):
        href = _relative_markdown_link(artifacts["mermaid_source"], from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">Mermaid source</a><span class="muted"><code>{_html_escape(Path(artifacts["mermaid_source"]).name)}</code></span></li>'
        )
    if artifacts.get("dot_source"):
        href = _relative_markdown_link(artifacts["dot_source"], from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">Graphviz DOT source</a><span class="muted"><code>{_html_escape(Path(artifacts["dot_source"]).name)}</code></span></li>'
        )

    schedule_json_paths = artifacts.get("worker_limited_schedule_jsons") or {}
    schedule_svg_paths = artifacts.get("worker_limited_schedule_svgs") or {}
    include_strategy_in_key = any(":" in key for key in set(schedule_json_paths) | set(schedule_svg_paths))
    schedule_entries: dict[tuple[int, str], WorkerLimitedSchedule] = {}
    for schedule in ordered_comparison_schedules:
        schedule_entries[(schedule.worker_limit, schedule.strategy)] = schedule
    for schedule in ordered_strategy_schedules:
        schedule_entries[(schedule.worker_limit, schedule.strategy)] = schedule

    schedule_rows: list[str] = []
    for _, schedule in sorted(
        schedule_entries.items(),
        key=lambda item: (item[0][0], SCHEDULE_STRATEGIES.index(item[0][1]), item[1].makespan),
    ):
        raw_key = (
            f"{schedule.worker_limit}:{schedule.strategy}"
            if include_strategy_in_key
            else str(schedule.worker_limit)
        )
        delayed_count = sum(1 for item in schedule.assignments if item.queue_delay > 0)
        links: list[str] = []
        if raw_key in schedule_svg_paths:
            href = _relative_markdown_link(schedule_svg_paths[raw_key], from_path=html_output_path)
            links.append(f'<a href="{_html_escape(href)}">SVG timeline</a>')
        if raw_key in schedule_json_paths:
            href = _relative_markdown_link(schedule_json_paths[raw_key], from_path=html_output_path)
            links.append(f'<a href="{_html_escape(href)}">JSON payload</a>')
        link_html = " · ".join(links) if links else '<span class="muted">No exported files</span>'
        schedule_rows.append(
            "<tr>"
            f"<td>{_html_escape(_format_worker_limit_label(schedule.worker_limit))}</td>"
            f"<td><code>{_html_escape(_format_schedule_strategy_label(schedule.strategy))}</code></td>"
            f"<td>{schedule.makespan}</td>"
            f"<td>{schedule.makespan - schedule.unlimited_makespan}</td>"
            f"<td>{_html_escape(_format_percent(schedule.utilization))}</td>"
            f"<td>{delayed_count}</td>"
            f"<td>{link_html}</td>"
            "</tr>"
        )
        if raw_key in schedule_svg_paths:
            href = _relative_markdown_link(schedule_svg_paths[raw_key], from_path=html_output_path)
            artifact_rows.append(
                f'<li><a href="{_html_escape(href)}">Schedule SVG — {_html_escape(_format_worker_limit_label(schedule.worker_limit))} / {_html_escape(_format_schedule_strategy_label(schedule.strategy))}</a><span class="muted"><code>{_html_escape(Path(schedule_svg_paths[raw_key]).name)}</code></span></li>'
            )
        if raw_key in schedule_json_paths:
            href = _relative_markdown_link(schedule_json_paths[raw_key], from_path=html_output_path)
            artifact_rows.append(
                f'<li><a href="{_html_escape(href)}">Schedule JSON — {_html_escape(_format_worker_limit_label(schedule.worker_limit))} / {_html_escape(_format_schedule_strategy_label(schedule.strategy))}</a><span class="muted"><code>{_html_escape(Path(schedule_json_paths[raw_key]).name)}</code></span></li>'
            )

    primary_schedule_svg = artifacts.get("worker_limited_schedule_svg")
    primary_schedule_img = ""
    if primary_schedule_svg:
        href = _relative_markdown_link(primary_schedule_svg, from_path=html_output_path)
        primary_schedule_img = f'''
      <section class="panel chart">
        <h2>Primary schedule preview</h2>
        <p class="muted">GitHub-friendly SVG timeline for the primary constrained schedule.</p>
        <a href="{_html_escape(href)}"><img src="{_html_escape(href)}" alt="Primary schedule SVG timeline" /></a>
      </section>'''

    worker_comparison_section = ""
    if schedule_rows:
        worker_comparison_section = f'''
      <section class="panel">
        <h2>Schedule comparison snapshot</h2>
        <table>
          <thead>
            <tr>
              <th>Worker limit</th>
              <th>Strategy</th>
              <th>Makespan</th>
              <th>Δ vs unlimited</th>
              <th>Utilization</th>
              <th>Delayed tasks</th>
              <th>Artifacts</th>
            </tr>
          </thead>
          <tbody>
            {"".join(schedule_rows)}
          </tbody>
        </table>
      </section>'''

    strategy_note = ""
    if len(ordered_strategy_schedules) > 1:
        strategy_note = (
            '<p class="muted">This report also includes a fixed-worker strategy comparison so reviewers can see '
            'how queue policy changes the same DAG under identical constraints.</p>'
        )

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_html_escape(resolved_title)} — dashboard</title>
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
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1440px; margin: 0 auto; padding: 32px 20px 64px; }}
      h1, h2, h3, p {{ margin-top: 0; }}
      a {{ color: var(--accent); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; word-break: break-word; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p {{ color: var(--muted); max-width: 980px; }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0; padding: 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; }}
      .summary-grid strong {{ display: block; font-size: 1.25rem; margin-bottom: 6px; }}
      .panel {{ padding: 20px; margin-bottom: 24px; overflow: auto; }}
      .artifact-list {{ margin: 0; padding-left: 1.1rem; }}
      .artifact-list li {{ margin: 0.6rem 0; }}
      .muted {{ color: var(--muted); display: block; margin-top: 4px; font-size: 0.92rem; }}
      .chart img {{ width: 100%; height: auto; min-width: 880px; display: block; border-radius: 18px; border: 1px solid var(--border); background: #fff; }}
      table {{ width: 100%; border-collapse: collapse; min-width: 760px; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.92rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
      .chips {{ display: flex; flex-wrap: wrap; gap: 0.65rem; margin-top: 1rem; }}
      .chip {{ display: inline-flex; align-items: center; padding: 0.45rem 0.75rem; border-radius: 999px; background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="chip">Dependency graph planner</p>
        <h1>{_html_escape(resolved_title)} — dashboard</h1>
        <p>{_html_escape(resolved_description)}</p>
        <p>Browser-friendly landing page for the committed walkthrough artifacts. Start here when you want the dependency graph story, the constrained schedule evidence, and the export bundle links without opening raw JSON first.</p>
        <div class="chips">
          <span class="chip">Source <code>{_html_escape(source_label)}</code></span>
          <span class="chip">Critical path <code>{_html_escape(critical_path_text)}</code></span>
        </div>
        <ul class="summary-grid">
          {summary_html}
        </ul>
      </section>
      <section class="panel">
        <h2>Artifact bundle</h2>
        <p class="muted">Stable, relative links make this dashboard safe to commit alongside the Markdown walkthrough and schedule exports.</p>
        <ul class="artifact-list">
          {"".join(artifact_rows) if artifact_rows else '<li>No companion artifacts were exported for this view yet.</li>'}
        </ul>
      </section>
      {primary_schedule_img}
      {worker_comparison_section}
      <section class="panel">
        <h2>Portfolio talking points</h2>
        <p>This project demonstrates deterministic DAG planning, critical-path timing, and realistic worker/resource bottlenecks in one small Python program. The linked Markdown walkthrough explains the reasoning, while the SVG timeline helps reviewers see the constrained schedule at a glance.</p>
        {strategy_note}
      </section>
    </main>
  </body>
</html>
'''


def _build_report_artifact_links(
    artifacts: dict[str, Any],
    *,
    report_markdown_out: str | None,
    report_html_out: str | None = None,
) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    if artifacts.get("mermaid_preview"):
        ordered.append(("GitHub-friendly Mermaid preview", artifacts["mermaid_preview"]))
    if artifacts.get("mermaid_source"):
        ordered.append(("Mermaid source", artifacts["mermaid_source"]))
    if artifacts.get("dot_source"):
        ordered.append(("Graphviz DOT source", artifacts["dot_source"]))
    if report_html_out:
        ordered.append(("Report dashboard HTML", report_html_out))

    schedule_json_paths = artifacts.get("worker_limited_schedule_jsons") or {}
    schedule_svg_paths = artifacts.get("worker_limited_schedule_svgs") or {}
    parsed_schedule_entries = _parse_schedule_artifact_entries(
        {
            key: schedule_json_paths.get(key) or schedule_svg_paths.get(key) or ""
            for key in set(schedule_json_paths) | set(schedule_svg_paths)
        }
    )
    if parsed_schedule_entries:
        if len(parsed_schedule_entries) == 1 and parsed_schedule_entries[0][2] is None:
            raw_key = parsed_schedule_entries[0][0]
            if raw_key in schedule_svg_paths:
                ordered.append(("Worker-limited schedule SVG", schedule_svg_paths[raw_key]))
            if raw_key in schedule_json_paths:
                ordered.append(("Worker-limited schedule JSON", schedule_json_paths[raw_key]))
        else:
            for raw_key, worker_limit, strategy, _ in parsed_schedule_entries:
                suffix = f" ({_format_worker_limit_label(worker_limit)}"
                if strategy is not None:
                    suffix += f", {_format_schedule_strategy_label(strategy)}"
                suffix += ")"
                if raw_key in schedule_svg_paths:
                    ordered.append((f"Worker-limited schedule SVG{suffix}", schedule_svg_paths[raw_key]))
                if raw_key in schedule_json_paths:
                    ordered.append((f"Worker-limited schedule JSON{suffix}", schedule_json_paths[raw_key]))
    if report_markdown_out:
        return [
            (label, _relative_markdown_link(target, from_path=report_markdown_out))
            for label, target in ordered
        ]
    return ordered


def benchmark_suite_to_dict(result: BenchmarkSuiteResult) -> dict[str, Any]:
    return {
        "title": result.title,
        "source_label": result.source_label,
        "scenario_count": len(result.scenarios),
        "scenarios": [
            {
                "label": scenario.label,
                "graph_label": scenario.graph_label,
                "graph_path": _display_path_label(scenario.graph_path),
                "worker_limit": scenario.worker_limit,
                "task_count": scenario.task_count,
                "unlimited_makespan": scenario.unlimited_makespan,
                "critical_path_lower_bound": scenario.critical_path_lower_bound,
                "resource_capacities": scenario.resource_capacities,
                "best_makespan": scenario.best_makespan,
                "best_makespan_strategies": scenario.best_makespan_strategies,
                "rank_1_strategies": scenario.rank_1_strategies,
                "strategy_results": [
                    {
                        "strategy": item.strategy,
                        "rank": item.rank,
                        "makespan": item.makespan,
                        "delta_vs_unlimited": item.delta_vs_unlimited,
                        "delta_vs_critical_path_lower_bound": item.delta_vs_critical_path_lower_bound,
                        "ratio_vs_critical_path_lower_bound": round(item.ratio_vs_critical_path_lower_bound, 6),
                        "delta_vs_best": item.delta_vs_best,
                        "total_queue_delay": item.total_queue_delay,
                        "max_queue_delay": item.max_queue_delay,
                        "utilization": round(item.utilization, 6),
                        "idle_capacity": item.idle_capacity,
                        "dispatch_order": item.dispatch_order,
                        "tied_best_makespan": item.tied_best_makespan,
                    }
                    for item in scenario.strategy_results
                ],
            }
            for scenario in result.scenarios
        ],
        "aggregates": [
            {
                "strategy": item.strategy,
                "scenario_count": item.scenario_count,
                "rank_1_finishes": item.rank_1_finishes,
                "best_makespan_finishes": item.best_makespan_finishes,
                "average_makespan": round(item.average_makespan, 6),
                "average_delta_vs_critical_path_lower_bound": round(item.average_delta_vs_critical_path_lower_bound, 6),
                "average_ratio_vs_critical_path_lower_bound": round(item.average_ratio_vs_critical_path_lower_bound, 6),
                "average_delta_vs_best": round(item.average_delta_vs_best, 6),
                "average_total_queue_delay": round(item.average_total_queue_delay, 6),
                "average_max_queue_delay": round(item.average_max_queue_delay, 6),
                "average_utilization": round(item.average_utilization, 6),
            }
            for item in result.aggregates
        ],
    }


def _render_csv_rows(rows: Sequence[dict[str, Any]], *, fieldnames: Sequence[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(fieldnames), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row.get(name, "") for name in fieldnames})
    return buffer.getvalue()


def benchmark_aggregate_rows(result: BenchmarkSuiteResult) -> list[dict[str, Any]]:
    return [
        {
            "strategy": item.strategy,
            "scenario_count": item.scenario_count,
            "rank_1_finishes": item.rank_1_finishes,
            "best_makespan_finishes": item.best_makespan_finishes,
            "average_makespan": round(item.average_makespan, 6),
            "average_delta_vs_critical_path_lower_bound": round(item.average_delta_vs_critical_path_lower_bound, 6),
            "average_ratio_vs_critical_path_lower_bound": round(item.average_ratio_vs_critical_path_lower_bound, 6),
            "average_delta_vs_best": round(item.average_delta_vs_best, 6),
            "average_total_queue_delay": round(item.average_total_queue_delay, 6),
            "average_max_queue_delay": round(item.average_max_queue_delay, 6),
            "average_utilization": round(item.average_utilization, 6),
        }
        for item in result.aggregates
    ]


def benchmark_strategy_rows(result: BenchmarkSuiteResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in result.scenarios:
        for item in scenario.strategy_results:
            rows.append(
                {
                    "suite_title": result.title,
                    "suite_source": result.source_label,
                    "scenario_label": scenario.label,
                    "graph_label": scenario.graph_label,
                    "graph_path": _display_path_label(scenario.graph_path),
                    "worker_limit": scenario.worker_limit,
                    "task_count": scenario.task_count,
                    "unlimited_makespan": scenario.unlimited_makespan,
                    "critical_path_lower_bound": scenario.critical_path_lower_bound,
                    "best_makespan": scenario.best_makespan,
                    "rank_1_strategies": ",".join(scenario.rank_1_strategies),
                    "best_makespan_strategies": ",".join(scenario.best_makespan_strategies),
                    "resource_capacities": json.dumps(scenario.resource_capacities, sort_keys=True),
                    "strategy": item.strategy,
                    "rank": item.rank,
                    "makespan": item.makespan,
                    "delta_vs_unlimited": item.delta_vs_unlimited,
                    "delta_vs_critical_path_lower_bound": item.delta_vs_critical_path_lower_bound,
                    "ratio_vs_critical_path_lower_bound": round(item.ratio_vs_critical_path_lower_bound, 6),
                    "delta_vs_best": item.delta_vs_best,
                    "total_queue_delay": item.total_queue_delay,
                    "max_queue_delay": item.max_queue_delay,
                    "idle_capacity": item.idle_capacity,
                    "utilization": round(item.utilization, 6),
                    "tied_best_makespan": item.tied_best_makespan,
                    "dispatch_order": ",".join(item.dispatch_order),
                }
            )
    return rows


def render_benchmark_aggregate_csv(result: BenchmarkSuiteResult) -> str:
    return _render_csv_rows(
        benchmark_aggregate_rows(result),
        fieldnames=(
            "strategy",
            "scenario_count",
            "rank_1_finishes",
            "best_makespan_finishes",
            "average_makespan",
            "average_delta_vs_critical_path_lower_bound",
            "average_ratio_vs_critical_path_lower_bound",
            "average_delta_vs_best",
            "average_total_queue_delay",
            "average_max_queue_delay",
            "average_utilization",
        ),
    )


def render_benchmark_strategy_csv(result: BenchmarkSuiteResult) -> str:
    return _render_csv_rows(
        benchmark_strategy_rows(result),
        fieldnames=(
            "suite_title",
            "suite_source",
            "scenario_label",
            "graph_label",
            "graph_path",
            "worker_limit",
            "task_count",
            "unlimited_makespan",
            "critical_path_lower_bound",
            "best_makespan",
            "rank_1_strategies",
            "best_makespan_strategies",
            "resource_capacities",
            "strategy",
            "rank",
            "makespan",
            "delta_vs_unlimited",
            "delta_vs_critical_path_lower_bound",
            "ratio_vs_critical_path_lower_bound",
            "delta_vs_best",
            "total_queue_delay",
            "max_queue_delay",
            "idle_capacity",
            "utilization",
            "tied_best_makespan",
            "dispatch_order",
        ),
    )


def _build_benchmark_artifact_links(
    artifacts: dict[str, str],
    *,
    benchmark_markdown_out: str | None,
) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    if artifacts.get("benchmark_html"):
        ordered.append(("Benchmark dashboard HTML", artifacts["benchmark_html"]))
    if artifacts.get("benchmark_json"):
        ordered.append(("Benchmark JSON snapshot", artifacts["benchmark_json"]))
    if artifacts.get("benchmark_aggregate_csv"):
        ordered.append(("Aggregate strategy CSV", artifacts["benchmark_aggregate_csv"]))
    if artifacts.get("benchmark_strategy_csv"):
        ordered.append(("Per-scenario strategy CSV", artifacts["benchmark_strategy_csv"]))
    if benchmark_markdown_out:
        return [
            (label, _relative_markdown_link(target, from_path=benchmark_markdown_out))
            for label, target in ordered
        ]
    return ordered



def render_benchmark_suite_markdown(
    result: BenchmarkSuiteResult,
    *,
    artifact_links: Sequence[tuple[str, str]] | None = None,
) -> str:
    strategies = [item.strategy for item in result.aggregates]
    top_strategy = result.aggregates[0].strategy if result.aggregates else "(none)"
    lines = [f"# {result.title}", ""]
    lines.extend(
        [
            f"- Suite source: {_markdown_code(result.source_label)}",
            f"- Scenario count: {_markdown_code(len(result.scenarios))}",
            f"- Strategies covered: {_markdown_code(', '.join(strategies))}",
            f"- Aggregate leader: {_markdown_code(top_strategy)}",
        ]
    )

    if artifact_links:
        lines.extend(["", "## Linked artifacts", ""])
        for label, target in artifact_links:
            lines.append(f"- [{label}]({target})")

    lines.extend(
        [
            "",
            "## Aggregate strategy scoreboard",
            "",
            "| Strategy | Scenarios | Rank-1 finishes | Best-makespan finishes | Avg makespan | Avg Δ vs critical path | Avg ratio vs critical path | Avg Δ vs best | Avg total queue delay | Avg max queue delay | Avg utilization |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in result.aggregates:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_markdown_table_cell(item.strategy),
                    str(item.scenario_count),
                    str(item.rank_1_finishes),
                    str(item.best_makespan_finishes),
                    f"{item.average_makespan:.2f}",
                    f"{item.average_delta_vs_critical_path_lower_bound:.2f}",
                    f"{item.average_ratio_vs_critical_path_lower_bound:.2f}×",
                    f"{item.average_delta_vs_best:.2f}",
                    f"{item.average_total_queue_delay:.2f}",
                    f"{item.average_max_queue_delay:.2f}",
                    f"{item.average_utilization * 100:.1f}%",
                ]
            )
            + " |"
        )

    for scenario in result.scenarios:
        lines.extend(
            [
                "",
                f"## Scenario — {scenario.label}",
                "",
                f"- Manifest: {_markdown_code(scenario.graph_label)}",
                f"- Worker limit: {_markdown_code(_format_worker_limit_label(scenario.worker_limit))}",
                f"- Task count: {_markdown_code(scenario.task_count)}",
                f"- Unlimited makespan: {_markdown_code(scenario.unlimited_makespan)}",
                f"- Critical-path lower bound: {_markdown_code(scenario.critical_path_lower_bound)}",
                f"- Best scenario makespan: {_markdown_code(scenario.best_makespan)} via {_markdown_code(', '.join(scenario.best_makespan_strategies))}",
                f"- Rank-1 strategies after queue-delay tie-breaks: {_markdown_code(', '.join(scenario.rank_1_strategies))}",
            ]
        )
        if scenario.resource_capacities:
            rendered_caps = ", ".join(
                f"{resource_class}={capacity}"
                for resource_class, capacity in scenario.resource_capacities.items()
            )
            lines.append(f"- Resource capacities: {_markdown_code(rendered_caps)}")

        lines.extend(
            [
                "",
                "| Rank | Strategy | Makespan | Δ vs unlimited | Δ vs critical path | Ratio vs critical path | Δ vs best | Total queue delay | Max queue delay | Idle capacity | Utilization | Dispatch order |",
                "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for item in scenario.strategy_results:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(item.rank),
                        _escape_markdown_table_cell(item.strategy),
                        str(item.makespan),
                        str(item.delta_vs_unlimited),
                        str(item.delta_vs_critical_path_lower_bound),
                        f"{item.ratio_vs_critical_path_lower_bound:.2f}×",
                        str(item.delta_vs_best),
                        str(item.total_queue_delay),
                        str(item.max_queue_delay),
                        str(item.idle_capacity),
                        f"{item.utilization * 100:.1f}%",
                        _escape_markdown_table_cell(", ".join(item.dispatch_order)),
                    ]
                )
                + " |"
            )

    return "\n".join(lines).rstrip() + "\n"



def render_benchmark_dashboard_html(
    result: BenchmarkSuiteResult,
    *,
    html_output_path: str,
    artifacts: dict[str, str] | None = None,
) -> str:
    artifacts = artifacts or {}
    strategy_count = len(result.aggregates)
    top_strategy = result.aggregates[0] if result.aggregates else None
    lowest_gap_strategy = (
        min(
            result.aggregates,
            key=lambda item: (
                item.average_delta_vs_critical_path_lower_bound,
                item.average_ratio_vs_critical_path_lower_bound,
                SCHEDULE_STRATEGIES.index(item.strategy),
            ),
        )
        if result.aggregates
        else None
    )
    summary_cards = [
        ("Scenarios", str(len(result.scenarios))),
        ("Strategies", str(strategy_count)),
        ("Top aggregate leader", top_strategy.strategy if top_strategy else "(none)"),
        (
            "Best average makespan",
            f"{top_strategy.average_makespan:.2f}" if top_strategy else "(n/a)",
        ),
        (
            "Lowest avg gap vs critical path",
            (
                f"{lowest_gap_strategy.average_delta_vs_critical_path_lower_bound:.2f}"
                f" ({lowest_gap_strategy.strategy})"
            )
            if lowest_gap_strategy
            else "(n/a)",
        ),
    ]
    summary_html = "".join(
        f'<li><strong>{_html_escape(value)}</strong>{_html_escape(label)}</li>' for label, value in summary_cards
    )

    artifact_rows: list[str] = []
    if artifacts.get("benchmark_markdown"):
        href = _relative_markdown_link(artifacts["benchmark_markdown"], from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">Markdown scoreboard</a><span class="muted"><code>{_html_escape(Path(artifacts["benchmark_markdown"]).name)}</code></span></li>'
        )
    if artifacts.get("benchmark_json"):
        href = _relative_markdown_link(artifacts["benchmark_json"], from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">Benchmark JSON snapshot</a><span class="muted"><code>{_html_escape(Path(artifacts["benchmark_json"]).name)}</code></span></li>'
        )
    if artifacts.get("benchmark_aggregate_csv"):
        href = _relative_markdown_link(artifacts["benchmark_aggregate_csv"], from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">Aggregate strategy CSV</a><span class="muted"><code>{_html_escape(Path(artifacts["benchmark_aggregate_csv"]).name)}</code></span></li>'
        )
    if artifacts.get("benchmark_strategy_csv"):
        href = _relative_markdown_link(artifacts["benchmark_strategy_csv"], from_path=html_output_path)
        artifact_rows.append(
            f'<li><a href="{_html_escape(href)}">Per-scenario strategy CSV</a><span class="muted"><code>{_html_escape(Path(artifacts["benchmark_strategy_csv"]).name)}</code></span></li>'
        )

    aggregate_rows = "".join(
        "<tr>"
        f"<td><code>{_html_escape(item.strategy)}</code></td>"
        f"<td>{item.scenario_count}</td>"
        f"<td>{item.rank_1_finishes}</td>"
        f"<td>{item.best_makespan_finishes}</td>"
        f"<td>{item.average_makespan:.2f}</td>"
        f"<td>{item.average_delta_vs_critical_path_lower_bound:.2f}</td>"
        f"<td>{item.average_ratio_vs_critical_path_lower_bound:.2f}×</td>"
        f"<td>{item.average_delta_vs_best:.2f}</td>"
        f"<td>{item.average_total_queue_delay:.2f}</td>"
        f"<td>{item.average_max_queue_delay:.2f}</td>"
        f"<td>{_html_escape(_format_percent(item.average_utilization))}</td>"
        "</tr>"
        for item in result.aggregates
    )

    scenario_rows = "".join(
        "<tr>"
        f"<td><strong>{_html_escape(scenario.label)}</strong><span class=\"muted\"><code>{_html_escape(scenario.graph_label)}</code></span></td>"
        f"<td>{_html_escape(_format_worker_limit_label(scenario.worker_limit))}</td>"
        f"<td>{scenario.task_count}</td>"
        f"<td>{scenario.unlimited_makespan}</td>"
        f"<td>{scenario.critical_path_lower_bound}</td>"
        f"<td>{scenario.best_makespan}</td>"
        f"<td>{_html_escape(', '.join(scenario.rank_1_strategies))}</td>"
        f"<td>{_html_escape(', '.join(f'{name}={capacity}' for name, capacity in scenario.resource_capacities.items()) if scenario.resource_capacities else '—')}</td>"
        "</tr>"
        for scenario in result.scenarios
    )

    scenario_sections: list[str] = []
    for scenario in result.scenarios:
        strategy_rows = "".join(
            "<tr>"
            f"<td>{item.rank}</td>"
            f"<td><code>{_html_escape(item.strategy)}</code></td>"
            f"<td>{item.makespan}</td>"
            f"<td>{item.delta_vs_unlimited}</td>"
            f"<td>{item.delta_vs_critical_path_lower_bound}</td>"
            f"<td>{item.ratio_vs_critical_path_lower_bound:.2f}×</td>"
            f"<td>{item.delta_vs_best}</td>"
            f"<td>{item.total_queue_delay}</td>"
            f"<td>{item.max_queue_delay}</td>"
            f"<td>{item.idle_capacity}</td>"
            f"<td>{_html_escape(_format_percent(item.utilization))}</td>"
            f"<td>{_html_escape(', '.join(item.dispatch_order))}</td>"
            "</tr>"
            for item in scenario.strategy_results
        )
        scenario_sections.append(
            f'''
      <section class="panel">
        <h2>Scenario — {_html_escape(scenario.label)}</h2>
        <p class="muted">Manifest <code>{_html_escape(scenario.graph_label)}</code> · {_html_escape(_format_worker_limit_label(scenario.worker_limit))} · critical-path lower bound {scenario.critical_path_lower_bound} · best makespan {scenario.best_makespan} via {_html_escape(', '.join(scenario.best_makespan_strategies))}</p>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Strategy</th>
              <th>Makespan</th>
              <th>Δ vs unlimited</th>
              <th>Δ vs critical path</th>
              <th>Ratio vs critical path</th>
              <th>Δ vs best</th>
              <th>Total queue delay</th>
              <th>Max queue delay</th>
              <th>Idle capacity</th>
              <th>Utilization</th>
              <th>Dispatch order</th>
            </tr>
          </thead>
          <tbody>
            {strategy_rows}
          </tbody>
        </table>
      </section>'''
        )

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_html_escape(result.title)} — benchmark dashboard</title>
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
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1500px; margin: 0 auto; padding: 32px 20px 64px; }}
      h1, h2, h3, p {{ margin-top: 0; }}
      a {{ color: var(--accent); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; word-break: break-word; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p {{ color: var(--muted); max-width: 1020px; }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0; padding: 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #bfdbfe; }}
      .summary-grid strong {{ display: block; font-size: 1.25rem; margin-bottom: 6px; }}
      .panel {{ padding: 20px; margin-bottom: 24px; overflow: auto; }}
      .artifact-list {{ margin: 0; padding-left: 1.1rem; }}
      .artifact-list li {{ margin: 0.6rem 0; }}
      .muted {{ color: var(--muted); display: block; margin-top: 4px; font-size: 0.92rem; }}
      table {{ width: 100%; border-collapse: collapse; min-width: 900px; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.92rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
      .chips {{ display: flex; flex-wrap: wrap; gap: 0.65rem; margin-top: 1rem; }}
      .chip {{ display: inline-flex; align-items: center; padding: 0.45rem 0.75rem; border-radius: 999px; background: #eff6ff; border: 1px solid #bfdbfe; color: #1d4ed8; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="chip">Dependency graph benchmark suite</p>
        <h1>{_html_escape(result.title)} — dashboard</h1>
        <p>Static landing page for the planner's benchmark suite exports. Use it to browse aggregate winners, per-scenario tradeoffs, and the committed JSON/CSV snapshots without starting from raw files.</p>
        <div class="chips">
          <span class="chip">Suite <code>{_html_escape(result.source_label)}</code></span>
          <span class="chip">Scenarios {len(result.scenarios)}</span>
          <span class="chip">Strategies {strategy_count}</span>
        </div>
        <ul class="summary-grid">
          {summary_html}
        </ul>
      </section>
      <section class="panel">
        <h2>Artifact bundle</h2>
        <p class="muted">Relative links keep the committed dashboard portable when it ships beside the Markdown, JSON, and CSV exports.</p>
        <ul class="artifact-list">
          {''.join(artifact_rows) if artifact_rows else '<li>No companion benchmark artifacts were exported for this view yet.</li>'}
        </ul>
      </section>
      <section class="panel">
        <h2>Aggregate strategy scoreboard</h2>
        <table>
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Scenarios</th>
              <th>Rank-1 finishes</th>
              <th>Best-makespan finishes</th>
              <th>Avg makespan</th>
              <th>Avg Δ vs critical path</th>
              <th>Avg ratio vs critical path</th>
              <th>Avg Δ vs best</th>
              <th>Avg total queue delay</th>
              <th>Avg max queue delay</th>
              <th>Avg utilization</th>
            </tr>
          </thead>
          <tbody>
            {aggregate_rows}
          </tbody>
        </table>
      </section>
      <section class="panel">
        <h2>Scenario summary</h2>
        <table>
          <thead>
            <tr>
              <th>Scenario</th>
              <th>Worker limit</th>
              <th>Tasks</th>
              <th>Unlimited makespan</th>
              <th>Critical-path lower bound</th>
              <th>Best makespan</th>
              <th>Rank-1 strategies</th>
              <th>Resource caps</th>
            </tr>
          </thead>
          <tbody>
            {scenario_rows}
          </tbody>
        </table>
      </section>
      {''.join(scenario_sections)}
    </main>
  </body>
</html>
'''



def _resolve_synthetic_generator_name(name: str) -> str:
    normalized = name.strip().lower().replace("_", "-")
    aliases = {
        "ci-pipeline": "ci",
        "pipeline-ci": "ci",
        "release-pipeline": "release",
        "data": "data-pipeline",
        "data-pipeline-bottleneck": "data-pipeline",
        "data-pipeline-bottlenecks": "data-pipeline",
        "data-pipeline-bottleneck-lab": "data-pipeline",
        "random": "stress",
        "randomized": "stress",
        "randomized-stress": "stress",
        "stress-test": "stress",
        "stress-suite": "stress",
    }
    resolved = aliases.get(normalized, normalized)
    if resolved not in SYNTHETIC_GENERATORS:
        raise ValueError(
            f"unknown generator {name!r}; expected one of: {', '.join(SYNTHETIC_GENERATORS)}"
        )
    return resolved



def _build_synthetic_task(
    name: str,
    *,
    deps: Sequence[str] | None = None,
    duration: int = 1,
    command: str | None = None,
    resource_class: str | None = None,
    resources: dict[str, int] | None = None,
) -> dict[str, Any]:
    task: dict[str, Any] = {"name": name, "duration": duration}
    if deps:
        task["deps"] = list(deps)
    if command:
        task["command"] = command
    if resources:
        task["resources"] = dict(sorted(resources.items()))
    elif resource_class:
        task["resource_class"] = resource_class
    return task



def _build_progressive_canary_percentages(width: int) -> list[int]:
    if width <= 0:
        raise ValueError("--generator-width must be a positive integer")
    if width == 1:
        return [25]
    if width == 2:
        return [10, 50]
    return [10 + round(index * 80 / (width - 1)) for index in range(width)]



def _synthetic_sequence_name(prefix: str, index: int, width: int) -> str:
    digits = max(2, len(str(width)))
    return f"{prefix}-{index:0{digits}d}"



def build_synthetic_manifest(
    generator_name: str,
    *,
    width: int = DEFAULT_GENERATOR_WIDTH,
    seed: int | None = None,
) -> dict[str, Any]:
    resolved_name = _resolve_synthetic_generator_name(generator_name)
    if width <= 0:
        raise ValueError("--generator-width must be a positive integer")
    if resolved_name == "ci":
        return _build_ci_pipeline_manifest(width)
    if resolved_name == "release":
        return _build_release_pipeline_manifest(width)
    if resolved_name == "stress":
        return _build_stress_pipeline_manifest(width, seed=seed)
    return _build_data_pipeline_manifest(width)


def _default_generator_seed(width: int, *, offset: int = 0) -> int:
    return DEFAULT_GENERATOR_SEED + offset + (width * 97)


def _random_duration(rng: random.Random, *, low: int = 1, high: int = 5) -> int:
    return rng.randint(low, high)


def _build_stress_pipeline_manifest(width: int, *, seed: int | None = None) -> dict[str, Any]:
    resolved_seed = _default_generator_seed(width) if seed is None else seed
    rng = random.Random(resolved_seed)
    distractor_count = width + 2
    chain_length = width + 3
    follow_up_count = max(2, width)

    tasks: list[dict[str, Any]] = [
        _build_synthetic_task("seed", duration=1, command="python -m planner.seed_critical_path"),
    ]

    distractor_names = [_synthetic_sequence_name("bulk", index, distractor_count) for index in range(1, distractor_count + 1)]
    for index, name in enumerate(distractor_names, start=1):
        duration = _random_duration(rng, low=3, high=6)
        tasks.append(
            _build_synthetic_task(
                name,
                duration=duration,
                command=f"python -m planner.run_bulk_job --batch={index}",
            )
        )

    previous = "seed"
    chain_names: list[str] = []
    for index in range(1, chain_length + 1):
        name = _synthetic_sequence_name("critical-chain", index, chain_length)
        chain_names.append(name)
        deps = [previous]
        if index > 1 and rng.random() < 0.45:
            deps.append(rng.choice(distractor_names[: min(index, len(distractor_names))]))
        tasks.append(
            _build_synthetic_task(
                name,
                deps=deps,
                duration=_random_duration(rng, low=2, high=4),
                command=f"python -m planner.advance_chain --step={index}",
            )
        )
        previous = name

    follow_up_names: list[str] = []
    for index in range(1, follow_up_count + 1):
        name = _synthetic_sequence_name("follow-up", index, follow_up_count)
        follow_up_names.append(name)
        deps = [rng.choice(distractor_names)]
        if rng.random() < 0.7:
            deps.append(rng.choice(chain_names[: max(1, min(len(chain_names), index + 1))]))
        tasks.append(
            _build_synthetic_task(
                name,
                deps=sorted(set(deps)),
                duration=_random_duration(rng, low=1, high=3),
                command=f"python -m planner.verify_batch --job={index}",
            )
        )

    final_deps = [chain_names[-1], *follow_up_names]
    final_deps.extend(rng.sample(distractor_names, k=min(len(distractor_names), max(2, width))))
    tasks.append(
        _build_synthetic_task(
            "ship",
            deps=sorted(set(final_deps)),
            duration=1,
            command="python -m planner.publish_schedule_story",
        )
    )

    return {
        "metadata": {
            "generator": "stress",
            "generator_width": width,
            "generator_seed": resolved_seed,
            "title": f"Synthetic stress DAG (seed {resolved_seed}, width {width})",
            "description": "Randomized-but-deterministic scheduling stress workload with a fragile critical chain, competing bulk work, and follow-up fan-in checks.",
        },
        "tasks": tasks,
    }


def _build_ci_pipeline_manifest(width: int) -> dict[str, Any]:
    shard_names = [_synthetic_sequence_name("unit-shard", index, width) for index in range(1, width + 1)]
    tasks = [
        _build_synthetic_task("checkout", duration=1, command="git checkout <git-sha>"),
        _build_synthetic_task("install-deps", deps=["checkout"], duration=2, command="pnpm install --frozen-lockfile"),
        _build_synthetic_task("lint", deps=["install-deps"], duration=1, command="pnpm lint"),
        _build_synthetic_task("typecheck", deps=["install-deps"], duration=1, command="pnpm typecheck"),
        _build_synthetic_task("build-app", deps=["install-deps"], duration=2, command="pnpm build"),
    ]
    for index, shard_name in enumerate(shard_names, start=1):
        tasks.append(
            _build_synthetic_task(
                shard_name,
                deps=["build-app"],
                duration=2 + (index % 2),
                command=f"pnpm test:unit -- --shard={index}/{width}",
            )
        )
    tasks.extend(
        [
            _build_synthetic_task(
                "package-artifact",
                deps=["lint", "typecheck", "build-app", *shard_names],
                duration=1,
                command="tar -czf dist/app.tgz dist/",
            ),
            _build_synthetic_task(
                "build-container",
                deps=["package-artifact"],
                duration=2,
                resources={"docker-builder": 1},
                command="docker build -t example/app:<git-sha> .",
            ),
            _build_synthetic_task(
                "publish-preview-image",
                deps=["build-container"],
                duration=1,
                resources={"docker-builder": 1},
                command="docker push registry.example/app:<git-sha>",
            ),
            _build_synthetic_task(
                "security-scan",
                deps=["build-container"],
                duration=2,
                command="trivy image registry.example/app:<git-sha>",
            ),
            _build_synthetic_task(
                "deploy-preview",
                deps=["publish-preview-image"],
                duration=1,
                command="kubectl apply -f deploy/preview.yaml",
            ),
            _build_synthetic_task(
                "smoke-preview",
                deps=["deploy-preview"],
                duration=2,
                resource_class="browser-lab",
                command="pnpm exec playwright test --config preview",
            ),
            _build_synthetic_task(
                "promote-mainline",
                deps=["smoke-preview", "security-scan"],
                duration=1,
                command="gh pr merge --auto --squash",
            ),
        ]
    )
    return {
        "metadata": {
            "generator": "ci",
            "generator_width": width,
            "title": f"Synthetic CI pipeline ({width} unit-test shards)",
            "description": "GitHub Actions style fan-out/fan-in workflow with artifact packaging, image publish, preview deploy, and smoke coverage.",
        },
        "resource_capacities": {"browser-lab": 1, "docker-builder": 1},
        "tasks": tasks,
    }



def _build_release_pipeline_manifest(width: int) -> dict[str, Any]:
    canary_percentages = _build_progressive_canary_percentages(width)
    build_targets = [
        ("linux", "python -m build --wheel"),
        ("macos", "python -m build --wheel --plat-name macosx_14_0_arm64"),
        ("windows", "python -m build --wheel --plat-name win_amd64"),
    ]
    tasks = [
        _build_synthetic_task("freeze-release-branch", duration=1, command="gh release create --draft vNEXT"),
        _build_synthetic_task(
            "assemble-release-notes",
            deps=["freeze-release-branch"],
            duration=1,
            command="gh release view --json body",
        ),
    ]
    sign_tasks: list[str] = []
    for platform_name, command in build_targets:
        build_name = f"build-{platform_name}"
        sign_name = f"sign-{platform_name}"
        sign_tasks.append(sign_name)
        tasks.append(
            _build_synthetic_task(
                build_name,
                deps=["freeze-release-branch"],
                duration=2 if platform_name != "macos" else 3,
                command=command,
            )
        )
        tasks.append(
            _build_synthetic_task(
                sign_name,
                deps=[build_name],
                duration=2,
                resource_class="signing",
                command=f"cosign sign dist/{platform_name}/*",
            )
        )
    tasks.extend(
        [
            _build_synthetic_task(
                "publish-candidates",
                deps=["assemble-release-notes", *sign_tasks],
                duration=1,
                command="gh release upload vNEXT dist/* --clobber",
            ),
            _build_synthetic_task(
                "deploy-staging",
                deps=["publish-candidates"],
                duration=1,
                command="kubectl apply -f deploy/staging.yaml",
            ),
            _build_synthetic_task(
                "verify-staging",
                deps=["deploy-staging"],
                duration=2,
                command="pytest tests/smoke/test_release_candidate.py",
            ),
        ]
    )
    previous = "verify-staging"
    for index, percentage in enumerate(canary_percentages, start=1):
        deploy_name = f"canary-{percentage:02d}pct"
        verify_name = f"verify-canary-{index:02d}"
        tasks.append(
            _build_synthetic_task(
                deploy_name,
                deps=[previous],
                duration=1,
                resource_class="prod-slot",
                command=f"gcloud deploy releases promote --percent={percentage}",
            )
        )
        tasks.append(
            _build_synthetic_task(
                verify_name,
                deps=[deploy_name],
                duration=2,
                command=f"check error budget after {percentage}% traffic",
            )
        )
        previous = verify_name
    tasks.extend(
        [
            _build_synthetic_task(
                "full-rollout",
                deps=[previous],
                duration=1,
                resource_class="prod-slot",
                command="gcloud deploy releases promote --to-target=prod",
            ),
            _build_synthetic_task(
                "announce-release",
                deps=["full-rollout"],
                duration=1,
                command="gh release edit vNEXT --draft=false",
            ),
        ]
    )
    return {
        "metadata": {
            "generator": "release",
            "generator_width": width,
            "title": f"Synthetic release pipeline ({width} canary phases)",
            "description": "Release-engineering workflow with per-platform builds, serialized signing, staging validation, and progressive canary rollout.",
        },
        "resource_capacities": {"prod-slot": 1, "signing": 1},
        "tasks": tasks,
    }



def _build_data_pipeline_manifest(width: int) -> dict[str, Any]:
    partition_names = [_synthetic_sequence_name("transform-partition", index, width) for index in range(1, width + 1)]
    tasks = [
        _build_synthetic_task("ingest-orders", duration=2, command="spark-submit jobs/ingest_orders.py"),
        _build_synthetic_task("ingest-events", duration=2, command="spark-submit jobs/ingest_events.py"),
        _build_synthetic_task("ingest-payments", duration=2, command="spark-submit jobs/ingest_payments.py"),
        _build_synthetic_task(
            "schema-validate",
            deps=["ingest-orders", "ingest-events", "ingest-payments"],
            duration=1,
            command="great_expectations checkpoint run bronze",
        ),
        _build_synthetic_task(
            "quality-profile",
            deps=["ingest-orders", "ingest-events", "ingest-payments"],
            duration=2,
            resource_class="warehouse",
            command="dbt run --select quality_profile",
        ),
    ]
    for index, partition_name in enumerate(partition_names, start=1):
        tasks.append(
            _build_synthetic_task(
                partition_name,
                deps=["schema-validate"],
                duration=2 + (index % 2),
                resource_class="warehouse",
                command=f"dbt run --select fact_orders_partition_{index}",
            )
        )
    tasks.extend(
        [
            _build_synthetic_task(
                "build-features",
                deps=["quality-profile", *partition_names],
                duration=3,
                resources={"warehouse": 2},
                command="dbt run --select feature_store",
            ),
            _build_synthetic_task(
                "train-model",
                deps=["build-features"],
                duration=4,
                resource_class="gpu",
                command="python jobs/train_model.py",
            ),
            _build_synthetic_task(
                "backfill-marts",
                deps=["build-features"],
                duration=3,
                resource_class="warehouse",
                command="dbt run --select marts.fct_revenue",
            ),
            _build_synthetic_task(
                "publish-dashboard",
                deps=["backfill-marts"],
                duration=1,
                command="python jobs/publish_dashboard.py",
            ),
            _build_synthetic_task(
                "publish-model",
                deps=["train-model"],
                duration=1,
                command="python jobs/register_model.py",
            ),
            _build_synthetic_task(
                "notify-ops",
                deps=["publish-dashboard", "publish-model"],
                duration=1,
                command="python jobs/notify_ops.py",
            ),
        ]
    )
    return {
        "metadata": {
            "generator": "data-pipeline",
            "generator_width": width,
            "title": f"Synthetic data pipeline ({width} transform partitions)",
            "description": "Airflow-style batch DAG with warehouse bottlenecks, feature building, GPU training, and downstream publishing tasks.",
        },
        "resource_capacities": {"gpu": 1, "warehouse": 2},
        "tasks": tasks,
    }

def _ensure_command_flags_are_valid(
    command: str,
    *,
    report_markdown_out: str | None,
    report_html_out: str | None,
    report_title: str | None,
    diagram_output_dir: str | None,
    worker_limit: int | None,
    compare_worker_limits: Sequence[int] | None,
    strategy: str | None,
    compare_strategies: Sequence[str] | None,
    resource_capacity_overrides: Sequence[str] | None,
    benchmark_markdown_out: str | None,
    benchmark_html_out: str | None,
    benchmark_json_out: str | None,
    benchmark_aggregate_csv_out: str | None,
    benchmark_strategy_csv_out: str | None,
    benchmark_title: str | None,
    generated_manifest_out: str | None,
    generator_width: int | None,
    generator_seed: int | None,
) -> None:
    if command == "generate" and any(
        value is not None
        for value in (
            report_markdown_out,
            report_html_out,
            report_title,
            diagram_output_dir,
            worker_limit,
            compare_worker_limits,
            strategy,
            compare_strategies,
            resource_capacity_overrides,
            benchmark_markdown_out,
            benchmark_html_out,
            benchmark_json_out,
            benchmark_aggregate_csv_out,
            benchmark_strategy_csv_out,
            benchmark_title,
        )
    ):
        raise ValueError("schedule/report/benchmark flags are not valid on the generate command")
    if command == "benchmark" and any(
        value is not None
        for value in (
            report_markdown_out,
            report_html_out,
            report_title,
            diagram_output_dir,
            worker_limit,
            compare_worker_limits,
            strategy,
            compare_strategies,
            resource_capacity_overrides,
        )
    ):
        raise ValueError("schedule/report flags are not valid on the benchmark command")
    if command != "report" and any(value is not None for value in (report_markdown_out, report_html_out, report_title, diagram_output_dir)):
        raise ValueError("report-specific flags require the report command")
    if command != "benchmark" and any(
        value is not None
        for value in (
            benchmark_markdown_out,
            benchmark_html_out,
            benchmark_json_out,
            benchmark_aggregate_csv_out,
            benchmark_strategy_csv_out,
            benchmark_title,
        )
    ):
        raise ValueError("benchmark-specific flags require the benchmark command")
    if command != "generate" and any(value is not None for value in (generated_manifest_out, generator_width, generator_seed)):
        raise ValueError("generator-specific flags require the generate command")
    if command not in {"report", "schedule"} and worker_limit is not None:
        raise ValueError("--worker-limit requires the schedule or report command")
    if command != "report" and compare_worker_limits:
        raise ValueError("--compare-worker-limit requires the report command")
    if command not in {"report", "schedule"} and strategy is not None:
        raise ValueError("--strategy requires the schedule or report command")
    if command != "report" and compare_strategies:
        raise ValueError("--compare-strategy requires the report command")
    if command not in {"report", "schedule"} and resource_capacity_overrides:
        raise ValueError("--resource-capacity requires the schedule or report command")
    if command == "schedule" and worker_limit is None:
        raise ValueError("the schedule command requires --worker-limit")
    if command == "report" and strategy is not None and worker_limit is None:
        raise ValueError("--strategy on the report command requires --worker-limit")
    if command == "report" and compare_strategies and worker_limit is None:
        raise ValueError("--compare-strategy requires --worker-limit on the report command")
    if worker_limit is not None and worker_limit <= 0:
        raise ValueError("--worker-limit must be a positive integer")
    if generator_width is not None and generator_width <= 0:
        raise ValueError("--generator-width must be a positive integer")
    if compare_worker_limits and any(limit <= 0 for limit in compare_worker_limits):
        raise ValueError("--compare-worker-limit values must be positive integers")
    if strategy is not None:
        _resolve_schedule_strategy(strategy)
    if compare_strategies:
        for item in compare_strategies:
            _resolve_schedule_strategy(item)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and plan dependency graphs")
    parser.add_argument(
        "command",
        choices=["validate", "plan", "critical-path", "layers", "diagram", "report", "schedule", "benchmark", "generate"],
        help="command to run",
    )
    parser.add_argument("graph", help="path to a JSON manifest or benchmark suite, or a generator name for generate")
    parser.add_argument("--json", action="store_true", dest="as_json", help="render machine-readable JSON output")
    parser.add_argument(
        "--format",
        dest="diagram_format",
        default="mermaid",
        choices=["mermaid", "dot"],
        help="diagram output format for the diagram command",
    )
    parser.add_argument("--report-markdown-out", help="write a recruiter-friendly Markdown walkthrough report")
    parser.add_argument("--report-html-out", help="write a compact static HTML dashboard for the report bundle")
    parser.add_argument("--report-title", help="optional title for the report command")
    parser.add_argument(
        "--diagram-output-dir",
        help="optional directory where the report command should emit Mermaid and DOT companion artifacts",
    )
    parser.add_argument("--benchmark-markdown-out", help="write a Markdown summary for the benchmark command")
    parser.add_argument("--benchmark-html-out", help="write a compact static HTML dashboard for the benchmark command")
    parser.add_argument("--benchmark-json-out", help="write the full benchmark JSON snapshot to a file")
    parser.add_argument("--benchmark-aggregate-csv-out", help="write aggregate strategy leaderboard rows as CSV")
    parser.add_argument("--benchmark-strategy-csv-out", help="write per-scenario strategy rows as CSV for plotting/notebooks")
    parser.add_argument("--benchmark-title", help="optional title for the benchmark command")
    parser.add_argument("--generated-manifest-out", help="write generated manifest JSON to a file for the generate command")
    parser.add_argument(
        "--generator-width",
        type=int,
        help="positive integer scale factor used by the generate command (unit-test shards, canary phases, transform partitions, or stress workload size)",
    )
    parser.add_argument(
        "--generator-seed",
        type=int,
        help="optional deterministic seed for the stress generator",
    )
    parser.add_argument(
        "--worker-limit",
        type=int,
        help="simulate a deterministic worker-limited schedule (required for schedule, optional for report)",
    )
    parser.add_argument(
        "--compare-worker-limit",
        dest="compare_worker_limits",
        action="append",
        type=int,
        help="repeatable extra worker limits to compare inside report output",
    )
    parser.add_argument(
        "--strategy",
        choices=SCHEDULE_STRATEGIES,
        help="ready-queue strategy for schedule/report worker-limited runs",
    )
    parser.add_argument(
        "--compare-strategy",
        dest="compare_strategies",
        action="append",
        choices=SCHEDULE_STRATEGIES,
        help="repeatable extra ready-queue strategies to compare inside report output (requires --worker-limit)",
    )
    parser.add_argument(
        "--resource-capacity",
        dest="resource_capacity_overrides",
        action="append",
        help="repeatable resource-class capacity override in class=count form for schedule/report commands",
    )
    return parser


def run_command(
    command: str,
    graph_path: str,
    as_json: bool = False,
    diagram_format: str = "mermaid",
    report_markdown_out: str | None = None,
    report_html_out: str | None = None,
    report_title: str | None = None,
    diagram_output_dir: str | None = None,
    worker_limit: int | None = None,
    compare_worker_limits: Sequence[int] | None = None,
    strategy: str | None = None,
    compare_strategies: Sequence[str] | None = None,
    resource_capacity_overrides: Sequence[str] | None = None,
    benchmark_markdown_out: str | None = None,
    benchmark_html_out: str | None = None,
    benchmark_json_out: str | None = None,
    benchmark_aggregate_csv_out: str | None = None,
    benchmark_strategy_csv_out: str | None = None,
    benchmark_title: str | None = None,
    generated_manifest_out: str | None = None,
    generator_width: int | None = None,
    generator_seed: int | None = None,
) -> str:
    _ensure_command_flags_are_valid(
        command,
        report_markdown_out=report_markdown_out,
        report_html_out=report_html_out,
        report_title=report_title,
        diagram_output_dir=diagram_output_dir,
        worker_limit=worker_limit,
        compare_worker_limits=compare_worker_limits,
        strategy=strategy,
        compare_strategies=compare_strategies,
        resource_capacity_overrides=resource_capacity_overrides,
        benchmark_markdown_out=benchmark_markdown_out,
        benchmark_html_out=benchmark_html_out,
        benchmark_json_out=benchmark_json_out,
        benchmark_aggregate_csv_out=benchmark_aggregate_csv_out,
        benchmark_strategy_csv_out=benchmark_strategy_csv_out,
        benchmark_title=benchmark_title,
        generated_manifest_out=generated_manifest_out,
        generator_width=generator_width,
        generator_seed=generator_seed,
    )
    if command == "generate":
        manifest = build_synthetic_manifest(
            graph_path,
            width=generator_width or DEFAULT_GENERATOR_WIDTH,
            seed=generator_seed,
        )
        rendered_manifest = json.dumps(manifest, indent=2)
        if generated_manifest_out:
            _write_text(generated_manifest_out, rendered_manifest + "\n")
        return rendered_manifest + "\n"

    if command == "benchmark":
        result = build_benchmark_suite_result(graph_path, title=benchmark_title)
        payload = benchmark_suite_to_dict(result)
        artifacts: dict[str, str] = {}
        if benchmark_markdown_out:
            artifacts["benchmark_markdown"] = benchmark_markdown_out
        if benchmark_html_out:
            artifacts["benchmark_html"] = benchmark_html_out
        if benchmark_json_out:
            artifacts["benchmark_json"] = benchmark_json_out
        if benchmark_aggregate_csv_out:
            artifacts["benchmark_aggregate_csv"] = benchmark_aggregate_csv_out
        if benchmark_strategy_csv_out:
            artifacts["benchmark_strategy_csv"] = benchmark_strategy_csv_out

        report = render_benchmark_suite_markdown(
            result,
            artifact_links=_build_benchmark_artifact_links(
                artifacts,
                benchmark_markdown_out=benchmark_markdown_out,
            ),
        )
        if benchmark_markdown_out:
            _write_text(benchmark_markdown_out, report)
        if benchmark_aggregate_csv_out:
            aggregate_csv = render_benchmark_aggregate_csv(result)
            _write_text(benchmark_aggregate_csv_out, aggregate_csv)
        if benchmark_strategy_csv_out:
            strategy_csv = render_benchmark_strategy_csv(result)
            _write_text(benchmark_strategy_csv_out, strategy_csv)
        if benchmark_html_out:
            _write_text(
                benchmark_html_out,
                render_benchmark_dashboard_html(
                    result,
                    html_output_path=benchmark_html_out,
                    artifacts=artifacts,
                ),
            )
        payload["benchmark_markdown"] = report
        payload["benchmark_markdown_out"] = benchmark_markdown_out
        payload["benchmark_html_out"] = benchmark_html_out
        payload["benchmark_json_out"] = benchmark_json_out
        payload["benchmark_aggregate_csv_out"] = benchmark_aggregate_csv_out
        payload["benchmark_strategy_csv_out"] = benchmark_strategy_csv_out
        payload["artifacts"] = artifacts
        if benchmark_json_out:
            _write_text(benchmark_json_out, json.dumps(payload, indent=2) + "\n")
        if as_json:
            return json.dumps(payload, indent=2)
        return report

    manifest = load_manifest(graph_path)
    manifest_metadata = parse_manifest_metadata(manifest)
    tasks = parse_tasks(manifest)
    manifest_resource_capacities = parse_resource_capacities(manifest)
    validate_manifest_resource_capacities(tasks, manifest_resource_capacities)
    plan = build_plan(tasks)
    resolved_strategy = _resolve_schedule_strategy(strategy)
    schedule_cache: dict[tuple[int, str], WorkerLimitedSchedule] = {}
    resolved_resource_capacities: dict[str, int] | None = None

    def get_resolved_resource_capacities() -> dict[str, int]:
        nonlocal resolved_resource_capacities
        if resolved_resource_capacities is None:
            resolved_resource_capacities = resolve_resource_capacities(
                tasks,
                manifest_resource_capacities,
                resource_capacity_overrides,
            )
        return resolved_resource_capacities

    def get_schedule(limit: int, schedule_strategy: str) -> WorkerLimitedSchedule:
        cache_key = (limit, schedule_strategy)
        cached = schedule_cache.get(cache_key)
        if cached is None:
            cached = build_worker_limited_schedule(
                tasks,
                plan,
                worker_limit=limit,
                strategy=schedule_strategy,
                resource_capacities=get_resolved_resource_capacities(),
            )
            schedule_cache[cache_key] = cached
        return cached

    schedule = get_schedule(worker_limit, resolved_strategy) if worker_limit is not None else None
    comparison_limits = _collect_report_worker_limits(
        worker_limit=worker_limit if command == "report" else None,
        compare_worker_limits=compare_worker_limits if command == "report" else None,
    )
    comparison_schedules = [get_schedule(limit, resolved_strategy) for limit in comparison_limits]
    strategy_comparison_schedules = (
        [
            get_schedule(worker_limit, schedule_strategy)
            for schedule_strategy in _collect_report_strategies(
                strategy=resolved_strategy,
                compare_strategies=compare_strategies if command == "report" else None,
            )
        ]
        if command == "report" and worker_limit is not None
        else []
    )
    if command == "validate":
        payload = {"status": "ok", "tasks": len(tasks), "order": plan.order}
    elif command == "critical-path":
        payload = {"critical_path": plan.critical_path, "total_duration": plan.total_duration}
    elif command == "layers":
        payload = {"layers": plan.layers, "total_duration": plan.total_duration}
    elif command == "diagram":
        diagram = render_dependency_diagram(tasks, plan, diagram_format=diagram_format)
        if as_json:
            return json.dumps({"format": diagram_format, "diagram": diagram}, indent=2)
        return diagram
    elif command == "schedule":
        if schedule is None:
            raise ValueError("the schedule command requires --worker-limit")
        if as_json:
            return json.dumps(schedule_to_dict(schedule), indent=2)
        return _render_text_schedule(schedule)
    elif command == "report":
        resolved_report_title = build_report_title(
            source_label=_display_path_label(graph_path),
            explicit_title=report_title,
            manifest_title=manifest_metadata.get("title"),
        )
        artifacts = (
            write_report_supporting_artifacts(
                tasks,
                plan,
                graph_path=graph_path,
                output_dir=diagram_output_dir,
                worker_limited_schedule=schedule,
                comparison_schedules=comparison_schedules,
                strategy_comparison_schedules=strategy_comparison_schedules,
            )
            if diagram_output_dir
            else {}
        )
        diagram_links = (
            _build_report_artifact_links(
                artifacts,
                report_markdown_out=report_markdown_out,
                report_html_out=report_html_out,
            )
            if artifacts or report_html_out
            else None
        )
        display_graph_label = _display_path_label(graph_path)
        report = render_report_markdown(
            tasks,
            plan,
            source_label=display_graph_label,
            title=resolved_report_title,
            manifest_title=manifest_metadata.get("title"),
            manifest_description=manifest_metadata.get("description"),
            diagram_links=diagram_links,
            worker_limited_schedule=schedule,
            comparison_schedules=comparison_schedules,
            strategy_comparison_schedules=strategy_comparison_schedules,
        )
        if report_markdown_out:
            _write_text(report_markdown_out, report)
        if report_html_out:
            _write_text(
                report_html_out,
                render_report_dashboard_html(
                    tasks,
                    plan,
                    source_label=display_graph_label,
                    html_output_path=report_html_out,
                    title=resolved_report_title,
                    manifest_title=manifest_metadata.get("title"),
                    manifest_description=manifest_metadata.get("description"),
                    report_markdown_out=report_markdown_out,
                    artifacts=artifacts,
                    worker_limited_schedule=schedule,
                    comparison_schedules=comparison_schedules,
                    strategy_comparison_schedules=strategy_comparison_schedules,
                ),
            )
        if as_json:
            return json.dumps(
                {
                    "summary": plan_to_dict(plan),
                    "worker_limited_schedule": schedule_to_dict(schedule) if schedule else None,
                    "worker_limited_schedule_comparisons": [schedule_to_dict(item) for item in comparison_schedules],
                    "worker_limited_strategy_comparisons": [schedule_to_dict(item) for item in strategy_comparison_schedules],
                    "report_title": resolved_report_title,
                    "report_markdown": report,
                    "artifacts": artifacts,
                    "report_markdown_out": report_markdown_out,
                    "report_html_out": report_html_out,
                },
                indent=2,
            )
        return report
    else:
        payload = plan_to_dict(plan)

    if as_json:
        return json.dumps(payload, indent=2)
    if command == "validate":
        return f"manifest valid: {len(tasks)} tasks"
    if command == "critical-path":
        return f"critical path ({plan.total_duration}): {', '.join(plan.critical_path)}"
    if command == "layers":
        return "\n".join(f"layer {idx}: {', '.join(layer)}" for idx, layer in enumerate(plan.layers))
    return _render_text_plan(plan)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = run_command(
            args.command,
            args.graph,
            as_json=args.as_json,
            diagram_format=args.diagram_format,
            report_markdown_out=args.report_markdown_out,
            report_html_out=args.report_html_out,
            report_title=args.report_title,
            diagram_output_dir=args.diagram_output_dir,
            worker_limit=args.worker_limit,
            compare_worker_limits=args.compare_worker_limits,
            strategy=args.strategy,
            compare_strategies=args.compare_strategies,
            resource_capacity_overrides=args.resource_capacity_overrides,
            benchmark_markdown_out=args.benchmark_markdown_out,
            benchmark_html_out=args.benchmark_html_out,
            benchmark_json_out=args.benchmark_json_out,
            benchmark_aggregate_csv_out=args.benchmark_aggregate_csv_out,
            benchmark_strategy_csv_out=args.benchmark_strategy_csv_out,
            benchmark_title=args.benchmark_title,
            generated_manifest_out=args.generated_manifest_out,
            generator_width=args.generator_width,
            generator_seed=args.generator_seed,
        )
    except (GraphValidationError, CycleError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
