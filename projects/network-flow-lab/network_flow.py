from __future__ import annotations

import argparse
import json
import random
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    capacity: int


@dataclass(frozen=True)
class FlowResult:
    source: str
    sink: str
    max_flow: int
    augmenting_paths: list[dict[str, Any]]
    edge_flows: list[dict[str, Any]]
    min_cut: dict[str, list[str]]
    algorithm: str = "edmonds-karp"
    phases: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "sink": self.sink,
            "algorithm": self.algorithm,
            "max_flow": self.max_flow,
            "augmenting_paths": self.augmenting_paths,
            "edge_flows": self.edge_flows,
            "min_cut": self.min_cut,
        }
        if self.phases is not None:
            payload["phases"] = self.phases
        return payload


@dataclass(frozen=True)
class MatchingResult:
    left_partition: list[str]
    right_partition: list[str]
    matches: list[dict[str, str]]
    unmatched_left: list[str]
    unmatched_right: list[str]
    minimum_vertex_cover: dict[str, Any]
    flow: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_partition": self.left_partition,
            "right_partition": self.right_partition,
            "matches": self.matches,
            "match_count": len(self.matches),
            "unmatched_left": self.unmatched_left,
            "unmatched_right": self.unmatched_right,
            "minimum_vertex_cover": self.minimum_vertex_cover,
            "flow": self.flow,
        }


def build_flow_explanation(flow_result: FlowResult) -> dict[str, Any]:
    source_side = set(flow_result.min_cut["source_side"])
    sink_side = set(flow_result.min_cut["sink_side"])
    cut_edges = [
        edge
        for edge in flow_result.edge_flows
        if edge["source"] in source_side and edge["target"] in sink_side
    ]
    cut_capacity = sum(edge["capacity"] for edge in cut_edges)
    return {
        "algorithm": flow_result.algorithm,
        "max_flow": flow_result.max_flow,
        "min_cut_capacity": cut_capacity,
        "max_flow_equals_min_cut_capacity": flow_result.max_flow == cut_capacity,
        "source_side": flow_result.min_cut["source_side"],
        "sink_side": flow_result.min_cut["sink_side"],
        "cut_edges": [
            {
                "source": edge["source"],
                "target": edge["target"],
                "flow": edge["flow"],
                "capacity": edge["capacity"],
                "saturated": edge["flow"] == edge["capacity"],
            }
            for edge in cut_edges
        ],
        "augmenting_path_count": len(flow_result.augmenting_paths),
        "narrative": [
            f"The final residual search reaches {len(flow_result.min_cut['source_side'])} node(s) on the source side and leaves {len(flow_result.min_cut['sink_side'])} node(s) on the sink side.",
            f"Edges that cross that partition have total capacity {cut_capacity}, which {'matches' if flow_result.max_flow == cut_capacity else 'does not match'} the computed max flow of {flow_result.max_flow}.",
            "Every source-to-sink residual path is blocked once those cut edges are saturated, giving a concrete max-flow/min-cut certificate.",
        ],
    }


def build_matching_explanation(matching_result: MatchingResult) -> dict[str, Any]:
    cover = matching_result.minimum_vertex_cover
    return {
        "match_count": len(matching_result.matches),
        "minimum_vertex_cover_size": cover["size"],
        "konig_theorem_check": cover["konig_theorem_check"],
        "cover_vertices": [{"side": "left", "node": node} for node in cover["left"]]
        + [{"side": "right", "node": node} for node in cover["right"]],
        "reachable_from_unmatched_left": cover["reachable_from_unmatched_left"],
        "narrative": [
            f"The matching contains {len(matching_result.matches)} edge(s), and the recovered minimum vertex cover contains {cover['size']} vertex/vertices.",
            "Unmatched left vertices seed alternating-path reachability; left vertices not reached and right vertices that are reached form the minimum cover.",
            f"König's theorem check is {'satisfied' if cover['konig_theorem_check'] else 'not satisfied'}, so the cover size matches the matching size.",
        ],
    }


