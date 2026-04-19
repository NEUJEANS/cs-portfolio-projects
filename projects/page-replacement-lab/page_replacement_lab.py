from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from math import ceil
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field
from html import escape
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True, slots=True)
class WorkloadPreset:
    name: str
    description: str
    reference_string: tuple[int, ...]


BENCHMARKS_DIR = Path(__file__).resolve().parent / "benchmarks"


@dataclass(frozen=True, slots=True)
class TraceBenchmark:
    name: str
    description: str
    filename: str

    @property
    def path(self) -> Path:
        return BENCHMARKS_DIR / self.filename


@dataclass(frozen=True, slots=True)
class GalleryWorkload:
    name: str
    description: str
    reference_string: tuple[int, ...]
    reference_source: str
    source_kind: str


WORKLOAD_PRESETS: dict[str, WorkloadPreset] = {
    "classic-belady": WorkloadPreset(
        name="classic-belady",
        description="classic Belady anomaly reference string that makes FIFO regress from 3 to 4 frames",
        reference_string=(1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5),
    ),
    "looping-hotset": WorkloadPreset(
        name="looping-hotset",
        description="small hot working set with a short burst page that rewards recency-aware policies",
        reference_string=(1, 2, 3, 1, 2, 4, 1, 2, 3, 4, 1, 2),
    ),
    "scan-then-reuse": WorkloadPreset(
        name="scan-then-reuse",
        description="large sequential scan followed by a tighter reuse window to show cache pollution pressure",
        reference_string=(1, 2, 3, 4, 5, 6, 1, 2, 3, 1, 2, 7, 1, 2, 3),
    ),
    "mixed-locality-bursts": WorkloadPreset(
        name="mixed-locality-bursts",
        description="alternates hot-loop bursts with cold misses to mimic uneven interactive workloads",
        reference_string=(1, 2, 1, 2, 3, 4, 1, 2, 5, 1, 2, 6, 1, 2, 3, 4, 1, 2),
    ),
}

TRACE_BENCHMARKS: dict[str, TraceBenchmark] = {
    "compiler-phase-shift": TraceBenchmark(
        name="compiler-phase-shift",
        description="larger compiler-style trace with parser hot loops, a code-generation scan, and optimizer table bursts",
        filename="compiler-phase-shift.txt",
    ),
    "db-hotset-scan": TraceBenchmark(
        name="db-hotset-scan",
        description="dashboard-style hot pages interrupted by analytics scans and checkpoint bursts",
        filename="db-hotset-scan.txt",
    ),
    "streaming-burst-window": TraceBenchmark(
        name="streaming-burst-window",
        description="stream-processing sliding window with cold backfill bursts and shifting hotsets",
        filename="streaming-burst-window.txt",
    ),
}

AGE_COUNTER_BITS = 8
AGE_COUNTER_TOP_BIT = 1 << (AGE_COUNTER_BITS - 1)
WS_CLOCK_WINDOW_MULTIPLIER = 2
WS_CLOCK_WINDOW_FLOOR = 4

ALGORITHMS = ("fifo", "clock", "aging", "wsclock", "lru", "opt")


def wsclock_window_mode(wsclock_window: int | None) -> str:
    return "fixed" if wsclock_window is not None else "auto"


def describe_wsclock_window_setting(wsclock_window: int | None) -> str:
    if wsclock_window is None:
        return (
            "auto (max("
            f"{WS_CLOCK_WINDOW_FLOOR}, frames * {WS_CLOCK_WINDOW_MULTIPLIER})"
            ")"
        )
    unit = "reference" if wsclock_window == 1 else "references"
    return f"fixed {wsclock_window} {unit}"


def resolve_wsclock_window(frame_count: int, wsclock_window: int | None = None) -> int:
    if wsclock_window is not None:
        if wsclock_window <= 0:
            raise InputError("wsclock window must be positive")
        return wsclock_window
    return max(WS_CLOCK_WINDOW_FLOOR, frame_count * WS_CLOCK_WINDOW_MULTIPLIER)


def normalize_dirty_pages(dirty_pages: Iterable[int] | None) -> tuple[int, ...]:
    return tuple(sorted({int(page) for page in dirty_pages or ()}))


def describe_dirty_pages_setting(dirty_pages: Iterable[int] | None) -> str:
    values = normalize_dirty_pages(dirty_pages)
    if not values:
        return "none"
    return ", ".join(str(page) for page in values)


@dataclass(slots=True)
class SimulationStep:
    index: int
    page: int
    hit: bool
    frames: list[int]
    evicted: int | None
    writebacks_scheduled: list[int] = field(default_factory=list)


@dataclass(slots=True)
class SimulationResult:
    algorithm: str
    frame_count: int
    reference_string: list[int]
    page_faults: int
    hits: int
    hit_rate: float
    steps: list[SimulationStep]
    writebacks: int = 0

    def to_dict(self, *, include_steps: bool = True) -> dict:
        payload = {
            "algorithm": self.algorithm,
            "frame_count": self.frame_count,
            "reference_string": self.reference_string,
            "reference_length": len(self.reference_string),
            "page_faults": self.page_faults,
            "hits": self.hits,
            "hit_rate": round(self.hit_rate, 6),
            "writebacks": self.writebacks,
        }
        if include_steps:
            payload["steps"] = [asdict(step) for step in self.steps]
        return payload


@dataclass(frozen=True, slots=True)
class ParsedReference:
    reference_string: list[int]
    source: str


class InputError(ValueError):
    pass


def validate_reference(reference_string: Iterable[int], frame_count: int) -> list[int]:
    if frame_count <= 0:
        raise InputError("frame count must be positive")
    reference = list(reference_string)
    if not reference:
        raise InputError("reference string must contain at least one page")
    return reference


def simulate_fifo(reference_string: Iterable[int], frame_count: int) -> SimulationResult:
    reference = validate_reference(reference_string, frame_count)
    frames: list[int] = []
    resident: set[int] = set()
    order: deque[int] = deque()
    faults = 0
    steps: list[SimulationStep] = []

    for index, page in enumerate(reference):
        evicted: int | None = None
        hit = page in resident
        if not hit:
            faults += 1
            if len(frames) < frame_count:
                frames.append(page)
            else:
                evicted = order.popleft()
                resident.remove(evicted)
                slot = frames.index(evicted)
                frames[slot] = page
            resident.add(page)
            order.append(page)
        steps.append(
            SimulationStep(
                index=index,
                page=page,
                hit=hit,
                frames=list(frames),
                evicted=evicted,
            )
        )

    hits = len(reference) - faults
    return SimulationResult(
        algorithm="fifo",
        frame_count=frame_count,
        reference_string=reference,
        page_faults=faults,
        hits=hits,
        hit_rate=hits / len(reference),
        steps=steps,
    )


def simulate_clock(reference_string: Iterable[int], frame_count: int) -> SimulationResult:
    reference = validate_reference(reference_string, frame_count)
    frames: list[int | None] = [None] * frame_count
    reference_bits = [0] * frame_count
    resident_slots: dict[int, int] = {}
    hand = 0
    faults = 0
    steps: list[SimulationStep] = []

    for index, page in enumerate(reference):
        evicted: int | None = None
        hit = page in resident_slots
        if hit:
            reference_bits[resident_slots[page]] = 1
        else:
            faults += 1
            while True:
                current_page = frames[hand]
                if current_page is None:
                    slot = hand
                    break
                if reference_bits[hand] == 0:
                    slot = hand
                    evicted = current_page
                    resident_slots.pop(current_page, None)
                    break
                reference_bits[hand] = 0
                hand = (hand + 1) % frame_count

            frames[slot] = page
            reference_bits[slot] = 1
            resident_slots[page] = slot
            hand = (slot + 1) % frame_count

        steps.append(
            SimulationStep(
                index=index,
                page=page,
                hit=hit,
                frames=[value for value in frames if value is not None],
                evicted=evicted,
            )
        )

    hits = len(reference) - faults
    return SimulationResult(
        algorithm="clock",
        frame_count=frame_count,
        reference_string=reference,
        page_faults=faults,
        hits=hits,
        hit_rate=hits / len(reference),
        steps=steps,
    )


def simulate_aging(reference_string: Iterable[int], frame_count: int) -> SimulationResult:
    reference = validate_reference(reference_string, frame_count)
    frames: list[int | None] = [None] * frame_count
    age_counters = [0] * frame_count
    reference_bits = [0] * frame_count
    resident_slots: dict[int, int] = {}
    loaded_at: dict[int, int] = {}
    faults = 0
    steps: list[SimulationStep] = []

    for index, page in enumerate(reference):
        evicted: int | None = None
        hit = page in resident_slots
        if hit:
            slot = resident_slots[page]
            reference_bits[slot] = 1
        else:
            faults += 1
            empty_slot = next((slot for slot, current_page in enumerate(frames) if current_page is None), None)
            if empty_slot is not None:
                slot = empty_slot
            else:
                slot = min(
                    range(frame_count),
                    key=lambda candidate: (
                        age_counters[candidate],
                        loaded_at[frames[candidate]],
                        candidate,
                    ),
                )
                evicted = frames[slot]
                if evicted is not None:
                    resident_slots.pop(evicted, None)
                    loaded_at.pop(evicted, None)
            frames[slot] = page
            age_counters[slot] = 0
            reference_bits[slot] = 1
            resident_slots[page] = slot
            loaded_at[page] = index

        for slot, current_page in enumerate(frames):
            if current_page is None:
                continue
            age_counters[slot] = (age_counters[slot] >> 1) | (reference_bits[slot] * AGE_COUNTER_TOP_BIT)
            reference_bits[slot] = 0

        steps.append(
            SimulationStep(
                index=index,
                page=page,
                hit=hit,
                frames=[value for value in frames if value is not None],
                evicted=evicted,
            )
        )

    hits = len(reference) - faults
    return SimulationResult(
        algorithm="aging",
        frame_count=frame_count,
        reference_string=reference,
        page_faults=faults,
        hits=hits,
        hit_rate=hits / len(reference),
        steps=steps,
    )


def simulate_wsclock(
    reference_string: Iterable[int],
    frame_count: int,
    wsclock_window: int | None = None,
    dirty_pages: Iterable[int] | None = None,
) -> SimulationResult:
    reference = validate_reference(reference_string, frame_count)
    dirty_page_set = set(normalize_dirty_pages(dirty_pages))
    frames: list[int | None] = [None] * frame_count
    reference_bits = [0] * frame_count
    dirty_bits = [0] * frame_count
    last_used = [-1] * frame_count
    resident_slots: dict[int, int] = {}
    hand = 0
    faults = 0
    writebacks = 0
    steps: list[SimulationStep] = []
    window = resolve_wsclock_window(frame_count, wsclock_window)

    for index, page in enumerate(reference):
        evicted: int | None = None
        writebacks_scheduled: list[int] = []
        hit = page in resident_slots
        is_dirty_access = page in dirty_page_set
        if hit:
            slot = resident_slots[page]
            reference_bits[slot] = 1
            last_used[slot] = index
            if is_dirty_access:
                dirty_bits[slot] = 1
        else:
            faults += 1
            slot: int | None = None
            fallback_slot: int | None = None
            cleaned_old_slot: int | None = None
            scanned = 0
            while scanned < frame_count:
                current_page = frames[hand]
                if current_page is None:
                    slot = hand
                    break
                if reference_bits[hand] == 1:
                    reference_bits[hand] = 0
                else:
                    age = index - last_used[hand]
                    if age > window:
                        if dirty_bits[hand] == 0:
                            slot = hand
                            break
                        dirty_bits[hand] = 0
                        writebacks += 1
                        writebacks_scheduled.append(current_page)
                        if cleaned_old_slot is None or (last_used[hand], hand) < (
                            last_used[cleaned_old_slot],
                            cleaned_old_slot,
                        ):
                            cleaned_old_slot = hand
                    elif fallback_slot is None or (last_used[hand], hand) < (
                        last_used[fallback_slot],
                        fallback_slot,
                    ):
                        fallback_slot = hand
                hand = (hand + 1) % frame_count
                scanned += 1

            if slot is None:
                if cleaned_old_slot is not None:
                    slot = cleaned_old_slot
                else:
                    if fallback_slot is None:
                        fallback_slot = min(range(frame_count), key=lambda candidate: (last_used[candidate], candidate))
                    slot = fallback_slot

            evicted = frames[slot]
            if evicted is not None:
                resident_slots.pop(evicted, None)

            frames[slot] = page
            reference_bits[slot] = 1
            dirty_bits[slot] = 1 if is_dirty_access else 0
            last_used[slot] = index
            resident_slots[page] = slot
            hand = (slot + 1) % frame_count

        steps.append(
            SimulationStep(
                index=index,
                page=page,
                hit=hit,
                frames=[value for value in frames if value is not None],
                evicted=evicted,
                writebacks_scheduled=list(writebacks_scheduled),
            )
        )

    hits = len(reference) - faults
    return SimulationResult(
        algorithm="wsclock",
        frame_count=frame_count,
        reference_string=reference,
        page_faults=faults,
        hits=hits,
        hit_rate=hits / len(reference),
        steps=steps,
        writebacks=writebacks,
    )


def simulate_lru(reference_string: Iterable[int], frame_count: int) -> SimulationResult:
    reference = validate_reference(reference_string, frame_count)
    frames: list[int] = []
    resident: set[int] = set()
    last_used: dict[int, int] = {}
    loaded_at: dict[int, int] = {}
    faults = 0
    steps: list[SimulationStep] = []

    for index, page in enumerate(reference):
        evicted: int | None = None
        hit = page in resident
        if hit:
            last_used[page] = index
        else:
            faults += 1
            if len(frames) < frame_count:
                frames.append(page)
            else:
                evicted = min(
                    frames,
                    key=lambda candidate: (
                        last_used[candidate],
                        loaded_at[candidate],
                        frames.index(candidate),
                    ),
                )
                resident.remove(evicted)
                last_used.pop(evicted, None)
                loaded_at.pop(evicted, None)
                slot = frames.index(evicted)
                frames[slot] = page
            resident.add(page)
            loaded_at[page] = index
            last_used[page] = index
        steps.append(
            SimulationStep(
                index=index,
                page=page,
                hit=hit,
                frames=list(frames),
                evicted=evicted,
            )
        )

    hits = len(reference) - faults
    return SimulationResult(
        algorithm="lru",
        frame_count=frame_count,
        reference_string=reference,
        page_faults=faults,
        hits=hits,
        hit_rate=hits / len(reference),
        steps=steps,
    )


def simulate_opt(reference_string: Iterable[int], frame_count: int) -> SimulationResult:
    reference = validate_reference(reference_string, frame_count)
    future_positions: dict[int, deque[int]] = defaultdict(deque)
    for index, page in enumerate(reference):
        future_positions[page].append(index)

    frames: list[int] = []
    resident: set[int] = set()
    loaded_at: dict[int, int] = {}
    faults = 0
    steps: list[SimulationStep] = []

    for index, page in enumerate(reference):
        future_positions[page].popleft()
        evicted: int | None = None
        hit = page in resident
        if not hit:
            faults += 1
            if len(frames) < frame_count:
                frames.append(page)
            else:
                evicted = max(
                    frames,
                    key=lambda candidate: (
                        future_positions[candidate][0]
                        if future_positions[candidate]
                        else float("inf"),
                        -loaded_at[candidate],
                        -frames.index(candidate),
                    ),
                )
                resident.remove(evicted)
                loaded_at.pop(evicted, None)
                slot = frames.index(evicted)
                frames[slot] = page
            resident.add(page)
            loaded_at[page] = index
        steps.append(
            SimulationStep(
                index=index,
                page=page,
                hit=hit,
                frames=list(frames),
                evicted=evicted,
            )
        )

    hits = len(reference) - faults
    return SimulationResult(
        algorithm="opt",
        frame_count=frame_count,
        reference_string=reference,
        page_faults=faults,
        hits=hits,
        hit_rate=hits / len(reference),
        steps=steps,
    )


SIMULATORS = {
    "fifo": simulate_fifo,
    "clock": simulate_clock,
    "aging": simulate_aging,
    "wsclock": simulate_wsclock,
    "lru": simulate_lru,
    "opt": simulate_opt,
}


def simulate(
    algorithm: str,
    reference_string: Iterable[int],
    frame_count: int,
    *,
    wsclock_window: int | None = None,
    dirty_pages: Iterable[int] | None = None,
) -> SimulationResult:
    if algorithm not in SIMULATORS:
        raise InputError(f"unsupported algorithm: {algorithm}")
    if algorithm == "wsclock":
        return simulate_wsclock(
            reference_string,
            frame_count,
            wsclock_window=wsclock_window,
            dirty_pages=dirty_pages,
        )
    return SIMULATORS[algorithm](reference_string, frame_count)


def compare_algorithms(
    reference_string: Iterable[int],
    frame_count: int,
    *,
    wsclock_window: int | None = None,
    dirty_pages: Iterable[int] | None = None,
) -> list[SimulationResult]:
    reference = validate_reference(reference_string, frame_count)
    return [
        simulate(
            name,
            reference,
            frame_count,
            wsclock_window=wsclock_window,
            dirty_pages=dirty_pages,
        )
        for name in ALGORITHMS
    ]


def study_frame_counts(
    reference_string: Iterable[int],
    min_frames: int,
    max_frames: int,
    *,
    wsclock_window: int | None = None,
    dirty_pages: Iterable[int] | None = None,
) -> dict:
    reference = list(reference_string)
    if min_frames <= 0 or max_frames <= 0:
        raise InputError("frame counts must be positive")
    if min_frames > max_frames:
        raise InputError("min-frames must be less than or equal to max-frames")
    if not reference:
        raise InputError("reference string must contain at least one page")

    resolved_dirty_pages = list(normalize_dirty_pages(dirty_pages))
    frame_results: list[dict] = []
    previous_faults: dict[str, int | None] = {algorithm: None for algorithm in ALGORITHMS}
    monotonicity_violations: list[dict] = []

    for frame_count in range(min_frames, max_frames + 1):
        run = {
            algorithm: simulate(
                algorithm,
                reference,
                frame_count,
                wsclock_window=wsclock_window,
                dirty_pages=resolved_dirty_pages,
            )
            for algorithm in ALGORITHMS
        }
        frame_results.append(
            {
                "frame_count": frame_count,
                "wsclock_window": resolve_wsclock_window(frame_count, wsclock_window),
                "algorithms": {
                    name: {
                        "page_faults": result.page_faults,
                        "hits": result.hits,
                        "hit_rate": round(result.hit_rate, 6),
                        "writebacks": result.writebacks,
                    }
                    for name, result in run.items()
                },
            }
        )
        for algorithm, result in run.items():
            previous = previous_faults[algorithm]
            if previous is not None and result.page_faults > previous:
                monotonicity_violations.append(
                    {
                        "algorithm": algorithm,
                        "from_frames": frame_count - 1,
                        "to_frames": frame_count,
                        "faults_before": previous,
                        "faults_after": result.page_faults,
                        "fault_delta": result.page_faults - previous,
                    }
                )
            previous_faults[algorithm] = result.page_faults

    fifo_anomalies = [
        violation
        for violation in monotonicity_violations
        if violation["algorithm"] == "fifo"
    ]

    return {
        "reference_string": reference,
        "frame_results": frame_results,
        "fifo_belady_anomalies": fifo_anomalies,
        "monotonicity_violations": monotonicity_violations,
        "wsclock_window_mode": wsclock_window_mode(wsclock_window),
        "wsclock_window_override": wsclock_window,
        "wsclock_window_description": describe_wsclock_window_setting(wsclock_window),
        "dirty_pages": resolved_dirty_pages,
        "dirty_page_count": len(resolved_dirty_pages),
        "dirty_page_description": describe_dirty_pages_setting(resolved_dirty_pages),
    }


def tune_wsclock_windows(
    reference_string: Iterable[int],
    frame_count: int,
    *,
    min_window: int = 1,
    max_window: int | None = None,
    dirty_pages: Iterable[int] | None = None,
    writeback_penalty: float = 1.0,
) -> dict:
    reference = validate_reference(reference_string, frame_count)
    if min_window <= 0:
        raise InputError("min-window must be positive")
    auto_window = resolve_wsclock_window(frame_count, None)
    resolved_max_window = max_window if max_window is not None else max(auto_window, frame_count * 3)
    if resolved_max_window <= 0:
        raise InputError("max-window must be positive")
    if min_window > resolved_max_window:
        raise InputError("min-window must be less than or equal to max-window")
    if writeback_penalty < 0:
        raise InputError("writeback-penalty must be non-negative")

    resolved_dirty_pages = list(normalize_dirty_pages(dirty_pages))
    evaluations: list[dict] = []
    for window in range(min_window, resolved_max_window + 1):
        result = simulate_wsclock(
            reference,
            frame_count,
            wsclock_window=window,
            dirty_pages=resolved_dirty_pages,
        )
        weighted_score = result.page_faults + (result.writebacks * writeback_penalty)
        evaluations.append(
            {
                "window": window,
                "page_faults": result.page_faults,
                "hits": result.hits,
                "hit_rate": round(result.hit_rate, 6),
                "writebacks": result.writebacks,
                "fault_rate": round(result.page_faults / len(reference), 6),
                "weighted_score": round(weighted_score, 6),
            }
        )

    recommended = min(
        evaluations,
        key=lambda entry: (
            entry["weighted_score"],
            entry["page_faults"],
            entry["writebacks"],
            entry["window"],
        ),
    )
    best_faults = min(entry["page_faults"] for entry in evaluations)
    best_writebacks = min(entry["writebacks"] for entry in evaluations)
    pareto_frontier = [
        candidate
        for candidate in evaluations
        if not any(
            (
                other["page_faults"] <= candidate["page_faults"]
                and other["writebacks"] <= candidate["writebacks"]
                and (
                    other["page_faults"] < candidate["page_faults"]
                    or other["writebacks"] < candidate["writebacks"]
                )
            )
            for other in evaluations
        )
    ]
    auto_window_result = next(
        (entry for entry in evaluations if entry["window"] == auto_window),
        None,
    )

    return {
        "frame_count": frame_count,
        "reference_string": reference,
        "min_window": min_window,
        "max_window": resolved_max_window,
        "candidate_window_count": len(evaluations),
        "auto_window": auto_window,
        "auto_window_in_range": auto_window_result is not None,
        "auto_window_result": auto_window_result,
        "writeback_penalty": round(writeback_penalty, 6),
        "dirty_pages": resolved_dirty_pages,
        "dirty_page_count": len(resolved_dirty_pages),
        "dirty_page_description": describe_dirty_pages_setting(resolved_dirty_pages),
        "evaluations": evaluations,
        "recommended_window": recommended["window"],
        "recommended": recommended,
        "best_fault_windows": [
            entry["window"] for entry in evaluations if entry["page_faults"] == best_faults
        ],
        "best_writeback_windows": [
            entry["window"] for entry in evaluations if entry["writebacks"] == best_writebacks
        ],
        "pareto_frontier": pareto_frontier,
    }


