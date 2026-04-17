from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import textwrap
import time
from datetime import UTC, datetime
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
BENCHMARK_GRAPH_FAMILIES = ("dag", "dense", "layered")
BENCHMARK_GRAPH_MIN_NODES = {
    "dag": 2,
    "dense": 4,
    "layered": 6,
}


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


def validate_benchmark_graph_inputs(
    *, node_count: int, edge_probability: float, capacity_min: int, capacity_max: int
) -> None:
    if node_count < 2:
        raise ValueError("node_count must be at least 2")
    if not 0 < edge_probability <= 1:
        raise ValueError("edge_probability must be within (0, 1]")
    if capacity_min <= 0 or capacity_max < capacity_min:
        raise ValueError("capacity bounds must be positive and ordered")


def append_unique_edge(
    edges: list[Edge],
    seen: set[tuple[str, str]],
    source: str,
    target: str,
    capacity: int,
) -> None:
    if source == target or (source, target) in seen:
        return
    seen.add((source, target))
    edges.append(Edge(source, target, capacity))


def generate_random_flow_graph(
    *, seed: int, node_count: int, edge_probability: float, capacity_min: int = 1, capacity_max: int = 20
) -> tuple[list[str], list[Edge], str, str]:
    validate_benchmark_graph_inputs(
        node_count=node_count,
        edge_probability=edge_probability,
        capacity_min=capacity_min,
        capacity_max=capacity_max,
    )

    rng = random.Random(seed)
    nodes = [f"n{i}" for i in range(node_count)]
    source = nodes[0]
    sink = nodes[-1]
    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()

    for left, right in zip(nodes, nodes[1:]):
        append_unique_edge(edges, seen, left, right, rng.randint(capacity_min, capacity_max))

    for i, left in enumerate(nodes[:-1]):
        for right in nodes[i + 1 :]:
            if rng.random() <= edge_probability:
                append_unique_edge(edges, seen, left, right, rng.randint(capacity_min, capacity_max))

    return nodes, edges, source, sink


def generate_dense_flow_graph(
    *, seed: int, node_count: int, edge_probability: float, capacity_min: int = 1, capacity_max: int = 20
) -> tuple[list[str], list[Edge], str, str]:
    validate_benchmark_graph_inputs(
        node_count=node_count,
        edge_probability=edge_probability,
        capacity_min=capacity_min,
        capacity_max=capacity_max,
    )
    if node_count < BENCHMARK_GRAPH_MIN_NODES["dense"]:
        raise ValueError(f"dense benchmark family requires at least {BENCHMARK_GRAPH_MIN_NODES['dense']} nodes")

    rng = random.Random(seed)
    nodes = [f"n{i}" for i in range(node_count)]
    source = nodes[0]
    sink = nodes[-1]
    middle = nodes[1:-1]
    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()

    for left, right in zip(nodes, nodes[1:]):
        append_unique_edge(edges, seen, left, right, rng.randint(capacity_min, capacity_max))

    for node in middle:
        append_unique_edge(edges, seen, source, node, rng.randint(capacity_min, capacity_max))
        append_unique_edge(edges, seen, node, sink, rng.randint(capacity_min, capacity_max))
    for left, right in zip(middle[1:], middle[:-1]):
        append_unique_edge(edges, seen, left, right, rng.randint(capacity_min, capacity_max))

    backward_probability = min(1.0, max(0.2, edge_probability * 0.75))
    forward_probability = min(1.0, max(edge_probability, 0.55))
    for index, left in enumerate(middle):
        for right in middle[index + 1 :]:
            if rng.random() <= forward_probability:
                append_unique_edge(edges, seen, left, right, rng.randint(capacity_min, capacity_max))
            if rng.random() <= backward_probability:
                append_unique_edge(edges, seen, right, left, rng.randint(capacity_min, capacity_max))

    return nodes, edges, source, sink


