from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TAKEN_TOKENS = {"1", "t", "taken", "true", "y", "yes"}
NOT_TAKEN_TOKENS = {"0", "f", "false", "n", "no", "not-taken", "not_taken", "nottaken", "untaken"}


@dataclass(frozen=True)
class BranchRecord:
    address: int
    taken: bool
    target: int | None = None
    label: str | None = None
    line_number: int | None = None

    @property
    def address_hex(self) -> str:
        return hex(self.address)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "address": self.address_hex,
            "taken": self.taken,
            "outcome": "T" if self.taken else "N",
        }
        if self.target is not None:
            payload["target"] = hex(self.target)
        if self.label:
            payload["label"] = self.label
        if self.line_number is not None:
            payload["line_number"] = self.line_number
        return payload


@dataclass
class SimulationResult:
    predictor: str
    total_branches: int
    correct_predictions: int
    mispredictions: int
    accuracy: float
    mpki: float
    taken_branches: int
    not_taken_branches: int
    hardest_branches: list[dict[str, Any]]
    first_events: list[dict[str, Any]]
    final_state: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "predictor": self.predictor,
            "total_branches": self.total_branches,
            "correct_predictions": self.correct_predictions,
            "mispredictions": self.mispredictions,
            "accuracy": self.accuracy,
            "accuracy_percent": round(self.accuracy * 100, 3),
            "mpki": self.mpki,
            "taken_branches": self.taken_branches,
            "not_taken_branches": self.not_taken_branches,
            "hardest_branches": self.hardest_branches,
            "first_events": self.first_events,
            "final_state": self.final_state,
        }


class BranchPredictor:
    name = "base"

    def predict(self, branch: BranchRecord) -> bool:  # pragma: no cover - interface only
        raise NotImplementedError

    def update(self, branch: BranchRecord) -> None:  # pragma: no cover - interface only
        raise NotImplementedError

    def snapshot(self) -> dict[str, Any]:
        return {}


class AlwaysTakenPredictor(BranchPredictor):
    name = "always-taken"

    def predict(self, branch: BranchRecord) -> bool:
        return True

    def update(self, branch: BranchRecord) -> None:
        return None


class AlwaysNotTakenPredictor(BranchPredictor):
    name = "always-not-taken"

    def predict(self, branch: BranchRecord) -> bool:
        return False

    def update(self, branch: BranchRecord) -> None:
        return None


class OneBitPredictor(BranchPredictor):
    name = "one-bit"

    def __init__(self, table_size: int = 16, default_taken: bool = False) -> None:
        _validate_power_of_two(table_size, "table_size")
        self.table_size = table_size
        self.mask = table_size - 1
        self.default_bit = 1 if default_taken else 0
        self.table = [self.default_bit] * table_size

    def _index(self, address: int) -> int:
        return (address >> 2) & self.mask

    def predict(self, branch: BranchRecord) -> bool:
        return bool(self.table[self._index(branch.address)])

    def update(self, branch: BranchRecord) -> None:
        self.table[self._index(branch.address)] = 1 if branch.taken else 0

    def snapshot(self) -> dict[str, Any]:
        trained_entries = sum(1 for value in self.table if value != self.default_bit)
        return {
            "table_size": self.table_size,
            "trained_entries": trained_entries,
            "default_prediction": "T" if self.default_bit else "N",
        }


class TwoBitPredictor(BranchPredictor):
    name = "two-bit"

    def __init__(self, table_size: int = 16, default_counter: int = 2) -> None:
        _validate_power_of_two(table_size, "table_size")
        if default_counter not in {0, 1, 2, 3}:
            raise ValueError("default_counter must be between 0 and 3")
        self.table_size = table_size
        self.mask = table_size - 1
        self.default_counter = default_counter
        self.table = [default_counter] * table_size

    def _index(self, address: int) -> int:
        return (address >> 2) & self.mask

    def predict(self, branch: BranchRecord) -> bool:
        return self.table[self._index(branch.address)] >= 2

    def update(self, branch: BranchRecord) -> None:
        index = self._index(branch.address)
        counter = self.table[index]
        if branch.taken:
            self.table[index] = min(3, counter + 1)
        else:
            self.table[index] = max(0, counter - 1)

    def snapshot(self) -> dict[str, Any]:
        trained_entries = sum(1 for value in self.table if value != self.default_counter)
        return {
            "table_size": self.table_size,
            "trained_entries": trained_entries,
            "default_counter": self.default_counter,
        }


