from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from statistics import mean
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
                        "remaining_edges": [list(edge) for edge in edges],
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


def build_cycle_graph(vertex_count: int) -> UndirectedMultiGraph:
    if vertex_count < 3:
        raise ValueError("cycle graphs require at least 3 vertices")
    vertices = [f"v{i}" for i in range(vertex_count)]
    edges = [(vertices[i], vertices[(i + 1) % vertex_count]) for i in range(vertex_count)]
    return UndirectedMultiGraph(vertices=vertices, edges=edges)


def build_complete_graph(vertex_count: int) -> UndirectedMultiGraph:
    if vertex_count < 2:
        raise ValueError("complete graphs require at least 2 vertices")
    vertices = [f"v{i}" for i in range(vertex_count)]
    edges = [(vertices[i], vertices[j]) for i in range(vertex_count) for j in range(i + 1, vertex_count)]
    return UndirectedMultiGraph(vertices=vertices, edges=edges)


def build_barbell_graph(clique_size: int) -> UndirectedMultiGraph:
    if clique_size < 3:
        raise ValueError("barbell graphs require clique size at least 3")
    left_vertices = [f"L{i}" for i in range(clique_size)]
    right_vertices = [f"R{i}" for i in range(clique_size)]
    vertices = left_vertices + right_vertices
    edges: list[tuple[str, str]] = []
    for side_vertices in (left_vertices, right_vertices):
        for i in range(len(side_vertices)):
            for j in range(i + 1, len(side_vertices)):
                edges.append((side_vertices[i], side_vertices[j]))
    edges.append((left_vertices[-1], right_vertices[0]))
    return UndirectedMultiGraph(vertices=vertices, edges=edges)


def build_erdos_renyi_graph(vertex_count: int, edge_probability: float, seed: int) -> UndirectedMultiGraph:
    if vertex_count < 2:
        raise ValueError("random graphs require at least 2 vertices")
    if not 0 < edge_probability <= 1:
        raise ValueError("edge probability must be between 0 and 1")
    rng = random.Random(seed)
    vertices = [f"v{i}" for i in range(vertex_count)]
    while True:
        edges = [
            (vertices[i], vertices[j])
            for i in range(vertex_count)
            for j in range(i + 1, vertex_count)
            if rng.random() <= edge_probability
        ]
        if edges:
            try:
                graph = UndirectedMultiGraph(vertices=vertices, edges=edges)
            except ValueError:
                continue
            if is_connected(graph):
                return graph


def is_connected(graph: UndirectedMultiGraph) -> bool:
    adjacency: dict[str, set[str]] = {vertex: set() for vertex in graph.vertices}
    for u, v in graph.edges:
        adjacency[u].add(v)
        adjacency[v].add(u)
    start = graph.vertices[0]
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(graph.vertices)


def build_graph_family(name: str, size: int, instance_seed: int) -> UndirectedMultiGraph:
    if name == "cycle":
        return build_cycle_graph(size)
    if name == "complete":
        return build_complete_graph(size)
    if name == "barbell":
        return build_barbell_graph(size)
    if name == "erdos-renyi":
        edge_probability = min(0.75, max(0.35, 1.8 / max(2, size)))
        return build_erdos_renyi_graph(size, edge_probability=edge_probability, seed=instance_seed)
    raise ValueError(f"unsupported graph family: {name}")


def benchmark_exact_cut(family: str, graph: UndirectedMultiGraph, size_parameter: int) -> int:
    if family == "cycle":
        return 2
    if family == "complete":
        return len(graph.vertices) - 1
    if family == "barbell":
        return 1
    return exact_min_cut_size(graph)


