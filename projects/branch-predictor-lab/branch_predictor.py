from __future__ import annotations

import argparse
import json
import random
import re
import textwrap
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


TAKEN_TOKENS = {"1", "t", "taken", "true", "y", "yes"}
NOT_TAKEN_TOKENS = {"0", "f", "false", "n", "no", "not-taken", "not_taken", "nottaken", "untaken"}
SYNTHETIC_WORKLOADS = (
    "loop-heavy",
    "random-biased",
    "tournament-style",
    "alias-thrash",
    "perceptron-majority",
)
SIMPLE_PREDICTOR_NAMES = {"always-taken", "always-not-taken", "one-bit", "two-bit"}
ADVANCED_PREDICTOR_NAMES = {"local-history", "gshare", "perceptron", "tournament"}
WORKLOAD_SWEEP_PROFILES: dict[str, dict[str, Any]] = {
    "loop-heavy": {
        "branches": 40,
        "seed": 7,
        "table_size": 8,
        "history_bits": 4,
        "headline": "loop backedges and exits",
    },
    "random-biased": {
        "branches": 96,
        "seed": 11,
        "table_size": 16,
        "history_bits": 2,
        "headline": "biased hot/cold guard branches",
    },
    "tournament-style": {
        "branches": 48,
        "seed": 5,
        "table_size": 16,
        "history_bits": 4,
        "headline": "mixed local/global correlation",
    },
    "alias-thrash": {
        "branches": 64,
        "seed": 7,
        "table_size": 16,
        "history_bits": 4,
        "headline": "small-table alias interference",
    },
    "perceptron-majority": {
        "branches": 96,
        "seed": 13,
        "table_size": 32,
        "history_bits": 12,
        "headline": "long-history linearly separable branch",
    },
}


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