class GSharePredictor(BranchPredictor):
    name = "gshare"

    def __init__(self, table_size: int = 16, history_bits: int = 4, default_counter: int = 2) -> None:
        _validate_power_of_two(table_size, "table_size")
        if history_bits < 1:
            raise ValueError("history_bits must be at least 1")
        if default_counter not in {0, 1, 2, 3}:
            raise ValueError("default_counter must be between 0 and 3")
        self.table_size = table_size
        self.mask = table_size - 1
        self.history_bits = history_bits
        self.history_mask = (1 << history_bits) - 1
        self.default_counter = default_counter
        self.history = 0
        self.table = [default_counter] * table_size

    def _index(self, address: int) -> int:
        pc_index = address >> 2
        return (pc_index ^ self.history) & self.mask

    def predict(self, branch: BranchRecord) -> bool:
        return self.table[self._index(branch.address)] >= 2

    def update(self, branch: BranchRecord) -> None:
        index = self._index(branch.address)
        counter = self.table[index]
        if branch.taken:
            self.table[index] = min(3, counter + 1)
        else:
            self.table[index] = max(0, counter - 1)
        self.history = ((self.history << 1) | int(branch.taken)) & self.history_mask

    def snapshot(self) -> dict[str, Any]:
        trained_entries = sum(1 for value in self.table if value != self.default_counter)
        return {
            "table_size": self.table_size,
            "history_bits": self.history_bits,
            "trained_entries": trained_entries,
            "default_counter": self.default_counter,
            "final_history": format(self.history, f"0{self.history_bits}b"),
        }


def _validate_power_of_two(value: int, label: str) -> None:
    if value < 2 or value & (value - 1) != 0:
        raise ValueError(f"{label} must be a power of two >= 2")


def parse_outcome(token: str) -> bool:
    normalized = token.strip().lower()
    if normalized in TAKEN_TOKENS:
        return True
    if normalized in NOT_TAKEN_TOKENS:
        return False
    raise ValueError(f"unsupported branch outcome token: {token!r}")


def parse_trace_line(line: str, line_number: int) -> BranchRecord | None:
    content = line.split("#", 1)[0].strip()
    if not content:
        return None
    tokens = [token for token in re.split(r"[\s,]+", content) if token]
    if len(tokens) < 2:
        raise ValueError(f"line {line_number}: expected '<address> <outcome>'")

    try:
        address = int(tokens[0], 0)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"line {line_number}: invalid address {tokens[0]!r}") from exc

    taken = parse_outcome(tokens[1])
    target: int | None = None
    label: str | None = None
    remainder = tokens[2:]
    if remainder:
        try:
            target = int(remainder[0], 0)
            remainder = remainder[1:]
        except ValueError:
            target = None
    if remainder:
        label = " ".join(remainder)

    return BranchRecord(address=address, taken=taken, target=target, label=label, line_number=line_number)


def load_trace(path: str | Path) -> list[BranchRecord]:
    trace_path = Path(path)
    records: list[BranchRecord] = []
    for line_number, line in enumerate(trace_path.read_text(encoding="utf-8").splitlines(), start=1):
        record = parse_trace_line(line, line_number)
        if record is not None:
            records.append(record)
    if not records:
        raise ValueError(f"trace file {trace_path} did not contain any branch records")
    return records


def simulate_trace(records: list[BranchRecord], predictor: BranchPredictor, event_preview: int = 8) -> SimulationResult:
    if not records:
        raise ValueError("records must not be empty")

    correct = 0
    mispredictions = 0
    taken_branches = 0
    not_taken_branches = 0
    branch_stats: dict[int, dict[str, int]] = {}
    events: list[dict[str, Any]] = []

    for offset, record in enumerate(records, start=1):
        predicted_taken = predictor.predict(record)
        is_correct = predicted_taken == record.taken
        predictor.update(record)

        if record.taken:
            taken_branches += 1
        else:
            not_taken_branches += 1

        stats = branch_stats.setdefault(record.address, {"total": 0, "incorrect": 0, "taken": 0, "not_taken": 0})
        stats["total"] += 1
        if record.taken:
            stats["taken"] += 1
        else:
            stats["not_taken"] += 1

        if is_correct:
            correct += 1
        else:
            mispredictions += 1
            stats["incorrect"] += 1

        if len(events) < event_preview:
            event = record.to_dict()
            event.update(
                {
                    "index": offset,
                    "predicted": "T" if predicted_taken else "N",
                    "correct": is_correct,
                }
            )
            events.append(event)

    total = len(records)
    accuracy = correct / total
    hardest_branches = [
        {
            "address": hex(address),
            "total": stats["total"],
            "mispredictions": stats["incorrect"],
            "accuracy_percent": round(((stats["total"] - stats["incorrect"]) / stats["total"]) * 100, 3),
            "taken": stats["taken"],
            "not_taken": stats["not_taken"],
        }
        for address, stats in sorted(
            branch_stats.items(),
            key=lambda item: (-item[1]["incorrect"], -item[1]["total"], item[0]),
        )
        if stats["incorrect"] > 0
    ]

    return SimulationResult(
        predictor=predictor.name,
        total_branches=total,
        correct_predictions=correct,
        mispredictions=mispredictions,
        accuracy=accuracy,
        mpki=round((mispredictions / total) * 1000, 3),
        taken_branches=taken_branches,
        not_taken_branches=not_taken_branches,
        hardest_branches=hardest_branches[:5],
        first_events=events,
        final_state=predictor.snapshot(),
    )


