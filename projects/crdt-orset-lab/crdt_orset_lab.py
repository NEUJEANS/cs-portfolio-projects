from __future__ import annotations

import argparse
import json
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


def write_text_output(path: str | Path, content: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)


def add_timeline_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeline-markdown-out")
    parser.add_argument("--timeline-mermaid-out")
    parser.add_argument("--timeline-svg-out")


def timeline_title_from_args(args: argparse.Namespace) -> str:
    if args.command == "run-script":
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
        ]
    ):
        return

    title = timeline_title_from_args(args)
    if args.timeline_markdown_out:
        write_text_output(args.timeline_markdown_out, render_timeline_markdown(snapshot, title))
    if args.timeline_mermaid_out:
        write_text_output(args.timeline_mermaid_out, render_timeline_mermaid(snapshot, title))
    if args.timeline_svg_out:
        write_text_output(args.timeline_svg_out, render_timeline_svg(snapshot, title))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Observed-remove set CRDT lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_script = subparsers.add_parser("run-script", help="run a JSON operation script across replicas")
    run_script.add_argument("--replicas", nargs="+", required=True)
    run_script.add_argument("--script", required=True)
    add_timeline_output_arguments(run_script)

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
