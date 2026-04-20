#!/usr/bin/env python3
"""Plan and inspect dependency graphs for build or project workflows."""

from __future__ import annotations

import argparse
import heapq
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


DEFAULT_SCHEDULE_STRATEGY = "critical-first"
SCHEDULE_STRATEGIES = ("critical-first", "fifo", "longest-processing-time")


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


def load_manifest(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GraphValidationError("manifest must be a JSON object")
    return data


def parse_tasks(data: dict) -> dict[str, Task]:
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
        if name in tasks:
            raise GraphValidationError(f"duplicate task name: {name}")
        deduped_deps = tuple(dict.fromkeys(dep.strip() for dep in deps))
        tasks[name] = Task(name=name, deps=deduped_deps, duration=duration, command=command)

    unknown = sorted({dep for task in tasks.values() for dep in task.deps if dep not in tasks})
    if unknown:
        raise GraphValidationError(f"unknown dependencies referenced: {', '.join(unknown)}")
    return tasks


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
) -> WorkerLimitedSchedule:
    if worker_limit <= 0:
        raise ValueError("--worker-limit must be a positive integer")
    resolved_strategy = _resolve_schedule_strategy(strategy)

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
    running: list[tuple[int, int, int, str]] = []
    assignments: list[ScheduledTask] = []
    dispatch_order: list[str] = []
    current_time = 0

    while ready_queue or running:
        while ready_queue and available_workers:
            *_, name = heapq.heappop(ready_queue)
            worker = heapq.heappop(available_workers)
            start = current_time
            finish = start + tasks[name].duration
            ready_time = ready_at.get(name, current_time)
            assignments.append(
                ScheduledTask(
                    name=name,
                    worker=worker,
                    ready_at=ready_time,
                    start=start,
                    finish=finish,
                    queue_delay=start - ready_time,
                    duration=tasks[name].duration,
                    critical=timings_by_name[name].critical,
                )
            )
            dispatch_order.append(name)
            heapq.heappush(running, (finish, worker, order_index[name], name))

        if not running:
            break

        current_time = running[0][0]
        completed: list[str] = []
        while running and running[0][0] == current_time:
            _, worker, _, name = heapq.heappop(running)
            finish_times[name] = current_time
            heapq.heappush(available_workers, worker)
            completed.append(name)

        for finished_name in sorted(completed, key=order_index.get):
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
                }
                for item in timeline
            ]
            for timeline in schedule.worker_timelines
        ],
    }


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
        "worker timelines:",
    ]
    for index, timeline in enumerate(schedule.worker_timelines, start=1):
        if not timeline:
            lines.append(f"- worker {index}: (idle)")
            continue
        rendered = ", ".join(f"{item.name} [{item.start}→{item.finish}]" for item in timeline)
        lines.append(f"- worker {index}: {rendered}")

    delayed = [item for item in schedule.assignments if item.queue_delay > 0]
    if delayed:
        lines.append("queue delays:")
        for item in delayed:
            lines.append(
                f"- {item.name}: ready={item.ready_at}, start={item.start}, delay={item.queue_delay}, worker={item.worker}"
            )
    return "\n".join(lines)