def generate_layered_flow_graph(
    *, seed: int, node_count: int, edge_probability: float, capacity_min: int = 1, capacity_max: int = 20
) -> tuple[list[str], list[Edge], str, str]:
    validate_benchmark_graph_inputs(
        node_count=node_count,
        edge_probability=edge_probability,
        capacity_min=capacity_min,
        capacity_max=capacity_max,
    )
    if node_count < BENCHMARK_GRAPH_MIN_NODES["layered"]:
        raise ValueError(f"layered benchmark family requires at least {BENCHMARK_GRAPH_MIN_NODES['layered']} nodes")

    rng = random.Random(seed)
    nodes = [f"n{i}" for i in range(node_count)]
    source = nodes[0]
    sink = nodes[-1]
    middle = nodes[1:-1]
    layer_count = max(2, round(math.sqrt(len(middle))))
    layer_width = math.ceil(len(middle) / layer_count)
    layers = [middle[offset : offset + layer_width] for offset in range(0, len(middle), layer_width)]
    if len(layers) == 1:
        midpoint = max(1, len(middle) // 2)
        layers = [middle[:midpoint], middle[midpoint:]]
        layers = [layer for layer in layers if layer]

    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()
    internal_capacity_max = min(capacity_max, max(capacity_min, 3))

    for node in layers[0]:
        append_unique_edge(edges, seen, source, node, rng.randint(capacity_min, capacity_max))
    for left_layer, right_layer in zip(layers, layers[1:]):
        for left in left_layer:
            for right in right_layer:
                append_unique_edge(edges, seen, left, right, rng.randint(capacity_min, internal_capacity_max))
    for node in layers[-1]:
        append_unique_edge(edges, seen, node, sink, rng.randint(capacity_min, capacity_max))

    for start_index, left_layer in enumerate(layers[:-2]):
        for later_layer in layers[start_index + 2 :]:
            for left in left_layer:
                for right in later_layer:
                    if rng.random() <= edge_probability:
                        append_unique_edge(edges, seen, left, right, rng.randint(capacity_min, internal_capacity_max))

    return nodes, edges, source, sink


def generate_benchmark_flow_graph(
    *,
    graph_family: str,
    seed: int,
    node_count: int,
    edge_probability: float,
    capacity_min: int = 1,
    capacity_max: int = 20,
) -> tuple[list[str], list[Edge], str, str]:
    if graph_family == "dag":
        return generate_random_flow_graph(
            seed=seed,
            node_count=node_count,
            edge_probability=edge_probability,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        )
    if graph_family == "dense":
        return generate_dense_flow_graph(
            seed=seed,
            node_count=node_count,
            edge_probability=edge_probability,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        )
    if graph_family == "layered":
        return generate_layered_flow_graph(
            seed=seed,
            node_count=node_count,
            edge_probability=edge_probability,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        )
    raise ValueError(f"unsupported benchmark graph family: {graph_family}")


def benchmark_algorithms(
    *,
    node_count: int,
    edge_probability: float,
    trials: int,
    seed: int,
    capacity_min: int = 1,
    capacity_max: int = 20,
    graph_family: str = "dag",
) -> dict[str, Any]:
    if trials <= 0:
        raise ValueError("trials must be positive")

    per_algorithm: dict[str, list[float]] = {name: [] for name in SUPPORTED_ALGORITHMS}
    phase_counts: list[int] = []
    augmentation_counts: dict[str, list[int]] = {name: [] for name in SUPPORTED_ALGORITHMS}
    flow_values: list[int] = []
    trial_payloads: list[dict[str, Any]] = []

    if graph_family not in BENCHMARK_GRAPH_FAMILIES:
        raise ValueError(f"graph_family must be one of {', '.join(BENCHMARK_GRAPH_FAMILIES)}")

    for trial_index in range(trials):
        trial_seed = seed + trial_index
        nodes, edges, source, sink = generate_benchmark_flow_graph(
            graph_family=graph_family,
            seed=trial_seed,
            node_count=node_count,
            edge_probability=edge_probability,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        )
        max_edges = max(1, node_count * (node_count - 1))
        trial_result: dict[str, Any] = {
            "trial": trial_index + 1,
            "seed": trial_seed,
            "graph_family": graph_family,
            "edge_count": len(edges),
            "edge_density": round(len(edges) / max_edges, 3),
        }
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
            "graph_family": graph_family,
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


def _svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _svg_text(x: float, y: float, text: str, *, size: int = 14, weight: str = "normal", fill: str = "#111827") -> str:
    font_family = 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}" font-family=\'{font_family}\'>{_svg_escape(text)}</text>'
    )


