import argparse
import hashlib
import json
import math
import random
import struct
from pathlib import Path
from typing import Iterable, List

MAGIC = b"BLMF"
VERSION = 1
VARIANT_STANDARD = 1
VARIANT_COUNTING = 2


class BloomFilter:
    variant = "standard"

    def __init__(
        self,
        capacity: int,
        error_rate: float,
        bit_count: int | None = None,
        hash_count: int | None = None,
        inserted_count: int = 0,
        bits: int = 0,
    ):
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
        variant = data.get("variant", "standard")
        if variant == "counting":
            return CountingBloomFilter.from_dict(data)
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
            "variant": self.variant,
            "capacity": self.capacity,
            "error_rate": self.error_rate,
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
            "bits": format(self.bits, "x"),
        }

    def binary_metadata(self) -> dict:
        return {
            "variant": self.variant,
            "capacity": self.capacity,
            "error_rate": self.error_rate,
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
        }

    def to_binary_payload(self) -> bytes:
        byte_count = (self.bit_count + 7) // 8
        return self.bits.to_bytes(byte_count, "big") if byte_count else b""

    @classmethod
    def from_binary_parts(cls, metadata: dict, payload: bytes) -> "BloomFilter":
        variant = metadata.get("variant", "standard")
        if variant == "counting":
            return CountingBloomFilter.from_binary_parts(metadata, payload)
        bit_count = metadata["bit_count"]
        expected_bytes = (bit_count + 7) // 8
        if len(payload) != expected_bytes:
            raise ValueError("binary payload length does not match bit_count")
        return cls(
            capacity=metadata["capacity"],
            error_rate=metadata["error_rate"],
            bit_count=bit_count,
            hash_count=metadata["hash_count"],
            inserted_count=metadata.get("inserted_count", 0),
            bits=int.from_bytes(payload, "big") if payload else 0,
        )

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
            "variant": self.variant,
            "capacity": self.capacity,
            "target_error_rate": self.error_rate,
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
            "set_bits": set_bits,
            "load_factor": load_factor,
            "estimated_false_positive_rate": self.estimated_false_positive_rate(),
        }