def list_workload_presets() -> list[WorkloadPreset]:
    return list(WORKLOAD_PRESETS.values())


def list_trace_benchmarks() -> list[TraceBenchmark]:
    return list(TRACE_BENCHMARKS.values())


def resolve_preset(name: str) -> WorkloadPreset:
    try:
        return WORKLOAD_PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(WORKLOAD_PRESETS))
        raise InputError(f"unknown preset: {name}. choose from: {available}") from exc


def resolve_trace_benchmark(name: str) -> TraceBenchmark:
    try:
        return TRACE_BENCHMARKS[name]
    except KeyError as exc:
        available = ", ".join(sorted(TRACE_BENCHMARKS))
        raise InputError(f"unknown benchmark: {name}. choose from: {available}") from exc


def parse_reference_text(content: str, *, source_label: str) -> list[int]:
    stripped_lines = [line.split("#", 1)[0].strip() for line in content.splitlines()]
    cleaned = "\n".join(line for line in stripped_lines if line).strip()
    if not cleaned:
        raise InputError(f"{source_label} is empty")
    if cleaned.startswith("["):
        payload = json.loads(cleaned)
        if not isinstance(payload, list):
            raise InputError(f"{source_label} must contain a JSON list")
        return [int(value) for value in payload]
    return [int(token) for token in cleaned.replace(",", " ").split()]


def load_trace_benchmark_reference(benchmark: TraceBenchmark) -> list[int]:
    return parse_reference_text(
        benchmark.path.read_text(encoding="utf-8"),
        source_label=f"benchmark {benchmark.name}",
    )


def workload_from_preset(preset: WorkloadPreset) -> GalleryWorkload:
    return GalleryWorkload(
        name=preset.name,
        description=preset.description,
        reference_string=preset.reference_string,
        reference_source=f"preset:{preset.name}",
        source_kind="preset",
    )


def workload_from_benchmark(benchmark: TraceBenchmark) -> GalleryWorkload:
    return GalleryWorkload(
        name=benchmark.name,
        description=benchmark.description,
        reference_string=tuple(load_trace_benchmark_reference(benchmark)),
        reference_source=f"benchmark:{benchmark.name}",
        source_kind="benchmark",
    )


def describe_pages_file(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def workload_from_pages_file(path: Path) -> GalleryWorkload:
    display_path = describe_pages_file(path)
    return GalleryWorkload(
        name=path.stem,
        description=f"custom imported trace from {display_path}",
        reference_string=tuple(
            parse_reference_text(
                path.read_text(encoding="utf-8"),
                source_label=f"pages file {display_path}",
            )
        ),
        reference_source=f"pages-file:{display_path}",
        source_kind="custom",
    )


def parse_reference_args(
    pages: list[str],
    pages_file: str | None,
    preset: str | None,
    benchmark: str | None = None,
) -> ParsedReference:
    if (preset or benchmark) and (pages or pages_file):
        raise InputError(
            "use exactly one of --preset, --benchmark, or explicit --page/--pages-file input"
        )
    if preset and benchmark:
        raise InputError("use either --preset or --benchmark, not both")

    if preset:
        selected = resolve_preset(preset)
        return ParsedReference(
            reference_string=list(selected.reference_string),
            source=f"preset:{selected.name}",
        )

    if benchmark:
        selected = resolve_trace_benchmark(benchmark)
        return ParsedReference(
            reference_string=load_trace_benchmark_reference(selected),
            source=f"benchmark:{selected.name}",
        )

    raw_pages = [int(token) for token in pages]

    if pages_file:
        raw_pages.extend(
            parse_reference_text(
                Path(pages_file).read_text(encoding="utf-8"),
                source_label="pages file",
            )
        )

    if not raw_pages:
        raise InputError(
            "provide at least one --page, a --pages-file, a --preset, or a --benchmark"
        )
    return ParsedReference(reference_string=raw_pages, source="custom")


def parse_dirty_page_args(
    dirty_pages: list[str] | None,
    dirty_pages_file: str | None,
) -> tuple[int, ...]:
    resolved = [int(token) for token in (dirty_pages or [])]
    if dirty_pages_file:
        resolved.extend(
            parse_reference_text(
                Path(dirty_pages_file).read_text(encoding="utf-8"),
                source_label="dirty pages file",
            )
        )
    return normalize_dirty_pages(resolved)


def add_wsclock_window_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--wsclock-window",
        type=int,
        help=(
            "override WSClock tau / working-set age window in references; "
            "default is auto max(4, frames * 2)"
        ),
    )


def add_dirty_page_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dirty-page",
        action="append",
        default=[],
        help=(
            "repeat to treat a page number as write-heavy for WSClock; "
            "every access to that page sets the dirty bit"
        ),
    )
    parser.add_argument(
        "--dirty-pages-file",
        help=(
            "optional JSON/whitespace page list to mark write-heavy for WSClock; "
            "applies globally to the selected workload(s)"
        ),
    )


def add_reference_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--page", action="append", default=[])
    parser.add_argument("--pages-file")
    parser.add_argument(
        "--preset",
        choices=tuple(WORKLOAD_PRESETS),
        help="use a built-in workload preset instead of explicit pages",
    )
    parser.add_argument(
        "--benchmark",
        choices=tuple(TRACE_BENCHMARKS),
        help="use a larger built-in trace benchmark instead of explicit pages",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulate classic page replacement algorithms for OS/virtual-memory workloads.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate_parser = subparsers.add_parser("simulate", help="simulate one algorithm")
    simulate_parser.add_argument("algorithm", choices=ALGORITHMS)
    simulate_parser.add_argument("--frames", type=int, required=True)
    add_reference_arguments(simulate_parser)
    add_wsclock_window_argument(simulate_parser)
    add_dirty_page_arguments(simulate_parser)
    simulate_parser.add_argument("--json", action="store_true")
    simulate_parser.add_argument(
        "--show-steps",
        action="store_true",
        help="print the full step-by-step trace in text mode",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="compare all bundled policies on one workload",
    )
    compare_parser.add_argument("--frames", type=int, required=True)
    add_reference_arguments(compare_parser)
    add_wsclock_window_argument(compare_parser)
    add_dirty_page_arguments(compare_parser)
    compare_parser.add_argument("--json", action="store_true")

    study_parser = subparsers.add_parser(
        "study",
        help="compare page faults across a frame-count range and flag fault regressions",
    )
    study_parser.add_argument("--min-frames", type=int, required=True)
    study_parser.add_argument("--max-frames", type=int, required=True)
    add_reference_arguments(study_parser)
    add_wsclock_window_argument(study_parser)
    add_dirty_page_arguments(study_parser)
    study_parser.add_argument("--json", action="store_true")
    study_parser.add_argument("--markdown-out", type=Path, help="write a Markdown study report")
    study_parser.add_argument("--svg-out", type=Path, help="write a self-contained SVG study chart")
    study_parser.add_argument("--csv-out", type=Path, help="write a chart-ready CSV study export")

    gallery_parser = subparsers.add_parser(
        "gallery",
        help="generate an HTML gallery plus companion study artifacts for preset workloads or larger built-in trace benchmarks",
    )
    gallery_parser.add_argument("--min-frames", type=int, required=True)
    gallery_parser.add_argument("--max-frames", type=int, required=True)
    add_wsclock_window_argument(gallery_parser)
    add_dirty_page_arguments(gallery_parser)
    gallery_parser.add_argument(
        "--preset",
        dest="gallery_presets",
        action="append",
        choices=tuple(WORKLOAD_PRESETS),
        help="repeat to include specific built-in presets",
    )
    gallery_parser.add_argument(
        "--benchmark",
        dest="gallery_benchmarks",
        action="append",
        choices=tuple(TRACE_BENCHMARKS),
        help="repeat to include specific larger built-in trace benchmarks",
    )
    gallery_parser.add_argument(
        "--include-benchmarks",
        action="store_true",
        help="add all built-in trace benchmarks to the default preset gallery",
    )
    gallery_parser.add_argument(
        "--pages-file",
        dest="gallery_pages_files",
        action="append",
        metavar="PATH",
        type=Path,
        help="repeat to include imported custom trace files with per-workload drill-down cards",
    )
    gallery_parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="directory where per-workload Markdown/SVG/CSV/JSON study artifacts will be written",
    )
    gallery_parser.add_argument(
        "--html-out",
        type=Path,
        help="optional explicit HTML path (default: <artifact-dir>/index.html)",
    )
    gallery_parser.add_argument("--json", action="store_true")

    aggregate_parser = subparsers.add_parser(
        "aggregate",
        help="build a cross-workload aggregate dashboard with normalized comparison charts",
    )
    aggregate_parser.add_argument("--min-frames", type=int, required=True)
    aggregate_parser.add_argument("--max-frames", type=int, required=True)
    add_wsclock_window_argument(aggregate_parser)
    add_dirty_page_arguments(aggregate_parser)
    aggregate_parser.add_argument(
        "--preset",
        dest="aggregate_presets",
        action="append",
        choices=tuple(WORKLOAD_PRESETS),
        help="repeat to include specific built-in presets",
    )
    aggregate_parser.add_argument(
        "--benchmark",
        dest="aggregate_benchmarks",
        action="append",
        choices=tuple(TRACE_BENCHMARKS),
        help="repeat to include specific larger built-in trace benchmarks",
    )
    aggregate_parser.add_argument(
        "--include-benchmarks",
        action="store_true",
        help="add all built-in trace benchmarks to the default preset aggregate run",
    )
    aggregate_parser.add_argument(
        "--pages-file",
        dest="aggregate_pages_files",
        action="append",
        metavar="PATH",
        type=Path,
        help="repeat to include imported custom trace files in the aggregate dashboard",
    )
    aggregate_parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="directory where aggregate CSV / SVG / JSON / HTML artifacts will be written",
    )
    aggregate_parser.add_argument(
        "--html-out",
        type=Path,
        help="optional explicit HTML path (default: <artifact-dir>/index.html)",
    )
    aggregate_parser.add_argument("--json", action="store_true")

    preset_parser = subparsers.add_parser(
        "list-presets",
        help="list built-in workload presets for repeatable demos",
    )
    preset_parser.add_argument("--json", action="store_true")

    benchmark_parser = subparsers.add_parser(
        "list-benchmarks",
        help="list larger built-in trace benchmarks for heavier portfolio demos",
    )
    benchmark_parser.add_argument("--json", action="store_true")

    trace_summary_parser = subparsers.add_parser(
        "trace-summary",
        help="summarize reuse-distance and phase-shift hints for one workload",
    )
    add_reference_arguments(trace_summary_parser)
    trace_summary_parser.add_argument(
        "--window-size",
        type=int,
        default=8,
        help="window size for working-set and phase-hint summaries",
    )
    trace_summary_parser.add_argument(
        "--phase-threshold",
        type=float,
        default=0.45,
        help="flag a phase-boundary hint when consecutive windows overlap at or below this Jaccard similarity",
    )
    trace_summary_parser.add_argument("--markdown-out", type=Path, help="write a Markdown trace-summary report")
    trace_summary_parser.add_argument("--svg-out", type=Path, help="write a slide-ready SVG trace-summary card")
    trace_summary_parser.add_argument("--html-out", type=Path, help="write a browsable HTML trace-summary card")
    trace_summary_parser.add_argument("--json", action="store_true")

    tune_wsclock_parser = subparsers.add_parser(
        "tune-wsclock",
        help="sweep WSClock tau windows and recommend a dirty-page-aware setting",
    )
    tune_wsclock_parser.add_argument("--frames", type=int, required=True)
    add_reference_arguments(tune_wsclock_parser)
    add_dirty_page_arguments(tune_wsclock_parser)
    tune_wsclock_parser.add_argument(
        "--min-window",
        type=int,
        default=1,
        help="smallest tau / working-set window to evaluate",
    )
    tune_wsclock_parser.add_argument(
        "--max-window",
        type=int,
        help="largest tau / working-set window to evaluate (default: max(auto, frames * 3))",
    )
    tune_wsclock_parser.add_argument(
        "--writeback-penalty",
        type=float,
        default=1.0,
        help="weight applied to each writeback in the recommendation score",
    )
    tune_wsclock_parser.add_argument("--markdown-out", type=Path, help="write a Markdown tuning report")
    tune_wsclock_parser.add_argument("--csv-out", type=Path, help="write a CSV tuning sweep export")
    tune_wsclock_parser.add_argument("--json", action="store_true")

    trace_compare_parser = subparsers.add_parser(
        "trace-compare",
        help="compare exactly two imported trace files side by side",
    )
    trace_compare_parser.add_argument("--min-frames", type=int, required=True)
    trace_compare_parser.add_argument("--max-frames", type=int, required=True)
    add_wsclock_window_argument(trace_compare_parser)
    add_dirty_page_arguments(trace_compare_parser)
    trace_compare_parser.add_argument(
        "--pages-file",
        dest="trace_compare_pages_files",
        action="append",
        metavar="PATH",
        type=Path,
        help="repeat exactly twice to compare two imported trace files side by side",
    )
    trace_compare_parser.add_argument(
        "--window-size",
        type=int,
        default=8,
        help="window size for per-trace working-set and phase-hint summaries",
    )
    trace_compare_parser.add_argument(
        "--phase-threshold",
        type=float,
        default=0.45,
        help="flag a phase-boundary hint when consecutive windows overlap at or below this Jaccard similarity",
    )
    trace_compare_parser.add_argument(
        "--artifact-dir",
        type=Path,
        required=True,
        help="directory where Markdown / SVG / CSV / JSON / HTML comparison artifacts will be written",
    )
    trace_compare_parser.add_argument(
        "--html-out",
        type=Path,
        help="optional explicit HTML path (default: <artifact-dir>/<left>-vs-<right>-trace-compare.html)",
    )
    trace_compare_parser.add_argument("--json", action="store_true")

    return parser


def format_reference_source(reference_source: str) -> str:
    if reference_source.startswith("preset:"):
        preset = resolve_preset(reference_source.split(":", 1)[1])
        return f"source: preset {preset.name} — {preset.description}"
    if reference_source.startswith("benchmark:"):
        benchmark = resolve_trace_benchmark(reference_source.split(":", 1)[1])
        return f"source: benchmark {benchmark.name} — {benchmark.description}"
    if reference_source.startswith("pages-file:"):
        display_path = reference_source.split(":", 1)[1]
        workload_name = Path(display_path).stem or display_path
        return f"source: imported trace {workload_name} — {display_path}"
    return "source: custom"


def format_simulation_text(
    result: SimulationResult,
    *,
    show_steps: bool = False,
    reference_source: str = "custom",
    wsclock_window: int | None = None,
    dirty_pages: Iterable[int] | None = None,
) -> str:
    lines = [
        f"algorithm: {result.algorithm}",
        f"frames: {result.frame_count}",
        format_reference_source(reference_source),
        "reference: " + " ".join(str(page) for page in result.reference_string),
    ]
    if result.algorithm == "wsclock":
        lines.append(
            f"wsclock window: {describe_wsclock_window_setting(wsclock_window)} "
            f"(effective {resolve_wsclock_window(result.frame_count, wsclock_window)})"
        )
        lines.append(f"dirty pages: {describe_dirty_pages_setting(dirty_pages)}")
    if show_steps:
        lines.append("steps:")
        for step in result.steps:
            state = "HIT" if step.hit else "MISS"
            evicted = f" evicted={step.evicted}" if step.evicted is not None else ""
            writeback = (
                f" writebacks={step.writebacks_scheduled}"
                if step.writebacks_scheduled
                else ""
            )
            lines.append(
                f"  {step.index:>2}: page={step.page:<3} {state:<4} frames={step.frames}{evicted}{writeback}"
            )
    summary_line = f"summary: faults={result.page_faults} hits={result.hits} hit_rate={result.hit_rate:.2%}"
    if result.algorithm == "wsclock":
        summary_line += f" writebacks={result.writebacks}"
    lines.append(summary_line)
    return "\n".join(lines)


def format_compare_text(
    results: list[SimulationResult],
    frame_count: int,
    reference: list[int],
    *,
    reference_source: str = "custom",
    wsclock_window: int | None = None,
    dirty_pages: Iterable[int] | None = None,
) -> str:
    algorithm_width = max(len("algorithm"), *(len(result.algorithm) for result in results))
    lines = [
        f"frames: {frame_count}",
        format_reference_source(reference_source),
        "reference: " + " ".join(str(page) for page in reference),
        f"wsclock window: {describe_wsclock_window_setting(wsclock_window)} (effective {resolve_wsclock_window(frame_count, wsclock_window)})",
        f"dirty pages: {describe_dirty_pages_setting(dirty_pages)}",
        f"{'algorithm':<{algorithm_width}}  faults  hits  writebacks  hit-rate",
    ]
    for result in results:
        lines.append(
            f"{result.algorithm:<{algorithm_width}}  {result.page_faults:<6}  {result.hits:<4}  {result.writebacks:<10}  {result.hit_rate:>7.2%}"
        )
    best_faults = min(result.page_faults for result in results)
    winners = ", ".join(
        result.algorithm for result in results if result.page_faults == best_faults
    )
    wsclock_writebacks = next(result.writebacks for result in results if result.algorithm == "wsclock")
    lines.append(f"best faults: {best_faults} ({winners})")
    lines.append(f"wsclock writebacks: {wsclock_writebacks}")
    return "\n".join(lines)


def format_study_text(payload: dict, *, reference_source: str = "custom") -> str:
    algorithms = list(ALGORITHMS)
    column_width = max(6, *(len(name) for name in algorithms))
    lines = [
        format_reference_source(reference_source),
        "reference: " + " ".join(str(page) for page in payload["reference_string"]),
        f"wsclock window: {payload['wsclock_window_description']}",
        f"dirty pages: {payload['dirty_page_description']}",
        " ".join(
            [f"{'frames':<{column_width}}"]
            + [f"{algorithm:<{column_width}}" for algorithm in algorithms]
        ),
    ]
    for row in payload["frame_results"]:
        lines.append(
            " ".join(
                [f"{row['frame_count']:<{column_width}}"]
                + [
                    f"{row['algorithms'][algorithm]['page_faults']:<{column_width}}"
                    for algorithm in algorithms
                ]
            )
        )
    anomalies = payload["fifo_belady_anomalies"]
    if anomalies:
        lines.append("fifo Belady anomalies:")
        for anomaly in anomalies:
            lines.append(
                f"  frames {anomaly['from_frames']} -> {anomaly['to_frames']}: "
                f"{anomaly['faults_before']} -> {anomaly['faults_after']} "
                f"(+{anomaly['fault_delta']})"
            )
    else:
        lines.append("fifo Belady anomalies: none detected in this frame range")

    non_fifo_violations = [
        violation
        for violation in payload["monotonicity_violations"]
        if violation["algorithm"] != "fifo"
    ]
    if non_fifo_violations:
        lines.append("other fault regressions:")
        for violation in non_fifo_violations:
            lines.append(
                f"  {violation['algorithm']}: frames {violation['from_frames']} -> {violation['to_frames']} "
                f"{violation['faults_before']} -> {violation['faults_after']} (+{violation['fault_delta']})"
            )
    else:
        lines.append("other fault regressions: none detected in this frame range")
    lines.append(
        "wsclock writebacks by frame: "
        + ", ".join(
            f"{row['frame_count']}→{row['algorithms']['wsclock']['writebacks']}"
            for row in payload["frame_results"]
        )
    )
    return "\n".join(lines)


def build_study_rows(payload: dict) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for row in payload["frame_results"]:
        best_faults = min(
            row["algorithms"][algorithm]["page_faults"] for algorithm in ALGORITHMS
        )
        winners = "/".join(
            algorithm
            for algorithm in ALGORITHMS
            if row["algorithms"][algorithm]["page_faults"] == best_faults
        )
        summary_row: dict[str, str | int] = {
            "frame_count": row["frame_count"],
            "wsclock_window": row["wsclock_window"],
            "wsclock_writebacks": row["algorithms"]["wsclock"]["writebacks"],
            "best_algorithms": winners,
        }
        for algorithm in ALGORITHMS:
            summary_row[f"{algorithm}_faults"] = row["algorithms"][algorithm]["page_faults"]
        rows.append(summary_row)
    return rows


def summarize_fault_averages(payload: dict) -> dict[str, float]:
    frame_results = payload["frame_results"]
    return {
        algorithm: sum(
            row["algorithms"][algorithm]["page_faults"] for row in frame_results
        )
        / len(frame_results)
        for algorithm in ALGORITHMS
    }


def summarize_wsclock_writeback_average(payload: dict) -> float:
    frame_results = payload["frame_results"]
    return sum(row["algorithms"]["wsclock"]["writebacks"] for row in frame_results) / len(frame_results)


