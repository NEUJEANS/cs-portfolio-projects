#!/usr/bin/env python3
"""Plan and inspect dependency graphs for build or project workflows."""

from __future__ import annotations

import argparse
import heapq
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


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


def build_plan(tasks: dict[str, Task]) -> PlanResult:
    order = topological_order(tasks)
    layers = build_layers(tasks, order)
    timings, total_duration, critical_path = compute_timings(tasks, order)
    return PlanResult(order=order, layers=layers, total_duration=total_duration, timings=timings, critical_path=critical_path)


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
) -> dict[str, str]:
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

    return {
        "mermaid_source": str(mermaid_path),
        "mermaid_preview": str(mermaid_preview_path),
        "dot_source": str(dot_path),
    }


def render_report_markdown(
    tasks: dict[str, Task],
    plan: PlanResult,
    *,
    source_label: str,
    title: str | None = None,
    diagram_links: Sequence[tuple[str, str]] | None = None,
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
                f"- widest parallel layer: {_markdown_code(f'layer {widest_layer_index}') } with "
                f"{_markdown_code(len(widest_layer))} task(s)"
                + (
                    ": " + ", ".join(_markdown_code(name) for name in widest_layer)
                    if widest_layer
                    else ""
                )
            ),
            f"- non-critical slack budget available for schedule tradeoffs: {_markdown_code(total_slack)} time units",
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
    artifacts: dict[str, str],
    *,
    report_markdown_out: str | None,
) -> list[tuple[str, str]]:
    ordered = [
        ("GitHub-friendly Mermaid preview", artifacts["mermaid_preview"]),
        ("Mermaid source", artifacts["mermaid_source"]),
        ("Graphviz DOT source", artifacts["dot_source"]),
    ]
    if report_markdown_out:
        return [
            (label, _relative_markdown_link(target, from_path=report_markdown_out))
            for label, target in ordered
        ]
    return ordered


def _ensure_report_flags_are_valid(
    command: str,
    *,
    report_markdown_out: str | None,
    report_title: str | None,
    diagram_output_dir: str | None,
) -> None:
    if command != "report" and any(value is not None for value in (report_markdown_out, report_title, diagram_output_dir)):
        raise ValueError("report-specific flags require the report command")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and plan dependency graphs")
    parser.add_argument(
        "command",
        choices=["validate", "plan", "critical-path", "layers", "diagram", "report"],
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
    return parser


def run_command(
    command: str,
    graph_path: str,
    as_json: bool = False,
    diagram_format: str = "mermaid",
    report_markdown_out: str | None = None,
    report_title: str | None = None,
    diagram_output_dir: str | None = None,
) -> str:
    _ensure_report_flags_are_valid(
        command,
        report_markdown_out=report_markdown_out,
        report_title=report_title,
        diagram_output_dir=diagram_output_dir,
    )
    tasks = parse_tasks(load_manifest(graph_path))
    plan = build_plan(tasks)
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
    elif command == "report":
        artifacts = (
            write_report_supporting_artifacts(tasks, plan, graph_path=graph_path, output_dir=diagram_output_dir)
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
        )
        if report_markdown_out:
            _write_text(report_markdown_out, report)
        if as_json:
            return json.dumps(
                {
                    "summary": plan_to_dict(plan),
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
        )
    except (GraphValidationError, CycleError, json.JSONDecodeError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
