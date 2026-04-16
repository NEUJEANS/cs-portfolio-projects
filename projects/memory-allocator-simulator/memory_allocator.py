from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Segment:
    start: int
    size: int
    allocated: bool = False
    allocation_id: str | None = None
    requested_size: int | None = None

    @property
    def end(self) -> int:
        return self.start + self.size

    @property
    def internal_fragmentation(self) -> int:
        if not self.allocated:
            return 0
        requested_size = self.requested_size if self.requested_size is not None else self.size
        return self.size - requested_size

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "size": self.size,
            "allocated": self.allocated,
            "allocation_id": self.allocation_id,
            "requested_size": self.requested_size,
            "internal_fragmentation": self.internal_fragmentation,
        }


VALID_STRATEGIES = {"first-fit", "best-fit", "worst-fit"}


class MemoryAllocator:
    def __init__(self, capacity: int, strategy: str = "first-fit", alignment: int = 1):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if strategy not in VALID_STRATEGIES:
            raise ValueError(f"unknown strategy: {strategy}")
        if alignment <= 0:
            raise ValueError("alignment must be positive")
        self.capacity = capacity
        self.strategy = strategy
        self.alignment = alignment
        self.segments = [Segment(start=0, size=capacity, allocated=False)]

    def _round_size(self, requested_size: int) -> int:
        if requested_size <= 0:
            raise ValueError("size must be positive")
        remainder = requested_size % self.alignment
        if remainder == 0:
            return requested_size
        return requested_size + (self.alignment - remainder)

    def _free_segments(self) -> list[tuple[int, Segment]]:
        return [
            (index, segment)
            for index, segment in enumerate(self.segments)
            if not segment.allocated
        ]

    def _pick_free_segment(self, size: int) -> int | None:
        candidates = [
            (index, segment)
            for index, segment in self._free_segments()
            if segment.size >= size
        ]
        if not candidates:
            return None

        if self.strategy == "first-fit":
            return candidates[0][0]
        if self.strategy == "best-fit":
            return min(candidates, key=lambda item: (item[1].size, item[1].start))[0]
        if self.strategy == "worst-fit":
            return max(candidates, key=lambda item: (item[1].size, -item[1].start))[0]
        raise ValueError(f"unknown strategy: {self.strategy}")

    def allocate(self, allocation_id: str, size: int) -> dict:
        if size <= 0:
            raise ValueError("size must be positive")
        if any(seg.allocated and seg.allocation_id == allocation_id for seg in self.segments):
            raise ValueError(f"allocation id already exists: {allocation_id}")

        allocated_size = self._round_size(size)
        index = self._pick_free_segment(allocated_size)
        if index is None:
            raise MemoryError(
                f"unable to allocate requested={size} bytes aligned={allocated_size} bytes with strategy {self.strategy}; "
                f"largest_free_block={self.metrics()['largest_free_block']}"
            )

        segment = self.segments[index]
        allocated = Segment(
            start=segment.start,
            size=allocated_size,
            allocated=True,
            allocation_id=allocation_id,
            requested_size=size,
        )
        remainder = segment.size - allocated_size

        new_segments = self.segments[:index] + [allocated]
        if remainder:
            new_segments.append(Segment(start=segment.start + allocated_size, size=remainder, allocated=False))
        new_segments.extend(self.segments[index + 1 :])
        self.segments = new_segments
        return allocated.to_dict()

    def free(self, allocation_id: str) -> dict:
        for index, segment in enumerate(self.segments):
            if segment.allocated and segment.allocation_id == allocation_id:
                released = Segment(start=segment.start, size=segment.size, allocated=False)
                self.segments[index] = released
                self._merge_free_neighbors()
                return released.to_dict()
        raise KeyError(f"unknown allocation id: {allocation_id}")

    def compact(self) -> list[dict]:
        allocated = [segment for segment in self.segments if segment.allocated]
        next_start = 0
        moved: list[dict] = []
        compacted: list[Segment] = []
        for segment in allocated:
            if segment.start != next_start:
                moved.append({
                    "allocation_id": segment.allocation_id,
                    "from": segment.start,
                    "to": next_start,
                    "size": segment.size,
                    "requested_size": segment.requested_size,
                })
            compacted.append(
                Segment(
                    start=next_start,
                    size=segment.size,
                    allocated=True,
                    allocation_id=segment.allocation_id,
                    requested_size=segment.requested_size,
                )
            )
            next_start += segment.size

        free_size = self.capacity - next_start
        if free_size:
            compacted.append(Segment(start=next_start, size=free_size, allocated=False))
        self.segments = compacted
        return moved

    def _merge_free_neighbors(self) -> None:
        merged: list[Segment] = []
        for segment in self.segments:
            if merged and not merged[-1].allocated and not segment.allocated:
                merged[-1].size += segment.size
            else:
                merged.append(Segment(**segment.__dict__))
        self.segments = merged

    def layout(self) -> list[dict]:
        return [segment.to_dict() for segment in self.segments]

    def metrics(self) -> dict:
        free_blocks = [segment.size for segment in self.segments if not segment.allocated]
        allocated_segments = [segment for segment in self.segments if segment.allocated]
        allocated_bytes = sum(segment.size for segment in allocated_segments)
        requested_bytes = sum(segment.requested_size or 0 for segment in allocated_segments)
        free_bytes = sum(free_blocks)
        largest_free_block = max(free_blocks, default=0)
        internal_fragmentation = sum(segment.internal_fragmentation for segment in allocated_segments)
        return {
            "capacity": self.capacity,
            "strategy": self.strategy,
            "alignment": self.alignment,
            "requested_bytes": requested_bytes,
            "allocated_bytes": allocated_bytes,
            "free_bytes": free_bytes,
            "utilization": round(allocated_bytes / self.capacity, 4),
            "payload_utilization": round(requested_bytes / self.capacity, 4),
            "hole_count": len(free_blocks),
            "largest_free_block": largest_free_block,
            "external_fragmentation": free_bytes - largest_free_block,
            "internal_fragmentation": internal_fragmentation,
        }


