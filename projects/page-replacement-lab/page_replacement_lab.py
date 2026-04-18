from __future__ import annotations

import argparse
import csv
import json
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


def resolve_preset(name: str) -> WorkloadPreset:
    try:
        return WORKLOAD_PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(WORKLOAD_PRESETS))
        raise InputError(f"unknown preset: {name}. choose from: {available}") from exc


def parse_reference_args(
    pages: list[str],
    pages_file: str | None,
    preset: str | None,
) -> ParsedReference:
    if preset and (pages or pages_file):
        raise InputError("use either --preset or explicit --page/--pages-file input, not both")

    if preset:
        selected = resolve_preset(preset)
        return ParsedReference(
            reference_string=list(selected.reference_string),
            source=f"preset:{selected.name}",
        )

    raw_pages: list[int] = []
    for token in pages:
        raw_pages.append(int(token))

    if pages_file:
        content = Path(pages_file).read_text(encoding="utf-8").strip()
        if not content:
            raise InputError("pages file is empty")
        if content.startswith("["):
            payload = json.loads(content)
            if not isinstance(payload, list):
                raise InputError("JSON pages file must contain a list")
            raw_pages.extend(int(value) for value in payload)
        else:
            for token in content.replace(",", " ").split():
                raw_pages.append(int(token))

    if not raw_pages:
        raise InputError("provide at least one --page, a --pages-file, or a --preset")
    return ParsedReference(reference_string=raw_pages, source="custom")


def add_reference_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--page", action="append", default=[])
    parser.add_argument("--pages-file")
    parser.add_argument(
        "--preset",
        choices=tuple(WORKLOAD_PRESETS),
        help="use a built-in workload preset instead of explicit pages",
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

    preset_parser = subparsers.add_parser(
        "list-presets",
        help="list built-in workload presets for repeatable demos",
    )
    preset_parser.add_argument("--json", action="store_true")

    return parser


def format_reference_source(reference_source: str) -> str:
    if reference_source.startswith("preset:"):
        preset = resolve_preset(reference_source.split(":", 1)[1])
        return f"source: preset {preset.name} — {preset.description}"
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
    return "custom workload"


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


def format_study_svg(payload: dict, *, reference_source: str = "custom") -> str:
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
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
            "  <title id=\"title\">Page replacement frame study chart</title>",
            f'  <desc id="desc">Page-fault vs frame-count chart for {escape(describe_reference_label(reference_source))}</desc>',
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


def format_preset_text() -> str:
    lines = ["built-in workload presets:"]
    for preset in list_workload_presets():
        reference = " ".join(str(page) for page in preset.reference_string)
        lines.append(
            f"- {preset.name} (length={len(preset.reference_string)}): {preset.description}"
        )
        lines.append(f"  pages: {reference}")
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

        parsed_reference = parse_reference_args(args.page, args.pages_file, args.preset)
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