def _truncate_svg_text(text: str, limit: int = 72) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _wrap_svg_text(text: str, *, max_chars: int = 58) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return ["(none)"]
    return textwrap.wrap(
        normalized,
        width=max_chars,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [normalized]


def _svg_add_wrapped_text(
    parts: list[str],
    x: float,
    y: float,
    text: str,
    *,
    max_chars: int = 58,
    line_height: int = 18,
    size: int = 13,
    weight: str = "normal",
    fill: str = "#334155",
) -> float:
    lines = _wrap_svg_text(text, max_chars=max_chars)
    for index, line in enumerate(lines):
        parts.append(_svg_text(x, y + index * line_height, line, size=size, weight=weight, fill=fill))
    return y + max(0, len(lines) - 1) * line_height


def render_benchmark_markdown(report: dict[str, Any]) -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    generator = report["generator"]
    summary = report["summary"]
    trials = report["trials"]
    graph_family = generator["graph_family"]
    family_story = {
        "dag": "acyclic baseline graphs that keep the benchmark easy to reason about",
        "dense": "residual-heavy dense meshes that create more rerouting pressure",
        "layered": "cut-stress layered networks that highlight blocking-flow phases",
    }[graph_family]
    mean_density = round(statistics.fmean(trial["edge_density"] for trial in trials), 3)
    mean_flow = round(statistics.fmean(report["trial_flows"]), 2)
    speedup_ratio = summary["speedup_ratio"]
    ek_summary = summary["edmonds-karp"]
    dinic_summary = summary["dinic"]
    ek_aug = float(ek_summary["mean_augmentations"])
    dinic_aug = float(dinic_summary["mean_augmentations"])
    if dinic_aug < ek_aug:
        augmentation_story = "fewer augmenting-path pushes"
    elif dinic_aug > ek_aug:
        augmentation_story = "more augmenting-path pushes despite the runtime trade-off"
    else:
        augmentation_story = "the same average augmenting-path count"

    if speedup_ratio is None:
        headline = "Timing resolution was too small to compute a stable speedup ratio, so use the raw timing rows instead."
    elif speedup_ratio > 1.05:
        headline = (
            f"Dinic averaged {speedup_ratio:.2f}x faster than Edmonds-Karp on this {graph_family} suite while using {augmentation_story}."
        )
    elif speedup_ratio < 0.95:
        headline = (
            f"Edmonds-Karp averaged {1 / speedup_ratio:.2f}x faster than Dinic on this {graph_family} suite, which is a useful reminder that small pure-Python workloads can invert the asymptotic story."
        )
    else:
        headline = (
            f"Edmonds-Karp and Dinic landed within about {abs(1 - speedup_ratio) * 100:.1f}% of each other on this {graph_family} suite, so the structural metrics matter as much as raw wall-clock time."
        )

    lines = [
        "# Network-flow benchmark report card",
        "",
        f"- Generated: {generated}",
        f"- Graph family: `{graph_family}`",
        f"- Setup: `{generator['node_count']}` nodes · edge probability `{generator['edge_probability']}` · capacity range `{generator['capacity_range'][0]}-{generator['capacity_range'][1]}` · `{generator['trials']}` trial(s) · seed `{generator['seed']}`",
        f"- Family focus: {family_story}",
        "",
        "## Headline",
        "",
        f"- {headline}",
        f"- Mean max flow across trials: `{mean_flow}` with mean edge density `{mean_density}`.",
        f"- Edmonds-Karp mean runtime: `{ek_summary['mean_ms']}` ms with `{ek_summary['mean_augmentations']}` mean augmentations.",
        f"- Dinic mean runtime: `{dinic_summary['mean_ms']}` ms with `{dinic_summary['mean_augmentations']}` mean augmentations and `{dinic_summary.get('mean_phases', 0)}` mean phases.",
        "",
        "## Trial table",
        "",
        "| Trial | Seed | Edges | Density | Max flow | Edmonds-Karp ms | EK augmentations | Dinic ms | Dinic augmentations | Dinic phases |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for trial in trials:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(trial["trial"]),
                    str(trial["seed"]),
                    str(trial["edge_count"]),
                    str(trial["edge_density"]),
                    str(trial["edmonds-karp"]["max_flow"]),
                    str(trial["edmonds-karp"]["elapsed_ms"]),
                    str(trial["edmonds-karp"]["augmentations"]),
                    str(trial["dinic"]["elapsed_ms"]),
                    str(trial["dinic"]["augmentations"]),
                    str(trial["dinic"].get("phases", 0)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Portfolio talking points",
            "",
            f"- `{graph_family}` gives you a concrete benchmark story: {family_story}.",
            "- The trial rows verify both algorithms agreed on every max-flow value, so the timing comparison is paired with a correctness cross-check.",
            "- Augmentation counts and Dinic phase counts make the runtime story easier to explain than a single speed number in isolation.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_benchmark_svg(report: dict[str, Any]) -> str:
    generator = report["generator"]
    summary = report["summary"]
    trials = report["trials"]
    graph_family = generator["graph_family"]
    ek_summary = summary["edmonds-karp"]
    dinic_summary = summary["dinic"]
    mean_density = statistics.fmean(trial["edge_density"] for trial in trials)
    mean_flow = statistics.fmean(report["trial_flows"])
    speedup_ratio = summary["speedup_ratio"]

    width = 960
    height = 580
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Network-flow benchmark report card</title>',
        f'<desc id="desc">Benchmark summary for the {graph_family} graph family comparing Edmonds-Karp and Dinic.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 40, "Network-flow benchmark report card", size=28, weight="700"),
        _svg_text(
            28,
            66,
            (
                f"Family: {graph_family} · nodes={generator['node_count']} · edge probability={generator['edge_probability']} "
                f"· trials={generator['trials']} · seed={generator['seed']}"
            ),
            size=14,
            fill="#334155",
        ),
    ]

    cards = [
        (28, "Mean speedup", f"{speedup_ratio:.2f}x" if speedup_ratio is not None else "n/a", "EK mean / Dinic mean"),
        (258, "Mean max flow", f"{mean_flow:.2f}", "across benchmark trials"),
        (488, "Mean edge density", f"{mean_density:.3f}", "directed edge count / n(n-1)"),
        (718, "Dinic mean phases", f"{dinic_summary.get('mean_phases', 0):.2f}", "blocking-flow rounds"),
    ]
    for x, label, value, subtitle in cards:
        parts.append(f'<rect x="{x}" y="92" width="214" height="86" rx="16" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(x + 18, 120, label, size=13, weight="700", fill="#475569"))
        parts.append(_svg_text(x + 18, 152, value, size=28, weight="700", fill="#0f172a"))
        parts.append(_svg_text(x + 18, 170, subtitle, size=11, fill="#64748b"))

    def add_bar_panel(
        *,
        x: int,
        y: int,
        title: str,
        left_label: str,
        left_value: float,
        right_label: str,
        right_value: float,
        value_suffix: str,
    ) -> None:
        panel_width = 430
        panel_height = 292
        chart_left = x + 46
        chart_right = x + panel_width - 28
        chart_top = y + 58
        chart_bottom = y + panel_height - 54
        chart_height = chart_bottom - chart_top
        bar_width = 88
        max_value = max(left_value, right_value, 1.0)
        scale_max = max_value * 1.15
        left_bar_height = chart_height * (left_value / scale_max)
        right_bar_height = chart_height * (right_value / scale_max)
        left_x = chart_left + 54
        right_x = chart_left + 214
        left_y = chart_bottom - left_bar_height
        right_y = chart_bottom - right_bar_height

        parts.append(f'<rect x="{x}" y="{y}" width="{panel_width}" height="{panel_height}" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(x + 20, y + 34, title, size=18, weight="700"))
        parts.append(f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="#94a3b8" stroke-width="1.5" />')
        parts.append(f'<line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="#94a3b8" stroke-width="1.5" />')
        for tick in range(5):
            value = scale_max * tick / 4
            tick_y = chart_bottom - chart_height * tick / 4
            parts.append(f'<line x1="{chart_left}" y1="{tick_y:.1f}" x2="{chart_right}" y2="{tick_y:.1f}" stroke="#e2e8f0" stroke-width="1" />')
            parts.append(_svg_text(x + 8, tick_y + 4, f"{value:.2f}", size=10, fill="#64748b"))
        parts.append(f'<rect x="{left_x}" y="{left_y:.1f}" width="{bar_width}" height="{left_bar_height:.1f}" rx="10" fill="#2563eb" />')
        parts.append(f'<rect x="{right_x}" y="{right_y:.1f}" width="{bar_width}" height="{right_bar_height:.1f}" rx="10" fill="#0f766e" />')
        parts.append(_svg_text(left_x - 6, max(left_y - 8, chart_top + 12), f"{left_value:.2f}{value_suffix}", size=11, fill="#1d4ed8"))
        parts.append(_svg_text(right_x - 6, max(right_y - 8, chart_top + 12), f"{right_value:.2f}{value_suffix}", size=11, fill="#0f766e"))
        parts.append(_svg_text(left_x + 2, chart_bottom + 24, left_label, size=12, weight="700"))
        parts.append(_svg_text(right_x + 16, chart_bottom + 24, right_label, size=12, weight="700"))

    add_bar_panel(
        x=28,
        y=214,
        title="Elapsed time (mean ms)",
        left_label="Edmonds-Karp",
        left_value=float(ek_summary["mean_ms"]),
        right_label="Dinic",
        right_value=float(dinic_summary["mean_ms"]),
        value_suffix=" ms",
    )
    add_bar_panel(
        x=502,
        y=214,
        title="Augmenting paths (mean)",
        left_label="Edmonds-Karp",
        left_value=float(ek_summary["mean_augmentations"]),
        right_label="Dinic",
        right_value=float(dinic_summary["mean_augmentations"]),
        value_suffix="",
    )

    footer = (
        f"Flow values stayed in sync across {len(trials)} trial(s). Dinic mean phases: {dinic_summary.get('mean_phases', 0):.2f}."
    )
    parts.append(_svg_text(28, 532, footer, size=13, fill="#334155"))
    parts.append(_svg_text(28, 554, "Use this card alongside the Markdown report for interview-ready benchmark commentary.", size=12, fill="#64748b"))
    parts.append('</svg>')
    return "".join(parts) + "\n"


def render_flow_svg(flow_result: FlowResult, *, graph_name: str = "network_flow") -> str:
    explanation = build_flow_explanation(flow_result)
    width = 960
    height = 640
    source_side_text = ", ".join(flow_result.min_cut["source_side"])
    sink_side_text = ", ".join(flow_result.min_cut["sink_side"])
    cut_edges = explanation["cut_edges"]
    displayed_cut_edges = cut_edges[:5]
    hidden_cut_edges = max(0, len(cut_edges) - len(displayed_cut_edges))
    displayed_paths = flow_result.augmenting_paths[:6]
    hidden_paths = max(0, len(flow_result.augmenting_paths) - len(displayed_paths))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Max-flow proof card</title>',
        f'<desc id="desc">Proof-style summary card for {graph_name} showing the max flow, min cut, and augmenting paths.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 42, "Max-flow proof card", size=28, weight="700"),
        _svg_text(28, 68, f"Graph: {graph_name} · source={flow_result.source} · sink={flow_result.sink}", size=14, fill="#334155"),
    ]

    stat_cards = [
        (28, "Algorithm", flow_result.algorithm, "solver used for this certificate"),
        (258, "Max flow", str(flow_result.max_flow), "total flow from source to sink"),
        (488, "Cut capacity", str(explanation["min_cut_capacity"]), "must match the reported max flow"),
        (718, "Augmenting paths", str(len(flow_result.augmenting_paths)), (f"Dinic phases: {flow_result.phases}" if flow_result.phases is not None else "recorded during the solve")),
    ]
    for x, label, value, subtitle in stat_cards:
        parts.append(f'<rect x="{x}" y="94" width="214" height="86" rx="16" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(x + 18, 122, label, size=13, weight="700", fill="#475569"))
        parts.append(_svg_text(x + 18, 154, value, size=28, weight="700", fill="#0f172a"))
        parts.append(_svg_text(x + 18, 172, subtitle, size=11, fill="#64748b"))

    parts.append('<rect x="28" y="206" width="420" height="170" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(48, 238, "Min-cut partition", size=18, weight="700"))
    parts.append(_svg_text(48, 266, "Source side", size=13, weight="700", fill="#1d4ed8"))
    _svg_add_wrapped_text(parts, 48, 288, source_side_text, max_chars=48, size=13)
    parts.append(_svg_text(48, 330, "Sink side", size=13, weight="700", fill="#b45309"))
    _svg_add_wrapped_text(parts, 48, 352, sink_side_text, max_chars=48, size=13)

    parts.append('<rect x="480" y="206" width="452" height="170" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(500, 238, "Cut edges that certify the answer", size=18, weight="700"))
    if displayed_cut_edges:
        for index, edge in enumerate(displayed_cut_edges):
            label = f"{edge['source']} → {edge['target']} · {edge['flow']}/{edge['capacity']} · saturated={edge['saturated']}"
            parts.append(_svg_text(500, 272 + index * 22, _truncate_svg_text(label, 62), size=13, fill="#334155"))
        if hidden_cut_edges:
            parts.append(_svg_text(500, 272 + len(displayed_cut_edges) * 22, f"+{hidden_cut_edges} more cut edge(s)", size=12, fill="#64748b"))
    else:
        _svg_add_wrapped_text(
            parts,
            500,
            272,
            "No cut edges cross the partition because the sink is unreachable with zero flow.",
            max_chars=52,
            size=13,
            fill="#334155",
        )

    parts.append('<rect x="28" y="398" width="420" height="208" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(48, 430, "Why this is a valid proof", size=18, weight="700"))
    narrative_y = 462
    for bullet in explanation["narrative"]:
        parts.append(_svg_text(48, narrative_y, "•", size=16, weight="700", fill="#2563eb"))
        narrative_y = _svg_add_wrapped_text(parts, 64, narrative_y, bullet, max_chars=46, size=13, fill="#334155") + 26

    parts.append('<rect x="480" y="398" width="452" height="208" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(500, 430, "Augmenting paths", size=18, weight="700"))
    if displayed_paths:
        for index, step in enumerate(displayed_paths, start=1):
            extra = f" · phase {step['phase']}" if "phase" in step else ""
            label = f"{index}. {' → '.join(step['path'])} · bottleneck {step['bottleneck']}{extra}"
            parts.append(_svg_text(500, 462 + (index - 1) * 24, _truncate_svg_text(label, 66), size=13, fill="#334155"))
        if hidden_paths:
            parts.append(_svg_text(500, 462 + len(displayed_paths) * 24, f"+{hidden_paths} more augmenting path(s)", size=12, fill="#64748b"))
    else:
        parts.append(_svg_text(500, 462, "No augmenting paths were found.", size=13, fill="#334155"))

    footer = f"Certificate check: max flow = {flow_result.max_flow}, cut capacity = {explanation['min_cut_capacity']}, equality holds = {explanation['max_flow_equals_min_cut_capacity']}."
    parts.append(_svg_text(28, 628, _truncate_svg_text(footer, 120), size=12, fill="#475569"))
    parts.append('</svg>')
    return "".join(parts) + "\n"


def render_matching_svg(matching_result: MatchingResult, *, graph_name: str = "bipartite_matching") -> str:
    explanation = build_matching_explanation(matching_result)
    cover = matching_result.minimum_vertex_cover
    width = 960
    height = 640
    displayed_matches = matching_result.matches[:6]
    hidden_matches = max(0, len(matching_result.matches) - len(displayed_matches))
    cover_text = f"Left: {', '.join(cover['left']) if cover['left'] else '(none)'} · Right: {', '.join(cover['right']) if cover['right'] else '(none)'}"
    reach = cover['reachable_from_unmatched_left']

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Bipartite matching proof card</title>',
        f'<desc id="desc">Proof-style summary card for {graph_name} showing the matching, minimum vertex cover, and König certificate.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 42, "Bipartite matching proof card", size=28, weight="700"),
        _svg_text(28, 68, f"Graph: {graph_name} · left={len(matching_result.left_partition)} · right={len(matching_result.right_partition)}", size=14, fill="#334155"),
    ]

    stat_cards = [
        (28, "Algorithm", matching_result.flow['algorithm'], "max-flow engine backing the reduction"),
        (258, "Matches", str(len(matching_result.matches)), "selected left-right pairs"),
        (488, "Min cover size", str(cover['size']), "should match the match count"),
        (718, "König check", str(cover['konig_theorem_check']), f"unmatched left: {len(matching_result.unmatched_left)}"),
    ]
    for x, label, value, subtitle in stat_cards:
        parts.append(f'<rect x="{x}" y="94" width="214" height="86" rx="16" fill="#ffffff" stroke="#dbe4ee" />')
        parts.append(_svg_text(x + 18, 122, label, size=13, weight="700", fill="#475569"))
        parts.append(_svg_text(x + 18, 154, value, size=28, weight="700", fill="#0f172a"))
        parts.append(_svg_text(x + 18, 172, subtitle, size=11, fill="#64748b"))

    parts.append('<rect x="28" y="206" width="420" height="170" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(48, 238, "Selected matches", size=18, weight="700"))
    if displayed_matches:
        for index, pair in enumerate(displayed_matches, start=1):
            parts.append(_svg_text(48, 272 + (index - 1) * 22, f"{index}. {pair['left']} → {pair['right']}", size=13, fill="#334155"))
        if hidden_matches:
            parts.append(_svg_text(48, 272 + len(displayed_matches) * 22, f"+{hidden_matches} more match(es)", size=12, fill="#64748b"))
    else:
        parts.append(_svg_text(48, 272, "No matches were selected.", size=13, fill="#334155"))
    _svg_add_wrapped_text(
        parts,
        48,
        344,
        f"Unmatched left: {', '.join(matching_result.unmatched_left) if matching_result.unmatched_left else '(none)'}",
        max_chars=46,
        size=12,
        fill="#64748b",
    )
    _svg_add_wrapped_text(
        parts,
        48,
        364,
        f"Unmatched right: {', '.join(matching_result.unmatched_right) if matching_result.unmatched_right else '(none)'}",
        max_chars=46,
        size=12,
        fill="#64748b",
    )

    parts.append('<rect x="480" y="206" width="452" height="170" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(500, 238, "Recovered minimum vertex cover", size=18, weight="700"))
    _svg_add_wrapped_text(parts, 500, 270, cover_text, max_chars=56, size=13, fill="#334155")
    parts.append(_svg_text(500, 326, "Alternating reachability from unmatched left", size=13, weight="700", fill="#475569"))
    _svg_add_wrapped_text(parts, 500, 348, f"Left reached: {', '.join(reach['left']) if reach['left'] else '(none)'}", max_chars=54, size=12, fill="#64748b")
    _svg_add_wrapped_text(parts, 500, 372, f"Right reached: {', '.join(reach['right']) if reach['right'] else '(none)'}", max_chars=54, size=12, fill="#64748b")

    parts.append('<rect x="28" y="398" width="420" height="208" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(48, 430, "Why the certificate works", size=18, weight="700"))
    narrative_y = 462
    for bullet in explanation["narrative"]:
        parts.append(_svg_text(48, narrative_y, "•", size=16, weight="700", fill="#059669"))
        narrative_y = _svg_add_wrapped_text(parts, 64, narrative_y, bullet, max_chars=46, size=13, fill="#334155") + 26

    parts.append('<rect x="480" y="398" width="452" height="208" rx="18" fill="#ffffff" stroke="#dbe4ee" />')
    parts.append(_svg_text(500, 430, "Certificate summary", size=18, weight="700"))
    summary_lines = [
        f"match count = {len(matching_result.matches)}",
        f"minimum vertex cover size = {cover['size']}",
        f"König theorem satisfied = {cover['konig_theorem_check']}",
        f"flow max value used by reduction = {matching_result.flow['max_flow']}",
    ]
    for index, line in enumerate(summary_lines):
        parts.append(_svg_text(500, 462 + index * 24, line, size=13, fill="#334155"))
    parts.append(_svg_text(500, 570, "This card is meant to pair with the Markdown proof artifact for portfolio screenshots.", size=12, fill="#64748b"))

    footer = f"König check ties the matching size ({len(matching_result.matches)}) to the recovered cover size ({cover['size']})."
    parts.append(_svg_text(28, 628, _truncate_svg_text(footer, 120), size=12, fill="#475569"))
    parts.append('</svg>')
    return "".join(parts) + "\n"


def render_flow_markdown(flow_result: FlowResult, *, graph_name: str = "network_flow") -> str:
    explanation = build_flow_explanation(flow_result)
    lines = [
        f"# Max-flow proof artifact: `{graph_name}`",
        "",
        f"- Generated: {datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        f"- Algorithm: `{flow_result.algorithm}`",
        f"- Max flow: `{flow_result.max_flow}`",
        f"- Augmenting paths recorded: `{len(flow_result.augmenting_paths)}`",
    ]
    if flow_result.phases is not None:
        lines.append(f"- Dinic phases: `{flow_result.phases}`")
    lines.extend(
        [
            "",
            "## Min-cut certificate",
            "",
            f"- Source side: {', '.join(flow_result.min_cut['source_side'])}",
            f"- Sink side: {', '.join(flow_result.min_cut['sink_side'])}",
            f"- Cut capacity: `{explanation['min_cut_capacity']}`",
            f"- Max-flow/min-cut check: `{explanation['max_flow_equals_min_cut_capacity']}`",
            "",
            "### Cut edges",
            "",
        ]
    )
    for edge in explanation['cut_edges']:
        lines.append(
            f"- `{edge['source']} -> {edge['target']}` carries `{edge['flow']}/{edge['capacity']}` (saturated={edge['saturated']})"
        )
    if not explanation['cut_edges']:
        lines.append('- No cut edges cross the final partition because the sink is unreachable with zero total flow.')
    lines.extend(["", "## Augmenting paths", ""])
    if flow_result.augmenting_paths:
        for index, step in enumerate(flow_result.augmenting_paths, start=1):
            extras = []
            if 'phase' in step:
                extras.append(f"phase {step['phase']}")
            extra_suffix = f" ({', '.join(extras)})" if extras else ''
            lines.append(
                f"{index}. `{ ' -> '.join(step['path']) }` | bottleneck `{step['bottleneck']}`{extra_suffix}"
            )
    else:
        lines.append('- No augmenting paths were found.')
    lines.extend(["", "## Narrative", ""])
    lines.extend([f"- {item}" for item in explanation['narrative']])
    return "\n".join(lines) + "\n"


def render_matching_markdown(matching_result: MatchingResult, *, graph_name: str = "bipartite_matching") -> str:
    explanation = build_matching_explanation(matching_result)
    lines = [
        f"# Bipartite matching proof artifact: `{graph_name}`",
        "",
        f"- Generated: {datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        f"- Flow algorithm: `{matching_result.flow['algorithm']}`",
        f"- Match count: `{len(matching_result.matches)}`",
        f"- Minimum vertex cover size: `{matching_result.minimum_vertex_cover['size']}`",
        f"- König check: `{matching_result.minimum_vertex_cover['konig_theorem_check']}`",
        "",
        "## Matches",
        "",
    ]
    if matching_result.matches:
        for pair in matching_result.matches:
            lines.append(f"- `{pair['left']} -> {pair['right']}`")
    else:
        lines.append('- No matches were selected.')
    lines.extend(["", "## Minimum vertex cover", ""])
    cover = matching_result.minimum_vertex_cover
    lines.append(f"- Left cover vertices: {', '.join(cover['left']) if cover['left'] else '(none)'}")
    lines.append(f"- Right cover vertices: {', '.join(cover['right']) if cover['right'] else '(none)'}")
    reach = cover['reachable_from_unmatched_left']
    lines.append(f"- Reachable unmatched-left expansion (left): {', '.join(reach['left']) if reach['left'] else '(none)'}")
    lines.append(f"- Reachable unmatched-left expansion (right): {', '.join(reach['right']) if reach['right'] else '(none)'}")
    lines.extend(["", "## Narrative", ""])
    lines.extend([f"- {item}" for item in explanation['narrative']])
    return "\n".join(lines) + "\n"


def write_markdown_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def write_dot_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents + "\n", encoding="utf-8")


def write_svg_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


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
    solve_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the solved flow graph")
    solve_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the solved flow graph")
    add_explain_argument(solve_parser)

    demo_parser = subparsers.add_parser("demo", help="run the bundled sample graph")
    demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    demo_parser.add_argument("--algorithm", choices=SUPPORTED_ALGORITHMS, default=DEFAULT_ALGORITHM)
    demo_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the sample flow graph")
    demo_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the sample flow graph")
    demo_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the sample flow graph")
    add_explain_argument(demo_parser)

    match_parser = subparsers.add_parser("match", help="solve a bipartite matching JSON file")
    match_parser.add_argument("graph", type=Path, help="path to bipartite graph JSON")
    match_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    match_parser.add_argument("--algorithm", choices=SUPPORTED_ALGORITHMS, default=DEFAULT_ALGORITHM)
    match_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the solved matching graph")
    match_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the solved matching graph")
    match_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the solved matching graph")
    add_explain_argument(match_parser)

    match_demo_parser = subparsers.add_parser("match-demo", help="run the bundled matching sample")
    match_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    match_demo_parser.add_argument("--algorithm", choices=SUPPORTED_ALGORITHMS, default=DEFAULT_ALGORITHM)
    match_demo_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the sample matching graph")
    match_demo_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the sample matching graph")
    match_demo_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the sample matching graph")
    add_explain_argument(match_demo_parser)

    benchmark_parser = subparsers.add_parser("benchmark", help="compare Edmonds-Karp vs Dinic on generated graphs")
    benchmark_parser.add_argument("--nodes", type=int, default=24, help="number of nodes in each generated benchmark graph")
    benchmark_parser.add_argument(
        "--graph-family",
        choices=BENCHMARK_GRAPH_FAMILIES,
        default="dag",
        help="benchmark graph generator: DAG, dense cyclic residual mesh, or dense layered network",
    )
    benchmark_parser.add_argument("--edge-probability", type=float, default=0.18, help="probability for optional generator-specific extra edges")
    benchmark_parser.add_argument("--trials", type=int, default=5, help="how many generated graphs to test")
    benchmark_parser.add_argument("--seed", type=int, default=42, help="base RNG seed for reproducible graphs")
    benchmark_parser.add_argument("--capacity-min", type=int, default=1)
    benchmark_parser.add_argument("--capacity-max", type=int, default=20)
    benchmark_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown benchmark report card")
    benchmark_parser.add_argument("--svg-out", type=Path, help="write an SVG benchmark report card")
    benchmark_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    return parser


def validate_cli_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.command != "benchmark":
        return
    try:
        validate_benchmark_graph_inputs(
            node_count=args.nodes,
            edge_probability=args.edge_probability,
            capacity_min=args.capacity_min,
            capacity_max=args.capacity_max,
        )
    except ValueError as exc:
        parser.error(str(exc))

    minimum_nodes = BENCHMARK_GRAPH_MIN_NODES[args.graph_family]
    if args.nodes < minimum_nodes:
        parser.error(f"--graph-family {args.graph_family} requires --nodes >= {minimum_nodes}")


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
        if getattr(args, "markdown_out", None):
            write_markdown_output(args.markdown_out, render_flow_markdown(flow_result, graph_name=graph_path.stem))
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(args.svg_out, render_flow_svg(flow_result, graph_name=graph_path.stem))
            payload["svg_output"] = str(args.svg_out)
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
        if getattr(args, "markdown_out", None):
            write_markdown_output(args.markdown_out, render_flow_markdown(flow_result, graph_name=graph_path.stem))
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(args.svg_out, render_flow_svg(flow_result, graph_name=graph_path.stem))
            payload["svg_output"] = str(args.svg_out)
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
        if getattr(args, "markdown_out", None):
            write_markdown_output(args.markdown_out, render_matching_markdown(matching_result, graph_name=graph_path.stem))
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(args.svg_out, render_matching_svg(matching_result, graph_name=graph_path.stem))
            payload["svg_output"] = str(args.svg_out)
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
        if getattr(args, "markdown_out", None):
            write_markdown_output(args.markdown_out, render_matching_markdown(matching_result, graph_name=graph_path.stem))
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(args.svg_out, render_matching_svg(matching_result, graph_name=graph_path.stem))
            payload["svg_output"] = str(args.svg_out)
        return payload

    payload = benchmark_algorithms(
        node_count=args.nodes,
        edge_probability=args.edge_probability,
        trials=args.trials,
        seed=args.seed,
        capacity_min=args.capacity_min,
        capacity_max=args.capacity_max,
        graph_family=args.graph_family,
    )
    if getattr(args, "markdown_out", None):
        write_markdown_output(args.markdown_out, render_benchmark_markdown(payload))
        payload["markdown_output"] = str(args.markdown_out)
    if getattr(args, "svg_out", None):
        write_svg_output(args.svg_out, render_benchmark_svg(payload))
        payload["svg_output"] = str(args.svg_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_cli_args(parser, args)
    payload = run_command(args)
    if getattr(args, "pretty", False):
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
