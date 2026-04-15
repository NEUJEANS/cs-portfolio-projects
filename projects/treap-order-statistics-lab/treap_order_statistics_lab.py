from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import random
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class Node:
    key: int
    priority: int
    left: Optional["Node"] = None
    right: Optional["Node"] = None
    size: int = 1


@dataclass
class Treap:
    seed: int = 0
    trace: bool = False
    root: Optional[Node] = None
    events: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def _log(self, message: str) -> None:
        if self.trace:
            self.events.append(message)

    def _size(self, node: Optional[Node]) -> int:
        return node.size if node is not None else 0

    def _update(self, node: Optional[Node]) -> None:
        if node is not None:
            node.size = 1 + self._size(node.left) + self._size(node.right)

    def height(self) -> int:
        return self._height(self.root)

    def _height(self, node: Optional[Node]) -> int:
        if node is None:
            return 0
        return 1 + max(self._height(node.left), self._height(node.right))

    def contains(self, key: int) -> bool:
        node = self.root
        while node is not None:
            if key == node.key:
                return True
            node = node.left if key < node.key else node.right
        return False

    def contains_with_stats(self, key: int) -> dict[str, int | bool]:
        node = self.root
        comparisons = 0
        while node is not None:
            comparisons += 1
            if key == node.key:
                return {"found": True, "comparisons": comparisons}
            node = node.left if key < node.key else node.right
        return {"found": False, "comparisons": comparisons}

    def _split(self, node: Optional[Node], key: int) -> tuple[Optional[Node], Optional[Node]]:
        if node is None:
            return None, None
        if key < node.key:
            left, node.left = self._split(node.left, key)
            self._update(node)
            return left, node
        node.right, right = self._split(node.right, key)
        self._update(node)
        return node, right

    def _merge(self, left: Optional[Node], right: Optional[Node]) -> Optional[Node]:
        if left is None:
            return right
        if right is None:
            return left
        if left.priority > right.priority:
            left.right = self._merge(left.right, right)
            self._update(left)
            return left
        right.left = self._merge(left, right.left)
        self._update(right)
        return right

    def insert(self, key: int) -> int:
        if self.contains(key):
            raise ValueError(f"duplicate key: {key}")
        priority = self._random.randint(1, 1_000_000_000)
        self._log(f"insert key={key} priority={priority}")
        self.root = self._insert(self.root, Node(key=key, priority=priority))
        return priority

    def _insert(self, node: Optional[Node], fresh: Node) -> Node:
        if node is None:
            return fresh
        if fresh.priority > node.priority:
            left, right = self._split(node, fresh.key)
            fresh.left = left
            fresh.right = right
            self._update(fresh)
            return fresh
        if fresh.key < node.key:
            node.left = self._insert(node.left, fresh)
        else:
            node.right = self._insert(node.right, fresh)
        self._update(node)
        return node

    def delete(self, key: int) -> None:
        self.root = self._delete(self.root, key)

    def _delete(self, node: Optional[Node], key: int) -> Optional[Node]:
        if node is None:
            raise KeyError(key)
        if key == node.key:
            self._log(f"delete key={key}")
            return self._merge(node.left, node.right)
        if key < node.key:
            node.left = self._delete(node.left, key)
        else:
            node.right = self._delete(node.right, key)
        self._update(node)
        return node

    def rank(self, key: int) -> int:
        node = self.root
        count = 0
        while node is not None:
            if key <= node.key:
                node = node.left
            else:
                count += 1 + self._size(node.left)
                node = node.right
        return count

    def select(self, index: int) -> int:
        if index < 0 or index >= self._size(self.root):
            raise IndexError(index)
        node = self.root
        remaining = index
        while node is not None:
            left_size = self._size(node.left)
            if remaining < left_size:
                node = node.left
            elif remaining == left_size:
                return node.key
            else:
                remaining -= left_size + 1
                node = node.right
        raise IndexError(index)

    def range_count(self, lower: int, upper: int) -> int:
        if lower > upper:
            raise ValueError("lower must be <= upper")
        return self.rank(upper + 1) - self.rank(lower)

    def inorder(self) -> List[int]:
        return self._inorder(self.root)

    def _inorder(self, node: Optional[Node]) -> List[int]:
        if node is None:
            return []
        return self._inorder(node.left) + [node.key] + self._inorder(node.right)

    def preorder(self) -> List[int]:
        return self._preorder(self.root)

    def _preorder(self, node: Optional[Node]) -> List[int]:
        if node is None:
            return []
        return [node.key] + self._preorder(node.left) + self._preorder(node.right)

    def validate(self) -> dict:
        result = self._validate(self.root, lower=None, upper=None)
        return {
            "is_valid": not result["issues"],
            "size": result["size"],
            "height": result["height"],
            "inorder": self.inorder(),
            "issues": result["issues"],
        }

    def _validate(self, node: Optional[Node], lower: Optional[int], upper: Optional[int]) -> dict:
        if node is None:
            return {"issues": [], "size": 0, "height": 0, "max_priority": None}
        issues: List[str] = []
        if lower is not None and node.key <= lower:
            issues.append(f"bst lower bound violated at {node.key}")
        if upper is not None and node.key >= upper:
            issues.append(f"bst upper bound violated at {node.key}")
        left = self._validate(node.left, lower, node.key)
        right = self._validate(node.right, node.key, upper)
        if left["max_priority"] is not None and left["max_priority"] > node.priority:
            issues.append(f"heap priority violated at {node.key} via left child")
        if right["max_priority"] is not None and right["max_priority"] > node.priority:
            issues.append(f"heap priority violated at {node.key} via right child")
        expected_size = 1 + left["size"] + right["size"]
        if node.size != expected_size:
            issues.append(
                f"size mismatch at {node.key}: stored={node.size}, expected={expected_size}"
            )
        issues.extend(left["issues"])
        issues.extend(right["issues"])
        return {
            "issues": issues,
            "size": expected_size,
            "height": 1 + max(left["height"], right["height"]),
            "max_priority": max(
                value
                for value in [node.priority, left["max_priority"], right["max_priority"]]
                if value is not None
            ),
        }


