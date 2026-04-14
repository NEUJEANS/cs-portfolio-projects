import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Iterable

MAX_HASH_BITS = 64
MAX_HASH_VALUE = 1 << MAX_HASH_BITS


class HyperLogLog:
    def __init__(self, precision: int = 10, registers: list[int] | None = None):
        if not (4 <= precision <= 16):
            raise ValueError("precision must be between 4 and 16")
        self.precision = precision
        self.register_count = 1 << precision
        self.registers = list(registers or [0] * self.register_count)
        if len(self.registers) != self.register_count:
            raise ValueError("register count does not match precision")

    @classmethod
    def from_dict(cls, data: dict) -> "HyperLogLog":
        return cls(precision=data["precision"], registers=data["registers"])

    def to_dict(self) -> dict:
        return {
            "precision": self.precision,
            "register_count": self.register_count,
            "registers": self.registers,
        }

    def _hash(self, item: str) -> int:
        digest = hashlib.sha1(item.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big")

    def _split_hash(self, hashed: int) -> tuple[int, int]:
        suffix_width = MAX_HASH_BITS - self.precision
        index = hashed >> suffix_width
        remainder_mask = (1 << suffix_width) - 1
        remainder = hashed & remainder_mask
        rank = self._rho(remainder, suffix_width)
        return index, rank

    @staticmethod
    def _rho(value: int, width: int) -> int:
        if value == 0:
            return width + 1
        leading_zeros = width - value.bit_length()
        return leading_zeros + 1

    def add(self, item: str) -> None:
        index, rank = self._split_hash(self._hash(item))
        self.registers[index] = max(self.registers[index], rank)

    def extend(self, items: Iterable[str]) -> int:
        inserted = 0
        for item in items:
            normalized = item.strip()
            if not normalized:
                continue
            self.add(normalized)
            inserted += 1
        return inserted

    def merge(self, other: "HyperLogLog") -> "HyperLogLog":
        if self.precision != other.precision:
            raise ValueError("cannot merge HyperLogLogs with different precisions")
        return HyperLogLog(
            precision=self.precision,
            registers=[max(left, right) for left, right in zip(self.registers, other.registers)],
        )

    def alpha_m(self) -> float:
        m = self.register_count
        if m == 16:
            return 0.673
        if m == 32:
            return 0.697
        if m == 64:
            return 0.709
        return 0.7213 / (1 + 1.079 / m)

    def raw_estimate(self) -> float:
        denominator = sum(2.0 ** (-register) for register in self.registers)
        return self.alpha_m() * (self.register_count ** 2) / denominator

    def estimate(self) -> float:
        estimate = self.raw_estimate()
        zero_registers = self.registers.count(0)
        m = self.register_count

        if estimate <= (5 / 2) * m and zero_registers:
            return m * math.log(m / zero_registers)
        if estimate > MAX_HASH_VALUE / 30:
            capped_ratio = min(estimate / MAX_HASH_VALUE, 1 - 1e-12)
            return -MAX_HASH_VALUE * math.log(1 - capped_ratio)
        return estimate

    def stats(self) -> dict:
        estimate = self.estimate()
        return {
            "precision": self.precision,
            "register_count": self.register_count,
            "zero_registers": self.registers.count(0),
            "max_register": max(self.registers),
            "raw_estimate": self.raw_estimate(),
            "estimate": estimate,
            "rounded_estimate": round(estimate),
            "relative_error_bound": 1.04 / math.sqrt(self.register_count),
        }


def load_hll(path: Path) -> HyperLogLog:
    return HyperLogLog.from_dict(json.loads(path.read_text()))


def save_hll(path: Path, sketch: HyperLogLog) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sketch.to_dict(), indent=2) + "\n")


def read_items(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def simulate_accuracy(precision: int, cardinality: int, trials: int, seed: int = 0) -> dict:
    if cardinality <= 0:
        raise ValueError("cardinality must be greater than 0")
    if trials <= 0:
        raise ValueError("trials must be greater than 0")

    rng = random.Random(seed)
    estimates = []
    for trial in range(trials):
        sketch = HyperLogLog(precision=precision)
        items = [f"trial-{trial}-item-{index}-{rng.getrandbits(64):016x}" for index in range(cardinality)]
        sketch.extend(items)
        estimates.append(sketch.estimate())

    mean_estimate = sum(estimates) / len(estimates)
    absolute_errors = [abs(estimate - cardinality) for estimate in estimates]
    relative_errors = [error / cardinality for error in absolute_errors]
    return {
        "precision": precision,
        "cardinality": cardinality,
        "trials": trials,
        "seed": seed,
        "mean_estimate": mean_estimate,
        "min_estimate": min(estimates),
        "max_estimate": max(estimates),
        "mean_absolute_error": sum(absolute_errors) / len(absolute_errors),
        "mean_relative_error": sum(relative_errors) / len(relative_errors),
        "theoretical_error_bound": 1.04 / math.sqrt(1 << precision),
    }


def build_command(args: argparse.Namespace) -> int:
    sketch = HyperLogLog(precision=args.precision)
    inserted = sketch.extend(read_items(Path(args.input)))
    save_hll(Path(args.output), sketch)
    print(json.dumps({"inserted": inserted, "output": args.output, **sketch.stats()}, indent=2))
    return 0


def stats_command(args: argparse.Namespace) -> int:
    sketch = load_hll(Path(args.sketch))
    print(json.dumps(sketch.stats(), indent=2))
    return 0


def merge_command(args: argparse.Namespace) -> int:
    if len(args.sketches) < 2:
        raise ValueError("merge requires at least two sketch files")
    merged = load_hll(Path(args.sketches[0]))
    for path in args.sketches[1:]:
        merged = merged.merge(load_hll(Path(path)))
    if args.output:
        save_hll(Path(args.output), merged)
    print(json.dumps({"merged_inputs": args.sketches, "output": args.output, **merged.stats()}, indent=2))
    return 0


def simulate_command(args: argparse.Namespace) -> int:
    print(json.dumps(simulate_accuracy(args.precision, args.cardinality, args.trials, args.seed), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Estimate distinct counts with a HyperLogLog sketch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a sketch from newline-delimited input")
    build_parser.add_argument("--input", required=True, help="newline-delimited input file")
    build_parser.add_argument("--output", required=True, help="where to write sketch JSON")
    build_parser.add_argument("--precision", type=int, default=10, help="register precision between 4 and 16")
    build_parser.set_defaults(func=build_command)

    stats_parser = subparsers.add_parser("stats", help="inspect sketch statistics")
    stats_parser.add_argument("--sketch", required=True, help="saved sketch JSON")
    stats_parser.set_defaults(func=stats_command)

    merge_parser = subparsers.add_parser("merge", help="merge two or more sketches")
    merge_parser.add_argument("--output", help="optional output path for merged sketch")
    merge_parser.add_argument("sketches", nargs="+", help="input sketch files with matching precision")
    merge_parser.set_defaults(func=merge_command)

    simulate_parser = subparsers.add_parser("simulate", help="sample estimation error for synthetic unique items")
    simulate_parser.add_argument("--precision", type=int, default=10, help="register precision between 4 and 16")
    simulate_parser.add_argument("--cardinality", type=int, required=True, help="true number of unique items per trial")
    simulate_parser.add_argument("--trials", type=int, default=10, help="number of synthetic trials to run")
    simulate_parser.add_argument("--seed", type=int, default=0, help="deterministic seed")
    simulate_parser.set_defaults(func=simulate_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