def benchmark_graph_families(
    families: list[str],
    sizes: list[int],
    trials: int,
    instances_per_size: int,
    seed: int,
) -> dict[str, object]:
    if instances_per_size < 1:
        raise ValueError("instances_per_size must be at least 1")
    rows: list[dict[str, object]] = []
    per_family_summary: list[dict[str, object]] = []
    row_seed = seed

    for family in families:
        family_rows: list[dict[str, object]] = []
        for size in sizes:
            for instance_index in range(instances_per_size):
                instance_seed = row_seed
                row_seed += 1
                graph = build_graph_family(family, size, instance_seed=instance_seed)
                exact_cut = benchmark_exact_cut(family, graph, size)
                result = KargerMinCutLab(graph).run_trials(trials=trials, seed=instance_seed)
                hit = int(result["best_cut_size"]) == exact_cut
                row = {
                    "family": family,
                    "size_parameter": size,
                    "instance_index": instance_index + 1,
                    "instance_seed": instance_seed,
                    "vertex_count": len(graph.vertices),
                    "edge_count": len(graph.edges),
                    "trials": trials,
                    "best_cut_size": int(result["best_cut_size"]),
                    "exact_min_cut_size": exact_cut,
                    "hit_exact_cut": hit,
                    "histogram": result["histogram"],
                    "recommended_trials": len(graph.vertices) ** 2,
                }
                rows.append(row)
                family_rows.append(row)
        per_family_summary.append(
            {
                "family": family,
                "instances": len(family_rows),
                "hit_rate": round(sum(1 for row in family_rows if row["hit_exact_cut"]) / len(family_rows), 4),
                "average_best_cut": round(mean(int(row["best_cut_size"]) for row in family_rows), 4),
                "average_exact_cut": round(mean(int(row["exact_min_cut_size"]) for row in family_rows), 4),
                "average_vertex_count": round(mean(int(row["vertex_count"]) for row in family_rows), 2),
            }
        )

    return {
        "algorithm": "karger-random-contraction",
        "benchmark": {
            "families": families,
            "sizes": sizes,
            "trials": trials,
            "instances_per_size": instances_per_size,
            "base_seed": seed,
            "total_instances": len(rows),
        },
        "rows": rows,
        "family_summary": per_family_summary,
    }


def write_benchmark_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "family",
        "size_parameter",
        "instance_index",
        "instance_seed",
        "vertex_count",
        "edge_count",
        "trials",
        "best_cut_size",
        "exact_min_cut_size",
        "hit_exact_cut",
        "recommended_trials",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})