class CountingBloomFilter(BloomFilter):
    variant = "counting"

    def __init__(
        self,
        capacity: int,
        error_rate: float,
        bit_count: int | None = None,
        hash_count: int | None = None,
        inserted_count: int = 0,
        counters: Iterable[int] | None = None,
        counter_bits: int = 8,
        max_counter_value: int | None = None,
    ):
        super().__init__(
            capacity=capacity,
            error_rate=error_rate,
            bit_count=bit_count,
            hash_count=hash_count,
            inserted_count=inserted_count,
            bits=0,
        )
        if counter_bits <= 0:
            raise ValueError("counter_bits must be greater than 0")
        self.counter_bits = counter_bits
        self.max_counter_value = max_counter_value if max_counter_value is not None else (2**counter_bits - 1)
        if self.max_counter_value <= 0:
            raise ValueError("max_counter_value must be greater than 0")

        raw_counters = list(counters) if counters is not None else [0] * self.bit_count
        if len(raw_counters) != self.bit_count:
            raise ValueError("counter length must match bit_count")
        if any(counter < 0 or counter > self.max_counter_value for counter in raw_counters):
            raise ValueError("counter values must stay within the configured range")
        self.counters = raw_counters

    @classmethod
    def from_dict(cls, data: dict) -> "CountingBloomFilter":
        return cls(
            capacity=data["capacity"],
            error_rate=data["error_rate"],
            bit_count=data["bit_count"],
            hash_count=data["hash_count"],
            inserted_count=data.get("inserted_count", 0),
            counters=data.get("counters", []),
            counter_bits=data.get("counter_bits", 8),
            max_counter_value=data.get("max_counter_value"),
        )

    def to_dict(self) -> dict:
        return {
            "variant": self.variant,
            "capacity": self.capacity,
            "error_rate": self.error_rate,
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
            "counter_bits": self.counter_bits,
            "max_counter_value": self.max_counter_value,
            "counters": self.counters,
        }

    def binary_metadata(self) -> dict:
        return {
            **super().binary_metadata(),
            "counter_bits": self.counter_bits,
            "max_counter_value": self.max_counter_value,
        }

    def to_binary_payload(self) -> bytes:
        counter_bytes = math.ceil(self.counter_bits / 8)
        blob = bytearray()
        for counter in self.counters:
            blob.extend(counter.to_bytes(counter_bytes, "big"))
        return bytes(blob)

    @classmethod
    def from_binary_parts(cls, metadata: dict, payload: bytes) -> "CountingBloomFilter":
        counter_bits = metadata.get("counter_bits", 8)
        counter_bytes = math.ceil(counter_bits / 8)
        bit_count = metadata["bit_count"]
        expected_bytes = bit_count * counter_bytes
        if len(payload) != expected_bytes:
            raise ValueError("binary payload length does not match counting filter shape")
        counters = [
            int.from_bytes(payload[index : index + counter_bytes], "big")
            for index in range(0, len(payload), counter_bytes)
        ]
        return cls(
            capacity=metadata["capacity"],
            error_rate=metadata["error_rate"],
            bit_count=bit_count,
            hash_count=metadata["hash_count"],
            inserted_count=metadata.get("inserted_count", 0),
            counters=counters,
            counter_bits=counter_bits,
            max_counter_value=metadata.get("max_counter_value"),
        )

    def add(self, item: str) -> None:
        for index in self._hashes(item):
            if self.counters[index] >= self.max_counter_value:
                raise OverflowError(
                    f"counter overflow at index {index}; choose a larger counter size or rebuild with a higher capacity"
                )
            self.counters[index] += 1
        self.inserted_count += 1

    def remove(self, item: str) -> bool:
        indexes = self._hashes(item)
        if any(self.counters[index] == 0 for index in indexes):
            return False
        for index in indexes:
            self.counters[index] -= 1
        self.inserted_count = max(0, self.inserted_count - 1)
        return True

    def might_contain(self, item: str) -> bool:
        return all(self.counters[index] > 0 for index in self._hashes(item))

    def stats(self) -> dict:
        non_zero_counters = sum(1 for counter in self.counters if counter > 0)
        max_counter = max(self.counters, default=0)
        return {
            "variant": self.variant,
            "capacity": self.capacity,
            "target_error_rate": self.error_rate,
            "bit_count": self.bit_count,
            "hash_count": self.hash_count,
            "inserted_count": self.inserted_count,
            "non_zero_counters": non_zero_counters,
            "load_factor": non_zero_counters / self.bit_count,
            "max_counter": max_counter,
            "counter_bits": self.counter_bits,
            "max_counter_value": self.max_counter_value,
            "estimated_false_positive_rate": self.estimated_false_positive_rate(),
        }


def load_filter(path: Path) -> BloomFilter:
    raw = path.read_bytes()
    if raw.startswith(MAGIC):
        return load_filter_binary(path)
    return BloomFilter.from_dict(json.loads(raw.decode("utf-8")))


def save_filter(path: Path, bloom_filter: BloomFilter) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bloom_filter.to_dict(), indent=2) + "\n")


def save_filter_binary(path: Path, bloom_filter: BloomFilter) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = bloom_filter.binary_metadata()
    metadata_bytes = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    payload = bloom_filter.to_binary_payload()
    variant_code = VARIANT_STANDARD if bloom_filter.variant == "standard" else VARIANT_COUNTING
    header = MAGIC + struct.pack(">BBII", VERSION, variant_code, len(metadata_bytes), len(payload)
    )
    path.write_bytes(header + metadata_bytes + payload)


def load_filter_binary(path: Path) -> BloomFilter:
    raw = path.read_bytes()
    minimum_header = 4 + 1 + 1 + 4 + 4
    if len(raw) < minimum_header:
        raise ValueError("binary filter file is too short")
    magic = raw[:4]
    if magic != MAGIC:
        raise ValueError("binary filter file has an invalid magic header")
    version, variant_code, metadata_length, payload_length = struct.unpack(">BBII", raw[4:14])
    if version != VERSION:
        raise ValueError(f"unsupported binary filter version: {version}")
    metadata_start = 14
    metadata_end = metadata_start + metadata_length
    payload_end = metadata_end + payload_length
    if payload_end != len(raw):
        raise ValueError("binary filter file length does not match header")
    metadata = json.loads(raw[metadata_start:metadata_end].decode("utf-8"))
    payload = raw[metadata_end:payload_end]
    if variant_code == VARIANT_STANDARD:
        metadata.setdefault("variant", "standard")
    elif variant_code == VARIANT_COUNTING:
        metadata.setdefault("variant", "counting")
    else:
        raise ValueError(f"unsupported binary filter variant code: {variant_code}")
    return BloomFilter.from_binary_parts(metadata, payload)


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


