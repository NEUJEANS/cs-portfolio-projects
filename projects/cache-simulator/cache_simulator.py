import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

SUPPORTED_WRITE_POLICIES = {"write-back", "write-through"}
SUPPORTED_REPLACEMENT_POLICIES = {"lru"}


@dataclass(frozen=True)
class CacheConfig:
    cache_size: int
    block_size: int
    associativity: int
    write_policy: str = "write-back"
    replacement_policy: str = "lru"

    def __post_init__(self) -> None:
        if self.cache_size <= 0:
            raise ValueError("cache_size must be > 0")
        if self.block_size <= 0:
            raise ValueError("block_size must be > 0")
        if self.associativity <= 0:
            raise ValueError("associativity must be > 0")
        if self.cache_size % (self.block_size * self.associativity) != 0:
            raise ValueError("cache_size must be divisible by block_size * associativity")
        if self.write_policy not in SUPPORTED_WRITE_POLICIES:
            raise ValueError(f"unsupported write_policy: {self.write_policy}")
        if self.replacement_policy not in SUPPORTED_REPLACEMENT_POLICIES:
            raise ValueError(f"unsupported replacement_policy: {self.replacement_policy}")

    @property
    def set_count(self) -> int:
        return self.cache_size // (self.block_size * self.associativity)


@dataclass(frozen=True)
class TraceOperation:
    op: str
    address: int
    size: int = 1
    value: Optional[int] = None

    def __post_init__(self) -> None:
        if self.op not in {"read", "write"}:
            raise ValueError(f"unsupported op: {self.op}")
        if self.address < 0:
            raise ValueError("address must be >= 0")
        if self.size <= 0:
            raise ValueError("size must be > 0")


@dataclass
class CacheLine:
    tag: int
    dirty: bool = False
    last_used: int = 0


class CacheSimulator:
    def __init__(self, config: CacheConfig):
        self.config = config
        self.sets: List[List[CacheLine]] = [[] for _ in range(config.set_count)]
        self.access_counter = 0
        self.stats: Dict[str, int] = {
            "reads": 0,
            "writes": 0,
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "dirty_evictions": 0,
            "memory_reads": 0,
            "memory_writes": 0,
        }

    def decode_address(self, address: int) -> Dict[str, int]:
        block_address = address // self.config.block_size
        return {
            "block_address": block_address,
            "set_index": block_address % self.config.set_count,
            "tag": block_address // self.config.set_count,
            "offset": address % self.config.block_size,
        }

    def _find_line(self, set_index: int, tag: int) -> Optional[CacheLine]:
        for line in self.sets[set_index]:
            if line.tag == tag:
                return line
        return None

    def _touch(self, line: CacheLine) -> None:
        self.access_counter += 1
        line.last_used = self.access_counter

    def _evict_if_needed(self, set_index: int) -> None:
        lines = self.sets[set_index]
        if len(lines) < self.config.associativity:
            return
        victim = min(lines, key=lambda line: line.last_used)
        lines.remove(victim)
        self.stats["evictions"] += 1
        if victim.dirty:
            self.stats["dirty_evictions"] += 1
            self.stats["memory_writes"] += 1

    def access(self, operation: TraceOperation) -> Dict[str, int | bool | str]:
        decoded = self.decode_address(operation.address)
        if decoded["offset"] + operation.size > self.config.block_size:
            raise ValueError("access spans multiple cache blocks; split it into block-sized operations")
        set_index = decoded["set_index"]
        tag = decoded["tag"]
        op_key = "reads" if operation.op == "read" else "writes"
        self.stats[op_key] += 1

        line = self._find_line(set_index, tag)
        hit = line is not None
        self.stats["hits" if hit else "misses"] += 1

        if not hit:
            self.stats["memory_reads"] += 1
            self._evict_if_needed(set_index)
            line = CacheLine(tag=tag)
            self.sets[set_index].append(line)

        self._touch(line)

        if operation.op == "write":
            if self.config.write_policy == "write-through":
                self.stats["memory_writes"] += 1
                line.dirty = False
            else:
                line.dirty = True

        return {
            "op": operation.op,
            "address": operation.address,
            "set_index": set_index,
            "tag": tag,
            "hit": hit,
            "dirty": line.dirty,
        }

    def flush(self) -> None:
        if self.config.write_policy != "write-back":
            return
        for lines in self.sets:
            for line in lines:
                if line.dirty:
                    self.stats["memory_writes"] += 1
                    line.dirty = False

    def snapshot(self) -> List[List[Dict[str, int | bool]]]:
        return [
            [
                {"tag": line.tag, "dirty": line.dirty, "last_used": line.last_used}
                for line in sorted(lines, key=lambda item: item.last_used, reverse=True)
            ]
            for lines in self.sets
        ]