def compare_predictors(records: list[BranchRecord], table_size: int = 16, history_bits: int = 4) -> list[SimulationResult]:
    results = [
        simulate_trace(records, AlwaysTakenPredictor()),
        simulate_trace(records, AlwaysNotTakenPredictor()),
        simulate_trace(records, OneBitPredictor(table_size=table_size)),
        simulate_trace(records, TwoBitPredictor(table_size=table_size)),
        simulate_trace(records, GSharePredictor(table_size=table_size, history_bits=history_bits)),
    ]
    return sorted(results, key=lambda item: (-item.accuracy, item.mispredictions, item.predictor))


def build_predictor(name: str, table_size: int, history_bits: int) -> BranchPredictor:
    normalized = name.strip().lower()
    if normalized == "always-taken":
        return AlwaysTakenPredictor()
    if normalized == "always-not-taken":
        return AlwaysNotTakenPredictor()
    if normalized == "one-bit":
        return OneBitPredictor(table_size=table_size)
    if normalized == "two-bit":
        return TwoBitPredictor(table_size=table_size)
    if normalized == "gshare":
        return GSharePredictor(table_size=table_size, history_bits=history_bits)
    raise ValueError(f"unsupported predictor: {name}")


def format_summary_table(results: list[SimulationResult]) -> str:
    lines = [
        "predictor          accuracy   mispreds   mpki    hardest branch",
        "----------------  ---------  ---------  ------  ---------------",
    ]
    for result in results:
        hardest = result.hardest_branches[0]["address"] if result.hardest_branches else "-"
        lines.append(
            f"{result.predictor:<16}  {result.accuracy * 100:>7.2f}%  {result.mispredictions:>9}  {result.mpki:>6.1f}  {hardest}"
        )
    return "\n".join(lines)


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot serialize object of type {type(value)!r}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate classic branch predictors on a local trace file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common_help = {
        "trace": {"help": "Path to a trace file with '<address> <outcome>' lines."},
        "table_size": {"help": "Predictor table size (power of two).", "type": int, "default": 16},
        "history_bits": {"help": "Global history bits for gshare.", "type": int, "default": 4},
    }

    compare_parser = subparsers.add_parser("compare", help="Run a fixed predictor suite and rank the results.")
    compare_parser.add_argument("trace", **common_help["trace"])
    compare_parser.add_argument("--table-size", **common_help["table_size"])
    compare_parser.add_argument("--history-bits", **common_help["history_bits"])
    compare_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text table.")

    simulate_parser = subparsers.add_parser("simulate", help="Run one specific predictor on the trace.")
    simulate_parser.add_argument("trace", **common_help["trace"])
    simulate_parser.add_argument(
        "--predictor",
        choices=["always-taken", "always-not-taken", "one-bit", "two-bit", "gshare"],
        default="two-bit",
        help="Predictor to simulate.",
    )
    simulate_parser.add_argument("--table-size", **common_help["table_size"])
    simulate_parser.add_argument("--history-bits", **common_help["history_bits"])
    simulate_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        records = load_trace(args.trace)
        if args.command == "compare":
            results = compare_predictors(records, table_size=args.table_size, history_bits=args.history_bits)
            if args.json:
                payload = {
                    "trace": str(Path(args.trace)),
                    "total_branches": len(records),
                    "results": [result.to_dict() for result in results],
                    "best_predictor": results[0].predictor,
                }
                print(json.dumps(payload, indent=2, default=_json_default))
            else:
                print(format_summary_table(results))
                print()
                print(f"best predictor: {results[0].predictor} ({results[0].accuracy * 100:.2f}% accuracy)")
            return 0

        predictor = build_predictor(args.predictor, table_size=args.table_size, history_bits=args.history_bits)
        result = simulate_trace(records, predictor)
        if args.json:
            payload = {"trace": str(Path(args.trace)), **result.to_dict()}
            print(json.dumps(payload, indent=2, default=_json_default))
        else:
            print(
                f"{result.predictor}: {result.accuracy * 100:.2f}% accuracy, "
                f"{result.mispredictions} mispredictions over {result.total_branches} branches (MPKI {result.mpki:.1f})"
            )
            if result.hardest_branches:
                top = result.hardest_branches[0]
                print(
                    "hardest branch: "
                    f"{top['address']} with {top['mispredictions']} mispredictions across {top['total']} executions"
                )
        return 0
    except ValueError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    raise SystemExit(main())
