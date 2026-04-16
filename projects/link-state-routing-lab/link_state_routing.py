from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from heapq import heappop, heappush
from pathlib import Path
from typing import Iterable, Mapping

MAX_AGE = 3600


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



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate link-state routing with LSA flooding and SPF recomputation.")
    parser.add_argument("topology", help="Path to a JSON topology map")
    parser.add_argument(
        "--format",
        choices=("json", "pretty"),
        default="pretty",
        help="Output format",
    )
    parser.add_argument(
        "--source",
        help="Optional router name to print only one forwarding table",
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



def main() -> None:
    args = parse_args()
    topology = load_topology(args.topology)
    result = run_simulation(topology)
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        return
    print(render_pretty(result, source=args.source))


if __name__ == "__main__":
    main()
