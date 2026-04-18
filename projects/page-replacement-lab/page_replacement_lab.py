from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
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