MATCH_SOURCE = "__source__"
MATCH_SINK = "__sink__"
DEFAULT_ALGORITHM = "edmonds-karp"
SUPPORTED_ALGORITHMS = ("edmonds-karp", "dinic")


def load_graph(path: Path) -> tuple[list[str], list[Edge], str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    nodes = payload.get("nodes")
    source = payload.get("source")
    sink = payload.get("sink")
    raw_edges = payload.get("edges")

    if not isinstance(nodes, list) or not nodes:
        raise ValueError("graph must include a non-empty 'nodes' list")
    if not isinstance(raw_edges, list):
        raise ValueError("graph must include an 'edges' list")
    if source not in nodes or sink not in nodes:
        raise ValueError("source and sink must both appear in nodes")
    if source == sink:
        raise ValueError("source and sink must differ")

    seen_nodes = set(nodes)
    edges: list[Edge] = []
    for item in raw_edges:
        if not isinstance(item, dict):
            raise ValueError("each edge must be an object")
        edge = Edge(str(item.get("source")), str(item.get("target")), int(item.get("capacity", -1)))
        if edge.source not in seen_nodes or edge.target not in seen_nodes:
            raise ValueError("edge endpoints must appear in nodes")
        if edge.source == edge.target:
            raise ValueError("self-loops are not supported")
        if edge.capacity < 0:
            raise ValueError("edge capacity must be non-negative")
        edges.append(edge)
    return [str(node) for node in nodes], edges, str(source), str(sink)


def load_bipartite_graph(path: Path) -> tuple[list[str], list[str], list[tuple[str, str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    left = payload.get("left")
    right = payload.get("right")
    raw_edges = payload.get("edges")

    if not isinstance(left, list) or not left:
        raise ValueError("matching graph must include a non-empty 'left' list")
    if not isinstance(right, list) or not right:
        raise ValueError("matching graph must include a non-empty 'right' list")
    if not isinstance(raw_edges, list):
        raise ValueError("matching graph must include an 'edges' list")

    left_nodes = [str(node) for node in left]
    right_nodes = [str(node) for node in right]
    if len(set(left_nodes)) != len(left_nodes) or len(set(right_nodes)) != len(right_nodes):
        raise ValueError("left and right partitions must not contain duplicate node names")
    reserved = {MATCH_SOURCE, MATCH_SINK}
    if reserved & set(left_nodes + right_nodes):
        raise ValueError("matching graphs may not use reserved internal node names")
    left_set = set(left_nodes)
    right_set = set(right_nodes)
    if left_set & right_set:
        raise ValueError("left and right partitions must be disjoint")

    edges: list[tuple[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()
    for item in raw_edges:
        if not isinstance(item, dict):
            raise ValueError("each matching edge must be an object")
        source = str(item.get("source"))
        target = str(item.get("target"))
        if source not in left_set or target not in right_set:
            raise ValueError("matching edges must point from left nodes to right nodes")
        pair = (source, target)
        if pair in seen_edges:
            continue
        seen_edges.add(pair)
        edges.append(pair)
    return left_nodes, right_nodes, edges


def build_bipartite_matching_flow(
    left: list[str], right: list[str], edges: list[tuple[str, str]]
) -> tuple[list[str], list[Edge], str, str]:
    nodes = [MATCH_SOURCE, *left, *right, MATCH_SINK]
    flow_edges = [Edge(MATCH_SOURCE, node, 1) for node in left]
    flow_edges.extend(Edge(source, target, 1) for source, target in edges)
    flow_edges.extend(Edge(node, MATCH_SINK, 1) for node in right)
    return nodes, flow_edges, MATCH_SOURCE, MATCH_SINK


def derive_minimum_vertex_cover(
    left: list[str], right: list[str], edges: list[tuple[str, str]], matches: list[dict[str, str]]
) -> dict[str, Any]:
    left_nodes = sorted(left)
    right_nodes = sorted(right)
    edge_set = set(edges)
    matched_left_to_right = {item["left"]: item["right"] for item in matches}
    matched_right_to_left = {item["right"]: item["left"] for item in matches}
    unmatched_left = sorted(node for node in left_nodes if node not in matched_left_to_right)

    reachable_left: set[str] = set()
    reachable_right: set[str] = set()
    queue: deque[tuple[str, str]] = deque(("L", node) for node in unmatched_left)

    while queue:
        partition, node = queue.popleft()
        if partition == "L":
            if node in reachable_left:
                continue
            reachable_left.add(node)
            for right_node in right_nodes:
                if (node, right_node) not in edge_set:
                    continue
                if matched_left_to_right.get(node) == right_node:
                    continue
                if right_node not in reachable_right:
                    queue.append(("R", right_node))
        else:
            if node in reachable_right:
                continue
            reachable_right.add(node)
            matched_left = matched_right_to_left.get(node)
            if matched_left is not None and matched_left not in reachable_left:
                queue.append(("L", matched_left))

    cover_left = sorted(node for node in left_nodes if node not in reachable_left)
    cover_right = sorted(node for node in reachable_right)
    return {
        "left": cover_left,
        "right": cover_right,
        "size": len(cover_left) + len(cover_right),
        "reachable_from_unmatched_left": {
            "left": sorted(reachable_left),
            "right": sorted(reachable_right),
        },
        "konig_theorem_check": len(matches) == len(cover_left) + len(cover_right),
    }


def solve_bipartite_matching(
    left: list[str], right: list[str], edges: list[tuple[str, str]], *, algorithm: str = DEFAULT_ALGORITHM
) -> MatchingResult:
    nodes, flow_edges, source, sink = build_bipartite_matching_flow(left, right, edges)
    flow_result = solve_max_flow(nodes, flow_edges, source, sink, algorithm=algorithm)
    matches: list[dict[str, str]] = []
    matched_left: set[str] = set()
    matched_right: set[str] = set()
    edge_lookup = {(item["source"], item["target"]): item for item in flow_result.edge_flows}

    for left_node, right_node in sorted(edges):
        edge = edge_lookup.get((left_node, right_node))
        if edge and edge["flow"] == 1:
            matches.append({"left": left_node, "right": right_node})
            matched_left.add(left_node)
            matched_right.add(right_node)

    minimum_vertex_cover = derive_minimum_vertex_cover(left, right, edges, matches)

    return MatchingResult(
        left_partition=sorted(left),
        right_partition=sorted(right),
        matches=matches,
        unmatched_left=sorted(node for node in left if node not in matched_left),
        unmatched_right=sorted(node for node in right if node not in matched_right),
        minimum_vertex_cover=minimum_vertex_cover,
        flow=flow_result.to_dict(),
    )


def _build_capacity_maps(
    nodes: list[str], edges: list[Edge]
) -> tuple[dict[str, dict[str, int]], list[tuple[str, str]], dict[str, set[str]]]:
    capacities: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    original_edges: list[tuple[str, str]] = []
    neighbors: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in edges:
        capacities[edge.source][edge.target] += edge.capacity
        capacities[edge.target]
        neighbors[edge.source].add(edge.target)
        neighbors[edge.target].add(edge.source)
        original_edges.append((edge.source, edge.target))
    return capacities, original_edges, neighbors


def _build_residual(
    nodes: list[str], capacities: dict[str, dict[str, int]], neighbors: dict[str, set[str]]
) -> dict[str, dict[str, int]]:
    residual: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for u in nodes:
        capacities[u]
        for v, capacity in capacities[u].items():
            residual[u][v] = capacity
            residual[v][u] += 0
            neighbors[u].add(v)
            neighbors[v].add(u)
    return residual


def _compute_flow_result(
    *,
    nodes: list[str],
    capacities: dict[str, dict[str, int]],
    original_edges: list[tuple[str, str]],
    residual: dict[str, dict[str, int]],
    neighbors: dict[str, set[str]],
    source: str,
    sink: str,
    max_flow: int,
    augmenting_paths: list[dict[str, Any]],
    algorithm: str,
    phases: int | None = None,
) -> FlowResult:
    reachable: set[str] = set()
    queue = deque([source])
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        for nxt in sorted(neighbors[current]):
            if residual[current][nxt] > 0 and nxt not in reachable:
                queue.append(nxt)

    edge_flows: list[dict[str, Any]] = []
    for edge in sorted(set(original_edges)):
        capacity = capacities[edge[0]][edge[1]]
        flow = capacity - residual[edge[0]][edge[1]]
        edge_flows.append(
            {
                "source": edge[0],
                "target": edge[1],
                "capacity": capacity,
                "flow": flow,
            }
        )

    cut_source_side = sorted(reachable)
    cut_sink_side = sorted(node for node in nodes if node not in reachable)
    return FlowResult(
        source=source,
        sink=sink,
        algorithm=algorithm,
        max_flow=max_flow,
        augmenting_paths=augmenting_paths,
        edge_flows=edge_flows,
        min_cut={"source_side": cut_source_side, "sink_side": cut_sink_side},
        phases=phases,
    )


def solve_max_flow(
    nodes: list[str], edges: list[Edge], source: str, sink: str, *, algorithm: str = DEFAULT_ALGORITHM
) -> FlowResult:
    if algorithm == "edmonds-karp":
        return solve_max_flow_edmonds_karp(nodes, edges, source, sink)
    if algorithm == "dinic":
        return solve_max_flow_dinic(nodes, edges, source, sink)
    raise ValueError(f"unsupported algorithm: {algorithm}")


def solve_max_flow_edmonds_karp(nodes: list[str], edges: list[Edge], source: str, sink: str) -> FlowResult:
    capacities, original_edges, neighbors = _build_capacity_maps(nodes, edges)
    residual = _build_residual(nodes, capacities, neighbors)
    augmenting_paths: list[dict[str, Any]] = []
    max_flow = 0

    while True:
        parent: dict[str, str | None] = {source: None}
        queue: deque[str] = deque([source])

        while queue and sink not in parent:
            current = queue.popleft()
            for nxt in sorted(neighbors[current]):
                if nxt in parent:
                    continue
                if residual[current][nxt] <= 0:
                    continue
                parent[nxt] = current
                queue.append(nxt)
                if nxt == sink:
                    break

        if sink not in parent:
            break

        path: list[str] = []
        bottleneck = float("inf")
        cursor = sink
        while cursor is not None:
            path.append(cursor)
            previous = parent[cursor]
            if previous is not None:
                bottleneck = min(bottleneck, residual[previous][cursor])
            cursor = previous
        path.reverse()
        bottleneck_int = int(bottleneck)

        for left_node, right_node in zip(path, path[1:]):
            residual[left_node][right_node] -= bottleneck_int
            residual[right_node][left_node] += bottleneck_int

        max_flow += bottleneck_int
        augmenting_paths.append({"path": path, "bottleneck": bottleneck_int})

    return _compute_flow_result(
        nodes=nodes,
        capacities=capacities,
        original_edges=original_edges,
        residual=residual,
        neighbors=neighbors,
        source=source,
        sink=sink,
        max_flow=max_flow,
        augmenting_paths=augmenting_paths,
        algorithm="edmonds-karp",
    )


def solve_max_flow_dinic(nodes: list[str], edges: list[Edge], source: str, sink: str) -> FlowResult:
    capacities, original_edges, neighbors = _build_capacity_maps(nodes, edges)
    residual = _build_residual(nodes, capacities, neighbors)
    max_flow = 0
    phases = 0
    augmenting_paths: list[dict[str, Any]] = []

    while True:
        level: dict[str, int] = {source: 0}
        queue: deque[str] = deque([source])
        while queue:
            current = queue.popleft()
            for nxt in sorted(neighbors[current]):
                if nxt in level or residual[current][nxt] <= 0:
                    continue
                level[nxt] = level[current] + 1
                queue.append(nxt)
        if sink not in level:
            break
        phases += 1
        next_index = {node: 0 for node in nodes}
        ordered_neighbors = {node: sorted(neighbors[node]) for node in nodes}

        def send_flow(current: str, pushed: int, path: list[str]) -> int:
            if current == sink:
                augmenting_paths.append({"path": path.copy(), "bottleneck": pushed, "phase": phases})
                return pushed
            neighbors_for_node = ordered_neighbors[current]
            while next_index[current] < len(neighbors_for_node):
                nxt = neighbors_for_node[next_index[current]]
                if residual[current][nxt] > 0 and level.get(nxt) == level[current] + 1:
                    bottleneck = send_flow(nxt, min(pushed, residual[current][nxt]), path + [nxt])
                    if bottleneck > 0:
                        residual[current][nxt] -= bottleneck
                        residual[nxt][current] += bottleneck
                        return bottleneck
                next_index[current] += 1
            return 0

        while True:
            pushed = send_flow(source, 10**18, [source])
            if pushed == 0:
                break
            max_flow += pushed

    return _compute_flow_result(
        nodes=nodes,
        capacities=capacities,
        original_edges=original_edges,
        residual=residual,
        neighbors=neighbors,
        source=source,
        sink=sink,
        max_flow=max_flow,
        augmenting_paths=augmenting_paths,
        algorithm="dinic",
        phases=phases,
    )


def generate_random_flow_graph(
    *, seed: int, node_count: int, edge_probability: float, capacity_min: int = 1, capacity_max: int = 20
) -> tuple[list[str], list[Edge], str, str]:
    if node_count < 2:
        raise ValueError("node_count must be at least 2")
    if not 0 < edge_probability <= 1:
        raise ValueError("edge_probability must be within (0, 1]")
    if capacity_min <= 0 or capacity_max < capacity_min:
        raise ValueError("capacity bounds must be positive and ordered")

    rng = random.Random(seed)
    nodes = [f"n{i}" for i in range(node_count)]
    source = nodes[0]
    sink = nodes[-1]
    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()

    for left, right in zip(nodes, nodes[1:]):
        capacity = rng.randint(capacity_min, capacity_max)
        edge = (left, right)
        seen.add(edge)
        edges.append(Edge(left, right, capacity))

    for i, left in enumerate(nodes[:-1]):
        for right in nodes[i + 1 :]:
            if (left, right) in seen:
                continue
            if rng.random() <= edge_probability:
                seen.add((left, right))
                edges.append(Edge(left, right, rng.randint(capacity_min, capacity_max)))

    return nodes, edges, source, sink


def benchmark_algorithms(
    *,
    node_count: int,
    edge_probability: float,
    trials: int,
    seed: int,
    capacity_min: int = 1,
    capacity_max: int = 20,
) -> dict[str, Any]:
    if trials <= 0:
        raise ValueError("trials must be positive")

    per_algorithm: dict[str, list[float]] = {name: [] for name in SUPPORTED_ALGORITHMS}
    phase_counts: list[int] = []
    augmentation_counts: dict[str, list[int]] = {name: [] for name in SUPPORTED_ALGORITHMS}
    flow_values: list[int] = []
    trial_payloads: list[dict[str, Any]] = []

    for trial_index in range(trials):
        trial_seed = seed + trial_index
        nodes, edges, source, sink = generate_random_flow_graph(
            seed=trial_seed,
            node_count=node_count,
            edge_probability=edge_probability,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        )
        trial_result: dict[str, Any] = {"trial": trial_index + 1, "seed": trial_seed, "edge_count": len(edges)}
        reference_flow: int | None = None
        for algorithm in SUPPORTED_ALGORITHMS:
            start = time.perf_counter()
            result = solve_max_flow(nodes, edges, source, sink, algorithm=algorithm)
            elapsed_ms = (time.perf_counter() - start) * 1000
            per_algorithm[algorithm].append(elapsed_ms)
            augmentation_counts[algorithm].append(len(result.augmenting_paths))
            if algorithm == "dinic" and result.phases is not None:
                phase_counts.append(result.phases)
            if reference_flow is None:
                reference_flow = result.max_flow
                flow_values.append(result.max_flow)
            elif result.max_flow != reference_flow:
                raise AssertionError(
                    f"algorithm mismatch on seed {trial_seed}: {algorithm}={result.max_flow}, expected={reference_flow}"
                )
            trial_result[algorithm] = {
                "max_flow": result.max_flow,
                "elapsed_ms": round(elapsed_ms, 3),
                "augmentations": len(result.augmenting_paths),
            }
            if result.phases is not None:
                trial_result[algorithm]["phases"] = result.phases
        trial_payloads.append(trial_result)

    def summarize(samples: list[float]) -> dict[str, float]:
        return {
            "min_ms": round(min(samples), 3),
            "median_ms": round(statistics.median(samples), 3),
            "max_ms": round(max(samples), 3),
            "mean_ms": round(statistics.fmean(samples), 3),
        }

    summary: dict[str, Any] = {}
    edmonds_mean = statistics.fmean(per_algorithm["edmonds-karp"])
    dinic_mean = statistics.fmean(per_algorithm["dinic"])
    for algorithm in SUPPORTED_ALGORITHMS:
        summary[algorithm] = {
            **summarize(per_algorithm[algorithm]),
            "mean_augmentations": round(statistics.fmean(augmentation_counts[algorithm]), 2),
        }
    if phase_counts:
        summary["dinic"]["mean_phases"] = round(statistics.fmean(phase_counts), 2)
    summary["speedup_ratio"] = round(edmonds_mean / dinic_mean, 3) if dinic_mean > 0 else None

    return {
        "command": "benchmark",
        "generator": {
            "node_count": node_count,
            "edge_probability": edge_probability,
            "capacity_range": [capacity_min, capacity_max],
            "trials": trials,
            "seed": seed,
        },
        "algorithms": list(SUPPORTED_ALGORITHMS),
        "trial_flows": flow_values,
        "trials": trial_payloads,
        "summary": summary,
    }


def render_flow_dot(flow_result: FlowResult, *, graph_name: str = "network_flow") -> str:
    source_side = set(flow_result.min_cut["source_side"])
    sink_side = set(flow_result.min_cut["sink_side"])
    cut_edges = {
        (item["source"], item["target"])
        for item in flow_result.edge_flows
        if item["source"] in source_side and item["target"] in sink_side
    }

    lines = [f'digraph "{graph_name}" {{', "  rankdir=LR;", '  node [shape=circle];']
    for node in flow_result.min_cut["source_side"]:
        attrs = ['style="filled"', 'fillcolor="lightblue"']
        if node == flow_result.source:
            attrs.append('peripheries=2')
        lines.append(f'  "{node}" [{", ".join(attrs)}];')
    for node in flow_result.min_cut["sink_side"]:
        attrs = ['style="filled"', 'fillcolor="lightgoldenrod1"']
        if node == flow_result.sink:
            attrs.append('peripheries=2')
        lines.append(f'  "{node}" [{", ".join(attrs)}];')

    for edge in flow_result.edge_flows:
        attrs = [f'label="{edge["flow"]}/{edge["capacity"]}"']
        if (edge["source"], edge["target"]) in cut_edges:
            attrs.extend(['color="crimson"', 'penwidth=2'])
        elif edge["flow"] > 0:
            attrs.extend(['color="navy"', 'penwidth=2'])
        lines.append(f'  "{edge["source"]}" -> "{edge["target"]}" [{", ".join(attrs)}];')

    lines.append("}")
    return "\n".join(lines)


def render_matching_dot(matching_result: MatchingResult, *, graph_name: str = "bipartite_matching") -> str:
    matched_pairs = {(item["left"], item["right"]) for item in matching_result.matches}
    cover_left = set(matching_result.minimum_vertex_cover["left"])
    cover_right = set(matching_result.minimum_vertex_cover["right"])
    flow = matching_result.flow
    flow_edges = {
        (item["source"], item["target"]): item for item in flow["edge_flows"]
    }

    lines = [f'digraph "{graph_name}" {{', "  rankdir=LR;", '  graph [splines=true];']
    lines.append('  node [shape=circle, style="filled", fillcolor="lightsteelblue1"];')
    for node in matching_result.left_partition:
        attrs = []
        if node in matching_result.unmatched_left:
            attrs.append('fillcolor="mistyrose"')
        if node in cover_left:
            attrs.append('peripheries=2')
        lines.append(f'  "{node}" [{", ".join(attrs)}];' if attrs else f'  "{node}";')

    lines.append('  node [shape=box, style="filled", fillcolor="honeydew2"];')
    for node in matching_result.right_partition:
        attrs = []
        if node in matching_result.unmatched_right:
            attrs.append('fillcolor="moccasin"')
        if node in cover_right:
            attrs.append('peripheries=2')
        lines.append(f'  "{node}" [{", ".join(attrs)}];' if attrs else f'  "{node}";')

    for left_node in matching_result.left_partition:
        edge = flow_edges.get((MATCH_SOURCE, left_node))
        if edge and edge["flow"] == 1:
            lines.append(f'  "source" -> "{left_node}" [style="dashed", color="gray50", label="1"];')
    for left_node, right_node in sorted(matched_pairs):
        lines.append(
            f'  "{left_node}" -> "{right_node}" [color="forestgreen", penwidth=3, label="match"];'
        )
    for edge_key, edge in sorted(flow_edges.items()):
        source, target = edge_key
        if source in {MATCH_SOURCE, MATCH_SINK} or target in {MATCH_SOURCE, MATCH_SINK}:
            continue
        if edge_key in matched_pairs:
            continue
        attrs = ['color="gray60"']
        if edge["flow"] > 0:
            attrs.extend(['color="navy"', 'penwidth=2', f'label="{edge["flow"]}/{edge["capacity"]}"'])
        lines.append(f'  "{source}" -> "{target}" [{", ".join(attrs)}];')
    for node in matching_result.right_partition:
        edge = flow_edges.get((node, MATCH_SINK))
        if edge and edge["flow"] == 1:
            lines.append(f'  "{node}" -> "sink" [style="dashed", color="gray50", label="1"];')

    lines.append('  "source" [shape=diamond, style="filled", fillcolor="white"];')
    lines.append('  "sink" [shape=diamond, style="filled", fillcolor="white"];')
    lines.append("}")
    return "\n".join(lines)


def write_dot_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents + "\n", encoding="utf-8")


def add_explain_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--explain",
        action="store_true",
        help="include a compact proof-style explanation of the computed result",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Solve max-flow graphs and bipartite matchings.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser("solve", help="solve a graph JSON file")
    solve_parser.add_argument("graph", type=Path, help="path to graph JSON")
    solve_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    solve_parser.add_argument("--algorithm", choices=SUPPORTED_ALGORITHMS, default=DEFAULT_ALGORITHM)
    solve_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the solved flow graph")
    add_explain_argument(solve_parser)

    demo_parser = subparsers.add_parser("demo", help="run the bundled sample graph")
    demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    demo_parser.add_argument("--algorithm", choices=SUPPORTED_ALGORITHMS, default=DEFAULT_ALGORITHM)
    demo_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the sample flow graph")
    add_explain_argument(demo_parser)

    match_parser = subparsers.add_parser("match", help="solve a bipartite matching JSON file")
    match_parser.add_argument("graph", type=Path, help="path to bipartite graph JSON")
    match_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    match_parser.add_argument("--algorithm", choices=SUPPORTED_ALGORITHMS, default=DEFAULT_ALGORITHM)
    match_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the solved matching graph")
    add_explain_argument(match_parser)

    match_demo_parser = subparsers.add_parser("match-demo", help="run the bundled matching sample")
    match_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    match_demo_parser.add_argument("--algorithm", choices=SUPPORTED_ALGORITHMS, default=DEFAULT_ALGORITHM)
    match_demo_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the sample matching graph")
    add_explain_argument(match_demo_parser)

    benchmark_parser = subparsers.add_parser("benchmark", help="compare Edmonds-Karp vs Dinic on generated graphs")
    benchmark_parser.add_argument("--nodes", type=int, default=24, help="number of nodes in each generated DAG")
    benchmark_parser.add_argument("--edge-probability", type=float, default=0.18, help="probability for extra forward edges")
    benchmark_parser.add_argument("--trials", type=int, default=5, help="how many generated graphs to test")
    benchmark_parser.add_argument("--seed", type=int, default=42, help="base RNG seed for reproducible graphs")
    benchmark_parser.add_argument("--capacity-min", type=int, default=1)
    benchmark_parser.add_argument("--capacity-max", type=int, default=20)
    benchmark_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    return parser


def run_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "solve":
        graph_path = args.graph
        nodes, edges, source, sink = load_graph(graph_path)
        flow_result = solve_max_flow(nodes, edges, source, sink, algorithm=args.algorithm)
        payload = {"command": args.command, "graph": str(graph_path), **flow_result.to_dict()}
        if getattr(args, "explain", False):
            payload["explanation"] = build_flow_explanation(flow_result)
        if args.dot_out:
            write_dot_output(args.dot_out, render_flow_dot(flow_result, graph_name=graph_path.stem))
            payload["dot_output"] = str(args.dot_out)
        return payload

    if args.command == "demo":
        graph_path = Path(__file__).with_name("sample_graph.json")
        nodes, edges, source, sink = load_graph(graph_path)
        flow_result = solve_max_flow(nodes, edges, source, sink, algorithm=args.algorithm)
        payload = {"command": args.command, "graph": str(graph_path), **flow_result.to_dict()}
        if getattr(args, "explain", False):
            payload["explanation"] = build_flow_explanation(flow_result)
        if args.dot_out:
            write_dot_output(args.dot_out, render_flow_dot(flow_result, graph_name=graph_path.stem))
            payload["dot_output"] = str(args.dot_out)
        return payload

    if args.command == "match":
        graph_path = args.graph
        left, right, edges = load_bipartite_graph(graph_path)
        matching_result = solve_bipartite_matching(left, right, edges, algorithm=args.algorithm)
        payload = {"command": args.command, "graph": str(graph_path), **matching_result.to_dict()}
        if getattr(args, "explain", False):
            payload["explanation"] = build_matching_explanation(matching_result)
        if args.dot_out:
            write_dot_output(args.dot_out, render_matching_dot(matching_result, graph_name=graph_path.stem))
            payload["dot_output"] = str(args.dot_out)
        return payload

    if args.command == "match-demo":
        graph_path = Path(__file__).with_name("sample_matching_graph.json")
        left, right, edges = load_bipartite_graph(graph_path)
        matching_result = solve_bipartite_matching(left, right, edges, algorithm=args.algorithm)
        payload = {"command": args.command, "graph": str(graph_path), **matching_result.to_dict()}
        if getattr(args, "explain", False):
            payload["explanation"] = build_matching_explanation(matching_result)
        if args.dot_out:
            write_dot_output(args.dot_out, render_matching_dot(matching_result, graph_name=graph_path.stem))
            payload["dot_output"] = str(args.dot_out)
        return payload

    return benchmark_algorithms(
        node_count=args.nodes,
        edge_probability=args.edge_probability,
        trials=args.trials,
        seed=args.seed,
        capacity_min=args.capacity_min,
        capacity_max=args.capacity_max,
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = run_command(args)
    if getattr(args, "pretty", False):
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
