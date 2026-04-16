from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from heapq import heappop, heappush
from pathlib import Path
from typing import Any, Iterable, Mapping

MAX_AGE = 3600
DISTANCE_VECTOR_MODULE_PATH = (
    Path(__file__).resolve().parent.parent / "distance-vector-routing-lab" / "distance_vector_routing.py"
)


@dataclass(frozen=True)
class LinkStateAdvertisement:
    router: str
    neighbors: dict[str, int]
    sequence: int
    age: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "router": self.router,
            "neighbors": dict(sorted(self.neighbors.items())),
            "sequence": self.sequence,
            "age": self.age,
        }


@dataclass(frozen=True)
class Route:
    destination: str
    cost: int
    next_hop: str | None
    path: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "destination": self.destination,
            "cost": self.cost,
            "next_hop": self.next_hop,
            "path": list(self.path),
        }


@dataclass(frozen=True)
class FloodStep:
    round_index: int
    sender: str
    recipient: str
    router: str
    sequence: int
    accepted: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "round": self.round_index,
            "sender": self.sender,
            "recipient": self.recipient,
            "router": self.router,
            "sequence": self.sequence,
            "accepted": self.accepted,
        }


@dataclass(frozen=True)
class SimulationResult:
    lsdb: dict[str, LinkStateAdvertisement]
    routes: dict[str, dict[str, Route]]
    flood_log: tuple[FloodStep, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "lsdb": {router: lsa.to_dict() for router, lsa in sorted(self.lsdb.items())},
            "routes": {
                router: {destination: route.to_dict() for destination, route in sorted(table.items())}
                for router, table in sorted(self.routes.items())
            },
            "flood_log": [step.to_dict() for step in self.flood_log],
        }


def normalize_topology(topology: Mapping[str, Mapping[str, int]]) -> dict[str, dict[str, int]]:
    normalized: dict[str, dict[str, int]] = {}
    for router, neighbors in topology.items():
        normalized[router] = {}
        for neighbor, cost in neighbors.items():
            if cost < 0:
                raise ValueError("link costs must be non-negative")
            normalized[router][neighbor] = int(cost)

    for router, neighbors in normalized.items():
        for neighbor, cost in neighbors.items():
            if neighbor not in normalized:
                raise ValueError(f"missing router {neighbor!r} referenced by {router!r}")
            reverse_cost = normalized[neighbor].get(router)
            if reverse_cost != cost:
                raise ValueError(
                    f"topology must be symmetric for {router!r}<->{neighbor!r}; got {cost} and {reverse_cost}"
                )
    return {router: dict(sorted(neighbors.items())) for router, neighbors in sorted(normalized.items())}


def originate_lsas(
    topology: Mapping[str, Mapping[str, int]],
    previous: Mapping[str, LinkStateAdvertisement] | None = None,
    *,
    age: int = 0,
) -> dict[str, LinkStateAdvertisement]:
    lsas: dict[str, LinkStateAdvertisement] = {}
    previous = previous or {}
    for router, neighbors in topology.items():
        prior_sequence = previous.get(router).sequence if router in previous else 0
        lsas[router] = LinkStateAdvertisement(
            router=router,
            neighbors=dict(neighbors),
            sequence=prior_sequence + 1,
            age=age,
        )
    return lsas


def install_lsa(
    lsdb: dict[str, LinkStateAdvertisement],
    lsa: LinkStateAdvertisement,
) -> bool:
    current = lsdb.get(lsa.router)
    if lsa.age >= MAX_AGE:
        lsdb.pop(lsa.router, None)
        return current is not None
    if current is None or (lsa.sequence, -lsa.age) > (current.sequence, -current.age):
        lsdb[lsa.router] = lsa
        return True
    return False


