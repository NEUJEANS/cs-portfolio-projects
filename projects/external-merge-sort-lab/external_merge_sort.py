from __future__ import annotations

import argparse
import heapq
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


@dataclass
class SortStats:
    total_numbers: int
    chunk_size: int
    runs_created: int
    merge_fan_in: int
    merge_rounds: int


def parse_numbers(text: str) -> list[int]:
    numbers: list[int] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        for token in line.replace(",", " ").split():
            numbers.append(int(token))
    return numbers


def read_numbers(path: Path) -> list[int]:
    return parse_numbers(path.read_text(encoding="utf-8"))


def write_numbers(path: Path, numbers: Iterable[int]) -> None:
    collected = [str(number) for number in numbers]
    content = "\n".join(collected)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def chunked(values: Sequence[int], chunk_size: int) -> Iterator[list[int]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    for start in range(0, len(values), chunk_size):
        yield list(values[start : start + chunk_size])


def create_sorted_runs(numbers: Sequence[int], chunk_size: int, temp_dir: Path) -> list[Path]:
    run_paths: list[Path] = []
    for index, chunk in enumerate(chunked(numbers, chunk_size), start=1):
        run_path = temp_dir / f"run_{index:03d}.txt"
        write_numbers(run_path, sorted(chunk))
        run_paths.append(run_path)
    return run_paths


def iter_run(path: Path) -> Iterator[int]:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            yield int(stripped)


def merge_run_group(run_paths: Sequence[Path], output_path: Path) -> Path:
    iterators = [iter_run(path) for path in run_paths]
    heap: list[tuple[int, int]] = []
    for run_index, iterator in enumerate(iterators):
        try:
            heap.append((next(iterator), run_index))
        except StopIteration:
            continue
    heapq.heapify(heap)

    with output_path.open("w", encoding="utf-8") as handle:
        while heap:
            value, run_index = heapq.heappop(heap)
            handle.write(f"{value}\n")
            iterator = iterators[run_index]
            try:
                heapq.heappush(heap, (next(iterator), run_index))
            except StopIteration:
                pass
    return output_path


def merge_runs(run_paths: Sequence[Path], fan_in: int, temp_dir: Path) -> tuple[Path, int]:
    if fan_in < 2:
        raise ValueError("fan_in must be at least 2")
    current_runs = list(run_paths)
    round_number = 0
    while len(current_runs) > 1:
        round_number += 1
        next_runs: list[Path] = []
        for group_index, start in enumerate(range(0, len(current_runs), fan_in), start=1):
            group = current_runs[start : start + fan_in]
            merged_path = temp_dir / f"merge_r{round_number:02d}_{group_index:03d}.txt"
            next_runs.append(merge_run_group(group, merged_path))
        current_runs = next_runs
    return current_runs[0], round_number


def external_merge_sort(input_path: Path, output_path: Path, chunk_size: int, fan_in: int) -> SortStats:
    numbers = read_numbers(input_path)
    with tempfile.TemporaryDirectory(prefix="external-merge-sort-") as tmp:
        temp_dir = Path(tmp)
        run_paths = create_sorted_runs(numbers, chunk_size, temp_dir)
        if not run_paths:
            write_numbers(output_path, [])
            return SortStats(0, chunk_size, 0, fan_in, 0)
        if len(run_paths) == 1:
            write_numbers(output_path, iter_run(run_paths[0]))
            merge_rounds = 0
        else:
            final_run, merge_rounds = merge_runs(run_paths, fan_in, temp_dir)
            write_numbers(output_path, iter_run(final_run))
        return SortStats(len(numbers), chunk_size, len(run_paths), fan_in, merge_rounds)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sort large integer files using chunked external merge sort.")
    parser.add_argument("input", type=Path, help="input text file containing integers")
    parser.add_argument("output", type=Path, help="output path for sorted integers")
    parser.add_argument("--chunk-size", type=int, default=8, help="numbers per initial in-memory run")
    parser.add_argument("--fan-in", type=int, default=4, help="how many runs to merge at once")
    parser.add_argument("--stats", action="store_true", help="print JSON stats after sorting")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.fan_in < 2:
        parser.error("--fan-in must be at least 2")

    stats = external_merge_sort(args.input, args.output, args.chunk_size, args.fan_in)
    if args.stats:
        print(json.dumps(stats.__dict__, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
