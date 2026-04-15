from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

INFINITY = 16


@dataclass(frozen=True)
class Route:
    destination: str
    cost: int
    next_hop: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "destination": self.destination,
            "cost": self.cost,
            "next_hop": self.next_hop,
        }


@dataclass(frozen=True)
class RoundState:
    round_index: int
    changed: bool
    tables: dict[str, dict[str, Route]]

    def to_dict(self) -> dict[str, object]:
        return {
            "round": self.round_index,
            "changed": self.changed,
            "tables": serialize_tables(self.tables),
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
                raise ValueError(f"router {neighbor!r} referenced by {router!r} is missing")
            reverse = normalized[neighbor].get(router)
            if reverse != cost:
                raise ValueError(
                    f"topology must be symmetric for {router!r}<->{neighbor!r}; got {cost} and {reverse}"
                )
    return normalized


def initialize_tables(topology: Mapping[str, Mapping[str, int]]) -> dict[str, dict[str, Route]]:
    tables: dict[str, dict[str, Route]] = {}
    for router, neighbors in topology.items():
        table: dict[str, Route] = {
            router: Route(destination=router, cost=0, next_hop=router)
        }
        for neighbor, cost in sorted(neighbors.items()):
            table[neighbor] = Route(destination=neighbor, cost=cost, next_hop=neighbor)
        tables[router] = table
    return tables


def advertised_cost(route: Route, *, sender: str, recipient: str, mode: str, infinity: int) -> int | None:
    if route.destination == recipient:
        return route.cost
    if mode == "split-horizon" and route.next_hop == recipient:
        return None
    if mode == "poison-reverse" and route.next_hop == recipient:
        return infinity
    return route.cost


def route_sort_key(route: Route) -> tuple[int, int, str]:
    next_hop = route.next_hop or ""
    return (route.cost, 0 if route.next_hop is not None else 1, next_hop)


def update_once(
    topology: Mapping[str, Mapping[str, int]],
    tables: Mapping[str, Mapping[str, Route]],
    *,
    mode: str,
    infinity: int,
) -> tuple[dict[str, dict[str, Route]], bool]:
    all_destinations = sorted(topology)
    next_tables: dict[str, dict[str, Route]] = {}
    changed = False

    for router in sorted(topology):
        current = tables[router]
        new_table: dict[str, Route] = {
            router: Route(destination=router, cost=0, next_hop=router)
        }
        for destination in all_destinations:
            if destination == router:
                continue
            candidates: list[Route] = []
            direct_cost = topology[router].get(destination)
            if direct_cost is not None:
                candidates.append(Route(destination=destination, cost=direct_cost, next_hop=destination))
            for neighbor, link_cost in sorted(topology[router].items()):
                neighbor_route = tables[neighbor].get(destination)
                if neighbor_route is None:
                    continue
                advertised = advertised_cost(
                    neighbor_route,
                    sender=neighbor,
                    recipient=router,
                    mode=mode,
                    infinity=infinity,
                )
                if advertised is None:
                    continue
                combined = min(infinity, link_cost + advertised)
                candidates.append(Route(destination=destination, cost=combined, next_hop=neighbor))
            best = min(candidates, key=route_sort_key) if candidates else Route(destination, infinity, None)
            if best.cost >= infinity:
                best = Route(destination, infinity, None)
            new_table[destination] = best
        next_tables[router] = new_table
        if serialize_table(current) != serialize_table(new_table):
            changed = True

    return next_tables, changed


def run_simulation(
    topology: Mapping[str, Mapping[str, int]],
    *,
    mode: str = "classic",
    infinity: int = INFINITY,
    max_rounds: int = 50,
) -> dict[str, object]:
    if mode not in {"classic", "split-horizon", "poison-reverse"}:
        raise ValueError("mode must be classic, split-horizon, or poison-reverse")
    normalized = normalize_topology(topology)
    tables = initialize_tables(normalized)
    history: list[RoundState] = [RoundState(round_index=0, changed=False, tables=tables)]

    converged = False
    for round_index in range(1, max_rounds + 1):
        tables, changed = update_once(normalized, tables, mode=mode, infinity=infinity)
        history.append(RoundState(round_index=round_index, changed=changed, tables=tables))
        if not changed:
            converged = True
            break

    return {
        "mode": mode,
        "infinity": infinity,
        "topology": {router: dict(sorted(neighbors.items())) for router, neighbors in sorted(normalized.items())},
        "converged": converged,
        "rounds": len(history) - 1,
        "tables": serialize_tables(tables),
        "history": [entry.to_dict() for entry in history],
    }


def remove_link(topology: Mapping[str, Mapping[str, int]], left: str, right: str) -> dict[str, dict[str, int]]:
    normalized = normalize_topology(topology)
    if right not in normalized.get(left, {}) or left not in normalized.get(right, {}):
        raise ValueError(f"link {left!r}<->{right!r} does not exist")
    normalized[left].pop(right)
    normalized[right].pop(left)
    return normalized


def serialize_table(table: Mapping[str, Route]) -> dict[str, dict[str, object]]:
    return {destination: route.to_dict() for destination, route in sorted(table.items())}


def serialize_tables(tables: Mapping[str, Mapping[str, Route]]) -> dict[str, dict[str, dict[str, object]]]:
    return {router: serialize_table(table) for router, table in sorted(tables.items())}


def parse_topology(raw: str) -> dict[str, dict[str, int]]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON topology: {exc}") from exc
    if not isinstance(payload, MutableMapping):
        raise ValueError("topology must be a JSON object mapping routers to neighbor-cost maps")
    normalized: dict[str, dict[str, int]] = {}
    for router, neighbors in payload.items():
        if not isinstance(router, str):
            raise ValueError("router names must be strings")
        if not isinstance(neighbors, MutableMapping):
            raise ValueError(f"neighbors for {router!r} must be an object")
        normalized[router] = {}
        for neighbor, cost in neighbors.items():
            if not isinstance(neighbor, str) or not isinstance(cost, int):
                raise ValueError("neighbor names must be strings and link costs must be integers")
            normalized[router][neighbor] = cost
    return normalize_topology(normalized)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate distance-vector routing convergence.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate_parser = subparsers.add_parser("simulate", help="run until convergence on a topology")
    simulate_parser.add_argument("--topology", required=True, help="JSON adjacency map with symmetric integer link costs")
    simulate_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    simulate_parser.add_argument("--infinity", type=int, default=INFINITY)
    simulate_parser.add_argument("--max-rounds", type=int, default=50)

    failure_parser = subparsers.add_parser("simulate-failure", help="remove one link and observe reconvergence")
    failure_parser.add_argument("--topology", required=True)
    failure_parser.add_argument("--remove-link", nargs=2, metavar=("LEFT", "RIGHT"), required=True)
    failure_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    failure_parser.add_argument("--infinity", type=int, default=INFINITY)
    failure_parser.add_argument("--max-rounds", type=int, default=50)

    return parser


def cli(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.infinity <= 0:
        parser.error("--infinity must be positive")
    if args.max_rounds <= 0:
        parser.error("--max-rounds must be positive")

    topology = parse_topology(args.topology)
    if args.command == "simulate":
        payload = run_simulation(topology, mode=args.mode, infinity=args.infinity, max_rounds=args.max_rounds)
    else:
        left, right = args.remove_link
        updated_topology = remove_link(topology, left, right)
        before = run_simulation(topology, mode=args.mode, infinity=args.infinity, max_rounds=args.max_rounds)
        after = run_simulation(updated_topology, mode=args.mode, infinity=args.infinity, max_rounds=args.max_rounds)
        payload = {
            "event": {"type": "remove-link", "left": left, "right": right},
            "before": before,
            "after": after,
        }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