def compare_artifact_sizes(capacity: int, error_rate: float, inserted_count: int, counter_bits: int = 8) -> dict:
    standard = BloomFilter(capacity=capacity, error_rate=error_rate)
    counting = CountingBloomFilter(capacity=capacity, error_rate=error_rate, counter_bits=counter_bits)
    items = [f"item-{index}" for index in range(inserted_count)]
    standard.extend(items)
    counting.extend(items)

    standard_json = (json.dumps(standard.to_dict(), indent=2) + "\n").encode("utf-8")
    counting_json = (json.dumps(counting.to_dict(), indent=2) + "\n").encode("utf-8")
    standard_binary_meta = json.dumps(standard.binary_metadata(), separators=(",", ":")).encode("utf-8")
    counting_binary_meta = json.dumps(counting.binary_metadata(), separators=(",", ":")).encode("utf-8")
    standard_binary = 14 + len(standard_binary_meta) + len(standard.to_binary_payload())
    counting_binary = 14 + len(counting_binary_meta) + len(counting.to_binary_payload())

    return {
        "capacity": capacity,
        "error_rate": error_rate,
        "inserted_count": inserted_count,
        "standard": {
            "bit_count": standard.bit_count,
            "hash_count": standard.hash_count,
            "json_bytes": len(standard_json),
            "binary_bytes": standard_binary,
            "bytes_per_inserted_item_binary": standard_binary / inserted_count,
        },
        "counting": {
            "bit_count": counting.bit_count,
            "hash_count": counting.hash_count,
            "counter_bits": counter_bits,
            "json_bytes": len(counting_json),
            "binary_bytes": counting_binary,
            "bytes_per_inserted_item_binary": counting_binary / inserted_count,
        },
        "binary_overhead_ratio_counting_vs_standard": counting_binary / standard_binary,
    }


def build_command(args: argparse.Namespace) -> int:
    bloom_filter = BloomFilter(capacity=args.capacity, error_rate=args.error_rate)
    inserted = bloom_filter.extend(read_items(Path(args.input)))
    save_filter(Path(args.output), bloom_filter)
    print(json.dumps({"written_to": args.output, "inserted": inserted, **bloom_filter.stats()}, indent=2))
    return 0


def build_counting_command(args: argparse.Namespace) -> int:
    bloom_filter = CountingBloomFilter(
        capacity=args.capacity,
        error_rate=args.error_rate,
        counter_bits=args.counter_bits,
    )
    inserted = bloom_filter.extend(read_items(Path(args.input)))
    save_filter(Path(args.output), bloom_filter)
    print(json.dumps({"written_to": args.output, "inserted": inserted, **bloom_filter.stats()}, indent=2))
    return 0


def export_binary_command(args: argparse.Namespace) -> int:
    bloom_filter = load_filter(Path(args.filter))
    save_filter_binary(Path(args.output), bloom_filter)
    output_path = Path(args.output)
    print(
        json.dumps(
            {
                "source": args.filter,
                "written_to": args.output,
                "variant": bloom_filter.variant,
                "binary_bytes": output_path.stat().st_size,
                **bloom_filter.stats(),
            },
            indent=2,
        )
    )
    return 0


def inspect_binary_command(args: argparse.Namespace) -> int:
    bloom_filter = load_filter_binary(Path(args.filter))
    print(json.dumps({"filter": args.filter, **bloom_filter.stats()}, indent=2))
    return 0


def compare_sizes_command(args: argparse.Namespace) -> int:
    result = compare_artifact_sizes(
        capacity=args.capacity,
        error_rate=args.error_rate,
        inserted_count=args.inserted_count,
        counter_bits=args.counter_bits,
    )
    print(json.dumps(result, indent=2))
    return 0


