from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable


@dataclass
class Segment:
    start: int
    size: int
    allocated: bool = False
    allocation_id: str | None = None

    @property
    def end(self) -> int:
        return self.start + self.size

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "size": self.size,
            "allocated": self.allocated,
            "allocation_id": self.allocation_id,
        }


VALID_STRATEGIES = {"first-fit", "best-fit", "worst-fit"}


class MemoryAllocator:
    def __init__(self, capacity: int, strategy: str = "first-fit"):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if strategy not in VALID_STRATEGIES:
            raise ValueError(f"unknown strategy: {strategy}")
        self.capacity = capacity
        self.strategy = strategy
        self.segments = [Segment(start=0, size=capacity, allocated=False)]

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

        index = self._pick_free_segment(size)
        if index is None:
            raise MemoryError(
                f"unable to allocate {size} bytes with strategy {self.strategy}; "
                f"largest_free_block={self.metrics()['largest_free_block']}"
            )

        segment = self.segments[index]
        allocated = Segment(
            start=segment.start,
            size=size,
            allocated=True,
            allocation_id=allocation_id,
        )
        remainder = segment.size - size

        new_segments = self.segments[:index] + [allocated]
        if remainder:
            new_segments.append(Segment(start=segment.start + size, size=remainder, allocated=False))
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
                })
            compacted.append(
                Segment(
                    start=next_start,
                    size=segment.size,
                    allocated=True,
                    allocation_id=segment.allocation_id,
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
        allocated_bytes = sum(segment.size for segment in self.segments if segment.allocated)
        free_bytes = sum(free_blocks)
        largest_free_block = max(free_blocks, default=0)
        return {
            "capacity": self.capacity,
            "strategy": self.strategy,
            "allocated_bytes": allocated_bytes,
            "free_bytes": free_bytes,
            "utilization": round(allocated_bytes / self.capacity, 4),
            "hole_count": len(free_blocks),
            "largest_free_block": largest_free_block,
            "external_fragmentation": free_bytes - largest_free_block,
        }


def parse_operation(raw: str) -> tuple[str, list[str]]:
    parts = raw.split(":")
    command = parts[0]
    return command, parts[1:]


def run_operations(allocator: MemoryAllocator, operations: Iterable[str]) -> dict:
    history = []
    for raw in operations:
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

    return {
        "history": history,
        "metrics": allocator.metrics(),
        "layout": allocator.layout(),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate contiguous memory allocation strategies.")
    parser.add_argument("--capacity", type=int, required=True, help="Total capacity in bytes")
    parser.add_argument(
        "--strategy",
        choices=["first-fit", "best-fit", "worst-fit"],
        default="first-fit",
        help="Allocation strategy",
    )
    parser.add_argument(
        "--op",
        action="append",
        default=[],
        help="Operation: alloc:ID:SIZE, free:ID, compact",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    allocator = MemoryAllocator(capacity=args.capacity, strategy=args.strategy)
    result = run_operations(allocator, args.op)
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