def describe_reference_label(reference_source: str) -> str:
    if reference_source.startswith("preset:"):
        preset = resolve_preset(reference_source.split(":", 1)[1])
        return f"preset {preset.name} — {preset.description}"
    if reference_source.startswith("benchmark:"):
        benchmark = resolve_trace_benchmark(reference_source.split(":", 1)[1])
        return f"benchmark {benchmark.name} — {benchmark.description}"
    if reference_source.startswith("pages-file:"):
        display_path = reference_source.split(":", 1)[1]
        workload_name = Path(display_path).stem or display_path
        return f"imported trace {workload_name} — {display_path}"
    return "custom workload"


def make_safe_identifier(value: str) -> str:
    safe = "".join(character if character.isalnum() else "-" for character in value.lower())
    safe = safe.strip("-")
    return safe or "page-replacement"


def ensure_output_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text_output(path: Path, content: str) -> None:
    ensure_output_parent(path)
    path.write_text(content, encoding="utf-8")


def write_study_csv(path: Path, payload: dict, *, reference_source: str = "custom") -> None:
    rows = build_study_rows(payload)
    ensure_output_parent(path)
    fault_fieldnames = [f"{algorithm}_faults" for algorithm in ALGORITHMS]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "frames",
                *fault_fieldnames,
                "wsclock_window",
                "wsclock_writebacks",
                "best_algorithms",
                "reference_source",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            payload_row = {
                "frames": row["frame_count"],
                "wsclock_window": row["wsclock_window"],
                "wsclock_writebacks": row["wsclock_writebacks"],
                "best_algorithms": row["best_algorithms"],
                "reference_source": reference_source,
            }
            for fieldname in fault_fieldnames:
                payload_row[fieldname] = row[fieldname]
            writer.writerow(payload_row)


def write_study_json(path: Path, payload: dict) -> None:
    write_text_output(path, json.dumps(payload, indent=2) + "\n")


def write_wsclock_tuning_csv(path: Path, payload: dict, *, reference_source: str = "custom") -> None:
    ensure_output_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "window",
                "page_faults",
                "hits",
                "hit_rate",
                "fault_rate",
                "writebacks",
                "weighted_score",
                "frame_count",
                "reference_source",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for entry in payload["evaluations"]:
            writer.writerow(
                {
                    **entry,
                    "frame_count": payload["frame_count"],
                    "reference_source": reference_source,
                }
            )


def format_wsclock_tuning_text(payload: dict, *, reference_source: str = "custom") -> str:
    recommended = payload["recommended"]
    lines = [
        f"frames: {payload['frame_count']}",
        format_reference_source(reference_source),
        f"candidate windows: {payload['min_window']} to {payload['max_window']} ({payload['candidate_window_count']} total)",
        f"writeback penalty: {payload['writeback_penalty']:.2f}",
        f"auto window: {payload['auto_window']}",
        f"dirty pages: {payload['dirty_page_description']}",
        (
            "recommended window: "
            f"{recommended['window']} (faults={recommended['page_faults']}, "
            f"writebacks={recommended['writebacks']}, score={recommended['weighted_score']:.2f})"
        ),
        "pareto frontier: "
        + ", ".join(
            f"τ={entry['window']} (faults={entry['page_faults']}, writes={entry['writebacks']})"
            for entry in payload["pareto_frontier"]
        ),
    ]
    if payload["auto_window_result"] is not None:
        auto_result = payload["auto_window_result"]
        lines.append(
            "auto window result: "
            f"faults={auto_result['page_faults']}, writebacks={auto_result['writebacks']}, score={auto_result['weighted_score']:.2f}"
        )
    else:
        lines.append("auto window result: not evaluated (outside the candidate window range)")
    lines.extend(
        [
            "window  faults  hits  writebacks  score",
            "------  ------  ----  ----------  -----",
        ]
    )
    for entry in payload["evaluations"]:
        lines.append(
            f"{entry['window']:<6}  {entry['page_faults']:<6}  {entry['hits']:<4}  {entry['writebacks']:<10}  {entry['weighted_score']:.2f}"
        )
    return "\n".join(lines)


def format_wsclock_tuning_markdown(payload: dict, *, reference_source: str = "custom") -> str:
    recommended = payload["recommended"]
    lines = [
        "# WSClock Window Tuning Report",
        "",
        f"- workload: {describe_reference_label(reference_source)}",
        f"- frames: {payload['frame_count']}",
        f"- candidate windows: {payload['min_window']} to {payload['max_window']}",
        f"- writeback penalty: {payload['writeback_penalty']:.2f}",
        f"- auto window: {payload['auto_window']}",
        f"- dirty pages: {payload['dirty_page_description']}",
        f"- recommended window: {recommended['window']} (faults {recommended['page_faults']}, writebacks {recommended['writebacks']}, score {recommended['weighted_score']:.2f})",
        f"- Pareto frontier windows: {', '.join(str(entry['window']) for entry in payload['pareto_frontier'])}",
        "",
        "## Why this recommendation",
        "",
        (
            f"Window {recommended['window']} minimizes the weighted score `faults + {payload['writeback_penalty']:.2f} × writebacks` "
            "for this workload and frame budget."
        ),
    ]
    if payload["auto_window_result"] is not None:
        auto_result = payload["auto_window_result"]
        lines.append(
            f"The built-in auto window `{payload['auto_window']}` lands at faults {auto_result['page_faults']}, writebacks {auto_result['writebacks']}, score {auto_result['weighted_score']:.2f}."
        )
    else:
        lines.append(
            f"The built-in auto window `{payload['auto_window']}` is outside this sweep, so it is listed for comparison only and was not evaluated directly."
        )
    lines.extend(
        [
            "",
            "## Candidate windows",
            "",
            "| τ window | Faults | Hits | Hit rate | Writebacks | Weighted score |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for entry in payload["evaluations"]:
        lines.append(
            f"| {entry['window']} | {entry['page_faults']} | {entry['hits']} | {format_percentage(entry['hit_rate'])} | {entry['writebacks']} | {entry['weighted_score']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Pareto frontier",
            "",
            "These windows are not strictly dominated on both page faults and writebacks:",
            "",
        ]
    )
    for entry in payload["pareto_frontier"]:
        lines.append(
            f"- τ={entry['window']}: faults {entry['page_faults']}, writebacks {entry['writebacks']}, score {entry['weighted_score']:.2f}"
        )
    return "\n".join(lines)


def format_study_markdown(payload: dict, *, reference_source: str = "custom") -> str:
    rows = build_study_rows(payload)
    averages = summarize_fault_averages(payload)
    average_wsclock_writebacks = summarize_wsclock_writeback_average(payload)
    best_average = min(averages.values())
    average_winners = "/".join(
        algorithm for algorithm in ALGORITHMS if averages[algorithm] == best_average
    )
    lines = [
        "# Page Replacement Study Report",
        "",
        f"- workload: {describe_reference_label(reference_source)}",
        f"- frame range: {rows[0]['frame_count']} to {rows[-1]['frame_count']}",
        f"- reference length: {len(payload['reference_string'])}",
        f"- WSClock window: {payload['wsclock_window_description']}",
        f"- dirty pages: {payload['dirty_page_description']}",
        f"- best average faults: {average_winners} ({best_average:.2f})",
        f"- average WSClock writebacks: {average_wsclock_writebacks:.2f}",
        "",
        "## Reference string",
        "",
        "```text",
        " ".join(str(page) for page in payload["reference_string"]),
        "```",
        "",
        "## Key takeaways",
        "",
    ]
    fifo_anomalies = payload["fifo_belady_anomalies"]
    if fifo_anomalies:
        first = fifo_anomalies[0]
        lines.append(
            f"- FIFO shows a Belady anomaly at frames {first['from_frames']} -> {first['to_frames']} "
            f"({first['faults_before']} -> {first['faults_after']})."
        )
    else:
        lines.append("- FIFO stays monotonic across this frame range.")

    non_fifo_violations = [
        violation
        for violation in payload["monotonicity_violations"]
        if violation["algorithm"] != "fifo"
    ]
    if non_fifo_violations:
        first = non_fifo_violations[0]
        lines.append(
            f"- {first['algorithm']} also regresses at frames {first['from_frames']} -> {first['to_frames']} "
            f"({first['faults_before']} -> {first['faults_after']})."
        )
    else:
        lines.append("- No non-FIFO regressions appear in this frame range.")
    lines.append(
        f"- {average_winners} has the lowest average page-fault count across the full frame sweep."
    )
    header_cells = ["Frames", *[algorithm.upper() for algorithm in ALGORITHMS], "WSClock τ", "Winner"]
    separator_cells = ["---:", *["---:" for _ in ALGORITHMS], "---:", ":---"]
    lines.extend(
        [
            "",
            "## Faults by frame count",
            "",
            "| " + " | ".join(header_cells) + " |",
            "| " + " | ".join(separator_cells) + " |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [str(row["frame_count"])]
                + [str(row[f"{algorithm}_faults"]) for algorithm in ALGORITHMS]
                + [str(row["wsclock_window"])]
                + [str(row["best_algorithms"])]
            )
            + " |"
        )

    lines.extend(["", "## Regression callouts", ""])
    if fifo_anomalies:
        lines.append("### FIFO Belady anomalies")
        lines.append("")
        for anomaly in fifo_anomalies:
            lines.append(
                f"- frames {anomaly['from_frames']} -> {anomaly['to_frames']}: {anomaly['faults_before']} -> {anomaly['faults_after']} (+{anomaly['fault_delta']})"
            )
        lines.append("")
    else:
        lines.extend(["- FIFO Belady anomalies: none in this study.", ""])

    if non_fifo_violations:
        lines.append("### Other fault regressions")
        lines.append("")
        for violation in non_fifo_violations:
            lines.append(
                f"- {violation['algorithm']}: frames {violation['from_frames']} -> {violation['to_frames']} {violation['faults_before']} -> {violation['faults_after']} (+{violation['fault_delta']})"
            )
        lines.append("")
    else:
        lines.extend(["- Other fault regressions: none in this study.", ""])

    return "\n".join(lines).rstrip() + "\n"


def choose_tick_step(max_value: int) -> int:
    if max_value <= 10:
        return 1
    if max_value <= 20:
        return 2
    if max_value <= 50:
        return 5
    return 10


SVG_COLORS = {
    "fifo": "#ef4444",
    "clock": "#f59e0b",
    "aging": "#8b5cf6",
    "wsclock": "#0f766e",
    "lru": "#2563eb",
    "opt": "#10b981",
}

SVG_STROKE_PATTERNS = {
    "fifo": None,
    "clock": "10 8",
    "aging": "2 6",
    "wsclock": "12 5 3 5",
    "lru": "4 7",
    "opt": None,
}


def format_study_svg(
    payload: dict,
    *,
    reference_source: str = "custom",
    id_prefix: str = "page-replacement-study",
) -> str:
    rows = build_study_rows(payload)
    width = 1080
    height = 720
    chart_left = 84
    chart_top = 118
    chart_width = 720
    chart_height = 360
    chart_bottom = chart_top + chart_height
    chart_right = chart_left + chart_width
    frame_counts = [int(row["frame_count"]) for row in rows]
    max_faults = max(
        int(row[f"{algorithm}_faults"]) for row in rows for algorithm in ALGORITHMS
    )
    tick_step = choose_tick_step(max_faults)
    y_max = max(tick_step, ((max_faults + tick_step - 1) // tick_step) * tick_step)
    y_ticks = list(range(0, y_max + 1, tick_step))
    identifier = make_safe_identifier(id_prefix)
    title_id = f"{identifier}-title"
    desc_id = f"{identifier}-desc"

    def x_position(frame_count: int) -> float:
        if len(frame_counts) == 1:
            return chart_left + chart_width / 2
        span = frame_counts[-1] - frame_counts[0]
        return chart_left + ((frame_count - frame_counts[0]) / span) * chart_width

    def y_position(faults: int) -> float:
        return chart_bottom - (faults / y_max) * chart_height

    grid_lines: list[str] = []
    for tick in y_ticks:
        y = y_position(tick)
        grid_lines.append(
            f'<line x1="{chart_left}" y1="{y:.2f}" x2="{chart_right}" y2="{y:.2f}" stroke="#d7dde8" stroke-width="1" />'
        )
        grid_lines.append(
            f'<text x="{chart_left - 14}" y="{y + 5:.2f}" font-size="13" text-anchor="end" fill="#475569">{tick}</text>'
        )

    x_labels = [
        f'<text x="{x_position(frame):.2f}" y="{chart_bottom + 28}" font-size="13" text-anchor="middle" fill="#475569">{frame}</text>'
        for frame in frame_counts
    ]

    legend_items: list[str] = []
    for index, algorithm in enumerate(ALGORITHMS):
        x = chart_left + index * 150
        dash = SVG_STROKE_PATTERNS[algorithm]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        legend_items.append(
            f'<line x1="{x}" y1="72" x2="{x + 28}" y2="72" stroke="{SVG_COLORS[algorithm]}" stroke-width="4" stroke-linecap="round"{dash_attr} />'
        )
        legend_items.append(
            f'<text x="{x + 38}" y="77" font-size="14" fill="#0f172a">{algorithm.upper()}</text>'
        )

    series_parts: list[str] = []
    for algorithm in ALGORITHMS:
        points = " ".join(
            f"{x_position(int(row['frame_count'])):.2f},{y_position(int(row[f'{algorithm}_faults'])):.2f}"
            for row in rows
        )
        color = SVG_COLORS[algorithm]
        dash = SVG_STROKE_PATTERNS[algorithm]
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        series_parts.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" points="{points}"{dash_attr} />'
        )
        for row in rows:
            x = x_position(int(row["frame_count"]))
            faults = int(row[f"{algorithm}_faults"])
            y = y_position(faults)
            series_parts.append(
                f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.5" fill="{color}" stroke="#ffffff" stroke-width="2" />'
            )
            series_parts.append(
                f'<text x="{x:.2f}" y="{y - 12:.2f}" font-size="11" text-anchor="middle" fill="{color}">{faults}</text>'
            )

    averages = summarize_fault_averages(payload)
    best_average = min(averages.values())
    average_winners = "/".join(
        algorithm.upper() for algorithm in ALGORITHMS if averages[algorithm] == best_average
    )
    summary_lines = [
        f"workload: {describe_reference_label(reference_source)}",
        f"frame range: {frame_counts[0]} to {frame_counts[-1]} frames | WSClock τ {payload['wsclock_window_description']}",
        f"best average faults: {average_winners} ({best_average:.2f})",
    ]
    fifo_anomalies = payload["fifo_belady_anomalies"]
    if fifo_anomalies:
        first = fifo_anomalies[0]
        summary_lines.append(
            f"FIFO anomaly: {first['from_frames']} -> {first['to_frames']} frames, {first['faults_before']} -> {first['faults_after']} faults"
        )
    else:
        summary_lines.append("FIFO anomaly: none in this frame range")

    non_fifo_violations = [
        violation
        for violation in payload["monotonicity_violations"]
        if violation["algorithm"] != "fifo"
    ]
    if non_fifo_violations:
        first = non_fifo_violations[0]
        summary_lines.append(
            f"Other regression: {first['algorithm'].upper()} {first['from_frames']} -> {first['to_frames']} frames, {first['faults_before']} -> {first['faults_after']} faults"
        )
    else:
        summary_lines.append("Other regressions: none detected")

    summary_text = []
    for index, line in enumerate(summary_lines):
        summary_text.append(
            f'<text x="84" y="{545 + index * 28}" font-size="18" fill="#0f172a">{escape(line)}</text>'
        )

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
            f'  <title id="{title_id}">Page replacement frame study chart</title>',
            f'  <desc id="{desc_id}">Page-fault vs frame-count chart for {escape(describe_reference_label(reference_source))}</desc>',
            '  <rect width="100%" height="100%" fill="#f8fafc" />',
            '  <rect x="36" y="28" width="1008" height="664" rx="28" fill="#ffffff" stroke="#d7dde8" stroke-width="2" />',
            '  <text x="84" y="64" font-size="30" font-weight="700" fill="#0f172a">Page faults vs frame count</text>',
            f'  <text x="84" y="96" font-size="16" fill="#475569">{escape(describe_reference_label(reference_source))}</text>',
            *legend_items,
            f'  <line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="2" />',
            f'  <line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="2" />',
            *grid_lines,
            *x_labels,
            f'  <text x="{chart_left + chart_width / 2:.2f}" y="{chart_bottom + 56}" font-size="14" text-anchor="middle" fill="#475569">Frames</text>',
            f'  <text x="28" y="{chart_top + chart_height / 2:.2f}" font-size="14" fill="#475569" transform="rotate(-90 28 {chart_top + chart_height / 2:.2f})">Page faults</text>',
            *series_parts,
            '  <rect x="64" y="514" width="952" height="142" rx="20" fill="#eef2ff" stroke="#c7d2fe" stroke-width="1.5" />',
            *summary_text,
            "</svg>",
        ]
    )


def resolve_gallery_workloads(
    selected_presets: list[str] | None,
    selected_benchmarks: list[str] | None,
    *,
    selected_pages_files: list[Path] | None = None,
    include_benchmarks: bool,
) -> list[GalleryWorkload]:
    ordered: list[GalleryWorkload] = []
    seen_sources: set[str] = set()
    seen_names: set[str] = set()

    def add_workload(workload: GalleryWorkload) -> None:
        if workload.reference_source in seen_sources:
            return
        unique_name = workload.name
        suffix = 2
        while unique_name in seen_names:
            unique_name = f"{workload.name}-{suffix}"
            suffix += 1
        if unique_name != workload.name:
            workload = GalleryWorkload(
                name=unique_name,
                description=workload.description,
                reference_string=workload.reference_string,
                reference_source=workload.reference_source,
                source_kind=workload.source_kind,
            )
        ordered.append(workload)
        seen_sources.add(workload.reference_source)
        seen_names.add(workload.name)

    if selected_presets or selected_benchmarks or selected_pages_files:
        for name in selected_presets or []:
            add_workload(workload_from_preset(resolve_preset(name)))
        for name in selected_benchmarks or []:
            add_workload(workload_from_benchmark(resolve_trace_benchmark(name)))
        for path in selected_pages_files or []:
            add_workload(workload_from_pages_file(path))
        return ordered

    for preset in list_workload_presets():
        add_workload(workload_from_preset(preset))
    if include_benchmarks:
        for benchmark in list_trace_benchmarks():
            add_workload(workload_from_benchmark(benchmark))
    return ordered


def format_average_fault_summary(averages: dict[str, float]) -> list[str]:
    return [f"{algorithm.upper()}: {averages[algorithm]:.2f}" for algorithm in ALGORITHMS]


def build_trace_summary_bundle(
    workload: GalleryWorkload,
    *,
    artifact_dir: Path,
    html_dir: Path,
    window_size: int = 8,
    phase_threshold: float = 0.45,
) -> dict:
    reference_source = workload.reference_source
    payload = summarize_trace(
        workload.reference_string,
        window_size=window_size,
        phase_threshold=phase_threshold,
    )
    payload["reference_source"] = reference_source
    stem = f"{workload.name}-trace-summary"
    markdown_path = artifact_dir / f"{stem}.md"
    svg_path = artifact_dir / f"{stem}.svg"
    html_path = artifact_dir / f"{stem}.html"
    json_path = artifact_dir / f"{stem}.json"

    write_text_output(
        markdown_path,
        format_trace_summary_markdown(payload, reference_source=reference_source),
    )
    svg_markup = format_trace_summary_svg(
        payload,
        reference_source=reference_source,
        id_prefix=f"page-replacement-trace-summary-{workload.name}",
    )
    write_text_output(svg_path, svg_markup)
    write_text_output(json_path, json.dumps(payload, indent=2) + "\n")
    write_text_output(
        html_path,
        format_trace_summary_html(
            payload,
            reference_source=reference_source,
            inline_svg=format_trace_summary_svg(
                payload,
                reference_source=reference_source,
                id_prefix=f"gallery-trace-summary-{workload.name}",
            ),
            downloads=[
                ("Markdown", os.path.relpath(markdown_path, html_path.parent)),
                ("SVG", os.path.relpath(svg_path, html_path.parent)),
                ("JSON", os.path.relpath(json_path, html_path.parent)),
            ],
        ),
    )
    return {
        "payload": payload,
        "relative_paths": {
            "markdown": os.path.relpath(markdown_path, html_dir),
            "svg": os.path.relpath(svg_path, html_dir),
            "html": os.path.relpath(html_path, html_dir),
            "json": os.path.relpath(json_path, html_dir),
        },
    }


def build_gallery_run(
    workload: GalleryWorkload,
    *,
    min_frames: int,
    max_frames: int,
    wsclock_window: int | None,
    dirty_pages: Iterable[int] | None,
    artifact_dir: Path,
    html_dir: Path,
) -> dict:
    reference_source = workload.reference_source
    payload = study_frame_counts(
        workload.reference_string,
        min_frames,
        max_frames,
        wsclock_window=wsclock_window,
        dirty_pages=dirty_pages,
    )
    payload["reference_source"] = reference_source
    stem = f"{workload.name}-study"
    markdown_path = artifact_dir / f"{stem}.md"
    svg_path = artifact_dir / f"{stem}.svg"
    csv_path = artifact_dir / f"{stem}.csv"
    json_path = artifact_dir / f"{stem}.json"

    write_text_output(
        markdown_path,
        format_study_markdown(payload, reference_source=reference_source),
    )
    write_text_output(
        svg_path,
        format_study_svg(
            payload,
            reference_source=reference_source,
            id_prefix=f"page-replacement-{workload.name}",
        ),
    )
    write_study_csv(csv_path, payload, reference_source=reference_source)
    write_study_json(json_path, payload)

    trace_summary = None
    if workload.source_kind == "custom":
        trace_summary = build_trace_summary_bundle(
            workload,
            artifact_dir=artifact_dir,
            html_dir=html_dir,
        )

    averages = summarize_fault_averages(payload)
    best_average = min(averages.values())
    best_average_winners = [
        algorithm for algorithm in ALGORITHMS if averages[algorithm] == best_average
    ]
    non_fifo_violations = [
        violation
        for violation in payload["monotonicity_violations"]
        if violation["algorithm"] != "fifo"
    ]
    return {
        "workload": workload,
        "payload": payload,
        "average_faults": averages,
        "best_average_faults": best_average,
        "best_average_winners": best_average_winners,
        "fifo_has_anomaly": bool(payload["fifo_belady_anomalies"]),
        "non_fifo_violations": non_fifo_violations,
        "relative_paths": {
            "markdown": os.path.relpath(markdown_path, html_dir),
            "svg": os.path.relpath(svg_path, html_dir),
            "csv": os.path.relpath(csv_path, html_dir),
            "json": os.path.relpath(json_path, html_dir),
        },
        "trace_summary": trace_summary,
        "inline_svg": format_study_svg(
            payload,
            reference_source=reference_source,
            id_prefix=f"gallery-{workload.name}",
        ),
    }