def check_command(args: argparse.Namespace) -> int:
    bloom_filter = load_filter(Path(args.filter))
    normalized_items = [item.strip() for item in args.items if item.strip()]
    results = [{"item": item, "might_contain": bloom_filter.might_contain(item)} for item in normalized_items]
    print(json.dumps(results, indent=2))
    return 0


def remove_command(args: argparse.Namespace) -> int:
    bloom_filter = load_filter(Path(args.filter))
    if not isinstance(bloom_filter, CountingBloomFilter):
        raise ValueError("remove requires a counting Bloom filter artifact")

    normalized_items = [item.strip() for item in args.items if item.strip()]
    results = []
    for item in normalized_items:
        removed = bloom_filter.remove(item)
        results.append({"item": item, "removed": removed, "might_contain_after": bloom_filter.might_contain(item)})
    if Path(args.filter).suffix == ".bf":
        save_filter_binary(Path(args.filter), bloom_filter)
    else:
        save_filter(Path(args.filter), bloom_filter)
    print(json.dumps({"updated_filter": args.filter, "results": results, **bloom_filter.stats()}, indent=2))
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

    build_parser = subparsers.add_parser("build", help="build a standard filter from a newline-delimited file")
    build_parser.add_argument("--input", required=True, help="path to newline-delimited items")
    build_parser.add_argument("--output", required=True, help="path to write filter JSON")
    build_parser.add_argument("--capacity", type=int, required=True, help="expected number of inserted items")
    build_parser.add_argument("--error-rate", type=float, default=0.01, help="target false-positive rate")
    build_parser.set_defaults(func=build_command)

    build_counting_parser = subparsers.add_parser("build-counting", help="build a counting Bloom filter with delete support")
    build_counting_parser.add_argument("--input", required=True, help="path to newline-delimited items")
    build_counting_parser.add_argument("--output", required=True, help="path to write filter JSON")
    build_counting_parser.add_argument("--capacity", type=int, required=True, help="expected number of inserted items")
    build_counting_parser.add_argument("--error-rate", type=float, default=0.01, help="target false-positive rate")
    build_counting_parser.add_argument("--counter-bits", type=int, default=8, help="bits allocated per counter before overflow")
    build_counting_parser.set_defaults(func=build_counting_command)

    export_binary_parser = subparsers.add_parser("export-binary", help="convert a JSON filter artifact into a compact binary artifact")
    export_binary_parser.add_argument("--filter", required=True, help="saved filter JSON")
    export_binary_parser.add_argument("--output", required=True, help="path to write binary artifact, for example filter.bf")
    export_binary_parser.set_defaults(func=export_binary_command)

    inspect_binary_parser = subparsers.add_parser("inspect-binary", help="inspect a binary filter artifact")
    inspect_binary_parser.add_argument("--filter", required=True, help="saved binary filter artifact")
    inspect_binary_parser.set_defaults(func=inspect_binary_command)

    compare_sizes_parser = subparsers.add_parser("compare-sizes", help="compare JSON and binary artifact sizes for standard vs counting filters")
    compare_sizes_parser.add_argument("--capacity", type=int, required=True, help="filter capacity used for sizing")
    compare_sizes_parser.add_argument("--error-rate", type=float, default=0.01, help="target false-positive rate")
    compare_sizes_parser.add_argument("--inserted-count", type=int, required=True, help="number of generated items to insert into both variants")
    compare_sizes_parser.add_argument("--counter-bits", type=int, default=8, help="counter width for the counting variant")
    compare_sizes_parser.set_defaults(func=compare_sizes_command)

    check_parser = subparsers.add_parser("check", help="query one or more items against a saved filter")
    check_parser.add_argument("--filter", required=True, help="saved filter JSON or binary artifact")
    check_parser.add_argument("items", nargs="+", help="items to check")
    check_parser.set_defaults(func=check_command)

    remove_parser = subparsers.add_parser("remove", help="remove one or more items from a counting Bloom filter")
    remove_parser.add_argument("--filter", required=True, help="saved counting filter JSON or binary artifact")
    remove_parser.add_argument("items", nargs="+", help="items to remove")
    remove_parser.set_defaults(func=remove_command)

    stats_parser = subparsers.add_parser("stats", help="show filter statistics")
    stats_parser.add_argument("--filter", required=True, help="saved filter JSON or binary artifact")
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
    try:
        return args.func(args)
    except (ValueError, OverflowError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
