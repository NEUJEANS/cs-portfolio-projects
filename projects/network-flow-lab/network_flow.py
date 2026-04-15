from __future__ import annotations

import argparse
import json
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "sink": self.sink,
            "max_flow": self.max_flow,
            "augmenting_paths": self.augmenting_paths,
            "edge_flows": self.edge_flows,
            "min_cut": self.min_cut,
        }


@dataclass(frozen=True)
class MatchingResult:
    left_partition: list[str]
    right_partition: list[str]
    matches: list[dict[str, str]]
    unmatched_left: list[str]
    unmatched_right: list[str]
    flow: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "left_partition": self.left_partition,
            "right_partition": self.right_partition,
            "matches": self.matches,
            "match_count": len(self.matches),
            "unmatched_left": self.unmatched_left,
            "unmatched_right": self.unmatched_right,
            "flow": self.flow,
        }


MATCH_SOURCE = "__source__"
MATCH_SINK = "__sink__"


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


def solve_bipartite_matching(
    left: list[str], right: list[str], edges: list[tuple[str, str]]
) -> MatchingResult:
    nodes, flow_edges, source, sink = build_bipartite_matching_flow(left, right, edges)
    flow_result = solve_max_flow(nodes, flow_edges, source, sink)
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

    return MatchingResult(
        left_partition=sorted(left),
        right_partition=sorted(right),
        matches=matches,
        unmatched_left=sorted(node for node in left if node not in matched_left),
        unmatched_right=sorted(node for node in right if node not in matched_right),
        flow=flow_result.to_dict(),
    )


def solve_max_flow(nodes: list[str], edges: list[Edge], source: str, sink: str) -> FlowResult:
    capacities: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    original_edges: list[tuple[str, str]] = []
    for edge in edges:
        capacities[edge.source][edge.target] += edge.capacity
        capacities[edge.target]
        original_edges.append((edge.source, edge.target))

    residual: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    neighbors: dict[str, set[str]] = {node: set() for node in nodes}
    for u in nodes:
        for v, capacity in capacities[u].items():
            residual[u][v] = capacity
            neighbors[u].add(v)
            neighbors[v].add(u)
            residual[v][u] += 0

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
        max_flow=max_flow,
        augmenting_paths=augmenting_paths,
        edge_flows=edge_flows,
        min_cut={"source_side": cut_source_side, "sink_side": cut_sink_side},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Solve max-flow graphs and bipartite matchings.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser("solve", help="solve a graph JSON file")
    solve_parser.add_argument("graph", type=Path, help="path to graph JSON")
    solve_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")

    demo_parser = subparsers.add_parser("demo", help="run the bundled sample graph")
    demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")

    match_parser = subparsers.add_parser("match", help="solve a bipartite matching JSON file")
    match_parser.add_argument("graph", type=Path, help="path to bipartite graph JSON")
    match_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")

    match_demo_parser = subparsers.add_parser("match-demo", help="run the bundled matching sample")
    match_demo_parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    return parser


def run_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "solve":
        graph_path = args.graph
        nodes, edges, source, sink = load_graph(graph_path)
        result = solve_max_flow(nodes, edges, source, sink).to_dict()
        return {"command": args.command, "graph": str(graph_path), **result}

    if args.command == "demo":
        graph_path = Path(__file__).with_name("sample_graph.json")
        nodes, edges, source, sink = load_graph(graph_path)
        result = solve_max_flow(nodes, edges, source, sink).to_dict()
        return {"command": args.command, "graph": str(graph_path), **result}

    if args.command == "match":
        graph_path = args.graph
        left, right, edges = load_bipartite_graph(graph_path)
        result = solve_bipartite_matching(left, right, edges).to_dict()
        return {"command": args.command, "graph": str(graph_path), **result}

    graph_path = Path(__file__).with_name("sample_matching_graph.json")
    left, right, edges = load_bipartite_graph(graph_path)
    result = solve_bipartite_matching(left, right, edges).to_dict()
    return {"command": args.command, "graph": str(graph_path), **result}


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