class LocalHistoryPredictor(BranchPredictor):
    name = "local-history"

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
        self.local_histories = [0] * table_size
        self.pattern_table = [default_counter] * (1 << history_bits)

    def _history_index(self, address: int) -> int:
        return (address >> 2) & self.mask

    def _pattern_index(self, address: int) -> int:
        return self.local_histories[self._history_index(address)]

    def predict(self, branch: BranchRecord) -> bool:
        return self.pattern_table[self._pattern_index(branch.address)] >= 2

    def update(self, branch: BranchRecord) -> None:
        history_index = self._history_index(branch.address)
        pattern_index = self.local_histories[history_index]
        counter = self.pattern_table[pattern_index]
        if branch.taken:
            self.pattern_table[pattern_index] = min(3, counter + 1)
        else:
            self.pattern_table[pattern_index] = max(0, counter - 1)
        self.local_histories[history_index] = ((pattern_index << 1) | int(branch.taken)) & self.history_mask

    def snapshot(self) -> dict[str, Any]:
        trained_patterns = sum(1 for value in self.pattern_table if value != self.default_counter)
        active_histories = sum(1 for value in self.local_histories if value != 0)
        return {
            "table_size": self.table_size,
            "history_bits": self.history_bits,
            "trained_patterns": trained_patterns,
            "active_histories": active_histories,
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


class PerceptronPredictor(BranchPredictor):
    name = "perceptron"

    def __init__(
        self,
        table_size: int = 16,
        history_bits: int = 8,
        threshold: int | None = None,
        weight_limit: int | None = None,
    ) -> None:
        _validate_power_of_two(table_size, "table_size")
        if history_bits < 1:
            raise ValueError("history_bits must be at least 1")
        self.table_size = table_size
        self.mask = table_size - 1
        self.history_bits = history_bits
        self.threshold = max(1, threshold if threshold is not None else int((1.93 * history_bits) + 14))
        self.weight_limit = max(1, weight_limit if weight_limit is not None else max(31, self.threshold * 2))
        self.history = [-1] * history_bits
        self.perceptrons = [[0] * (history_bits + 1) for _ in range(table_size)]

    def _index(self, address: int) -> int:
        return (address >> 2) & self.mask

    def _activation(self, address: int) -> int:
        weights = self.perceptrons[self._index(address)]
        return weights[0] + sum(weight * history_bit for weight, history_bit in zip(weights[1:], self.history))

    def predict(self, branch: BranchRecord) -> bool:
        return self._activation(branch.address) >= 0

    def update(self, branch: BranchRecord) -> None:
        target = 1 if branch.taken else -1
        index = self._index(branch.address)
        weights = self.perceptrons[index]
        activation = weights[0] + sum(weight * history_bit for weight, history_bit in zip(weights[1:], self.history))
        prediction = activation >= 0
        if prediction != branch.taken or abs(activation) <= self.threshold:
            weights[0] = _clamp_to_limit(weights[0] + target, self.weight_limit)
            for offset, history_bit in enumerate(self.history, start=1):
                weights[offset] = _clamp_to_limit(weights[offset] + (target * history_bit), self.weight_limit)
        self.history = [target, *self.history[:-1]]

    def snapshot(self) -> dict[str, Any]:
        trained_perceptrons = sum(1 for weights in self.perceptrons if any(weight != 0 for weight in weights))
        non_zero_weights = sum(1 for weights in self.perceptrons for weight in weights if weight != 0)
        max_abs_weight = max((abs(weight) for weights in self.perceptrons for weight in weights), default=0)
        return {
            "table_size": self.table_size,
            "history_bits": self.history_bits,
            "threshold": self.threshold,
            "weight_limit": self.weight_limit,
            "trained_perceptrons": trained_perceptrons,
            "non_zero_weights": non_zero_weights,
            "max_abs_weight": max_abs_weight,
            "final_history": "".join("1" if bit > 0 else "0" for bit in self.history),
        }


class TournamentPredictor(BranchPredictor):
    name = "tournament"

    def __init__(
        self,
        table_size: int = 16,
        history_bits: int = 4,
        default_chooser: int = 1,
    ) -> None:
        _validate_power_of_two(table_size, "table_size")
        if default_chooser not in {0, 1, 2, 3}:
            raise ValueError("default_chooser must be between 0 and 3")
        self.table_size = table_size
        self.mask = table_size - 1
        self.history_bits = history_bits
        self.default_chooser = default_chooser
        self.local_predictor = LocalHistoryPredictor(table_size=table_size, history_bits=history_bits)
        self.global_predictor = GSharePredictor(table_size=table_size, history_bits=history_bits)
        self.chooser = [default_chooser] * table_size

    def _index(self, address: int) -> int:
        return (address >> 2) & self.mask

    def _choose_global(self, address: int) -> bool:
        return self.chooser[self._index(address)] >= 2

    def predict(self, branch: BranchRecord) -> bool:
        local_prediction = self.local_predictor.predict(branch)
        global_prediction = self.global_predictor.predict(branch)
        return global_prediction if self._choose_global(branch.address) else local_prediction

    def update(self, branch: BranchRecord) -> None:
        local_prediction = self.local_predictor.predict(branch)
        global_prediction = self.global_predictor.predict(branch)
        chooser_index = self._index(branch.address)

        if local_prediction != global_prediction:
            if global_prediction == branch.taken:
                self.chooser[chooser_index] = min(3, self.chooser[chooser_index] + 1)
            elif local_prediction == branch.taken:
                self.chooser[chooser_index] = max(0, self.chooser[chooser_index] - 1)

        self.local_predictor.update(branch)
        self.global_predictor.update(branch)

    def snapshot(self) -> dict[str, Any]:
        trained_entries = sum(1 for value in self.chooser if value != self.default_chooser)
        gshare_favored_entries = sum(1 for value in self.chooser if value >= 2)
        return {
            "table_size": self.table_size,
            "history_bits": self.history_bits,
            "trained_entries": trained_entries,
            "default_chooser": self.default_chooser,
            "gshare_favored_entries": gshare_favored_entries,
            "chooser_table": {
                "strongly_local": sum(1 for value in self.chooser if value == 0),
                "weakly_local": sum(1 for value in self.chooser if value == 1),
                "weakly_global": sum(1 for value in self.chooser if value == 2),
                "strongly_global": sum(1 for value in self.chooser if value == 3),
            },
            "local_predictor": self.local_predictor.snapshot(),
            "global_predictor": self.global_predictor.snapshot(),
        }


def _validate_power_of_two(value: int, label: str) -> None:
    if value < 2 or value & (value - 1) != 0:
        raise ValueError(f"{label} must be a power of two >= 2")


def _clamp_to_limit(value: int, limit: int) -> int:
    return max(-limit, min(limit, value))


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


def _append_generated_record(
    records: list[BranchRecord],
    *,
    address: int,
    taken: bool,
    target: int | None = None,
    label: str | None = None,
) -> None:
    records.append(
        BranchRecord(
            address=address,
            taken=taken,
            target=target,
            label=label,
            line_number=len(records) + 1,
        )
    )


def _generate_loop_heavy_trace(branches: int, seed: int) -> list[BranchRecord]:
    del seed
    loop_specs = [
        {"address": 0x100, "target": 0x0F0, "iterations": 5, "label": "outer-loop"},
        {"address": 0x140, "target": 0x130, "iterations": 4, "label": "inner-loop"},
        {"address": 0x180, "target": 0x170, "iterations": 6, "label": "cleanup-loop"},
    ]
    records: list[BranchRecord] = []
    spec_index = 0
    while len(records) < branches:
        spec = loop_specs[spec_index % len(loop_specs)]
        trip_count = spec["iterations"]
        for offset in range(trip_count):
            if len(records) >= branches:
                break
            taken = offset < trip_count - 1
            suffix = "backedge" if taken else "exit"
            target = spec["target"] if taken else spec["address"] + 4
            _append_generated_record(
                records,
                address=spec["address"],
                taken=taken,
                target=target,
                label=f"{spec['label']}-{suffix}",
            )
        spec_index += 1
    return records


def _generate_random_biased_trace(branches: int, seed: int) -> list[BranchRecord]:
    rng = random.Random(seed)
    branch_profiles = [
        {"address": 0x240, "target": 0x2A0, "taken_probability": 0.88, "label": "hot-fast-path"},
        {"address": 0x280, "target": 0x2E0, "taken_probability": 0.72, "label": "cache-hit"},
        {"address": 0x2C0, "target": 0x320, "taken_probability": 0.38, "label": "rare-fallback"},
        {"address": 0x300, "target": 0x360, "taken_probability": 0.12, "label": "guard-rail"},
    ]
    records: list[BranchRecord] = []
    while len(records) < branches:
        profile = branch_profiles[len(records) % len(branch_profiles)]
        taken = rng.random() < profile["taken_probability"]
        _append_generated_record(
            records,
            address=profile["address"],
            taken=taken,
            target=profile["target"] if taken else profile["address"] + 4,
            label=profile["label"],
        )
    return records


def _generate_tournament_style_trace(branches: int, seed: int) -> list[BranchRecord]:
    rng = random.Random(seed)
    records: list[BranchRecord] = []
    loop_phase = 0
    round_index = 0
    while len(records) < branches:
        driver_taken = round_index % 2 == 0
        _append_generated_record(
            records,
            address=0x340,
            taken=driver_taken,
            target=0x390 if driver_taken else 0x344,
            label="history-driver",
        )
        if len(records) >= branches:
            break

        _append_generated_record(
            records,
            address=0x380,
            taken=driver_taken,
            target=0x3D0 if driver_taken else 0x384,
            label="history-follower",
        )
        if len(records) >= branches:
            break

        loop_taken = loop_phase < 3
        _append_generated_record(
            records,
            address=0x100,
            taken=loop_taken,
            target=0x0F0 if loop_taken else 0x104,
            label="loop-backedge" if loop_taken else "loop-exit",
        )
        loop_phase = (loop_phase + 1) % 4
        if len(records) >= branches:
            break

        biased_taken = rng.random() < 0.75
        _append_generated_record(
            records,
            address=0x3C0,
            taken=biased_taken,
            target=0x420 if biased_taken else 0x3C4,
            label="biased-cleanup",
        )
        round_index += 1
    return records


def _generate_alias_thrash_trace(branches: int, seed: int) -> list[BranchRecord]:
    rng = random.Random(seed)
    records: list[BranchRecord] = []
    collision_groups = [
        (
            {"address": 0x100, "target": 0x0F0, "taken_probability": 0.92, "label": "alias-hot-taken-a"},
            {"address": 0x140, "target": 0x144, "taken_probability": 0.12, "label": "alias-cold-not-a"},
        ),
        (
            {"address": 0x110, "target": 0x100, "taken_probability": 0.82, "label": "alias-hot-taken-b"},
            {"address": 0x150, "target": 0x154, "taken_probability": 0.18, "label": "alias-cold-not-b"},
        ),
    ]

    pair_index = 0
    while len(records) < branches:
        hot_branch, cold_branch = collision_groups[pair_index % len(collision_groups)]
        for branch in (hot_branch, cold_branch):
            if len(records) >= branches:
                break
            taken = rng.random() < branch["taken_probability"]
            target = branch["target"] if taken else branch["address"] + 4
            _append_generated_record(
                records,
                address=branch["address"],
                taken=taken,
                target=target,
                label=branch["label"],
            )
        pair_index += 1
    return records


def _generate_perceptron_majority_trace(branches: int, seed: int) -> list[BranchRecord]:
    rng = random.Random(seed)
    records: list[BranchRecord] = []
    history = [1 if rng.random() < 0.5 else -1 for _ in range(12)]
    weights = [3, 2, -2, 2, 1, -1, 1, 1, -1, 2, -2, 1]
    bias = -1

    while len(records) < branches:
        score = bias + sum(weight * history_bit for weight, history_bit in zip(weights, history))
        taken = score >= 0
        target = 0x4B0 if taken else 0x484
        _append_generated_record(
            records,
            address=0x480,
            taken=taken,
            target=target,
            label="perceptron-majority-target",
        )
        history = [1 if taken else -1, *history[:-1]]
    return records


SYNTHETIC_TRACE_BUILDERS: dict[str, Callable[[int, int], list[BranchRecord]]] = {
    "loop-heavy": _generate_loop_heavy_trace,
    "random-biased": _generate_random_biased_trace,
    "tournament-style": _generate_tournament_style_trace,
    "alias-thrash": _generate_alias_thrash_trace,
    "perceptron-majority": _generate_perceptron_majority_trace,
}


def generate_synthetic_trace(workload: str, branches: int = 32, seed: int = 7) -> list[BranchRecord]:
    normalized = workload.strip().lower()
    if branches < 4:
        raise ValueError("branches must be at least 4 for a meaningful synthetic trace")
    builder = SYNTHETIC_TRACE_BUILDERS.get(normalized)
    if builder is None:
        supported = ", ".join(sorted(SYNTHETIC_TRACE_BUILDERS))
        raise ValueError(f"unsupported synthetic workload: {workload}. Expected one of: {supported}")
    return builder(branches, seed)


def format_trace(records: list[BranchRecord]) -> str:
    lines: list[str] = []
    for record in records:
        tokens = [record.address_hex, "T" if record.taken else "N"]
        if record.target is not None:
            tokens.append(hex(record.target))
        if record.label:
            tokens.append(record.label)
        lines.append(" ".join(tokens))
    return "\n".join(lines)


def summarize_trace(records: list[BranchRecord]) -> dict[str, Any]:
    if not records:
        raise ValueError("records must not be empty")
    taken_count = sum(1 for record in records if record.taken)
    address_counts: dict[int, int] = {}
    label_counts: dict[str, int] = {}
    for record in records:
        address_counts[record.address] = address_counts.get(record.address, 0) + 1
        if record.label:
            label_counts[record.label] = label_counts.get(record.label, 0) + 1
    return {
        "total_branches": len(records),
        "taken_branches": taken_count,
        "not_taken_branches": len(records) - taken_count,
        "taken_percent": round((taken_count / len(records)) * 100, 3),
        "unique_addresses": len(address_counts),
        "address_counts": {hex(address): count for address, count in sorted(address_counts.items())},
        "label_counts": dict(sorted(label_counts.items())),
    }


def summarize_table_aliasing(records: list[BranchRecord], table_size: int) -> dict[str, Any]:
    if not records:
        raise ValueError("records must not be empty")
    _validate_power_of_two(table_size, "table_size")

    groups: dict[int, dict[str, Any]] = {}
    for record in records:
        index = (record.address >> 2) & (table_size - 1)
        group = groups.setdefault(index, {"index": index, "addresses": {}})
        address_entry = group["addresses"].setdefault(
            record.address,
            {
                "total": 0,
                "taken": 0,
                "not_taken": 0,
                "labels": set(),
            },
        )
        address_entry["total"] += 1
        if record.taken:
            address_entry["taken"] += 1
        else:
            address_entry["not_taken"] += 1
        if record.label:
            address_entry["labels"].add(record.label)

    collision_groups: list[dict[str, Any]] = []
    total_collision_events = 0
    for index, group in sorted(groups.items()):
        addresses = group["addresses"]
        if len(addresses) < 2:
            continue
        sorted_addresses: list[dict[str, Any]] = []
        dominant_outcomes: set[str] = set()
        branch_events = 0
        for address, stats in sorted(addresses.items()):
            taken_percent = round((stats["taken"] / stats["total"]) * 100, 3)
            dominant_outcome = "mixed"
            if stats["taken"] > stats["not_taken"]:
                dominant_outcome = "taken"
            elif stats["not_taken"] > stats["taken"]:
                dominant_outcome = "not-taken"
            dominant_outcomes.add(dominant_outcome)
            branch_events += stats["total"]
            sorted_addresses.append(
                {
                    "address": hex(address),
                    "total": stats["total"],
                    "taken": stats["taken"],
                    "not_taken": stats["not_taken"],
                    "taken_percent": taken_percent,
                    "dominant_outcome": dominant_outcome,
                    "labels": sorted(stats["labels"]),
                }
            )
        total_collision_events += branch_events
        collision_groups.append(
            {
                "index": index,
                "index_hex": hex(index),
                "address_count": len(sorted_addresses),
                "branch_events": branch_events,
                "conflicting_biases": len(dominant_outcomes) > 1,
                "addresses": sorted_addresses,
            }
        )

    conflict_groups = [group for group in collision_groups if group["conflicting_biases"]]
    return {
        "table_size": table_size,
        "unique_indices": len(groups),
        "colliding_indices": len(collision_groups),
        "conflicting_indices": len(conflict_groups),
        "branch_events_in_collisions": total_collision_events,
        "collision_groups": sorted(
            collision_groups,
            key=lambda group: (-group["conflicting_biases"], -group["branch_events"], group["index"]),
        )[:5],
    }


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
        simulate_trace(records, LocalHistoryPredictor(table_size=table_size, history_bits=history_bits)),
        simulate_trace(records, GSharePredictor(table_size=table_size, history_bits=history_bits)),
        simulate_trace(records, PerceptronPredictor(table_size=table_size, history_bits=history_bits)),
        simulate_trace(records, TournamentPredictor(table_size=table_size, history_bits=history_bits)),
    ]
    return sorted(results, key=lambda item: (-item.accuracy, item.mispredictions, item.predictor))


