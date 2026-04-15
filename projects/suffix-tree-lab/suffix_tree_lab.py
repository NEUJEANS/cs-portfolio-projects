from __future__ import annotations

import argparse
import re
import time
from bisect import bisect_left
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class Node:
    children: Dict[str, "Edge"] = field(default_factory=dict)
    suffix_starts: List[int] = field(default_factory=list)


@dataclass
class Edge:
    start: int
    end: int
    child: Node


@dataclass(frozen=True)
class BenchmarkResult:
    method: str
    pattern: str
    matches: int
    total_seconds: float
    avg_seconds: float


@dataclass(frozen=True)
class SuffixArrayIndex:
    text: str
    suffix_starts: List[int]

    @classmethod
    def build(cls, text: str) -> "SuffixArrayIndex":
        return cls(text=text, suffix_starts=sorted(range(len(text)), key=lambda start: text[start:]))

    def find(self, pattern: str) -> List[int]:
        if not pattern:
            raise ValueError("pattern must be non-empty")

        left = bisect_left(self.suffix_starts, pattern, key=lambda start: self.text[start:])
        matches: List[int] = []
        for suffix_start in self.suffix_starts[left:]:
            if self.text.startswith(pattern, suffix_start):
                matches.append(suffix_start)
                continue
            if matches:
                break
            suffix = self.text[suffix_start:]
            if suffix > pattern:
                break
        return sorted(matches)


