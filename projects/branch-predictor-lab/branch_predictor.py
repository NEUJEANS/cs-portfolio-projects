from __future__ import annotations

import argparse
import csv
import io
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

BUDGET_SWEEP_BUDGETS = (64, 128, 256, 512, 1024)
BUDGET_SWEEP_TABLE_SIZES = (4, 8, 16, 32, 64)
BUDGET_SWEEP_HISTORY_BITS = (1, 2, 4, 8, 12)
BUDGET_SWEEP_WEIGHT_LIMITS = (15, 31, 74)
TABLE_SIZE_ALIAS_SWEEP_TABLE_SIZES = (4, 8, 16, 32, 64)
BUDGET_SWEEP_PREDICTOR_NAMES = (
    "always-taken",
    "always-not-taken",
    "one-bit",
    "two-bit",
    "local-history",
    "gshare",
    "perceptron",
    "tournament",
)


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


def _dominant_outcome(*, taken: int, not_taken: int) -> str:
    if taken > not_taken:
        return "taken"
    if not_taken > taken:
        return "not-taken"
    return "mixed"


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
            dominant_outcome = _dominant_outcome(taken=stats["taken"], not_taken=stats["not_taken"])
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


def summarize_gshare_aliasing(records: list[BranchRecord], table_size: int, history_bits: int) -> dict[str, Any]:
    if not records:
        raise ValueError("records must not be empty")
    _validate_power_of_two(table_size, "table_size")
    if history_bits < 1:
        raise ValueError("history_bits must be at least 1")

    mask = table_size - 1
    history_mask = (1 << history_bits) - 1
    history = 0
    groups: dict[int, dict[str, Any]] = {}

    for offset, record in enumerate(records, start=1):
        index = ((record.address >> 2) ^ history) & mask
        history_string = format(history, f"0{history_bits}b")
        group = groups.setdefault(index, {"index": index, "contexts": {}})
        context_entry = group["contexts"].setdefault(
            (record.address, history),
            {
                "address": record.address,
                "history": history,
                "history_before": history_string,
                "total": 0,
                "taken": 0,
                "not_taken": 0,
                "labels": set(),
                "first_event": offset,
            },
        )
        context_entry["total"] += 1
        if record.taken:
            context_entry["taken"] += 1
        else:
            context_entry["not_taken"] += 1
        if record.label:
            context_entry["labels"].add(record.label)
        history = ((history << 1) | int(record.taken)) & history_mask

    collision_groups: list[dict[str, Any]] = []
    total_collision_events = 0
    cross_address_collisions = 0
    history_spread_collisions = 0
    for index, group in sorted(groups.items()):
        contexts = group["contexts"]
        if len(contexts) < 2:
            continue
        sorted_contexts: list[dict[str, Any]] = []
        dominant_outcomes: set[str] = set()
        branch_events = 0
        addresses = {address for address, _history in contexts}
        histories = {history_value for _address, history_value in contexts}
        for (_address, _history), stats in sorted(contexts.items(), key=lambda item: (item[0][0], item[0][1])):
            taken_percent = round((stats["taken"] / stats["total"]) * 100, 3)
            dominant_outcome = _dominant_outcome(taken=stats["taken"], not_taken=stats["not_taken"])
            dominant_outcomes.add(dominant_outcome)
            branch_events += stats["total"]
            sorted_contexts.append(
                {
                    "address": hex(stats["address"]),
                    "history_before": stats["history_before"],
                    "total": stats["total"],
                    "taken": stats["taken"],
                    "not_taken": stats["not_taken"],
                    "taken_percent": taken_percent,
                    "dominant_outcome": dominant_outcome,
                    "labels": sorted(stats["labels"]),
                    "first_event": stats["first_event"],
                }
            )
        if len(addresses) > 1:
            cross_address_collisions += 1
        if len(histories) > 1:
            history_spread_collisions += 1
        total_collision_events += branch_events
        collision_groups.append(
            {
                "index": index,
                "index_hex": hex(index),
                "context_count": len(sorted_contexts),
                "address_count": len(addresses),
                "history_count": len(histories),
                "branch_events": branch_events,
                "conflicting_biases": len(dominant_outcomes) > 1,
                "contexts": sorted_contexts,
            }
        )

    conflict_groups = [group for group in collision_groups if group["conflicting_biases"]]
    return {
        "table_size": table_size,
        "history_bits": history_bits,
        "unique_indices": len(groups),
        "colliding_indices": len(collision_groups),
        "conflicting_indices": len(conflict_groups),
        "cross_address_colliding_indices": cross_address_collisions,
        "history_spread_colliding_indices": history_spread_collisions,
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
        gshare_alias_summary = summarize_gshare_aliasing(records, table_size=table_size, history_bits=history_bits)
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
                "gshare_alias_summary": gshare_alias_summary,
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


def _signed_bits_for_limit(limit: int) -> int:
    return max(1, (max(1, limit) * 2).bit_length())


def estimate_predictor_state_bits(
    name: str,
    *,
    table_size: int | None = None,
    history_bits: int | None = None,
    threshold: int | None = None,
    weight_limit: int | None = None,
) -> int:
    normalized = name.strip().lower()
    if normalized in {"always-taken", "always-not-taken"}:
        return 0
    if normalized == "one-bit":
        if table_size is None:
            raise ValueError("table_size is required for one-bit state sizing")
        return table_size
    if normalized == "two-bit":
        if table_size is None:
            raise ValueError("table_size is required for two-bit state sizing")
        return table_size * 2
    if normalized == "local-history":
        if table_size is None or history_bits is None:
            raise ValueError("table_size and history_bits are required for local-history state sizing")
        return (table_size * history_bits) + (2 * (1 << history_bits))
    if normalized == "gshare":
        if table_size is None or history_bits is None:
            raise ValueError("table_size and history_bits are required for gshare state sizing")
        return (table_size * 2) + history_bits
    if normalized == "perceptron":
        if table_size is None or history_bits is None:
            raise ValueError("table_size and history_bits are required for perceptron state sizing")
        resolved = PerceptronPredictor(
            table_size=table_size,
            history_bits=history_bits,
            threshold=threshold,
            weight_limit=weight_limit,
        )
        signed_weight_bits = _signed_bits_for_limit(resolved.weight_limit)
        return (table_size * (history_bits + 1) * signed_weight_bits) + history_bits
    if normalized == "tournament":
        if table_size is None or history_bits is None:
            raise ValueError("table_size and history_bits are required for tournament state sizing")
        return (table_size * history_bits) + (2 * (1 << history_bits)) + (table_size * 4) + history_bits
    raise ValueError(f"unsupported predictor for state sizing: {name}")


def _budget_candidate_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (
        -candidate["accuracy"],
        candidate["mispredictions"],
        candidate["state_bits"],
        candidate.get("history_bits") or 0,
        candidate.get("table_size") or 0,
        candidate.get("weight_limit") or 0,
        candidate["predictor"],
    )


def _first_budget_result_from_group(
    results: list[dict[str, Any]], allowed_names: set[str], *, required: bool = True
) -> dict[str, Any] | None:
    match = next((result for result in results if result["predictor"] in allowed_names), None)
    if match is None and required:
        raise ValueError(f"missing predictors from group: {sorted(allowed_names)}")
    return match


def _budget_group_label(predictor: str | None, accuracy_percent: float | None) -> str:
    if predictor is None or accuracy_percent is None:
        return "n/a"
    return f"`{predictor}` `{accuracy_percent:.2f}%`"


def _format_budget_candidate_label(candidate: dict[str, Any]) -> str:
    if candidate["predictor"] in {"always-taken", "always-not-taken"}:
        return f"{candidate['predictor']} · stateless"
    parts = [candidate["predictor"]]
    if candidate.get("table_size") is not None:
        parts.append(f"table={candidate['table_size']}")
    if candidate.get("history_bits") is not None and candidate["predictor"] not in {"one-bit", "two-bit"}:
        parts.append(f"history={candidate['history_bits']}")
    if candidate.get("weight_limit") is not None:
        parts.append(f"w={candidate['weight_limit']}")
    parts.append(f"bits={candidate['state_bits']}")
    return " · ".join(parts)


def enumerate_budget_candidates(
    records: list[BranchRecord],
    *,
    table_sizes: list[int] | tuple[int, ...] | None = None,
    history_bits_options: list[int] | tuple[int, ...] | None = None,
    weight_limits: list[int] | tuple[int, ...] | None = None,
) -> list[dict[str, Any]]:
    table_values = sorted({value for value in (table_sizes or BUDGET_SWEEP_TABLE_SIZES) if value >= 2})
    history_values = sorted({value for value in (history_bits_options or BUDGET_SWEEP_HISTORY_BITS) if value >= 1})
    weight_limit_values = sorted({value for value in (weight_limits or BUDGET_SWEEP_WEIGHT_LIMITS) if value >= 1})

    candidates: list[dict[str, Any]] = []

    def add_candidate(
        predictor: BranchPredictor,
        *,
        predictor_name: str,
        table_size: int | None = None,
        history_bits: int | None = None,
        threshold: int | None = None,
        weight_limit: int | None = None,
    ) -> None:
        result = simulate_trace(records, predictor)
        resolved_threshold = threshold
        resolved_weight_limit = weight_limit
        if isinstance(predictor, PerceptronPredictor):
            resolved_threshold = predictor.threshold
            resolved_weight_limit = predictor.weight_limit
        state_bits = estimate_predictor_state_bits(
            predictor_name,
            table_size=table_size,
            history_bits=history_bits,
            threshold=resolved_threshold,
            weight_limit=resolved_weight_limit,
        )
        candidates.append(
            {
                "predictor": predictor_name,
                "table_size": table_size,
                "history_bits": history_bits,
                "threshold": resolved_threshold,
                "weight_limit": resolved_weight_limit,
                "state_bits": state_bits,
                "accuracy": result.accuracy,
                "accuracy_percent": round(result.accuracy * 100, 3),
                "mispredictions": result.mispredictions,
                "mpki": result.mpki,
                "hardest_branch": result.hardest_branches[0]["address"] if result.hardest_branches else None,
            }
        )

    add_candidate(AlwaysTakenPredictor(), predictor_name="always-taken")
    add_candidate(AlwaysNotTakenPredictor(), predictor_name="always-not-taken")

    for table_size in table_values:
        add_candidate(OneBitPredictor(table_size=table_size), predictor_name="one-bit", table_size=table_size)
        add_candidate(TwoBitPredictor(table_size=table_size), predictor_name="two-bit", table_size=table_size)
        for history_bits in history_values:
            add_candidate(
                LocalHistoryPredictor(table_size=table_size, history_bits=history_bits),
                predictor_name="local-history",
                table_size=table_size,
                history_bits=history_bits,
            )
            add_candidate(
                GSharePredictor(table_size=table_size, history_bits=history_bits),
                predictor_name="gshare",
                table_size=table_size,
                history_bits=history_bits,
            )
            add_candidate(
                TournamentPredictor(table_size=table_size, history_bits=history_bits),
                predictor_name="tournament",
                table_size=table_size,
                history_bits=history_bits,
            )
            for weight_limit in weight_limit_values:
                predictor = PerceptronPredictor(
                    table_size=table_size,
                    history_bits=history_bits,
                    weight_limit=weight_limit,
                )
                add_candidate(
                    predictor,
                    predictor_name="perceptron",
                    table_size=table_size,
                    history_bits=history_bits,
                    threshold=predictor.threshold,
                    weight_limit=predictor.weight_limit,
                )

    return sorted(candidates, key=_budget_candidate_sort_key)


def run_budget_normalized_sweep(
    records: list[BranchRecord],
    *,
    budgets: list[int] | tuple[int, ...] | None = None,
    table_sizes: list[int] | tuple[int, ...] | None = None,
    history_bits_options: list[int] | tuple[int, ...] | None = None,
    weight_limits: list[int] | tuple[int, ...] | None = None,
) -> dict[str, Any]:
    budget_values = sorted({value for value in (budgets or BUDGET_SWEEP_BUDGETS) if value >= 1})
    if not budget_values:
        raise ValueError("budgets must contain at least one positive integer")
    table_values = sorted({value for value in (table_sizes or BUDGET_SWEEP_TABLE_SIZES) if value >= 2})
    history_values = sorted({value for value in (history_bits_options or BUDGET_SWEEP_HISTORY_BITS) if value >= 1})
    weight_limit_values = sorted({value for value in (weight_limits or BUDGET_SWEEP_WEIGHT_LIMITS) if value >= 1})
    candidates = enumerate_budget_candidates(
        records,
        table_sizes=table_values,
        history_bits_options=history_values,
        weight_limits=weight_limit_values,
    )

    budget_reports: list[dict[str, Any]] = []
    for budget_bits in budget_values:
        best_by_predictor: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            if candidate["state_bits"] > budget_bits:
                continue
            current = best_by_predictor.get(candidate["predictor"])
            if current is None or _budget_candidate_sort_key(candidate) < _budget_candidate_sort_key(current):
                best_by_predictor[candidate["predictor"]] = candidate
        if not best_by_predictor:
            raise ValueError(f"no predictor configs fit budget {budget_bits} bits")

        predictor_results = sorted(best_by_predictor.values(), key=_budget_candidate_sort_key)
        winner = predictor_results[0]
        runner_up = predictor_results[1] if len(predictor_results) > 1 else winner
        best_simple = _first_budget_result_from_group(predictor_results, SIMPLE_PREDICTOR_NAMES, required=False)
        best_advanced = _first_budget_result_from_group(predictor_results, ADVANCED_PREDICTOR_NAMES, required=False)
        budget_reports.append(
            {
                "budget_bits": budget_bits,
                "winner_predictor": winner["predictor"],
                "winner_accuracy_percent": winner["accuracy_percent"],
                "runner_up_predictor": runner_up["predictor"],
                "winner_margin_percent": round((winner["accuracy"] - runner_up["accuracy"]) * 100, 3),
                "best_simple_predictor": best_simple["predictor"] if best_simple is not None else None,
                "best_simple_accuracy_percent": best_simple["accuracy_percent"] if best_simple is not None else None,
                "best_advanced_predictor": best_advanced["predictor"] if best_advanced is not None else None,
                "best_advanced_accuracy_percent": best_advanced["accuracy_percent"] if best_advanced is not None else None,
                "predictor_results": predictor_results,
            }
        )

    return {
        "trace_summary": summarize_trace(records),
        "budgets": budget_values,
        "table_sizes": table_values,
        "history_bits_options": history_values,
        "weight_limits": weight_limit_values,
        "candidate_count": len(candidates),
        "budget_reports": budget_reports,
    }


def run_budget_workload_sweep(
    workloads: list[str] | None = None,
    *,
    branches_override: int | None = None,
    seed_override: int | None = None,
    budgets: list[int] | tuple[int, ...] | None = None,
    table_sizes: list[int] | tuple[int, ...] | None = None,
    history_bits_options: list[int] | tuple[int, ...] | None = None,
    weight_limits: list[int] | tuple[int, ...] | None = None,
    trace_dir: Path | None = None,
) -> list[dict[str, Any]]:
    selected = workloads or list(SYNTHETIC_WORKLOADS)
    scenarios: list[dict[str, Any]] = []
    if trace_dir is not None:
        trace_dir.mkdir(parents=True, exist_ok=True)

    for workload in selected:
        if workload not in WORKLOAD_SWEEP_PROFILES:
            supported = ", ".join(sorted(WORKLOAD_SWEEP_PROFILES))
            raise ValueError(f"unsupported budget-sweep workload: {workload}. Expected one of: {supported}")
        profile = WORKLOAD_SWEEP_PROFILES[workload]
        branches = branches_override if branches_override is not None else int(profile["branches"])
        seed = seed_override if seed_override is not None else int(profile["seed"])
        records = generate_synthetic_trace(workload, branches=branches, seed=seed)
        trace_output: Path | None = None
        if trace_dir is not None:
            trace_output = trace_dir / f"{workload}-seed{seed}.trace"
            trace_output.write_text(f"{format_trace(records)}\n", encoding="utf-8")
        report = run_budget_normalized_sweep(
            records,
            budgets=budgets,
            table_sizes=table_sizes,
            history_bits_options=history_bits_options,
            weight_limits=weight_limits,
        )
        scenarios.append(
            {
                "workload": workload,
                "headline": profile["headline"],
                "config": {"branches": branches, "seed": seed},
                "trace_output": str(trace_output) if trace_output is not None else None,
                **report,
            }
        )
    return scenarios


def format_budget_sweep_summary_table(scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        return "no scenarios"
    budgets = scenarios[0]["budgets"]
    header = ["workload", *[f"{budget}b" for budget in budgets]]
    lines = [" | ".join(header), " | ".join(["---"] * len(header))]
    for scenario in scenarios:
        cells = [scenario["workload"]]
        by_budget = {entry["budget_bits"]: entry for entry in scenario["budget_reports"]}
        for budget in budgets:
            entry = by_budget[budget]
            cells.append(f"{entry['winner_predictor']} {entry['winner_accuracy_percent']:.1f}%")
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def _default_perceptron_threshold_values(default_threshold: int) -> list[int]:
    return sorted({max(1, default_threshold + offset) for offset in (-18, -9, 0, 9, 18)})


def _default_perceptron_weight_limits(default_weight_limit: int) -> list[int]:
    return sorted(
        {
            max(8, default_weight_limit // 4),
            max(8, default_weight_limit // 2),
            default_weight_limit,
            default_weight_limit * 2,
        }
    )


def run_perceptron_tuning_sweep(
    records: list[BranchRecord],
    *,
    table_size: int = 32,
    history_bits: int = 12,
    thresholds: list[int] | None = None,
    weight_limits: list[int] | None = None,
) -> dict[str, Any]:
    baseline = PerceptronPredictor(table_size=table_size, history_bits=history_bits)
    default_threshold = baseline.threshold
    default_weight_limit = baseline.weight_limit
    threshold_values = sorted({max(1, value) for value in (thresholds or _default_perceptron_threshold_values(default_threshold))})
    weight_limit_values = sorted({max(1, value) for value in (weight_limits or _default_perceptron_weight_limits(default_weight_limit))})

    configs: list[dict[str, Any]] = []
    for threshold in threshold_values:
        for weight_limit in weight_limit_values:
            result = simulate_trace(
                records,
                PerceptronPredictor(
                    table_size=table_size,
                    history_bits=history_bits,
                    threshold=threshold,
                    weight_limit=weight_limit,
                ),
            )
            max_abs_weight = int(result.final_state["max_abs_weight"])
            configs.append(
                {
                    "threshold": threshold,
                    "weight_limit": weight_limit,
                    "accuracy_percent": round(result.accuracy * 100, 3),
                    "accuracy": result.accuracy,
                    "mispredictions": result.mispredictions,
                    "mpki": result.mpki,
                    "trained_perceptrons": int(result.final_state["trained_perceptrons"]),
                    "non_zero_weights": int(result.final_state["non_zero_weights"]),
                    "max_abs_weight": max_abs_weight,
                    "saturated_max_weight": max_abs_weight >= weight_limit,
                    "is_default_config": threshold == default_threshold and weight_limit == default_weight_limit,
                }
            )

    configs.sort(
        key=lambda config: (
            -config["accuracy"],
            config["mispredictions"],
            abs(config["threshold"] - default_threshold),
            abs(config["weight_limit"] - default_weight_limit),
            config["threshold"],
            config["weight_limit"],
        )
    )

    best_config = configs[0]
    default_config = next((config for config in configs if config["is_default_config"]), None)
    saturated_config_count = sum(1 for config in configs if config["saturated_max_weight"])
    accuracy_values = [config["accuracy_percent"] for config in configs]
    return {
        "trace_summary": summarize_trace(records),
        "table_size": table_size,
        "history_bits": history_bits,
        "default_threshold": default_threshold,
        "default_weight_limit": default_weight_limit,
        "thresholds": threshold_values,
        "weight_limits": weight_limit_values,
        "config_count": len(configs),
        "saturated_config_count": saturated_config_count,
        "best_config": best_config,
        "default_config": default_config,
        "min_accuracy_percent": min(accuracy_values),
        "max_accuracy_percent": max(accuracy_values),
        "configs": configs,
    }


def format_perceptron_tuning_summary_table(report: dict[str, Any]) -> str:
    lines = [
        "threshold   weight limit   accuracy   mispreds   mpki    max|w|   notes",
        "----------  -------------  ---------  ---------  ------  -------  ------------------------------",
    ]
    for config in report["configs"]:
        notes: list[str] = []
        if config is report["best_config"]:
            notes.append("best")
        if config["is_default_config"]:
            notes.append("default")
        if config["saturated_max_weight"]:
            notes.append("saturated")
        lines.append(
            f"{config['threshold']:>10}  {config['weight_limit']:>13}  {config['accuracy_percent']:>7.2f}%  "
            f"{config['mispredictions']:>9}  {config['mpki']:>6.1f}  {config['max_abs_weight']:>7}  {', '.join(notes) or '-'}"
        )
    return "\n".join(lines)


def build_predictor(
    name: str,
    table_size: int,
    history_bits: int,
    *,
    threshold: int | None = None,
    weight_limit: int | None = None,
) -> BranchPredictor:
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
        return PerceptronPredictor(
            table_size=table_size,
            history_bits=history_bits,
            threshold=threshold,
            weight_limit=weight_limit,
        )
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
    gshare_alias_summary: dict[str, Any],
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

    if alias_summary["colliding_indices"]:
        points.append(
            f"Static table aliasing: {alias_summary['colliding_indices']} colliding indices at table size {alias_summary['table_size']} "
            f"({alias_summary['conflicting_indices']} with conflicting taken/not-taken biases)."
        )

    if gshare_alias_summary["colliding_indices"]:
        points.append(
            f"Dynamic gshare aliasing: {gshare_alias_summary['colliding_indices']} live index collisions at table size {gshare_alias_summary['table_size']} "
            f"with history={gshare_alias_summary['history_bits']} ({gshare_alias_summary['conflicting_indices']} conflicting bias groups)."
        )
        top_collision = next(
            (group for group in gshare_alias_summary["collision_groups"] if group["conflicting_biases"]),
            gshare_alias_summary["collision_groups"][0],
        )
        contexts = ", ".join(
            f"{item['address']}@{item['history_before']}" for item in top_collision["contexts"][:3]
        )
        points.append(
            f"Worst gshare bucket: index {top_collision['index_hex']} mixes {contexts} across {top_collision['branch_events']} branch events."
        )
    elif alias_summary["colliding_indices"]:
        top_collision = next(
            (group for group in alias_summary["collision_groups"] if group["conflicting_biases"]),
            alias_summary["collision_groups"][0],
        )
        addresses = ", ".join(item["address"] for item in top_collision["addresses"])
        points.append(
            f"Worst alias bucket: index {top_collision['index_hex']} merges {addresses} across {top_collision['branch_events']} branch events."
        )

    hardest = best.hardest_branches[0] if best.hardest_branches else None
    if hardest is not None:
        points.append(
            f"Hardest branch for the winning predictor is {hardest['address']} with "
            f"{hardest['mispredictions']} misses across {hardest['total']} executions."
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
    gshare_alias_summary: dict[str, Any],
    results: list[SimulationResult],
    table_size: int,
    history_bits: int,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    best = results[0]
    worst = results[-1]
    talking_points = _build_comparison_talking_points(results, trace_summary, alias_summary, gshare_alias_summary)
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

    lines.extend(["", "## Dynamic gshare aliasing", ""])
    lines.append(
        f"- `{gshare_alias_summary['colliding_indices']}` live gshare index groups collide at table size `{gshare_alias_summary['table_size']}` with history bits `{gshare_alias_summary['history_bits']}`; "
        f"`{gshare_alias_summary['conflicting_indices']}` groups mix opposite dominant biases."
    )
    lines.append(
        f"- `{gshare_alias_summary['cross_address_colliding_indices']}` groups merge different PCs; "
        f"`{gshare_alias_summary['history_spread_colliding_indices']}` groups merge multiple global-history states."
    )
    lines.append(
        f"- `{gshare_alias_summary['branch_events_in_collisions']}` branch events land in dynamic gshare collisions on this trace."
    )
    if gshare_alias_summary["collision_groups"]:
        for group in gshare_alias_summary["collision_groups"]:
            members = ", ".join(
                f"`{item['address']}@{item['history_before']}` ({item['taken_percent']:.1f}% taken)" for item in group["contexts"]
            )
            suffix = "conflicting biases" if group["conflicting_biases"] else "similar biases"
            lines.append(
                f"- Index `{group['index_hex']}`: {members} · `{group['branch_events']}` events · {suffix}."
            )
    else:
        lines.append("- No dynamic gshare collisions for this table/history configuration.")

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
    gshare_alias_summary: dict[str, Any],
    results: list[SimulationResult],
    table_size: int,
    history_bits: int,
) -> str:
    width = 960
    height = 640
    best = results[0]
    runner_up = results[1]
    talking_points = _build_comparison_talking_points(results, trace_summary, alias_summary, gshare_alias_summary)[:3]
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
        gshare_alias_summary = scenario["gshare_alias_summary"]
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
                f"- Dynamic gshare aliasing: `{gshare_alias_summary['colliding_indices']}` live collisions, `{gshare_alias_summary['conflicting_indices']}` with conflicting dominant biases, `{gshare_alias_summary['history_spread_colliding_indices']}` spanning multiple history states.",
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


def write_csv_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8", newline="")


def _perceptron_tuning_cell_fill(accuracy_percent: float, minimum: float, maximum: float) -> str:
    palette = ["#e2e8f0", "#bfdbfe", "#93c5fd", "#60a5fa", "#3b82f6", "#1d4ed8"]
    if maximum <= minimum:
        return palette[-1]
    ratio = (accuracy_percent - minimum) / (maximum - minimum)
    index = min(len(palette) - 1, max(0, round(ratio * (len(palette) - 1))))
    return palette[index]


def _budget_winner_sequence(budget_reports: list[dict[str, Any]]) -> str:
    steps: list[str] = []
    previous: str | None = None
    for entry in budget_reports:
        label = f"{entry['budget_bits']}b:{entry['winner_predictor']}"
        if label != previous:
            steps.append(label)
        previous = label
    return " → ".join(steps)


def _budget_predictor_fill(predictor: str) -> str:
    palette = {
        "always-taken": "#cbd5e1",
        "always-not-taken": "#94a3b8",
        "one-bit": "#38bdf8",
        "two-bit": "#0ea5e9",
        "local-history": "#8b5cf6",
        "gshare": "#6366f1",
        "perceptron": "#f59e0b",
        "tournament": "#10b981",
    }
    return palette.get(predictor, "#e2e8f0")


def _budget_heatmap_fill(count: int, max_count: int) -> str:
    palette = ["#f8fafc", "#dbeafe", "#bfdbfe", "#93c5fd", "#60a5fa", "#2563eb"]
    if count <= 0 or max_count <= 0:
        return palette[0]
    ratio = count / max_count
    index = min(len(palette) - 1, max(1, round(ratio * (len(palette) - 1))))
    return palette[index]


def _budget_winner_sequence_csv(budget_reports: list[dict[str, Any]]) -> str:
    return _budget_winner_sequence(budget_reports).replace(" → ", " -> ")


def _format_budget_candidate_csv_label(candidate: dict[str, Any]) -> str:
    return _format_budget_candidate_label(candidate).replace(" · ", " | ")


def _compress_name_sequence(names: list[str]) -> str:
    if not names:
        return "-"
    runs: list[str] = []
    current = names[0]
    count = 1
    for name in names[1:]:
        if name == current:
            count += 1
            continue
        runs.append(f"{current} ×{count}" if count > 1 else current)
        current = name
        count = 1
    runs.append(f"{current} ×{count}" if count > 1 else current)
    return " → ".join(runs)


def summarize_budget_winner_grid(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    budgets = scenarios[0]["budgets"]
    winners_only = {
        entry["winner_predictor"]
        for scenario in scenarios
        for entry in scenario["budget_reports"]
    }
    predictor_order = [name for name in BUDGET_SWEEP_PREDICTOR_NAMES if name in winners_only]
    if not predictor_order:
        predictor_order = sorted(winners_only)

    predictor_totals: dict[str, dict[str, Any]] = {
        predictor: {
            "predictor": predictor,
            "wins": 0,
            "workloads": set(),
            "budget_bits": set(),
        }
        for predictor in predictor_order
    }
    budget_predictor_counts: dict[int, dict[str, int]] = {
        budget: {predictor: 0 for predictor in predictor_order}
        for budget in budgets
    }
    total_cells = 0
    max_budget_wins = 0

    for scenario in scenarios:
        workload = scenario["workload"]
        for entry in scenario["budget_reports"]:
            predictor = entry["winner_predictor"]
            predictor_totals[predictor]["wins"] += 1
            predictor_totals[predictor]["workloads"].add(workload)
            predictor_totals[predictor]["budget_bits"].add(entry["budget_bits"])
            budget_predictor_counts[entry["budget_bits"]][predictor] += 1
            max_budget_wins = max(max_budget_wins, budget_predictor_counts[entry["budget_bits"]][predictor])
            total_cells += 1

    predictor_rows = []
    for predictor in predictor_order:
        row = predictor_totals[predictor]
        wins = int(row["wins"])
        predictor_rows.append(
            {
                "predictor": predictor,
                "wins": wins,
                "share_percent": round((wins / total_cells) * 100, 3) if total_cells else 0.0,
                "workload_count": len(row["workloads"]),
                "budget_count": len(row["budget_bits"]),
                "workloads": sorted(row["workloads"]),
                "budgets": sorted(row["budget_bits"]),
            }
        )
    predictor_rows.sort(
        key=lambda row: (-row["wins"], predictor_order.index(row["predictor"]))
    )

    budget_rows = []
    for budget in budgets:
        counts = budget_predictor_counts[budget]
        leaders = sorted(
            (
                {
                    "predictor": predictor,
                    "wins": wins,
                }
                for predictor, wins in counts.items()
                if wins > 0
            ),
            key=lambda row: (-row["wins"], predictor_order.index(row["predictor"])),
        )
        budget_rows.append(
            {
                "budget_bits": budget,
                "predictor_counts": counts,
                "leaders": leaders,
            }
        )

    return {
        "total_cells": total_cells,
        "workload_count": len(scenarios),
        "predictors": [row["predictor"] for row in predictor_rows],
        "predictor_rows": predictor_rows,
        "budget_rows": budget_rows,
        "max_budget_wins": max_budget_wins,
    }


def summarize_budget_margin_story(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    budgets = scenarios[0]["budgets"]
    total_cells = 0
    thresholds = (0.5, 1.0, 2.0)
    threshold_counts = {threshold: 0 for threshold in thresholds}
    budget_entries: dict[int, list[dict[str, Any]]] = {budget: [] for budget in budgets}
    winner_entries: dict[str, list[dict[str, Any]]] = {}
    workload_rows: list[dict[str, Any]] = []
    tightest_cell: dict[str, Any] | None = None
    widest_cell: dict[str, Any] | None = None

    for scenario in scenarios:
        runner_up_names = [entry["runner_up_predictor"] for entry in scenario["budget_reports"]]
        workload_tightest = min(scenario["budget_reports"], key=lambda entry: entry["winner_margin_percent"])
        workload_widest = max(scenario["budget_reports"], key=lambda entry: entry["winner_margin_percent"])
        runner_up_changes = sum(
            1
            for previous, current in zip(runner_up_names, runner_up_names[1:])
            if previous != current
        )
        workload_rows.append(
            {
                "workload": scenario["workload"],
                "runner_up_sequence": runner_up_names,
                "runner_up_flow": _compress_name_sequence(runner_up_names),
                "unique_runner_up_count": len(set(runner_up_names)),
                "runner_up_changes": runner_up_changes,
                "tightest_budget_bits": workload_tightest["budget_bits"],
                "tightest_margin_percent": workload_tightest["winner_margin_percent"],
                "widest_budget_bits": workload_widest["budget_bits"],
                "widest_margin_percent": workload_widest["winner_margin_percent"],
            }
        )
        for entry in scenario["budget_reports"]:
            row = {
                "workload": scenario["workload"],
                "budget_bits": entry["budget_bits"],
                "winner_predictor": entry["winner_predictor"],
                "runner_up_predictor": entry["runner_up_predictor"],
                "winner_margin_percent": float(entry["winner_margin_percent"]),
            }
            margin = row["winner_margin_percent"]
            total_cells += 1
            for threshold in thresholds:
                if margin <= threshold:
                    threshold_counts[threshold] += 1
            budget_entries[row["budget_bits"]].append(row)
            winner_entries.setdefault(row["winner_predictor"], []).append(row)
            if tightest_cell is None or margin < tightest_cell["winner_margin_percent"]:
                tightest_cell = row
            if widest_cell is None or margin > widest_cell["winner_margin_percent"]:
                widest_cell = row

    threshold_rows = [
        {
            "threshold": threshold,
            "label": f"≤{threshold:.2f} pp",
            "count": threshold_counts[threshold],
            "share_percent": round((threshold_counts[threshold] / total_cells) * 100, 3) if total_cells else 0.0,
        }
        for threshold in thresholds
    ]

    budget_rows: list[dict[str, Any]] = []
    max_average_margin = 0.0
    max_close_races = 0
    max_photo_finishes = 0
    for budget in budgets:
        entries = budget_entries[budget]
        average_margin = sum(entry["winner_margin_percent"] for entry in entries) / len(entries)
        close_race_count = sum(1 for entry in entries if entry["winner_margin_percent"] <= 1.0)
        photo_finish_count = sum(1 for entry in entries if entry["winner_margin_percent"] <= 0.5)
        runner_up_counts: dict[str, int] = {}
        for entry in entries:
            runner_up_counts[entry["runner_up_predictor"]] = runner_up_counts.get(entry["runner_up_predictor"], 0) + 1
        top_runner_up_predictor = None
        top_runner_up_count = 0
        if runner_up_counts:
            top_runner_up_predictor, top_runner_up_count = sorted(
                runner_up_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )[0]
        max_average_margin = max(max_average_margin, average_margin)
        max_close_races = max(max_close_races, close_race_count)
        max_photo_finishes = max(max_photo_finishes, photo_finish_count)
        budget_rows.append(
            {
                "budget_bits": budget,
                "cell_count": len(entries),
                "average_margin_percent": round(average_margin, 3),
                "close_race_count": close_race_count,
                "photo_finish_count": photo_finish_count,
                "top_runner_up_predictor": top_runner_up_predictor,
                "top_runner_up_count": top_runner_up_count,
                "runner_up_predictor_counts": runner_up_counts,
            }
        )

    winner_rows: list[dict[str, Any]] = []
    for predictor, entries in sorted(winner_entries.items(), key=lambda item: item[0]):
        average_margin = sum(entry["winner_margin_percent"] for entry in entries) / len(entries)
        winner_rows.append(
            {
                "predictor": predictor,
                "win_count": len(entries),
                "average_margin_percent": round(average_margin, 3),
                "close_win_count": sum(1 for entry in entries if entry["winner_margin_percent"] <= 1.0),
                "photo_finish_count": sum(1 for entry in entries if entry["winner_margin_percent"] <= 0.5),
            }
        )
    winner_rows.sort(key=lambda row: (-row["win_count"], row["average_margin_percent"], row["predictor"]))

    return {
        "total_cells": total_cells,
        "threshold_rows": threshold_rows,
        "budget_rows": budget_rows,
        "winner_rows": winner_rows,
        "workload_rows": workload_rows,
        "tightest_cell": tightest_cell,
        "widest_cell": widest_cell,
        "max_average_margin": round(max_average_margin, 3),
        "max_close_races": max_close_races,
        "max_photo_finishes": max_photo_finishes,
    }


def _format_budget_crossover_label(crossover: dict[str, Any]) -> str:
    return (
        f"{crossover['from_budget_bits']}→{crossover['to_budget_bits']}b "
        f"{crossover['previous_winner_predictor']}→{crossover['next_winner_predictor']}"
    )


def _budget_crossover_chip_label(crossover: dict[str, Any]) -> str:
    return f"{crossover['from_budget_bits']}→{crossover['to_budget_bits']}b"


def _build_budget_crossover_lookup(crossover_summary: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    return {
        (row["workload"], row["to_budget_bits"]): row
        for row in crossover_summary["crossovers"]
    }


def summarize_budget_crossover_points(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    if not scenarios:
        raise ValueError("scenarios must not be empty")

    crossovers: list[dict[str, Any]] = []
    workload_rows: list[dict[str, Any]] = []
    transition_counts: dict[tuple[int, int, str, str], dict[str, Any]] = {}

    for scenario in scenarios:
        scenario_crossovers: list[dict[str, Any]] = []
        for previous, current in zip(scenario["budget_reports"], scenario["budget_reports"][1:]):
            if previous["winner_predictor"] == current["winner_predictor"]:
                continue
            crossover = {
                "workload": scenario["workload"],
                "headline": scenario["headline"],
                "from_budget_bits": previous["budget_bits"],
                "to_budget_bits": current["budget_bits"],
                "previous_winner_predictor": previous["winner_predictor"],
                "next_winner_predictor": current["winner_predictor"],
                "previous_winner_accuracy_percent": previous["winner_accuracy_percent"],
                "next_winner_accuracy_percent": current["winner_accuracy_percent"],
                "previous_runner_up_predictor": previous["runner_up_predictor"],
                "next_runner_up_predictor": current["runner_up_predictor"],
                "previous_margin_percent": previous["winner_margin_percent"],
                "next_margin_percent": current["winner_margin_percent"],
            }
            crossover["label"] = _format_budget_crossover_label(crossover)
            crossovers.append(crossover)
            scenario_crossovers.append(crossover)
            key = (
                crossover["from_budget_bits"],
                crossover["to_budget_bits"],
                crossover["previous_winner_predictor"],
                crossover["next_winner_predictor"],
            )
            entry = transition_counts.setdefault(
                key,
                {
                    "from_budget_bits": crossover["from_budget_bits"],
                    "to_budget_bits": crossover["to_budget_bits"],
                    "previous_winner_predictor": crossover["previous_winner_predictor"],
                    "next_winner_predictor": crossover["next_winner_predictor"],
                    "count": 0,
                    "workloads": [],
                },
            )
            entry["count"] += 1
            entry["workloads"].append(scenario["workload"])

        workload_rows.append(
            {
                "workload": scenario["workload"],
                "headline": scenario["headline"],
                "crossover_count": len(scenario_crossovers),
                "crossovers": scenario_crossovers,
                "crossover_sequence": "none" if not scenario_crossovers else " | ".join(
                    crossover["label"] for crossover in scenario_crossovers
                ),
                "first_crossover_budget_bits": scenario_crossovers[0]["to_budget_bits"] if scenario_crossovers else None,
                "last_crossover_budget_bits": scenario_crossovers[-1]["to_budget_bits"] if scenario_crossovers else None,
            }
        )

    transition_rows = sorted(
        (
            {
                **entry,
                "workloads": sorted(entry["workloads"]),
            }
            for entry in transition_counts.values()
        ),
        key=lambda row: (-row["count"], row["from_budget_bits"], row["to_budget_bits"], row["previous_winner_predictor"], row["next_winner_predictor"]),
    )

    return {
        "total_crossovers": len(crossovers),
        "workloads_with_crossovers": sum(1 for row in workload_rows if row["crossover_count"] > 0),
        "workload_rows": workload_rows,
        "transition_rows": transition_rows,
        "crossovers": sorted(
            crossovers,
            key=lambda row: (row["from_budget_bits"], row["to_budget_bits"], row["workload"], row["next_winner_predictor"]),
        ),
    }


def render_budget_sweep_markdown(*, scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    generated = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    budgets = scenarios[0]["budgets"]
    table_sizes = scenarios[0]["table_sizes"]
    history_bits_options = scenarios[0]["history_bits_options"]
    weight_limits = scenarios[0]["weight_limits"]
    winner_summary = summarize_budget_winner_grid(scenarios)
    margin_summary = summarize_budget_margin_story(scenarios)
    crossover_summary = summarize_budget_crossover_points(scenarios)
    crossover_lookup = _build_budget_crossover_lookup(crossover_summary)
    lines = [
        "# Branch predictor budget-normalized sweep",
        "",
        f"- Generated: `{generated}`",
        f"- Workloads: `{len(scenarios)}` synthetic families",
        f"- Compared budgets: `{', '.join(f'{budget} bits' for budget in budgets)}`",
        f"- Search space: table sizes `{', '.join(str(value) for value in table_sizes)}` · history bits `{', '.join(str(value) for value in history_bits_options)}` · perceptron weight limits `{', '.join(str(value) for value in weight_limits)}`",
        "- Goal: compare the best config each predictor can afford under the same approximate state-bit budget instead of one fixed table/history setting for everyone.",
        "- Export note: the SVG now includes whole-grid win totals, a budget-by-predictor heatmap, a winner-margin trend card, a crossover card, and blue flip chips on the winner matrix cells that mark exactly where the winning predictor changes.",
        "",
        "## Overview",
        "",
        "| Workload | " + " | ".join(f"`{budget} bits`" for budget in budgets) + " |",
        "| --- | " + " | ".join(["---"] * len(budgets)) + " |",
    ]
    for scenario in scenarios:
        row = [f"`{scenario['workload']}`"]
        for entry in scenario["budget_reports"]:
            row.append(f"`{entry['winner_predictor']}` {entry['winner_accuracy_percent']:.2f}%")
        lines.append("| " + " | ".join(row) + " |")

    lines.extend([
        "",
        "## Whole-grid winner summary",
        "",
        f"- Grid cells: `{winner_summary['total_cells']}` workload-budget combinations.",
    ])
    if winner_summary["predictor_rows"]:
        leader = winner_summary["predictor_rows"][0]
        lines.append(
            f"- Overall leader: `{leader['predictor']}` with `{leader['wins']}` wins (`{leader['share_percent']:.2f}%` of the grid)."
        )
    lines.extend(
        [
            "",
            "| Predictor | Grid wins | Share | Workloads won | Budgets won |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in winner_summary["predictor_rows"]:
        budgets_text = ", ".join(str(value) for value in row["budgets"]) if row["budgets"] else "-"
        lines.append(
            f"| `{row['predictor']}` | `{row['wins']}` | `{row['share_percent']:.2f}%` | `{row['workload_count']}` | `{budgets_text}` |"
        )

    lines.extend([
        "",
        "### Budget × predictor win counts",
        "",
        "| Predictor | " + " | ".join(f"`{budget} bits`" for budget in budgets) + " |",
        "| --- | " + " | ".join(["---:"] * len(budgets)) + " |",
    ])
    for predictor in winner_summary["predictors"]:
        counts = []
        for budget_row in winner_summary["budget_rows"]:
            counts.append(f"`{budget_row['predictor_counts'][predictor]}`")
        lines.append("| " + " | ".join([f"`{predictor}`", *counts]) + " |")

    lines.extend([
        "",
        "## Winner crossover points",
        "",
        f"- Exact winner flips: `{crossover_summary['total_crossovers']}` across `{crossover_summary['workloads_with_crossovers']}` workloads.",
    ])
    if crossover_summary["transition_rows"]:
        lines.extend(
            [
                "",
                "### Transition counts",
                "",
                "| Budget step | Winner flip | Count | Workloads |",
                "| --- | --- | ---: | --- |",
            ]
        )
        for row in crossover_summary["transition_rows"]:
            lines.append(
                f"| `{row['from_budget_bits']}→{row['to_budget_bits']} bits` | `{row['previous_winner_predictor']} → {row['next_winner_predictor']}` | `{row['count']}` | `{', '.join(row['workloads'])}` |"
            )
        lines.extend(
            [
                "",
                "### Workload crossover triggers",
                "",
                "| Workload | Trigger budget step | Winner flip | Before gap | After gap |",
                "| --- | --- | --- | ---: | ---: |",
            ]
        )
        for row in crossover_summary["crossovers"]:
            lines.append(
                f"| `{row['workload']}` | `{row['from_budget_bits']}→{row['to_budget_bits']} bits` | `{row['previous_winner_predictor']} → {row['next_winner_predictor']}` | `{row['previous_margin_percent']:.2f} pp` | `{row['next_margin_percent']:.2f} pp` |"
            )
    else:
        lines.extend(["", "- No winner changes across adjacent budgets in this sweep."])

    lines.extend([
        "",
        "## Margin and runner-up story",
        "",
        f"- Photo finishes (≤0.50 pp): `{margin_summary['threshold_rows'][0]['count']}` grid cells (`{margin_summary['threshold_rows'][0]['share_percent']:.2f}%`).",
        f"- Close races (≤1.00 pp): `{margin_summary['threshold_rows'][1]['count']}` grid cells (`{margin_summary['threshold_rows'][1]['share_percent']:.2f}%`).",
        f"- Tightest cell: `{margin_summary['tightest_cell']['workload']}` @ `{margin_summary['tightest_cell']['budget_bits']} bits` → `{margin_summary['tightest_cell']['winner_predictor']}` over `{margin_summary['tightest_cell']['runner_up_predictor']}` by `{margin_summary['tightest_cell']['winner_margin_percent']:.2f} pp`.",
        f"- Widest cell: `{margin_summary['widest_cell']['workload']}` @ `{margin_summary['widest_cell']['budget_bits']} bits` → `{margin_summary['widest_cell']['winner_predictor']}` over `{margin_summary['widest_cell']['runner_up_predictor']}` by `{margin_summary['widest_cell']['winner_margin_percent']:.2f} pp`.",
        "",
        "### Margin trend by budget",
        "",
        "| Budget | Avg winner gap | Photo finishes (≤0.50 pp) | Close races (≤1.00 pp) | Most common runner-up |",
        "| ---: | ---: | ---: | ---: | --- |",
    ])
    for row in margin_summary["budget_rows"]:
        runner_up_label = "-"
        if row["top_runner_up_predictor"] is not None:
            runner_up_label = f"`{row['top_runner_up_predictor']}` (`{row['top_runner_up_count']}/{row['cell_count']}` cells)"
        lines.append(
            f"| `{row['budget_bits']}` | `{row['average_margin_percent']:.2f} pp` | `{row['photo_finish_count']}` | `{row['close_race_count']}` | {runner_up_label} |"
        )

    lines.extend([
        "",
        "### Runner-up stability by workload",
        "",
        "| Workload | Runner-up flow | Changes | Tightest gap | Widest gap |",
        "| --- | --- | ---: | --- | --- |",
    ])
    for row in margin_summary["workload_rows"]:
        lines.append(
            f"| `{row['workload']}` | `{row['runner_up_flow']}` | `{row['runner_up_changes']}` | `{row['tightest_budget_bits']} bits` (`{row['tightest_margin_percent']:.2f} pp`) | `{row['widest_budget_bits']} bits` (`{row['widest_margin_percent']:.2f} pp`) |"
        )

    lines.extend(["", "## Per-workload notes", ""])
    crossover_rows_by_workload = {row['workload']: row for row in crossover_summary['workload_rows']}
    for scenario in scenarios:
        workload_crossover_rows = crossover_rows_by_workload[scenario['workload']]['crossovers']
        workload_callouts = "none"
        if workload_crossover_rows:
            workload_callouts = "; ".join(
                f"{_budget_crossover_chip_label(row)} marks {row['previous_winner_predictor']} → {row['next_winner_predictor']}"
                for row in workload_crossover_rows
            )
        lines.extend(
            [
                f"### `{scenario['workload']}`",
                "",
                f"- Focus: {scenario['headline']}",
                f"- Trace config: `branches={scenario['config']['branches']}` · `seed={scenario['config']['seed']}`",
                f"- Winner sequence: {_budget_winner_sequence(scenario['budget_reports'])}",
                f"- Crossover points: {crossover_rows_by_workload[scenario['workload']]['crossover_sequence']}",
                f"- SVG matrix callouts: {workload_callouts}",
                "",
                "| Budget | Winner | Runner-up | Matrix callout | Best simple | Best advanced |",
                "| ---: | --- | --- | --- | --- | --- |",
            ]
        )
        for entry in scenario["budget_reports"]:
            crossover = crossover_lookup.get((scenario["workload"], entry["budget_bits"]))
            matrix_callout = "-"
            if crossover is not None:
                matrix_callout = (
                    f"`{_budget_crossover_chip_label(crossover)}` "
                    f"`{crossover['previous_winner_predictor']} → {crossover['next_winner_predictor']}`"
                )
            lines.append(
                f"| `{entry['budget_bits']}` | `{entry['winner_predictor']}` `{entry['winner_accuracy_percent']:.2f}%` | `{entry['runner_up_predictor']}` (`{entry['winner_margin_percent']:.2f} pp` gap) | {matrix_callout} | {_budget_group_label(entry['best_simple_predictor'], entry['best_simple_accuracy_percent'])} | {_budget_group_label(entry['best_advanced_predictor'], entry['best_advanced_accuracy_percent'])} |"
            )
        lines.append("")
        lines.append("Representative best-fit configs:")
        for entry in scenario["budget_reports"]:
            top_three = "; ".join(
                f"{candidate['predictor']} {candidate['accuracy_percent']:.2f}% ({_format_budget_candidate_label(candidate)})"
                for candidate in entry["predictor_results"][:3]
            )
            lines.append(f"- `{entry['budget_bits']} bits` → {top_three}")
        lines.append("")

    lines.extend(
        [
            "## Portfolio usage",
            "",
            "- Use this report when you want to show that ‘best predictor’ depends not only on the trace family, but also on the hardware budget you are willing to spend.",
            "- Use the new whole-grid summary before diving into per-workload rows when you want one fast answer for which predictors dominate the entire budget grid most often.",
            "- Use the margin-trend section when you want to point out that some budget winners are basically photo finishes while others create real separation from the runner-up.",
            "- Use the crossover section when you want the exact budget step that triggers an architecture change instead of only a winner-at-each-budget table, and point at the blue flip chips on the SVG matrix when you need the screenshot to show that trigger directly.",
            "- Pair it with the trace-family sweep and perceptron tuning artifact so you can discuss workload sensitivity, hardware budget, and parameter tuning as three separate design axes.",
            "- The budget-normalized view is especially useful in interviews because it turns a raw accuracy chart into an architecture trade-off conversation.",
            "- Import the CSV export into spreadsheets or slide-deck tooling when you want to chart winner changes across budgets without scraping Markdown.",
            "",
        ]
    )
    return "\n".join(lines)


def render_budget_sweep_csv(*, scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    budgets = scenarios[0]["budgets"]
    crossover_summary = summarize_budget_crossover_points(scenarios)
    crossover_rows_by_workload = {row['workload']: row for row in crossover_summary['workload_rows']}
    fieldnames = [
        "workload",
        "headline",
        "branches",
        "seed",
        "trace_output",
        "winner_sequence",
        "crossover_count",
        "crossover_sequence",
    ]
    for budget in budgets:
        prefix = f"budget_{budget}_"
        fieldnames.extend(
            [
                f"{prefix}winner_predictor",
                f"{prefix}winner_accuracy_percent",
                f"{prefix}winner_state_bits",
                f"{prefix}winner_config",
                f"{prefix}runner_up_predictor",
                f"{prefix}runner_up_accuracy_percent",
                f"{prefix}winner_margin_percent",
                f"{prefix}best_simple_predictor",
                f"{prefix}best_simple_accuracy_percent",
                f"{prefix}best_advanced_predictor",
                f"{prefix}best_advanced_accuracy_percent",
            ]
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for scenario in scenarios:
        workload_crossover = crossover_rows_by_workload[scenario['workload']]
        row: dict[str, Any] = {
            "workload": scenario["workload"],
            "headline": scenario["headline"],
            "branches": scenario["config"]["branches"],
            "seed": scenario["config"]["seed"],
            "trace_output": scenario.get("trace_output") or "",
            "winner_sequence": _budget_winner_sequence_csv(scenario["budget_reports"]),
            "crossover_count": workload_crossover["crossover_count"],
            "crossover_sequence": workload_crossover["crossover_sequence"],
        }
        for entry in scenario["budget_reports"]:
            winner = entry["predictor_results"][0]
            runner_up = entry["predictor_results"][1] if len(entry["predictor_results"]) > 1 else winner
            prefix = f"budget_{entry['budget_bits']}_"
            row.update(
                {
                    f"{prefix}winner_predictor": entry["winner_predictor"],
                    f"{prefix}winner_accuracy_percent": entry["winner_accuracy_percent"],
                    f"{prefix}winner_state_bits": winner["state_bits"],
                    f"{prefix}winner_config": _format_budget_candidate_csv_label(winner),
                    f"{prefix}runner_up_predictor": entry["runner_up_predictor"],
                    f"{prefix}runner_up_accuracy_percent": runner_up["accuracy_percent"],
                    f"{prefix}winner_margin_percent": entry["winner_margin_percent"],
                    f"{prefix}best_simple_predictor": entry["best_simple_predictor"] or "",
                    f"{prefix}best_simple_accuracy_percent": entry["best_simple_accuracy_percent"] if entry["best_simple_accuracy_percent"] is not None else "",
                    f"{prefix}best_advanced_predictor": entry["best_advanced_predictor"] or "",
                    f"{prefix}best_advanced_accuracy_percent": entry["best_advanced_accuracy_percent"] if entry["best_advanced_accuracy_percent"] is not None else "",
                }
            )
        writer.writerow(row)
    return output.getvalue()


def render_budget_sweep_svg(*, scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    budgets = scenarios[0]["budgets"]
    winner_summary = summarize_budget_winner_grid(scenarios)
    margin_summary = summarize_budget_margin_story(scenarios)
    crossover_summary = summarize_budget_crossover_points(scenarios)
    crossover_lookup = _build_budget_crossover_lookup(crossover_summary)
    display_crossovers = crossover_summary['crossovers'][:6]
    summary_predictors = winner_summary["predictors"]
    width = 1320
    cell_w = 180
    cell_h = 84
    left_w = 220
    summary_y = 100
    stacked_w = 430
    heatmap_x = 480
    heatmap_w = width - heatmap_x - 28
    stacked_h = max(156, 54 + (len(summary_predictors) * 28))
    heatmap_h = max(156, 66 + (len(summary_predictors) * 28))
    margin_y = summary_y + max(stacked_h, heatmap_h) + 18
    margin_card_h = 190
    crossover_card_h = max(130, 84 + (((len(display_crossovers) + (1 if len(display_crossovers) > 3 else 0)) // (2 if len(display_crossovers) > 3 else 1)) * 26))
    crossover_y = margin_y + margin_card_h + 18
    grid_y = crossover_y + crossover_card_h + 24
    height = grid_y + 56 + (cell_h * len(scenarios)) + 82
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Budget-normalized branch predictor sweep</title>',
        '<desc id="desc">Winner matrix plus whole-grid summary across synthetic workloads and predictor state-bit budgets, including exact crossover points where the winning predictor changes.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 40, "Budget-normalized branch predictor sweep", size=28, weight="700"),
        _svg_text(28, 66, "Best-fit predictor per workload after constraining each candidate by approximate state bits.", size=14, fill="#334155"),
    ]
    legend_x = 28
    legend_y = 78
    for index, predictor in enumerate(summary_predictors):
        x = legend_x + (index * 140)
        parts.append(f'<rect x="{x}" y="{legend_y}" width="18" height="18" rx="6" fill="{_budget_predictor_fill(predictor)}" />')
        parts.append(_svg_text(x + 26, legend_y + 14, predictor, size=12, weight="700", fill="#334155"))

    parts.append(f'<rect x="28" y="{summary_y}" width="{stacked_w}" height="{stacked_h}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(46, summary_y + 32, "Grid win totals", size=20, weight="700"))
    parts.append(_svg_text(46, summary_y + 52, f"{winner_summary['total_cells']} workload-budget cells across {winner_summary['workload_count']} workloads", size=12, fill="#64748b"))
    bar_left = 170
    bar_right = 28 + stacked_w - 22
    bar_width = bar_right - bar_left
    max_wins = max((row['wins'] for row in winner_summary['predictor_rows']), default=1)
    for index, row in enumerate(winner_summary['predictor_rows']):
        y = summary_y + 74 + (index * 28)
        parts.append(_svg_text(46, y + 14, row['predictor'], size=12, weight='700', fill='#334155'))
        parts.append(f'<rect x="{bar_left}" y="{y}" width="{bar_width}" height="16" rx="8" fill="#e2e8f0" />')
        fill_width = 0 if max_wins == 0 else bar_width * (row['wins'] / max_wins)
        parts.append(f'<rect x="{bar_left}" y="{y}" width="{fill_width:.1f}" height="16" rx="8" fill="{_budget_predictor_fill(row["predictor"])}" />')
        parts.append(_svg_text(bar_left + 8, y + 12, f"{row['wins']} wins", size=10, weight='700', fill='#0f172a'))
        parts.append(_svg_text(bar_right - 72, y + 12, f"{row['share_percent']:.1f}%", size=10, weight='700', fill='#0f172a'))

    parts.append(f'<rect x="{heatmap_x}" y="{summary_y}" width="{heatmap_w}" height="{heatmap_h}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(heatmap_x + 18, summary_y + 32, "Budget winner heatmap", size=20, weight="700"))
    parts.append(_svg_text(heatmap_x + 18, summary_y + 52, "Counts show how many workloads each predictor wins at each budget.", size=12, fill="#64748b"))
    heatmap_left = heatmap_x + 130
    heatmap_top = summary_y + 72
    heatmap_cell_w = max(84, (heatmap_w - 160) // max(1, len(budgets)))
    heatmap_cell_h = 24
    for column, budget in enumerate(budgets):
        x = heatmap_left + (column * heatmap_cell_w)
        parts.append(_svg_text(x + 10, heatmap_top - 12, f"{budget}b", size=11, weight='700', fill='#475569'))
    for row_index, predictor in enumerate(summary_predictors):
        y = heatmap_top + (row_index * heatmap_cell_h)
        parts.append(_svg_text(heatmap_x + 18, y + 16, predictor, size=11, weight='700', fill='#334155'))
        for column, budget_row in enumerate(winner_summary['budget_rows']):
            x = heatmap_left + (column * heatmap_cell_w)
            count = budget_row['predictor_counts'][predictor]
            parts.append(
                f'<rect x="{x}" y="{y}" width="{heatmap_cell_w - 8}" height="18" rx="9" fill="{_budget_heatmap_fill(count, winner_summary["max_budget_wins"])}" stroke="#dbe4ee" />'
            )
            parts.append(_svg_text(x + (heatmap_cell_w / 2) - 4, y + 14, str(count), size=10, weight='700', fill='#0f172a'))

    parts.append(f'<rect x="28" y="{margin_y}" width="{stacked_w}" height="{margin_card_h}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(46, margin_y + 32, "Near-tie counts", size=20, weight="700"))
    parts.append(_svg_text(46, margin_y + 52, "How often the winner is separated from the runner-up by only a tiny accuracy gap.", size=12, fill="#64748b"))
    tie_bar_left = 200
    tie_bar_right = 28 + stacked_w - 22
    tie_bar_width = tie_bar_right - tie_bar_left
    max_threshold_count = max((row['count'] for row in margin_summary['threshold_rows']), default=1)
    for index, row in enumerate(margin_summary['threshold_rows']):
        y = margin_y + 74 + (index * 32)
        parts.append(_svg_text(46, y + 14, row['label'], size=12, weight='700', fill='#334155'))
        parts.append(f'<rect x="{tie_bar_left}" y="{y}" width="{tie_bar_width}" height="16" rx="8" fill="#e2e8f0" />')
        fill_width = 0 if max_threshold_count == 0 else tie_bar_width * (row['count'] / max_threshold_count)
        parts.append(f'<rect x="{tie_bar_left}" y="{y}" width="{fill_width:.1f}" height="16" rx="8" fill="#f59e0b" />')
        parts.append(_svg_text(tie_bar_left + 8, y + 12, f"{row['count']} cells", size=10, weight='700', fill='#0f172a'))
        parts.append(_svg_text(tie_bar_right - 76, y + 12, f"{row['share_percent']:.1f}%", size=10, weight='700', fill='#0f172a'))
    parts.append(_svg_text(46, margin_y + 178, f"Tightest: {margin_summary['tightest_cell']['workload']} @ {margin_summary['tightest_cell']['budget_bits']}b ({margin_summary['tightest_cell']['winner_margin_percent']:.2f} pp)", size=11, fill='#475569'))

    parts.append(f'<rect x="{heatmap_x}" y="{margin_y}" width="{heatmap_w}" height="{margin_card_h}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(heatmap_x + 18, margin_y + 32, "Winner-margin trend by budget", size=20, weight="700"))
    parts.append(_svg_text(heatmap_x + 18, margin_y + 52, "Average winner gap per budget, with close-race counts kept alongside each point.", size=12, fill="#64748b"))
    trend_left = heatmap_x + 68
    trend_right = heatmap_x + heatmap_w - 26
    trend_top = margin_y + 76
    trend_bottom = margin_y + 134
    trend_w = trend_right - trend_left
    trend_h = trend_bottom - trend_top
    parts.append(f'<line x1="{trend_left}" y1="{trend_bottom}" x2="{trend_right}" y2="{trend_bottom}" stroke="#cbd5e1" stroke-width="1" />')
    parts.append(f'<line x1="{trend_left}" y1="{trend_top}" x2="{trend_left}" y2="{trend_bottom}" stroke="#cbd5e1" stroke-width="1" />')
    max_average_margin = max(margin_summary['max_average_margin'], 1.0)
    trend_points: list[tuple[float, float]] = []
    budget_rows = margin_summary['budget_rows']
    for index, row in enumerate(budget_rows):
        x = trend_left if len(budget_rows) == 1 else trend_left + (trend_w * index / (len(budget_rows) - 1))
        y = trend_bottom - (trend_h * (row['average_margin_percent'] / max_average_margin))
        trend_points.append((x, y))
        parts.append(f'<line x1="{x}" y1="{trend_top}" x2="{x}" y2="{trend_bottom}" stroke="#e2e8f0" stroke-dasharray="3 4" />')
        parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#0ea5e9" stroke="#ffffff" stroke-width="2" />')
        parts.append(_svg_text(x - 18, trend_bottom + 18, f"{row['budget_bits']}b", size=10, weight='700', fill='#475569'))
        parts.append(_svg_text(x - 22, y - 10, f"{row['average_margin_percent']:.2f}", size=10, weight='700', fill='#0f172a'))
        parts.append(_svg_text(x - 28, trend_bottom + 34, f"tight {row['close_race_count']}/{row['cell_count']}", size=10, fill='#475569'))
        if row['top_runner_up_predictor'] is not None:
            parts.append(_svg_text(x - 34, trend_bottom + 48, _truncate_svg_text(f"RU {row['top_runner_up_predictor']}×{row['top_runner_up_count']}", 16), size=10, fill='#64748b'))
    if len(trend_points) >= 2:
        path_data = " ".join(
            ("M" if index == 0 else "L") + f" {x:.1f} {y:.1f}"
            for index, (x, y) in enumerate(trend_points)
        )
        parts.append(f'<path d="{path_data}" fill="none" stroke="#0ea5e9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
    parts.append(_svg_text(heatmap_x + 18, margin_y + 176, f"Widest: {margin_summary['widest_cell']['workload']} @ {margin_summary['widest_cell']['budget_bits']}b ({margin_summary['widest_cell']['winner_margin_percent']:.2f} pp)", size=11, fill='#475569'))

    parts.append(f'<rect x="28" y="{crossover_y}" width="{width - 56}" height="{crossover_card_h}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(46, crossover_y + 32, "Winner crossover points", size=20, weight="700"))
    parts.append(_svg_text(46, crossover_y + 52, "Exact adjacent-budget steps where the winning predictor changes.", size=12, fill="#64748b"))
    if display_crossovers:
        column_count = 2 if len(display_crossovers) > 3 else 1
        per_column = (len(display_crossovers) + column_count - 1) // column_count
        column_width = (width - 92) / column_count
        for index, row in enumerate(display_crossovers):
            column = index // per_column
            row_index = index % per_column
            x = 46 + (column * column_width)
            y = crossover_y + 76 + (row_index * 26)
            parts.append(f'<rect x="{x}" y="{y - 12}" width="{column_width - 18:.1f}" height="20" rx="10" fill="#eff6ff" stroke="#bfdbfe" />')
            parts.append(_svg_text(x + 10, y + 2, _truncate_svg_text(f"{row['workload']}: {row['from_budget_bits']}→{row['to_budget_bits']}b {row['previous_winner_predictor']}→{row['next_winner_predictor']}", 54), size=11, weight='700', fill='#1d4ed8'))
        if crossover_summary['transition_rows']:
            top_transition = crossover_summary['transition_rows'][0]
            workloads = ', '.join(top_transition['workloads'])
            parts.append(_svg_text(46, crossover_y + crossover_card_h - 18, _truncate_svg_text(f"Most repeated transition: {top_transition['from_budget_bits']}→{top_transition['to_budget_bits']}b {top_transition['previous_winner_predictor']}→{top_transition['next_winner_predictor']} across {top_transition['count']} workload(s): {workloads}", 140), size=11, fill='#475569'))
    else:
        parts.append(_svg_text(46, crossover_y + 88, "No winner changes across adjacent budgets in this sweep.", size=13, weight='700', fill='#475569'))

    grid_x = 28
    parts.append(_svg_text(grid_x, grid_y - 14, "Blue flip chips mark the budget cell where the winner changes from the previous column.", size=12, weight="700", fill="#1d4ed8"))
    parts.append(f'<rect x="{grid_x}" y="{grid_y}" width="{left_w}" height="42" rx="14" fill="#e2e8f0" />')
    parts.append(_svg_text(grid_x + 18, grid_y + 27, "Workload", size=13, weight="700", fill="#334155"))
    for column, budget in enumerate(budgets):
        x = grid_x + left_w + (column * cell_w)
        parts.append(f'<rect x="{x}" y="{grid_y}" width="{cell_w - 12}" height="42" rx="14" fill="#e2e8f0" />')
        parts.append(_svg_text(x + 18, grid_y + 27, f"{budget} bits", size=13, weight="700", fill="#334155"))

    start_y = grid_y + 56
    for row, scenario in enumerate(scenarios):
        y = start_y + (row * cell_h)
        parts.append(f'<rect x="{grid_x}" y="{y}" width="{left_w}" height="{cell_h - 10}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(grid_x + 18, y + 30, scenario["workload"], size=15, weight="700"))
        _svg_add_wrapped_text(parts, grid_x + 18, y + 50, scenario["headline"], max_chars=26, size=11, fill="#64748b")
        for column, entry in enumerate(scenario["budget_reports"]):
            x = grid_x + left_w + (column * cell_w)
            fill = _budget_predictor_fill(entry["winner_predictor"])
            crossover = crossover_lookup.get((scenario["workload"], entry["budget_bits"]))
            stroke = "#2563eb" if crossover is not None else "#dbe4ee"
            stroke_width = "2" if crossover is not None else "1"
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_w - 12}" height="{cell_h - 10}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
            )
            text_fill = "#0f172a"
            if crossover is not None:
                badge_label = _budget_crossover_chip_label(crossover)
                badge_w = max(54, 18 + (len(badge_label) * 6))
                badge_x = x + (cell_w - 12) - badge_w - 10
                badge_y = y + 8
                parts.append(f'<rect x="{badge_x}" y="{badge_y}" width="{badge_w}" height="18" rx="9" fill="#eff6ff" stroke="#60a5fa" />')
                parts.append(_svg_text(badge_x + 8, badge_y + 12, badge_label, size=9, weight="700", fill="#1d4ed8"))
            parts.append(_svg_text(x + 16, y + 28, entry["winner_predictor"], size=14, weight="700", fill=text_fill))
            parts.append(_svg_text(x + 16, y + 48, f"{entry['winner_accuracy_percent']:.2f}%", size=18, weight="700", fill=text_fill))
            runner_up_line = _truncate_svg_text(
                f"runner-up: {entry['runner_up_predictor']} (+{entry['winner_margin_percent']:.2f} pp)",
                28 if crossover is None else 24,
            )
            parts.append(_svg_text(x + 16, y + 66, runner_up_line, size=10, fill=text_fill))

    footer_y = height - 24
    parts.append(_svg_text(28, footer_y, "Use the top summary first for the whole-grid story, then the matrix below for workload-by-workload budget trade-offs.", size=12, fill="#475569"))
    parts.append('</svg>')
    return ''.join(parts) + "\n"


def run_table_size_alias_sweep(
    workloads: list[str] | None = None,
    *,
    branches_override: int | None = None,
    seed_override: int | None = None,
    table_sizes: list[int] | tuple[int, ...] | None = None,
    history_bits_override: int | None = None,
    trace_dir: Path | None = None,
) -> list[dict[str, Any]]:
    selected = workloads or list(SYNTHETIC_WORKLOADS)
    table_values = sorted({value for value in (table_sizes or TABLE_SIZE_ALIAS_SWEEP_TABLE_SIZES) if value >= 2})
    if not table_values:
        raise ValueError("table_sizes must contain at least one value >= 2")
    scenarios: list[dict[str, Any]] = []
    if trace_dir is not None:
        trace_dir.mkdir(parents=True, exist_ok=True)

    for workload in selected:
        if workload not in WORKLOAD_SWEEP_PROFILES:
            supported = ", ".join(sorted(WORKLOAD_SWEEP_PROFILES))
            raise ValueError(f"unsupported table-size sweep workload: {workload}. Expected one of: {supported}")
        profile = WORKLOAD_SWEEP_PROFILES[workload]
        branches = branches_override if branches_override is not None else int(profile["branches"])
        seed = seed_override if seed_override is not None else int(profile["seed"])
        history_bits = history_bits_override if history_bits_override is not None else int(profile["history_bits"])
        records = generate_synthetic_trace(workload, branches=branches, seed=seed)
        trace_output: Path | None = None
        if trace_dir is not None:
            trace_output = trace_dir / f"{workload}-seed{seed}.trace"
            trace_output.write_text(f"{format_trace(records)}\n", encoding="utf-8")

        sweep_rows: list[dict[str, Any]] = []
        for table_size in table_values:
            alias_summary = summarize_table_aliasing(records, table_size=table_size)
            gshare_alias_summary = summarize_gshare_aliasing(records, table_size=table_size, history_bits=history_bits)
            two_bit = simulate_trace(records, TwoBitPredictor(table_size=table_size))
            gshare = simulate_trace(records, GSharePredictor(table_size=table_size, history_bits=history_bits))
            sweep_rows.append(
                {
                    "table_size": table_size,
                    "static_colliding_indices": alias_summary["colliding_indices"],
                    "static_conflicting_indices": alias_summary["conflicting_indices"],
                    "static_branch_events_in_collisions": alias_summary["branch_events_in_collisions"],
                    "dynamic_colliding_indices": gshare_alias_summary["colliding_indices"],
                    "dynamic_conflicting_indices": gshare_alias_summary["conflicting_indices"],
                    "dynamic_cross_address_colliding_indices": gshare_alias_summary["cross_address_colliding_indices"],
                    "dynamic_history_spread_colliding_indices": gshare_alias_summary["history_spread_colliding_indices"],
                    "dynamic_branch_events_in_collisions": gshare_alias_summary["branch_events_in_collisions"],
                    "two_bit_accuracy_percent": round(two_bit.accuracy * 100, 3),
                    "gshare_accuracy_percent": round(gshare.accuracy * 100, 3),
                }
            )

        best_static_row = min(
            sweep_rows,
            key=lambda row: (row["static_colliding_indices"], row["static_conflicting_indices"], row["table_size"]),
        )
        best_dynamic_row = min(
            sweep_rows,
            key=lambda row: (
                row["dynamic_colliding_indices"],
                row["dynamic_conflicting_indices"],
                row["dynamic_cross_address_colliding_indices"],
                row["table_size"],
            ),
        )
        scenarios.append(
            {
                "workload": workload,
                "headline": profile["headline"],
                "config": {
                    "branches": branches,
                    "seed": seed,
                    "history_bits": history_bits,
                },
                "trace_output": str(trace_output) if trace_output is not None else None,
                "trace_summary": summarize_trace(records),
                "table_sizes": table_values,
                "sweep_rows": sweep_rows,
                "best_static_table_size": best_static_row["table_size"],
                "best_dynamic_table_size": best_dynamic_row["table_size"],
                "static_collision_drop": sweep_rows[0]["static_colliding_indices"] - sweep_rows[-1]["static_colliding_indices"],
                "dynamic_collision_drop": sweep_rows[0]["dynamic_colliding_indices"] - sweep_rows[-1]["dynamic_colliding_indices"],
            }
        )
    return scenarios


def format_table_size_alias_summary_table(scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        return "no scenarios"
    table_sizes = scenarios[0]["table_sizes"]
    header = ["workload", "history", *[f"{table_size}e" for table_size in table_sizes]]
    lines = [" | ".join(header), " | ".join(["---"] * len(header))]
    for scenario in scenarios:
        cells = [scenario["workload"], str(scenario["config"]["history_bits"])]
        for row in scenario["sweep_rows"]:
            cells.append(f"S{row['static_colliding_indices']}/G{row['dynamic_colliding_indices']}")
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def render_table_size_alias_markdown(*, scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    generated = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    table_sizes = scenarios[0]["table_sizes"]
    lines = [
        "# Branch predictor alias table-size sweep",
        "",
        f"- Generated: `{generated}`",
        f"- Workloads: `{len(scenarios)}` synthetic families",
        f"- Table sizes: `{', '.join(str(value) for value in table_sizes)}`",
        "- Goal: compare static PC-index aliasing and dynamic gshare live collisions side by side across the same workload family as table size changes.",
        "- Dynamic note: gshare collisions do not have to fall monotonically because XORed history bits can reshuffle which branch-history contexts share each counter bucket.",
        "",
        "## Overview",
        "",
        "| Workload | History bits | " + " | ".join(f"`{table_size}` entries" for table_size in table_sizes) + " |",
        "| --- | ---: | " + " | ".join(["---"] * len(table_sizes)) + " |",
    ]
    for scenario in scenarios:
        row = [f"`{scenario['workload']}`", f"`{scenario['config']['history_bits']}`"]
        for cell in scenario["sweep_rows"]:
            row.append(f"`S{cell['static_colliding_indices']}/G{cell['dynamic_colliding_indices']}`")
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(["", "## Per-workload notes", ""])
    for scenario in scenarios:
        lines.extend(
            [
                f"### `{scenario['workload']}`",
                "",
                f"- Focus: {scenario['headline']}",
                f"- Trace config: `branches={scenario['config']['branches']}` · `seed={scenario['config']['seed']}` · `history={scenario['config']['history_bits']}`",
                f"- Lowest static PC-collision count appears at table size `{scenario['best_static_table_size']}`; lowest dynamic gshare collision count appears at table size `{scenario['best_dynamic_table_size']}`.",
                f"- Sweep delta from smallest to largest table: static `{scenario['sweep_rows'][0]['static_colliding_indices']} → {scenario['sweep_rows'][-1]['static_colliding_indices']}` · dynamic `{scenario['sweep_rows'][0]['dynamic_colliding_indices']} → {scenario['sweep_rows'][-1]['dynamic_colliding_indices']}` live collisions.",
                "",
                "| Table entries | Static collisions | Static conflicting | Static events | Dynamic collisions | Dynamic conflicting | Cross-PC dynamic | History-spread dynamic | Two-bit acc. | Gshare acc. |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in scenario["sweep_rows"]:
            lines.append(
                f"| `{row['table_size']}` | `{row['static_colliding_indices']}` | `{row['static_conflicting_indices']}` | `{row['static_branch_events_in_collisions']}` | `{row['dynamic_colliding_indices']}` | `{row['dynamic_conflicting_indices']}` | `{row['dynamic_cross_address_colliding_indices']}` | `{row['dynamic_history_spread_colliding_indices']}` | `{row['two_bit_accuracy_percent']:.2f}%` | `{row['gshare_accuracy_percent']:.2f}%` |"
            )
        lines.extend(
            [
                "",
                "Interpretation tips:",
                "- Static counts answer: 'how many PCs collide if the table indexes only by PC bits?'",
                "- Dynamic counts answer: 'how many live gshare buckets still merge multiple PC+history contexts after XORing in global history?'",
                "- The paired accuracy columns keep the alias numbers grounded so interviewers can see when fewer collisions actually translate into fewer mispredictions.",
                "",
            ]
        )

    lines.extend(
        [
            "## Portfolio usage",
            "",
            "- Use this artifact after the single-trace alias-thrash comparison card when you want to show that static and dynamic aliasing shrink differently as the predictor table grows.",
            "- Use the CSV export when you want to chart collision counts or overlay accuracy/collision trade-offs in slides without scraping Markdown.",
            "- The non-monotonic dynamic rows are useful interview material because they show that history-aware predictors change the indexing problem rather than simply eliminating aliasing.",
            "",
        ]
    )
    return "\n".join(lines)


def render_table_size_alias_csv(*, scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    fieldnames = [
        "workload",
        "headline",
        "branches",
        "seed",
        "history_bits",
        "trace_output",
        "table_size",
        "static_colliding_indices",
        "static_conflicting_indices",
        "static_branch_events_in_collisions",
        "dynamic_colliding_indices",
        "dynamic_conflicting_indices",
        "dynamic_cross_address_colliding_indices",
        "dynamic_history_spread_colliding_indices",
        "dynamic_branch_events_in_collisions",
        "two_bit_accuracy_percent",
        "gshare_accuracy_percent",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for scenario in scenarios:
        for row in scenario["sweep_rows"]:
            writer.writerow(
                {
                    "workload": scenario["workload"],
                    "headline": scenario["headline"],
                    "branches": scenario["config"]["branches"],
                    "seed": scenario["config"]["seed"],
                    "history_bits": scenario["config"]["history_bits"],
                    "trace_output": scenario.get("trace_output") or "",
                    "table_size": row["table_size"],
                    "static_colliding_indices": row["static_colliding_indices"],
                    "static_conflicting_indices": row["static_conflicting_indices"],
                    "static_branch_events_in_collisions": row["static_branch_events_in_collisions"],
                    "dynamic_colliding_indices": row["dynamic_colliding_indices"],
                    "dynamic_conflicting_indices": row["dynamic_conflicting_indices"],
                    "dynamic_cross_address_colliding_indices": row["dynamic_cross_address_colliding_indices"],
                    "dynamic_history_spread_colliding_indices": row["dynamic_history_spread_colliding_indices"],
                    "dynamic_branch_events_in_collisions": row["dynamic_branch_events_in_collisions"],
                    "two_bit_accuracy_percent": row["two_bit_accuracy_percent"],
                    "gshare_accuracy_percent": row["gshare_accuracy_percent"],
                }
            )
    return output.getvalue()


def render_table_size_alias_svg(*, scenarios: list[dict[str, Any]]) -> str:
    if not scenarios:
        raise ValueError("scenarios must not be empty")
    table_sizes = scenarios[0]["table_sizes"]
    cell_w = 166
    cell_h = 96
    left_w = 238
    width = 28 + left_w + (len(table_sizes) * cell_w) + 20
    height = 188 + (len(scenarios) * cell_h) + 82
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Branch predictor alias table-size sweep</title>',
        '<desc id="desc">Side-by-side static PC and dynamic gshare collision counts across table sizes.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 40, "Branch predictor alias table-size sweep", size=28, weight="700"),
        _svg_text(28, 66, "Each cell shows static PC collisions (S) and dynamic gshare live collisions (G) for the same seeded trace.", size=14, fill="#334155"),
        _svg_text(28, 92, "Top line = static PC buckets · middle = dynamic gshare buckets · bottom = two-bit vs gshare accuracy.", size=12, fill="#64748b"),
    ]

    grid_x = 28
    grid_y = 120
    parts.append(f'<rect x="{grid_x}" y="{grid_y}" width="{left_w}" height="42" rx="14" fill="#e2e8f0" />')
    parts.append(_svg_text(grid_x + 18, grid_y + 27, "Workload", size=13, weight="700", fill="#334155"))
    for column, table_size in enumerate(table_sizes):
        x = grid_x + left_w + (column * cell_w)
        parts.append(f'<rect x="{x}" y="{grid_y}" width="{cell_w - 12}" height="42" rx="14" fill="#e2e8f0" />')
        parts.append(_svg_text(x + 18, grid_y + 27, f"{table_size} entries", size=13, weight="700", fill="#334155"))

    start_y = grid_y + 56
    for row_index, scenario in enumerate(scenarios):
        y = start_y + (row_index * cell_h)
        parts.append(f'<rect x="{grid_x}" y="{y}" width="{left_w}" height="{cell_h - 12}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(grid_x + 18, y + 30, scenario["workload"], size=15, weight="700"))
        _svg_add_wrapped_text(parts, grid_x + 18, y + 50, scenario["headline"], max_chars=24, size=11, fill="#64748b")
        parts.append(_svg_text(grid_x + 18, y + 78, f"history={scenario['config']['history_bits']} · seed={scenario['config']['seed']}", size=11, fill="#64748b"))
        for column, cell in enumerate(scenario["sweep_rows"]):
            x = grid_x + left_w + (column * cell_w)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w - 12}" height="{cell_h - 12}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
            parts.append(_svg_text(x + 16, y + 26, f"S {cell['static_colliding_indices']} · C {cell['static_conflicting_indices']}", size=13, weight="700", fill="#0f172a"))
            parts.append(_svg_text(x + 16, y + 46, f"G {cell['dynamic_colliding_indices']} · C {cell['dynamic_conflicting_indices']}", size=13, weight="700", fill="#2563eb"))
            parts.append(_svg_text(x + 16, y + 64, f"cross {cell['dynamic_cross_address_colliding_indices']} · hist {cell['dynamic_history_spread_colliding_indices']}", size=10, fill="#64748b"))
            parts.append(_svg_text(x + 16, y + 80, f"2b {cell['two_bit_accuracy_percent']:.1f}% · gsh {cell['gshare_accuracy_percent']:.1f}%", size=10, fill="#64748b"))

    footer_y = height - 24
    parts.append(_svg_text(28, footer_y, "Use this grid with the alias-thrash comparison card to discuss why history-aware hashing changes, but does not erase, branch-predictor aliasing.", size=12, fill="#475569"))
    parts.append('</svg>')
    return ''.join(parts) + "\n"


def render_perceptron_tuning_markdown(*, trace_path: Path, report: dict[str, Any]) -> str:
    generated = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    trace_summary = report["trace_summary"]
    best = report["best_config"]
    default = report["default_config"]
    lines = [
        "# Branch predictor perceptron tuning sweep",
        "",
        f"- Generated: `{generated}`",
        f"- Trace: `{trace_path}`",
        f"- Branches: `{trace_summary['total_branches']}` across `{trace_summary['unique_addresses']}` unique PCs",
        f"- Predictor config: `table={report['table_size']}` · `history={report['history_bits']}`",
        f"- Swept thresholds: `{', '.join(str(value) for value in report['thresholds'])}`",
        f"- Swept weight limits: `{', '.join(str(value) for value in report['weight_limits'])}`",
        f"- Default heuristic: `threshold={report['default_threshold']}` · `weight_limit={report['default_weight_limit']}`",
        "",
        "## Headlines",
        "",
        f"- Best config: `threshold={best['threshold']}` · `weight_limit={best['weight_limit']}` → `{best['accuracy_percent']:.2f}%` accuracy with `{best['mispredictions']}` mispredictions.",
    ]
    if default is not None:
        delta = best["accuracy_percent"] - default["accuracy_percent"]
        lines.append(
            f"- Default heuristic: `{default['accuracy_percent']:.2f}%` accuracy with `{default['mispredictions']}` mispredictions ({delta:+.2f} pp vs best)."
        )
    lines.extend(
        [
            f"- Saturation visible in `{report['saturated_config_count']}` / `{report['config_count']}` swept configs (`max|w|` hit the clamp limit).",
            "",
            "## Accuracy matrix",
            "",
        ]
    )
    header = ["Threshold ↓ / Weight limit →", *[f"`{value}`" for value in report["weight_limits"]]]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---", *(["---:"] * len(report["weight_limits"]))]) + " |")
    by_key = {(config["threshold"], config["weight_limit"]): config for config in report["configs"]}
    for threshold in report["thresholds"]:
        row = [f"`{threshold}`"]
        for weight_limit in report["weight_limits"]:
            config = by_key[(threshold, weight_limit)]
            badges: list[str] = []
            if config is best:
                badges.append("best")
            if config["is_default_config"]:
                badges.append("default")
            if config["saturated_max_weight"]:
                badges.append("sat")
            cell = f"{config['accuracy_percent']:.2f}%"
            if badges:
                cell += f" ({', '.join(badges)})"
            row.append(cell)
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "## Top configs",
            "",
            "| Rank | Threshold | Weight limit | Accuracy | Mispredictions | Max abs(w) | Notes |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for index, config in enumerate(report["configs"][: min(8, len(report["configs"]))], start=1):
        notes: list[str] = []
        if config is best:
            notes.append("best")
        if config["is_default_config"]:
            notes.append("default")
        if config["saturated_max_weight"]:
            notes.append("saturated")
        lines.append(
            f"| {index} | `{config['threshold']}` | `{config['weight_limit']}` | `{config['accuracy_percent']:.2f}%` | `{config['mispredictions']}` | `{config['max_abs_weight']}` | {', '.join(notes) or '-'} |"
        )

    lines.extend(
        [
            "",
            "## Portfolio usage",
            "",
            "- Use this report to show that neural branch predictors still need practical tuning; longer history alone is not the whole story.",
            "- Pair it with the perceptron-majority comparison card when you want both a single-trace win story and a parameter-sensitivity artifact.",
            "- Call out saturated low-clamp runs when explaining why hardware-friendly limits can trade off training headroom against stability.",
            "",
        ]
    )
    return "\n".join(lines)


def render_perceptron_tuning_svg(*, trace_path: Path, report: dict[str, Any]) -> str:
    thresholds = report["thresholds"]
    weight_limits = report["weight_limits"]
    best = report["best_config"]
    default = report["default_config"]
    width = 1080
    grid_x = 36
    grid_y = 214
    cell_w = 132
    cell_h = 54
    grid_w = cell_w * len(weight_limits)
    grid_h = cell_h * len(thresholds)
    top_rows = min(6, len(report["configs"]))
    height = max(620, grid_y + grid_h + 120, grid_y + (108 + (top_rows * 62)) + 60)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Perceptron tuning sweep</title>',
        f'<desc id="desc">Threshold and weight-limit sweep for {trace_path.stem}.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(36, 40, "Perceptron tuning sweep", size=28, weight="700"),
        _svg_text(36, 66, f"Trace: {trace_path.stem} · branches={report['trace_summary']['total_branches']} · table={report['table_size']} · history={report['history_bits']}", size=14, fill="#334155"),
    ]

    cards = [
        (36, "Best config", f"t={best['threshold']} · w={best['weight_limit']}", f"{best['accuracy_percent']:.2f}% accuracy"),
        (292, "Default heuristic", f"t={report['default_threshold']} · w={report['default_weight_limit']}", f"{default['accuracy_percent']:.2f}% accuracy" if default is not None else "not included in sweep"),
        (548, "Sweep size", f"{report['config_count']} configs", f"{len(thresholds)} thresholds × {len(weight_limits)} limits"),
        (804, "Saturated configs", str(report['saturated_config_count']), "configs hit the clamp ceiling"),
    ]
    for x, label, value, subtitle in cards:
        parts.append(f'<rect x="{x}" y="92" width="240" height="92" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(x + 18, 120, label, size=13, weight="700", fill="#475569"))
        parts.append(_svg_text(x + 18, 150, value, size=22, weight="700"))
        parts.append(_svg_text(x + 18, 170, _truncate_svg_text(subtitle, 32), size=11, fill="#64748b"))

    parts.append(_svg_text(grid_x, grid_y - 16, "Accuracy heatmap (threshold rows, weight-limit columns)", size=18, weight="700"))
    by_key = {(config["threshold"], config["weight_limit"]): config for config in report["configs"]}
    for column, weight_limit in enumerate(weight_limits):
        x = grid_x + 120 + column * cell_w
        parts.append(_svg_text(x + 24, grid_y - 16, f"w={weight_limit}", size=12, weight="700", fill="#475569"))
    for row, threshold in enumerate(thresholds):
        y = grid_y + row * cell_h
        parts.append(_svg_text(grid_x, y + 32, f"t={threshold}", size=12, weight="700", fill="#475569"))
        for column, weight_limit in enumerate(weight_limits):
            x = grid_x + 120 + column * cell_w
            config = by_key[(threshold, weight_limit)]
            fill = _perceptron_tuning_cell_fill(
                config["accuracy_percent"],
                report["min_accuracy_percent"],
                report["max_accuracy_percent"],
            )
            stroke = "#f59e0b" if config is best else ("#7c3aed" if config["is_default_config"] else "#dbe4ee")
            stroke_width = 3 if config is best else (2 if config["is_default_config"] else 1)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w - 10}" height="{cell_h - 10}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />')
            parts.append(_svg_text(x + 14, y + 24, f"{config['accuracy_percent']:.2f}%", size=14, weight="700", fill="#0f172a"))
            parts.append(_svg_text(x + 14, y + 40, _truncate_svg_text(f"miss={config['mispredictions']} · max|w|={config['max_abs_weight']}", 22), size=10, fill="#0f172a"))
            tags: list[str] = []
            if config is best:
                tags.append("best")
            if config["is_default_config"]:
                tags.append("default")
            if config["saturated_max_weight"]:
                tags.append("sat")
            if tags:
                parts.append(_svg_text(x + 14, y + 54, ", ".join(tags), size=10, weight="700", fill="#0f172a"))

    right_x = grid_x + 120 + grid_w + 28
    panel_w = width - right_x - 36
    panel_h = 108 + (top_rows * 62)
    parts.append(f'<rect x="{right_x}" y="{grid_y}" width="{panel_w}" height="{panel_h}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(right_x + 18, grid_y + 30, "Top tuning configs", size=20, weight="700"))
    current_y = grid_y + 60
    for index, config in enumerate(report["configs"][:top_rows], start=1):
        notes: list[str] = []
        if config is best:
            notes.append("best")
        if config["is_default_config"]:
            notes.append("default")
        if config["saturated_max_weight"]:
            notes.append("saturated")
        summary = (
            f"#{index} · t={config['threshold']} · w={config['weight_limit']} · {config['accuracy_percent']:.2f}% · "
            f"miss={config['mispredictions']}"
        )
        current_y = _svg_add_wrapped_text(parts, right_x + 18, current_y, summary, max_chars=28, size=13, fill="#334155") + 16
        if notes:
            parts.append(_svg_text(right_x + 18, current_y - 4, ", ".join(notes), size=11, weight="700", fill="#64748b"))
            current_y += 8

    footer_y = max(grid_y + grid_h + 46, grid_y + panel_h + 24)
    parts.append(_svg_text(36, footer_y, "Use this card beside the perceptron-majority comparison report to show tuning sensitivity, not just the headline win.", size=12, fill="#475569"))
    parts.append("</svg>")
    return "".join(parts) + "\n"


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
    simulate_parser.add_argument("--threshold", type=int, help="Perceptron confidence threshold override (perceptron only).")
    simulate_parser.add_argument("--weight-limit", type=int, help="Perceptron signed weight clamp limit (perceptron only).")
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

    perceptron_sweep_parser = subparsers.add_parser(
        "perceptron-sweep",
        help="Sweep perceptron threshold and weight-limit tuning on one trace.",
    )
    perceptron_sweep_parser.add_argument("trace", **common_help["trace"])
    perceptron_sweep_parser.add_argument("--table-size", **common_help["table_size"])
    perceptron_sweep_parser.add_argument("--history-bits", **common_help["history_bits"])
    perceptron_sweep_parser.add_argument("--thresholds", type=int, nargs="+", help="Optional threshold values to sweep.")
    perceptron_sweep_parser.add_argument("--weight-limits", type=int, nargs="+", help="Optional signed weight clamp limits to sweep.")
    perceptron_sweep_parser.add_argument("--markdown-out", type=Path, help="Write a Markdown tuning report.")
    perceptron_sweep_parser.add_argument("--svg-out", type=Path, help="Write an SVG tuning card.")
    perceptron_sweep_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary table.")

    budget_sweep_parser = subparsers.add_parser(
        "budget-sweep",
        help="Compare the best predictor configs that fit the same approximate state-bit budgets across synthetic workloads.",
    )
    budget_sweep_parser.add_argument(
        "workloads",
        nargs="*",
        choices=list(SYNTHETIC_WORKLOADS),
        help="Optional subset of workload families to include. Defaults to all built-in synthetic workloads.",
    )
    budget_sweep_parser.add_argument("--budgets", type=int, nargs="+", help="Optional state-bit budgets to compare.")
    budget_sweep_parser.add_argument("--branches", type=int, help="Override the branch count for every selected workload.")
    budget_sweep_parser.add_argument("--seed", type=int, help="Override the random seed for every selected workload.")
    budget_sweep_parser.add_argument("--table-sizes", type=int, nargs="+", help="Candidate table sizes to search under each budget.")
    budget_sweep_parser.add_argument("--history-bits-options", type=int, nargs="+", help="Candidate history-bit values to search under each budget.")
    budget_sweep_parser.add_argument("--weight-limits", type=int, nargs="+", help="Candidate perceptron weight-clamp limits to search under each budget.")
    budget_sweep_parser.add_argument("--trace-dir", type=Path, help="Optional directory to write the generated trace files for the budget sweep.")
    budget_sweep_parser.add_argument("--markdown-out", type=Path, help="Write a Markdown budget report.")
    budget_sweep_parser.add_argument("--svg-out", type=Path, help="Write an SVG budget matrix card.")
    budget_sweep_parser.add_argument("--csv-out", type=Path, help="Write a CSV winner matrix for spreadsheet/chart reuse.")
    budget_sweep_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary table.")

    table_size_sweep_parser = subparsers.add_parser(
        "table-size-sweep",
        help="Compare static PC aliasing and dynamic gshare aliasing across table sizes for one or more workloads.",
    )
    table_size_sweep_parser.add_argument(
        "workloads",
        nargs="*",
        choices=list(SYNTHETIC_WORKLOADS),
        help="Optional subset of workload families to include. Defaults to all built-in synthetic workloads.",
    )
    table_size_sweep_parser.add_argument("--branches", type=int, help="Override the branch count for every selected workload.")
    table_size_sweep_parser.add_argument("--seed", type=int, help="Override the random seed for every selected workload.")
    table_size_sweep_parser.add_argument("--history-bits", type=int, help="Override the history bits used for every selected workload.")
    table_size_sweep_parser.add_argument("--table-sizes", type=int, nargs="+", help="Optional table sizes to compare in the sweep.")
    table_size_sweep_parser.add_argument("--trace-dir", type=Path, help="Optional directory to write the generated trace files for the table-size sweep.")
    table_size_sweep_parser.add_argument("--markdown-out", type=Path, help="Write a Markdown alias sweep report.")
    table_size_sweep_parser.add_argument("--svg-out", type=Path, help="Write an SVG alias sweep summary card.")
    table_size_sweep_parser.add_argument("--csv-out", type=Path, help="Write a CSV alias sweep export for charting.")
    table_size_sweep_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary table.")
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

        if args.command == "perceptron-sweep":
            trace_path = Path(args.trace)
            records = load_trace(trace_path)
            report = run_perceptron_tuning_sweep(
                records,
                table_size=args.table_size,
                history_bits=args.history_bits,
                thresholds=list(args.thresholds) if args.thresholds else None,
                weight_limits=list(args.weight_limits) if args.weight_limits else None,
            )
            payload = {
                "trace": str(trace_path),
                **report,
            }
            if getattr(args, "markdown_out", None):
                write_markdown_output(args.markdown_out, render_perceptron_tuning_markdown(trace_path=trace_path, report=report))
                payload["markdown_output"] = str(args.markdown_out)
            if getattr(args, "svg_out", None):
                write_svg_output(args.svg_out, render_perceptron_tuning_svg(trace_path=trace_path, report=report))
                payload["svg_output"] = str(args.svg_out)
            if args.json:
                print(json.dumps(payload, indent=2, default=_json_default))
            else:
                print(format_perceptron_tuning_summary_table(report))
                print()
                print(
                    f"best config: threshold={report['best_config']['threshold']} weight_limit={report['best_config']['weight_limit']} "
                    f"({report['best_config']['accuracy_percent']:.2f}% accuracy)"
                )
                if report["default_config"] is not None:
                    print(
                        f"default heuristic: threshold={report['default_threshold']} weight_limit={report['default_weight_limit']} "
                        f"({report['default_config']['accuracy_percent']:.2f}% accuracy)"
                    )
                print(
                    f"saturated configs: {report['saturated_config_count']} / {report['config_count']} "
                    f"(max|w| reached the clamp limit)"
                )
                if "markdown_output" in payload:
                    print(f"markdown report: {payload['markdown_output']}")
                if "svg_output" in payload:
                    print(f"svg card: {payload['svg_output']}")
            return 0

        if args.command == "budget-sweep":
            scenarios = run_budget_workload_sweep(
                list(args.workloads),
                branches_override=args.branches,
                seed_override=args.seed,
                budgets=list(args.budgets) if args.budgets else None,
                table_sizes=list(args.table_sizes) if args.table_sizes else None,
                history_bits_options=list(args.history_bits_options) if args.history_bits_options else None,
                weight_limits=list(args.weight_limits) if args.weight_limits else None,
                trace_dir=args.trace_dir,
            )
            payload = {
                "workloads": [scenario["workload"] for scenario in scenarios],
                "scenario_count": len(scenarios),
                "winner_summary": summarize_budget_winner_grid(scenarios),
                "margin_summary": summarize_budget_margin_story(scenarios),
                "crossover_summary": summarize_budget_crossover_points(scenarios),
                "scenarios": scenarios,
            }
            if args.trace_dir is not None:
                payload["trace_dir"] = str(args.trace_dir)
            if getattr(args, "markdown_out", None):
                write_markdown_output(args.markdown_out, render_budget_sweep_markdown(scenarios=scenarios))
                payload["markdown_output"] = str(args.markdown_out)
            if getattr(args, "svg_out", None):
                write_svg_output(args.svg_out, render_budget_sweep_svg(scenarios=scenarios))
                payload["svg_output"] = str(args.svg_out)
            if getattr(args, "csv_out", None):
                write_csv_output(args.csv_out, render_budget_sweep_csv(scenarios=scenarios))
                payload["csv_output"] = str(args.csv_out)
            if args.json:
                print(json.dumps(payload, indent=2, default=_json_default))
            else:
                print(format_budget_sweep_summary_table(scenarios))
                if "markdown_output" in payload:
                    print(f"markdown report: {payload['markdown_output']}")
                if "svg_output" in payload:
                    print(f"svg card: {payload['svg_output']}")
                if "csv_output" in payload:
                    print(f"csv export: {payload['csv_output']}")
                if args.trace_dir is not None:
                    print(f"trace directory: {args.trace_dir}")
            return 0

        if args.command == "table-size-sweep":
            scenarios = run_table_size_alias_sweep(
                list(args.workloads),
                branches_override=args.branches,
                seed_override=args.seed,
                table_sizes=list(args.table_sizes) if args.table_sizes else None,
                history_bits_override=args.history_bits,
                trace_dir=args.trace_dir,
            )
            payload = {
                "workloads": [scenario["workload"] for scenario in scenarios],
                "scenario_count": len(scenarios),
                "scenarios": scenarios,
            }
            if args.trace_dir is not None:
                payload["trace_dir"] = str(args.trace_dir)
            if getattr(args, "markdown_out", None):
                write_markdown_output(args.markdown_out, render_table_size_alias_markdown(scenarios=scenarios))
                payload["markdown_output"] = str(args.markdown_out)
            if getattr(args, "svg_out", None):
                write_svg_output(args.svg_out, render_table_size_alias_svg(scenarios=scenarios))
                payload["svg_output"] = str(args.svg_out)
            if getattr(args, "csv_out", None):
                write_csv_output(args.csv_out, render_table_size_alias_csv(scenarios=scenarios))
                payload["csv_output"] = str(args.csv_out)
            if args.json:
                print(json.dumps(payload, indent=2, default=_json_default))
            else:
                print(format_table_size_alias_summary_table(scenarios))
                if "markdown_output" in payload:
                    print(f"markdown report: {payload['markdown_output']}")
                if "svg_output" in payload:
                    print(f"svg card: {payload['svg_output']}")
                if "csv_output" in payload:
                    print(f"csv export: {payload['csv_output']}")
                if args.trace_dir is not None:
                    print(f"trace directory: {args.trace_dir}")
            return 0

        records = load_trace(args.trace)
        if args.command == "compare":
            trace_path = Path(args.trace)
            trace_summary = summarize_trace(records)
            alias_summary = summarize_table_aliasing(records, table_size=args.table_size)
            gshare_alias_summary = summarize_gshare_aliasing(records, table_size=args.table_size, history_bits=args.history_bits)
            results = compare_predictors(records, table_size=args.table_size, history_bits=args.history_bits)
            payload = {
                "trace": str(trace_path),
                "table_size": args.table_size,
                "history_bits": args.history_bits,
                "trace_summary": trace_summary,
                "alias_summary": alias_summary,
                "gshare_alias_summary": gshare_alias_summary,
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
                        gshare_alias_summary=gshare_alias_summary,
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
                        gshare_alias_summary=gshare_alias_summary,
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
                print(
                    f"dynamic gshare aliasing: {gshare_alias_summary['colliding_indices']} live collisions at table size {gshare_alias_summary['table_size']} "
                    f"with history={gshare_alias_summary['history_bits']} ({gshare_alias_summary['conflicting_indices']} conflicting bias groups)"
                )
                if "markdown_output" in payload:
                    print(f"markdown card: {payload['markdown_output']}")
                if "svg_output" in payload:
                    print(f"svg card: {payload['svg_output']}")
            return 0

        predictor = build_predictor(
            args.predictor,
            table_size=args.table_size,
            history_bits=args.history_bits,
            threshold=getattr(args, "threshold", None),
            weight_limit=getattr(args, "weight_limit", None),
        )
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