def flood_lsas(
    topology: Mapping[str, Mapping[str, int]],
    origin_lsas: Iterable[LinkStateAdvertisement] | Mapping[str, LinkStateAdvertisement],
    *,
    initial_lsdb: Mapping[str, LinkStateAdvertisement] | None = None,
) -> tuple[dict[str, LinkStateAdvertisement], tuple[FloodStep, ...]]:
    lsdb = dict(initial_lsdb or {})
    pending: list[tuple[int, str, str, str, int, LinkStateAdvertisement]] = []
    log: list[FloodStep] = []

    iterable = origin_lsas.values() if isinstance(origin_lsas, Mapping) else origin_lsas
    for lsa in iterable:
        install_lsa(lsdb, lsa)
        for neighbor in topology.get(lsa.router, {}):
            heappush(pending, (1, lsa.router, neighbor, lsa.router, lsa.sequence, lsa))

    while pending:
        round_index, sender, recipient, _router, _sequence, lsa = heappop(pending)
        accepted = install_lsa(lsdb, lsa)
        log.append(
            FloodStep(
                round_index=round_index,
                sender=sender,
                recipient=recipient,
                router=lsa.router,
                sequence=lsa.sequence,
                accepted=accepted,
            )
        )
        if not accepted:
            continue
        for neighbor in topology.get(recipient, {}):
            if neighbor == sender:
                continue
            heappush(pending, (round_index + 1, recipient, neighbor, lsa.router, lsa.sequence, lsa))

    return lsdb, tuple(log)


