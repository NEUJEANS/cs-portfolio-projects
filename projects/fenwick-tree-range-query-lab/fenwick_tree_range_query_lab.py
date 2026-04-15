import argparse
import json
from dataclasses import dataclass
from pathlib import Path


class FenwickTree:
    def __init__(self, size: int):
        if size < 1:
            raise ValueError("size must be positive")
        self.size = size
        self.tree = [0] * (size + 1)

    def add(self, index: int, delta: int) -> None:
        if not 1 <= index <= self.size:
            raise IndexError("index out of bounds")
        while index <= self.size:
            self.tree[index] += delta
            index += index & -index

    def prefix_sum(self, index: int) -> int:
        if index < 0:
            return 0
        if index > self.size:
            index = self.size
        result = 0
        while index > 0:
            result += self.tree[index]
            index -= index & -index
        return result

    @classmethod
    def from_values(cls, values: list[int]) -> "FenwickTree":
        fenwick = cls(len(values))
        for offset, value in enumerate(values, start=1):
            fenwick.add(offset, value)
        return fenwick


@dataclass
class RangeFenwick:
    values: list[int]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("values must not be empty")
        original_values = list(self.values)
        self.values = list(self.values)
        self._tree_a = FenwickTree(len(self.values))
        self._tree_b = FenwickTree(len(self.values))
        for index, value in enumerate(original_values, start=1):
            self._range_add_internal(index, index, value)

    @property
    def size(self) -> int:
        return len(self.values)

    def _apply_internal(self, index: int, delta: int) -> None:
        if index <= 0:
            return
        if index > self.size + 1:
            return
        if index <= self.size:
            self._tree_a.add(index, delta)
            self._tree_b.add(index, delta * (index - 1))

    def _prefix_sum(self, index: int) -> int:
        return self._tree_a.prefix_sum(index) * index - self._tree_b.prefix_sum(index)

    def point_query(self, index: int) -> int:
        return self.range_sum(index, index)

    def point_add(self, index: int, delta: int) -> None:
        self.range_add(index, index, delta)

    def point_set(self, index: int, value: int) -> None:
        self._validate_index(index)
        self.point_add(index, value - self.values[index - 1])

    def _range_add_internal(self, left: int, right: int, delta: int) -> None:
        self._apply_internal(left, delta)
        self._apply_internal(right + 1, -delta)

    def range_add(self, left: int, right: int, delta: int) -> None:
        self._validate_range(left, right)
        self._range_add_internal(left, right, delta)
        for index in range(left - 1, right):
            self.values[index] += delta

    def prefix_sum(self, index: int) -> int:
        if index < 0:
            return 0
        if index == 0:
            return 0
        if index > self.size:
            index = self.size
        return self._prefix_sum(index)

    def range_sum(self, left: int, right: int) -> int:
        self._validate_range(left, right)
        return self._prefix_sum(right) - self._prefix_sum(left - 1)

    def stats(self) -> dict:
        total = self.range_sum(1, self.size)
        return {
            "size": self.size,
            "total": total,
            "min": min(self.values),
            "max": max(self.values),
            "values": self.values,
        }

    def to_dict(self) -> dict:
        return {"values": self.values}

    @classmethod
    def from_dict(cls, data: dict) -> "RangeFenwick":
        values = data.get("values")
        if not isinstance(values, list) or not values:
            raise ValueError("snapshot must include a non-empty values list")
        if not all(type(value) is int for value in values):
            raise ValueError("snapshot values must be integers")
        return cls(values=list(values))

    def _validate_index(self, index: int) -> None:
        if not 1 <= index <= self.size:
            raise IndexError("index out of bounds")

    def _validate_range(self, left: int, right: int) -> None:
        if left > right:
            raise ValueError("left must be <= right")
        self._validate_index(left)
        self._validate_index(right)


def load_values(path: Path) -> list[int]:
    values: list[int] = []
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            values.append(int(line))
        except ValueError as exc:
            raise ValueError(f"invalid integer on line {line_number}: {line}") from exc
    if not values:
        raise ValueError("input must contain at least one integer")
    return values


def save_snapshot(path: Path, fenwick: RangeFenwick) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fenwick.to_dict(), indent=2) + "\n")


def load_snapshot(path: Path) -> RangeFenwick:
    return RangeFenwick.from_dict(json.loads(path.read_text()))


def build_command(args: argparse.Namespace) -> int:
    fenwick = RangeFenwick(load_values(Path(args.input)))
    if args.output:
        save_snapshot(Path(args.output), fenwick)
    print(json.dumps({"output": args.output, **fenwick.stats()}, indent=2))
    return 0


def sum_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    print(json.dumps({"left": args.left, "right": args.right, "sum": fenwick.range_sum(args.left, args.right)}, indent=2))
    return 0


def add_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    fenwick.range_add(args.left, args.right, args.delta)
    save_snapshot(Path(args.output), fenwick)
    print(json.dumps({"left": args.left, "right": args.right, "delta": args.delta, "output": args.output, **fenwick.stats()}, indent=2))
    return 0


def set_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    fenwick.point_set(args.index, args.value)
    save_snapshot(Path(args.output), fenwick)
    print(json.dumps({"index": args.index, "value": args.value, "output": args.output, **fenwick.stats()}, indent=2))
    return 0


def export_command(args: argparse.Namespace) -> int:
    fenwick = load_snapshot(Path(args.snapshot))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["index,value,prefix_sum"]
    for index, value in enumerate(fenwick.values, start=1):
        lines.append(f"{index},{value},{fenwick.prefix_sum(index)}")
    output.write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": args.output, "rows": fenwick.size}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fenwick tree range query lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="build a snapshot from newline-delimited integers")
    build_parser.add_argument("--input", required=True)
    build_parser.add_argument("--output")
    build_parser.set_defaults(func=build_command)

    sum_parser = subparsers.add_parser("sum", help="query an inclusive range sum")
    sum_parser.add_argument("--snapshot", required=True)
    sum_parser.add_argument("left", type=int)
    sum_parser.add_argument("right", type=int)
    sum_parser.set_defaults(func=sum_command)

    add_parser = subparsers.add_parser("add", help="add a delta to an inclusive range")
    add_parser.add_argument("--snapshot", required=True)
    add_parser.add_argument("--output", required=True)
    add_parser.add_argument("left", type=int)
    add_parser.add_argument("right", type=int)
    add_parser.add_argument("delta", type=int)
    add_parser.set_defaults(func=add_command)

    set_parser = subparsers.add_parser("set", help="set a single index to a new value")
    set_parser.add_argument("--snapshot", required=True)
    set_parser.add_argument("--output", required=True)
    set_parser.add_argument("index", type=int)
    set_parser.add_argument("value", type=int)
    set_parser.set_defaults(func=set_command)

    export_parser = subparsers.add_parser("export", help="export current values and prefix sums")
    export_parser.add_argument("--snapshot", required=True)
    export_parser.add_argument("--output", required=True)
    export_parser.set_defaults(func=export_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