def format_gallery_text(gallery_runs: list[dict], *, html_path: Path) -> str:
    lines = [
        f"gallery workloads: {len(gallery_runs)}",
        f"html report: {html_path}",
        f"wsclock window: {gallery_runs[0]['payload']['wsclock_window_description']}" if gallery_runs else "wsclock window: n/a",
        f"dirty pages: {gallery_runs[0]['payload']['dirty_page_description']}" if gallery_runs else "dirty pages: n/a",
    ]
    for run in gallery_runs:
        winners = "/".join(algorithm.upper() for algorithm in run["best_average_winners"])
        workload = run["workload"]
        drilldown_suffix = ", trace drill-down=yes" if run["trace_summary"] else ""
        lines.append(
            f"- {workload.source_kind} {workload.name}: best average faults {winners} ({run['best_average_faults']:.2f}), "
            f"fifo anomaly={'yes' if run['fifo_has_anomaly'] else 'no'}, "
            f"other regressions={len(run['non_fifo_violations'])}{drilldown_suffix}"
        )
    return "\n".join(lines)


def format_gallery_html(
    gallery_runs: list[dict],
    *,
    min_frames: int,
    max_frames: int,
) -> str:
    workload_count = len(gallery_runs)
    fifo_anomaly_count = sum(1 for run in gallery_runs if run["fifo_has_anomaly"])
    non_fifo_regression_count = sum(
        1 for run in gallery_runs if run["non_fifo_violations"]
    )
    benchmark_count = sum(
        1 for run in gallery_runs if run["workload"].source_kind == "benchmark"
    )
    custom_count = sum(
        1 for run in gallery_runs if run["workload"].source_kind == "custom"
    )
    trace_drilldown_count = sum(1 for run in gallery_runs if run["trace_summary"])
    winner_counts: dict[str, int] = {algorithm: 0 for algorithm in ALGORITHMS}
    for run in gallery_runs:
        for algorithm in run["best_average_winners"]:
            winner_counts[algorithm] += 1
    winner_summary = ", ".join(
        f"{algorithm.upper()} × {winner_counts[algorithm]}" for algorithm in ALGORITHMS
    )

    summary_rows: list[str] = []
    for run in gallery_runs:
        workload = run["workload"]
        section_id = f"workload-{make_safe_identifier(workload.name)}"
        winners = "/".join(algorithm.upper() for algorithm in run["best_average_winners"])
        drilldown_cell = "—"
        if run["trace_summary"]:
            drilldown_cell = (
                f'<a href="{escape(run["trace_summary"]["relative_paths"]["html"])}">'
                'custom trace card</a>'
            )
        summary_rows.append(
            "<tr>"
            f"<td>{escape(workload.source_kind)}</td>"
            f"<td><a href=\"#{section_id}\"><code>{escape(workload.name)}</code></a></td>"
            f"<td>{escape(workload.description)}</td>"
            f"<td>{run['best_average_faults']:.2f} ({escape(winners)})</td>"
            f"<td>{'yes' if run['fifo_has_anomaly'] else 'no'}</td>"
            f"<td>{len(run['non_fifo_violations'])}</td>"
            f"<td>{drilldown_cell}</td>"
            "</tr>"
        )

    sections: list[str] = []
    for run in gallery_runs:
        workload = run["workload"]
        section_id = f"workload-{make_safe_identifier(workload.name)}"
        averages = format_average_fault_summary(run["average_faults"])
        average_items = "".join(
            f"<li><code>{escape(item)}</code></li>" for item in averages
        )
        if run["payload"]["fifo_belady_anomalies"]:
            fifo_items = "".join(
                "<li>"
                f"frames {entry['from_frames']} → {entry['to_frames']}: "
                f"{entry['faults_before']} → {entry['faults_after']} (+{entry['fault_delta']})"
                "</li>"
                for entry in run["payload"]["fifo_belady_anomalies"]
            )
        else:
            fifo_items = "<li>none in this frame range</li>"

        if run["non_fifo_violations"]:
            other_items = "".join(
                "<li>"
                f"{escape(entry['algorithm'].upper())}: frames {entry['from_frames']} → {entry['to_frames']} "
                f"{entry['faults_before']} → {entry['faults_after']} (+{entry['fault_delta']})"
                "</li>"
                for entry in run["non_fifo_violations"]
            )
        else:
            other_items = "<li>none in this frame range</li>"

        download_links = " · ".join(
            f'<a href="{escape(path)}">{label}</a>'
            for label, path in (
                ("Markdown", run["relative_paths"]["markdown"]),
                ("SVG", run["relative_paths"]["svg"]),
                ("CSV", run["relative_paths"]["csv"]),
                ("JSON", run["relative_paths"]["json"]),
            )
        )
        trace_summary_panel = ""
        if run["trace_summary"]:
            trace_payload = run["trace_summary"]["payload"]
            working_set = trace_payload["working_set_stats"]
            reuse_stats = trace_payload["reuse_distance_stats"]
            reuse_line = (
                f"min {reuse_stats['min']}, median {reuse_stats['median']:.1f}, p90 {reuse_stats['p90']:.1f}, max {reuse_stats['max']}, avg {reuse_stats['average']:.2f}"
                if reuse_stats["count"]
                else "no repeated pages in this workload"
            )
            trace_downloads = " · ".join(
                f'<a href="{escape(path)}">{label}</a>'
                for label, path in (
                    ("HTML", run["trace_summary"]["relative_paths"]["html"]),
                    ("Markdown", run["trace_summary"]["relative_paths"]["markdown"]),
                    ("SVG", run["trace_summary"]["relative_paths"]["svg"]),
                    ("JSON", run["trace_summary"]["relative_paths"]["json"]),
                )
            )
            trace_summary_panel = (
                '<div class="meta-panel">'
                '<h3>Custom trace drill-down</h3>'
                '<ul>'
                f'<li>window size {trace_payload["window_size"]}</li>'
                f'<li>working-set range {working_set["min"]}–{working_set["max"]} (avg {working_set["average"]:.2f})</li>'
                f'<li>phase hints {len(trace_payload["phase_boundaries"])}</li>'
                f'<li>reuse summary {escape(reuse_line)}</li>'
                '</ul>'
                f'<p class="muted">Trace drill-down downloads: {trace_downloads}</p>'
                '</div>'
            )
        trace_chip = (
            '<span class="chip chip--accent">trace drill-down ready</span>'
            if run["trace_summary"]
            else ""
        )
        sections.append(
            f"<section class=\"study-card\" id=\"{section_id}\">"
            "<div class=\"study-card__header\">"
            f"<div><h2><code>{escape(workload.name)}</code></h2><p>{escape(workload.description)}</p></div>"
            "<div class=\"study-card__chips\">"
            f"<span class=\"chip\">{escape(workload.source_kind)}</span>"
            f"<span class=\"chip\">frames {min_frames}–{max_frames}</span>"
            f"<span class=\"chip\">reference length {len(workload.reference_string)}</span>"
            f"<span class=\"chip chip--accent\">best average {'/'.join(algorithm.upper() for algorithm in run['best_average_winners'])}</span>"
            f"<span class=\"chip {'chip--warn' if run['fifo_has_anomaly'] else 'chip--ok'}\">FIFO anomaly {'yes' if run['fifo_has_anomaly'] else 'no'}</span>"
            f"{trace_chip}"
            "</div>"
            "</div>"
            f"<figure>{run['inline_svg']}<figcaption>Study downloads: {download_links}</figcaption></figure>"
            "<div class=\"study-card__meta\">"
            f"<div class=\"meta-panel\"><h3>Average faults</h3><ul>{average_items}</ul></div>"
            f"<div class=\"meta-panel\"><h3>FIFO anomaly callouts</h3><ul>{fifo_items}</ul></div>"
            f"<div class=\"meta-panel\"><h3>Other regressions</h3><ul>{other_items}</ul></div>"
            f"{trace_summary_panel}"
            "</div>"
            "</section>"
        )

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Page Replacement Study Gallery</title>
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
        --ok: #16a34a;
        --warn: #dc2626;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); }}
      main {{ max-width: 1480px; margin: 0 auto; padding: 32px 20px 64px; }}
      h1, h2, h3, p {{ margin-top: 0; }}
      a {{ color: var(--accent); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
      .hero, .study-card, .summary-table {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p {{ color: var(--muted); max-width: 960px; }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; }}
      .summary-grid strong {{ display: block; font-size: 1.4rem; margin-bottom: 6px; }}
      .summary-table {{ overflow: auto; padding: 18px; margin-bottom: 24px; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      .study-grid {{ display: grid; gap: 24px; }}
      .study-card {{ padding: 22px; }}
      .study-card__header {{ display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 14px; }}
      .study-card__header p {{ color: var(--muted); max-width: 70ch; margin-bottom: 0; }}
      .study-card__chips {{ display: flex; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }}
      .chip {{ display: inline-flex; align-items: center; padding: 8px 12px; border-radius: 999px; background: #e2e8f0; color: var(--text); font-size: 0.92rem; text-transform: capitalize; }}
      .chip--accent {{ background: #dbeafe; color: #1d4ed8; }}
      .chip--ok {{ background: #dcfce7; color: #166534; }}
      .chip--warn {{ background: #fee2e2; color: #991b1b; }}
      figure {{ margin: 0; overflow-x: auto; }}
      figure svg {{ width: 100%; height: auto; min-width: 720px; display: block; }}
      figcaption {{ margin-top: 10px; color: var(--muted); }}
      .study-card__meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 18px; }}
      .meta-panel {{ border-radius: 18px; background: #f8fafc; border: 1px solid var(--border); padding: 16px; }}
      .meta-panel h3 {{ margin-bottom: 10px; font-size: 1rem; }}
      .meta-panel ul {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      .meta-panel li + li {{ margin-top: 8px; }}
      .meta-panel p {{ margin: 10px 0 0; }}
      .muted {{ color: var(--muted); }}
      @media (max-width: 900px) {{
        .study-card__header {{ flex-direction: column; }}
        .study-card__chips {{ justify-content: flex-start; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>Page Replacement Study Gallery</h1>
        <p>Frame-range study cards for <code>page-replacement-lab</code>. The gallery can mix compact presets, larger trace benchmarks, and imported custom traces, keeps the screenshot-ready SVG study cards inline, links the exported Markdown / SVG / CSV / JSON companions, and now adds trace-summary drill-down cards for imported workloads.</p>
        <ul class="summary-grid">
          <li><strong>{workload_count}</strong> workloads</li>
          <li><strong>{benchmark_count}</strong> trace benchmarks</li>
          <li><strong>{custom_count}</strong> imported traces</li>
          <li><strong>{trace_drilldown_count}</strong> trace drill-down cards</li>
          <li><strong>{min_frames}–{max_frames}</strong> frame range</li>
          <li><strong>{fifo_anomaly_count}</strong> FIFO anomaly workloads</li>
          <li><strong>{non_fifo_regression_count}</strong> workloads with non-FIFO regressions</li>
          <li><strong>{escape(gallery_runs[0]['payload']['wsclock_window_description']) if gallery_runs else 'n/a'}</strong> WSClock τ</li>
          <li><strong>{escape(gallery_runs[0]['payload']['dirty_page_description']) if gallery_runs else 'n/a'}</strong> dirty pages</li>
          <li><strong>Winner tally</strong>{escape(winner_summary)}</li>
        </ul>
      </section>
      <section class="summary-table">
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Workload</th>
              <th>Description</th>
              <th>Best average faults</th>
              <th>FIFO anomaly</th>
              <th>Other regressions</th>
              <th>Drill-down</th>
            </tr>
          </thead>
          <tbody>
            {''.join(summary_rows)}
          </tbody>
        </table>
      </section>
      <div class="study-grid">
        {''.join(sections)}
      </div>
    </main>
  </body>
</html>
'''

def select_lowest_keys(values: dict[str, float], *, tolerance: float = 1e-12) -> list[str]:
    best_value = min(values.values())
    return [
        key for key, value in values.items() if abs(value - best_value) <= tolerance
    ]


def format_percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def build_aggregate_run(
    workload: GalleryWorkload,
    *,
    min_frames: int,
    max_frames: int,
    wsclock_window: int | None,
    dirty_pages: Iterable[int] | None,
) -> dict:
    payload = study_frame_counts(
        workload.reference_string,
        min_frames,
        max_frames,
        wsclock_window=wsclock_window,
        dirty_pages=dirty_pages,
    )
    payload["reference_source"] = workload.reference_source
    average_faults = summarize_fault_averages(payload)
    average_wsclock_writebacks = summarize_wsclock_writeback_average(payload)
    reference_length = len(workload.reference_string)
    average_fault_rates = {
        algorithm: average_faults[algorithm] / reference_length
        for algorithm in ALGORITHMS
    }
    best_average_faults = min(average_faults.values())
    best_average_winners = select_lowest_keys(average_faults)
    best_average_fault_rate = min(average_fault_rates.values())
    best_rate_winners = select_lowest_keys(average_fault_rates)
    non_fifo_violations = [
        violation
        for violation in payload["monotonicity_violations"]
        if violation["algorithm"] != "fifo"
    ]
    return {
        "workload": workload,
        "payload": payload,
        "reference_length": reference_length,
        "average_faults": average_faults,
        "average_wsclock_writebacks": average_wsclock_writebacks,
        "average_fault_rates": average_fault_rates,
        "best_average_faults": best_average_faults,
        "best_average_winners": best_average_winners,
        "best_average_fault_rate": best_average_fault_rate,
        "best_rate_winners": best_rate_winners,
        "fifo_has_anomaly": bool(payload["fifo_belady_anomalies"]),
        "non_fifo_violations": non_fifo_violations,
    }


def summarize_aggregate_runs(aggregate_runs: list[dict]) -> dict:
    if not aggregate_runs:
        raise InputError("aggregate dashboard needs at least one workload")

    winner_counts = {algorithm: 0 for algorithm in ALGORITHMS}
    for run in aggregate_runs:
        for algorithm in run["best_rate_winners"]:
            winner_counts[algorithm] += 1

    overall_average_fault_rates = {
        algorithm: sum(run["average_fault_rates"][algorithm] for run in aggregate_runs)
        / len(aggregate_runs)
        for algorithm in ALGORITHMS
    }
    overall_average_faults = {
        algorithm: sum(run["average_faults"][algorithm] for run in aggregate_runs)
        / len(aggregate_runs)
        for algorithm in ALGORITHMS
    }
    overall_average_wsclock_writebacks = sum(
        run["average_wsclock_writebacks"] for run in aggregate_runs
    ) / len(aggregate_runs)
    preset_count = sum(
        1 for run in aggregate_runs if run["workload"].source_kind == "preset"
    )
    benchmark_count = sum(
        1 for run in aggregate_runs if run["workload"].source_kind == "benchmark"
    )
    custom_count = sum(
        1 for run in aggregate_runs if run["workload"].source_kind == "custom"
    )
    fifo_anomaly_count = sum(1 for run in aggregate_runs if run["fifo_has_anomaly"])
    non_fifo_regression_count = sum(
        1 for run in aggregate_runs if run["non_fifo_violations"]
    )
    return {
        "workload_count": len(aggregate_runs),
        "preset_count": preset_count,
        "benchmark_count": benchmark_count,
        "custom_count": custom_count,
        "fifo_anomaly_count": fifo_anomaly_count,
        "non_fifo_regression_count": non_fifo_regression_count,
        "winner_counts": winner_counts,
        "overall_average_fault_rates": overall_average_fault_rates,
        "overall_average_faults": overall_average_faults,
        "overall_average_wsclock_writebacks": overall_average_wsclock_writebacks,
        "overall_best_rate_winners": select_lowest_keys(overall_average_fault_rates),
    }


def write_aggregate_csv(path: Path, aggregate_runs: list[dict]) -> None:
    ensure_output_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "type",
            "workload",
            "reference_source",
            "reference_length",
            "best_average_fault_algorithms",
            "best_average_fault_rate_algorithms",
            "fifo_has_anomaly",
            "non_fifo_regression_count",
            "wsclock_avg_writebacks",
            *[f"{algorithm}_avg_faults" for algorithm in ALGORITHMS],
            *[f"{algorithm}_avg_fault_rate" for algorithm in ALGORITHMS],
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for run in aggregate_runs:
            row = {
                "type": run["workload"].source_kind,
                "workload": run["workload"].name,
                "reference_source": run["workload"].reference_source,
                "reference_length": run["reference_length"],
                "best_average_fault_algorithms": "/".join(run["best_average_winners"]),
                "best_average_fault_rate_algorithms": "/".join(run["best_rate_winners"]),
                "fifo_has_anomaly": "yes" if run["fifo_has_anomaly"] else "no",
                "non_fifo_regression_count": len(run["non_fifo_violations"]),
                "wsclock_avg_writebacks": f"{run['average_wsclock_writebacks']:.6f}",
            }
            for algorithm in ALGORITHMS:
                row[f"{algorithm}_avg_faults"] = f"{run['average_faults'][algorithm]:.6f}"
                row[f"{algorithm}_avg_fault_rate"] = f"{run['average_fault_rates'][algorithm]:.6f}"
            writer.writerow(row)


def build_aggregate_payload(
    aggregate_runs: list[dict],
    *,
    min_frames: int,
    max_frames: int,
    html_path: Path,
    artifact_dir: Path,
) -> dict:
    summary = summarize_aggregate_runs(aggregate_runs)
    return {
        "min_frames": min_frames,
        "max_frames": max_frames,
        "artifact_dir": str(artifact_dir),
        "html_path": str(html_path),
        "wsclock_window_mode": aggregate_runs[0]["payload"]["wsclock_window_mode"],
        "wsclock_window_override": aggregate_runs[0]["payload"]["wsclock_window_override"],
        "wsclock_window_description": aggregate_runs[0]["payload"]["wsclock_window_description"],
        "dirty_pages": aggregate_runs[0]["payload"]["dirty_pages"],
        "dirty_page_count": aggregate_runs[0]["payload"]["dirty_page_count"],
        "dirty_page_description": aggregate_runs[0]["payload"]["dirty_page_description"],
        "summary": {
            **summary,
            "overall_average_fault_rates": {
                algorithm: round(value, 6)
                for algorithm, value in summary["overall_average_fault_rates"].items()
            },
            "overall_average_faults": {
                algorithm: round(value, 6)
                for algorithm, value in summary["overall_average_faults"].items()
            },
            "overall_average_wsclock_writebacks": round(summary["overall_average_wsclock_writebacks"], 6),
        },
        "workloads": [
            {
                "type": run["workload"].source_kind,
                "workload": run["workload"].name,
                "description": run["workload"].description,
                "reference_length": run["reference_length"],
                "reference_source": run["workload"].reference_source,
                "best_average_faults": round(run["best_average_faults"], 6),
                "best_average_fault_rate": round(run["best_average_fault_rate"], 6),
                "average_wsclock_writebacks": round(run["average_wsclock_writebacks"], 6),
                "best_average_winners": run["best_average_winners"],
                "best_rate_winners": run["best_rate_winners"],
                "fifo_has_anomaly": run["fifo_has_anomaly"],
                "non_fifo_regression_count": len(run["non_fifo_violations"]),
                "average_faults": {
                    algorithm: round(value, 6)
                    for algorithm, value in run["average_faults"].items()
                },
                "average_fault_rates": {
                    algorithm: round(value, 6)
                    for algorithm, value in run["average_fault_rates"].items()
                },
            }
            for run in aggregate_runs
        ],
    }


def choose_rate_tick_step(max_rate: float) -> float:
    if max_rate <= 0.1:
        return 0.02
    if max_rate <= 0.2:
        return 0.05
    if max_rate <= 0.4:
        return 0.1
    return 0.2


def format_aggregate_svg(
    aggregate_runs: list[dict],
    *,
    min_frames: int,
    max_frames: int,
    id_prefix: str = "page-replacement-aggregate",
) -> str:
    summary = summarize_aggregate_runs(aggregate_runs)
    width = 1480
    header_height = 156
    group_height = 118
    chart_top = header_height
    chart_left = 340
    chart_right = width - 88
    chart_width = chart_right - chart_left
    bar_height = 11
    bar_gap = 8
    chart_height = len(aggregate_runs) * group_height
    chart_bottom = chart_top + chart_height
    footer_height = 150
    height = chart_bottom + footer_height
    max_rate = max(
        run["average_fault_rates"][algorithm]
        for run in aggregate_runs
        for algorithm in ALGORITHMS
    )
    tick_step = choose_rate_tick_step(max_rate)
    tick_count = max(1, int(max_rate / tick_step) + 1)
    x_max = max(tick_step, tick_count * tick_step)
    ticks = [round(index * tick_step, 10) for index in range(tick_count + 1)]
    identifier = make_safe_identifier(id_prefix)
    title_id = f"{identifier}-title"
    desc_id = f"{identifier}-desc"

    def x_position(rate: float) -> float:
        return chart_left + (rate / x_max) * chart_width

    grid_lines: list[str] = []
    for tick in ticks:
        x = x_position(tick)
        grid_lines.append(
            f'<line x1="{x:.2f}" y1="{chart_top}" x2="{x:.2f}" y2="{chart_bottom}" stroke="#d7dde8" stroke-width="1" />'
        )
        grid_lines.append(
            f'<text x="{x:.2f}" y="{chart_bottom + 30}" font-size="13" text-anchor="middle" fill="#475569">{escape(format_percentage(tick))}</text>'
        )

    legend_items: list[str] = []
    for index, algorithm in enumerate(ALGORITHMS):
        x = 340 + index * 170
        legend_items.append(
            f'<rect x="{x}" y="74" width="26" height="12" rx="6" fill="{SVG_COLORS[algorithm]}" />'
        )
        legend_items.append(
            f'<text x="{x + 36}" y="84" font-size="14" fill="#0f172a">{algorithm.upper()}</text>'
        )

    group_parts: list[str] = []
    for run_index, run in enumerate(aggregate_runs):
        workload = run["workload"]
        group_y = chart_top + run_index * group_height
        label_y = group_y + 18
        group_parts.append(
            f'<text x="36" y="{label_y}" font-size="18" font-weight="700" fill="#0f172a"><tspan font-family="SFMono-Regular, ui-monospace, monospace">{escape(workload.name)}</tspan></text>'
        )
        meta = f"{workload.source_kind} · len {run['reference_length']} · winner {'/'.join(algorithm.upper() for algorithm in run['best_rate_winners'])}"
        group_parts.append(
            f'<text x="36" y="{label_y + 22}" font-size="13" fill="#475569">{escape(meta)}</text>'
        )
        group_parts.append(
            f'<line x1="36" y1="{group_y + group_height - 12}" x2="{width - 36}" y2="{group_y + group_height - 12}" stroke="#e2e8f0" stroke-width="1" />'
        )
        for algorithm_index, algorithm in enumerate(ALGORITHMS):
            y = group_y + 44 + algorithm_index * (bar_height + bar_gap)
            rate = run["average_fault_rates"][algorithm]
            x = x_position(rate)
            label_x = min(x + 10, width - 60)
            group_parts.append(
                f'<text x="250" y="{y + 9}" font-size="13" text-anchor="end" fill="#475569">{algorithm.upper()}</text>'
            )
            group_parts.append(
                f'<rect x="{chart_left}" y="{y}" width="{max(x - chart_left, 0):.2f}" height="{bar_height}" rx="5.5" fill="{SVG_COLORS[algorithm]}" />'
            )
            group_parts.append(
                f'<text x="{label_x:.2f}" y="{y + 9}" font-size="12" fill="{SVG_COLORS[algorithm]}">{escape(format_percentage(rate))}</text>'
            )

    overall_winners = "/".join(algorithm.upper() for algorithm in summary["overall_best_rate_winners"])
    winner_tally = "; ".join(
        f"{algorithm.upper()} × {summary['winner_counts'][algorithm]}"
        for algorithm in ALGORITHMS
    )
    summary_lines = [
        f"frame range: {min_frames} to {max_frames} frames across {summary['workload_count']} workloads ({summary['benchmark_count']} benchmarks, {summary['custom_count']} custom traces)",
        f"overall best normalized average fault rate: {overall_winners}",
        f"winner tally: {winner_tally}",
        f"FIFO anomalies in {summary['fifo_anomaly_count']} workloads; non-FIFO regressions in {summary['non_fifo_regression_count']} workloads",
    ]
    summary_text = [
        f'<text x="84" y="{chart_bottom + 48 + index * 24}" font-size="18" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(summary_lines)
    ]

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
            f'  <title id="{title_id}">Page replacement aggregate workload comparison</title>',
            f'  <desc id="{desc_id}">Normalized average page-fault rate by workload and algorithm across a shared frame range.</desc>',
            '  <rect width="100%" height="100%" fill="#f8fafc" />',
            f'  <rect x="28" y="24" width="{width - 56}" height="{height - 48}" rx="28" fill="#ffffff" stroke="#d7dde8" stroke-width="2" />',
            '  <text x="84" y="64" font-size="30" font-weight="700" fill="#0f172a">Normalized average page-fault rate by workload</text>',
            '  <text x="84" y="96" font-size="16" fill="#475569">Cross-workload aggregate dashboard for page-replacement-lab with one grouped bar set per workload.</text>',
            *legend_items,
            f'  <line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="2" />',
            f'  <line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="2" />',
            *grid_lines,
            f'  <text x="{chart_left + chart_width / 2:.2f}" y="{chart_bottom + 58}" font-size="14" text-anchor="middle" fill="#475569">Average page-fault rate across frame counts</text>',
            *group_parts,
            f'  <rect x="64" y="{chart_bottom + 18}" width="1352" height="112" rx="20" fill="#eef2ff" stroke="#c7d2fe" stroke-width="1.5" />',
            *summary_text,
            '</svg>',
        ]
    )


def format_aggregate_text(aggregate_runs: list[dict], *, html_path: Path, svg_path: Path) -> str:
    summary = summarize_aggregate_runs(aggregate_runs)
    overall_winners = "/".join(algorithm.upper() for algorithm in summary["overall_best_rate_winners"])
    lines = [
        f"aggregate workloads: {summary['workload_count']}",
        f"html report: {html_path}",
        f"svg chart: {svg_path}",
        f"wsclock window: {aggregate_runs[0]['payload']['wsclock_window_description']}" if aggregate_runs else "wsclock window: n/a",
        f"dirty pages: {aggregate_runs[0]['payload']['dirty_page_description']}" if aggregate_runs else "dirty pages: n/a",
        f"overall best normalized average fault rate: {overall_winners}",
        f"overall average WSClock writebacks: {summary['overall_average_wsclock_writebacks']:.2f}",
    ]
    for run in aggregate_runs:
        workload = run["workload"]
        winners = "/".join(algorithm.upper() for algorithm in run["best_rate_winners"])
        lines.append(
            f"- {workload.source_kind} {workload.name}: best normalized average rate {winners} ({format_percentage(run['best_average_fault_rate'])}), wsclock avg writebacks={run['average_wsclock_writebacks']:.2f}, fifo anomaly={'yes' if run['fifo_has_anomaly'] else 'no'}, other regressions={len(run['non_fifo_violations'])}"
        )
    return "\n".join(lines)


def format_aggregate_html(
    aggregate_runs: list[dict],
    *,
    min_frames: int,
    max_frames: int,
    svg_filename: str,
    csv_filename: str,
    json_filename: str,
) -> str:
    summary = summarize_aggregate_runs(aggregate_runs)
    winner_summary = ", ".join(
        f"{algorithm.upper()} × {summary['winner_counts'][algorithm]}" for algorithm in ALGORITHMS
    )
    overall_rows = "".join(
        "<tr>"
        f"<td><code>{escape(algorithm.upper())}</code></td>"
        f"<td>{escape(format_percentage(summary['overall_average_fault_rates'][algorithm]))}</td>"
        f"<td>{summary['overall_average_faults'][algorithm]:.2f}</td>"
        "</tr>"
        for algorithm in ALGORITHMS
    )
    workload_rows: list[str] = []
    for run in aggregate_runs:
        workload = run["workload"]
        rate_cells = "<br />".join(
            f"<code>{escape(algorithm.upper())}</code> {escape(format_percentage(run['average_fault_rates'][algorithm]))}"
            for algorithm in ALGORITHMS
        )
        workload_rows.append(
            "<tr>"
            f"<td>{escape(workload.source_kind)}</td>"
            f"<td><code>{escape(workload.name)}</code><div class=\"muted\">len {run['reference_length']}</div><div class=\"muted\">{escape(workload.reference_source)}</div></td>"
            f"<td>{escape(workload.description)}</td>"
            f"<td>{escape('/'.join(algorithm.upper() for algorithm in run['best_rate_winners']))}<div class=\"muted\">{escape(format_percentage(run['best_average_fault_rate']))}</div><div class=\"muted\">WSClock writes {run['average_wsclock_writebacks']:.2f}</div></td>"
            f"<td>{'yes' if run['fifo_has_anomaly'] else 'no'}</td>"
            f"<td>{len(run['non_fifo_violations'])}</td>"
            f"<td>{rate_cells}</td>"
            "</tr>"
        )

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Page Replacement Aggregate Dashboard</title>
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
      main {{ max-width: 1480px; margin: 0 auto; padding: 32px 20px 64px; }}
      h1, h2, h3, p {{ margin-top: 0; }}
      a {{ color: var(--accent); }}
      code {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p {{ color: var(--muted); max-width: 960px; }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0; padding: 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; }}
      .summary-grid strong {{ display: block; font-size: 1.35rem; margin-bottom: 6px; }}
      .downloads {{ color: var(--muted); }}
      .panel {{ padding: 20px; margin-bottom: 24px; overflow: auto; }}
      .chart img {{ width: 100%; height: auto; min-width: 900px; display: block; border-radius: 18px; border: 1px solid var(--border); background: #fff; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      .muted {{ color: var(--muted); margin-top: 4px; font-size: 0.92rem; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>Page Replacement Aggregate Dashboard</h1>
        <p>Cross-workload summary for <code>page-replacement-lab</code>. This dashboard normalizes page faults by reference length so compact presets, heavier benchmark traces, and imported custom traces can share the same slide-ready comparison chart.</p>
        <ul class="summary-grid">
          <li><strong>{summary['workload_count']}</strong> workloads</li>
          <li><strong>{summary['benchmark_count']}</strong> trace benchmarks</li>
          <li><strong>{summary['custom_count']}</strong> custom traces</li>
          <li><strong>{min_frames}–{max_frames}</strong> frame range</li>
          <li><strong>{'/'.join(algorithm.upper() for algorithm in summary['overall_best_rate_winners'])}</strong> overall normalized winner</li>
          <li><strong>{summary['fifo_anomaly_count']}</strong> FIFO anomaly workloads</li>
          <li><strong>{escape(aggregate_runs[0]['payload']['wsclock_window_description']) if aggregate_runs else 'n/a'}</strong> WSClock τ</li>
          <li><strong>{escape(aggregate_runs[0]['payload']['dirty_page_description']) if aggregate_runs else 'n/a'}</strong> dirty pages</li>
          <li><strong>{summary['overall_average_wsclock_writebacks']:.2f}</strong> avg WSClock writebacks</li>
          <li><strong>Winner tally</strong>{escape(winner_summary)}</li>
        </ul>
        <p class="downloads">Downloads: <a href="{escape(svg_filename)}">SVG chart</a> · <a href="{escape(csv_filename)}">CSV table</a> · <a href="{escape(json_filename)}">JSON payload</a></p>
      </section>
      <section class="panel chart">
        <h2>Normalized average page-fault rate chart</h2>
        <img src="{escape(svg_filename)}" alt="Normalized average page-fault rate by workload and algorithm" />
      </section>
      <section class="panel">
        <h2>Overall algorithm summary</h2>
        <table>
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Mean normalized fault rate</th>
              <th>Mean average faults</th>
            </tr>
          </thead>
          <tbody>
            {overall_rows}
          </tbody>
        </table>
      </section>
      <section class="panel">
        <h2>Workload breakdown</h2>
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Workload</th>
              <th>Description</th>
              <th>Best normalized winner</th>
              <th>FIFO anomaly</th>
              <th>Other regressions</th>
              <th>Average fault rates</th>
            </tr>
          </thead>
          <tbody>
            {''.join(workload_rows)}
          </tbody>
        </table>
      </section>
    </main>
  </body>
</html>
'''


def compute_reuse_distances(reference_string: list[int]) -> list[int | None]:
    last_seen: dict[int, int] = {}
    reuse_distances: list[int | None] = []
    for index, page in enumerate(reference_string):
        previous = last_seen.get(page)
        if previous is None:
            reuse_distances.append(None)
        else:
            reuse_distances.append(len(set(reference_string[previous + 1 : index])))
        last_seen[page] = index
    return reuse_distances


def bucket_reuse_distance(distance: int | None) -> str:
    if distance is None:
        return 'cold'
    if distance <= 2:
        return '1-2'
    if distance <= 5:
        return '3-5'
    if distance <= 9:
        return '6-9'
    return '10+'


def percentile(sorted_values: list[int], value: float) -> float:
    if not sorted_values:
        return 0.0
    index = max(0, ceil(value * len(sorted_values)) - 1)
    return float(sorted_values[index])


def summarize_trace(
    reference_string: Iterable[int],
    *,
    window_size: int = 8,
    phase_threshold: float = 0.45,
) -> dict:
    reference = list(reference_string)
    if not reference:
        raise InputError('reference string must contain at least one page')
    if window_size <= 0:
        raise InputError('window size must be positive')
    if not 0 <= phase_threshold <= 1:
        raise InputError('phase-threshold must be between 0 and 1')

    page_frequencies = Counter(reference)
    top_pages = [
        {'page': page, 'count': count}
        for page, count in sorted(page_frequencies.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]

    reuse_distances = compute_reuse_distances(reference)
    finite_reuse_distances = sorted(distance for distance in reuse_distances if distance is not None)
    bucket_order = ['cold', '1-2', '3-5', '6-9', '10+']
    bucket_counts = Counter(bucket_reuse_distance(distance) for distance in reuse_distances)

    working_set_sizes: list[int] = []
    active_window = deque()
    active_counts: Counter[int] = Counter()
    for page in reference:
        active_window.append(page)
        active_counts[page] += 1
        if len(active_window) > window_size:
            removed = active_window.popleft()
            active_counts[removed] -= 1
            if active_counts[removed] == 0:
                del active_counts[removed]
        working_set_sizes.append(len(active_counts))

    windows: list[dict] = []
    window_page_sets: list[set[int]] = []
    for start in range(0, len(reference), window_size):
        chunk = reference[start : start + window_size]
        chunk_counts = Counter(chunk)
        top_chunk_pages = [
            {'page': page, 'count': count}
            for page, count in sorted(chunk_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
        ]
        windows.append(
            {
                'window_index': len(windows) + 1,
                'start_reference': start + 1,
                'end_reference': start + len(chunk),
                'reference_count': len(chunk),
                'unique_pages': len(chunk_counts),
                'top_pages': top_chunk_pages,
            }
        )
        window_page_sets.append(set(chunk_counts))

    phase_boundaries: list[dict] = []
    unique_shift_threshold = max(2, window_size // 3)
    for previous_window, current_window, previous_pages, current_pages in zip(
        windows, windows[1:], window_page_sets, window_page_sets[1:]
    ):
        union = previous_pages | current_pages
        jaccard_similarity = len(previous_pages & current_pages) / len(union) if union else 1.0
        unique_delta = current_window['unique_pages'] - previous_window['unique_pages']
        if jaccard_similarity <= phase_threshold:
            reason = 'page-set overlap dropped sharply'
            if unique_delta >= unique_shift_threshold:
                reason += ' and the working set expanded'
            elif unique_delta <= -unique_shift_threshold:
                reason += ' and the working set contracted'
            phase_boundaries.append(
                {
                    'after_reference': previous_window['end_reference'],
                    'before_window': previous_window['window_index'],
                    'after_window': current_window['window_index'],
                    'jaccard_similarity': round(jaccard_similarity, 4),
                    'unique_pages_before': previous_window['unique_pages'],
                    'unique_pages_after': current_window['unique_pages'],
                    'reason': reason,
                }
            )

    reuse_stats = {
        'count': len(finite_reuse_distances),
        'min': min(finite_reuse_distances) if finite_reuse_distances else None,
        'median': percentile(finite_reuse_distances, 0.5) if finite_reuse_distances else None,
        'p90': percentile(finite_reuse_distances, 0.9) if finite_reuse_distances else None,
        'max': max(finite_reuse_distances) if finite_reuse_distances else None,
        'average': round(sum(finite_reuse_distances) / len(finite_reuse_distances), 3) if finite_reuse_distances else None,
    }

    return {
        'reference_string': reference,
        'reference_length': len(reference),
        'window_size': window_size,
        'phase_threshold': round(phase_threshold, 4),
        'unique_pages': len(page_frequencies),
        'first_touches': sum(distance is None for distance in reuse_distances),
        'reuses': len(finite_reuse_distances),
        'top_pages': top_pages,
        'reuse_distance_stats': reuse_stats,
        'reuse_distance_buckets': [
            {'bucket': bucket, 'count': bucket_counts.get(bucket, 0)} for bucket in bucket_order
        ],
        'working_set_stats': {
            'min': min(working_set_sizes),
            'max': max(working_set_sizes),
            'average': round(sum(working_set_sizes) / len(working_set_sizes), 3),
            'final': working_set_sizes[-1],
        },
        'windows': windows,
        'phase_boundaries': phase_boundaries,
    }


def format_trace_summary_text(payload: dict, *, reference_source: str = 'custom') -> str:
    hot_pages = ', '.join(
        f"{entry['page']}×{entry['count']}" for entry in payload['top_pages']
    ) or 'none'
    bucket_lines = [
        f"  - {entry['bucket']}: {entry['count']}" for entry in payload['reuse_distance_buckets']
    ]
    lines = [
        format_reference_source(reference_source),
        f"reference length: {payload['reference_length']}",
        f"unique pages: {payload['unique_pages']}",
        f"window size: {payload['window_size']}",
        f"first touches: {payload['first_touches']}",
        f"reuses: {payload['reuses']}",
        f"top hot pages: {hot_pages}",
    ]

    reuse_stats = payload['reuse_distance_stats']
    if reuse_stats['count']:
        lines.append(
            'reuse distance stats: '
            f"min={reuse_stats['min']} median={reuse_stats['median']:.1f} "
            f"p90={reuse_stats['p90']:.1f} max={reuse_stats['max']} avg={reuse_stats['average']:.2f}"
        )
    else:
        lines.append('reuse distance stats: no repeated pages in this workload')

    working_set = payload['working_set_stats']
    lines.append(
        'working-set size (sliding window): '
        f"min={working_set['min']} max={working_set['max']} avg={working_set['average']:.2f} final={working_set['final']}"
    )
    lines.append('reuse distance buckets:')
    lines.extend(bucket_lines)
    lines.append('window summaries:')
    for window in payload['windows']:
        top_pages = ', '.join(
            f"{entry['page']}×{entry['count']}" for entry in window['top_pages']
        ) or 'none'
        lines.append(
            f"  - window {window['window_index']} ({window['start_reference']}..{window['end_reference']}): "
            f"unique={window['unique_pages']} hot={top_pages}"
        )

    if payload['phase_boundaries']:
        lines.append('phase-boundary hints:')
        for boundary in payload['phase_boundaries']:
            lines.append(
                f"  - after ref {boundary['after_reference']}: windows {boundary['before_window']} -> {boundary['after_window']} "
                f"overlap={boundary['jaccard_similarity']:.2f} ({boundary['reason']})"
            )
    else:
        lines.append('phase-boundary hints: none detected for this window size')
    return '\n'.join(lines)


def format_trace_summary_markdown(payload: dict, *, reference_source: str = 'custom') -> str:
    reuse_stats = payload['reuse_distance_stats']
    working_set = payload['working_set_stats']
    lines = [
        '# Page Replacement Trace Summary',
        '',
        f"- workload: {describe_reference_label(reference_source)}",
        f"- reference length: {payload['reference_length']}",
        f"- unique pages: {payload['unique_pages']}",
        f"- window size: {payload['window_size']}",
        f"- first touches: {payload['first_touches']}",
        f"- reuses: {payload['reuses']}",
        f"- working-set size (sliding window): min {working_set['min']}, max {working_set['max']}, avg {working_set['average']:.2f}, final {working_set['final']}",
    ]

    if reuse_stats['count']:
        lines.append(
            f"- reuse distance stats: min {reuse_stats['min']}, median {reuse_stats['median']:.1f}, p90 {reuse_stats['p90']:.1f}, max {reuse_stats['max']}, avg {reuse_stats['average']:.2f}"
        )
    else:
        lines.append('- reuse distance stats: no repeated pages in this workload')

    lines.extend(
        [
            '',
            '## Top hot pages',
            '',
            '| Page | Hits |',
            '| ---: | ---: |',
        ]
    )
    for entry in payload['top_pages']:
        lines.append(f"| {entry['page']} | {entry['count']} |")

    lines.extend(
        [
            '',
            '## Reuse distance buckets',
            '',
            '| Bucket | Count |',
            '| :--- | ---: |',
        ]
    )
    for entry in payload['reuse_distance_buckets']:
        lines.append(f"| {entry['bucket']} | {entry['count']} |")

    lines.extend(
        [
            '',
            '## Window summaries',
            '',
            '| Window | References | Unique pages | Hottest pages |',
            '| ---: | :--- | ---: | :--- |',
        ]
    )
    for window in payload['windows']:
        hot_pages = ', '.join(
            f"{entry['page']}×{entry['count']}" for entry in window['top_pages']
        ) or 'none'
        lines.append(
            f"| {window['window_index']} | {window['start_reference']}..{window['end_reference']} | {window['unique_pages']} | {hot_pages} |"
        )

    lines.extend(['', '## Phase-boundary hints', ''])
    if payload['phase_boundaries']:
        for boundary in payload['phase_boundaries']:
            lines.append(
                f"- after reference {boundary['after_reference']}: windows {boundary['before_window']} -> {boundary['after_window']} have Jaccard overlap {boundary['jaccard_similarity']:.2f}; {boundary['reason']}."
            )
    else:
        lines.append('- none detected for this window size.')

    lines.extend(['', '## Reference string', '', '```text', ' '.join(str(page) for page in payload['reference_string']), '```'])
    return '\n'.join(lines).rstrip() + '\n'


def format_trace_summary_svg(
    payload: dict,
    *,
    reference_source: str = 'custom',
    id_prefix: str = 'page-replacement-trace-summary',
) -> str:
    width = 1360
    height = 1040
    identifier = make_safe_identifier(id_prefix)
    title_id = f"{identifier}-title"
    desc_id = f"{identifier}-desc"
    bucket_chart_left = 84
    bucket_chart_top = 302
    bucket_chart_width = 480
    bucket_chart_height = 248
    bucket_chart_bottom = bucket_chart_top + bucket_chart_height
    window_chart_left = 736
    window_chart_top = 302
    window_chart_width = 540
    window_chart_height = 248
    window_chart_bottom = window_chart_top + window_chart_height

    bucket_entries = payload['reuse_distance_buckets']
    max_bucket_count = max((entry['count'] for entry in bucket_entries), default=1) or 1
    bucket_slot_width = bucket_chart_width / max(len(bucket_entries), 1)
    bar_width = min(62.0, bucket_slot_width * 0.56)
    bucket_parts: list[str] = []
    bucket_tick_step = choose_tick_step(max_bucket_count)
    bucket_tick_max = max(bucket_tick_step, ((max_bucket_count + bucket_tick_step - 1) // bucket_tick_step) * bucket_tick_step)
    for tick in range(0, bucket_tick_max + 1, bucket_tick_step):
        y = bucket_chart_bottom - (tick / bucket_tick_max) * bucket_chart_height
        bucket_parts.append(
            f'<line x1="{bucket_chart_left}" y1="{y:.2f}" x2="{bucket_chart_left + bucket_chart_width}" y2="{y:.2f}" stroke="#d7dde8" stroke-width="1" />'
        )
        bucket_parts.append(
            f'<text x="{bucket_chart_left - 12}" y="{y + 5:.2f}" font-size="12" text-anchor="end" fill="#475569">{tick}</text>'
        )
    for index, entry in enumerate(bucket_entries):
        center_x = bucket_chart_left + (index + 0.5) * bucket_slot_width
        bar_height = (entry['count'] / bucket_tick_max) * bucket_chart_height if bucket_tick_max else 0
        x = center_x - bar_width / 2
        y = bucket_chart_bottom - bar_height
        bucket_parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{max(bar_height, 0):.2f}" rx="14" fill="#8b5cf6" />'
        )
        bucket_parts.append(
            f'<text x="{center_x:.2f}" y="{y - 10:.2f}" font-size="12" text-anchor="middle" fill="#6d28d9">{entry["count"]}</text>'
        )
        bucket_parts.append(
            f'<text x="{center_x:.2f}" y="{bucket_chart_bottom + 26}" font-size="12" text-anchor="middle" fill="#475569">{escape(entry["bucket"])}</text>'
        )

    window_entries = payload['windows']
    window_counts = [window['unique_pages'] for window in window_entries]
    max_unique_pages = max(window_counts, default=1) or 1
    window_tick_step = choose_tick_step(max_unique_pages)
    window_tick_max = max(window_tick_step, ((max_unique_pages + window_tick_step - 1) // window_tick_step) * window_tick_step)

    def window_x(index: int) -> float:
        if len(window_entries) == 1:
            return window_chart_left + window_chart_width / 2
        return window_chart_left + (index / (len(window_entries) - 1)) * window_chart_width

    def window_y(value: int) -> float:
        return window_chart_bottom - (value / window_tick_max) * window_chart_height

    window_parts: list[str] = []
    for tick in range(0, window_tick_max + 1, window_tick_step):
        y = window_y(tick)
        window_parts.append(
            f'<line x1="{window_chart_left}" y1="{y:.2f}" x2="{window_chart_left + window_chart_width}" y2="{y:.2f}" stroke="#d7dde8" stroke-width="1" />'
        )
        window_parts.append(
            f'<text x="{window_chart_left - 12}" y="{y + 5:.2f}" font-size="12" text-anchor="end" fill="#475569">{tick}</text>'
        )

    if window_entries:
        point_string = ' '.join(
            f"{window_x(index):.2f},{window_y(window['unique_pages']):.2f}"
            for index, window in enumerate(window_entries)
        )
        window_parts.append(
            f'<polyline fill="none" stroke="#2563eb" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" points="{point_string}" />'
        )
        phase_lookup = {boundary['after_window']: boundary for boundary in payload['phase_boundaries']}
        for index, window in enumerate(window_entries):
            x = window_x(index)
            y = window_y(window['unique_pages'])
            if window['window_index'] in phase_lookup:
                window_parts.append(
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="#dc2626" stroke="#ffffff" stroke-width="2" />'
                )
                boundary = phase_lookup[window['window_index']]
                window_parts.append(
                    f'<text x="{x:.2f}" y="{y - 14:.2f}" font-size="11" text-anchor="middle" fill="#991b1b">phase {boundary["before_window"]}→{boundary["after_window"]}</text>'
                )
            else:
                window_parts.append(
                    f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="#2563eb" stroke="#ffffff" stroke-width="2" />'
                )
            window_parts.append(
                f'<text x="{x:.2f}" y="{window_chart_bottom + 26}" font-size="12" text-anchor="middle" fill="#475569">W{window["window_index"]}</text>'
            )
            window_parts.append(
                f'<text x="{x:.2f}" y="{y - 12:.2f}" font-size="11" text-anchor="middle" fill="#1d4ed8">{window["unique_pages"]}</text>'
            )

    hot_page_lines = [
        f"{entry['page']}×{entry['count']}"
        for entry in payload['top_pages']
    ] or ['none']
    if payload['phase_boundaries']:
        phase_lines = [
            f"after ref {boundary['after_reference']}: W{boundary['before_window']}→W{boundary['after_window']} overlap {boundary['jaccard_similarity']:.2f}"
            for boundary in payload['phase_boundaries'][:3]
        ]
    else:
        phase_lines = ['no phase-boundary hints at this window size']

    reuse_stats = payload['reuse_distance_stats']
    reuse_summary = (
        f"min {reuse_stats['min']} · median {reuse_stats['median']:.1f} · p90 {reuse_stats['p90']:.1f} · max {reuse_stats['max']} · avg {reuse_stats['average']:.2f}"
        if reuse_stats['count']
        else 'no repeated pages in this workload'
    )
    working_set = payload['working_set_stats']
    overview_lines = [
        f"workload: {describe_reference_label(reference_source)}",
        f"reference length {payload['reference_length']} · unique pages {payload['unique_pages']} · window size {payload['window_size']}",
        f"first touches {payload['first_touches']} · reuses {payload['reuses']} · phase hints {len(payload['phase_boundaries'])}",
        f"working-set window stats: min {working_set['min']} · max {working_set['max']} · avg {working_set['average']:.2f} · final {working_set['final']}",
        f"reuse distance stats: {reuse_summary}",
    ]
    overview_text = [
        f'<text x="84" y="{90 + index * 26}" font-size="18" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(overview_lines)
    ]

    hot_page_text = [
        f'<text x="84" y="{684 + index * 24}" font-size="17" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(hot_page_lines[:5])
    ]
    phase_text = [
        f'<text x="736" y="{684 + index * 24}" font-size="17" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(phase_lines[:4])
    ]

    reference_preview = ' '.join(str(page) for page in payload['reference_string'][:32])
    if payload['reference_length'] > 32:
        reference_preview += ' …'

    return '\n'.join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
            f'  <title id="{title_id}">Page replacement trace-summary card</title>',
            f'  <desc id="{desc_id}">Trace summary charts for {escape(describe_reference_label(reference_source))}, including reuse-distance buckets, working-set window sizes, hot pages, and phase-boundary hints.</desc>',
            '  <rect width="100%" height="100%" fill="#f8fafc" />',
            '  <rect x="28" y="24" width="1304" height="992" rx="28" fill="#ffffff" stroke="#d7dde8" stroke-width="2" />',
            '  <text x="84" y="58" font-size="32" font-weight="700" fill="#0f172a">Trace summary card</text>',
            *overview_text,
            '  <rect x="64" y="252" width="540" height="338" rx="24" fill="#faf5ff" stroke="#ddd6fe" stroke-width="1.5" />',
            '  <text x="84" y="286" font-size="22" font-weight="700" fill="#5b21b6">Reuse-distance buckets</text>',
            '  <text x="84" y="574" font-size="13" fill="#475569">Cold touches dominate first-use pages; tighter buckets indicate stronger locality.</text>',
            '  <line x1="84" y1="302" x2="84" y2="550" stroke="#0f172a" stroke-width="2" />',
            '  <line x1="84" y1="550" x2="564" y2="550" stroke="#0f172a" stroke-width="2" />',
            *bucket_parts,
            '  <rect x="716" y="252" width="580" height="338" rx="24" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5" />',
            '  <text x="736" y="286" font-size="22" font-weight="700" fill="#1d4ed8">Per-window unique-page pressure</text>',
            '  <text x="736" y="574" font-size="13" fill="#475569">Red points mark windows immediately after a flagged phase-boundary hint.</text>',
            '  <line x1="736" y1="302" x2="736" y2="550" stroke="#0f172a" stroke-width="2" />',
            '  <line x1="736" y1="550" x2="1276" y2="550" stroke="#0f172a" stroke-width="2" />',
            *window_parts,
            '  <rect x="64" y="610" width="580" height="176" rx="24" fill="#f8fafc" stroke="#d7dde8" stroke-width="1.5" />',
            '  <text x="84" y="646" font-size="22" font-weight="700" fill="#0f172a">Top hot pages</text>',
            *hot_page_text,
            '  <rect x="716" y="610" width="580" height="176" rx="24" fill="#f8fafc" stroke="#d7dde8" stroke-width="1.5" />',
            '  <text x="736" y="646" font-size="22" font-weight="700" fill="#0f172a">Phase-boundary hints</text>',
            *phase_text,
            '  <rect x="64" y="816" width="1232" height="152" rx="24" fill="#eef2ff" stroke="#c7d2fe" stroke-width="1.5" />',
            '  <text x="84" y="850" font-size="22" font-weight="700" fill="#1e3a8a">Reference preview</text>',
            f'  <text x="84" y="888" font-size="16" fill="#0f172a">{escape(reference_preview)}</text>',
            f'  <text x="84" y="920" font-size="15" fill="#475569">source: {escape(reference_source)} · exported window size {payload["window_size"]} · phase threshold {payload["phase_threshold"]:.2f}</text>',
            '  <text x="84" y="948" font-size="15" fill="#475569">Use the Markdown / JSON companions for the full reference string, bucket tables, and all phase-hint details.</text>',
            '</svg>',
        ]
    )


def format_trace_summary_html(
    payload: dict,
    *,
    reference_source: str = 'custom',
    inline_svg: str,
    downloads: list[tuple[str, str]] | None = None,
) -> str:
    downloads = downloads or []
    download_links = ' · '.join(
        f'<a href="{escape(path)}">{escape(label)}</a>' for label, path in downloads
    ) or 'inline card only'
    hot_page_rows = ''.join(
        f"<tr><td><code>{entry['page']}</code></td><td>{entry['count']}</td></tr>"
        for entry in payload['top_pages']
    )
    bucket_rows = ''.join(
        f"<tr><td><code>{escape(entry['bucket'])}</code></td><td>{entry['count']}</td></tr>"
        for entry in payload['reuse_distance_buckets']
    )
    window_rows = ''.join(
        '<tr>'
        f"<td>{window['window_index']}</td>"
        f"<td>{window['start_reference']}..{window['end_reference']}</td>"
        f"<td>{window['unique_pages']}</td>"
        f"<td>{escape(', '.join(f"{entry['page']}×{entry['count']}" for entry in window['top_pages']) or 'none')}</td>"
        '</tr>'
        for window in payload['windows']
    )
    if payload['phase_boundaries']:
        phase_items = ''.join(
            '<li>'
            f"after reference {boundary['after_reference']}: windows {boundary['before_window']} → {boundary['after_window']} have Jaccard overlap {boundary['jaccard_similarity']:.2f}; {escape(boundary['reason'])}."
            '</li>'
            for boundary in payload['phase_boundaries']
        )
    else:
        phase_items = '<li>none detected for this window size.</li>'

    working_set = payload['working_set_stats']
    reuse_stats = payload['reuse_distance_stats']
    reuse_line = (
        f"min {reuse_stats['min']}, median {reuse_stats['median']:.1f}, p90 {reuse_stats['p90']:.1f}, max {reuse_stats['max']}, avg {reuse_stats['average']:.2f}"
        if reuse_stats['count']
        else 'no repeated pages in this workload'
    )
    reference_string = ' '.join(str(page) for page in payload['reference_string'])

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Page Replacement Trace Summary</title>
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
      code, pre {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p, .muted {{ color: var(--muted); }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0 0; padding: 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; }}
      .summary-grid strong {{ display: block; font-size: 1.35rem; margin-bottom: 6px; }}
      .panel {{ padding: 20px; margin-bottom: 24px; overflow: auto; }}
      .chart svg {{ width: 100%; height: auto; min-width: 960px; display: block; }}
      .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      ul {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      li + li {{ margin-top: 8px; }}
      pre {{ background: #0f172a; color: #e2e8f0; padding: 18px; border-radius: 18px; overflow-x: auto; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>Page Replacement Trace Summary</h1>
        <p>Portfolio-ready trace diagnostics for <code>{escape(describe_reference_label(reference_source))}</code>. The inline card summarizes locality, working-set pressure, and phase-shift hints, while the tables keep the underlying metrics easy to inspect or reuse later.</p>
        <ul class="summary-grid">
          <li><strong>{payload['reference_length']}</strong> references</li>
          <li><strong>{payload['unique_pages']}</strong> unique pages</li>
          <li><strong>{payload['window_size']}</strong> window size</li>
          <li><strong>{payload['first_touches']}</strong> first touches</li>
          <li><strong>{payload['reuses']}</strong> reuses</li>
          <li><strong>{len(payload['phase_boundaries'])}</strong> phase hints</li>
        </ul>
        <p class="muted">Downloads: {download_links}</p>
      </section>
      <section class="panel chart">
        <h2>Trace summary card</h2>
        {inline_svg}
      </section>
      <section class="panel">
        <h2>Summary metrics</h2>
        <div class="meta-grid">
          <div>
            <h3>Reuse distance</h3>
            <p class="muted">{escape(reuse_line)}</p>
          </div>
          <div>
            <h3>Working-set window</h3>
            <p class="muted">min {working_set['min']}, max {working_set['max']}, avg {working_set['average']:.2f}, final {working_set['final']}</p>
          </div>
        </div>
      </section>
      <section class="panel">
        <h2>Hot pages and reuse buckets</h2>
        <div class="meta-grid">
          <div>
            <table>
              <thead><tr><th>Page</th><th>Touches</th></tr></thead>
              <tbody>{hot_page_rows}</tbody>
            </table>
          </div>
          <div>
            <table>
              <thead><tr><th>Bucket</th><th>Count</th></tr></thead>
              <tbody>{bucket_rows}</tbody>
            </table>
          </div>
        </div>
      </section>
      <section class="panel">
        <h2>Window summaries</h2>
        <table>
          <thead><tr><th>Window</th><th>References</th><th>Unique pages</th><th>Hottest pages</th></tr></thead>
          <tbody>{window_rows}</tbody>
        </table>
      </section>
      <section class="panel">
        <h2>Phase-boundary hints</h2>
        <ul>{phase_items}</ul>
      </section>
      <section class="panel">
        <h2>Reference string</h2>
        <pre>{escape(reference_string)}</pre>
      </section>
    </main>
  </body>
</html>
'''


def build_trace_compare_payload(
    left_workload: GalleryWorkload,
    right_workload: GalleryWorkload,
    *,
    min_frames: int,
    max_frames: int,
    window_size: int,
    phase_threshold: float,
    wsclock_window: int | None,
    dirty_pages: Iterable[int] | None,
) -> dict:
    left_study = study_frame_counts(
        left_workload.reference_string,
        min_frames,
        max_frames,
        wsclock_window=wsclock_window,
        dirty_pages=dirty_pages,
    )
    left_study["reference_source"] = left_workload.reference_source
    right_study = study_frame_counts(
        right_workload.reference_string,
        min_frames,
        max_frames,
        wsclock_window=wsclock_window,
        dirty_pages=dirty_pages,
    )
    right_study["reference_source"] = right_workload.reference_source

    left_trace_summary = summarize_trace(
        left_workload.reference_string,
        window_size=window_size,
        phase_threshold=phase_threshold,
    )
    left_trace_summary["reference_source"] = left_workload.reference_source
    right_trace_summary = summarize_trace(
        right_workload.reference_string,
        window_size=window_size,
        phase_threshold=phase_threshold,
    )
    right_trace_summary["reference_source"] = right_workload.reference_source

    left_average_faults = summarize_fault_averages(left_study)
    right_average_faults = summarize_fault_averages(right_study)
    left_average_fault_rates = {
        algorithm: left_average_faults[algorithm] / len(left_workload.reference_string)
        for algorithm in ALGORITHMS
    }
    right_average_fault_rates = {
        algorithm: right_average_faults[algorithm] / len(right_workload.reference_string)
        for algorithm in ALGORITHMS
    }

    left_best_average_faults = min(left_average_faults.values())
    right_best_average_faults = min(right_average_faults.values())
    left_best_average_winners = select_lowest_keys(left_average_faults)
    right_best_average_winners = select_lowest_keys(right_average_faults)

    algorithm_summaries: list[dict] = []
    left_average_wsclock_writebacks = summarize_wsclock_writeback_average(left_study)
    right_average_wsclock_writebacks = summarize_wsclock_writeback_average(right_study)
    for algorithm in ALGORITHMS:
        fault_delta = round(
            right_average_faults[algorithm] - left_average_faults[algorithm],
            6,
        )
        rate_delta = round(
            right_average_fault_rates[algorithm] - left_average_fault_rates[algorithm],
            6,
        )
        if abs(fault_delta) <= 1e-12:
            better = "tie"
        elif fault_delta > 0:
            better = "left"
        else:
            better = "right"
        algorithm_summaries.append(
            {
                "algorithm": algorithm,
                "left_average_faults": round(left_average_faults[algorithm], 6),
                "right_average_faults": round(right_average_faults[algorithm], 6),
                "fault_delta_right_minus_left": fault_delta,
                "left_average_fault_rate": round(left_average_fault_rates[algorithm], 6),
                "right_average_fault_rate": round(right_average_fault_rates[algorithm], 6),
                "left_average_writebacks": round(
                    left_average_wsclock_writebacks if algorithm == "wsclock" else 0.0,
                    6,
                ),
                "right_average_writebacks": round(
                    right_average_wsclock_writebacks if algorithm == "wsclock" else 0.0,
                    6,
                ),
                "fault_rate_delta_right_minus_left": rate_delta,
                "better_average_faults": better,
            }
        )

    frame_comparisons: list[dict] = []
    for left_row, right_row in zip(
        left_study["frame_results"],
        right_study["frame_results"],
        strict=True,
    ):
        left_faults = {
            algorithm: left_row["algorithms"][algorithm]["page_faults"]
            for algorithm in ALGORITHMS
        }
        right_faults = {
            algorithm: right_row["algorithms"][algorithm]["page_faults"]
            for algorithm in ALGORITHMS
        }
        algorithm_rows: dict[str, dict] = {}
        for algorithm in ALGORITHMS:
            fault_delta = right_faults[algorithm] - left_faults[algorithm]
            if fault_delta == 0:
                better = "tie"
            elif fault_delta > 0:
                better = "left"
            else:
                better = "right"
            algorithm_rows[algorithm] = {
                "left_faults": left_faults[algorithm],
                "right_faults": right_faults[algorithm],
                "fault_delta_right_minus_left": fault_delta,
                "left_hit_rate": left_row["algorithms"][algorithm]["hit_rate"],
                "right_hit_rate": right_row["algorithms"][algorithm]["hit_rate"],
                "left_writebacks": left_row["algorithms"][algorithm]["writebacks"],
                "right_writebacks": right_row["algorithms"][algorithm]["writebacks"],
                "better": better,
            }
        frame_comparisons.append(
            {
                "frame_count": left_row["frame_count"],
                "wsclock_window": left_row["wsclock_window"],
                "left_best_algorithms": select_lowest_keys(left_faults),
                "right_best_algorithms": select_lowest_keys(right_faults),
                "algorithms": algorithm_rows,
            }
        )

    overall_left_rate = sum(left_average_fault_rates.values()) / len(ALGORITHMS)
    overall_right_rate = sum(right_average_fault_rates.values()) / len(ALGORITHMS)
    if abs(overall_left_rate - overall_right_rate) <= 1e-12:
        overall_better = "tie"
    elif overall_left_rate < overall_right_rate:
        overall_better = "left"
    else:
        overall_better = "right"

    largest_gap = max(
        algorithm_summaries,
        key=lambda entry: abs(entry["fault_delta_right_minus_left"]),
    )

    return {
        "min_frames": min_frames,
        "max_frames": max_frames,
        "window_size": window_size,
        "phase_threshold": round(phase_threshold, 4),
        "wsclock_window_mode": left_study["wsclock_window_mode"],
        "wsclock_window_override": left_study["wsclock_window_override"],
        "wsclock_window_description": left_study["wsclock_window_description"],
        "dirty_pages": left_study["dirty_pages"],
        "dirty_page_count": left_study["dirty_page_count"],
        "dirty_page_description": left_study["dirty_page_description"],
        "left": {
            "workload": left_workload.name,
            "description": left_workload.description,
            "reference_source": left_workload.reference_source,
            "reference_length": len(left_workload.reference_string),
            "reference_string": list(left_workload.reference_string),
            "study": left_study,
            "trace_summary": left_trace_summary,
            "average_faults": {
                algorithm: round(value, 6)
                for algorithm, value in left_average_faults.items()
            },
            "average_fault_rates": {
                algorithm: round(value, 6)
                for algorithm, value in left_average_fault_rates.items()
            },
            "best_average_faults": round(left_best_average_faults, 6),
            "best_average_winners": left_best_average_winners,
            "fifo_anomaly_count": len(left_study["fifo_belady_anomalies"]),
            "non_fifo_regression_count": sum(
                1
                for violation in left_study["monotonicity_violations"]
                if violation["algorithm"] != "fifo"
            ),
        },
        "right": {
            "workload": right_workload.name,
            "description": right_workload.description,
            "reference_source": right_workload.reference_source,
            "reference_length": len(right_workload.reference_string),
            "reference_string": list(right_workload.reference_string),
            "study": right_study,
            "trace_summary": right_trace_summary,
            "average_faults": {
                algorithm: round(value, 6)
                for algorithm, value in right_average_faults.items()
            },
            "average_fault_rates": {
                algorithm: round(value, 6)
                for algorithm, value in right_average_fault_rates.items()
            },
            "best_average_faults": round(right_best_average_faults, 6),
            "best_average_winners": right_best_average_winners,
            "fifo_anomaly_count": len(right_study["fifo_belady_anomalies"]),
            "non_fifo_regression_count": sum(
                1
                for violation in right_study["monotonicity_violations"]
                if violation["algorithm"] != "fifo"
            ),
        },
        "algorithm_summaries": algorithm_summaries,
        "frame_comparisons": frame_comparisons,
        "summary": {
            "overall_better_average_fault_rate": overall_better,
            "largest_average_fault_gap": {
                "algorithm": largest_gap["algorithm"],
                "better_average_faults": largest_gap["better_average_faults"],
                "fault_delta_right_minus_left": largest_gap[
                    "fault_delta_right_minus_left"
                ],
            },
            "left_phase_hint_count": len(left_trace_summary["phase_boundaries"]),
            "right_phase_hint_count": len(right_trace_summary["phase_boundaries"]),
            "left_fifo_anomaly_count": len(left_study["fifo_belady_anomalies"]),
            "right_fifo_anomaly_count": len(right_study["fifo_belady_anomalies"]),
            "left_non_fifo_regression_count": sum(
                1
                for violation in left_study["monotonicity_violations"]
                if violation["algorithm"] != "fifo"
            ),
            "right_non_fifo_regression_count": sum(
                1
                for violation in right_study["monotonicity_violations"]
                if violation["algorithm"] != "fifo"
            ),
        },
    }


def write_trace_compare_csv(path: Path, payload: dict) -> None:
    ensure_output_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "frame_count",
                "wsclock_window",
                "algorithm",
                "left_workload",
                "right_workload",
                "left_faults",
                "right_faults",
                "fault_delta_right_minus_left",
                "left_hit_rate",
                "right_hit_rate",
                "left_writebacks",
                "right_writebacks",
                "better",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for frame in payload["frame_comparisons"]:
            for algorithm in ALGORITHMS:
                entry = frame["algorithms"][algorithm]
                writer.writerow(
                    {
                        "frame_count": frame["frame_count"],
                        "wsclock_window": frame["wsclock_window"],
                        "algorithm": algorithm,
                        "left_workload": payload["left"]["workload"],
                        "right_workload": payload["right"]["workload"],
                        "left_faults": entry["left_faults"],
                        "right_faults": entry["right_faults"],
                        "fault_delta_right_minus_left": entry[
                            "fault_delta_right_minus_left"
                        ],
                        "left_hit_rate": entry["left_hit_rate"],
                        "right_hit_rate": entry["right_hit_rate"],
                        "left_writebacks": entry["left_writebacks"],
                        "right_writebacks": entry["right_writebacks"],
                        "better": entry["better"],
                    }
                )


def format_trace_compare_markdown(payload: dict) -> str:
    left = payload["left"]
    right = payload["right"]
    lines = [
        "# Page Replacement Imported Trace Comparison",
        "",
        f"- left trace: {describe_reference_label(left['reference_source'])}",
        f"- right trace: {describe_reference_label(right['reference_source'])}",
        f"- frame range: {payload['min_frames']} to {payload['max_frames']}",
        f"- window size: {payload['window_size']}",
        f"- phase threshold: {payload['phase_threshold']:.2f}",
        f"- WSClock window: {payload['wsclock_window_description']}",
        f"- dirty pages: {payload['dirty_page_description']}",
        "",
        "## Trace overview",
        "",
        "| Trace | References | Unique pages | Working-set avg | Phase hints | Best average faults |",
        "| :--- | ---: | ---: | ---: | ---: | :--- |",
        (
            f"| {left['workload']} | {left['reference_length']} | {left['trace_summary']['unique_pages']} | "
            f"{left['trace_summary']['working_set_stats']['average']:.2f} | {len(left['trace_summary']['phase_boundaries'])} | "
            f"{'/'.join(algorithm.upper() for algorithm in left['best_average_winners'])} ({left['best_average_faults']:.2f}) |"
        ),
        (
            f"| {right['workload']} | {right['reference_length']} | {right['trace_summary']['unique_pages']} | "
            f"{right['trace_summary']['working_set_stats']['average']:.2f} | {len(right['trace_summary']['phase_boundaries'])} | "
            f"{'/'.join(algorithm.upper() for algorithm in right['best_average_winners'])} ({right['best_average_faults']:.2f}) |"
        ),
        "",
        "## Average algorithm comparison",
        "",
        "| Algorithm | Left avg faults | Right avg faults | Δ right-left | Better avg | Left avg fault rate | Right avg fault rate | Left avg writebacks | Right avg writebacks |",
        "| :--- | ---: | ---: | ---: | :--- | ---: | ---: | ---: | ---: |",
    ]
    for entry in payload["algorithm_summaries"]:
        lines.append(
            f"| {entry['algorithm'].upper()} | {entry['left_average_faults']:.2f} | {entry['right_average_faults']:.2f} | "
            f"{entry['fault_delta_right_minus_left']:.2f} | {entry['better_average_faults']} | "
            f"{format_percentage(entry['left_average_fault_rate'])} | {format_percentage(entry['right_average_fault_rate'])} | "
            f"{entry['left_average_writebacks']:.2f} | {entry['right_average_writebacks']:.2f} |"
        )

    lines.extend(
        [
            "",
            f"- WSClock average writebacks: left {summarize_wsclock_writeback_average(left['study']):.2f}, right {summarize_wsclock_writeback_average(right['study']):.2f}",
        ]
    )

    frame_header_cells = ["Frames", "WSClock τ", "Left winner", "Right winner", *[f"{algorithm.upper()} L/R" for algorithm in ALGORITHMS]]
    frame_separator_cells = ["---:", "---:", ":---", ":---", *[":---" for _ in ALGORITHMS]]
    lines.extend(
        [
            "",
            "## Frame-by-frame comparison",
            "",
            f"| {' | '.join(frame_header_cells)} |",
            f"| {' | '.join(frame_separator_cells)} |",
        ]
    )
    for frame in payload["frame_comparisons"]:
        frame_fault_pairs = [
            f"{frame['algorithms'][algorithm]['left_faults']}/{frame['algorithms'][algorithm]['right_faults']}"
            for algorithm in ALGORITHMS
        ]
        lines.append(
            f"| {frame['frame_count']} | {frame['wsclock_window']} | {'/'.join(algorithm.upper() for algorithm in frame['left_best_algorithms'])} | "
            f"{'/'.join(algorithm.upper() for algorithm in frame['right_best_algorithms'])} | "
            f"{' | '.join(frame_fault_pairs)} |"
        )

    def add_trace_snapshot(label: str, trace_payload: dict) -> None:
        reuse_stats = trace_payload["reuse_distance_stats"]
        working_set = trace_payload["working_set_stats"]
        if reuse_stats["count"]:
            reuse_line = (
                f"min {reuse_stats['min']}, median {reuse_stats['median']:.1f}, p90 {reuse_stats['p90']:.1f}, "
                f"max {reuse_stats['max']}, avg {reuse_stats['average']:.2f}"
            )
        else:
            reuse_line = "no repeated pages in this workload"
        hot_pages = ", ".join(
            f"{entry['page']}×{entry['count']}" for entry in trace_payload["top_pages"]
        ) or "none"
        lines.extend(
            [
                "",
                f"## {label} locality snapshot",
                "",
                f"- working-set size: min {working_set['min']}, max {working_set['max']}, avg {working_set['average']:.2f}, final {working_set['final']}",
                f"- reuse distance: {reuse_line}",
                f"- hot pages: {hot_pages}",
            ]
        )
        if trace_payload["phase_boundaries"]:
            lines.append("- phase-boundary hints:")
            for boundary in trace_payload["phase_boundaries"][:4]:
                lines.append(
                    f"  - after reference {boundary['after_reference']}: windows {boundary['before_window']} -> {boundary['after_window']} overlap {boundary['jaccard_similarity']:.2f}; {boundary['reason']}."
                )
        else:
            lines.append("- phase-boundary hints: none detected for this window size.")

    add_trace_snapshot(left["workload"], left["trace_summary"])
    add_trace_snapshot(right["workload"], right["trace_summary"])

    lines.extend(
        [
            "",
            f"## {left['workload']} reference string",
            "",
            "```text",
            " ".join(str(page) for page in left["reference_string"]),
            "```",
            "",
            f"## {right['workload']} reference string",
            "",
            "```text",
            " ".join(str(page) for page in right["reference_string"]),
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def format_trace_compare_svg(
    payload: dict,
    *,
    id_prefix: str = "page-replacement-trace-compare",
) -> str:
    width = 1480
    height = 1120
    identifier = make_safe_identifier(id_prefix)
    title_id = f"{identifier}-title"
    desc_id = f"{identifier}-desc"
    left = payload["left"]
    right = payload["right"]

    chart_left = 120
    chart_top = 410
    chart_width = 1180
    chart_height = 300
    chart_bottom = chart_top + chart_height
    left_color = "#2563eb"
    right_color = "#7c3aed"

    percent_values = [
        entry["left_average_fault_rate"] * 100 for entry in payload["algorithm_summaries"]
    ] + [
        entry["right_average_fault_rate"] * 100 for entry in payload["algorithm_summaries"]
    ]
    max_percent = max(percent_values, default=1.0)
    percent_ceiling = max(1, ceil(max_percent))
    tick_step = choose_tick_step(percent_ceiling)
    tick_max = max(tick_step, ((percent_ceiling + tick_step - 1) // tick_step) * tick_step)

    def chart_y(value: float) -> float:
        return chart_bottom - (value / tick_max) * chart_height

    grid_parts: list[str] = []
    for tick in range(0, tick_max + 1, tick_step):
        y = chart_y(tick)
        grid_parts.append(
            f'<line x1="{chart_left}" y1="{y:.2f}" x2="{chart_left + chart_width}" y2="{y:.2f}" stroke="#d7dde8" stroke-width="1" />'
        )
        grid_parts.append(
            f'<text x="{chart_left - 16}" y="{y + 5:.2f}" font-size="12" text-anchor="end" fill="#475569">{tick}%</text>'
        )

    group_width = chart_width / len(ALGORITHMS)
    bar_width = min(74.0, group_width * 0.24)
    bar_gap = bar_width * 0.45
    bar_parts: list[str] = []
    for index, entry in enumerate(payload["algorithm_summaries"]):
        group_center = chart_left + (index + 0.5) * group_width
        left_percent = entry["left_average_fault_rate"] * 100
        right_percent = entry["right_average_fault_rate"] * 100
        for offset, percent, color in (
            (-(bar_width / 2 + bar_gap / 2), left_percent, left_color),
            ((bar_width / 2 + bar_gap / 2), right_percent, right_color),
        ):
            x = group_center + offset - bar_width / 2
            y = chart_y(percent)
            height_value = chart_bottom - y
            bar_parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{height_value:.2f}" rx="16" fill="{color}" />'
            )
            bar_parts.append(
                f'<text x="{group_center + offset:.2f}" y="{y - 10:.2f}" font-size="12" text-anchor="middle" fill="{color}">{percent:.1f}%</text>'
            )
        bar_parts.append(
            f'<text x="{group_center:.2f}" y="{chart_bottom + 28}" font-size="13" text-anchor="middle" fill="#475569">{entry["algorithm"].upper()}</text>'
        )

    def build_overview_lines(trace_payload: dict) -> list[str]:
        reuse_stats = trace_payload["trace_summary"]["reuse_distance_stats"]
        working_set = trace_payload["trace_summary"]["working_set_stats"]
        reuse_line = (
            f"reuse median {reuse_stats['median']:.1f} · p90 {reuse_stats['p90']:.1f}"
            if reuse_stats["count"]
            else "reuse median n/a · no repeated pages"
        )
        return [
            trace_payload["workload"],
            f"refs {trace_payload['reference_length']} · unique {trace_payload['trace_summary']['unique_pages']} · phase hints {len(trace_payload['trace_summary']['phase_boundaries'])}",
            f"working-set avg {working_set['average']:.2f} · final {working_set['final']} · {reuse_line}",
            f"best avg {'/'.join(algorithm.upper() for algorithm in trace_payload['best_average_winners'])} ({trace_payload['best_average_faults']:.2f})",
            f"FIFO anomalies {trace_payload['fifo_anomaly_count']} · other regressions {trace_payload['non_fifo_regression_count']}",
        ]

    left_overview = [
        f'<text x="92" y="{156 + index * 28}" font-size="18" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(build_overview_lines(left))
    ]
    right_overview = [
        f'<text x="748" y="{156 + index * 28}" font-size="18" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(build_overview_lines(right))
    ]

    algorithm_lines = []
    for entry in payload["algorithm_summaries"]:
        better = entry["better_average_faults"]
        if better == "left":
            better_label = left["workload"]
        elif better == "right":
            better_label = right["workload"]
        else:
            better_label = "tie"
        algorithm_lines.append(
            f"{entry['algorithm'].upper()}: {entry['left_average_faults']:.2f} vs {entry['right_average_faults']:.2f} avg faults → {better_label}"
        )
    algorithm_text = [
        f'<text x="92" y="{858 + index * 28}" font-size="18" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(algorithm_lines)
    ]

    left_frame_winners = ", ".join(
        f"{frame['frame_count']}:{'/'.join(algorithm.upper() for algorithm in frame['left_best_algorithms'])}"
        for frame in payload["frame_comparisons"]
    )
    right_frame_winners = ", ".join(
        f"{frame['frame_count']}:{'/'.join(algorithm.upper() for algorithm in frame['right_best_algorithms'])}"
        for frame in payload["frame_comparisons"]
    )
    largest_gap = payload["summary"]["largest_average_fault_gap"]
    if largest_gap["better_average_faults"] == "left":
        largest_gap_winner = left["workload"]
    elif largest_gap["better_average_faults"] == "right":
        largest_gap_winner = right["workload"]
    else:
        largest_gap_winner = "tie"
    overall_better = payload["summary"]["overall_better_average_fault_rate"]
    if overall_better == "left":
        overall_label = left["workload"]
    elif overall_better == "right":
        overall_label = right["workload"]
    else:
        overall_label = "tie"
    comparison_lines = [
        f"frame range {payload['min_frames']}–{payload['max_frames']} · window size {payload['window_size']} · phase threshold {payload['phase_threshold']:.2f}",
        f"lower normalized overall average fault rate: {overall_label}",
        f"largest average gap: {largest_gap['algorithm'].upper()} → {largest_gap_winner} ({abs(largest_gap['fault_delta_right_minus_left']):.2f} faults)",
        f"phase hints: left {payload['summary']['left_phase_hint_count']} · right {payload['summary']['right_phase_hint_count']}",
        f"left winners by frame: {left_frame_winners}",
        f"right winners by frame: {right_frame_winners}",
    ]
    comparison_text = [
        f'<text x="748" y="{858 + index * 28}" font-size="18" fill="#0f172a">{escape(line)}</text>'
        for index, line in enumerate(comparison_lines)
    ]

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id} {desc_id}">',
            f'  <title id="{title_id}">Page replacement imported-trace comparison card</title>',
            f'  <desc id="{desc_id}">Side-by-side average fault-rate comparison for imported traces {escape(left["workload"])} and {escape(right["workload"])}.</desc>',
            '  <rect width="100%" height="100%" fill="#f8fafc" />',
            '  <rect x="28" y="24" width="1424" height="1072" rx="28" fill="#ffffff" stroke="#d7dde8" stroke-width="2" />',
            '  <text x="72" y="62" font-size="32" font-weight="700" fill="#0f172a">Imported trace comparison card</text>',
            '  <text x="72" y="96" font-size="18" fill="#475569">Compare exactly two custom traces side by side across the same frame sweep for portfolio-ready memory-management storytelling.</text>',
            '  <rect x="64" y="118" width="620" height="236" rx="24" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5" />',
            f'  <text x="92" y="146" font-size="22" font-weight="700" fill="{left_color}">Left trace</text>',
            *left_overview,
            '  <rect x="720" y="118" width="620" height="236" rx="24" fill="#f5f3ff" stroke="#ddd6fe" stroke-width="1.5" />',
            f'  <text x="748" y="146" font-size="22" font-weight="700" fill="{right_color}">Right trace</text>',
            *right_overview,
            '  <rect x="64" y="378" width="1312" height="372" rx="24" fill="#f8fafc" stroke="#d7dde8" stroke-width="1.5" />',
            '  <text x="92" y="410" font-size="24" font-weight="700" fill="#0f172a">Average page-fault rate by algorithm</text>',
            '  <text x="92" y="438" font-size="14" fill="#475569">Blue bars show the left trace. Purple bars show the right trace. Lower is better because it means fewer page faults per reference.</text>',
            f'  <line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="2" />',
            f'  <line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_left + chart_width}" y2="{chart_bottom}" stroke="#0f172a" stroke-width="2" />',
            *grid_parts,
            *bar_parts,
            f'  <text x="{chart_left + chart_width / 2:.2f}" y="{chart_bottom + 60}" font-size="14" text-anchor="middle" fill="#475569">Algorithms</text>',
            f'  <text x="48" y="{chart_top + chart_height / 2:.2f}" font-size="14" fill="#475569" transform="rotate(-90 48 {chart_top + chart_height / 2:.2f})">Average page-fault rate</text>',
            f'  <circle cx="1098" cy="92" r="8" fill="{left_color}" />',
            f'  <text x="1114" y="98" font-size="15" fill="#0f172a">{escape(left["workload"])}</text>',
            f'  <circle cx="1238" cy="92" r="8" fill="{right_color}" />',
            f'  <text x="1254" y="98" font-size="15" fill="#0f172a">{escape(right["workload"])}</text>',
            '  <rect x="64" y="796" width="620" height="256" rx="24" fill="#f8fafc" stroke="#d7dde8" stroke-width="1.5" />',
            '  <text x="92" y="832" font-size="22" font-weight="700" fill="#0f172a">Algorithm gaps</text>',
            *algorithm_text,
            '  <rect x="720" y="796" width="620" height="256" rx="24" fill="#eef2ff" stroke="#c7d2fe" stroke-width="1.5" />',
            '  <text x="748" y="832" font-size="22" font-weight="700" fill="#1e3a8a">Overall comparison</text>',
            *comparison_text,
            '</svg>',
        ]
    )


def format_trace_compare_html(
    payload: dict,
    *,
    inline_svg: str,
    downloads: list[tuple[str, str]] | None = None,
) -> str:
    downloads = downloads or []
    download_links = ' · '.join(
        f'<a href="{escape(path)}">{escape(label)}</a>' for label, path in downloads
    ) or 'inline card only'

    algorithm_rows = ''.join(
        '<tr>'
        f'<td><code>{escape(entry["algorithm"].upper())}</code></td>'
        f'<td>{entry["left_average_faults"]:.2f}</td>'
        f'<td>{entry["right_average_faults"]:.2f}</td>'
        f'<td>{entry["fault_delta_right_minus_left"]:.2f}</td>'
        f'<td>{escape(entry["better_average_faults"])}</td>'
        f'<td>{escape(format_percentage(entry["left_average_fault_rate"]))}</td>'
        f'<td>{escape(format_percentage(entry["right_average_fault_rate"]))}</td>'
        f'<td>{entry["left_average_writebacks"]:.2f}</td>'
        f'<td>{entry["right_average_writebacks"]:.2f}</td>'
        '</tr>'
        for entry in payload['algorithm_summaries']
    )

    frame_rows = ''.join(
        '<tr>'
        f'<td>{frame["frame_count"]}</td>'
        f'<td>{frame["wsclock_window"]}</td>'
        f'<td>{escape("/".join(algorithm.upper() for algorithm in frame["left_best_algorithms"]))}</td>'
        f'<td>{escape("/".join(algorithm.upper() for algorithm in frame["right_best_algorithms"]))}</td>'
        + ''.join(
            f'<td>{frame["algorithms"][algorithm]["left_faults"]}/{frame["algorithms"][algorithm]["right_faults"]}</td>'
            for algorithm in ALGORITHMS
        )
        + '</tr>'
        for frame in payload['frame_comparisons']
    )

    frame_header_cells = ''.join(
        f'<th>{escape(algorithm.upper())} L/R</th>'
        for algorithm in ALGORITHMS
    )

    def render_trace_panel(title: str, trace_payload: dict) -> str:
        working_set = trace_payload['trace_summary']['working_set_stats']
        reuse_stats = trace_payload['trace_summary']['reuse_distance_stats']
        reuse_line = (
            f"min {reuse_stats['min']}, median {reuse_stats['median']:.1f}, p90 {reuse_stats['p90']:.1f}, max {reuse_stats['max']}, avg {reuse_stats['average']:.2f}"
            if reuse_stats['count']
            else 'no repeated pages in this workload'
        )
        hot_pages = ', '.join(
            f"{entry['page']}×{entry['count']}" for entry in trace_payload['trace_summary']['top_pages']
        ) or 'none'
        if trace_payload['trace_summary']['phase_boundaries']:
            phase_items = ''.join(
                '<li>'
                f"after reference {boundary['after_reference']}: windows {boundary['before_window']} → {boundary['after_window']} overlap {boundary['jaccard_similarity']:.2f}; {escape(boundary['reason'])}."
                '</li>'
                for boundary in trace_payload['trace_summary']['phase_boundaries'][:4]
            )
        else:
            phase_items = '<li>none detected for this window size.</li>'
        return f'''<section class="panel">
        <h2>{escape(title)}</h2>
        <p class="muted"><code>{escape(trace_payload['workload'])}</code> · {escape(describe_reference_label(trace_payload['reference_source']))}</p>
        <ul class="summary-list">
          <li><strong>{trace_payload['reference_length']}</strong> references</li>
          <li><strong>{trace_payload['trace_summary']['unique_pages']}</strong> unique pages</li>
          <li><strong>{trace_payload['trace_summary']['working_set_stats']['average']:.2f}</strong> avg working-set size</li>
          <li><strong>{len(trace_payload['trace_summary']['phase_boundaries'])}</strong> phase hints</li>
        </ul>
        <p class="muted">Best average faults: {'/'.join(algorithm.upper() for algorithm in trace_payload['best_average_winners'])} ({trace_payload['best_average_faults']:.2f})</p>
        <p class="muted">Reuse distance: {escape(reuse_line)}</p>
        <p class="muted">Working-set window: min {working_set['min']}, max {working_set['max']}, avg {working_set['average']:.2f}, final {working_set['final']}</p>
        <p class="muted">Hot pages: {escape(hot_pages)}</p>
        <h3>Phase-boundary hints</h3>
        <ul>{phase_items}</ul>
        <h3>Reference string</h3>
        <pre>{escape(' '.join(str(page) for page in trace_payload['reference_string']))}</pre>
      </section>'''

    left = payload['left']
    right = payload['right']

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Page Replacement Imported Trace Comparison</title>
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
      main {{ max-width: 1500px; margin: 0 auto; padding: 32px 20px 64px; }}
      h1, h2, h3, p {{ margin-top: 0; }}
      a {{ color: var(--accent); }}
      code, pre {{ font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, monospace; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .hero p, .muted {{ color: var(--muted); }}
      .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 24px 0 0; padding: 0; }}
      .summary-grid li {{ list-style: none; margin: 0; padding: 16px 18px; border-radius: 18px; background: var(--panel-alt); border: 1px solid #c7d2fe; }}
      .summary-grid strong {{ display: block; font-size: 1.35rem; margin-bottom: 6px; }}
      .panel {{ padding: 20px; margin-bottom: 24px; overflow: auto; }}
      .chart svg {{ width: 100%; height: auto; min-width: 1080px; display: block; }}
      .two-up {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 24px; }}
      .summary-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; padding: 0; margin: 0 0 16px; }}
      .summary-list li {{ list-style: none; padding: 12px 14px; border-radius: 16px; background: #f8fafc; border: 1px solid var(--border); }}
      .summary-list strong {{ display: block; font-size: 1.2rem; margin-bottom: 4px; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 12px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
      th {{ font-size: 0.95rem; color: var(--muted); }}
      ul {{ margin: 0; padding-left: 18px; color: var(--muted); }}
      li + li {{ margin-top: 8px; }}
      pre {{ background: #0f172a; color: #e2e8f0; padding: 18px; border-radius: 18px; overflow-x: auto; white-space: pre-wrap; word-break: break-word; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <h1>Page Replacement Imported Trace Comparison</h1>
        <p>Side-by-side study for two imported traces. The inline SVG card compares normalized average page-fault rates by algorithm, while the tables below keep the exact frame-by-frame and locality details easy to inspect for portfolio screenshots or interview walkthroughs.</p>
        <ul class="summary-grid">
          <li><strong>{left['workload']}</strong> left trace</li>
          <li><strong>{right['workload']}</strong> right trace</li>
          <li><strong>{payload['min_frames']}–{payload['max_frames']}</strong> frame range</li>
          <li><strong>{payload['window_size']}</strong> window size</li>
          <li><strong>{payload['summary']['left_phase_hint_count']}</strong> left phase hints</li>
          <li><strong>{payload['summary']['right_phase_hint_count']}</strong> right phase hints</li>
          <li><strong>{escape(payload['wsclock_window_description'])}</strong> WSClock τ</li>
          <li><strong>{escape(payload['dirty_page_description'])}</strong> dirty pages</li>
        </ul>
        <p class="muted">Downloads: {download_links}</p>
      </section>
      <section class="panel chart">
        <h2>Imported trace comparison card</h2>
        {inline_svg}
      </section>
      <section class="panel">
        <h2>Average algorithm comparison</h2>
        <table>
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Left avg faults</th>
              <th>Right avg faults</th>
              <th>Δ right-left</th>
              <th>Better avg</th>
              <th>Left avg fault rate</th>
              <th>Right avg fault rate</th>
              <th>Left avg writebacks</th>
              <th>Right avg writebacks</th>
            </tr>
          </thead>
          <tbody>{algorithm_rows}</tbody>
        </table>
      </section>
      <section class="panel">
        <h2>Frame-by-frame comparison</h2>
        <table>
          <thead>
            <tr>
              <th>Frames</th>
              <th>WSClock τ</th>
              <th>Left winner</th>
              <th>Right winner</th>
              {frame_header_cells}
            </tr>
          </thead>
          <tbody>{frame_rows}</tbody>
        </table>
      </section>
      <div class="two-up">
        {render_trace_panel('Left trace details', left)}
        {render_trace_panel('Right trace details', right)}
      </div>
    </main>
  </body>
</html>
'''


def format_trace_compare_text(payload: dict, *, html_path: Path, svg_path: Path) -> str:
    left = payload['left']
    right = payload['right']
    overall_better = payload['summary']['overall_better_average_fault_rate']
    if overall_better == 'left':
        overall_label = left['workload']
    elif overall_better == 'right':
        overall_label = right['workload']
    else:
        overall_label = 'tie'
    largest_gap = payload['summary']['largest_average_fault_gap']
    if largest_gap['better_average_faults'] == 'left':
        largest_gap_label = left['workload']
    elif largest_gap['better_average_faults'] == 'right':
        largest_gap_label = right['workload']
    else:
        largest_gap_label = 'tie'
    lines = [
        f"trace comparison: {left['workload']} vs {right['workload']}",
        f"html report: {html_path}",
        f"svg card: {svg_path}",
        f"wsclock window: {payload['wsclock_window_description']}",
        f"dirty pages: {payload['dirty_page_description']}",
        f"lower normalized overall average fault rate: {overall_label}",
        (
            f"wsclock average writebacks: {left['workload']}="
            f"{summarize_wsclock_writeback_average(left['study']):.2f}, "
            f"{right['workload']}={summarize_wsclock_writeback_average(right['study']):.2f}"
        ),
        (
            f"largest average fault gap: {largest_gap['algorithm'].upper()} → "
            f"{largest_gap_label} ({abs(largest_gap['fault_delta_right_minus_left']):.2f} faults)"
        ),
    ]
    for entry in payload['algorithm_summaries']:
        if entry['better_average_faults'] == 'left':
            winner = left['workload']
        elif entry['better_average_faults'] == 'right':
            winner = right['workload']
        else:
            winner = 'tie'
        lines.append(
            f"- {entry['algorithm']}: {left['workload']}={entry['left_average_faults']:.2f}, {right['workload']}={entry['right_average_faults']:.2f}, better={winner}"
        )
    return '\n'.join(lines)
def format_preset_text() -> str:
    lines = ["built-in workload presets:"]
    for preset in list_workload_presets():
        reference = " ".join(str(page) for page in preset.reference_string)
        lines.append(
            f"- {preset.name} (length={len(preset.reference_string)}): {preset.description}"
        )
        lines.append(f"  pages: {reference}")
    return "\n".join(lines)


def format_benchmark_text() -> str:
    lines = ["built-in trace benchmarks:"]
    for benchmark in list_trace_benchmarks():
        reference = load_trace_benchmark_reference(benchmark)
        preview = " ".join(str(page) for page in reference[:18])
        if len(reference) > 18:
            preview += " …"
        lines.append(
            f"- {benchmark.name} (length={len(reference)}): {benchmark.description}"
        )
        lines.append(f"  file: benchmarks/{benchmark.filename}")
        lines.append(f"  preview: {preview}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dirty_pages = parse_dirty_page_args(
        getattr(args, "dirty_page", None),
        getattr(args, "dirty_pages_file", None),
    )

    try:
        if args.command == "list-presets":
            presets = list_workload_presets()
            if args.json:
                print(
                    json.dumps(
                        [
                            {
                                "name": preset.name,
                                "description": preset.description,
                                "reference_length": len(preset.reference_string),
                                "reference_string": list(preset.reference_string),
                            }
                            for preset in presets
                        ],
                        indent=2,
                    )
                )
            else:
                print(format_preset_text())
            return 0

        if args.command == "list-benchmarks":
            benchmarks = list_trace_benchmarks()
            if args.json:
                print(
                    json.dumps(
                        [
                            {
                                "name": benchmark.name,
                                "description": benchmark.description,
                                "filename": benchmark.filename,
                                "reference_length": len(load_trace_benchmark_reference(benchmark)),
                            }
                            for benchmark in benchmarks
                        ],
                        indent=2,
                    )
                )
            else:
                print(format_benchmark_text())
            return 0

        if args.command == "gallery":
            workloads = resolve_gallery_workloads(
                args.gallery_presets,
                args.gallery_benchmarks,
                selected_pages_files=args.gallery_pages_files,
                include_benchmarks=args.include_benchmarks,
            )
            html_path = args.html_out or (args.artifact_dir / "index.html")
            gallery_runs = [
                build_gallery_run(
                    workload,
                    min_frames=args.min_frames,
                    max_frames=args.max_frames,
                    wsclock_window=args.wsclock_window,
                    dirty_pages=dirty_pages,
                    artifact_dir=args.artifact_dir,
                    html_dir=html_path.parent,
                )
                for workload in workloads
            ]
            write_text_output(
                html_path,
                format_gallery_html(
                    gallery_runs,
                    min_frames=args.min_frames,
                    max_frames=args.max_frames,
                ),
            )
            if args.json:
                print(
                    json.dumps(
                        {
                            "min_frames": args.min_frames,
                            "max_frames": args.max_frames,
                            "html_path": str(html_path),
                            "artifact_dir": str(args.artifact_dir),
                            "wsclock_window_mode": wsclock_window_mode(args.wsclock_window),
                            "wsclock_window_override": args.wsclock_window,
                            "wsclock_window_description": describe_wsclock_window_setting(args.wsclock_window),
                            "dirty_pages": list(dirty_pages),
                            "dirty_page_count": len(dirty_pages),
                            "dirty_page_description": describe_dirty_pages_setting(dirty_pages),
                            "workloads": [
                                {
                                    "type": run["workload"].source_kind,
                                    "workload": run["workload"].name,
                                    "description": run["workload"].description,
                                    "reference_length": len(run["workload"].reference_string),
                                    "reference_source": run["workload"].reference_source,
                                    "best_average_faults": round(run["best_average_faults"], 6),
                                    "average_wsclock_writebacks": round(
                                        summarize_wsclock_writeback_average(run["payload"]),
                                        6,
                                    ),
                                    "best_average_winners": run["best_average_winners"],
                                    "fifo_has_anomaly": run["fifo_has_anomaly"],
                                    "non_fifo_regression_count": len(run["non_fifo_violations"]),
                                    "paths": run["relative_paths"],
                                    "trace_summary_paths": (
                                        run["trace_summary"]["relative_paths"]
                                        if run["trace_summary"]
                                        else None
                                    ),
                                    "trace_summary_phase_hint_count": (
                                        len(run["trace_summary"]["payload"]["phase_boundaries"])
                                        if run["trace_summary"]
                                        else 0
                                    ),
                                }
                                for run in gallery_runs
                            ],
                        },
                        indent=2,
                    )
                )
            else:
                print(format_gallery_text(gallery_runs, html_path=html_path))
            return 0

        if args.command == "aggregate":
            workloads = resolve_gallery_workloads(
                args.aggregate_presets,
                args.aggregate_benchmarks,
                selected_pages_files=args.aggregate_pages_files,
                include_benchmarks=args.include_benchmarks,
            )
            html_path = args.html_out or (args.artifact_dir / "index.html")
            svg_path = args.artifact_dir / "aggregate-average-fault-rate.svg"
            csv_path = args.artifact_dir / "aggregate-workload-comparison.csv"
            json_path = args.artifact_dir / "aggregate-summary.json"
            aggregate_runs = [
                build_aggregate_run(
                    workload,
                    min_frames=args.min_frames,
                    max_frames=args.max_frames,
                    wsclock_window=args.wsclock_window,
                    dirty_pages=dirty_pages,
                )
                for workload in workloads
            ]
            write_text_output(
                svg_path,
                format_aggregate_svg(
                    aggregate_runs,
                    min_frames=args.min_frames,
                    max_frames=args.max_frames,
                ),
            )
            write_aggregate_csv(csv_path, aggregate_runs)
            aggregate_payload = build_aggregate_payload(
                aggregate_runs,
                min_frames=args.min_frames,
                max_frames=args.max_frames,
                html_path=html_path,
                artifact_dir=args.artifact_dir,
            )
            write_text_output(json_path, json.dumps(aggregate_payload, indent=2) + "\n")
            write_text_output(
                html_path,
                format_aggregate_html(
                    aggregate_runs,
                    min_frames=args.min_frames,
                    max_frames=args.max_frames,
                    svg_filename=os.path.relpath(svg_path, html_path.parent),
                    csv_filename=os.path.relpath(csv_path, html_path.parent),
                    json_filename=os.path.relpath(json_path, html_path.parent),
                ),
            )
            if args.json:
                print(json.dumps(aggregate_payload, indent=2))
            else:
                print(format_aggregate_text(aggregate_runs, html_path=html_path, svg_path=svg_path))
            return 0

        if args.command == "trace-compare":
            selected_pages_files = args.trace_compare_pages_files or []
            if len(selected_pages_files) != 2:
                raise InputError("trace-compare needs exactly two --pages-file inputs")
            workloads = resolve_gallery_workloads(
                None,
                None,
                selected_pages_files=selected_pages_files,
                include_benchmarks=False,
            )
            if len(workloads) != 2:
                raise InputError("trace-compare needs exactly two distinct imported trace files")
            left_workload, right_workload = workloads
            payload = build_trace_compare_payload(
                left_workload,
                right_workload,
                min_frames=args.min_frames,
                max_frames=args.max_frames,
                window_size=args.window_size,
                phase_threshold=args.phase_threshold,
                wsclock_window=args.wsclock_window,
                dirty_pages=dirty_pages,
            )
            stem = f"{left_workload.name}-vs-{right_workload.name}-trace-compare"
            markdown_path = args.artifact_dir / f"{stem}.md"
            svg_path = args.artifact_dir / f"{stem}.svg"
            csv_path = args.artifact_dir / f"{stem}.csv"
            json_path = args.artifact_dir / f"{stem}.json"
            html_path = args.html_out or (args.artifact_dir / f"{stem}.html")

            write_text_output(markdown_path, format_trace_compare_markdown(payload))
            svg_markup = format_trace_compare_svg(
                payload,
                id_prefix=f"page-replacement-{stem}",
            )
            write_text_output(svg_path, svg_markup)
            write_trace_compare_csv(csv_path, payload)
            trace_compare_payload = {
                **payload,
                "artifact_dir": str(args.artifact_dir),
                "html_path": str(html_path),
                "paths": {
                    "markdown": str(markdown_path),
                    "svg": str(svg_path),
                    "csv": str(csv_path),
                    "json": str(json_path),
                    "html": str(html_path),
                },
            }
            write_text_output(json_path, json.dumps(trace_compare_payload, indent=2) + "\n")
            write_text_output(
                html_path,
                format_trace_compare_html(
                    payload,
                    inline_svg=format_trace_compare_svg(
                        payload,
                        id_prefix=f"page-replacement-inline-{stem}",
                    ),
                    downloads=[
                        ("Markdown", os.path.relpath(markdown_path, html_path.parent)),
                        ("SVG", os.path.relpath(svg_path, html_path.parent)),
                        ("CSV", os.path.relpath(csv_path, html_path.parent)),
                        ("JSON", os.path.relpath(json_path, html_path.parent)),
                    ],
                ),
            )
            if args.json:
                print(json.dumps(trace_compare_payload, indent=2))
            else:
                print(format_trace_compare_text(payload, html_path=html_path, svg_path=svg_path))
            return 0

        parsed_reference = parse_reference_args(
            args.page,
            args.pages_file,
            args.preset,
            getattr(args, "benchmark", None),
        )
        reference = parsed_reference.reference_string

        if args.command == "trace-summary":
            payload = summarize_trace(
                reference,
                window_size=args.window_size,
                phase_threshold=args.phase_threshold,
            )
            payload["reference_source"] = parsed_reference.source
            if args.markdown_out:
                write_text_output(
                    args.markdown_out,
                    format_trace_summary_markdown(
                        payload,
                        reference_source=parsed_reference.source,
                    ),
                )
            svg_markup: str | None = None
            if args.svg_out or args.html_out:
                svg_markup = format_trace_summary_svg(
                    payload,
                    reference_source=parsed_reference.source,
                    id_prefix=f"trace-summary-{parsed_reference.source.replace(':', '-')}",
                )
            if args.svg_out and svg_markup is not None:
                write_text_output(args.svg_out, svg_markup)
            if args.html_out:
                html_downloads: list[tuple[str, str]] = []
                if args.markdown_out:
                    html_downloads.append(("Markdown", os.path.relpath(args.markdown_out, args.html_out.parent)))
                if args.svg_out:
                    html_downloads.append(("SVG", os.path.relpath(args.svg_out, args.html_out.parent)))
                if svg_markup is None:
                    svg_markup = format_trace_summary_svg(
                        payload,
                        reference_source=parsed_reference.source,
                        id_prefix=f"trace-summary-{parsed_reference.source.replace(':', '-')}",
                    )
                write_text_output(
                    args.html_out,
                    format_trace_summary_html(
                        payload,
                        reference_source=parsed_reference.source,
                        inline_svg=svg_markup,
                        downloads=html_downloads,
                    ),
                )
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(
                    format_trace_summary_text(
                        payload,
                        reference_source=parsed_reference.source,
                    )
                )
            return 0

        if args.command == "tune-wsclock":
            payload = tune_wsclock_windows(
                reference,
                args.frames,
                min_window=args.min_window,
                max_window=args.max_window,
                dirty_pages=dirty_pages,
                writeback_penalty=args.writeback_penalty,
            )
            payload["reference_source"] = parsed_reference.source
            if args.csv_out:
                write_wsclock_tuning_csv(
                    args.csv_out,
                    payload,
                    reference_source=parsed_reference.source,
                )
            if args.markdown_out:
                write_text_output(
                    args.markdown_out,
                    format_wsclock_tuning_markdown(
                        payload,
                        reference_source=parsed_reference.source,
                    ),
                )
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(
                    format_wsclock_tuning_text(
                        payload,
                        reference_source=parsed_reference.source,
                    )
                )
            return 0

        if args.command == "simulate":
            result = simulate(
                args.algorithm,
                reference,
                args.frames,
                wsclock_window=args.wsclock_window,
                dirty_pages=dirty_pages,
            )
            if args.json:
                print(
                    json.dumps(
                        {
                            **result.to_dict(include_steps=True),
                            "reference_source": parsed_reference.source,
                            "wsclock_window_mode": wsclock_window_mode(args.wsclock_window),
                            "wsclock_window_override": args.wsclock_window,
                            "wsclock_window_description": describe_wsclock_window_setting(args.wsclock_window),
                            "effective_wsclock_window": (
                                resolve_wsclock_window(args.frames, args.wsclock_window)
                                if result.algorithm == "wsclock"
                                else None
                            ),
                            "dirty_pages": list(dirty_pages),
                            "dirty_page_count": len(dirty_pages),
                            "dirty_page_description": describe_dirty_pages_setting(dirty_pages),
                        },
                        indent=2,
                    )
                )
            else:
                print(
                    format_simulation_text(
                        result,
                        show_steps=args.show_steps,
                        reference_source=parsed_reference.source,
                        wsclock_window=args.wsclock_window,
                        dirty_pages=dirty_pages,
                    )
                )
            return 0

        if args.command == "compare":
            results = compare_algorithms(
                reference,
                args.frames,
                wsclock_window=args.wsclock_window,
                dirty_pages=dirty_pages,
            )
            if args.json:
                print(
                    json.dumps(
                        {
                            "frame_count": args.frames,
                            "reference_string": reference,
                            "reference_source": parsed_reference.source,
                            "wsclock_window_mode": wsclock_window_mode(args.wsclock_window),
                            "wsclock_window_override": args.wsclock_window,
                            "wsclock_window_description": describe_wsclock_window_setting(args.wsclock_window),
                            "effective_wsclock_window": resolve_wsclock_window(args.frames, args.wsclock_window),
                            "dirty_pages": list(dirty_pages),
                            "dirty_page_count": len(dirty_pages),
                            "dirty_page_description": describe_dirty_pages_setting(dirty_pages),
                            "results": [result.to_dict(include_steps=False) for result in results],
                        },
                        indent=2,
                    )
                )
            else:
                print(
                    format_compare_text(
                        results,
                        args.frames,
                        reference,
                        reference_source=parsed_reference.source,
                        wsclock_window=args.wsclock_window,
                        dirty_pages=dirty_pages,
                    )
                )
            return 0

        if args.command == "study":
            payload = study_frame_counts(
                reference,
                args.min_frames,
                args.max_frames,
                wsclock_window=args.wsclock_window,
                dirty_pages=dirty_pages,
            )
            payload["reference_source"] = parsed_reference.source
            if args.csv_out:
                write_study_csv(args.csv_out, payload, reference_source=parsed_reference.source)
            if args.markdown_out:
                write_text_output(
                    args.markdown_out,
                    format_study_markdown(payload, reference_source=parsed_reference.source),
                )
            if args.svg_out:
                write_text_output(
                    args.svg_out,
                    format_study_svg(payload, reference_source=parsed_reference.source),
                )
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(format_study_text(payload, reference_source=parsed_reference.source))
            return 0
    except (InputError, FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
