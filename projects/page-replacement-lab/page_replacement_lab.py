from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ALGORITHMS = ("fifo", "lru", "opt")


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
    previous_fifo_faults: int | None = None
    fifo_anomalies: list[dict] = []

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
        fifo_faults = run["fifo"].page_faults
        if previous_fifo_faults is not None and fifo_faults > previous_fifo_faults:
            fifo_anomalies.append(
                {
                    "algorithm": "fifo",
                    "from_frames": frame_count - 1,
                    "to_frames": frame_count,
                    "faults_before": previous_fifo_faults,
                    "faults_after": fifo_faults,
                    "fault_delta": fifo_faults - previous_fifo_faults,
                }
            )
        previous_fifo_faults = fifo_faults

    return {
        "reference_string": reference,
        "frame_results": frame_results,
        "fifo_belady_anomalies": fifo_anomalies,
    }


def parse_reference_args(pages: list[str], pages_file: str | None) -> list[int]:
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
        raise InputError("provide at least one --page or a --pages-file")
    return raw_pages


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulate classic page replacement algorithms for OS/virtual-memory workloads.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate_parser = subparsers.add_parser("simulate", help="simulate one algorithm")
    simulate_parser.add_argument("algorithm", choices=ALGORITHMS)
    simulate_parser.add_argument("--frames", type=int, required=True)
    simulate_parser.add_argument("--page", action="append", default=[])
    simulate_parser.add_argument("--pages-file")
    simulate_parser.add_argument("--json", action="store_true")
    simulate_parser.add_argument(
        "--show-steps",
        action="store_true",
        help="print the full step-by-step trace in text mode",
    )

    compare_parser = subparsers.add_parser("compare", help="compare fifo/lru/opt on one workload")
    compare_parser.add_argument("--frames", type=int, required=True)
    compare_parser.add_argument("--page", action="append", default=[])
    compare_parser.add_argument("--pages-file")
    compare_parser.add_argument("--json", action="store_true")

    study_parser = subparsers.add_parser(
        "study",
        help="compare page faults across a frame-count range and flag FIFO Belady anomalies",
    )
    study_parser.add_argument("--min-frames", type=int, required=True)
    study_parser.add_argument("--max-frames", type=int, required=True)
    study_parser.add_argument("--page", action="append", default=[])
    study_parser.add_argument("--pages-file")
    study_parser.add_argument("--json", action="store_true")

    return parser


def format_simulation_text(result: SimulationResult, *, show_steps: bool = False) -> str:
    lines = [
        f"algorithm: {result.algorithm}",
        f"frames: {result.frame_count}",
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


def format_compare_text(results: list[SimulationResult], frame_count: int, reference: list[int]) -> str:
    lines = [
        f"frames: {frame_count}",
        "reference: " + " ".join(str(page) for page in reference),
        "algorithm  faults  hits  hit-rate",
    ]
    for result in results:
        lines.append(
            f"{result.algorithm:<9} {result.page_faults:<6} {result.hits:<5} {result.hit_rate:>7.2%}"
        )
    return "\n".join(lines)


def format_study_text(payload: dict) -> str:
    lines = [
        "reference: " + " ".join(str(page) for page in payload["reference_string"]),
        "frames  fifo  lru  opt",
    ]
    for row in payload["frame_results"]:
        lines.append(
            f"{row['frame_count']:<6} {row['algorithms']['fifo']['page_faults']:<5} "
            f"{row['algorithms']['lru']['page_faults']:<4} {row['algorithms']['opt']['page_faults']:<4}"
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
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        reference = parse_reference_args(args.page, args.pages_file)
        if args.command == "simulate":
            result = simulate(args.algorithm, reference, args.frames)
            if args.json:
                print(json.dumps(result.to_dict(include_steps=True), indent=2))
            else:
                print(format_simulation_text(result, show_steps=args.show_steps))
            return 0

        if args.command == "compare":
            results = compare_algorithms(reference, args.frames)
            if args.json:
                print(
                    json.dumps(
                        {
                            "frame_count": args.frames,
                            "reference_string": reference,
                            "results": [result.to_dict(include_steps=False) for result in results],
                        },
                        indent=2,
                    )
                )
            else:
                print(format_compare_text(results, args.frames, reference))
            return 0

        if args.command == "study":
            payload = study_frame_counts(reference, args.min_frames, args.max_frames)
            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                print(format_study_text(payload))
            return 0
    except (InputError, FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