def _quote_dot(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return '"' + escaped + '"'


def _escape_mermaid(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;").replace("\n", "<br/>")


def _diagram_label(timing: TaskTiming) -> str:
    return f"{timing.name}\nd={timing.duration}, slack={timing.slack}"


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
                label = _escape_mermaid(_diagram_label(timings[name]))
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
            attributes = [f"label={_quote_dot(_diagram_label(timings[name]))}"]
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


def build_report_title(*, source_label: str, explicit_title: str | None = None) -> str:
    if explicit_title:
        return explicit_title
    display_name = _humanize_stem(Path(source_label).stem).title()
    return f"Dependency graph walkthrough — {display_name}"


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
        include_strategy_in_key = len({schedule.strategy for schedule in schedule_lookup.values()}) > 1 or any(
            schedule.strategy != DEFAULT_SCHEDULE_STRATEGY for schedule in schedule_lookup.values()
        )
        ordered_schedules = sorted(
            schedule_lookup.values(),
            key=lambda item: (item.worker_limit, SCHEDULE_STRATEGIES.index(item.strategy), item.dispatch_order),
        )
        for schedule in ordered_schedules:
            key = (
                f"{schedule.worker_limit}:{schedule.strategy}"
                if include_strategy_in_key
                else str(schedule.worker_limit)
            )
            filename = f"{stem}_{_worker_limit_slug(schedule.worker_limit)}"
            if include_strategy_in_key or schedule.strategy != DEFAULT_SCHEDULE_STRATEGY:
                filename += f"_{_strategy_slug(schedule.strategy)}"
            schedule_json_path = output_dir / f"{filename}_schedule.json"
            _write_text(schedule_json_path, json.dumps(schedule_to_dict(schedule), indent=2) + "\n")
            schedule_paths[key] = str(schedule_json_path)
        artifacts["worker_limited_schedule_jsons"] = schedule_paths
        if worker_limited_schedule is not None:
            primary_key = (
                f"{worker_limited_schedule.worker_limit}:{worker_limited_schedule.strategy}"
                if include_strategy_in_key
                else str(worker_limited_schedule.worker_limit)
            )
            artifacts["worker_limited_schedule_json"] = schedule_paths[primary_key]
        elif len(schedule_paths) == 1:
            artifacts["worker_limited_schedule_json"] = next(iter(schedule_paths.values()))

    return artifacts


def render_report_markdown(
    tasks: dict[str, Task],
    plan: PlanResult,
    *,
    source_label: str,
    title: str | None = None,
    diagram_links: Sequence[tuple[str, str]] | None = None,
    worker_limited_schedule: WorkerLimitedSchedule | None = None,
    comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
    strategy_comparison_schedules: Sequence[WorkerLimitedSchedule] | None = None,
) -> str:
    resolved_title = build_report_title(source_label=source_label, explicit_title=title)
    timings_by_name = {timing.name: timing for timing in plan.timings}
    layer_by_name = {name: index for index, layer in enumerate(plan.layers) for name in layer}
    total_slack = sum(item.slack for item in plan.timings if not item.critical)
    widest_layer_index, widest_layer = max(
        enumerate(plan.layers),
        key=lambda item: (len(item[1]), -item[0]),
        default=(0, []),
    )
    critical_path_rendered = " -> ".join(plan.critical_path) if plan.critical_path else "(none)"
    comparison_schedule_lookup = {schedule.worker_limit: schedule for schedule in comparison_schedules or ()}
    if worker_limited_schedule is not None:
        comparison_schedule_lookup.setdefault(worker_limited_schedule.worker_limit, worker_limited_schedule)
    ordered_comparison_schedules = [comparison_schedule_lookup[limit] for limit in sorted(comparison_schedule_lookup)]

    ordered_strategy_schedules: list[WorkerLimitedSchedule] = []
    seen_strategies: set[str] = set()
    if worker_limited_schedule is not None:
        ordered_strategy_schedules.append(worker_limited_schedule)
        seen_strategies.add(worker_limited_schedule.strategy)
    for schedule in strategy_comparison_schedules or ():
        if schedule.strategy in seen_strategies:
            continue
        ordered_strategy_schedules.append(schedule)
        seen_strategies.add(schedule.strategy)

    lines = [f"# {resolved_title}", ""]
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
            lines.append(
                f"- biggest queue delay: {_markdown_code(most_delayed.name)} waited {_markdown_code(most_delayed.queue_delay)} time unit(s) after becoming ready"
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
                f"{item.name} ({item.start}→{item.finish})" for item in timeline
            )
            lines.append(
                f"- Worker {index} ({_markdown_code(window)}): {tasks_rendered}"
            )

        lines.extend(
            [
                "",
                "### Worker-limited task table",
                "",
                "| Task | Worker | Ready at | Start | Finish | Queue delay | Critical |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for item in worker_limited_schedule.assignments:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_markdown_table_cell(item.name),
                        str(item.worker),
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
            "| Task | Layer | Depends on | Duration | ES | EF | LS | LF | Slack | Critical | Command |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
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
                f"   - Command: {command}",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _build_report_artifact_links(
    artifacts: dict[str, Any],
    *,
    report_markdown_out: str | None,
) -> list[tuple[str, str]]:
    ordered = [
        ("GitHub-friendly Mermaid preview", artifacts["mermaid_preview"]),
        ("Mermaid source", artifacts["mermaid_source"]),
        ("Graphviz DOT source", artifacts["dot_source"]),
    ]
    schedule_paths = artifacts.get("worker_limited_schedule_jsons") or {}
    if isinstance(schedule_paths, dict) and schedule_paths:
        parsed_schedule_paths: list[tuple[int, str | None, str]] = []
        for raw_key, path in schedule_paths.items():
            if ":" in raw_key:
                raw_limit, strategy = raw_key.split(":", maxsplit=1)
                parsed_schedule_paths.append((int(raw_limit), strategy, path))
            else:
                parsed_schedule_paths.append((int(raw_key), None, path))

        parsed_schedule_paths.sort(
            key=lambda item: (item[0], SCHEDULE_STRATEGIES.index(item[1]) if item[1] else -1)
        )

        if len(parsed_schedule_paths) == 1 and parsed_schedule_paths[0][1] is None:
            ordered.append(("Worker-limited schedule JSON", parsed_schedule_paths[0][2]))
        else:
            for worker_limit, strategy, path in parsed_schedule_paths:
                label = f"Worker-limited schedule JSON ({_format_worker_limit_label(worker_limit)}"
                if strategy is not None:
                    label += f", {_format_schedule_strategy_label(strategy)}"
                label += ")"
                ordered.append((label, path))
    if report_markdown_out:
        return [
            (label, _relative_markdown_link(target, from_path=report_markdown_out))
            for label, target in ordered
        ]
    return ordered


def _ensure_command_flags_are_valid(
    command: str,
    *,
    report_markdown_out: str | None,
    report_title: str | None,
    diagram_output_dir: str | None,
    worker_limit: int | None,
    compare_worker_limits: Sequence[int] | None,
    strategy: str | None,
    compare_strategies: Sequence[str] | None,
) -> None:
    if command != "report" and any(value is not None for value in (report_markdown_out, report_title, diagram_output_dir)):
        raise ValueError("report-specific flags require the report command")
    if command not in {"report", "schedule"} and worker_limit is not None:
        raise ValueError("--worker-limit requires the schedule or report command")
    if command != "report" and compare_worker_limits:
        raise ValueError("--compare-worker-limit requires the report command")
    if command not in {"report", "schedule"} and strategy is not None:
        raise ValueError("--strategy requires the schedule or report command")
    if command != "report" and compare_strategies:
        raise ValueError("--compare-strategy requires the report command")
    if command == "schedule" and worker_limit is None:
        raise ValueError("the schedule command requires --worker-limit")
    if command == "report" and strategy is not None and worker_limit is None:
        raise ValueError("--strategy on the report command requires --worker-limit")
    if command == "report" and compare_strategies and worker_limit is None:
        raise ValueError("--compare-strategy requires --worker-limit on the report command")
    if worker_limit is not None and worker_limit <= 0:
        raise ValueError("--worker-limit must be a positive integer")
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
        choices=["validate", "plan", "critical-path", "layers", "diagram", "report", "schedule"],
        help="command to run",
    )
    parser.add_argument("graph", help="path to a JSON manifest")
    parser.add_argument("--json", action="store_true", dest="as_json", help="render machine-readable JSON output")
    parser.add_argument(
        "--format",
        dest="diagram_format",
        default="mermaid",
        choices=["mermaid", "dot"],
        help="diagram output format for the diagram command",
    )
    parser.add_argument("--report-markdown-out", help="write a recruiter-friendly Markdown walkthrough report")
    parser.add_argument("--report-title", help="optional title for the report command")
    parser.add_argument(
        "--diagram-output-dir",
        help="optional directory where the report command should emit Mermaid and DOT companion artifacts",
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
    return parser


def run_command(
    command: str,
    graph_path: str,
    as_json: bool = False,
    diagram_format: str = "mermaid",
    report_markdown_out: str | None = None,
    report_title: str | None = None,
    diagram_output_dir: str | None = None,
    worker_limit: int | None = None,
    compare_worker_limits: Sequence[int] | None = None,
    strategy: str | None = None,
    compare_strategies: Sequence[str] | None = None,
) -> str:
    _ensure_command_flags_are_valid(
        command,
        report_markdown_out=report_markdown_out,
        report_title=report_title,
        diagram_output_dir=diagram_output_dir,
        worker_limit=worker_limit,
        compare_worker_limits=compare_worker_limits,
        strategy=strategy,
        compare_strategies=compare_strategies,
    )
    tasks = parse_tasks(load_manifest(graph_path))
    plan = build_plan(tasks)
    resolved_strategy = _resolve_schedule_strategy(strategy)
    schedule_cache: dict[tuple[int, str], WorkerLimitedSchedule] = {}

    def get_schedule(limit: int, schedule_strategy: str) -> WorkerLimitedSchedule:
        cache_key = (limit, schedule_strategy)
        cached = schedule_cache.get(cache_key)
        if cached is None:
            cached = build_worker_limited_schedule(tasks, plan, worker_limit=limit, strategy=schedule_strategy)
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
        diagram_links = _build_report_artifact_links(artifacts, report_markdown_out=report_markdown_out) if artifacts else None
        report = render_report_markdown(
            tasks,
            plan,
            source_label=graph_path,
            title=report_title,
            diagram_links=diagram_links,
            worker_limited_schedule=schedule,
            comparison_schedules=comparison_schedules,
            strategy_comparison_schedules=strategy_comparison_schedules,
        )
        if report_markdown_out:
            _write_text(report_markdown_out, report)
        if as_json:
            return json.dumps(
                {
                    "summary": plan_to_dict(plan),
                    "worker_limited_schedule": schedule_to_dict(schedule) if schedule else None,
                    "worker_limited_schedule_comparisons": [schedule_to_dict(item) for item in comparison_schedules],
                    "worker_limited_strategy_comparisons": [schedule_to_dict(item) for item in strategy_comparison_schedules],
                    "report_title": build_report_title(source_label=graph_path, explicit_title=report_title),
                    "report_markdown": report,
                    "artifacts": artifacts,
                    "report_markdown_out": report_markdown_out,
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
            report_title=args.report_title,
            diagram_output_dir=args.diagram_output_dir,
            worker_limit=args.worker_limit,
            compare_worker_limits=args.compare_worker_limits,
            strategy=args.strategy,
            compare_strategies=args.compare_strategies,
        )
    except (GraphValidationError, CycleError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