def build_treap(keys: Iterable[int], seed: int = 0, trace: bool = False) -> Treap:
    treap = Treap(seed=seed, trace=trace)
    for key in keys:
        treap.insert(key)
    return treap


def load_keys(path: Path) -> List[int]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list) or not all(isinstance(item, int) for item in payload):
        raise ValueError("sample file must be a JSON array of integers")
    return payload


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


_AVL_MODULE: object | None = None
_RED_BLACK_MODULE: object | None = None
_SPLAY_MODULE: object | None = None


def _load_module(cache_name: str, module_path: Path, spec_name: str) -> object:
    spec = importlib.util.spec_from_file_location(spec_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    globals()[cache_name] = module
    return module


def _load_avl_module() -> object:
    global _AVL_MODULE
    if _AVL_MODULE is None:
        _AVL_MODULE = _load_module(
            "_AVL_MODULE",
            _project_root() / "projects" / "avl-tree-lab" / "avl_tree_lab.py",
            "avl_tree_lab_for_treap_benchmark",
        )
    return _AVL_MODULE


def _load_red_black_module() -> object:
    global _RED_BLACK_MODULE
    if _RED_BLACK_MODULE is None:
        _RED_BLACK_MODULE = _load_module(
            "_RED_BLACK_MODULE",
            _project_root() / "projects" / "red-black-tree-lab" / "red_black_tree.py",
            "red_black_tree_lab_for_treap_benchmark",
        )
    return _RED_BLACK_MODULE


def _load_splay_module() -> object:
    global _SPLAY_MODULE
    if _SPLAY_MODULE is None:
        _SPLAY_MODULE = _load_module(
            "_SPLAY_MODULE",
            _project_root() / "projects" / "splay-tree-lab" / "splay_tree_lab.py",
            "splay_tree_lab_for_treap_benchmark",
        )
    return _SPLAY_MODULE


def _count_avl_lookup(tree: object, key: int) -> dict[str, int | bool]:
    node = tree.root
    comparisons = 0
    while node is not None:
        comparisons += 1
        if key == node.key:
            return {"found": True, "comparisons": comparisons}
        node = node.left if key < node.key else node.right
    return {"found": False, "comparisons": comparisons}


def _count_red_black_lookup(tree: object, key: int) -> dict[str, int | bool]:
    node = tree.root
    comparisons = 0
    while node is not None:
        comparisons += 1
        if key == node.key:
            return {"found": True, "comparisons": comparisons}
        node = node.left if key < node.key else node.right
    return {"found": False, "comparisons": comparisons}


def _splay_height(node: object | None) -> int:
    if node is None:
        return 0
    return 1 + max(_splay_height(node.left), _splay_height(node.right))


def _benchmark_case(sequence: list[int], queries: list[int], seed: int) -> dict[str, object]:
    treap = build_treap(sequence, seed=seed)
    treap_validation = treap.validate()
    if not treap_validation["is_valid"]:
        raise ValueError(f"treap benchmark built an invalid tree: {treap_validation['issues']}")

    avl_module = _load_avl_module()
    avl_tree = avl_module.build_tree(sequence, trace=True)
    avl_validation = avl_tree.validate()
    if not avl_validation["is_valid"]:
        raise ValueError(f"AVL benchmark built an invalid tree: {avl_validation['issues']}")

    red_black_module = _load_red_black_module()
    rb_tree = red_black_module.build_tree(sequence, trace_enabled=True)
    rb_valid, _, rb_errors = rb_tree.validate()
    if not rb_valid:
        raise ValueError(f"red-black benchmark built an invalid tree: {rb_errors}")

    splay_module = _load_splay_module()
    splay_tree = splay_module.SplayTree(sequence)

    treap_query_stats = [treap.contains_with_stats(query) for query in queries]
    avl_query_stats = [_count_avl_lookup(avl_tree, query) for query in queries]
    rb_query_stats = [_count_red_black_lookup(rb_tree, query) for query in queries]

    splay_before_comparisons = splay_tree.comparison_count
    splay_before_rotations = splay_tree.rotation_count
    splay_hits = [splay_tree.find(query) for query in queries]
    splay_comparisons = splay_tree.comparison_count - splay_before_comparisons
    splay_rotations = splay_tree.rotation_count - splay_before_rotations

    treap_hits = [bool(entry["found"]) for entry in treap_query_stats]
    avl_hits = [bool(entry["found"]) for entry in avl_query_stats]
    rb_hits = [bool(entry["found"]) for entry in rb_query_stats]
    if not (treap_hits == avl_hits == rb_hits == splay_hits):
        raise ValueError("benchmark lookup results diverged across tree implementations")

    return {
        "input_size": len(sequence),
        "query_count": len(queries),
        "treap": {
            "height": treap.height(),
            "mean_lookup_comparisons": round(
                statistics.fmean(int(entry["comparisons"]) for entry in treap_query_stats), 3
            ),
        },
        "avl": {
            "height": avl_tree.height(),
            "rotation_count": sum(1 for event in avl_tree.events if "rotation" in event),
            "mean_lookup_comparisons": round(
                statistics.fmean(int(entry["comparisons"]) for entry in avl_query_stats), 3
            ),
        },
        "red_black": {
            "height": rb_tree.height(),
            "black_height": rb_tree.black_height(),
            "rotation_count": sum(
                1 for event in rb_tree.trace if event["event"] in {"rotate_left", "rotate_right"}
            ),
            "mean_lookup_comparisons": round(
                statistics.fmean(int(entry["comparisons"]) for entry in rb_query_stats), 3
            ),
        },
        "splay": {
            "height_after_build": _splay_height(splay_tree.root),
            "comparisons_used": splay_comparisons,
            "rotations_used": splay_rotations,
            "mean_lookup_comparisons": round(splay_comparisons / len(queries), 3),
            "mean_lookup_rotations": round(splay_rotations / len(queries), 3),
            "root_after_queries": None if splay_tree.root is None else splay_tree.root.key,
        },
    }


def _benchmark_rows(cases: dict[str, dict[str, object]]) -> list[dict[str, int | float | str]]:
    rows: list[dict[str, int | float | str]] = []
    for case_name, case in cases.items():
        rows.append(
            {
                "case": case_name,
                "input_size": int(case["input_size"]),
                "query_count": int(case["query_count"]),
                "treap_height": int(case["treap"]["height"]),
                "avl_height": int(case["avl"]["height"]),
                "red_black_height": int(case["red_black"]["height"]),
                "splay_height_after_build": int(case["splay"]["height_after_build"]),
                "treap_mean_lookup_comparisons": float(case["treap"]["mean_lookup_comparisons"]),
                "avl_mean_lookup_comparisons": float(case["avl"]["mean_lookup_comparisons"]),
                "red_black_mean_lookup_comparisons": float(case["red_black"]["mean_lookup_comparisons"]),
                "splay_mean_lookup_comparisons": float(case["splay"]["mean_lookup_comparisons"]),
                "splay_mean_lookup_rotations": float(case["splay"]["mean_lookup_rotations"]),
                "avl_rotation_count": int(case["avl"]["rotation_count"]),
                "red_black_rotation_count": int(case["red_black"]["rotation_count"]),
                "height_gap_treap_minus_avl": int(case["treap"]["height"]) - int(case["avl"]["height"]),
                "height_gap_treap_minus_red_black": int(case["treap"]["height"]) - int(case["red_black"]["height"]),
            }
        )
    return rows


def _benchmark_csv(rows: list[dict[str, int | float | str]]) -> str:
    if not rows:
        raise ValueError("benchmark rows cannot be empty")
    fieldnames = list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def benchmark_trees(*, count: int, start: int, build_seed: int, query_seed: int, queries: int) -> dict[str, object]:
    if count <= 0:
        raise ValueError("benchmark count must be positive")
    if queries <= 0:
        raise ValueError("benchmark queries must be positive")

    ascending = list(range(start, start + count))
    descending = list(reversed(ascending))
    shuffled = ascending.copy()
    random.Random(build_seed).shuffle(shuffled)

    query_rng = random.Random(query_seed)
    workloads = {
        "ascending": ascending,
        "descending": descending,
        "shuffled": shuffled,
    }
    cases = {
        name: _benchmark_case(sequence, [query_rng.choice(ascending) for _ in range(queries)], seed=build_seed)
        for name, sequence in workloads.items()
    }
    rows = _benchmark_rows(cases)
    summary = {
        "treap_height_mean": round(statistics.fmean(case["treap"]["height"] for case in cases.values()), 3),
        "avl_height_mean": round(statistics.fmean(case["avl"]["height"] for case in cases.values()), 3),
        "red_black_height_mean": round(statistics.fmean(case["red_black"]["height"] for case in cases.values()), 3),
        "splay_height_after_build_mean": round(
            statistics.fmean(case["splay"]["height_after_build"] for case in cases.values()), 3
        ),
        "treap_lookup_mean": round(
            statistics.fmean(case["treap"]["mean_lookup_comparisons"] for case in cases.values()), 3
        ),
        "avl_lookup_mean": round(
            statistics.fmean(case["avl"]["mean_lookup_comparisons"] for case in cases.values()), 3
        ),
        "red_black_lookup_mean": round(
            statistics.fmean(case["red_black"]["mean_lookup_comparisons"] for case in cases.values()), 3
        ),
        "splay_lookup_mean": round(
            statistics.fmean(case["splay"]["mean_lookup_comparisons"] for case in cases.values()), 3
        ),
    }
    summary["height_gap_treap_minus_avl"] = round(summary["treap_height_mean"] - summary["avl_height_mean"], 3)
    summary["height_gap_treap_minus_red_black"] = round(
        summary["treap_height_mean"] - summary["red_black_height_mean"], 3
    )
    summary["lookup_gap_treap_minus_avl"] = round(summary["treap_lookup_mean"] - summary["avl_lookup_mean"], 3)
    summary["lookup_gap_treap_minus_red_black"] = round(
        summary["treap_lookup_mean"] - summary["red_black_lookup_mean"], 3
    )
    return {
        "count": count,
        "start": start,
        "build_seed": build_seed,
        "query_seed": query_seed,
        "query_count": queries,
        "cases": cases,
        "summary": summary,
        "takeaway": (
            "Treap height stays close to AVL/red-black across deterministic insertion orders while preserving simple randomized split/merge logic; "
            "splay can pay extra rotations during lookups because it adapts the tree on every access."
        ),
        "csv": _benchmark_csv(rows),
    }


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def command_demo(args: argparse.Namespace) -> None:
    keys = load_keys(Path(args.sample)) if args.sample else [40, 10, 60, 5, 20, 50, 70, 65, 15]
    treap = build_treap(keys, seed=args.seed, trace=args.trace)
    _print_json(
        {
            "keys": keys,
            "seed": args.seed,
            "inorder": treap.inorder(),
            "preorder": treap.preorder(),
            "validation": treap.validate(),
            "rank_50": treap.rank(50),
            "select_3": treap.select(3),
            "range_count_15_65": treap.range_count(15, 65),
            "trace": treap.events,
        }
    )


def command_build(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed, trace=args.trace)
    _print_json(
        {
            "seed": args.seed,
            "inorder": treap.inorder(),
            "preorder": treap.preorder(),
            "validation": treap.validate(),
            "trace": treap.events,
        }
    )


def command_delete(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed, trace=args.trace)
    treap.delete(args.query)
    _print_json(
        {
            "deleted": args.query,
            "inorder": treap.inorder(),
            "preorder": treap.preorder(),
            "validation": treap.validate(),
            "trace": treap.events,
        }
    )


def command_rank(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json({"query": args.query, "rank": treap.rank(args.query)})


def command_select(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json({"index": args.index, "key": treap.select(args.index)})


def command_range_count(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json({"lower": args.lower, "upper": args.upper, "count": treap.range_count(args.lower, args.upper)})


def command_validate(args: argparse.Namespace) -> None:
    treap = build_treap(args.keys, seed=args.seed)
    _print_json(treap.validate())


def command_benchmark(args: argparse.Namespace) -> None:
    payload = benchmark_trees(
        count=args.count,
        start=args.start,
        build_seed=args.seed,
        query_seed=args.query_seed,
        queries=args.queries,
    )
    if args.csv_file:
        csv_path = Path(args.csv_file)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text(payload["csv"], encoding="utf-8")
        payload["csv_file"] = str(csv_path)
    if not args.csv:
        payload.pop("csv")
    payload["command"] = "benchmark"
    _print_json(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Treap order-statistics lab")
    parser.add_argument("--seed", type=int, default=0, help="seed for deterministic priorities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run the bundled demo")
    demo.add_argument("--sample", help="optional JSON array of integer keys")
    demo.add_argument("--trace", action="store_true")
    demo.set_defaults(func=command_demo)

    build = subparsers.add_parser("build", help="build a treap from keys")
    build.add_argument("keys", nargs="+", type=int)
    build.add_argument("--trace", action="store_true")
    build.set_defaults(func=command_build)

    delete = subparsers.add_parser("delete", help="delete a key and print the repaired treap")
    delete.add_argument("query", type=int)
    delete.add_argument("keys", nargs="+", type=int)
    delete.add_argument("--trace", action="store_true")
    delete.set_defaults(func=command_delete)

    rank = subparsers.add_parser("rank", help="count keys smaller than a query")
    rank.add_argument("query", type=int)
    rank.add_argument("keys", nargs="+", type=int)
    rank.set_defaults(func=command_rank)

    select = subparsers.add_parser("select", help="return the zero-based kth smallest key")
    select.add_argument("index", type=int)
    select.add_argument("keys", nargs="+", type=int)
    select.set_defaults(func=command_select)

    range_count = subparsers.add_parser("range-count", help="count keys inside an inclusive range")
    range_count.add_argument("lower", type=int)
    range_count.add_argument("upper", type=int)
    range_count.add_argument("keys", nargs="+", type=int)
    range_count.set_defaults(func=command_range_count)

    validate = subparsers.add_parser("validate", help="validate a built treap")
    validate.add_argument("keys", nargs="+", type=int)
    validate.set_defaults(func=command_validate)

    benchmark = subparsers.add_parser(
        "benchmark",
        help="compare treap build/query behavior against AVL, red-black, and splay tree labs",
    )
    benchmark.add_argument("--count", type=int, default=63, help="number of sequential integers to insert")
    benchmark.add_argument("--start", type=int, default=1, help="starting integer for the benchmark range")
    benchmark.add_argument("--queries", type=int, default=96, help="number of successful lookup queries per case")
    benchmark.add_argument("--query-seed", type=int, default=19, help="seed for deterministic lookup workload")
    benchmark.add_argument("--csv", action="store_true", help="include chart-ready CSV in the JSON output")
    benchmark.add_argument("--csv-file", help="write chart-ready CSV to disk")
    benchmark.set_defaults(func=command_benchmark)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (KeyError, ValueError, IndexError) as exc:
        _print_json({"error": str(exc)})
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
