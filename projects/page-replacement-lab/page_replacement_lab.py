from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
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

ALGORITHMS = ("fifo", "clock", "lru", "opt")


@dataclass(slots=True)
class SimulationStep:
    index: int
    page: int
    hit: bool
    frames: list[int]
    evicted: int | None


@dataclass(slots=True)
class SimulationResult:
    algorithm: str
    frame_count: int
    reference_string: list[int]
    page_faults: int
    hits: int
    hit_rate: float
    steps: list[SimulationStep]

    def to_dict(self, *, include_steps: bool = True) -> dict:
        payload = {
            "algorithm": self.algorithm,
            "frame_count": self.frame_count,
            "reference_string": self.reference_string,
            "reference_length": len(self.reference_string),
            "page_faults": self.page_faults,
            "hits": self.hits,
            "hit_rate": round(self.hit_rate, 6),
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
    "lru": simulate_lru,
    "opt": simulate_opt,
}


def simulate(algorithm: str, reference_string: Iterable[int], frame_count: int) -> SimulationResult:
    if algorithm not in SIMULATORS:
        raise InputError(f"unsupported algorithm: {algorithm}")
    return SIMULATORS[algorithm](reference_string, frame_count)


def compare_algorithms(reference_string: Iterable[int], frame_count: int) -> list[SimulationResult]:
    reference = validate_reference(reference_string, frame_count)
    return [simulate(name, reference, frame_count) for name in ALGORITHMS]