def _first_result_from_group(results: list[SimulationResult], allowed_names: set[str]) -> SimulationResult:
    match = next((result for result in results if result.predictor in allowed_names), None)
    if match is None:
        raise ValueError(f"missing predictors from group: {sorted(allowed_names)}")
    return match


def run_workload_sweep(
    workloads: list[str] | None = None,
    *,
    branches_override: int | None = None,
    table_size_override: int | None = None,
    history_bits_override: int | None = None,
    seed_override: int | None = None,
    trace_dir: Path | None = None,
) -> list[dict[str, Any]]:
    selected = workloads or list(SYNTHETIC_WORKLOADS)
    scenarios: list[dict[str, Any]] = []
    if trace_dir is not None:
        trace_dir.mkdir(parents=True, exist_ok=True)

    for workload in selected:
        if workload not in WORKLOAD_SWEEP_PROFILES:
            supported = ", ".join(sorted(WORKLOAD_SWEEP_PROFILES))
            raise ValueError(f"unsupported sweep workload: {workload}. Expected one of: {supported}")
        profile = WORKLOAD_SWEEP_PROFILES[workload]
        branches = branches_override if branches_override is not None else int(profile["branches"])
        table_size = table_size_override if table_size_override is not None else int(profile["table_size"])
        history_bits = history_bits_override if history_bits_override is not None else int(profile["history_bits"])
        seed = seed_override if seed_override is not None else int(profile["seed"])

        records = generate_synthetic_trace(workload, branches=branches, seed=seed)
        trace_output: Path | None = None
        if trace_dir is not None:
            trace_output = trace_dir / f"{workload}-seed{seed}.trace"
            trace_output.write_text(f"{format_trace(records)}\n", encoding="utf-8")

        trace_summary = summarize_trace(records)
        alias_summary = summarize_table_aliasing(records, table_size=table_size)
        results = compare_predictors(records, table_size=table_size, history_bits=history_bits)
        best = results[0]
        runner_up = results[1]
        best_simple = _first_result_from_group(results, SIMPLE_PREDICTOR_NAMES)
        best_advanced = _first_result_from_group(results, ADVANCED_PREDICTOR_NAMES)
        scenarios.append(
            {
                "workload": workload,
                "headline": profile["headline"],
                "config": {
                    "branches": branches,
                    "seed": seed,
                    "table_size": table_size,
                    "history_bits": history_bits,
                },
                "trace_output": str(trace_output) if trace_output is not None else None,
                "trace_summary": trace_summary,
                "alias_summary": alias_summary,
                "best_predictor": best.predictor,
                "runner_up_predictor": runner_up.predictor,
                "winner_margin_percent": round((best.accuracy - runner_up.accuracy) * 100, 3),
                "best_simple_predictor": best_simple.predictor,
                "best_simple_accuracy_percent": round(best_simple.accuracy * 100, 3),
                "best_advanced_predictor": best_advanced.predictor,
                "best_advanced_accuracy_percent": round(best_advanced.accuracy * 100, 3),
                "results": [result.to_dict() for result in results],
            }
        )

    return scenarios


