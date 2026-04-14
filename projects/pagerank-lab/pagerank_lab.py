from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class PageRankResult:
    scores: dict[str, float]
    iterations: int
    converged: bool
    delta: float

    def top(self, limit: int) -> list[dict[str, float | str]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        ranked = sorted(self.scores.items(), key=lambda item: (-item[1], item[0]))
        return [
            {"node": node, "score": round(score, 6)}
            for node, score in ranked[:limit]
        ]

    def to_dict(self, limit: int | None = None) -> dict[str, object]:
        payload: dict[str, object] = {
            "iterations": self.iterations,
            "converged": self.converged,
            "delta": round(self.delta, 12),
            "scores": {
                node: round(score, 12) for node, score in sorted(self.scores.items())
            },
        }
        if limit is not None:
            payload["top"] = self.top(limit)
        return payload


class DirectedGraph:
    def __init__(self, adjacency: dict[str, set[str]]) -> None:
        if not adjacency:
            raise ValueError("graph must contain at least one node")
        normalized: dict[str, set[str]] = {}
        for node, neighbors in adjacency.items():
            if not node:
                raise ValueError("node names must be non-empty")
            normalized[node] = {neighbor for neighbor in neighbors if neighbor}
        for neighbors in list(normalized.values()):
            for neighbor in neighbors:
                normalized.setdefault(neighbor, set())
        self.adjacency = {node: set(sorted(neighbors)) for node, neighbors in sorted(normalized.items())}

    @classmethod
    def from_edges(cls, edges: Iterable[tuple[str, str]]) -> "DirectedGraph":
        adjacency: dict[str, set[str]] = {}
        saw_edge = False
        for source, target in edges:
            if not source or not target:
                raise ValueError("edges must use non-empty source and target names")
            adjacency.setdefault(source, set()).add(target)
            adjacency.setdefault(target, set())
            saw_edge = True
        if not saw_edge:
            raise ValueError("graph input must contain at least one edge")
        return cls(adjacency)

    @classmethod
    def from_edge_list_file(cls, path: str | Path) -> "DirectedGraph":
        rows: list[tuple[str, str]] = []
        with Path(path).open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) != 2:
                    raise ValueError(
                        f"invalid edge list line {line_number}: expected 'source target'"
                    )
                rows.append((parts[0], parts[1]))
        return cls.from_edges(rows)

    @property
    def nodes(self) -> list[str]:
        return sorted(self.adjacency)

    def outgoing(self, node: str) -> set[str]:
        return set(self.adjacency[node])


def compute_pagerank(
    graph: DirectedGraph,
    damping: float = 0.85,
    max_iterations: int = 100,
    tolerance: float = 1e-9,
) -> PageRankResult:
    if not 0 < damping < 1:
        raise ValueError("damping must be between 0 and 1")
    if max_iterations <= 0:
        raise ValueError("max_iterations must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")

    nodes = graph.nodes
    count = len(nodes)
    scores = {node: 1.0 / count for node in nodes}
    teleport = (1.0 - damping) / count
    delta = 0.0

    for iteration in range(1, max_iterations + 1):
        next_scores = {node: teleport for node in nodes}
        dangling_mass = sum(scores[node] for node in nodes if not graph.outgoing(node))
        dangling_share = damping * dangling_mass / count
        for node in nodes:
            next_scores[node] += dangling_share

        for source in nodes:
            targets = graph.outgoing(source)
            if not targets:
                continue
            share = damping * scores[source] / len(targets)
            for target in targets:
                next_scores[target] += share

        delta = sum(abs(next_scores[node] - scores[node]) for node in nodes)
        scores = next_scores
        if delta <= tolerance:
            return PageRankResult(scores=scores, iterations=iteration, converged=True, delta=delta)

    return PageRankResult(scores=scores, iterations=max_iterations, converged=False, delta=delta)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute PageRank for a local edge-list graph")
    subparsers = parser.add_subparsers(dest="command", required=True)

    rank = subparsers.add_parser("rank", help="compute PageRank for an edge-list file")
    rank.add_argument("path", help="path to an edge-list text file")
    rank.add_argument("--damping", type=float, default=0.85)
    rank.add_argument("--max-iterations", type=int, default=100)
    rank.add_argument("--tolerance", type=float, default=1e-9)
    rank.add_argument("--top", type=int, default=5, help="number of top nodes to show")

    inspect = subparsers.add_parser("inspect", help="show graph structure summary")
    inspect.add_argument("path", help="path to an edge-list text file")

    return parser


def command_rank(args: argparse.Namespace) -> dict[str, object]:
    graph = DirectedGraph.from_edge_list_file(args.path)
    result = compute_pagerank(
        graph,
        damping=args.damping,
        max_iterations=args.max_iterations,
        tolerance=args.tolerance,
    )
    if args.top <= 0:
        raise ValueError("--top must be positive")
    payload = result.to_dict(limit=args.top)
    payload["node_count"] = len(graph.nodes)
    payload["edge_count"] = sum(len(graph.outgoing(node)) for node in graph.nodes)
    payload["score_sum"] = round(sum(result.scores.values()), 12)
    return payload


def command_inspect(args: argparse.Namespace) -> dict[str, object]:
    graph = DirectedGraph.from_edge_list_file(args.path)
    dangling = sorted(node for node in graph.nodes if not graph.outgoing(node))
    return {
        "node_count": len(graph.nodes),
        "edge_count": sum(len(graph.outgoing(node)) for node in graph.nodes),
        "dangling_nodes": dangling,
        "nodes": [
            {"node": node, "outgoing": sorted(graph.outgoing(node))}
            for node in graph.nodes
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "rank":
        payload = command_rank(args)
    else:
        payload = command_inspect(args)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