def maybe_write_json(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _trace_contractions(payload: dict[str, object]) -> list[dict[str, object]]:
    direct = payload.get("contractions")
    if isinstance(direct, list) and direct:
        return direct
    trial_results = payload.get("trial_results")
    if isinstance(trial_results, list) and trial_results:
        first_trial = trial_results[0]
        if isinstance(first_trial, dict):
            contractions = first_trial.get("contractions")
            if isinstance(contractions, list) and contractions:
                return contractions
    raise ValueError("payload must include a contraction trace before DOT export")


def build_trace_dot(payload: dict[str, object], step: int) -> str:
    if step < 0:
        raise ValueError("step must be non-negative")
    graph_summary = payload.get("graph_summary")
    if not isinstance(graph_summary, dict):
        raise ValueError("payload must include graph_summary for trace export")
    vertices = graph_summary.get("vertices")
    if not isinstance(vertices, list) or not vertices:
        raise ValueError("graph_summary must include vertices")
    contractions = _trace_contractions(payload)

    if step == 0:
        remaining_supernodes = [[str(vertex)] for vertex in vertices]
        remaining_edges = payload.get("input_edges")
    else:
        if step > len(contractions):
            raise ValueError("step exceeds available contraction trace")
        contraction = contractions[step - 1]
        if not isinstance(contraction, dict):
            raise ValueError("invalid contraction entry")
        remaining_supernodes = contraction.get("remaining_supernodes")
        remaining_edges = contraction.get("remaining_edges")

    if not isinstance(remaining_supernodes, list) or not isinstance(remaining_edges, list):
        raise ValueError("trace step must include remaining supernodes and edges")

    lines = ["graph KargerTrace {", '  graph [labelloc="t"];', f'  label="Karger trace step {step}";', "  node [shape=ellipse];"]
    for group in remaining_supernodes:
        members = [str(member) for member in group]
        node_id = "cluster_" + "_".join(members)
        label = "\\n".join(members)
        lines.append(f'  "{node_id}" [label="{label}"];')

    multiplicity = Counter(tuple(sorted((str(edge[0]), str(edge[1])))) for edge in remaining_edges)
    for (left, right), count in sorted(multiplicity.items()):
        left_id = "cluster_" + "_".join(left.strip("{}").split(",")) if left.startswith("{") else f"cluster_{left}"
        right_id = "cluster_" + "_".join(right.strip("{}").split(",")) if right.startswith("{") else f"cluster_{right}"
        lines.append(f'  "{left_id}" -- "{right_id}" [label="{count}", penwidth={1 + count / 2:.1f}];')
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_trace_dot_snapshots(output_dir: Path, payload: dict[str, object]) -> list[Path]:
    contractions = _trace_contractions(payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []
    for step in range(len(contractions) + 1):
        path = output_dir / f"step-{step:02d}.dot"
        path.write_text(build_trace_dot(payload, step))
        written_paths.append(path)
    return written_paths


def parse_csv_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_int_csv(raw: str) -> list[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("expected at least one integer size")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Karger's randomized min-cut algorithm on a small undirected multigraph.")
    parser.add_argument("command", nargs="?", default="demo", choices=["demo", "run", "benchmark"], help="demo uses the built-in sample graph")
    parser.add_argument("--graph-file", type=Path, help="path to a JSON file with vertices and edges")
    parser.add_argument("--trials", type=int, default=1, help="number of independent trials to run")
    parser.add_argument("--seed", type=int, help="starting seed for deterministic sequential trials")
    parser.add_argument("--include-trace", action="store_true", help="include contraction trace for the first reported trial")
    parser.add_argument("--trace-dot-dir", type=Path, help="write Graphviz DOT snapshots for each contraction step")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    parser.add_argument("--exact-check", action="store_true", help="also compute the exact min-cut size for small graphs")
    parser.add_argument("--families", default="cycle,complete,barbell,erdos-renyi", help="comma-separated graph families for benchmark mode")
    parser.add_argument("--sizes", default="4,6,8", help="comma-separated size parameters for benchmark mode")
    parser.add_argument("--instances-per-size", type=int, default=2, help="number of instances per family/size pair in benchmark mode")
    parser.add_argument("--output-json", type=Path, help="write benchmark JSON output to a file")
    parser.add_argument("--output-csv", type=Path, help="write benchmark CSV summary to a file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "run" and args.graph_file is None:
        raise SystemExit("--graph-file is required when command=run")
    if args.command == "benchmark":
        base_seed = 0 if args.seed is None else args.seed
        payload = benchmark_graph_families(
            families=parse_csv_list(args.families),
            sizes=parse_int_csv(args.sizes),
            trials=args.trials,
            instances_per_size=args.instances_per_size,
            seed=base_seed,
        )
        maybe_write_json(args.output_json, payload)
        if args.output_csv is not None:
            write_benchmark_csv(args.output_csv, payload["rows"])
        print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
        return

    graph = build_sample_graph() if args.command == "demo" and args.graph_file is None else load_graph(args.graph_file)
    lab = KargerMinCutLab(graph)
    include_trace = args.include_trace or args.trace_dot_dir is not None
    payload = lab.run_trials(trials=args.trials, seed=args.seed, include_trace=include_trace)
    payload["graph_summary"] = {
        "vertices": graph.vertices,
        "edge_count": len(graph.edges),
    }
    payload["input_edges"] = [list(edge) for edge in graph.edges]
    if args.exact_check:
        payload["exact_min_cut_size"] = exact_min_cut_size(graph)
    if args.trace_dot_dir is not None:
        payload["trace_dot_files"] = [str(path) for path in write_trace_dot_snapshots(args.trace_dot_dir, payload)]
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
