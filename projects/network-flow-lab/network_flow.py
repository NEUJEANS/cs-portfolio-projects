from __future__ import annotations

import argparse
import heapq
import html
import json
import math
import os
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
class WeightedEdge:
    source: str
    target: str
    capacity: int
    cost: int


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


@dataclass(frozen=True)
class MinCostFlowResult:
    source: str
    sink: str
    total_flow: int
    total_cost: int
    augmenting_paths: list[dict[str, Any]]
    edge_flows: list[dict[str, Any]]
    algorithm: str = "successive-shortest-path"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "sink": self.sink,
            "algorithm": self.algorithm,
            "total_flow": self.total_flow,
            "total_cost": self.total_cost,
            "augmenting_paths": self.augmenting_paths,
            "edge_flows": self.edge_flows,
        }


@dataclass(frozen=True)
class AssignmentResult:
    left_partition: list[str]
    right_partition: list[str]
    assignments: list[dict[str, Any]]
    unmatched_left: list[str]
    unmatched_right: list[str]
    total_cost: int
    covers_smaller_partition: bool
    flow: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_partition": self.left_partition,
            "right_partition": self.right_partition,
            "assignments": self.assignments,
            "assignment_count": len(self.assignments),
            "unmatched_left": self.unmatched_left,
            "unmatched_right": self.unmatched_right,
            "total_cost": self.total_cost,
            "covers_smaller_partition": self.covers_smaller_partition,
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


def build_assignment_explanation(assignment_result: AssignmentResult) -> dict[str, Any]:
    assignment_cost = sum(item["cost"] for item in assignment_result.assignments)
    assignment_count = len(assignment_result.assignments)
    average_cost = round(assignment_cost / assignment_count, 3) if assignment_count else None
    return {
        "assignment_count": assignment_count,
        "total_cost": assignment_result.total_cost,
        "average_cost": average_cost,
        "covers_smaller_partition": assignment_result.covers_smaller_partition,
        "cost_matches_flow_total": assignment_cost == assignment_result.total_cost,
        "selected_pairs": assignment_result.assignments,
        "narrative": [
            f"The min-cost flow picked {assignment_count} assignment edge(s) with total cost {assignment_result.total_cost}.",
            "Each left node and right node is capped at one unit of flow, so any positive-cost path corresponds to a valid one-to-one assignment.",
            f"Coverage of the smaller partition is {'complete' if assignment_result.covers_smaller_partition else 'partial'}, which makes it easy to see whether the input graph admitted a full assignment.",
        ],
    }


def build_min_cost_flow_explanation(
    flow_result: MinCostFlowResult,
    *,
    target_flow: int | None = None,
) -> dict[str, Any]:
    positive_flow_edges = [edge for edge in flow_result.edge_flows if edge["flow"] > 0]
    used_edge_cost = sum(edge["flow"] * edge["cost"] for edge in positive_flow_edges)
    average_cost_per_unit = round(flow_result.total_cost / flow_result.total_flow, 3) if flow_result.total_flow else None
    target_reached = target_flow is None or flow_result.total_flow >= target_flow
    return {
        "total_flow": flow_result.total_flow,
        "target_flow": target_flow,
        "target_reached": target_reached,
        "total_cost": flow_result.total_cost,
        "average_cost_per_unit": average_cost_per_unit,
        "cost_matches_used_edges": used_edge_cost == flow_result.total_cost,
        "positive_flow_edges": positive_flow_edges,
        "narrative": [
            (
                f"The solver shipped {flow_result.total_flow} unit(s) of flow"
                f"{' out of the requested ' + str(target_flow) if target_flow is not None else ''}"
                f" with total cost {flow_result.total_cost}."
            ),
            "Every positive-flow edge contributes `flow × cost` to the certificate, so the selected residual paths can be audited directly from the exported edge table.",
            (
                "The requested flow target was reached before the residual graph ran out of augmenting paths."
                if target_reached
                else "The residual graph ran out of augmenting paths before the requested flow target was reached, so the result is a best-effort partial shipment."
            ),
        ],
    }


MATCH_SOURCE = "__source__"
MATCH_SINK = "__sink__"
ASSIGN_SOURCE = "__assignment_source__"
ASSIGN_SINK = "__assignment_sink__"
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