class SuffixTree:
    """Naive compressed suffix tree for a single string.

    The implementation builds a compact edge-labeled suffix tree by inserting all
    suffixes and splitting edges on mismatch. It is intentionally educational:
    construction is O(n^2), while query traversal stays linear in the pattern.
    """

    def __init__(self, text: str, sentinel: str = "$") -> None:
        if not text:
            raise ValueError("text must be non-empty")
        if sentinel in text:
            raise ValueError(f"sentinel {sentinel!r} must not appear in text")
        self.original_text = text
        self.text = text + sentinel
        self.root = Node()
        self.suffix_array = SuffixArrayIndex.build(text)
        for start in range(len(self.text)):
            self._insert_suffix(start)

    def _insert_suffix(self, suffix_start: int) -> None:
        node = self.root
        node.suffix_starts.append(suffix_start)
        index = suffix_start

        while index < len(self.text):
            char = self.text[index]
            edge = node.children.get(char)
            if edge is None:
                leaf = Node(suffix_starts=[suffix_start])
                node.children[char] = Edge(index, len(self.text), leaf)
                return

            match_len = self._edge_match_length(edge, index)
            edge_length = edge.end - edge.start

            if match_len == edge_length:
                index += match_len
                node = edge.child
                node.suffix_starts.append(suffix_start)
                continue

            split = Node(suffix_starts=edge.child.suffix_starts.copy())
            split.suffix_starts.append(suffix_start)

            old_char = self.text[edge.start + match_len]
            split.children[old_char] = Edge(edge.start + match_len, edge.end, edge.child)

            new_leaf = Node(suffix_starts=[suffix_start])
            new_char = self.text[index + match_len]
            split.children[new_char] = Edge(index + match_len, len(self.text), new_leaf)

            node.children[char] = Edge(edge.start, edge.start + match_len, split)
            return

    def _edge_match_length(self, edge: Edge, index: int) -> int:
        matched = 0
        while (
            edge.start + matched < edge.end
            and index + matched < len(self.text)
            and self.text[edge.start + matched] == self.text[index + matched]
        ):
            matched += 1
        return matched

    def contains(self, pattern: str) -> bool:
        return bool(pattern) and self._match_node(pattern) is not None

    def find(self, pattern: str) -> List[int]:
        if not pattern:
            raise ValueError("pattern must be non-empty")
        node = self._match_node(pattern)
        if node is None:
            return []
        limit = len(self.original_text) - len(pattern)
        return sorted(start for start in node.suffix_starts if start <= limit)

    def count(self, pattern: str) -> int:
        return len(self.find(pattern))

    def longest_repeated_substring(self, min_occurrences: int = 2) -> str:
        if min_occurrences < 2:
            raise ValueError("min_occurrences must be at least 2")

        best = ""

        def walk(node: Node, path: str) -> None:
            nonlocal best
            if path and len(node.suffix_starts) >= min_occurrences:
                candidate = path.replace("$", "")
                if len(candidate) > len(best):
                    best = candidate
            for edge in node.children.values():
                label = self.text[edge.start:edge.end]
                walk(edge.child, path + label)

        walk(self.root, "")
        return best

    def edge_labels(self) -> List[str]:
        labels: List[str] = []

        def walk(node: Node) -> None:
            for edge in node.children.values():
                labels.append(self.text[edge.start:edge.end])
                walk(edge.child)

        walk(self.root)
        return sorted(labels)

    def explain_find(self, pattern: str) -> List[str]:
        if not pattern:
            raise ValueError("pattern must be non-empty")
        steps: List[str] = []
        node = self.root
        consumed = 0
        while consumed < len(pattern):
            edge = node.children.get(pattern[consumed])
            if edge is None:
                steps.append(f"No outgoing edge for {pattern[consumed]!r} after matching {consumed} chars")
                return steps
            label = self.text[edge.start:edge.end]
            steps.append(f"follow edge {label!r}")
            for offset, edge_char in enumerate(label):
                if consumed == len(pattern):
                    return steps
                wanted = pattern[consumed]
                if edge_char != wanted:
                    steps.append(
                        f"mismatch at edge offset {offset}: expected {wanted!r}, saw {edge_char!r}"
                    )
                    return steps
                consumed += 1
            node = edge.child
        steps.append(f"matched {pattern!r} with {len(node.suffix_starts)} suffix hits")
        return steps

    def benchmark_search(self, patterns: Sequence[str], *, iterations: int = 200) -> List[BenchmarkResult]:
        if not patterns:
            raise ValueError("patterns must be non-empty")
        if iterations < 1:
            raise ValueError("iterations must be at least 1")

        normalized = []
        for pattern in patterns:
            if not pattern:
                raise ValueError("patterns must not contain empty strings")
            normalized.append(pattern)

        baseline_counts = {pattern: len(self.find(pattern)) for pattern in normalized}
        methods = {
            "suffix_tree": self.find,
            "suffix_array": self.suffix_array.find,
            "python_find": lambda pattern: find_with_python(self.original_text, pattern),
            "regex_lookahead": lambda pattern: find_with_regex(self.original_text, pattern),
        }
        results: List[BenchmarkResult] = []

        for method_name, method in methods.items():
            for pattern in normalized:
                start = time.perf_counter()
                matches: List[int] = []
                for _ in range(iterations):
                    matches = method(pattern)
                total_seconds = time.perf_counter() - start
                match_count = len(matches)
                if match_count != baseline_counts[pattern]:
                    raise AssertionError(
                        f"benchmark mismatch for {method_name} and pattern {pattern!r}: "
                        f"expected {baseline_counts[pattern]}, saw {match_count}"
                    )
                results.append(
                    BenchmarkResult(
                        method=method_name,
                        pattern=pattern,
                        matches=match_count,
                        total_seconds=total_seconds,
                        avg_seconds=total_seconds / iterations,
                    )
                )
        return results

    def _node_render_plan(self, *, show_suffix_starts: bool = False) -> List[Tuple[str, str, bool, List[Tuple[str, str]]]]:
        node_ids: Dict[int, str] = {}
        counter = 0

        def node_id(node: Node) -> str:
            nonlocal counter
            key = id(node)
            if key not in node_ids:
                node_ids[key] = f"n{counter}"
                counter += 1
            return node_ids[key]

        plan: List[Tuple[str, str, bool, List[Tuple[str, str]]]] = []

        def walk(node: Node) -> None:
            current = node_id(node)
            if node is self.root:
                label = "root"
                if show_suffix_starts:
                    suffixes = ", ".join(map(str, sorted(node.suffix_starts)))
                    label = f"root\n[{suffixes}]"
            elif show_suffix_starts:
                suffixes = ", ".join(map(str, sorted(node.suffix_starts)))
                label = f"[{suffixes}]"
            else:
                label = ""

            children: List[Tuple[str, str]] = []
            for edge in sorted(node.children.values(), key=lambda current_edge: self.text[current_edge.start:current_edge.end]):
                child = node_id(edge.child)
                edge_label = self.text[edge.start:edge.end]
                children.append((child, edge_label))
            plan.append((current, label, not node.children, children))
            for edge in sorted(node.children.values(), key=lambda current_edge: self.text[current_edge.start:current_edge.end]):
                walk(edge.child)

        walk(self.root)
        return plan

    def to_dot(self, *, show_suffix_starts: bool = False) -> str:
        """Render the suffix tree as a Graphviz DOT graph."""
        lines = [
            "digraph suffix_tree {",
            '  rankdir=LR;',
            '  node [shape=circle, fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
        ]

        def escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', '\\"')

        for current, label, is_leaf, children in self._node_render_plan(show_suffix_starts=show_suffix_starts):
            shape = "doublecircle" if is_leaf else "circle"
            lines.append(f'  {current} [label="{escape(label)}", shape={shape}];')
            for child, edge_label in children:
                lines.append(f'  {current} -> {child} [label="{escape(edge_label)}"];')

        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self, *, show_suffix_starts: bool = False) -> str:
        """Render the suffix tree as a Mermaid flowchart."""
        lines = [
            "flowchart LR",
            "  classDef leaf stroke-width:2px",
        ]

        def escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', "#quot;").replace("\n", "<br/>")

        for current, label, is_leaf, children in self._node_render_plan(show_suffix_starts=show_suffix_starts):
            node_label = escape(label)
            lines.append(f'  {current}["{node_label}"]')
            if is_leaf:
                lines.append(f"  class {current} leaf")
            for child, edge_label in children:
                lines.append(f'  {current} -->|"{escape(edge_label)}"| {child}')

        return "\n".join(lines)

    def _match_node(self, pattern: str) -> Optional[Node]:
        node = self.root
        consumed = 0
        while consumed < len(pattern):
            edge = node.children.get(pattern[consumed])
            if edge is None:
                return None
            label = self.text[edge.start:edge.end]
            for edge_char in label:
                if consumed == len(pattern):
                    return edge.child
                if edge_char != pattern[consumed]:
                    return None
                consumed += 1
            node = edge.child
        return node