def format_sweep_summary_table(scenarios: list[dict[str, Any]]) -> str:
    lines = [
        "workload              best predictor    accuracy   gap     simple best       advanced best",
        "--------------------  ----------------  ---------  ------  ----------------  ----------------",
    ]
    for scenario in scenarios:
        lines.append(
            f"{scenario['workload']:<20}  {scenario['best_predictor']:<16}  "
            f"{scenario['results'][0]['accuracy_percent']:>7.2f}%  "
            f"{scenario['winner_margin_percent']:>5.2f}pp  "
            f"{scenario['best_simple_predictor']:<16}  {scenario['best_advanced_predictor']:<16}"
        )
    return "\n".join(lines)


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
    if normalized == "local-history":
        return LocalHistoryPredictor(table_size=table_size, history_bits=history_bits)
    if normalized == "gshare":
        return GSharePredictor(table_size=table_size, history_bits=history_bits)
    if normalized == "perceptron":
        return PerceptronPredictor(table_size=table_size, history_bits=history_bits)
    if normalized == "tournament":
        return TournamentPredictor(table_size=table_size, history_bits=history_bits)
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


def _build_comparison_talking_points(
    results: list[SimulationResult],
    trace_summary: dict[str, Any],
    alias_summary: dict[str, Any],
) -> list[str]:
    by_name = {result.predictor: result for result in results}
    best = results[0]
    runner_up = results[1]
    points: list[str] = []

    if abs(best.accuracy - runner_up.accuracy) < 1e-9:
        tied = [result.predictor for result in results if abs(result.accuracy - best.accuracy) < 1e-9]
        points.append(
            f"Top spot is a tie at {best.accuracy * 100:.2f}% accuracy across {', '.join(tied)}."
        )
    else:
        points.append(
            f"{best.predictor} wins this trace at {best.accuracy * 100:.2f}% accuracy, "
            f"beating {runner_up.predictor} by {(best.accuracy - runner_up.accuracy) * 100:.2f} percentage points."
        )

    one_bit = by_name.get("one-bit")
    two_bit = by_name.get("two-bit")
    if one_bit is not None and two_bit is not None:
        delta = (two_bit.accuracy - one_bit.accuracy) * 100
        if delta >= 0:
            points.append(
                f"Two-bit vs one-bit: {two_bit.accuracy * 100:.2f}% vs {one_bit.accuracy * 100:.2f}% accuracy "
                f"({delta:.2f} pp in favor of two-bit)."
            )
        else:
            points.append(
                f"Two-bit vs one-bit: {two_bit.accuracy * 100:.2f}% vs {one_bit.accuracy * 100:.2f}% accuracy "
                f"({abs(delta):.2f} pp in favor of one-bit on this trace)."
            )

    advanced_best = next((result for result in results if result.predictor in ADVANCED_PREDICTOR_NAMES), None)
    simple_best = next((result for result in results if result.predictor in SIMPLE_PREDICTOR_NAMES), None)
    if advanced_best is not None and simple_best is not None:
        points.append(
            f"Best advanced predictor: {advanced_best.predictor} at {advanced_best.accuracy * 100:.2f}% "
            f"vs best simple baseline {simple_best.predictor} at {simple_best.accuracy * 100:.2f}%."
        )

    hardest = best.hardest_branches[0] if best.hardest_branches else None
    if hardest is not None:
        points.append(
            f"Hardest branch for the winning predictor is {hardest['address']} with "
            f"{hardest['mispredictions']} misses across {hardest['total']} executions."
        )

    if alias_summary["colliding_indices"]:
        points.append(
            f"Static table aliasing: {alias_summary['colliding_indices']} colliding indices at table size {alias_summary['table_size']} "
            f"({alias_summary['conflicting_indices']} with conflicting taken/not-taken biases)."
        )
        top_collision = next(
            (group for group in alias_summary["collision_groups"] if group["conflicting_biases"]),
            alias_summary["collision_groups"][0],
        )
        addresses = ", ".join(item["address"] for item in top_collision["addresses"])
        points.append(
            f"Worst alias bucket: index {top_collision['index_hex']} merges {addresses} across {top_collision['branch_events']} branch events."
        )

    label_counts = trace_summary.get("label_counts", {})
    if label_counts:
        top_labels = sorted(label_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
        points.append(
            "Top labeled branch motifs: " + ", ".join(f"{label} ({count})" for label, count in top_labels) + "."
        )

    return points[:5]


def render_comparison_markdown(
    *,
    trace_path: Path,
    trace_summary: dict[str, Any],
    alias_summary: dict[str, Any],
    results: list[SimulationResult],
    table_size: int,
    history_bits: int,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    best = results[0]
    worst = results[-1]
    talking_points = _build_comparison_talking_points(results, trace_summary, alias_summary)
    address_counts = list(trace_summary["address_counts"].items())[:5]
    label_counts = list(trace_summary["label_counts"].items())[:5]

    lines = [
        f"# Branch predictor comparison card: `{trace_path.stem}`",
        "",
        f"- Generated: `{generated}`",
        f"- Trace: `{trace_path}`",
        f"- Branches: `{trace_summary['total_branches']}` across `{trace_summary['unique_addresses']}` static PCs",
        f"- Taken rate: `{trace_summary['taken_percent']:.3f}%` (`{trace_summary['taken_branches']}` taken / `{trace_summary['not_taken_branches']}` not taken)",
        f"- Predictor config: table size `{table_size}` · history bits `{history_bits}`",
        "",
        "## Headline",
        "",
        f"- Best predictor: `{best.predictor}` at `{best.accuracy * 100:.2f}%` accuracy with `{best.mispredictions}` mispredictions.",
        f"- Weakest predictor on this trace: `{worst.predictor}` at `{worst.accuracy * 100:.2f}%` accuracy.",
        "",
        "## Ranking",
        "",
        "| Predictor | Accuracy | Mispredictions | MPKI | Hardest branch |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for result in results:
        hardest = result.hardest_branches[0]["address"] if result.hardest_branches else "-"
        lines.append(
            f"| `{result.predictor}` | `{result.accuracy * 100:.2f}%` | `{result.mispredictions}` | `{result.mpki:.1f}` | `{hardest}` |"
        )

    lines.extend(["", "## Portfolio talking points", ""])
    lines.extend(f"- {point}" for point in talking_points)

    lines.extend(["", "## Trace mix", ""])
    lines.append(
        "- Top PCs: " + ", ".join(f"`{address}` × `{count}`" for address, count in address_counts)
    )
    if label_counts:
        lines.append(
            "- Top labels: " + ", ".join(f"`{label}` × `{count}`" for label, count in label_counts)
        )
    else:
        lines.append("- Top labels: `(none)`")

    lines.extend(["", "## Table aliasing", ""])
    lines.append(
        f"- `{alias_summary['colliding_indices']}` colliding index groups at table size `{alias_summary['table_size']}`; "
        f"`{alias_summary['conflicting_indices']}` groups mix opposite dominant biases."
    )
    lines.append(
        f"- `{alias_summary['branch_events_in_collisions']}` branch events land in colliding buckets on this trace."
    )
    if alias_summary["collision_groups"]:
        for group in alias_summary["collision_groups"]:
            members = ", ".join(
                f"`{item['address']}` ({item['taken_percent']:.1f}% taken)" for item in group["addresses"]
            )
            suffix = "conflicting biases" if group["conflicting_biases"] else "similar biases"
            lines.append(
                f"- Index `{group['index_hex']}`: {members} · `{group['branch_events']}` events · {suffix}."
            )
    else:
        lines.append("- No static PC aliasing for this table size.")

    if best.hardest_branches:
        lines.extend(["", "## Hardest branches for the winning predictor", ""])
        for branch in best.hardest_branches:
            lines.append(
                f"- `{branch['address']}` · `{branch['mispredictions']}` mispredictions over `{branch['total']}` executions "
                f"(`{branch['accuracy_percent']:.2f}%` accuracy on that branch)"
            )

    return "\n".join(lines) + "\n"


def _svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _svg_text(x: float, y: float, text: str, *, size: int = 14, weight: str = "normal", fill: str = "#111827") -> str:
    font_family = "ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    return (
        f"<text x=\"{x:.1f}\" y=\"{y:.1f}\" font-size=\"{size}\" font-weight=\"{weight}\" "
        f"fill=\"{fill}\" font-family=\"{font_family}\">{_svg_escape(text)}</text>"
    )


def _truncate_svg_text(text: str, limit: int = 68) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _wrap_svg_text(text: str, *, max_chars: int = 44) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return ["(none)"]
    return textwrap.wrap(
        normalized,
        width=max_chars,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [normalized]


def _svg_add_wrapped_text(
    parts: list[str],
    x: float,
    y: float,
    text: str,
    *,
    max_chars: int = 44,
    line_height: int = 18,
    size: int = 13,
    weight: str = "normal",
    fill: str = "#334155",
) -> float:
    lines = _wrap_svg_text(text, max_chars=max_chars)
    for index, line in enumerate(lines):
        parts.append(_svg_text(x, y + index * line_height, line, size=size, weight=weight, fill=fill))
    return y + max(0, len(lines) - 1) * line_height


def render_comparison_svg(
    *,
    trace_path: Path,
    trace_summary: dict[str, Any],
    alias_summary: dict[str, Any],
    results: list[SimulationResult],
    table_size: int,
    history_bits: int,
) -> str:
    width = 960
    height = 640
    best = results[0]
    runner_up = results[1]
    talking_points = _build_comparison_talking_points(results, trace_summary, alias_summary)[:3]
    hardest_branches = best.hardest_branches[:3]
    gap_text = (
        f"Tie at {best.accuracy * 100:.2f}%"
        if abs(best.accuracy - runner_up.accuracy) < 1e-9
        else f"{(best.accuracy - runner_up.accuracy) * 100:.2f} pp"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Branch predictor comparison card</title>',
        f'<desc id="desc">Comparison card for {trace_path.stem} showing branch predictor accuracy rankings and trace insights.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 40, "Branch predictor comparison card", size=28, weight="700"),
        _svg_text(28, 66, f"Trace: {trace_path.stem} · branches={trace_summary['total_branches']} · unique PCs={trace_summary['unique_addresses']} · table={table_size} · history={history_bits}", size=14, fill="#334155"),
    ]

    cards = [
        (28, "Best predictor", best.predictor, f"{best.accuracy * 100:.2f}% accuracy"),
        (258, "Runner-up gap", gap_text, runner_up.predictor),
        (488, "Taken rate", f"{trace_summary['taken_percent']:.2f}%", f"{trace_summary['taken_branches']} taken / {trace_summary['not_taken_branches']} not taken"),
        (718, "Worst predictor", results[-1].predictor, f"{results[-1].accuracy * 100:.2f}% accuracy"),
    ]
    for x, label, value, subtitle in cards:
        parts.append(f'<rect x="{x}" y="92" width="214" height="86" rx="16" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(x + 18, 120, label, size=13, weight="700", fill="#475569"))
        parts.append(_svg_text(x + 18, 152, value, size=24, weight="700", fill="#0f172a"))
        parts.append(_svg_text(x + 18, 170, _truncate_svg_text(subtitle, 30), size=11, fill="#64748b"))

    left_x = 28
    left_y = 214
    left_w = 500
    left_h = 376
    parts.append(f'<rect x="{left_x}" y="{left_y}" width="{left_w}" height="{left_h}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(left_x + 20, left_y + 34, "Accuracy ranking", size=20, weight="700"))
    chart_left = left_x + 132
    chart_right = left_x + left_w - 28
    chart_width = chart_right - chart_left
    row_top = left_y + 78
    row_height = 40
    for tick in range(0, 101, 20):
        tick_x = chart_left + chart_width * (tick / 100)
        parts.append(f'<line x1="{tick_x:.1f}" y1="{left_y + 58}" x2="{tick_x:.1f}" y2="{left_y + left_h - 24}" stroke="#e2e8f0" stroke-width="1" />')
        parts.append(_svg_text(tick_x - 10, left_y + 54, str(tick), size=10, fill="#94a3b8"))
    for index, result in enumerate(results):
        row_y = row_top + index * row_height
        bar_width = chart_width * result.accuracy
        bar_color = "#2563eb" if index == 0 else ("#7c3aed" if result.predictor in {"local-history", "gshare", "perceptron", "tournament"} else "#94a3b8")
        parts.append(_svg_text(left_x + 20, row_y + 16, result.predictor, size=13, weight="700", fill="#0f172a"))
        parts.append(f'<rect x="{chart_left}" y="{row_y}" width="{chart_width:.1f}" height="18" rx="9" fill="#e2e8f0" />')
        parts.append(f'<rect x="{chart_left}" y="{row_y}" width="{bar_width:.1f}" height="18" rx="9" fill="{bar_color}" />')
        parts.append(_svg_text(chart_right - 70, row_y + 15, f"{result.accuracy * 100:.2f}%", size=12, weight="700", fill="#0f172a"))
        hardest = result.hardest_branches[0]["address"] if result.hardest_branches else "-"
        parts.append(_svg_text(chart_left, row_y + 33, f"mispreds={result.mispredictions} · hardest={hardest}", size=11, fill="#64748b"))

    right_x = 556
    right_y = 214
    right_w = 376
    parts.append(f'<rect x="{right_x}" y="{right_y}" width="{right_w}" height="178" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(right_x + 20, right_y + 34, "Interview-ready talking points", size=20, weight="700"))
    current_y = right_y + 66
    for point in talking_points:
        parts.append(_svg_text(right_x + 20, current_y, "•", size=15, weight="700", fill="#2563eb"))
        current_y = _svg_add_wrapped_text(parts, right_x + 34, current_y, point, max_chars=40, size=13, fill="#334155") + 24

    lower_y = 412
    parts.append(f'<rect x="{right_x}" y="{lower_y}" width="{right_w}" height="178" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(right_x + 20, lower_y + 34, "Hardest branches for the winner", size=20, weight="700"))
    if hardest_branches:
        current_y = lower_y + 66
        for branch in hardest_branches:
            summary = (
                f"{branch['address']} · {branch['mispredictions']} misses / {branch['total']} execs · "
                f"{branch['accuracy_percent']:.2f}% branch accuracy"
            )
            current_y = _svg_add_wrapped_text(parts, right_x + 20, current_y, summary, max_chars=42, size=13, fill="#334155") + 20
    else:
        parts.append(_svg_text(right_x + 20, lower_y + 66, "No mispredicted branches on this trace.", size=13, fill="#334155"))

    footer = "Use this card next to the Markdown report to explain why simple vs history-aware predictors diverge on the same trace."
    parts.append(_svg_text(28, 620, _truncate_svg_text(footer, 120), size=12, fill="#475569"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


def render_sweep_markdown(*, scenarios: list[dict[str, Any]]) -> str:
    generated = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    lines = [
        "# Branch predictor trace-family sweep",
        "",
        f"- Generated: `{generated}`",
        f"- Workloads: `{len(scenarios)}` synthetic families run in one batch command",
        "- Goal: show how the recommended trace/config pairs shift the best predictor across loop, bias, aliasing, mixed-history, and perceptron-friendly cases.",
        "",
        "## Overview",
        "",
        "| Workload | Focus | Branches | Table | History | Best | Accuracy | Runner-up | Gap |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: |",
    ]
    for scenario in scenarios:
        best = scenario["results"][0]
        lines.append(
            f"| `{scenario['workload']}` | {scenario['headline']} | `{scenario['config']['branches']}` | `{scenario['config']['table_size']}` | `{scenario['config']['history_bits']}` | `{scenario['best_predictor']}` | `{best['accuracy_percent']:.2f}%` | `{scenario['runner_up_predictor']}` | `{scenario['winner_margin_percent']:.2f} pp` |"
        )

    lines.extend(["", "## Per-workload notes", ""])
    for scenario in scenarios:
        best = scenario["results"][0]
        alias_summary = scenario["alias_summary"]
        lines.extend(
            [
                f"### `{scenario['workload']}`",
                "",
                f"- Focus: {scenario['headline']}",
                f"- Config: `branches={scenario['config']['branches']}` · `seed={scenario['config']['seed']}` · `table={scenario['config']['table_size']}` · `history={scenario['config']['history_bits']}`",
                f"- Winner: `{scenario['best_predictor']}` at `{best['accuracy_percent']:.2f}%` with `{best['mispredictions']}` mispredictions.",
                f"- Best simple baseline: `{scenario['best_simple_predictor']}` at `{scenario['best_simple_accuracy_percent']:.2f}%`.",
                f"- Best advanced predictor: `{scenario['best_advanced_predictor']}` at `{scenario['best_advanced_accuracy_percent']:.2f}%`.",
                f"- Static aliasing: `{alias_summary['colliding_indices']}` colliding buckets, `{alias_summary['conflicting_indices']}` with conflicting dominant biases.",
                "",
                "Top three predictors:",
            ]
        )
        for result in scenario["results"][:3]:
            lines.append(
                f"- `{result['predictor']}` · `{result['accuracy_percent']:.2f}%` accuracy · `{result['mispredictions']}` mispredictions"
            )
        lines.append("")

    lines.extend(
        [
            "## Portfolio usage",
            "",
            "- Use this sweep report when you want one artifact that compares multiple branch families without manually running five separate `generate` + `compare` commands.",
            "- Pair the sweep SVG with the existing per-trace cards when you need both an overview slide and deeper single-trace evidence.",
            "- The report is intentionally configuration-aware so interviewers can see that long-history perceptron cases use deeper history than simple bias/loop demos.",
            "",
        ]
    )
    return "\n".join(lines)


def render_sweep_svg(*, scenarios: list[dict[str, Any]]) -> str:
    width = 1120
    row_height = 92
    height = 170 + (row_height * len(scenarios)) + 56
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Branch predictor trace-family sweep</title>',
        '<desc id="desc">Batch branch predictor sweep summary across multiple synthetic workload families.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 40, "Branch predictor trace-family sweep", size=28, weight="700"),
        _svg_text(28, 66, f"{len(scenarios)} workload families · one batch command · recommended configs per trace family", size=14, fill="#334155"),
    ]
    header_y = 104
    parts.append(f'<rect x="28" y="{header_y}" width="1064" height="42" rx="14" fill="#e2e8f0" />')
    for x, label in [(46, 'Workload'), (274, 'Focus'), (618, 'Winner'), (780, 'Accuracy'), (902, 'Gap'), (980, 'Simple vs advanced')]:
        parts.append(_svg_text(x, header_y + 27, label, size=13, weight='700', fill='#334155'))

    start_y = header_y + 60
    for index, scenario in enumerate(scenarios):
        y = start_y + index * row_height
        best = scenario['results'][0]
        advanced_gap = scenario['best_advanced_accuracy_percent'] - scenario['best_simple_accuracy_percent']
        parts.append(f'<rect x="28" y="{y}" width="1064" height="76" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(46, y + 30, scenario['workload'], size=16, weight='700'))
        _svg_add_wrapped_text(parts, 46, y + 50, scenario['headline'], max_chars=26, size=12, fill='#64748b')
        _svg_add_wrapped_text(parts, 274, y + 30, f"branches={scenario['config']['branches']} · table={scenario['config']['table_size']} · history={scenario['config']['history_bits']} · seed={scenario['config']['seed']}", max_chars=42, size=12, fill='#334155')
        parts.append(_svg_text(618, y + 30, scenario['best_predictor'], size=15, weight='700', fill='#0f172a'))
        parts.append(_svg_text(618, y + 50, f"runner-up: {scenario['runner_up_predictor']}", size=12, fill='#64748b'))
        parts.append(f'<rect x="780" y="{y + 20}" width="96" height="16" rx="8" fill="#e2e8f0" />')
        parts.append(f'<rect x="780" y="{y + 20}" width="{96 * (best["accuracy_percent"] / 100):.1f}" height="16" rx="8" fill="#2563eb" />')
        parts.append(_svg_text(780, y + 52, f"{best['accuracy_percent']:.2f}%", size=12, weight='700'))
        parts.append(_svg_text(902, y + 38, f"{scenario['winner_margin_percent']:.2f} pp", size=13, weight='700', fill='#0f172a'))
        parts.append(_svg_text(980, y + 30, scenario['best_simple_predictor'], size=13, weight='700', fill='#475569'))
        parts.append(_svg_text(980, y + 50, f"{scenario['best_simple_accuracy_percent']:.2f}% → {scenario['best_advanced_predictor']} {scenario['best_advanced_accuracy_percent']:.2f}% ({advanced_gap:+.2f} pp)", size=11, fill='#64748b'))

    footer_y = height - 24
    parts.append(_svg_text(28, footer_y, 'Pair this sweep card with the per-trace Markdown/SVG cards when you need both overview and drill-down evidence.', size=12, fill='#475569'))
    parts.append('</svg>')
    return ''.join(parts) + '\n'


def write_markdown_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def write_svg_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


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
        "history_bits": {"help": "History-register bits for local-history, gshare, and tournament predictors.", "type": int, "default": 4},
    }

    compare_parser = subparsers.add_parser("compare", help="Run a fixed predictor suite and rank the results.")
    compare_parser.add_argument("trace", **common_help["trace"])
    compare_parser.add_argument("--table-size", **common_help["table_size"])
    compare_parser.add_argument("--history-bits", **common_help["history_bits"])
    compare_parser.add_argument("--markdown-out", type=Path, help="Write a Markdown comparison card for the ranked predictor suite.")
    compare_parser.add_argument("--svg-out", type=Path, help="Write an SVG comparison card for the ranked predictor suite.")
    compare_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text table.")

    simulate_parser = subparsers.add_parser("simulate", help="Run one specific predictor on the trace.")
    simulate_parser.add_argument("trace", **common_help["trace"])
    simulate_parser.add_argument(
        "--predictor",
        choices=["always-taken", "always-not-taken", "one-bit", "two-bit", "local-history", "gshare", "perceptron", "tournament"],
        default="two-bit",
        help="Predictor to simulate.",
    )
    simulate_parser.add_argument("--table-size", **common_help["table_size"])
    simulate_parser.add_argument("--history-bits", **common_help["history_bits"])
    simulate_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a synthetic branch trace for loop-heavy, random-biased, alias-thrash, perceptron-majority, or mixed tournament-style workloads.",
    )
    generate_parser.add_argument("workload", choices=list(SYNTHETIC_WORKLOADS), help="Synthetic workload family to generate.")
    generate_parser.add_argument("--branches", type=int, default=32, help="How many branch records to generate.")
    generate_parser.add_argument("--seed", type=int, default=7, help="Random seed for workloads that use randomness.")
    generate_parser.add_argument("--output", help="Optional path to write the generated trace text.")
    generate_parser.add_argument("--json", action="store_true", help="Emit a JSON summary instead of raw trace text.")

    sweep_parser = subparsers.add_parser(
        "sweep",
        help="Batch-generate one or more synthetic workload families and compare predictors in one run.",
    )
    sweep_parser.add_argument(
        "workloads",
        nargs="*",
        choices=list(SYNTHETIC_WORKLOADS),
        help="Optional subset of workload families to sweep. Defaults to all built-in synthetic workloads.",
    )
    sweep_parser.add_argument("--branches", type=int, help="Override the branch count for every selected workload.")
    sweep_parser.add_argument("--table-size", type=int, help="Override the predictor table size for every selected workload.")
    sweep_parser.add_argument("--history-bits", type=int, help="Override the history bits for every selected workload.")
    sweep_parser.add_argument("--seed", type=int, help="Override the random seed for every selected workload.")
    sweep_parser.add_argument("--trace-dir", type=Path, help="Optional directory to write the generated trace files for the sweep.")
    sweep_parser.add_argument("--markdown-out", type=Path, help="Write a Markdown sweep report.")
    sweep_parser.add_argument("--svg-out", type=Path, help="Write an SVG sweep summary card.")
    sweep_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary table.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "generate":
            records = generate_synthetic_trace(args.workload, branches=args.branches, seed=args.seed)
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(f"{format_trace(records)}\n", encoding="utf-8")
            else:
                output_path = None

            summary = {
                "workload": args.workload,
                "seed": args.seed,
                **summarize_trace(records),
            }
            if args.json:
                payload = {
                    **summary,
                    "output": str(output_path) if output_path is not None else None,
                    "records": [record.to_dict() for record in records],
                }
                print(json.dumps(payload, indent=2, default=_json_default))
            elif output_path is not None:
                print(
                    f"wrote {len(records)} synthetic branches to {output_path} "
                    f"({summary['taken_percent']:.2f}% taken across {summary['unique_addresses']} PCs)"
                )
            else:
                print(format_trace(records))
            return 0

        if args.command == "sweep":
            scenarios = run_workload_sweep(
                list(args.workloads),
                branches_override=args.branches,
                table_size_override=args.table_size,
                history_bits_override=args.history_bits,
                seed_override=args.seed,
                trace_dir=args.trace_dir,
            )
            payload = {
                "workloads": [scenario["workload"] for scenario in scenarios],
                "scenario_count": len(scenarios),
                "scenarios": scenarios,
            }
            if getattr(args, "markdown_out", None):
                write_markdown_output(args.markdown_out, render_sweep_markdown(scenarios=scenarios))
                payload["markdown_output"] = str(args.markdown_out)
            if getattr(args, "svg_out", None):
                write_svg_output(args.svg_out, render_sweep_svg(scenarios=scenarios))
                payload["svg_output"] = str(args.svg_out)
            if args.json:
                print(json.dumps(payload, indent=2, default=_json_default))
            else:
                print(format_sweep_summary_table(scenarios))
                if "markdown_output" in payload:
                    print(f"markdown report: {payload['markdown_output']}")
                if "svg_output" in payload:
                    print(f"svg card: {payload['svg_output']}")
                if args.trace_dir is not None:
                    print(f"trace directory: {args.trace_dir}")
            return 0

        records = load_trace(args.trace)
        if args.command == "compare":
            trace_path = Path(args.trace)
            trace_summary = summarize_trace(records)
            alias_summary = summarize_table_aliasing(records, table_size=args.table_size)
            results = compare_predictors(records, table_size=args.table_size, history_bits=args.history_bits)
            payload = {
                "trace": str(trace_path),
                "table_size": args.table_size,
                "history_bits": args.history_bits,
                "trace_summary": trace_summary,
                "alias_summary": alias_summary,
                "total_branches": len(records),
                "results": [result.to_dict() for result in results],
                "best_predictor": results[0].predictor,
            }
            if getattr(args, "markdown_out", None):
                write_markdown_output(
                    args.markdown_out,
                    render_comparison_markdown(
                        trace_path=trace_path,
                        trace_summary=trace_summary,
                        alias_summary=alias_summary,
                        results=results,
                        table_size=args.table_size,
                        history_bits=args.history_bits,
                    ),
                )
                payload["markdown_output"] = str(args.markdown_out)
            if getattr(args, "svg_out", None):
                write_svg_output(
                    args.svg_out,
                    render_comparison_svg(
                        trace_path=trace_path,
                        trace_summary=trace_summary,
                        alias_summary=alias_summary,
                        results=results,
                        table_size=args.table_size,
                        history_bits=args.history_bits,
                    ),
                )
                payload["svg_output"] = str(args.svg_out)
            if args.json:
                print(json.dumps(payload, indent=2, default=_json_default))
            else:
                print(format_summary_table(results))
                print()
                print(f"best predictor: {results[0].predictor} ({results[0].accuracy * 100:.2f}% accuracy)")
                print(
                    f"static aliasing: {alias_summary['colliding_indices']} colliding indices at table size {alias_summary['table_size']} "
                    f"({alias_summary['conflicting_indices']} conflicting bias groups)"
                )
                if "markdown_output" in payload:
                    print(f"markdown card: {payload['markdown_output']}")
                if "svg_output" in payload:
                    print(f"svg card: {payload['svg_output']}")
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