def allocation_symbol(allocation_id: str | None) -> str:
    if not allocation_id:
        return "#"
    for character in allocation_id:
        if character.isalnum():
            return character.upper()
    return "#"


def render_layout_ascii(layout: list[dict], capacity: int, width: int | None = None) -> str:
    if capacity <= 0:
        raise ValueError("capacity must be positive")

    width = width or min(capacity, 64)
    if width <= 0:
        raise ValueError("timeline width must be positive")

    if capacity <= width:
        cells: list[str] = []
        for segment in layout:
            symbol = allocation_symbol(segment["allocation_id"]) if segment["allocated"] else "."
            cells.extend(symbol for _ in range(segment["size"]))
        return "".join(cells)

    rendered: list[str] = []
    segment_index = 0
    for column in range(width):
        address = min(capacity - 1, (2 * column + 1) * capacity // (2 * width))
        while segment_index < len(layout) - 1 and address >= layout[segment_index]["end"]:
            segment_index += 1
        segment = layout[segment_index]
        rendered.append(allocation_symbol(segment["allocation_id"]) if segment["allocated"] else ".")
    return "".join(rendered)


def capture_timeline_snapshot(
    allocator: MemoryAllocator,
    operation: str,
    step: int,
    timeline_width: int | None = None,
) -> dict:
    layout = allocator.layout()
    return {
        "step": step,
        "operation": operation,
        "render": render_layout_ascii(layout, capacity=allocator.capacity, width=timeline_width),
        "layout": layout,
        "metrics": allocator.metrics(),
    }


def export_timeline_markdown(timeline: list[dict], capacity: int) -> str:
    ruler_width = len(timeline[0]["render"]) if timeline else 0
    ruler = "0" + (" " * max(ruler_width - 2, 0)) + str(capacity)
    lines = ["# Memory Allocation Timeline", "", f"Capacity: {capacity} bytes", ""]
    if timeline:
        first_metrics = timeline[0]["metrics"]
        lines.append(f"Alignment: {first_metrics['alignment']} byte(s)")
        lines.append("")
    if ruler_width:
        lines.extend(["```text", ruler, "```", ""])
    lines.extend([
        "| Step | Operation | Render | Requested | Allocated | Internal frag | Free bytes | Holes |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for entry in timeline:
        metrics = entry["metrics"]
        lines.append(
            f"| {entry['step']} | `{entry['operation']}` | `{entry['render']}` | {metrics['requested_bytes']} | {metrics['allocated_bytes']} | {metrics['internal_fragmentation']} | {metrics['free_bytes']} | {metrics['hole_count']} |"
        )
    return "\n".join(lines)


def parse_operation(raw: str) -> tuple[str, list[str]]:
    parts = raw.split(":")
    command = parts[0]
    return command, parts[1:]


def load_trace(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, list):
        operations = payload
        trace = {}
    elif isinstance(payload, dict):
        operations = payload.get("operations", [])
        trace = {
            "capacity": payload.get("capacity"),
            "strategy": payload.get("strategy"),
            "alignment": payload.get("alignment"),
            "timeline": payload.get("timeline"),
            "timeline_width": payload.get("timeline_width"),
            "operations": operations,
        }
    else:
        raise ValueError("trace must be a JSON object or list")

    if not isinstance(operations, list) or not all(isinstance(item, str) for item in operations):
        raise ValueError("trace operations must be a list of strings")
    trace["operations"] = operations
    return trace


def write_trace(path: str | Path, trace: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(trace, indent=2) + "\n")


def run_operations(
    allocator: MemoryAllocator,
    operations: Iterable[str],
    include_timeline: bool = False,
    timeline_width: int | None = None,
) -> dict:
    history = []
    timeline = [capture_timeline_snapshot(allocator, operation="initial", step=0, timeline_width=timeline_width)] if include_timeline else []
    for step, raw in enumerate(operations, start=1):
        command, args = parse_operation(raw)
        if command == "alloc" and len(args) == 2:
            allocation_id, size_text = args
            result = allocator.allocate(allocation_id, int(size_text))
        elif command == "free" and len(args) == 1:
            result = allocator.free(args[0])
        elif command == "compact" and not args:
            result = allocator.compact()
        else:
            raise ValueError(f"invalid operation: {raw}")
        history.append({"operation": raw, "result": result})
        if include_timeline:
            timeline.append(capture_timeline_snapshot(allocator, operation=raw, step=step, timeline_width=timeline_width))

    payload = {
        "history": history,
        "metrics": allocator.metrics(),
        "layout": allocator.layout(),
    }
    if include_timeline:
        payload["timeline"] = timeline
        payload["timeline_markdown"] = export_timeline_markdown(timeline, capacity=allocator.capacity)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate contiguous memory allocation strategies.")
    parser.add_argument("--capacity", type=int, help="Total capacity in bytes (or provide it in --trace-in)")
    parser.add_argument(
        "--strategy",
        choices=["first-fit", "best-fit", "worst-fit"],
        default=None,
        help="Allocation strategy (default: first-fit)",
    )
    parser.add_argument(
        "--alignment",
        type=int,
        default=None,
        help="Round allocations up to this alignment quantum in bytes (default: 1)",
    )
    parser.add_argument(
        "--op",
        action="append",
        default=[],
        help="Operation: alloc:ID:SIZE, free:ID, compact",
    )
    parser.add_argument(
        "--trace-in",
        help="Load a JSON trace file containing operations and optional default capacity/strategy/alignment/timeline settings",
    )
    parser.add_argument(
        "--trace-out",
        help="Write a replayable JSON trace file with the resolved configuration and operations",
    )
    parser.add_argument(
        "--timeline",
        action="store_true",
        help="Include per-step timeline snapshots and a Markdown timeline export",
    )
    parser.add_argument(
        "--timeline-width",
        type=int,
        default=None,
        help="Rendered timeline width in characters (default: 32)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    trace = load_trace(args.trace_in) if args.trace_in else {}
    capacity = args.capacity if args.capacity is not None else trace.get("capacity")
    strategy = args.strategy if args.strategy is not None else trace.get("strategy", "first-fit")
    alignment = args.alignment if args.alignment is not None else trace.get("alignment", 1)
    include_timeline = args.timeline or bool(trace.get("timeline"))
    timeline_width = args.timeline_width if args.timeline_width is not None else trace.get("timeline_width", 32)
    operations = [*trace.get("operations", []), *args.op]

    if capacity is None:
        parser.error("--capacity is required unless provided by --trace-in")
    if timeline_width <= 0:
        parser.error("--timeline-width must be positive")
    if alignment <= 0:
        parser.error("--alignment must be positive")

    allocator = MemoryAllocator(capacity=capacity, strategy=strategy, alignment=alignment)
    result = run_operations(
        allocator,
        operations,
        include_timeline=include_timeline,
        timeline_width=timeline_width,
    )
    if args.trace_out:
        write_trace(
            args.trace_out,
            {
                "capacity": capacity,
                "strategy": strategy,
                "alignment": alignment,
                "timeline": include_timeline,
                "timeline_width": timeline_width,
                "operations": operations,
            },
        )
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