def load_trace(path: Path) -> List[TraceOperation]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("trace JSON must be a list")
    return [
        TraceOperation(
            op=item["op"],
            address=int(item["address"]),
            size=int(item.get("size", 1)),
            value=item.get("value"),
        )
        for item in raw
    ]


def simulate_trace(trace: Iterable[TraceOperation], config: CacheConfig) -> Dict:
    simulator = CacheSimulator(config)
    accesses = [simulator.access(operation) for operation in trace]
    simulator.flush()
    total = simulator.stats["reads"] + simulator.stats["writes"]
    hit_rate = round((simulator.stats["hits"] / total) * 100, 2) if total else 0.0
    miss_rate = round((simulator.stats["misses"] / total) * 100, 2) if total else 0.0
    return {
        "config": {
            "cache_size": config.cache_size,
            "block_size": config.block_size,
            "associativity": config.associativity,
            "set_count": config.set_count,
            "write_policy": config.write_policy,
            "replacement_policy": config.replacement_policy,
        },
        "stats": {**simulator.stats, "hit_rate": hit_rate, "miss_rate": miss_rate},
        "accesses": accesses,
        "final_sets": simulator.snapshot(),
    }


def format_summary(result: Dict) -> str:
    config = result["config"]
    stats = result["stats"]
    return (
        "Cache Simulator Summary\n"
        f"Cache size: {config['cache_size']} bytes\n"
        f"Block size: {config['block_size']} bytes\n"
        f"Associativity: {config['associativity']}-way\n"
        f"Set count: {config['set_count']}\n"
        f"Write policy: {config['write_policy']}\n"
        f"Replacement policy: {config['replacement_policy']}\n"
        f"Reads/Writes: {stats['reads']}/{stats['writes']}\n"
        f"Hits/Misses: {stats['hits']}/{stats['misses']}\n"
        f"Hit rate: {stats['hit_rate']}%\n"
        f"Miss rate: {stats['miss_rate']}%\n"
        f"Evictions: {stats['evictions']} (dirty: {stats['dirty_evictions']})\n"
        f"Memory reads: {stats['memory_reads']}\n"
        f"Memory writes: {stats['memory_writes']}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate a set-associative cache with LRU replacement")
    parser.add_argument("trace", type=Path, help="path to a JSON trace file")
    parser.add_argument("--cache-size", type=int, required=True, help="total cache size in bytes")
    parser.add_argument("--block-size", type=int, required=True, help="cache block size in bytes")
    parser.add_argument("--associativity", type=int, required=True, help="number of ways per set")
    parser.add_argument(
        "--write-policy",
        choices=sorted(SUPPORTED_WRITE_POLICIES),
        default="write-back",
        help="how writes propagate to memory",
    )
    parser.add_argument("--json", action="store_true", help="print JSON output")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = CacheConfig(
        cache_size=args.cache_size,
        block_size=args.block_size,
        associativity=args.associativity,
        write_policy=args.write_policy,
    )
    trace = load_trace(args.trace)
    result = simulate_trace(trace, config)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
