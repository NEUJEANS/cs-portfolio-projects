from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Edge:
    u: str
    v: str

    def normalized(self) -> tuple[str, str]:
        if self.u == self.v:
            raise ValueError("self-loops are not allowed in the input graph")
        return tuple(sorted((self.u, self.v)))


class UndirectedMultiGraph:
    def __init__(self, vertices: Iterable[str], edges: Iterable[tuple[str, str] | Edge]) -> None:
        vertex_list = [str(vertex) for vertex in vertices]
        if len(vertex_list) < 2:
            raise ValueError("at least two vertices are required")
        if len(set(vertex_list)) != len(vertex_list):
            raise ValueError("vertices must be unique")
        self.vertices = sorted(vertex_list)
        vertex_set = set(self.vertices)
        normalized_edges: list[tuple[str, str]] = []
        for raw_edge in edges:
            edge = raw_edge if isinstance(raw_edge, Edge) else Edge(*raw_edge)
            u, v = edge.normalized()
            if u not in vertex_set or v not in vertex_set:
                raise ValueError("every edge endpoint must belong to the vertex set")
            normalized_edges.append((u, v))
        if not normalized_edges:
            raise ValueError("at least one edge is required")
        self.edges = normalized_edges

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> "UndirectedMultiGraph":
        vertices = payload.get("vertices")
        edges = payload.get("edges")
        if not isinstance(vertices, list) or not isinstance(edges, list):
            raise ValueError("payload must include list fields 'vertices' and 'edges'")
        parsed_edges: list[tuple[str, str]] = []
        for edge in edges:
            if not isinstance(edge, list) or len(edge) != 2:
                raise ValueError("each edge must be a two-item list")
            parsed_edges.append((str(edge[0]), str(edge[1])))
        return cls(vertices=[str(vertex) for vertex in vertices], edges=parsed_edges)

    def summary(self) -> dict[str, object]:
        return {
            "vertex_count": len(self.vertices),
            "edge_count": len(self.edges),
            "parallel_edge_multiplicity": Counter(self.edges),
        }


class KargerMinCutLab:
    def __init__(self, graph: UndirectedMultiGraph) -> None:
        self.graph = graph

    def run_trial(self, seed: int | None = None, include_trace: bool = False) -> dict[str, object]:
        rng = random.Random(seed)
        supernodes = {vertex: {vertex} for vertex in self.graph.vertices}
        edges = list(self.graph.edges)
        contractions: list[dict[str, object]] = []

        while len(supernodes) > 2:
            left, right = rng.choice(edges)
            if left == right:
                continue
            merged_label = "{" + ",".join(sorted(supernodes[left] | supernodes[right])) + "}"
            merged_members = supernodes[left] | supernodes[right]
            del supernodes[left]
            del supernodes[right]
            supernodes[merged_label] = merged_members

            next_edges: list[tuple[str, str]] = []
            removed_loops = 0
            for edge_u, edge_v in edges:
                mapped_u = merged_label if edge_u in {left, right} else edge_u
                mapped_v = merged_label if edge_v in {left, right} else edge_v
                if mapped_u == mapped_v:
                    removed_loops += 1
                    continue
                next_edges.append(tuple(sorted((mapped_u, mapped_v))))
            edges = next_edges

            if not edges and len(supernodes) > 2:
                raise ValueError("graph became disconnected before reaching two supernodes")
            if include_trace:
                contractions.append(
                    {
                        "picked_edge": [left, right],
                        "merged_supernode": merged_label,
                        "remaining_supernodes": sorted(sorted(group) for group in supernodes.values()),
                        "remaining_edge_count": len(edges),
                        "removed_self_loops": removed_loops,
                    }
                )

        partitions = [sorted(group) for group in supernodes.values()]
        partitions.sort(key=lambda group: (len(group), group))
        cut_edges = len(edges)
        success_probability_lower_bound = 2 / (len(self.graph.vertices) * (len(self.graph.vertices) - 1))
        result = {
            "algorithm": "karger-random-contraction",
            "seed": seed,
            "vertex_count": len(self.graph.vertices),
            "original_edge_count": len(self.graph.edges),
            "remaining_supernode_count": len(supernodes),
            "partitions": partitions,
            "cut_size": cut_edges,
            "surviving_parallel_edges": [list(edge) for edge in edges],
            "success_probability_lower_bound": round(success_probability_lower_bound, 6),
            "recommended_trials": max(1, len(self.graph.vertices) ** 2),
        }
        if include_trace:
            result["contractions"] = contractions
        return result

    def run_trials(self, trials: int, seed: int | None = None, include_trace: bool = False) -> dict[str, object]:
        if trials < 1:
            raise ValueError("trials must be at least 1")
        best_result: dict[str, object] | None = None
        trial_results: list[dict[str, object]] = []
        base_seed = 0 if seed is None else seed
        for trial_index in range(trials):
            trial_seed = None if seed is None else base_seed + trial_index
            result = self.run_trial(seed=trial_seed, include_trace=include_trace and trial_index == 0)
            result["trial"] = trial_index + 1
            trial_results.append(result)
            if best_result is None or int(result["cut_size"]) < int(best_result["cut_size"]):
                best_result = result
        assert best_result is not None
        cut_histogram = Counter(int(result["cut_size"]) for result in trial_results)
        return {
            "algorithm": "karger-random-contraction",
            "trials": trials,
            "seed_mode": "sequential" if seed is not None else "system-random",
            "best_cut_size": best_result["cut_size"],
            "best_partitions": best_result["partitions"],
            "best_trial": best_result["trial"],
            "histogram": dict(sorted(cut_histogram.items())),
            "trial_results": trial_results,
        }