def study_frame_counts(
    reference_string: Iterable[int], min_frames: int, max_frames: int
) -> dict:
    reference = list(reference_string)
    if min_frames <= 0 or max_frames <= 0:
        raise InputError("frame counts must be positive")
    if min_frames > max_frames:
        raise InputError("min-frames must be less than or equal to max-frames")
    if not reference:
        raise InputError("reference string must contain at least one page")

    frame_results: list[dict] = []
    previous_faults: dict[str, int | None] = {algorithm: None for algorithm in ALGORITHMS}
    monotonicity_violations: list[dict] = []

    for frame_count in range(min_frames, max_frames + 1):
        run = {algorithm: simulate(algorithm, reference, frame_count) for algorithm in ALGORITHMS}
        frame_results.append(
            {
                "frame_count": frame_count,
                "algorithms": {
                    name: {
                        "page_faults": result.page_faults,
                        "hits": result.hits,
                        "hit_rate": round(result.hit_rate, 6),
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
    simulate_parser.add_argument("--json", action="store_true")
    simulate_parser.add_argument(
        "--show-steps",
        action="store_true",
        help="print the full step-by-step trace in text mode",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="compare fifo/clock/lru/opt on one workload",
    )
    compare_parser.add_argument("--frames", type=int, required=True)
    add_reference_arguments(compare_parser)
    compare_parser.add_argument("--json", action="store_true")

    study_parser = subparsers.add_parser(
        "study",
        help="compare page faults across a frame-count range and flag fault regressions",
    )
    study_parser.add_argument("--min-frames", type=int, required=True)
    study_parser.add_argument("--max-frames", type=int, required=True)
    add_reference_arguments(study_parser)
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

    return parser


def format_reference_source(reference_source: str) -> str:
    if reference_source.startswith("preset:"):
        preset = resolve_preset(reference_source.split(":", 1)[1])
        return f"source: preset {preset.name} — {preset.description}"
    if reference_source.startswith("benchmark:"):
        benchmark = resolve_trace_benchmark(reference_source.split(":", 1)[1])
        return f"source: benchmark {benchmark.name} — {benchmark.description}"
    return "source: custom"


def format_simulation_text(
    result: SimulationResult,
    *,
    show_steps: bool = False,
    reference_source: str = "custom",
) -> str:
    lines = [
        f"algorithm: {result.algorithm}",
        f"frames: {result.frame_count}",
        format_reference_source(reference_source),
        "reference: " + " ".join(str(page) for page in result.reference_string),
    ]
    if show_steps:
        lines.append("steps:")
        for step in result.steps:
            state = "HIT" if step.hit else "MISS"
            evicted = f" evicted={step.evicted}" if step.evicted is not None else ""
            lines.append(
                f"  {step.index:>2}: page={step.page:<3} {state:<4} frames={step.frames}{evicted}"
            )
    lines.append(
        f"summary: faults={result.page_faults} hits={result.hits} hit_rate={result.hit_rate:.2%}"
    )
    return "\n".join(lines)


def format_compare_text(
    results: list[SimulationResult],
    frame_count: int,
    reference: list[int],
    *,
    reference_source: str = "custom",
) -> str:
    algorithm_width = max(len("algorithm"), *(len(result.algorithm) for result in results))
    lines = [
        f"frames: {frame_count}",
        format_reference_source(reference_source),
        "reference: " + " ".join(str(page) for page in reference),
        f"{'algorithm':<{algorithm_width}}  faults  hits  hit-rate",
    ]
    for result in results:
        lines.append(
            f"{result.algorithm:<{algorithm_width}}  {result.page_faults:<6}  {result.hits:<4}  {result.hit_rate:>7.2%}"
        )
    best_faults = min(result.page_faults for result in results)
    winners = ", ".join(
        result.algorithm for result in results if result.page_faults == best_faults
    )
    lines.append(f"best faults: {best_faults} ({winners})")
    return "\n".join(lines)


def format_study_text(payload: dict, *, reference_source: str = "custom") -> str:
    algorithms = list(ALGORITHMS)
    column_width = max(6, *(len(name) for name in algorithms))
    lines = [
        format_reference_source(reference_source),
        "reference: " + " ".join(str(page) for page in payload["reference_string"]),
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
        rows.append(
            {
                "frame_count": row["frame_count"],
                "fifo_faults": row["algorithms"]["fifo"]["page_faults"],
                "clock_faults": row["algorithms"]["clock"]["page_faults"],
                "lru_faults": row["algorithms"]["lru"]["page_faults"],
                "opt_faults": row["algorithms"]["opt"]["page_faults"],
                "best_algorithms": winners,
            }
        )
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


def describe_reference_label(reference_source: str) -> str:
    if reference_source.startswith("preset:"):
        preset = resolve_preset(reference_source.split(":", 1)[1])
        return f"preset {preset.name} — {preset.description}"
    if reference_source.startswith("benchmark:"):
        benchmark = resolve_trace_benchmark(reference_source.split(":", 1)[1])
        return f"benchmark {benchmark.name} — {benchmark.description}"
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "frames",
                "fifo_faults",
                "clock_faults",
                "lru_faults",
                "opt_faults",
                "best_algorithms",
                "reference_source",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "frames": row["frame_count"],
                    "fifo_faults": row["fifo_faults"],
                    "clock_faults": row["clock_faults"],
                    "lru_faults": row["lru_faults"],
                    "opt_faults": row["opt_faults"],
                    "best_algorithms": row["best_algorithms"],
                    "reference_source": reference_source,
                }
            )


def write_study_json(path: Path, payload: dict) -> None:
    write_text_output(path, json.dumps(payload, indent=2) + "\n")


def format_study_markdown(payload: dict, *, reference_source: str = "custom") -> str:
    rows = build_study_rows(payload)
    averages = summarize_fault_averages(payload)
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
        f"- best average faults: {average_winners} ({best_average:.2f})",
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
    lines.extend(
        [
            "",
            "## Faults by frame count",
            "",
            "| Frames | FIFO | Clock | LRU | OPT | Winner |",
            "| ---: | ---: | ---: | ---: | ---: | :--- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['frame_count']} | {row['fifo_faults']} | {row['clock_faults']} | {row['lru_faults']} | {row['opt_faults']} | {row['best_algorithms']} |"
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
    "lru": "#2563eb",
    "opt": "#10b981",
}

SVG_STROKE_PATTERNS = {
    "fifo": None,
    "clock": "10 8",
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
        f"frame range: {frame_counts[0]} to {frame_counts[-1]} frames | best average faults: {average_winners} ({best_average:.2f})",
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
    include_benchmarks: bool,
) -> list[GalleryWorkload]:
    ordered: list[GalleryWorkload] = []
    seen: set[str] = set()

    def add_workload(workload: GalleryWorkload) -> None:
        if workload.reference_source in seen:
            return
        ordered.append(workload)
        seen.add(workload.reference_source)

    if selected_presets or selected_benchmarks:
        for name in selected_presets or []:
            add_workload(workload_from_preset(resolve_preset(name)))
        for name in selected_benchmarks or []:
            add_workload(workload_from_benchmark(resolve_trace_benchmark(name)))
        return ordered

    for preset in list_workload_presets():
        add_workload(workload_from_preset(preset))
    if include_benchmarks:
        for benchmark in list_trace_benchmarks():
            add_workload(workload_from_benchmark(benchmark))
    return ordered


def format_average_fault_summary(averages: dict[str, float]) -> list[str]:
    return [f"{algorithm.upper()}: {averages[algorithm]:.2f}" for algorithm in ALGORITHMS]


def build_gallery_run(
    workload: GalleryWorkload,
    *,
    min_frames: int,
    max_frames: int,
    artifact_dir: Path,
    html_dir: Path,
) -> dict:
    reference_source = workload.reference_source
    payload = study_frame_counts(workload.reference_string, min_frames, max_frames)
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
    ]
    for run in gallery_runs:
        winners = "/".join(algorithm.upper() for algorithm in run["best_average_winners"])
        workload = run["workload"]
        lines.append(
            f"- {workload.source_kind} {workload.name}: best average faults {winners} ({run['best_average_faults']:.2f}), "
            f"fifo anomaly={'yes' if run['fifo_has_anomaly'] else 'no'}, "
            f"other regressions={len(run['non_fifo_violations'])}"
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
        summary_rows.append(
            "<tr>"
            f"<td>{escape(workload.source_kind)}</td>"
            f"<td><a href=\"#{section_id}\"><code>{escape(workload.name)}</code></a></td>"
            f"<td>{escape(workload.description)}</td>"
            f"<td>{run['best_average_faults']:.2f} ({escape(winners)})</td>"
            f"<td>{'yes' if run['fifo_has_anomaly'] else 'no'}</td>"
            f"<td>{len(run['non_fifo_violations'])}</td>"
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
            "</div>"
            "</div>"
            f"<figure>{run['inline_svg']}<figcaption>Downloads: {download_links}</figcaption></figure>"
            "<div class=\"study-card__meta\">"
            f"<div class=\"meta-panel\"><h3>Average faults</h3><ul>{average_items}</ul></div>"
            f"<div class=\"meta-panel\"><h3>FIFO anomaly callouts</h3><ul>{fifo_items}</ul></div>"
            f"<div class=\"meta-panel\"><h3>Other regressions</h3><ul>{other_items}</ul></div>"
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
        <p>Frame-range study cards for the built-in workloads in <code>page-replacement-lab</code>. The gallery can mix compact presets with larger trace-benchmark bundles, keeps the screenshot-ready SVG inline, links the exported Markdown / SVG / CSV / JSON companions, and highlights where FIFO or other policies regress as frame count increases.</p>
        <ul class="summary-grid">
          <li><strong>{workload_count}</strong> workloads</li>
          <li><strong>{benchmark_count}</strong> trace benchmarks</li>
          <li><strong>{min_frames}–{max_frames}</strong> frame range</li>
          <li><strong>{fifo_anomaly_count}</strong> FIFO anomaly workloads</li>
          <li><strong>{non_fifo_regression_count}</strong> workloads with non-FIFO regressions</li>
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
                include_benchmarks=args.include_benchmarks,
            )
            html_path = args.html_out or (args.artifact_dir / "index.html")
            gallery_runs = [
                build_gallery_run(
                    workload,
                    min_frames=args.min_frames,
                    max_frames=args.max_frames,
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
                            "workloads": [
                                {
                                    "type": run["workload"].source_kind,
                                    "workload": run["workload"].name,
                                    "description": run["workload"].description,
                                    "reference_length": len(run["workload"].reference_string),
                                    "reference_source": run["workload"].reference_source,
                                    "best_average_faults": round(run["best_average_faults"], 6),
                                    "best_average_winners": run["best_average_winners"],
                                    "fifo_has_anomaly": run["fifo_has_anomaly"],
                                    "non_fifo_regression_count": len(run["non_fifo_violations"]),
                                    "paths": run["relative_paths"],
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

        parsed_reference = parse_reference_args(
            args.page,
            args.pages_file,
            args.preset,
            getattr(args, "benchmark", None),
        )
        reference = parsed_reference.reference_string
        if args.command == "simulate":
            result = simulate(args.algorithm, reference, args.frames)
            if args.json:
                print(
                    json.dumps(
                        {
                            **result.to_dict(include_steps=True),
                            "reference_source": parsed_reference.source,
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
                    )
                )
            return 0

        if args.command == "compare":
            results = compare_algorithms(reference, args.frames)
            if args.json:
                print(
                    json.dumps(
                        {
                            "frame_count": args.frames,
                            "reference_string": reference,
                            "reference_source": parsed_reference.source,
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
                    )
                )
            return 0

        if args.command == "study":
            payload = study_frame_counts(reference, args.min_frames, args.max_frames)
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
