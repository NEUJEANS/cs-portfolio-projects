from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class Node:
    children: Dict[str, "Edge"] = field(default_factory=dict)
    suffix_starts: List[int] = field(default_factory=list)


@dataclass
class Edge:
    start: int
    end: int
    child: Node


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

    def to_dot(self, *, show_suffix_starts: bool = False) -> str:
        """Render the suffix tree as a Graphviz DOT graph."""
        lines = [
            "digraph suffix_tree {",
            '  rankdir=LR;',
            '  node [shape=circle, fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
        ]
        node_ids: Dict[int, str] = {}
        counter = 0

        def node_id(node: Node) -> str:
            nonlocal counter
            key = id(node)
            if key not in node_ids:
                node_ids[key] = f"n{counter}"
                counter += 1
            return node_ids[key]

        def escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace('"', '\\"')

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
            shape = "doublecircle" if not node.children else "circle"
            lines.append(f'  {current} [label="{escape(label)}", shape={shape}];')
            for edge in sorted(node.children.values(), key=lambda current_edge: self.text[current_edge.start:current_edge.end]):
                child = node_id(edge.child)
                edge_label = self.text[edge.start:edge.end]
                lines.append(f'  {current} -> {child} [label="{escape(edge_label)}"];')
                walk(edge.child)

        walk(self.root)
        lines.append("}")
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
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    tree = SuffixTree(args.text)

    if args.command == "find":
        matches = tree.find(args.pattern)
        print(f"matches={matches}")
        return 0 if matches else 1
    if args.command == "repeat":
        repeated = tree.longest_repeated_substring(args.min_occurrences)
        print(repeated)
        return 0 if repeated else 1
    if args.command == "explain":
        for line in tree.explain_find(args.pattern):
            print(line)
        return 0
    if args.command == "export-dot":
        print(tree.to_dot(show_suffix_starts=args.show_suffix_starts))
        return 0
    raise AssertionError(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