def find_with_python(text: str, pattern: str) -> List[int]:
    matches: List[int] = []
    start = 0
    while True:
        index = text.find(pattern, start)
        if index == -1:
            return matches
        matches.append(index)
        start = index + 1


def find_with_regex(text: str, pattern: str) -> List[int]:
    compiled = re.compile(f"(?={re.escape(pattern)})")
    return [match.start() for match in compiled.finditer(text)]


def benchmark_results_to_csv(results: Sequence[BenchmarkResult]) -> str:
    rows = [["method", "pattern", "matches", "total_seconds", "avg_seconds"]]
    for result in results:
        rows.append(
            [
                result.method,
                result.pattern,
                str(result.matches),
                f"{result.total_seconds:.9f}",
                f"{result.avg_seconds:.9f}",
            ]
        )

    output: List[str] = []
    for row in rows:
        output.append(",".join(_csv_escape(value) for value in row))
    return "\n".join(output)


def _csv_escape(value: str) -> str:
    if any(char in value for char in [",", '"', "\n"]):
        return '"' + value.replace('"', '""') + '"'
    return value


def parse_patterns(patterns: str) -> List[str]:
    parsed = [pattern.strip() for pattern in patterns.split(",") if pattern.strip()]
    if not parsed:
        raise ValueError("at least one non-empty pattern is required")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compressed suffix tree lab")
    parser.add_argument("text", help="source text to index")
    subparsers = parser.add_subparsers(dest="command", required=True)

    find_parser = subparsers.add_parser("find", help="find all occurrences of a pattern")
    find_parser.add_argument("pattern")

    repeat_parser = subparsers.add_parser("repeat", help="show longest repeated substring")
    repeat_parser.add_argument("--min-occurrences", type=int, default=2)

    explain_parser = subparsers.add_parser("explain", help="trace a pattern lookup")
    explain_parser.add_argument("pattern")

    export_parser = subparsers.add_parser("export-dot", help="export the tree as Graphviz DOT")
    export_parser.add_argument("--show-suffix-starts", action="store_true")

    mermaid_parser = subparsers.add_parser("export-mermaid", help="export the tree as a Mermaid flowchart")
    mermaid_parser.add_argument("--show-suffix-starts", action="store_true")

    benchmark_parser = subparsers.add_parser(
        "benchmark", help="compare suffix-tree search against Python and regex baselines"
    )
    benchmark_parser.add_argument(
        "--patterns",
        required=True,
        help="comma-separated patterns to benchmark, for example ana,na,ban",
    )
    benchmark_parser.add_argument("--iterations", type=int, default=200)
    benchmark_parser.add_argument("--csv", action="store_true", help="print CSV instead of a readable table")
    benchmark_parser.add_argument(
        "--output",
        type=Path,
        help="optional output file path for CSV export; parent directories are created automatically",
    )

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    tree = SuffixTree(args.text)

    if args.command == "find":
        matches = tree.find(args.pattern)
        print(f"matches={matches}")
    elif args.command == "repeat":
        repeated = tree.longest_repeated_substring(min_occurrences=args.min_occurrences)
        print(repeated)
    elif args.command == "explain":
        lines = tree.explain_find(args.pattern)
        print("\n".join(lines))
    elif args.command == "export-dot":
        print(tree.to_dot(show_suffix_starts=args.show_suffix_starts))
    elif args.command == "export-mermaid":
        print(tree.to_mermaid(show_suffix_starts=args.show_suffix_starts))
    elif args.command == "benchmark":
        patterns = parse_patterns(args.patterns)
        results = tree.benchmark_search(patterns, iterations=args.iterations)
        csv_output = benchmark_results_to_csv(results)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(csv_output + "\n", encoding="utf-8")
        if args.csv:
            print(csv_output)
        else:
            print("method           pattern  matches  total_seconds  avg_seconds")
            for result in results:
                print(
                    f"{result.method:<16} {result.pattern:<8} {result.matches:<8} "
                    f"{result.total_seconds:>13.6f} {result.avg_seconds:>12.6f}"
                )
            if args.output is not None:
                print(f"wrote_csv={args.output}")
    else:
        raise AssertionError(f"unknown command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