def load_weighted_assignment_graph(path: Path) -> tuple[list[str], list[str], list[tuple[str, str, int]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    left = payload.get("left")
    right = payload.get("right")
    raw_edges = payload.get("edges")

    if not isinstance(left, list) or not left:
        raise ValueError("assignment graph must include a non-empty 'left' list")
    if not isinstance(right, list) or not right:
        raise ValueError("assignment graph must include a non-empty 'right' list")
    if not isinstance(raw_edges, list):
        raise ValueError("assignment graph must include an 'edges' list")

    left_nodes = [str(node) for node in left]
    right_nodes = [str(node) for node in right]
    if len(set(left_nodes)) != len(left_nodes) or len(set(right_nodes)) != len(right_nodes):
        raise ValueError("left and right partitions must not contain duplicate node names")
    reserved = {ASSIGN_SOURCE, ASSIGN_SINK, MATCH_SOURCE, MATCH_SINK}
    if reserved & set(left_nodes + right_nodes):
        raise ValueError("assignment graphs may not use reserved internal node names")
    left_set = set(left_nodes)
    right_set = set(right_nodes)
    if left_set & right_set:
        raise ValueError("left and right partitions must be disjoint")

    edges: list[tuple[str, str, int]] = []
    seen_edges: set[tuple[str, str]] = set()
    for item in raw_edges:
        if not isinstance(item, dict):
            raise ValueError("each assignment edge must be an object")
        source = str(item.get("source"))
        target = str(item.get("target"))
        if source not in left_set or target not in right_set:
            raise ValueError("assignment edges must point from left nodes to right nodes")
        pair = (source, target)
        if pair in seen_edges:
            raise ValueError("assignment graphs must not repeat the same left/right pair")
        seen_edges.add(pair)
        cost = int(item.get("cost", -1))
        if cost < 0:
            raise ValueError("assignment edge cost must be non-negative")
        edges.append((source, target, cost))
    return left_nodes, right_nodes, edges


def load_costed_flow_graph(path: Path) -> tuple[list[str], list[WeightedEdge], str, str, int | None]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    nodes = payload.get("nodes")
    source = str(payload.get("source"))
    sink = str(payload.get("sink"))
    raw_edges = payload.get("edges")
    target_flow = payload.get("target_flow")

    if not isinstance(nodes, list) or not nodes:
        raise ValueError("costed flow graph must include a non-empty 'nodes' list")
    if not isinstance(raw_edges, list):
        raise ValueError("costed flow graph must include an 'edges' list")

    node_names = [str(node) for node in nodes]
    if len(set(node_names)) != len(node_names):
        raise ValueError("costed flow graph nodes must not contain duplicates")
    if source not in node_names or sink not in node_names:
        raise ValueError("costed flow graph source and sink must both appear in nodes")
    if source == sink:
        raise ValueError("costed flow graph source and sink must differ")

    parsed_target_flow = int(target_flow) if target_flow is not None else None
    if parsed_target_flow is not None and parsed_target_flow < 0:
        raise ValueError("target_flow must be non-negative when provided")

    node_set = set(node_names)
    edges: list[WeightedEdge] = []
    for item in raw_edges:
        if not isinstance(item, dict):
            raise ValueError("each costed flow edge must be an object")
        edge = WeightedEdge(
            source=str(item.get("source")),
            target=str(item.get("target")),
            capacity=int(item.get("capacity", -1)),
            cost=int(item.get("cost", -1)),
        )
        if edge.source not in node_set or edge.target not in node_set:
            raise ValueError("costed flow edge endpoints must appear in nodes")
        if edge.source == edge.target:
            raise ValueError("costed flow self-loops are not supported")
        if edge.capacity < 0:
            raise ValueError("costed flow edge capacity must be non-negative")
        if edge.cost < 0:
            raise ValueError("costed flow edge cost must be non-negative")
        edges.append(edge)
    return node_names, edges, source, sink, parsed_target_flow


def build_bipartite_matching_flow(
    left: list[str], right: list[str], edges: list[tuple[str, str]]
) -> tuple[list[str], list[Edge], str, str]:
    nodes = [MATCH_SOURCE, *left, *right, MATCH_SINK]
    flow_edges = [Edge(MATCH_SOURCE, node, 1) for node in left]
    flow_edges.extend(Edge(source, target, 1) for source, target in edges)
    flow_edges.extend(Edge(node, MATCH_SINK, 1) for node in right)
    return nodes, flow_edges, MATCH_SOURCE, MATCH_SINK


def build_weighted_assignment_flow(
    left: list[str], right: list[str], edges: list[tuple[str, str, int]]
) -> tuple[list[str], list[WeightedEdge], str, str]:
    nodes = [ASSIGN_SOURCE, *left, *right, ASSIGN_SINK]
    flow_edges = [WeightedEdge(ASSIGN_SOURCE, node, 1, 0) for node in left]
    flow_edges.extend(WeightedEdge(source, target, 1, cost) for source, target, cost in edges)
    flow_edges.extend(WeightedEdge(node, ASSIGN_SINK, 1, 0) for node in right)
    return nodes, flow_edges, ASSIGN_SOURCE, ASSIGN_SINK


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


@dataclass
class _MinCostResidualEdge:
    target: str
    rev: int
    capacity: int
    cost: int
    original_capacity: int = 0


def solve_min_cost_max_flow(
    nodes: list[str],
    edges: list[WeightedEdge],
    source: str,
    sink: str,
    *,
    target_flow: int | None = None,
) -> MinCostFlowResult:
    graph: dict[str, list[_MinCostResidualEdge]] = {node: [] for node in nodes}
    original_edge_refs: list[tuple[WeightedEdge, _MinCostResidualEdge]] = []

    def add_edge(edge: WeightedEdge) -> None:
        if edge.capacity < 0:
            raise ValueError("min-cost flow capacity must be non-negative")
        forward = _MinCostResidualEdge(
            target=edge.target,
            rev=len(graph[edge.target]),
            capacity=edge.capacity,
            cost=edge.cost,
            original_capacity=edge.capacity,
        )
        reverse = _MinCostResidualEdge(
            target=edge.source,
            rev=len(graph[edge.source]),
            capacity=0,
            cost=-edge.cost,
            original_capacity=0,
        )
        graph[edge.source].append(forward)
        graph[edge.target].append(reverse)
        original_edge_refs.append((edge, forward))

    for edge in edges:
        add_edge(edge)

    if target_flow is not None and target_flow < 0:
        raise ValueError("target_flow must be non-negative")

    total_flow = 0
    total_cost = 0
    augmenting_paths: list[dict[str, Any]] = []
    potentials = {node: 0 for node in nodes}

    while target_flow is None or total_flow < target_flow:
        dist = {node: math.inf for node in nodes}
        previous: dict[str, tuple[str, int]] = {}
        dist[source] = 0
        heap: list[tuple[int, str]] = [(0, source)]

        while heap:
            current_dist, node = heapq.heappop(heap)
            if current_dist != dist[node]:
                continue
            for edge_index, edge in enumerate(graph[node]):
                if edge.capacity <= 0:
                    continue
                reduced_cost = edge.cost + potentials[node] - potentials[edge.target]
                candidate = current_dist + reduced_cost
                if candidate < dist[edge.target]:
                    dist[edge.target] = candidate
                    previous[edge.target] = (node, edge_index)
                    heapq.heappush(heap, (candidate, edge.target))

        if math.isinf(dist[sink]):
            break

        for node in nodes:
            if not math.isinf(dist[node]):
                potentials[node] += int(dist[node])

        bottleneck = target_flow - total_flow if target_flow is not None else 10**18
        path_edges: list[tuple[str, int]] = []
        path_nodes = [sink]
        path_cost = 0
        cursor = sink
        while cursor != source:
            if cursor not in previous:
                raise AssertionError("missing predecessor while reconstructing min-cost path")
            previous_node, edge_index = previous[cursor]
            edge = graph[previous_node][edge_index]
            bottleneck = min(bottleneck, edge.capacity)
            path_cost += edge.cost
            path_edges.append((previous_node, edge_index))
            cursor = previous_node
            path_nodes.append(cursor)
        path_nodes.reverse()

        for previous_node, edge_index in path_edges:
            edge = graph[previous_node][edge_index]
            reverse_edge = graph[edge.target][edge.rev]
            edge.capacity -= bottleneck
            reverse_edge.capacity += bottleneck

        total_flow += bottleneck
        total_cost += bottleneck * path_cost
        augmenting_paths.append(
            {
                "path": path_nodes,
                "bottleneck": bottleneck,
                "cost_per_unit": path_cost,
                "path_cost": bottleneck * path_cost,
            }
        )

    edge_flows: list[dict[str, Any]] = []
    for original_edge, forward_edge in sorted(
        original_edge_refs,
        key=lambda item: (item[0].source, item[0].target, item[0].cost, item[0].capacity),
    ):
        edge_flows.append(
            {
                "source": original_edge.source,
                "target": original_edge.target,
                "capacity": original_edge.capacity,
                "cost": original_edge.cost,
                "flow": original_edge.capacity - forward_edge.capacity,
            }
        )

    return MinCostFlowResult(
        source=source,
        sink=sink,
        total_flow=total_flow,
        total_cost=total_cost,
        augmenting_paths=augmenting_paths,
        edge_flows=edge_flows,
    )


def solve_weighted_assignment(
    left: list[str], right: list[str], edges: list[tuple[str, str, int]]
) -> AssignmentResult:
    nodes, flow_edges, source, sink = build_weighted_assignment_flow(left, right, edges)
    target_flow = min(len(left), len(right))
    flow_result = solve_min_cost_max_flow(nodes, flow_edges, source, sink, target_flow=target_flow)
    edge_lookup = {(item["source"], item["target"]): item for item in flow_result.edge_flows}
    assignments: list[dict[str, Any]] = []
    matched_left: set[str] = set()
    matched_right: set[str] = set()

    for left_node, right_node, cost in sorted(edges):
        edge = edge_lookup.get((left_node, right_node))
        if edge and edge["flow"] == 1:
            assignments.append({"left": left_node, "right": right_node, "cost": cost})
            matched_left.add(left_node)
            matched_right.add(right_node)

    return AssignmentResult(
        left_partition=sorted(left),
        right_partition=sorted(right),
        assignments=assignments,
        unmatched_left=sorted(node for node in left if node not in matched_left),
        unmatched_right=sorted(node for node in right if node not in matched_right),
        total_cost=flow_result.total_cost,
        covers_smaller_partition=flow_result.total_flow == target_flow,
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


def render_assignment_dot(assignment_result: AssignmentResult, *, graph_name: str = "weighted_assignment") -> str:
    selected_pairs = {
        (item["left"], item["right"]): item["cost"] for item in assignment_result.assignments
    }
    selected_left = {item["left"] for item in assignment_result.assignments}
    selected_right = {item["right"] for item in assignment_result.assignments}
    flow_edges = {
        (item["source"], item["target"]): item for item in assignment_result.flow["edge_flows"]
    }

    lines = [
        f'digraph "{graph_name}" {{',
        '  rankdir=LR;',
        '  labelloc="t";',
        (
            '  label="'
            f'assignment count={len(assignment_result.assignments)}, cost={assignment_result.total_cost}, '
            f'full_coverage={assignment_result.covers_smaller_partition}'
            '";'
        ),
        '  graph [splines=true, ranksep=1.0, nodesep=0.55];',
        '  "source" [shape=diamond, style="filled", fillcolor="white", peripheries=2];',
        '  "sink" [shape=diamond, style="filled", fillcolor="white", peripheries=2];',
        '  subgraph "cluster_left_partition" {',
        '    label="left partition";',
        '    color="lightsteelblue4";',
        '    style="rounded,dashed";',
        '    rank="same";',
        '    node [shape=circle, style="filled", fillcolor="lightsteelblue1"];',
    ]
    for node in assignment_result.left_partition:
        attrs = []
        if node in assignment_result.unmatched_left:
            attrs.append('fillcolor="mistyrose"')
        elif node in selected_left:
            attrs.append('fillcolor="honeydew2"')
        lines.append(f'    "{node}" [{", ".join(attrs)}];' if attrs else f'    "{node}";')
    lines.extend([
        '  }',
        '  subgraph "cluster_right_partition" {',
        '    label="right partition";',
        '    color="darkseagreen4";',
        '    style="rounded,dashed";',
        '    rank="same";',
        '    node [shape=box, style="filled", fillcolor="honeydew2"];',
    ])
    for node in assignment_result.right_partition:
        attrs = []
        if node in assignment_result.unmatched_right:
            attrs.append('fillcolor="moccasin"')
        elif node in selected_right:
            attrs.append('peripheries=2')
        lines.append(f'    "{node}" [{", ".join(attrs)}];' if attrs else f'    "{node}";')
    lines.extend([
        '  }',
        '  subgraph "source_rank" { rank="source"; "source"; }',
        '  subgraph "sink_rank" { rank="sink"; "sink"; }',
    ])

    for node in assignment_result.left_partition:
        edge = flow_edges.get((ASSIGN_SOURCE, node))
        if edge and edge["flow"] == 1:
            lines.append(f'  "source" -> "{node}" [style="dashed", color="gray50", label="1"];')
        else:
            lines.append(f'  "source" -> "{node}" [style="dashed", color="gray80", label="0/1"];')

    for left_node in assignment_result.left_partition:
        for right_node in assignment_result.right_partition:
            edge = flow_edges.get((left_node, right_node))
            if edge is None:
                continue
            attrs = [f'label="cost {edge["cost"]}"']
            if (left_node, right_node) in selected_pairs:
                attrs = [f'label="selected @ {edge["cost"]}"', 'color="forestgreen"', 'penwidth=3']
            else:
                attrs.append('color="gray60"')
            lines.append(f'  "{left_node}" -> "{right_node}" [{", ".join(attrs)}];')

    for node in assignment_result.right_partition:
        edge = flow_edges.get((node, ASSIGN_SINK))
        if edge and edge["flow"] == 1:
            lines.append(f'  "{node}" -> "sink" [style="dashed", color="gray50", label="1"];')
        else:
            lines.append(f'  "{node}" -> "sink" [style="dashed", color="gray80", label="0/1"];')

    lines.append('}')
    return "\n".join(lines)


def render_min_cost_flow_dot(
    flow_result: MinCostFlowResult,
    *,
    graph_name: str = "costed_flow",
    target_flow: int | None = None,
) -> str:
    explanation = build_min_cost_flow_explanation(flow_result, target_flow=target_flow)
    node_pool = (
        {flow_result.source, flow_result.sink}
        | {edge["source"] for edge in flow_result.edge_flows}
        | {edge["target"] for edge in flow_result.edge_flows}
    )
    node_names = [flow_result.source]
    node_names.extend(sorted(node for node in node_pool if node not in {flow_result.source, flow_result.sink}))
    node_names.append(flow_result.sink)
    positive_nodes = {
        edge["source"]
        for edge in flow_result.edge_flows
        if edge["flow"] > 0
    } | {
        edge["target"]
        for edge in flow_result.edge_flows
        if edge["flow"] > 0
    }
    requested_flow = target_flow if target_flow is not None else "maximize"

    lines = [
        f'digraph "{graph_name}" {{',
        '  rankdir=LR;',
        '  labelloc="t";',
        (
            '  label="'
            f'min-cost flow={flow_result.total_flow}, cost={flow_result.total_cost}, '
            f'target={requested_flow}, reached={explanation["target_reached"]}'
            '";'
        ),
        '  node [shape=circle, style="filled", fillcolor="white"];',
    ]

    for node in node_names:
        attrs: list[str] = []
        if node == flow_result.source:
            attrs.extend(['fillcolor="lightblue"', 'peripheries=2'])
        elif node == flow_result.sink:
            attrs.extend(['fillcolor="lightgoldenrod1"', 'peripheries=2'])
        elif node in positive_nodes:
            attrs.append('fillcolor="honeydew2"')
        lines.append(f'  "{node}" [{", ".join(attrs)}];' if attrs else f'  "{node}";')

    for edge in flow_result.edge_flows:
        attrs = [f'label="{edge["flow"]}/{edge["capacity"]} @ {edge["cost"]}"']
        if edge["flow"] > 0:
            attrs.extend(['color="forestgreen"', 'penwidth=3'])
        else:
            attrs.append('color="gray60"')
        lines.append(f'  "{edge["source"]}" -> "{edge["target"]}" [{", ".join(attrs)}];')

    lines.append("}")
    return "\n".join(lines)


def _humanize_assignment_path(path: list[str]) -> list[str]:
    labels = {
        ASSIGN_SOURCE: "source",
        ASSIGN_SINK: "sink",
    }
    return [labels.get(node, node) for node in path]


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


def _html_escape(text: str) -> str:
    return html.escape(text, quote=True)


def _namespace_embedded_svg_accessibility(svg: str, *, prefix: str) -> str:
    return (
        svg.replace('aria-labelledby="title desc"', f'aria-labelledby="{prefix}-title {prefix}-desc"')
        .replace('id="title"', f'id="{prefix}-title"')
        .replace('id="desc"', f'id="{prefix}-desc"')
    )


def _relative_output_path(target: Path, base_dir: Path) -> str:
    return Path(os.path.relpath(target, start=base_dir)).as_posix()


def build_artifact_gallery_paths(*, html_out: Path, artifact_dir: Path | None = None) -> dict[str, Path]:
    base_dir = artifact_dir if artifact_dir is not None else html_out.parent
    return {
        "assignment_page": base_dir / "sample-assignment-artifact-page.html",
        "assignment_proof_svg": base_dir / "sample-assignment-proof.svg",
        "assignment_markdown": base_dir / "sample-assignment-proof.md",
        "assignment_dot": base_dir / "sample-assignment.dot",
        "cost_page": base_dir / "sample-cost-flow-artifact-page.html",
        "cost_proof_svg": base_dir / "sample-cost-flow-proof.svg",
        "cost_markdown": base_dir / "sample-cost-flow-proof.md",
        "cost_dot": base_dir / "sample-cost-flow.dot",
    }


def build_benchmark_gallery_paths(*, html_out: Path, artifact_dir: Path | None = None) -> dict[str, Path]:
    base_dir = artifact_dir if artifact_dir is not None else html_out.parent
    return {
        "dag_svg": base_dir / "benchmark-dag-report.svg",
        "dag_markdown": base_dir / "benchmark-dag-report.md",
        "dense_svg": base_dir / "benchmark-dense-report.svg",
        "dense_markdown": base_dir / "benchmark-dense-report.md",
        "layered_svg": base_dir / "benchmark-layered-report.svg",
        "layered_markdown": base_dir / "benchmark-layered-report.md",
    }


def build_showcase_paths(*, html_out: Path, artifact_dir: Path | None = None) -> dict[str, Path]:
    base_dir = artifact_dir if artifact_dir is not None else html_out.parent
    return {
        "artifact_gallery": base_dir / "artifact-gallery.html",
        "benchmark_gallery": base_dir / "benchmark-gallery.html",
        "flow_svg": base_dir / "sample-flow-proof.svg",
        "flow_markdown": base_dir / "sample-flow-proof.md",
        "matching_svg": base_dir / "sample-matching-proof.svg",
        "matching_markdown": base_dir / "sample-matching-proof.md",
        "assignment_page": base_dir / "sample-assignment-artifact-page.html",
        "assignment_svg": base_dir / "sample-assignment-proof.svg",
        "assignment_markdown": base_dir / "sample-assignment-proof.md",
        "assignment_dot": base_dir / "sample-assignment.dot",
        "cost_page": base_dir / "sample-cost-flow-artifact-page.html",
        "cost_svg": base_dir / "sample-cost-flow-proof.svg",
        "cost_markdown": base_dir / "sample-cost-flow-proof.md",
        "cost_dot": base_dir / "sample-cost-flow.dot",
        "dag_svg": base_dir / "benchmark-dag-report.svg",
        "dag_markdown": base_dir / "benchmark-dag-report.md",
        "dense_svg": base_dir / "benchmark-dense-report.svg",
        "dense_markdown": base_dir / "benchmark-dense-report.md",
        "layered_svg": base_dir / "benchmark-layered-report.svg",
        "layered_markdown": base_dir / "benchmark-layered-report.md",
    }


def _compute_vertical_positions(count: int, *, top: float, bottom: float) -> list[float]:
    if count <= 0:
        return []
    if count == 1:
        return [(top + bottom) / 2]
    step = (bottom - top) / (count - 1)
    return [top + step * index for index in range(count)]


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


def render_min_cost_flow_svg(
    flow_result: MinCostFlowResult,
    *,
    graph_name: str = "costed_flow",
    target_flow: int | None = None,
) -> str:
    explanation = build_min_cost_flow_explanation(flow_result, target_flow=target_flow)
    width = 960
    height = 640
    displayed_edges = explanation["positive_flow_edges"][:6]
    hidden_edges = max(0, len(explanation["positive_flow_edges"]) - len(displayed_edges))
    displayed_paths = flow_result.augmenting_paths[:5]
    hidden_paths = max(0, len(flow_result.augmenting_paths) - len(displayed_paths))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Min-cost flow proof card</title>',
        f'<desc id="desc">Proof-style summary card for {graph_name} showing the chosen min-cost flow edges and residual certificate.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 42, "Min-cost flow proof card", size=28, weight="700"),
        _svg_text(28, 68, f"Graph: {graph_name} · flow={flow_result.total_flow} · cost={flow_result.total_cost}", size=14, fill="#334155"),
    ]

    requested_flow_label = str(target_flow) if target_flow is not None else "maximize"
    stat_cards = [
        (28, "Algorithm", flow_result.algorithm, "successive shortest paths over the residual graph"),
        (258, "Requested flow", requested_flow_label, "explicit target or saturate until no path remains"),
        (488, "Delivered flow", str(flow_result.total_flow), f"target reached: {explanation['target_reached']}"),
        (718, "Total cost", str(flow_result.total_cost), f"avg cost/unit: {explanation['average_cost_per_unit']}"),
    ]
    for x, label, value, subtitle in stat_cards:
        parts.append(f'<rect x="{x}" y="96" width="202" height="88" rx="18" fill="#ffffff" stroke="#cbd5e1" />')
        parts.append(_svg_text(x + 16, 124, label, size=13, weight="600", fill="#475569"))
        parts.append(_svg_text(x + 16, 154, value, size=24, weight="700"))
        parts.append(_svg_text(x + 16, 176, _truncate_svg_text(subtitle, 34), size=12, fill="#64748b"))

    section_top = 218
    parts.append('<rect x="28" y="218" width="420" height="380" rx="24" fill="#ffffff" stroke="#cbd5e1" />')
    parts.append(_svg_text(48, section_top + 26, "Edges carrying flow", size=20, weight="700"))
    current_y = section_top + 56
    if displayed_edges:
        for edge in displayed_edges:
            line = f"{edge['source']} -> {edge['target']} ({edge['flow']}/{edge['capacity']} @ cost {edge['cost']})"
            parts.append(_svg_text(48, current_y, _truncate_svg_text(line, 46), size=15, weight="600", fill="#0f172a"))
            current_y += 26
    else:
        parts.append(_svg_text(48, current_y, "(no edges carried positive flow)", size=15, fill="#475569"))
        current_y += 26
    if hidden_edges:
        parts.append(_svg_text(48, current_y, f"+ {hidden_edges} more positive-flow edge(s)", size=13, fill="#64748b"))
        current_y += 24
    current_y += 10
    current_y = _svg_add_wrapped_text(
        parts,
        48,
        current_y,
        f"Cost matches used edges: {explanation['cost_matches_used_edges']}",
        max_chars=46,
        size=13,
        weight="600",
    ) + 24
    _svg_add_wrapped_text(
        parts,
        48,
        current_y,
        f"Target reached: {explanation['target_reached']}",
        max_chars=46,
        size=13,
        weight="600",
    )

    parts.append('<rect x="478" y="218" width="454" height="380" rx="24" fill="#ffffff" stroke="#cbd5e1" />')
    parts.append(_svg_text(498, section_top + 26, "Residual-path certificate", size=20, weight="700"))
    current_y = section_top + 54
    for line in explanation["narrative"]:
        current_y = _svg_add_wrapped_text(parts, 498, current_y, line, max_chars=50, size=13) + 22
    parts.append(_svg_text(498, current_y, "Augmenting paths", size=16, weight="700"))
    current_y += 24
    for index, step in enumerate(displayed_paths, start=1):
        summary = f"#{index}: bottleneck {step['bottleneck']} · unit cost {step['cost_per_unit']} · total {step['path_cost']}"
        current_y = _svg_add_wrapped_text(parts, 498, current_y, summary, max_chars=50, size=13, weight="600", fill="#0f172a") + 18
        current_y = _svg_add_wrapped_text(parts, 514, current_y, ' -> '.join(step['path']), max_chars=46, size=12, fill="#475569") + 20
    if hidden_paths:
        parts.append(_svg_text(498, min(current_y, 572), f"+ {hidden_paths} more augmenting path(s)", size=12, fill="#64748b"))

    parts.append(_svg_text(28, 622, "Tip: pair this card with the assignment proof card to show the same min-cost engine in both generic and bipartite settings.", size=12, fill="#64748b"))
    parts.append("</svg>")
    return "\n".join(parts)


def _compute_min_cost_flow_diagram_columns(flow_result: MinCostFlowResult) -> list[list[str]]:
    nodes = sorted({flow_result.source, flow_result.sink} | {edge["source"] for edge in flow_result.edge_flows} | {edge["target"] for edge in flow_result.edge_flows})
    outgoing: dict[str, set[str]] = {node: set() for node in nodes}
    incoming: dict[str, set[str]] = {node: set() for node in nodes}
    for edge in flow_result.edge_flows:
        outgoing[edge["source"]].add(edge["target"])
        incoming[edge["target"]].add(edge["source"])

    source_distance: dict[str, int] = {flow_result.source: 0}
    queue: deque[str] = deque([flow_result.source])
    while queue:
        node = queue.popleft()
        for nxt in sorted(outgoing[node]):
            if nxt in source_distance:
                continue
            source_distance[nxt] = source_distance[node] + 1
            queue.append(nxt)

    sink_distance: dict[str, int] = {flow_result.sink: 0}
    queue = deque([flow_result.sink])
    while queue:
        node = queue.popleft()
        for prev in sorted(incoming[node]):
            if prev in sink_distance:
                continue
            sink_distance[prev] = sink_distance[node] + 1
            queue.append(prev)

    fallback_middle_depth = max(1, max(source_distance.values(), default=0))
    sink_depth = max(
        source_distance.get(flow_result.sink, 0),
        max((distance + 1 for distance in source_distance.values()), default=1),
    )
    columns: dict[int, list[str]] = {depth: [] for depth in range(sink_depth + 1)}
    for node in nodes:
        if node == flow_result.source:
            depth = 0
        elif node == flow_result.sink:
            depth = sink_depth
        elif node in source_distance:
            depth = min(source_distance[node], sink_depth - 1)
        elif node in sink_distance:
            depth = max(1, sink_depth - sink_distance[node])
        else:
            depth = fallback_middle_depth
        columns.setdefault(depth, []).append(node)

    return [sorted(columns.get(depth, [])) for depth in range(sink_depth + 1)]



def render_min_cost_flow_diagram_svg(
    flow_result: MinCostFlowResult,
    *,
    graph_name: str = "costed_flow",
    target_flow: int | None = None,
) -> str:
    width = 940
    columns = _compute_min_cost_flow_diagram_columns(flow_result)
    max_rows = max((len(column) for column in columns), default=1)
    height = max(430, 240 + max_rows * 108)
    top_y = 176
    bottom_y = height - 118
    column_left = 112
    column_right = width - 120
    circle_radius = 28
    diamond_half = 30
    label_font = 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    explanation = build_min_cost_flow_explanation(flow_result, target_flow=target_flow)
    node_positions: dict[str, tuple[float, float]] = {}
    positive_nodes = {
        edge["source"]
        for edge in flow_result.edge_flows
        if edge["flow"] > 0
    } | {
        edge["target"]
        for edge in flow_result.edge_flows
        if edge["flow"] > 0
    }

    def add_label(parts: list[str], x: float, y: float, text: str, *, fill: str = "#475569", size: int = 12, weight: str = "600") -> None:
        parts.append(
            f"<text x=\"{x:.1f}\" y=\"{y:.1f}\" text-anchor=\"middle\" font-size=\"{size}\" font-weight=\"{weight}\" "
            f"fill=\"{fill}\" font-family='{label_font}'>{_svg_escape(text)}</text>"
        )

    def add_diamond(parts: list[str], x: float, y: float, label: str, *, fill: str) -> None:
        points = f"{x:.1f},{y - diamond_half:.1f} {x + diamond_half:.1f},{y:.1f} {x:.1f},{y + diamond_half:.1f} {x - diamond_half:.1f},{y:.1f}"
        parts.append(f'<polygon points="{points}" fill="{fill}" stroke="#0f172a" stroke-width="2.2" />')
        add_label(parts, x, y + 5, label, fill="#0f172a", size=14, weight="700")

    def edge_anchor(point: tuple[float, float], *, direction: str, diamond: bool = False) -> tuple[float, float]:
        x, y = point
        offset = diamond_half if diamond else circle_radius
        if direction == "left":
            return (x - offset, y)
        if direction == "right":
            return (x + offset, y)
        return (x, y)

    def line_label_position(x1: float, y1: float, x2: float, y2: float, *, offset: float = 0) -> tuple[float, float]:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        slope_offset = -16 if y2 < y1 else (18 if y2 > y1 else -10)
        return (mid_x, mid_y + slope_offset + offset)

    usable_width = max(1, len(columns) - 1)
    for index, column_nodes in enumerate(columns):
        x = column_left + (column_right - column_left) * (index / usable_width)
        if len(column_nodes) == 1:
            positions = [(top_y + bottom_y) / 2]
        else:
            positions = _compute_vertical_positions(len(column_nodes), top=top_y, bottom=bottom_y)
        for node, y in zip(column_nodes, positions):
            node_positions[node] = (x, y)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Generic min-cost-flow diagram</title>',
        f'<desc id="desc">DOT-style generic min-cost-flow diagram for {graph_name} showing used shipment paths, unused edges, and the requested flow target.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="26" fill="#f8fafc" />',
        _svg_text(40, 42, "Generic min-cost-flow diagram", size=28, weight="700"),
        _svg_text(
            40,
            68,
            (
                f"Graph: {graph_name} · delivered={flow_result.total_flow} · cost={flow_result.total_cost} · "
                f"target={target_flow if target_flow is not None else 'maximize'} · reached={explanation['target_reached']}"
            ),
            size=14,
            fill="#334155",
        ),
    ]

    for column_index, column_nodes in enumerate(columns):
        if not column_nodes:
            continue
        xs = [node_positions[node][0] for node in column_nodes]
        ys = [node_positions[node][1] for node in column_nodes]
        left = min(xs) - 54
        top = min(ys) - 54
        right = max(xs) + 54
        bottom = max(ys) + 54
        fill = "#e0f2fe" if column_index == 0 else ("#fef3c7" if column_index == len(columns) - 1 else "#ffffff")
        parts.append(
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{right - left:.1f}" height="{bottom - top:.1f}" rx="24" '
            f'fill="{fill}" fill-opacity="0.65" stroke="#d7dee8" stroke-dasharray="7 6" />'
        )
        label = "source" if column_index == 0 else ("sink" if column_index == len(columns) - 1 else f"stage {column_index}")
        parts.append(_svg_text(left + 18, top - 12, label, size=13, weight="700", fill="#475569"))

    marker = (
        '<defs>'
        '<marker id="arrowhead-gray" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        '<polygon points="0 0, 10 3.5, 0 7" fill="#94a3b8" /></marker>'
        '<marker id="arrowhead-green" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        '<polygon points="0 0, 10 3.5, 0 7" fill="#15803d" /></marker>'
        '</defs>'
    )
    parts.insert(4, marker)

    for edge in sorted(flow_result.edge_flows, key=lambda item: (item["source"], item["target"], item["cost"], item["capacity"])):
        source_point = node_positions[edge["source"]]
        target_point = node_positions[edge["target"]]
        start_x, start_y = edge_anchor(source_point, direction="right", diamond=edge["source"] == flow_result.source)
        end_x, end_y = edge_anchor(target_point, direction="left", diamond=edge["target"] == flow_result.sink)
        positive = edge["flow"] > 0
        stroke = "#15803d" if positive else "#94a3b8"
        stroke_width = 4 if positive else 1.6
        stroke_opacity = 0.95 if positive else 0.72
        marker_id = "arrowhead-green" if positive else "arrowhead-gray"
        parts.append(
            f'<line x1="{start_x:.1f}" y1="{start_y:.1f}" x2="{end_x:.1f}" y2="{end_y:.1f}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" stroke-opacity="{stroke_opacity}" marker-end="url(#{marker_id})" />'
        )
        label_x, label_y = line_label_position(start_x, start_y, end_x, end_y)
        add_label(
            parts,
            label_x,
            label_y,
            f"{edge['flow']}/{edge['capacity']} @ {edge['cost']}",
            fill="#166534" if positive else "#64748b",
            size=11,
            weight="700" if positive else "500",
        )

    for node, (x, y) in node_positions.items():
        if node == flow_result.source:
            add_diamond(parts, x, y, node, fill="#dbeafe")
            continue
        if node == flow_result.sink:
            add_diamond(parts, x, y, node, fill="#fef3c7")
            continue
        fill = "#dcfce7" if node in positive_nodes else "#ffffff"
        stroke = "#15803d" if node in positive_nodes else "#475569"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{circle_radius}" fill="{fill}" stroke="{stroke}" stroke-width="2.4" />')
        add_label(parts, x, y + 4, node, fill="#0f172a", size=13, weight="700")

    parts.append(f'<rect x="36" y="{height - 82}" width="868" height="48" rx="16" fill="#ffffff" stroke="#dbe4ee" />')
    add_label(parts, 210, height - 53, "green edge = shipped path segment", fill="#166534", size=12)
    add_label(parts, 492, height - 53, "label = flow/capacity @ unit cost", fill="#475569", size=12)
    add_label(parts, 748, height - 53, "green node = touched by positive flow", fill="#166534", size=12)
    parts.append('</svg>')
    return "\n".join(parts) + "\n"



def render_min_cost_flow_artifact_html(
    flow_result: MinCostFlowResult,
    *,
    graph_name: str = "costed_flow",
    target_flow: int | None = None,
    companion_links: dict[str, str] | None = None,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    explanation = build_min_cost_flow_explanation(flow_result, target_flow=target_flow)
    diagram_svg = _namespace_embedded_svg_accessibility(
        render_min_cost_flow_diagram_svg(flow_result, graph_name=graph_name, target_flow=target_flow),
        prefix="cost-diagram",
    )
    proof_svg = _namespace_embedded_svg_accessibility(
        render_min_cost_flow_svg(flow_result, graph_name=graph_name, target_flow=target_flow),
        prefix="cost-proof",
    )
    positive_flow_items = "".join(
        f"<li><code>{_html_escape(edge['source'])} -&gt; {_html_escape(edge['target'])}</code> · <code>{edge['flow']}/{edge['capacity']}</code> @ cost <code>{edge['cost']}</code></li>"
        for edge in explanation["positive_flow_edges"]
    ) or "<li>No edges carried positive flow.</li>"
    path_items = "".join(
        f"<li><code>{_html_escape(' -> '.join(step['path']))}</code> · bottleneck <code>{step['bottleneck']}</code> · unit cost <code>{step['cost_per_unit']}</code> · path cost <code>{step['path_cost']}</code></li>"
        for step in flow_result.augmenting_paths
    ) or "<li>No augmenting paths were found.</li>"
    narrative_items = "".join(
        f"<li>{_html_escape(line)}</li>"
        for line in explanation["narrative"]
    )
    companion_links = companion_links or {}
    link_labels = {
        "dot": "DOT source",
        "markdown": "Markdown proof",
        "svg": "Standalone proof SVG",
    }
    companion_links_html = "".join(
        f'<li><a href="{_html_escape(path)}">{_html_escape(link_labels[key])}</a></li>'
        for key, path in companion_links.items()
        if key in link_labels
    )
    if not companion_links_html:
        companion_links_html = "<li>This HTML file is self-contained; add --dot-out, --markdown-out, or --svg-out if you want companion artifacts too.</li>"

    requested_flow = target_flow if target_flow is not None else "maximize"
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Generic min-cost-flow artifact page ({_html_escape(graph_name)})</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1500px; padding: 0 1rem 3rem; line-height: 1.5; }}
    h1, h2, h3 {{ line-height: 1.2; }}
    code, pre {{ font-family: 'SFMono-Regular', Consolas, monospace; }}
    .meta, .links {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin: 1rem 0 2rem; padding: 0; }}
    .meta li, .links li {{ list-style: none; padding: 0.8rem 0.95rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.9rem; background: rgba(255, 255, 255, 0.45); }}
    .artifact-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(540px, 1fr)); gap: 1.25rem; margin: 1.5rem 0 2rem; }}
    .artifact-card {{ border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.52); }}
    .artifact-card h2 {{ margin-top: 0; }}
    svg {{ width: 100%; height: auto; display: block; }}
    .detail-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-top: 1rem; }}
    .detail-card {{ padding: 1rem; border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1rem; background: rgba(248, 250, 252, 0.82); }}
    .detail-card h3 {{ margin-top: 0; margin-bottom: 0.75rem; }}
    ul {{ padding-left: 1.2rem; }}
    p.caption {{ margin-top: 0.75rem; color: #475569; }}
  </style>
</head>
<body>
  <h1>Generic min-cost-flow artifact page</h1>
  <p>This page pairs a browser-friendly shipping/routing diagram with the proof card so the generic min-cost-flow story is easy to browse on GitHub Pages without DOT rendering or terminal screenshots.</p>
  <ul class="meta">
    <li><strong>Graph</strong><br><code>{_html_escape(graph_name)}</code></li>
    <li><strong>Generated</strong><br><code>{generated}</code></li>
    <li><strong>Requested flow</strong><br><code>{requested_flow}</code></li>
    <li><strong>Delivered flow</strong><br><code>{flow_result.total_flow}</code></li>
    <li><strong>Total cost</strong><br><code>{flow_result.total_cost}</code></li>
    <li><strong>Target reached</strong><br><code>{str(explanation['target_reached']).lower()}</code></li>
  </ul>
  <div class="artifact-grid">
    <section class="artifact-card">
      <h2>DOT-style shipping/routing diagram</h2>
      {diagram_svg}
      <p class="caption">Green paths show the shipped flow, while gray edges still reveal the unused residual options that the solver chose against.</p>
    </section>
    <section class="artifact-card">
      <h2>Proof card</h2>
      {proof_svg}
      <p class="caption">Use this card when you want the augmenting-path evidence, edge-cost certificate, and target-flow status in one screenshot-friendly block.</p>
    </section>
  </div>
  <div class="detail-grid">
    <section class="detail-card">
      <h3>Edges carrying flow</h3>
      <ul>{positive_flow_items}</ul>
    </section>
    <section class="detail-card">
      <h3>Residual-path narrative</h3>
      <ul>{narrative_items}</ul>
    </section>
    <section class="detail-card">
      <h3>Augmenting paths</h3>
      <ul>{path_items}</ul>
    </section>
    <section class="detail-card">
      <h3>Companion artifacts</h3>
      <ul class="links">{companion_links_html}</ul>
    </section>
  </div>
</body>
</html>
'''



def render_artifact_gallery_html(
    *,
    assignment_page: str,
    assignment_proof_svg: str,
    assignment_markdown: str,
    assignment_dot: str,
    cost_page: str,
    cost_proof_svg: str,
    cost_markdown: str,
    cost_dot: str,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    sections = [
        {
            "eyebrow": "Optimization story #1",
            "title": "Weighted assignment walkthrough",
            "summary": "Start here when you want the bipartite min-cost-flow story in recruiter-friendly form: chosen student/project pairs, proof card, and DOT-style diagram all stay one click away.",
            "preview": assignment_page,
            "preview_title": "Weighted assignment artifact page preview",
            "links": [
                ("Open full artifact page", assignment_page),
                ("Standalone proof SVG", assignment_proof_svg),
                ("Markdown proof", assignment_markdown),
                ("DOT source", assignment_dot),
            ],
        },
        {
            "eyebrow": "Optimization story #2",
            "title": "Generic min-cost-flow walkthrough",
            "summary": "Use this when you want the same engine framed as a shipping/routing example, with shipped edges, path costs, and the browser-friendly proof card side by side.",
            "preview": cost_page,
            "preview_title": "Generic min-cost-flow artifact page preview",
            "links": [
                ("Open full artifact page", cost_page),
                ("Standalone proof SVG", cost_proof_svg),
                ("Markdown proof", cost_markdown),
                ("DOT source", cost_dot),
            ],
        },
    ]

    cards = []
    for section in sections:
        links_html = "".join(
            f'<a class="chip" href="{_html_escape(path)}">{_html_escape(label)}</a>'
            for label, path in section["links"]
        )
        cards.append(
            f'''<section class="gallery-card">
      <p class="eyebrow">{_html_escape(section["eyebrow"])}</p>
      <h2>{_html_escape(section["title"])}</h2>
      <p>{_html_escape(section["summary"])}</p>
      <div class="chip-row">{links_html}</div>
      <iframe src="{_html_escape(section["preview"])}" title="{_html_escape(section["preview_title"])}" loading="lazy"></iframe>
    </section>'''
        )
    cards_html = "\n".join(cards)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Network-flow lab artifact gallery</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1600px; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    h1, h2 {{ line-height: 1.15; }}
    p {{ line-height: 1.55; }}
    .hero {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.4rem; padding: 1.4rem; background: linear-gradient(135deg, rgba(219, 234, 254, 0.9), rgba(236, 253, 245, 0.92)); box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08); }}
    .hero p {{ max-width: 72ch; }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }}
    .hero-meta span {{ padding: 0.55rem 0.85rem; border-radius: 999px; background: rgba(255, 255, 255, 0.72); border: 1px solid rgba(148, 163, 184, 0.35); font-size: 0.95rem; }}
    .gallery-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 1.25rem; margin-top: 1.5rem; }}
    .gallery-card {{ border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 1.2rem; padding: 1.1rem; background: rgba(255, 255, 255, 0.86); box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06); }}
    .gallery-card h2 {{ margin: 0.2rem 0 0.7rem; }}
    .eyebrow {{ margin: 0; font-size: 0.86rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #0f766e; }}
    .chip-row {{ display: flex; flex-wrap: wrap; gap: 0.65rem; margin: 1rem 0 1.1rem; }}
    .chip {{ display: inline-flex; align-items: center; padding: 0.55rem 0.85rem; border-radius: 999px; border: 1px solid rgba(59, 130, 246, 0.28); background: rgba(239, 246, 255, 0.95); color: #1d4ed8; text-decoration: none; font-weight: 600; }}
    .chip:hover {{ background: rgba(219, 234, 254, 1); }}
    iframe {{ width: 100%; min-height: 760px; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 1rem; background: white; }}
    @media (max-width: 760px) {{
      main {{ padding: 1rem 0.75rem 2rem; }}
      iframe {{ min-height: 560px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>Network-flow lab artifact gallery</h1>
      <p>One browser landing page for the two portfolio-friendly optimization stories in this lab: the weighted assignment walkthrough and the generic min-cost-flow shipping walkthrough. Each card keeps the full HTML artifact, proof SVG, Markdown explanation, and DOT source close together so reviewers can browse without hunting through the repo tree.</p>
      <div class="hero-meta">
        <span>Generated <strong>{generated}</strong></span>
        <span>Includes <strong>2</strong> interactive HTML walkthroughs</span>
        <span>Built for GitHub Pages / quick recruiter demos</span>
      </div>
    </section>
    <div class="gallery-grid">
{cards_html}
    </div>
  </main>
</body>
</html>
'''



def render_benchmark_gallery_html(
    *,
    dag_svg: str,
    dag_markdown: str,
    dense_svg: str,
    dense_markdown: str,
    layered_svg: str,
    layered_markdown: str,
    artifact_gallery: str | None = None,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    sections = [
        {
            "eyebrow": "Benchmark family #1",
            "title": "DAG baseline",
            "summary": "The simplest story: acyclic graphs that keep the Edmonds-Karp vs Dinic comparison easy to explain in interviews before moving into nastier residual behavior.",
            "preview": dag_svg,
            "preview_title": "DAG benchmark SVG preview",
            "links": [
                ("Open SVG card", dag_svg),
                ("Open Markdown report", dag_markdown),
            ],
        },
        {
            "eyebrow": "Benchmark family #2",
            "title": "Dense residual mesh",
            "summary": "Use this when you want to show rerouting pressure: shortcut edges, backward middle-layer edges, and more chances for the algorithms to diverge on path work.",
            "preview": dense_svg,
            "preview_title": "Dense benchmark SVG preview",
            "links": [
                ("Open SVG card", dense_svg),
                ("Open Markdown report", dense_markdown),
            ],
        },
        {
            "eyebrow": "Benchmark family #3",
            "title": "Layered cut stress",
            "summary": "This family emphasizes blocking-flow phases and cut-heavy structure, making it the strongest companion when the optimization walkthroughs need a performance-story follow-up.",
            "preview": layered_svg,
            "preview_title": "Layered benchmark SVG preview",
            "links": [
                ("Open SVG card", layered_svg),
                ("Open Markdown report", layered_markdown),
            ],
        },
    ]

    cards = []
    for section in sections:
        links_html = "".join(
            f'<a class="chip" href="{_html_escape(path)}">{_html_escape(label)}</a>'
            for label, path in section["links"]
        )
        cards.append(
            f'''<section class="gallery-card">
      <p class="eyebrow">{_html_escape(section["eyebrow"])}</p>
      <h2>{_html_escape(section["title"])}</h2>
      <p>{_html_escape(section["summary"])}</p>
      <a class="preview-frame" href="{_html_escape(section["preview"])}" aria-label="{_html_escape(section["preview_title"])}">
        <img src="{_html_escape(section["preview"])}" alt="{_html_escape(section["preview_title"])}" loading="lazy" />
      </a>
      <div class="chip-row">{links_html}</div>
    </section>'''
        )
    cards_html = "\n".join(cards)
    sibling_gallery_html = (
        f'<a class="hero-link" href="{_html_escape(artifact_gallery)}">Open optimization artifact gallery</a>'
        if artifact_gallery is not None
        else ''
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Network-flow lab benchmark gallery</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1580px; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    h1, h2 {{ line-height: 1.15; }}
    p {{ line-height: 1.55; }}
    .hero {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.4rem; padding: 1.4rem; background: linear-gradient(135deg, rgba(254, 249, 195, 0.92), rgba(219, 234, 254, 0.92)); box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08); }}
    .hero p {{ max-width: 74ch; }}
    .hero-meta {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }}
    .hero-meta span {{ padding: 0.55rem 0.85rem; border-radius: 999px; background: rgba(255, 255, 255, 0.72); border: 1px solid rgba(148, 163, 184, 0.35); font-size: 0.95rem; }}
    .hero-links {{ display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }}
    .hero-link {{ display: inline-flex; align-items: center; padding: 0.6rem 0.9rem; border-radius: 999px; border: 1px solid rgba(59, 130, 246, 0.28); background: rgba(239, 246, 255, 0.95); color: #1d4ed8; text-decoration: none; font-weight: 700; }}
    .hero-link:hover {{ background: rgba(219, 234, 254, 1); }}
    .gallery-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.2rem; margin-top: 1.5rem; }}
    .gallery-card {{ border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 1.2rem; padding: 1.1rem; background: rgba(255, 255, 255, 0.88); box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06); }}
    .gallery-card h2 {{ margin: 0.2rem 0 0.7rem; }}
    .eyebrow {{ margin: 0; font-size: 0.86rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #1d4ed8; }}
    .preview-frame {{ display: block; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 1rem; background: white; padding: 0.8rem; text-decoration: none; }}
    .preview-frame img {{ display: block; width: 100%; height: auto; border-radius: 0.75rem; }}
    .chip-row {{ display: flex; flex-wrap: wrap; gap: 0.65rem; margin-top: 1rem; }}
    .chip {{ display: inline-flex; align-items: center; padding: 0.55rem 0.85rem; border-radius: 999px; border: 1px solid rgba(59, 130, 246, 0.28); background: rgba(239, 246, 255, 0.95); color: #1d4ed8; text-decoration: none; font-weight: 600; }}
    .chip:hover {{ background: rgba(219, 234, 254, 1); }}
    @media (max-width: 760px) {{
      main {{ padding: 1rem 0.75rem 2rem; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>Network-flow lab benchmark gallery</h1>
      <p>A lightweight browser landing page for the committed benchmark report cards. Use it when the algorithm walkthroughs need a performance companion: reviewers can compare the DAG baseline, dense residual mesh, and layered cut-stress stories without digging through the repo tree.</p>
      <div class="hero-meta">
        <span>Generated <strong>{generated}</strong></span>
        <span>Includes <strong>3</strong> benchmark report families</span>
        <span>Optimized for GitHub Pages / recruiter browsing</span>
      </div>
      <div class="hero-links">{sibling_gallery_html}</div>
    </section>
    <div class="gallery-grid">
{cards_html}
    </div>
  </main>
</body>
</html>
'''



def render_showcase_html(
    *,
    artifact_gallery: str,
    benchmark_gallery: str,
    flow_svg: str,
    flow_markdown: str,
    matching_svg: str,
    matching_markdown: str,
    assignment_page: str,
    assignment_svg: str,
    assignment_markdown: str,
    assignment_dot: str,
    cost_page: str,
    cost_svg: str,
    cost_markdown: str,
    cost_dot: str,
    dag_svg: str,
    dag_markdown: str,
    dense_svg: str,
    dense_markdown: str,
    layered_svg: str,
    layered_markdown: str,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    cards = [
        {
            "title": "Max-flow proof card",
            "eyebrow": "Core proof",
            "summary": "Lead with this when you want the pure Edmonds-Karp / Dinic correctness story without extra reductions.",
            "preview_kind": "image",
            "preview": flow_svg,
            "preview_title": "Max-flow proof SVG preview",
            "tags": ["proof", "svg", "markdown"],
            "links": [("Open SVG card", flow_svg), ("Open Markdown proof", flow_markdown)],
        },
        {
            "title": "Bipartite matching proof card",
            "eyebrow": "Core proof",
            "summary": "Shows the matching-to-flow reduction and the minimum vertex-cover follow-up in one interviewer-friendly artifact.",
            "preview_kind": "image",
            "preview": matching_svg,
            "preview_title": "Matching proof SVG preview",
            "tags": ["proof", "svg", "markdown"],
            "links": [("Open SVG card", matching_svg), ("Open Markdown proof", matching_markdown)],
        },
        {
            "title": "Weighted assignment walkthrough",
            "eyebrow": "Optimization walkthrough",
            "summary": "Browser-friendly assignment story with the HTML walkthrough, proof SVG, Markdown explanation, and DOT diagram grouped together.",
            "preview_kind": "iframe",
            "preview": assignment_page,
            "preview_title": "Weighted assignment walkthrough preview",
            "tags": ["walkthrough", "html", "proof", "svg", "markdown", "dot"],
            "links": [
                ("Open HTML walkthrough", assignment_page),
                ("Open SVG card", assignment_svg),
                ("Open Markdown proof", assignment_markdown),
                ("Open DOT diagram", assignment_dot),
            ],
        },
        {
            "title": "Generic min-cost-flow walkthrough",
            "eyebrow": "Optimization walkthrough",
            "summary": "Use this when the same engine needs to look like a shipping/routing optimization demo instead of a bipartite assignment reduction.",
            "preview_kind": "iframe",
            "preview": cost_page,
            "preview_title": "Generic min-cost-flow walkthrough preview",
            "tags": ["walkthrough", "html", "proof", "svg", "markdown", "dot"],
            "links": [
                ("Open HTML walkthrough", cost_page),
                ("Open SVG card", cost_svg),
                ("Open Markdown proof", cost_markdown),
                ("Open DOT diagram", cost_dot),
            ],
        },
        {
            "title": "DAG baseline benchmark",
            "eyebrow": "Benchmark report",
            "summary": "The simplest performance story: a clean acyclic baseline before the denser residual-heavy families.",
            "preview_kind": "image",
            "preview": dag_svg,
            "preview_title": "DAG benchmark SVG preview",
            "tags": ["benchmark", "svg", "markdown"],
            "links": [("Open SVG card", dag_svg), ("Open Markdown report", dag_markdown)],
        },
        {
            "title": "Dense residual benchmark",
            "eyebrow": "Benchmark report",
            "summary": "Best for showing rerouting pressure and how the algorithm traces diverge once the graph gets messy.",
            "preview_kind": "image",
            "preview": dense_svg,
            "preview_title": "Dense benchmark SVG preview",
            "tags": ["benchmark", "svg", "markdown"],
            "links": [("Open SVG card", dense_svg), ("Open Markdown report", dense_markdown)],
        },
        {
            "title": "Layered cut-stress benchmark",
            "eyebrow": "Benchmark report",
            "summary": "The strongest companion when you want a blocking-flow / cut-heavy performance follow-up beside the optimization walkthroughs.",
            "preview_kind": "image",
            "preview": layered_svg,
            "preview_title": "Layered benchmark SVG preview",
            "tags": ["benchmark", "svg", "markdown"],
            "links": [("Open SVG card", layered_svg), ("Open Markdown report", layered_markdown)],
        },
    ]

    card_parts = []
    for card in cards:
        links_html = ''.join(
            f'<a class="chip" href="{_html_escape(path)}">{_html_escape(label)}</a>'
            for label, path in card["links"]
        )
        badges_html = ''.join(
            f'<span class="badge">{_html_escape(tag)}</span>'
            for tag in card["tags"]
        )
        if card["preview_kind"] == "iframe":
            preview_html = (
                f'<iframe src="{_html_escape(card["preview"])}" '
                f'title="{_html_escape(card["preview_title"])}" loading="lazy"></iframe>'
            )
        else:
            preview_html = (
                f'<a class="preview-frame" href="{_html_escape(card["preview"])}" '
                f'aria-label="{_html_escape(card["preview_title"])}">'
                f'<img src="{_html_escape(card["preview"])}" alt="{_html_escape(card["preview_title"])}" loading="lazy" />'
                '</a>'
            )
        card_parts.append(
            f'''<article class="showcase-card" data-tags="{' '.join(card["tags"])}">
      <p class="eyebrow">{_html_escape(card["eyebrow"])}</p>
      <h2>{_html_escape(card["title"])}</h2>
      <p>{_html_escape(card["summary"])}</p>
      <div class="badge-row">{badges_html}</div>
      {preview_html}
      <div class="chip-row">{links_html}</div>
    </article>'''
        )
    cards_html = "\n".join(card_parts)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Network-flow lab showcase</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1680px; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    h1, h2 {{ line-height: 1.1; }}
    p {{ line-height: 1.55; }}
    .hero {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.5rem; padding: 1.5rem; background: linear-gradient(135deg, rgba(224, 231, 255, 0.94), rgba(236, 253, 245, 0.92)); box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08); }}
    .hero p {{ max-width: 78ch; }}
    .hero-meta, .hero-links, .filter-row, .chip-row, .badge-row {{ display: flex; flex-wrap: wrap; gap: 0.75rem; }}
    .hero-meta {{ margin-top: 1rem; }}
    .hero-meta span, .badge {{ padding: 0.45rem 0.78rem; border-radius: 999px; background: rgba(255, 255, 255, 0.78); border: 1px solid rgba(148, 163, 184, 0.35); font-size: 0.92rem; }}
    .hero-links {{ margin-top: 1rem; }}
    .hero-link, .chip, .filter-button {{ display: inline-flex; align-items: center; justify-content: center; padding: 0.58rem 0.9rem; border-radius: 999px; border: 1px solid rgba(59, 130, 246, 0.28); background: rgba(239, 246, 255, 0.95); color: #1d4ed8; text-decoration: none; font-weight: 700; cursor: pointer; }}
    .hero-link:hover, .chip:hover, .filter-button:hover {{ background: rgba(219, 234, 254, 1); }}
    .filter-button[aria-pressed="true"] {{ background: #1d4ed8; color: white; border-color: #1d4ed8; }}
    .filters {{ margin-top: 1.35rem; border: 1px solid rgba(148, 163, 184, 0.22); border-radius: 1.2rem; padding: 1rem; background: rgba(255, 255, 255, 0.76); }}
    .filters p {{ margin: 0 0 0.85rem; color: #334155; }}
    .showcase-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.2rem; margin-top: 1.5rem; }}
    .showcase-card {{ border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 1.25rem; padding: 1.05rem; background: rgba(255, 255, 255, 0.88); box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06); }}
    .showcase-card[hidden] {{ display: none; }}
    .showcase-card h2 {{ margin: 0.22rem 0 0.7rem; }}
    .eyebrow {{ margin: 0; font-size: 0.86rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #0f766e; }}
    .preview-frame {{ display: block; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 1rem; background: white; padding: 0.85rem; text-decoration: none; margin-top: 0.95rem; }}
    .preview-frame img {{ display: block; width: 100%; height: auto; border-radius: 0.75rem; }}
    iframe {{ width: 100%; min-height: 420px; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 1rem; background: white; margin-top: 0.95rem; }}
    .chip-row {{ margin-top: 1rem; }}
    @media (max-width: 760px) {{
      main {{ padding: 1rem 0.75rem 2rem; }}
      iframe {{ min-height: 320px; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>Network-flow lab showcase</h1>
      <p>A single browser-friendly hub for the committed <code>network-flow-lab</code> artifacts. Use the filters to jump between proof cards, HTML walkthroughs, DOT-backed optimization demos, and benchmark reports without digging through the repo tree. The two gallery pages are still linked directly when you want a broader optimization-only or benchmark-only view.</p>
      <div class="hero-meta">
        <span>Generated <strong>{generated}</strong></span>
        <span>Includes <strong>7</strong> artifact groups</span>
        <span>Filters: proof / html / benchmark / markdown / dot</span>
      </div>
      <div class="hero-links">
        <a class="hero-link" href="{_html_escape(artifact_gallery)}">Open optimization gallery</a>
        <a class="hero-link" href="{_html_escape(benchmark_gallery)}">Open benchmark gallery</a>
      </div>
      <section class="filters" aria-labelledby="showcase-filter-heading">
        <p id="showcase-filter-heading"><strong>Quick filters</strong> — cards stay visible when they match the selected tag.</p>
        <div class="filter-row" role="toolbar" aria-label="Artifact filters">
          <button type="button" class="filter-button" data-filter="all" aria-pressed="true">All</button>
          <button type="button" class="filter-button" data-filter="proof" aria-pressed="false">Proof cards</button>
          <button type="button" class="filter-button" data-filter="html" aria-pressed="false">HTML walkthroughs</button>
          <button type="button" class="filter-button" data-filter="benchmark" aria-pressed="false">Benchmark reports</button>
          <button type="button" class="filter-button" data-filter="markdown" aria-pressed="false">Markdown companions</button>
          <button type="button" class="filter-button" data-filter="dot" aria-pressed="false">DOT diagrams</button>
        </div>
      </section>
    </section>
    <section class="showcase-grid" id="showcase-grid">
{cards_html}
    </section>
  </main>
  <script>
    const buttons = Array.from(document.querySelectorAll('.filter-button'));
    const cards = Array.from(document.querySelectorAll('.showcase-card'));
    const applyFilter = (filter) => {{
      buttons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.filter === filter)));
      cards.forEach((card) => {{
        const tags = (card.dataset.tags || '').split(/\\s+/).filter(Boolean);
        card.hidden = filter !== 'all' && !tags.includes(filter);
      }});
    }};
    buttons.forEach((button) => button.addEventListener('click', () => applyFilter(button.dataset.filter || 'all')));
  </script>
</body>
</html>
'''


def render_assignment_svg(assignment_result: AssignmentResult, *, graph_name: str = "weighted_assignment") -> str:
    explanation = build_assignment_explanation(assignment_result)
    width = 960
    height = 640
    displayed_assignments = assignment_result.assignments[:6]
    hidden_assignments = max(0, len(assignment_result.assignments) - len(displayed_assignments))
    displayed_paths = assignment_result.flow["augmenting_paths"][:5]
    hidden_paths = max(0, len(assignment_result.flow["augmenting_paths"]) - len(displayed_paths))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Weighted assignment proof card</title>',
        f'<desc id="desc">Proof-style summary card for {graph_name} showing the chosen weighted assignment and min-cost-flow certificate.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fafc" />',
        _svg_text(28, 42, "Weighted assignment proof card", size=28, weight="700"),
        _svg_text(28, 68, f"Graph: {graph_name} · left={len(assignment_result.left_partition)} · right={len(assignment_result.right_partition)}", size=14, fill="#334155"),
    ]

    stat_cards = [
        (28, "Algorithm", assignment_result.flow["algorithm"], "successive shortest paths over the residual graph"),
        (258, "Assignments", str(len(assignment_result.assignments)), "selected left-right pairs"),
        (488, "Total cost", str(assignment_result.total_cost), "sum of chosen edge weights"),
        (718, "Full coverage", str(assignment_result.covers_smaller_partition), f"augmenting paths: {len(assignment_result.flow['augmenting_paths'])}"),
    ]
    for x, label, value, subtitle in stat_cards:
        parts.append(f'<rect x="{x}" y="96" width="202" height="88" rx="18" fill="#ffffff" stroke="#cbd5e1" />')
        parts.append(_svg_text(x + 16, 124, label, size=13, weight="600", fill="#475569"))
        parts.append(_svg_text(x + 16, 154, value, size=24, weight="700"))
        parts.append(_svg_text(x + 16, 176, _truncate_svg_text(subtitle, 34), size=12, fill="#64748b"))

    section_top = 218
    parts.append('<rect x="28" y="218" width="420" height="380" rx="24" fill="#ffffff" stroke="#cbd5e1" />')
    parts.append(_svg_text(48, section_top + 26, "Selected assignments", size=20, weight="700"))
    current_y = section_top + 56
    if displayed_assignments:
        for item in displayed_assignments:
            line = f"{item['left']} -> {item['right']} (cost {item['cost']})"
            parts.append(_svg_text(48, current_y, _truncate_svg_text(line, 46), size=15, weight="600", fill="#0f172a"))
            current_y += 26
    else:
        parts.append(_svg_text(48, current_y, "(no feasible assignment edges carried flow)", size=15, fill="#475569"))
        current_y += 26
    if hidden_assignments:
        parts.append(_svg_text(48, current_y, f"+ {hidden_assignments} more selected pair(s)", size=13, fill="#64748b"))
        current_y += 24
    current_y += 10
    current_y = _svg_add_wrapped_text(
        parts,
        48,
        current_y,
        f"Unmatched left: {', '.join(assignment_result.unmatched_left) if assignment_result.unmatched_left else '(none)'}",
        max_chars=46,
        size=13,
        weight="600",
    ) + 24
    _svg_add_wrapped_text(
        parts,
        48,
        current_y,
        f"Unmatched right: {', '.join(assignment_result.unmatched_right) if assignment_result.unmatched_right else '(none)'}",
        max_chars=46,
        size=13,
        weight="600",
    )

    parts.append('<rect x="478" y="218" width="454" height="380" rx="24" fill="#ffffff" stroke="#cbd5e1" />')
    parts.append(_svg_text(498, section_top + 26, "Min-cost-flow certificate", size=20, weight="700"))
    current_y = section_top + 54
    for line in explanation["narrative"]:
        current_y = _svg_add_wrapped_text(parts, 498, current_y, line, max_chars=50, size=13) + 22
    parts.append(_svg_text(498, current_y, "Augmenting paths", size=16, weight="700"))
    current_y += 24
    for index, step in enumerate(displayed_paths, start=1):
        path_text = " -> ".join(_humanize_assignment_path(step["path"]))
        summary = f"#{index}: bottleneck {step['bottleneck']} · unit cost {step['cost_per_unit']} · total {step['path_cost']}"
        current_y = _svg_add_wrapped_text(parts, 498, current_y, summary, max_chars=50, size=13, weight="600", fill="#0f172a") + 18
        current_y = _svg_add_wrapped_text(parts, 514, current_y, path_text, max_chars=46, size=12, fill="#475569") + 20
    if hidden_paths:
        parts.append(_svg_text(498, min(current_y, 572), f"+ {hidden_paths} more augmenting path(s)", size=12, fill="#64748b"))

    parts.append(_svg_text(28, 622, "Tip: pair this card with the max-flow proof SVGs to show both feasibility and optimization storytelling.", size=12, fill="#64748b"))
    parts.append("</svg>")
    return "\n".join(parts)



def render_assignment_diagram_svg(assignment_result: AssignmentResult, *, graph_name: str = "weighted_assignment") -> str:
    width = 920
    rows = max(len(assignment_result.left_partition), len(assignment_result.right_partition), 1)
    height = max(420, 220 + rows * 92)
    left_x = 286
    right_x = 634
    source_x = 96
    sink_x = 824
    top_y = 176
    bottom_y = height - 106
    circle_radius = 28
    right_box_width = 110
    right_box_height = 46
    diamond_half = 30
    label_font = 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'

    flow_edges = {
        (item["source"], item["target"]): item
        for item in assignment_result.flow["edge_flows"]
    }
    selected_pairs = {
        (item["left"], item["right"]): item["cost"]
        for item in assignment_result.assignments
    }
    selected_left = {item["left"] for item in assignment_result.assignments}
    selected_right = {item["right"] for item in assignment_result.assignments}

    left_positions = {
        node: (left_x, y)
        for node, y in zip(
            assignment_result.left_partition,
            _compute_vertical_positions(len(assignment_result.left_partition), top=top_y, bottom=bottom_y),
        )
    }
    right_positions = {
        node: (right_x, y)
        for node, y in zip(
            assignment_result.right_partition,
            _compute_vertical_positions(len(assignment_result.right_partition), top=top_y, bottom=bottom_y),
        )
    }
    center_y = (top_y + bottom_y) / 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Weighted assignment diagram</title>',
        f'<desc id="desc">DOT-style weighted assignment diagram for {graph_name} showing selected pairs, unmatched vertices, and source or sink capacities.</desc>',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="26" fill="#f8fafc" />',
        f'<rect x="188" y="118" width="196" height="{height - 214}" rx="26" fill="#eff6ff" stroke="#64748b" stroke-dasharray="8 6" />',
        f'<rect x="540" y="118" width="196" height="{height - 214}" rx="26" fill="#ecfdf5" stroke="#4d7c0f" stroke-dasharray="8 6" />',
        _svg_text(40, 42, "Weighted assignment diagram", size=28, weight="700"),
        _svg_text(40, 68, f"Graph: {graph_name} · selected={len(assignment_result.assignments)} · cost={assignment_result.total_cost} · full coverage={assignment_result.covers_smaller_partition}", size=14, fill="#334155"),
        _svg_text(226, 106, "left partition", size=15, weight="700", fill="#334155"),
        _svg_text(580, 106, "right partition", size=15, weight="700", fill="#334155"),
    ]

    def add_label(x: float, y: float, text: str, *, fill: str = "#475569", size: int = 12, weight: str = "600") -> None:
        parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" font-family=\'{label_font}\'>{_svg_escape(text)}</text>'
        )

    def add_diamond(x: float, y: float, label: str) -> None:
        points = f"{x:.1f},{y - diamond_half:.1f} {x + diamond_half:.1f},{y:.1f} {x:.1f},{y + diamond_half:.1f} {x - diamond_half:.1f},{y:.1f}"
        parts.append(f'<polygon points="{points}" fill="#ffffff" stroke="#0f172a" stroke-width="2" />')
        add_label(x, y + 5, label, fill="#0f172a", size=14, weight="700")

    def edge_anchor(point: tuple[float, float], *, direction: str, box: bool = False) -> tuple[float, float]:
        x, y = point
        if box:
            offset = right_box_width / 2
        else:
            offset = circle_radius
        if direction == "left":
            return (x - offset, y)
        if direction == "right":
            return (x + offset, y)
        return (x, y)

    def line_label_position(x1: float, y1: float, x2: float, y2: float, *, offset: float = 0) -> tuple[float, float]:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        slope_offset = -14 if y2 < y1 else (18 if y2 > y1 else -10)
        return (mid_x, mid_y + slope_offset + offset)

    add_diamond(source_x, center_y, "source")
    add_diamond(sink_x, center_y, "sink")

    for node in assignment_result.left_partition:
        x, y = left_positions[node]
        edge = flow_edges.get((ASSIGN_SOURCE, node))
        selected = bool(edge and edge["flow"] == 1)
        start_x = source_x + diamond_half
        end_x = x - circle_radius
        parts.append(
            f'<line x1="{start_x:.1f}" y1="{center_y:.1f}" x2="{end_x:.1f}" y2="{y:.1f}" '
            f'stroke="{"#6b7280" if selected else "#cbd5e1"}" stroke-width="{2.4 if selected else 1.6}" stroke-dasharray="8 6" />'
        )
        label_x, label_y = line_label_position(start_x, center_y, end_x, y, offset=-8)
        add_label(label_x, label_y, "1" if selected else "0/1", fill="#64748b", size=11)

    for node in assignment_result.right_partition:
        x, y = right_positions[node]
        edge = flow_edges.get((node, ASSIGN_SINK))
        selected = bool(edge and edge["flow"] == 1)
        start_x = x + right_box_width / 2
        end_x = sink_x - diamond_half
        parts.append(
            f'<line x1="{start_x:.1f}" y1="{y:.1f}" x2="{end_x:.1f}" y2="{center_y:.1f}" '
            f'stroke="{"#6b7280" if selected else "#cbd5e1"}" stroke-width="{2.4 if selected else 1.6}" stroke-dasharray="8 6" />'
        )
        label_x, label_y = line_label_position(start_x, y, end_x, center_y, offset=-8)
        add_label(label_x, label_y, "1" if selected else "0/1", fill="#64748b", size=11)

    for edge in sorted(
        (
            item
            for item in assignment_result.flow["edge_flows"]
            if item["source"] in left_positions and item["target"] in right_positions
        ),
        key=lambda item: (item["source"], item["target"], item["cost"], item["capacity"]),
    ):
        start_x, start_y = edge_anchor(left_positions[edge["source"]], direction="right")
        end_x, end_y = edge_anchor(right_positions[edge["target"]], direction="left", box=True)
        selected = (edge["source"], edge["target"]) in selected_pairs
        stroke = "#15803d" if selected else "#94a3b8"
        stroke_width = 4 if selected else 1.5
        stroke_opacity = 0.95 if selected else 0.72
        parts.append(
            f'<line x1="{start_x:.1f}" y1="{start_y:.1f}" x2="{end_x:.1f}" y2="{end_y:.1f}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" stroke-opacity="{stroke_opacity}" />'
        )
        label_x, label_y = line_label_position(start_x, start_y, end_x, end_y)
        label_text = f"selected @ {edge['cost']}" if selected else f"cost {edge['cost']}"
        add_label(label_x, label_y, label_text, fill="#166534" if selected else "#64748b", size=11, weight="700" if selected else "500")

    for node in assignment_result.left_partition:
        x, y = left_positions[node]
        fill = "#fda4af" if node in assignment_result.unmatched_left else ("#dcfce7" if node in selected_left else "#dbeafe")
        stroke = "#b91c1c" if node in assignment_result.unmatched_left else "#2563eb"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{circle_radius}" fill="{fill}" stroke="{stroke}" stroke-width="2.4" />')
        add_label(x, y + 4, node, fill="#0f172a", size=13, weight="700")

    for node in assignment_result.right_partition:
        x, y = right_positions[node]
        fill = "#ffedd5" if node in assignment_result.unmatched_right else "#ecfccb"
        stroke_width = 3 if node in selected_right else 2
        stroke = "#b45309" if node in assignment_result.unmatched_right else "#15803d"
        parts.append(
            f'<rect x="{x - right_box_width / 2:.1f}" y="{y - right_box_height / 2:.1f}" width="{right_box_width}" height="{right_box_height}" '
            f'rx="14" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
        )
        add_label(x, y + 4, node, fill="#0f172a", size=13, weight="700")

    parts.append(f'<rect x="34" y="{height - 76}" width="852" height="42" rx="16" fill="#ffffff" stroke="#dbe4ee" />')
    add_label(194, height - 50, "green edge = selected pair", fill="#166534", size=12)
    add_label(474, height - 50, "pink or orange node = unmatched vertex", fill="#7c2d12", size=12)
    add_label(730, height - 50, "dashed source or sink edges show unit-capacity usage", fill="#475569", size=12)
    parts.append('</svg>')
    return "\n".join(parts) + "\n"



def render_assignment_artifact_html(
    assignment_result: AssignmentResult,
    *,
    graph_name: str = "weighted_assignment",
    companion_links: dict[str, str] | None = None,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    explanation = build_assignment_explanation(assignment_result)
    diagram_svg = _namespace_embedded_svg_accessibility(
        render_assignment_diagram_svg(assignment_result, graph_name=graph_name),
        prefix="assignment-diagram",
    )
    proof_svg = _namespace_embedded_svg_accessibility(
        render_assignment_svg(assignment_result, graph_name=graph_name),
        prefix="assignment-proof",
    )
    selected_assignment_items = "".join(
        f"<li><code>{_html_escape(item['left'])} -&gt; {_html_escape(item['right'])}</code> · cost <code>{item['cost']}</code></li>"
        for item in assignment_result.assignments
    ) or "<li>No assignment edges carried flow.</li>"
    narrative_items = "".join(
        f"<li>{_html_escape(line)}</li>"
        for line in explanation["narrative"]
    )
    companion_links = companion_links or {}
    link_labels = {
        "dot": "DOT source",
        "markdown": "Markdown proof",
        "svg": "Standalone proof SVG",
    }
    companion_links_html = "".join(
        f'<li><a href="{_html_escape(path)}">{_html_escape(link_labels[key])}</a></li>'
        for key, path in companion_links.items()
        if key in link_labels
    )
    if not companion_links_html:
        companion_links_html = "<li>This HTML file is self-contained; add --dot-out, --markdown-out, or --svg-out if you want companion artifacts too.</li>"

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Weighted assignment artifact page ({_html_escape(graph_name)})</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 2rem auto; max-width: 1500px; padding: 0 1rem 3rem; line-height: 1.5; }}
    h1, h2, h3 {{ line-height: 1.2; }}
    code, pre {{ font-family: 'SFMono-Regular', Consolas, monospace; }}
    .meta, .links {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin: 1rem 0 2rem; padding: 0; }}
    .meta li, .links li {{ list-style: none; padding: 0.8rem 0.95rem; border: 1px solid rgba(148, 163, 184, 0.35); border-radius: 0.9rem; background: rgba(255, 255, 255, 0.45); }}
    .artifact-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(540px, 1fr)); gap: 1.25rem; margin: 1.5rem 0 2rem; }}
    .artifact-card {{ border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 1rem; padding: 1rem; background: rgba(255, 255, 255, 0.52); }}
    .artifact-card h2 {{ margin-top: 0; }}
    svg {{ width: 100%; height: auto; display: block; }}
    .detail-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-top: 1rem; }}
    .detail-card {{ padding: 1rem; border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1rem; background: rgba(248, 250, 252, 0.82); }}
    .detail-card h3 {{ margin-top: 0; margin-bottom: 0.75rem; }}
    ul {{ padding-left: 1.2rem; }}
    p.caption {{ margin-top: 0.75rem; color: #475569; }}
  </style>
</head>
<body>
  <h1>Weighted assignment artifact page</h1>
  <p>This page pairs the DOT-style assignment diagram with the proof card so the weighted bipartite min-cost-flow story is easy to browse on GitHub Pages without terminal screenshots.</p>
  <ul class=\"meta\">
    <li><strong>Graph</strong><br><code>{_html_escape(graph_name)}</code></li>
    <li><strong>Generated</strong><br><code>{generated}</code></li>
    <li><strong>Assignments</strong><br><code>{len(assignment_result.assignments)}</code></li>
    <li><strong>Total cost</strong><br><code>{assignment_result.total_cost}</code></li>
    <li><strong>Full coverage</strong><br><code>{str(assignment_result.covers_smaller_partition).lower()}</code></li>
    <li><strong>Solver</strong><br><code>{_html_escape(str(assignment_result.flow['algorithm']))}</code></li>
  </ul>
  <div class=\"artifact-grid\">
    <section class=\"artifact-card\">
      <h2>DOT-style assignment diagram</h2>
      {diagram_svg}
      <p class=\"caption\">Selected pairs stay green and unmatched vertices are highlighted, matching the same story as the DOT export without depending on Graphviz during browsing.</p>
    </section>
    <section class=\"artifact-card\">
      <h2>Proof card</h2>
      {proof_svg}
      <p class=\"caption\">Use this card when you want the optimization certificate, augmenting-path evidence, and coverage summary in one screenshot-friendly block.</p>
    </section>
  </div>
  <div class=\"detail-grid\">
    <section class=\"detail-card\">
      <h3>Selected assignments</h3>
      <ul>{selected_assignment_items}</ul>
    </section>
    <section class=\"detail-card\">
      <h3>Why the certificate works</h3>
      <ul>{narrative_items}</ul>
    </section>
    <section class=\"detail-card\">
      <h3>Companion artifacts</h3>
      <ul class=\"links\">{companion_links_html}</ul>
    </section>
  </div>
</body>
</html>
"""



def render_min_cost_flow_markdown(
    flow_result: MinCostFlowResult,
    *,
    graph_name: str = "costed_flow",
    target_flow: int | None = None,
) -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    explanation = build_min_cost_flow_explanation(flow_result, target_flow=target_flow)
    positive_edge_lines = "\n".join(
        f"- `{edge['source']} -> {edge['target']}` carries `{edge['flow']}/{edge['capacity']}` at unit cost `{edge['cost']}`"
        for edge in explanation["positive_flow_edges"]
    ) or "- (no edges carried positive flow)"
    path_lines = "\n".join(
        f"- `{ ' -> '.join(step['path']) }` · bottleneck `{step['bottleneck']}` · unit cost `{step['cost_per_unit']}` · path cost `{step['path_cost']}`"
        for step in flow_result.augmenting_paths
    ) or "- (no augmenting paths)"
    narrative = "\n".join(f"- {line}" for line in explanation["narrative"])
    requested_flow = target_flow if target_flow is not None else "maximize until no augmenting path remains"
    return f"""# Min-cost flow proof artifact: `{graph_name}`

- Generated: `{generated}`
- Solver: `{flow_result.algorithm}`
- Requested flow: `{requested_flow}`
- Delivered flow: `{flow_result.total_flow}`
- Total cost: `{flow_result.total_cost}`
- Average cost per unit: `{explanation['average_cost_per_unit']}`

## Edges carrying flow

{positive_edge_lines}

## Coverage summary

- Target reached: `{explanation['target_reached']}`
- Cost matches used edges: `{explanation['cost_matches_used_edges']}`

## Residual-path narrative

{narrative}

## Augmenting paths

{path_lines}
"""


def render_assignment_markdown(assignment_result: AssignmentResult, *, graph_name: str = "weighted_assignment") -> str:
    generated = datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
    explanation = build_assignment_explanation(assignment_result)
    assignment_lines = "\n".join(
        f"- `{item['left']} -> {item['right']}` with cost `{item['cost']}`"
        for item in assignment_result.assignments
    ) or "- (no selected assignments)"
    unmatched_left = ", ".join(assignment_result.unmatched_left) if assignment_result.unmatched_left else "(none)"
    unmatched_right = ", ".join(assignment_result.unmatched_right) if assignment_result.unmatched_right else "(none)"
    path_lines = "\n".join(
        f"- `{ ' -> '.join(_humanize_assignment_path(step['path'])) }` · bottleneck `{step['bottleneck']}` · unit cost `{step['cost_per_unit']}` · path cost `{step['path_cost']}`"
        for step in assignment_result.flow["augmenting_paths"]
    ) or "- (no augmenting paths)"
    narrative = "\n".join(f"- {line}" for line in explanation["narrative"])
    return f"""# Weighted assignment proof artifact: `{graph_name}`

- Generated: `{generated}`
- Solver: `{assignment_result.flow['algorithm']}`
- Selected assignments: `{len(assignment_result.assignments)}`
- Total cost: `{assignment_result.total_cost}`
- Covers smaller partition: `{assignment_result.covers_smaller_partition}`

## Selected assignments

{assignment_lines}

## Coverage summary

- Unmatched left: `{unmatched_left}`
- Unmatched right: `{unmatched_right}`
- Cost matches selected edges: `{explanation['cost_matches_flow_total']}`

## Min-cost-flow narrative

{narrative}

## Augmenting paths

{path_lines}
"""



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


def write_html_output(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def add_explain_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--explain",
        action="store_true",
        help="include a compact proof-style explanation of the computed result",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Solve max-flow graphs, bipartite matchings, weighted assignments, and generic min-cost-flow graphs.")
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

    assign_parser = subparsers.add_parser("assign", help="solve a weighted assignment JSON file")
    assign_parser.add_argument("graph", type=Path, help="path to weighted assignment JSON")
    assign_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    assign_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the solved weighted assignment graph")
    assign_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the solved assignment graph")
    assign_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the solved assignment graph")
    assign_parser.add_argument("--html-out", type=Path, help="write a self-contained HTML artifact page that places the assignment diagram next to the proof card")
    add_explain_argument(assign_parser)

    assign_demo_parser = subparsers.add_parser("assign-demo", help="run the bundled weighted assignment sample")
    assign_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    assign_demo_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the sample weighted assignment graph")
    assign_demo_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the sample assignment graph")
    assign_demo_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the sample assignment graph")
    assign_demo_parser.add_argument("--html-out", type=Path, help="write a self-contained HTML artifact page that places the assignment diagram next to the proof card")
    add_explain_argument(assign_demo_parser)

    cost_parser = subparsers.add_parser("cost-solve", help="solve a generic min-cost-flow JSON file")
    cost_parser.add_argument("graph", type=Path, help="path to generic min-cost-flow JSON")
    cost_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    cost_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the solved costed flow graph")
    cost_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the solved costed flow graph")
    cost_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the solved costed flow graph")
    cost_parser.add_argument("--html-out", type=Path, help="write a self-contained HTML artifact page that places the shipping/routing diagram next to the proof card")
    add_explain_argument(cost_parser)

    cost_demo_parser = subparsers.add_parser("cost-demo", help="run the bundled generic min-cost-flow sample")
    cost_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    cost_demo_parser.add_argument("--dot-out", type=Path, help="write a Graphviz DOT file for the sample costed flow graph")
    cost_demo_parser.add_argument("--markdown-out", type=Path, help="write a standalone Markdown proof artifact for the sample costed flow graph")
    cost_demo_parser.add_argument("--svg-out", type=Path, help="write a standalone SVG proof card for the sample costed flow graph")
    cost_demo_parser.add_argument("--html-out", type=Path, help="write a self-contained HTML artifact page that places the shipping/routing diagram next to the proof card")
    add_explain_argument(cost_demo_parser)

    gallery_demo_parser = subparsers.add_parser("gallery-demo", help="write a tiny HTML gallery that links the bundled assignment and min-cost-flow artifact pages")
    gallery_demo_parser.add_argument("--html-out", type=Path, required=True, help="write a static HTML gallery that links the committed assignment and cost-flow artifact pages")
    gallery_demo_parser.add_argument("--artifact-dir", type=Path, help="directory that already contains the sample assignment/cost-flow HTML pages plus their proof companions; defaults to the output directory")
    gallery_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")

    benchmark_gallery_demo_parser = subparsers.add_parser("benchmark-gallery-demo", help="write a tiny HTML gallery that links the bundled benchmark report cards")
    benchmark_gallery_demo_parser.add_argument("--html-out", type=Path, required=True, help="write a static HTML gallery that links the committed benchmark report cards")
    benchmark_gallery_demo_parser.add_argument("--artifact-dir", type=Path, help="directory that already contains the sample benchmark Markdown/SVG artifacts; defaults to the output directory")
    benchmark_gallery_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")

    showcase_demo_parser = subparsers.add_parser("showcase-demo", help="write a filterable HTML hub for the bundled proof, walkthrough, and benchmark artifacts")
    showcase_demo_parser.add_argument("--html-out", type=Path, required=True, help="write a static HTML showcase page that links the committed artifact galleries plus their core proof/report companions")
    showcase_demo_parser.add_argument("--artifact-dir", type=Path, help="directory that already contains the committed HTML/SVG/Markdown/DOT artifacts; defaults to the output directory")
    showcase_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")

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
    if args.command == "gallery-demo":
        artifact_paths = build_artifact_gallery_paths(
            html_out=args.html_out,
            artifact_dir=getattr(args, "artifact_dir", None),
        )
        missing = [path.name for path in artifact_paths.values() if not path.exists()]
        if missing:
            parser.error(
                "gallery-demo requires the bundled assignment/cost-flow artifacts to exist first; missing: "
                + ", ".join(sorted(missing))
            )
        return

    if args.command == "benchmark-gallery-demo":
        artifact_paths = build_benchmark_gallery_paths(
            html_out=args.html_out,
            artifact_dir=getattr(args, "artifact_dir", None),
        )
        missing = [path.name for path in artifact_paths.values() if not path.exists()]
        if missing:
            parser.error(
                "benchmark-gallery-demo requires the bundled benchmark markdown/svg artifacts to exist first; missing: "
                + ", ".join(sorted(missing))
            )
        return

    if args.command == "showcase-demo":
        artifact_paths = build_showcase_paths(
            html_out=args.html_out,
            artifact_dir=getattr(args, "artifact_dir", None),
        )
        missing = [path.name for path in artifact_paths.values() if not path.exists()]
        if missing:
            parser.error(
                "showcase-demo requires the bundled galleries and proof/report artifacts to exist first; missing: "
                + ", ".join(sorted(missing))
            )
        return

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

    if args.command == "assign":
        graph_path = args.graph
        left, right, edges = load_weighted_assignment_graph(graph_path)
        assignment_result = solve_weighted_assignment(left, right, edges)
        payload = {"command": args.command, "graph": str(graph_path), **assignment_result.to_dict()}
        if getattr(args, "explain", False):
            payload["explanation"] = build_assignment_explanation(assignment_result)
        if getattr(args, "dot_out", None):
            write_dot_output(args.dot_out, render_assignment_dot(assignment_result, graph_name=graph_path.stem))
            payload["dot_output"] = str(args.dot_out)
        if getattr(args, "markdown_out", None):
            write_markdown_output(args.markdown_out, render_assignment_markdown(assignment_result, graph_name=graph_path.stem))
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(args.svg_out, render_assignment_svg(assignment_result, graph_name=graph_path.stem))
            payload["svg_output"] = str(args.svg_out)
        if getattr(args, "html_out", None):
            companion_links = {
                key: _relative_output_path(Path(value), args.html_out.parent)
                for key, value in {
                    "dot": payload.get("dot_output"),
                    "markdown": payload.get("markdown_output"),
                    "svg": payload.get("svg_output"),
                }.items()
                if value is not None
            }
            write_html_output(
                args.html_out,
                render_assignment_artifact_html(
                    assignment_result,
                    graph_name=graph_path.stem,
                    companion_links=companion_links,
                ),
            )
            payload["html_output"] = str(args.html_out)
        return payload

    if args.command == "assign-demo":
        graph_path = Path(__file__).with_name("sample_assignment_graph.json")
        left, right, edges = load_weighted_assignment_graph(graph_path)
        assignment_result = solve_weighted_assignment(left, right, edges)
        payload = {"command": args.command, "graph": str(graph_path), **assignment_result.to_dict()}
        if getattr(args, "explain", False):
            payload["explanation"] = build_assignment_explanation(assignment_result)
        if getattr(args, "dot_out", None):
            write_dot_output(args.dot_out, render_assignment_dot(assignment_result, graph_name=graph_path.stem))
            payload["dot_output"] = str(args.dot_out)
        if getattr(args, "markdown_out", None):
            write_markdown_output(args.markdown_out, render_assignment_markdown(assignment_result, graph_name=graph_path.stem))
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(args.svg_out, render_assignment_svg(assignment_result, graph_name=graph_path.stem))
            payload["svg_output"] = str(args.svg_out)
        if getattr(args, "html_out", None):
            companion_links = {
                key: _relative_output_path(Path(value), args.html_out.parent)
                for key, value in {
                    "dot": payload.get("dot_output"),
                    "markdown": payload.get("markdown_output"),
                    "svg": payload.get("svg_output"),
                }.items()
                if value is not None
            }
            write_html_output(
                args.html_out,
                render_assignment_artifact_html(
                    assignment_result,
                    graph_name=graph_path.stem,
                    companion_links=companion_links,
                ),
            )
            payload["html_output"] = str(args.html_out)
        return payload

    if args.command == "cost-solve":
        graph_path = args.graph
        nodes, edges, source, sink, target_flow = load_costed_flow_graph(graph_path)
        flow_result = solve_min_cost_max_flow(nodes, edges, source, sink, target_flow=target_flow)
        payload = {
            "command": args.command,
            "graph": str(graph_path),
            "target_flow": target_flow,
            "target_reached": target_flow is None or flow_result.total_flow >= target_flow,
            **flow_result.to_dict(),
        }
        if getattr(args, "explain", False):
            payload["explanation"] = build_min_cost_flow_explanation(flow_result, target_flow=target_flow)
        if getattr(args, "dot_out", None):
            write_dot_output(
                args.dot_out,
                render_min_cost_flow_dot(flow_result, graph_name=graph_path.stem, target_flow=target_flow),
            )
            payload["dot_output"] = str(args.dot_out)
        if getattr(args, "markdown_out", None):
            write_markdown_output(
                args.markdown_out,
                render_min_cost_flow_markdown(flow_result, graph_name=graph_path.stem, target_flow=target_flow),
            )
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(
                args.svg_out,
                render_min_cost_flow_svg(flow_result, graph_name=graph_path.stem, target_flow=target_flow),
            )
            payload["svg_output"] = str(args.svg_out)
        if getattr(args, "html_out", None):
            companion_links = {
                key: _relative_output_path(Path(value), args.html_out.parent)
                for key, value in {
                    "dot": payload.get("dot_output"),
                    "markdown": payload.get("markdown_output"),
                    "svg": payload.get("svg_output"),
                }.items()
                if value is not None
            }
            write_html_output(
                args.html_out,
                render_min_cost_flow_artifact_html(
                    flow_result,
                    graph_name=graph_path.stem,
                    target_flow=target_flow,
                    companion_links=companion_links,
                ),
            )
            payload["html_output"] = str(args.html_out)
        return payload

    if args.command == "gallery-demo":
        artifact_paths = build_artifact_gallery_paths(
            html_out=args.html_out,
            artifact_dir=getattr(args, "artifact_dir", None),
        )
        relative_paths = {
            key: _relative_output_path(path, args.html_out.parent)
            for key, path in artifact_paths.items()
        }
        write_html_output(
            args.html_out,
            render_artifact_gallery_html(
                assignment_page=relative_paths["assignment_page"],
                assignment_proof_svg=relative_paths["assignment_proof_svg"],
                assignment_markdown=relative_paths["assignment_markdown"],
                assignment_dot=relative_paths["assignment_dot"],
                cost_page=relative_paths["cost_page"],
                cost_proof_svg=relative_paths["cost_proof_svg"],
                cost_markdown=relative_paths["cost_markdown"],
                cost_dot=relative_paths["cost_dot"],
            ),
        )
        return {
            "command": args.command,
            "artifact_dir": str((getattr(args, "artifact_dir", None) or args.html_out.parent)),
            "html_output": str(args.html_out),
            **{key: str(path) for key, path in artifact_paths.items()},
        }

    if args.command == "benchmark-gallery-demo":
        artifact_paths = build_benchmark_gallery_paths(
            html_out=args.html_out,
            artifact_dir=getattr(args, "artifact_dir", None),
        )
        relative_paths = {
            key: _relative_output_path(path, args.html_out.parent)
            for key, path in artifact_paths.items()
        }
        optimization_gallery_path = (getattr(args, "artifact_dir", None) or args.html_out.parent) / "artifact-gallery.html"
        optimization_gallery_relative = (
            _relative_output_path(optimization_gallery_path, args.html_out.parent)
            if optimization_gallery_path.exists()
            else None
        )
        write_html_output(
            args.html_out,
            render_benchmark_gallery_html(
                dag_svg=relative_paths["dag_svg"],
                dag_markdown=relative_paths["dag_markdown"],
                dense_svg=relative_paths["dense_svg"],
                dense_markdown=relative_paths["dense_markdown"],
                layered_svg=relative_paths["layered_svg"],
                layered_markdown=relative_paths["layered_markdown"],
                artifact_gallery=optimization_gallery_relative,
            ),
        )
        return {
            "command": args.command,
            "artifact_dir": str((getattr(args, "artifact_dir", None) or args.html_out.parent)),
            "html_output": str(args.html_out),
            **{key: str(path) for key, path in artifact_paths.items()},
        }

    if args.command == "showcase-demo":
        artifact_paths = build_showcase_paths(
            html_out=args.html_out,
            artifact_dir=getattr(args, "artifact_dir", None),
        )
        relative_paths = {
            key: _relative_output_path(path, args.html_out.parent)
            for key, path in artifact_paths.items()
        }
        write_html_output(
            args.html_out,
            render_showcase_html(
                artifact_gallery=relative_paths["artifact_gallery"],
                benchmark_gallery=relative_paths["benchmark_gallery"],
                flow_svg=relative_paths["flow_svg"],
                flow_markdown=relative_paths["flow_markdown"],
                matching_svg=relative_paths["matching_svg"],
                matching_markdown=relative_paths["matching_markdown"],
                assignment_page=relative_paths["assignment_page"],
                assignment_svg=relative_paths["assignment_svg"],
                assignment_markdown=relative_paths["assignment_markdown"],
                assignment_dot=relative_paths["assignment_dot"],
                cost_page=relative_paths["cost_page"],
                cost_svg=relative_paths["cost_svg"],
                cost_markdown=relative_paths["cost_markdown"],
                cost_dot=relative_paths["cost_dot"],
                dag_svg=relative_paths["dag_svg"],
                dag_markdown=relative_paths["dag_markdown"],
                dense_svg=relative_paths["dense_svg"],
                dense_markdown=relative_paths["dense_markdown"],
                layered_svg=relative_paths["layered_svg"],
                layered_markdown=relative_paths["layered_markdown"],
            ),
        )
        return {
            "command": args.command,
            "artifact_dir": str((getattr(args, "artifact_dir", None) or args.html_out.parent)),
            "html_output": str(args.html_out),
            **{key: str(path) for key, path in artifact_paths.items()},
        }

    if args.command == "cost-demo":
        graph_path = Path(__file__).with_name("sample_cost_flow_graph.json")
        nodes, edges, source, sink, target_flow = load_costed_flow_graph(graph_path)
        flow_result = solve_min_cost_max_flow(nodes, edges, source, sink, target_flow=target_flow)
        payload = {
            "command": args.command,
            "graph": str(graph_path),
            "target_flow": target_flow,
            "target_reached": target_flow is None or flow_result.total_flow >= target_flow,
            **flow_result.to_dict(),
        }
        if getattr(args, "explain", False):
            payload["explanation"] = build_min_cost_flow_explanation(flow_result, target_flow=target_flow)
        if getattr(args, "dot_out", None):
            write_dot_output(
                args.dot_out,
                render_min_cost_flow_dot(flow_result, graph_name=graph_path.stem, target_flow=target_flow),
            )
            payload["dot_output"] = str(args.dot_out)
        if getattr(args, "markdown_out", None):
            write_markdown_output(
                args.markdown_out,
                render_min_cost_flow_markdown(flow_result, graph_name=graph_path.stem, target_flow=target_flow),
            )
            payload["markdown_output"] = str(args.markdown_out)
        if getattr(args, "svg_out", None):
            write_svg_output(
                args.svg_out,
                render_min_cost_flow_svg(flow_result, graph_name=graph_path.stem, target_flow=target_flow),
            )
            payload["svg_output"] = str(args.svg_out)
        if getattr(args, "html_out", None):
            companion_links = {
                key: _relative_output_path(Path(value), args.html_out.parent)
                for key, value in {
                    "dot": payload.get("dot_output"),
                    "markdown": payload.get("markdown_output"),
                    "svg": payload.get("svg_output"),
                }.items()
                if value is not None
            }
            write_html_output(
                args.html_out,
                render_min_cost_flow_artifact_html(
                    flow_result,
                    graph_name=graph_path.stem,
                    target_flow=target_flow,
                    companion_links=companion_links,
                ),
            )
            payload["html_output"] = str(args.html_out)
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