def _path_metric(path: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    return len(path), path


def shortest_paths(topology: Mapping[str, Mapping[str, int]], source: str) -> dict[str, Route]:
    queue: list[tuple[int, tuple[str, ...], str, str | None]] = [(0, (source,), source, None)]
    best_cost: dict[str, int] = {}
    best_path: dict[str, tuple[str, ...]] = {}
    routes: dict[str, Route] = {}

    while queue:
        cost, path, node, first_hop = heappop(queue)
        if node in best_cost:
            if cost > best_cost[node]:
                continue
            if cost == best_cost[node] and _path_metric(path) >= _path_metric(best_path[node]):
                continue
        best_cost[node] = cost
        best_path[node] = path
        routes[node] = Route(destination=node, cost=cost, next_hop=first_hop or node, path=path)

        for neighbor, edge_cost in sorted(topology[node].items()):
            next_cost = cost + edge_cost
            next_path = path + (neighbor,)
            next_first_hop = first_hop or neighbor
            heappush(queue, (next_cost, next_path, neighbor, next_first_hop))

    for router in topology:
        routes.setdefault(router, Route(destination=router, cost=float("inf"), next_hop=None, path=()))
    routes[source] = Route(destination=source, cost=0, next_hop=source, path=(source,))
    return dict(sorted(routes.items()))


def compute_forwarding_tables(lsdb: Mapping[str, LinkStateAdvertisement]) -> dict[str, dict[str, Route]]:
    topology = normalize_topology({router: lsa.neighbors for router, lsa in lsdb.items()})
    return {router: shortest_paths(topology, router) for router in sorted(topology)}


def run_simulation(
    topology: Mapping[str, Mapping[str, int]],
    *,
    previous_lsdb: Mapping[str, LinkStateAdvertisement] | None = None,
) -> SimulationResult:
    normalized = normalize_topology(topology)
    origin_lsas = originate_lsas(normalized, previous_lsdb)
    lsdb, flood_log = flood_lsas(normalized, origin_lsas, initial_lsdb=previous_lsdb)
    routes = compute_forwarding_tables(lsdb)
    return SimulationResult(lsdb=lsdb, routes=routes, flood_log=flood_log)


def load_topology(path: str) -> dict[str, dict[str, int]]:
    return normalize_topology(json.loads(Path(path).read_text()))


def max_flood_round(result: SimulationResult) -> int:
    return max((step.round_index for step in result.flood_log), default=0)


def load_distance_vector_module() -> Any:
    spec = importlib.util.spec_from_file_location("distance_vector_routing_module", DISTANCE_VECTOR_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load distance-vector module from {DISTANCE_VECTOR_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def compare_with_distance_vector(
    topology: Mapping[str, Mapping[str, int]],
    *,
    distance_vector_mode: str = "classic",
    distance_vector_update_strategy: str = "periodic",
    remove_link: tuple[str, str] | None = None,
    max_rounds: int = 50,
) -> dict[str, object]:
    normalized = normalize_topology(topology)
    before_link_state = run_simulation(normalized)
    distance_vector = load_distance_vector_module()
    before_distance_vector = distance_vector.run_simulation(
        normalized,
        mode=distance_vector_mode,
        max_rounds=max_rounds,
        update_strategy=distance_vector_update_strategy,
    )

    comparison: dict[str, object] = {
        "distance_vector_mode": distance_vector_mode,
        "distance_vector_update_strategy": distance_vector_update_strategy,
        "topology": {router: dict(neighbors) for router, neighbors in sorted(normalized.items())},
        "before": {
            "link_state": {
                "flood_events": len(before_link_state.flood_log),
                "flood_rounds": max_flood_round(before_link_state),
                "lsa_count": len(before_link_state.lsdb),
            },
            "distance_vector": {
                "rounds": before_distance_vector["rounds"],
                "converged": before_distance_vector["converged"],
                "mode": before_distance_vector["mode"],
                "update_strategy": before_distance_vector["update_strategy"],
            },
        },
        "observations": [
            (
                "link-state converges by flooding whole-topology LSAs and then running local SPF, "
                "while distance-vector converges through neighbor table exchange over multiple rounds"
            )
        ],
    }

    if remove_link is not None:
        left, right = remove_link
        updated_topology = {
            router: dict(neighbors) for router, neighbors in normalized.items()
        }
        if right not in updated_topology.get(left, {}) or left not in updated_topology.get(right, {}):
            raise ValueError(f"link {left!r}<->{right!r} does not exist")
        updated_topology[left].pop(right)
        updated_topology[right].pop(left)
        after_link_state = run_simulation(updated_topology, previous_lsdb=before_link_state.lsdb)
        after_distance_vector = distance_vector.run_failure_simulation(
            normalized,
            left,
            right,
            mode=distance_vector_mode,
            max_rounds=max_rounds,
            update_strategy=distance_vector_update_strategy,
        )["after"]
        comparison["event"] = {"type": "remove-link", "left": left, "right": right}
        comparison["after"] = {
            "link_state": {
                "flood_events": len(after_link_state.flood_log),
                "flood_rounds": max_flood_round(after_link_state),
                "changed_routers": sorted(
                    router
                    for router, lsa in after_link_state.lsdb.items()
                    if before_link_state.lsdb.get(router) is None
                    or lsa.neighbors != before_link_state.lsdb[router].neighbors
                ),
            },
            "distance_vector": {
                "rounds": after_distance_vector["rounds"],
                "converged": after_distance_vector["converged"],
                "mode": after_distance_vector["mode"],
                "update_strategy": after_distance_vector["update_strategy"],
            },
        }
        comparison["observations"].append(
            "after a link failure, link-state re-floods fresh LSAs and recomputes SPF, while distance-vector may take extra rounds to propagate changed next-hop costs"
        )
        if distance_vector_mode == "classic":
            comparison["observations"].append(
                "classic distance-vector can exhibit count-to-infinity-style behavior on some failures, which link-state avoids because every router recomputes from a refreshed global graph"
            )

    return comparison


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate link-state routing with LSA flooding and SPF recomputation.")
    parser.add_argument("topology", help="Path to a JSON topology map")
    parser.add_argument(
        "--format",
        choices=("json", "pretty", "mermaid"),
        default="pretty",
        help="Output format",
    )
    parser.add_argument(
        "--source",
        help="Optional router name to print only one forwarding table or SPF tree root",
    )
    parser.add_argument(
        "--compare-distance-vector",
        action="store_true",
        help="Compare link-state convergence against the distance-vector lab on the same topology",
    )
    parser.add_argument(
        "--distance-vector-mode",
        choices=("classic", "split-horizon", "poison-reverse"),
        default="classic",
        help="Distance-vector mode to use when --compare-distance-vector is enabled",
    )
    parser.add_argument(
        "--distance-vector-update-strategy",
        choices=("periodic", "triggered"),
        default="periodic",
        help="Distance-vector update strategy to use when --compare-distance-vector is enabled",
    )
    parser.add_argument(
        "--remove-link",
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        help="Optional link failure to compare after initial convergence",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=50,
        help="Maximum rounds for the distance-vector comparison run",
    )
    return parser.parse_args()


def render_pretty(result: SimulationResult, source: str | None = None) -> str:
    lines: list[str] = []
    lines.append("LSDB:")
    for router, lsa in sorted(result.lsdb.items()):
        lines.append(f"- {router}: seq={lsa.sequence} neighbors={json.dumps(lsa.neighbors, sort_keys=True)}")

    lines.append("")
    lines.append("Forwarding tables:")
    routers = [source] if source else sorted(result.routes)
    for router in routers:
        if router not in result.routes:
            raise ValueError(f"unknown router {router!r}")
        lines.append(f"[{router}]")
        for destination, route in result.routes[router].items():
            path_text = " -> ".join(route.path) if route.path else "unreachable"
            lines.append(
                f"  {destination}: cost={route.cost} next_hop={route.next_hop} path={path_text}"
            )
    lines.append("")
    lines.append(f"Flood events: {len(result.flood_log)}")
    return "\n".join(lines)


def render_mermaid(result: SimulationResult, source: str | None = None) -> str:
    topology = normalize_topology({router: lsa.neighbors for router, lsa in result.lsdb.items()})
    routers = sorted(topology)
    if source and source not in topology:
        raise ValueError(f"unknown router {source!r}")

    lines: list[str] = ["flowchart LR"]
    for router in routers:
        lines.append(f"    {router}[\"{router}\"]")

    emitted_edges: set[tuple[str, str]] = set()
    for router in routers:
        for neighbor, cost in sorted(topology[router].items()):
            edge = tuple(sorted((router, neighbor)))
            if edge in emitted_edges:
                continue
            emitted_edges.add(edge)
            left, right = edge
            lines.append(f"    {left} <-->|\"{cost}\"| {right}")

    if source:
        lines.append("")
        lines.append(f"    %% SPF tree rooted at {source}")
        lines.append(f"    classDef root fill:#fde68a,stroke:#92400e,stroke-width:2px")
        lines.append(f"    class {source} root")

        tree_edges: set[tuple[str, str]] = set()
        for destination, route in sorted(result.routes[source].items()):
            if destination == source or len(route.path) < 2:
                continue
            for left, right in zip(route.path, route.path[1:]):
                tree_edges.add((left, right))

        edge_index = 0
        for left, right in sorted(tree_edges):
            edge_index += 1
            cost = topology[left][right]
            lines.append(f"    {left} -->|\"SPF {cost}\"| {right}")
            lines.append(f"    linkStyle {len(emitted_edges) + edge_index - 1} stroke:#dc2626,stroke-width:3px")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.max_rounds <= 0:
        raise ValueError("max_rounds must be positive")
    topology = load_topology(args.topology)
    if args.compare_distance_vector:
        payload = compare_with_distance_vector(
            topology,
            distance_vector_mode=args.distance_vector_mode,
            distance_vector_update_strategy=args.distance_vector_update_strategy,
            remove_link=tuple(args.remove_link) if args.remove_link else None,
            max_rounds=args.max_rounds,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    result = run_simulation(topology)
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return
    if args.format == "mermaid":
        print(render_mermaid(result, source=args.source))
        return
    print(render_pretty(result, source=args.source))


if __name__ == "__main__":
    main()