def exact_min_cut_size(graph: UndirectedMultiGraph) -> int:
    vertices = graph.vertices
    if len(vertices) > 14:
        raise ValueError("exact verification is limited to graphs with at most 14 vertices")
    anchor = vertices[0]
    remainder = vertices[1:]
    best: int | None = None
    for subset_size in range(len(remainder) + 1):
        for subset in combinations(remainder, subset_size):
            group = {anchor, *subset}
            if len(group) == len(vertices):
                continue
            cut = 0
            for u, v in graph.edges:
                if (u in group) != (v in group):
                    cut += 1
            if best is None or cut < best:
                best = cut
    assert best is not None
    return best


def load_graph(path: Path) -> UndirectedMultiGraph:
    payload = json.loads(path.read_text())
    return UndirectedMultiGraph.from_json(payload)


def build_sample_graph() -> UndirectedMultiGraph:
    return UndirectedMultiGraph(
        vertices=["A", "B", "C", "D"],
        edges=[("A", "B"), ("A", "C"), ("B", "C"), ("B", "D"), ("C", "D")],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Karger's randomized min-cut algorithm on a small undirected multigraph.")
    parser.add_argument("--graph-file", type=Path, help="path to a JSON file with vertices and edges")
    parser.add_argument("--trials", type=int, default=1, help="number of independent trials to run")
    parser.add_argument("--seed", type=int, help="starting seed for deterministic sequential trials")
    parser.add_argument("--include-trace", action="store_true", help="include contraction trace for the first reported trial")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    parser.add_argument("--exact-check", action="store_true", help="also compute the exact min-cut size for small graphs")
    parser.add_argument("command", nargs="?", default="demo", choices=["demo", "run"], help="demo uses the built-in sample graph")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    graph = build_sample_graph() if args.command == "demo" and args.graph_file is None else load_graph(args.graph_file)
    lab = KargerMinCutLab(graph)
    payload = lab.run_trials(trials=args.trials, seed=args.seed, include_trace=args.include_trace)
    payload["graph_summary"] = {
        "vertices": graph.vertices,
        "edge_count": len(graph.edges),
    }
    if args.exact_check:
        payload["exact_min_cut_size"] = exact_min_cut_size(graph)
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
