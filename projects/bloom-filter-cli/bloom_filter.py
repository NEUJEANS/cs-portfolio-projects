import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Iterable, List


class BloomFilter:
    def __init__(self, capacity: int, error_rate: float, bit_count: int | None = None, hash_count: int | None = None, inserted_count: int = 0, bits: int = 0):
        if capacity <= 0:
            raise ValueError("capacity must be greater than 0")
        if not (0 < error_rate < 1):
            raise ValueError("error_rate must be between 0 and 1")

        calculated_bits = math.ceil(-(capacity * math.log(error_rate)) / (math.log(2) ** 2))
        calculated_hashes = math.ceil((calculated_bits / capacity) * math.log(2))

        self.capacity = capacity
        self.error_rate = error_rate
        self.bit_count = max(1, bit_count or calculated_bits)
        self.hash_count = max(1, hash_count or calculated_hashes)
        self.inserted_count = inserted_count
        self.bits = bits

    @classmethod
    def from_dict(cls, data: dict) -> "BloomFilter":
        return cls(
            capacity=data["capacity"],
            error_rate=data["error_rate"],
            bit_count=data["bit_count"],
            hash_count=data["hash_count"],
            inserted_count=data.get("inserted_count", 0),
            bits=int(data.get("bits", "0"), 16),
        )

    def to_dict(self) -> dict:
        return {
            "capacity": self.capacity,
            "error_rate": self.error_rate,
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
            "bits": format(self.bits, "x"),
        }

    def _hashes(self, item: str) -> List[int]:
        payload = item.encode("utf-8")
        digest = hashlib.sha256(payload).digest()
        h1 = int.from_bytes(digest[:16], "big")
        h2 = int.from_bytes(digest[16:], "big") or 1
        return [((h1 + index * h2) % self.bit_count) for index in range(self.hash_count)]

    def add(self, item: str) -> None:
        for index in self._hashes(item):
            self.bits |= 1 << index
        self.inserted_count += 1

    def extend(self, items: Iterable[str]) -> int:
        count = 0
        for item in items:
            normalized = item.strip()
            if not normalized:
                continue
            self.add(normalized)
            count += 1
        return count

    def might_contain(self, item: str) -> bool:
        return all((self.bits >> index) & 1 for index in self._hashes(item))

    def estimated_false_positive_rate(self) -> float:
        if self.inserted_count <= 0:
            return 0.0
        return (1 - math.exp(-(self.hash_count * self.inserted_count) / self.bit_count)) ** self.hash_count

    def stats(self) -> dict:
        set_bits = self.bits.bit_count()
        load_factor = set_bits / self.bit_count
        return {
            "capacity": self.capacity,
            "target_error_rate": self.error_rate,
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
            "set_bits": set_bits,
            "load_factor": load_factor,
            "estimated_false_positive_rate": self.estimated_false_positive_rate(),
        }


def load_filter(path: Path) -> BloomFilter:
    return BloomFilter.from_dict(json.loads(path.read_text()))


def save_filter(path: Path, bloom_filter: BloomFilter) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bloom_filter.to_dict(), indent=2) + "\n")


def read_items(path: Path) -> List[str]:
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def benchmark_filter(capacity: int, error_rate: float, inserted_count: int, probe_count: int, seed: int = 0) -> dict:
    if inserted_count <= 0:
        raise ValueError("inserted_count must be greater than 0")
    if probe_count <= 0:
        raise ValueError("probe_count must be greater than 0")

    rng = random.Random(seed)
    bloom_filter = BloomFilter(capacity=capacity, error_rate=error_rate)
    bloom_filter.extend(
        f"inserted-{seed}-{index}-{rng.getrandbits(64):016x}" for index in range(inserted_count)
    )

    false_positive_count = 0
    for index in range(probe_count):
        probe = f"probe-{seed}-{index}-{rng.getrandbits(64):016x}"
        if bloom_filter.might_contain(probe):
            false_positive_count += 1

    observed_false_positive_rate = false_positive_count / probe_count
    return {
        **bloom_filter.stats(),
        "probe_count": probe_count,
        "seed": seed,
        "false_positive_count": false_positive_count,
        "observed_false_positive_rate": observed_false_positive_rate,
    }


def build_command(args: argparse.Namespace) -> int:
    bloom_filter = BloomFilter(capacity=args.capacity, error_rate=args.error_rate)
    inserted = bloom_filter.extend(read_items(Path(args.input)))
    save_filter(Path(args.output), bloom_filter)
    print(json.dumps({"written_to": args.output, "inserted": inserted, **bloom_filter.stats()}, indent=2))
    return 0


def check_command(args: argparse.Namespace) -> int:
    bloom_filter = load_filter(Path(args.filter))
    normalized_items = [item.strip() for item in args.items if item.strip()]
    results = [{"item": item, "might_contain": bloom_filter.might_contain(item)} for item in normalized_items]
    print(json.dumps(results, indent=2))
    return 0


def stats_command(args: argparse.Namespace) -> int:
    bloom_filter = load_filter(Path(args.filter))
    print(json.dumps(bloom_filter.stats(), indent=2))
    return 0


def benchmark_command(args: argparse.Namespace) -> int:
    result = benchmark_filter(
        capacity=args.capacity,
        error_rate=args.error_rate,
        inserted_count=args.inserted_count,
        probe_count=args.probe_count,
        seed=args.seed,
    )
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and query a Bloom filter from the command line")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a filter from a newline-delimited file")
    build_parser.add_argument("--input", required=True, help="path to newline-delimited items")
    build_parser.add_argument("--output", required=True, help="path to write filter JSON")
    build_parser.add_argument("--capacity", type=int, required=True, help="expected number of inserted items")
    build_parser.add_argument("--error-rate", type=float, default=0.01, help="target false-positive rate")
    build_parser.set_defaults(func=build_command)

    check_parser = subparsers.add_parser("check", help="query one or more items against a saved filter")
    check_parser.add_argument("--filter", required=True, help="saved filter JSON")
    check_parser.add_argument("items", nargs="+", help="items to check")
    check_parser.set_defaults(func=check_command)

    stats_parser = subparsers.add_parser("stats", help="show filter statistics")
    stats_parser.add_argument("--filter", required=True, help="saved filter JSON")
    stats_parser.set_defaults(func=stats_command)

    benchmark_parser = subparsers.add_parser("benchmark", help="estimate and sample false-positive behavior")
    benchmark_parser.add_argument("--capacity", type=int, required=True, help="filter capacity used for sizing")
    benchmark_parser.add_argument("--error-rate", type=float, default=0.01, help="target false-positive rate")
    benchmark_parser.add_argument("--inserted-count", type=int, required=True, help="number of generated items to insert")
    benchmark_parser.add_argument("--probe-count", type=int, required=True, help="number of generated probe items to test")
    benchmark_parser.add_argument("--seed", type=int, default=0, help="deterministic RNG seed for reproducible benchmark output")
    benchmark_parser.set_defaults(func=benchmark_command)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
