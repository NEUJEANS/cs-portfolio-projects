from __future__ import annotations

import argparse
import csv
import json
import io
from collections import deque
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence

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
    active_routers: tuple[str, ...] = ()
    route_ages: dict[str, dict[str, int]] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "round": self.round_index,
            "changed": self.changed,
            "active_routers": list(self.active_routers),
            "tables": serialize_tables(self.tables),
        }
        if self.route_ages is not None:
            payload["route_ages"] = {
                router: dict(sorted(destinations.items()))
                for router, destinations in sorted(self.route_ages.items())
            }
        return payload


@dataclass(frozen=True)
class FailureScenario:
    name: str
    description: str
    topology: dict[str, dict[str, int]]
    remove_link: tuple[str, str]
    router: str
    destination: str

    def to_dict(self) -> dict[str, object]:
        left, right = self.remove_link
        return {
            "name": self.name,
            "description": self.description,
            "topology": {router: dict(sorted(neighbors.items())) for router, neighbors in sorted(self.topology.items())},
            "event": {"type": "remove-link", "left": left, "right": right},
            "tracked_route": {"router": self.router, "destination": self.destination},
        }


FAILURE_SCENARIOS: dict[str, FailureScenario] = {
    "count-to-infinity-line": FailureScenario(
        name="count-to-infinity-line",
        description="The classic A-B-C line where removing B-C isolates C and exposes the clean two-router count-to-infinity story.",
        topology={
            "A": {"B": 1},
            "B": {"A": 1, "C": 1},
            "C": {"B": 1},
        },
        remove_link=("B", "C"),
        router="A",
        destination="C",
    ),
    "square-detour": FailureScenario(
        name="square-detour",
        description="A four-router square where the watched route survives via a longer alternate path after the primary edge disappears.",
        topology={
            "A": {"B": 1, "D": 4},
            "B": {"A": 1, "C": 2},
            "C": {"B": 2, "D": 1},
            "D": {"A": 4, "C": 1},
        },
        remove_link=("B", "C"),
        router="A",
        destination="C",
    ),
    "ring-isolation": FailureScenario(
        name="ring-isolation",
        description="A four-router ring feeding a destination leaf, useful for showing that larger loops can still bounce even with split horizon or poison reverse.",
        topology={
            "A": {"B": 1, "D": 1},
            "B": {"A": 1, "C": 1},
            "C": {"B": 1, "D": 1, "E": 1},
            "D": {"A": 1, "C": 1},
            "E": {"C": 1},
        },
        remove_link=("C", "E"),
        router="A",
        destination="E",
    ),
    "five-node-bypass": FailureScenario(
        name="five-node-bypass",
        description="A five-router topology where the best path breaks, briefly inflates, then settles onto a more expensive but still reachable bypass.",
        topology={
            "A": {"B": 1, "D": 2},
            "B": {"A": 1, "C": 1},
            "C": {"B": 1, "E": 1},
            "D": {"A": 2, "E": 2},
            "E": {"C": 1, "D": 2},
        },
        remove_link=("B", "C"),
        router="A",
        destination="C",
    ),
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
        table: dict[str, Route] = {router: Route(destination=router, cost=0, next_hop=router)}
        for neighbor, cost in sorted(neighbors.items()):
            table[neighbor] = Route(destination=neighbor, cost=cost, next_hop=neighbor)
        tables[router] = table
    return tables


def advertised_cost(
    route: Route,
    *,
    recipient: str,
    mode: str,
    infinity: int,
    advertiser_silent: bool,
) -> int | None:
    if advertiser_silent:
        return None
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


def clone_tables(tables: Mapping[str, Mapping[str, Route]]) -> dict[str, dict[str, Route]]:
    return {router: dict(table) for router, table in tables.items()}


def initialize_route_ages(
    topology: Mapping[str, Mapping[str, int]],
    tables: Mapping[str, Mapping[str, Route]],
) -> dict[str, dict[str, int]]:
    route_ages: dict[str, dict[str, int]] = {}
    for router, table in tables.items():
        route_ages[router] = {}
        for destination, route in table.items():
            if destination == router:
                continue
            if route.next_hop is None:
                route_ages[router][destination] = 0
            elif route.next_hop == destination and destination in topology[router]:
                route_ages[router][destination] = 0
            else:
                route_ages[router][destination] = 0
    return route_ages


def compute_best_route(
    router: str,
    destination: str,
    topology: Mapping[str, Mapping[str, int]],
    tables: Mapping[str, Mapping[str, Route]],
    *,
    mode: str,
    infinity: int,
    silent_routers: set[str],
) -> tuple[Route, bool]:
    candidates: list[tuple[Route, bool]] = []
    direct_cost = topology[router].get(destination)
    if direct_cost is not None:
        candidates.append((Route(destination=destination, cost=direct_cost, next_hop=destination), False))

    for neighbor, link_cost in sorted(topology[router].items()):
        neighbor_route = tables[neighbor].get(destination)
        if neighbor_route is None:
            continue
        advertised = advertised_cost(
            neighbor_route,
            recipient=router,
            mode=mode,
            infinity=infinity,
            advertiser_silent=neighbor in silent_routers,
        )
        if advertised is None:
            continue
        combined = min(infinity, link_cost + advertised)
        candidates.append((Route(destination=destination, cost=combined, next_hop=neighbor), True))

    if not candidates:
        return Route(destination, infinity, None), False

    best_route, refreshed = min(candidates, key=lambda item: route_sort_key(item[0]))
    if best_route.cost >= infinity:
        return Route(destination, infinity, None), refreshed
    return best_route, refreshed


def apply_route_aging(
    topology: Mapping[str, Mapping[str, int]],
    previous_tables: Mapping[str, Mapping[str, Route]],
    previous_ages: Mapping[str, Mapping[str, int]],
    next_tables: dict[str, dict[str, Route]],
    refresh_flags: Mapping[str, Mapping[str, bool]],
    *,
    route_timeout: int | None,
    infinity: int,
) -> dict[str, dict[str, int]] | None:
    if route_timeout is None:
        return None

    next_ages: dict[str, dict[str, int]] = {}
    for router, table in next_tables.items():
        next_ages[router] = {}
        for destination, route in table.items():
            if destination == router:
                continue
            if route.next_hop is None:
                next_ages[router][destination] = 0
                continue
            if route.next_hop == destination and destination in topology[router]:
                next_ages[router][destination] = 0
                continue

            previous_route = previous_tables[router].get(destination)
            previous_age = previous_ages.get(router, {}).get(destination, 0)
            refreshed = refresh_flags.get(router, {}).get(destination, False)

            if refreshed:
                age = 0
            elif previous_route is not None and previous_route.next_hop == route.next_hop and previous_route.cost == route.cost:
                age = previous_age + 1
            else:
                age = 0

            if age >= route_timeout:
                next_tables[router][destination] = Route(destination=destination, cost=infinity, next_hop=None)
                next_ages[router][destination] = route_timeout
            else:
                next_ages[router][destination] = age
    return next_ages


def update_once(
    topology: Mapping[str, Mapping[str, int]],
    tables: Mapping[str, Mapping[str, Route]],
    previous_ages: Mapping[str, Mapping[str, int]],
    *,
    mode: str,
    infinity: int,
    silent_routers: set[str],
    route_timeout: int | None,
) -> tuple[dict[str, dict[str, Route]], dict[str, dict[str, int]] | None, bool]:
    all_destinations = sorted(topology)
    next_tables: dict[str, dict[str, Route]] = {}
    refresh_flags: dict[str, dict[str, bool]] = {}

    for router in sorted(topology):
        new_table: dict[str, Route] = {router: Route(destination=router, cost=0, next_hop=router)}
        refresh_flags[router] = {}
        for destination in all_destinations:
            if destination == router:
                continue
            best, refreshed = compute_best_route(
                router,
                destination,
                topology,
                tables,
                mode=mode,
                infinity=infinity,
                silent_routers=silent_routers,
            )
            previous_route = tables[router].get(destination)
            if (
                route_timeout is not None
                and previous_route is not None
                and previous_route.next_hop is not None
                and previous_route.next_hop != destination
                and best.next_hop is None
                and previous_route.next_hop in silent_routers
            ):
                best = previous_route
                refreshed = False
            new_table[destination] = best
            refresh_flags[router][destination] = refreshed
        next_tables[router] = new_table

    next_ages = apply_route_aging(
        topology,
        tables,
        previous_ages,
        next_tables,
        refresh_flags,
        route_timeout=route_timeout,
        infinity=infinity,
    )
    changed = serialize_tables(tables) != serialize_tables(next_tables)
    if route_timeout is not None:
        changed = changed or dict(previous_ages) != dict(next_ages or {})
    return next_tables, next_ages, changed


def run_rounds(
    topology: Mapping[str, Mapping[str, int]],
    initial_tables: Mapping[str, Mapping[str, Route]],
    *,
    mode: str,
    infinity: int,
    max_rounds: int,
    update_strategy: str,
    silent_routers: set[str],
    route_timeout: int | None,
) -> tuple[dict[str, dict[str, Route]], dict[str, dict[str, int]] | None, list[RoundState], bool]:
    tables = clone_tables(initial_tables)
    route_ages = initialize_route_ages(topology, tables) if route_timeout is not None else None
    routers = tuple(sorted(topology))
    advertising_routers = tuple(router for router in routers if router not in silent_routers)
    history: list[RoundState] = [
        RoundState(
            round_index=0,
            changed=False,
            tables=clone_tables(tables),
            active_routers=advertising_routers if update_strategy == "periodic" else advertising_routers,
            route_ages=None if route_ages is None else {router: dict(ages) for router, ages in route_ages.items()},
        )
    ]

    if update_strategy == "periodic":
        converged = False
        current_ages = route_ages or {}
        for round_index in range(1, max_rounds + 1):
            tables, route_ages, changed = update_once(
                topology,
                tables,
                current_ages,
                mode=mode,
                infinity=infinity,
                silent_routers=silent_routers,
                route_timeout=route_timeout,
            )
            current_ages = route_ages or {}
            history.append(
                RoundState(
                    round_index=round_index,
                    changed=changed,
                    tables=clone_tables(tables),
                    active_routers=advertising_routers,
                    route_ages=None if route_ages is None else {router: dict(ages) for router, ages in route_ages.items()},
                )
            )
            if not changed:
                converged = True
                break
        return tables, route_ages, history, converged

    if update_strategy != "triggered":
        raise ValueError("update_strategy must be periodic or triggered")

    converged = False
    current_ages = route_ages or {}
    pending = deque(advertising_routers)
    queued = set(advertising_routers)

    for round_index in range(1, max_rounds + 1):
        if not pending:
            history.append(
                RoundState(
                    round_index=round_index,
                    changed=False,
                    tables=clone_tables(tables),
                    active_routers=(),
                    route_ages=None if route_ages is None else {router: dict(ages) for router, ages in current_ages.items()},
                )
            )
            converged = True
            break

        active_router = pending.popleft()
        queued.remove(active_router)
        next_tables = clone_tables(tables)
        refresh_flags: dict[str, dict[str, bool]] = {router: {} for router in tables}
        changed_routers: list[str] = []

        for router in sorted(topology[active_router]):
            current = tables[router]
            new_table: dict[str, Route] = {router: Route(destination=router, cost=0, next_hop=router)}
            for destination in routers:
                if destination == router:
                    continue
                best, refreshed = compute_best_route(
                    router,
                    destination,
                    topology,
                    tables,
                    mode=mode,
                    infinity=infinity,
                    silent_routers=silent_routers,
                )
                new_table[destination] = best
                refresh_flags[router][destination] = refreshed and best.next_hop == active_router
            if serialize_table(current) != serialize_table(new_table):
                next_tables[router] = new_table
                changed_routers.append(router)

        next_ages = apply_route_aging(
            topology,
            tables,
            current_ages,
            next_tables,
            refresh_flags,
            route_timeout=route_timeout,
            infinity=infinity,
        )
        route_ages = next_ages
        current_ages = next_ages or {}
        tables = next_tables

        for router in sorted(changed_routers):
            for neighbor in sorted(topology[router]):
                if neighbor in silent_routers:
                    continue
                if neighbor not in queued:
                    pending.append(neighbor)
                    queued.add(neighbor)

        changed = bool(changed_routers) or serialize_tables(history[-1].tables) != serialize_tables(tables)
        history.append(
            RoundState(
                round_index=round_index,
                changed=changed,
                tables=clone_tables(tables),
                active_routers=(active_router,),
                route_ages=None if route_ages is None else {router: dict(ages) for router, ages in current_ages.items()},
            )
        )
        if not pending and not changed:
            converged = True
            break

    return tables, route_ages, history, converged


def run_simulation(
    topology: Mapping[str, Mapping[str, int]],
    *,
    mode: str = "classic",
    infinity: int = INFINITY,
    max_rounds: int = 50,
    update_strategy: str = "periodic",
    silent_routers: Sequence[str] | None = None,
    route_timeout: int | None = None,
) -> dict[str, object]:
    if mode not in {"classic", "split-horizon", "poison-reverse"}:
        raise ValueError("mode must be classic, split-horizon, or poison-reverse")
    if update_strategy not in {"periodic", "triggered"}:
        raise ValueError("update_strategy must be periodic or triggered")
    if route_timeout is not None and route_timeout <= 0:
        raise ValueError("route_timeout must be positive when provided")

    normalized = normalize_topology(topology)
    silent = set(silent_routers or ())
    unknown = sorted(silent - set(normalized))
    if unknown:
        raise ValueError(f"silent routers must exist in the topology: {', '.join(unknown)}")

    tables, route_ages, history, converged = run_rounds(
        normalized,
        initialize_tables(normalized),
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
        silent_routers=silent,
        route_timeout=route_timeout,
    )

    payload: dict[str, object] = {
        "mode": mode,
        "infinity": infinity,
        "update_strategy": update_strategy,
        "silent_routers": sorted(silent),
        "route_timeout": route_timeout,
        "topology": {router: dict(sorted(neighbors.items())) for router, neighbors in sorted(normalized.items())},
        "converged": converged,
        "rounds": len(history) - 1,
        "tables": serialize_tables(tables),
        "history": [entry.to_dict() for entry in history],
    }
    if route_ages is not None:
        payload["route_ages"] = {
            router: dict(sorted(ages.items())) for router, ages in sorted(route_ages.items())
        }
    return payload


def remove_link(topology: Mapping[str, Mapping[str, int]], left: str, right: str) -> dict[str, dict[str, int]]:
    normalized = normalize_topology(topology)
    if right not in normalized.get(left, {}) or left not in normalized.get(right, {}):
        raise ValueError(f"link {left!r}<->{right!r} does not exist")
    normalized[left].pop(right)
    normalized[right].pop(left)
    return normalized


def run_outage_simulation(
    topology: Mapping[str, Mapping[str, int]],
    *,
    silent_routers: Sequence[str],
    mode: str = "classic",
    infinity: int = INFINITY,
    max_rounds: int = 50,
    update_strategy: str = "periodic",
    route_timeout: int | None = None,
) -> dict[str, object]:
    normalized = normalize_topology(topology)
    before = run_simulation(
        normalized,
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
        silent_routers=[],
        route_timeout=None,
    )
    initial_tables = {
        router: {
            destination: Route(
                destination=route["destination"],
                cost=int(route["cost"]),
                next_hop=route["next_hop"],
            )
            for destination, route in table.items()
        }
        for router, table in before["tables"].items()
    }
    after_tables, route_ages, outage_history, converged = run_rounds(
        normalized,
        initial_tables,
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
        silent_routers=set(silent_routers),
        route_timeout=route_timeout,
    )
    after_payload: dict[str, object] = {
        "mode": mode,
        "infinity": infinity,
        "update_strategy": update_strategy,
        "silent_routers": sorted(set(silent_routers)),
        "route_timeout": route_timeout,
        "topology": {router: dict(sorted(neighbors.items())) for router, neighbors in sorted(normalized.items())},
        "converged": converged,
        "rounds": len(outage_history) - 1,
        "tables": serialize_tables(after_tables),
        "history": [entry.to_dict() for entry in outage_history],
        "starts_from_converged_before_outage": True,
    }
    if route_ages is not None:
        after_payload["route_ages"] = {
            router: dict(sorted(ages.items())) for router, ages in sorted(route_ages.items())
        }
    return {
        "event": {"type": "silent-router-outage", "routers": sorted(set(silent_routers))},
        "before": before,
        "after": after_payload,
    }


def run_failure_simulation(
    topology: Mapping[str, Mapping[str, int]],
    left: str,
    right: str,
    *,
    mode: str = "classic",
    infinity: int = INFINITY,
    max_rounds: int = 50,
    update_strategy: str = "periodic",
    silent_routers: Sequence[str] | None = None,
    route_timeout: int | None = None,
) -> dict[str, object]:
    normalized = normalize_topology(topology)
    before = run_simulation(
        normalized,
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
        silent_routers=silent_routers,
        route_timeout=route_timeout,
    )
    updated_topology = remove_link(normalized, left, right)
    initial_tables = {
        router: {
            destination: Route(
                destination=route["destination"],
                cost=int(route["cost"]),
                next_hop=route["next_hop"],
            )
            for destination, route in table.items()
        }
        for router, table in before["tables"].items()
    }
    after_tables, route_ages, failure_history, converged = run_rounds(
        updated_topology,
        initial_tables,
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
        silent_routers=set(silent_routers or ()),
        route_timeout=route_timeout,
    )
    after_payload: dict[str, object] = {
        "mode": mode,
        "infinity": infinity,
        "update_strategy": update_strategy,
        "silent_routers": sorted(set(silent_routers or ())),
        "route_timeout": route_timeout,
        "topology": {
            router: dict(sorted(neighbors.items())) for router, neighbors in sorted(updated_topology.items())
        },
        "converged": converged,
        "rounds": len(failure_history) - 1,
        "tables": serialize_tables(after_tables),
        "history": [entry.to_dict() for entry in failure_history],
        "starts_from_converged_before_failure": True,
    }
    if route_ages is not None:
        after_payload["route_ages"] = {
            router: dict(sorted(ages.items())) for router, ages in sorted(route_ages.items())
        }
    return {
        "event": {"type": "remove-link", "left": left, "right": right},
        "before": before,
        "after": after_payload,
    }


def serialize_table(table: Mapping[str, Route]) -> dict[str, dict[str, object]]:
    return {destination: route.to_dict() for destination, route in sorted(table.items())}


def serialize_tables(tables: Mapping[str, Mapping[str, Route]]) -> dict[str, dict[str, dict[str, object]]]:
    return {router: serialize_table(table) for router, table in sorted(tables.items())}


def mermaid_id(label: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in label)


def quote_dot(label: str) -> str:
    return '"' + label.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_topology_diagram(topology: Mapping[str, Mapping[str, int]], *, diagram_format: str) -> str:
    normalized = normalize_topology(topology)
    edges: list[tuple[str, str, int]] = []
    for left, neighbors in sorted(normalized.items()):
        for right, cost in sorted(neighbors.items()):
            if left < right:
                edges.append((left, right, cost))

    if diagram_format == "mermaid":
        lines = ["graph LR"]
        for router in sorted(normalized):
            lines.append(f"    {mermaid_id(router)}[{router}]")
        for left, right, cost in edges:
            lines.append(f"    {mermaid_id(left)} <-->|{cost}| {mermaid_id(right)}")
        return "\n".join(lines)

    lines = ["graph DistanceVectorTopology {", "  rankdir=LR;"]
    for router in sorted(normalized):
        lines.append(f"  {quote_dot(router)} [shape=circle];")
    for left, right, cost in edges:
        lines.append(f"  {quote_dot(left)} -- {quote_dot(right)} [label={quote_dot(str(cost))}];")
    lines.append("}")
    return "\n".join(lines)


def render_routes_diagram(simulation: Mapping[str, object], *, router: str | None, diagram_format: str) -> str:
    tables = simulation["tables"]
    if not isinstance(tables, dict):
        raise ValueError("simulation tables payload must be a mapping")
    routers = sorted(tables)
    if router is not None and router not in tables:
        raise ValueError(f"router {router!r} is not present in the routing tables")

    selected = [router] if router is not None else routers

    if diagram_format == "mermaid":
        lines = ["flowchart TD"]
        for origin in selected:
            root = f"{mermaid_id(origin)}_root"
            lines.append(f"    {root}(({origin}))")
            origin_table = tables[origin]
            for destination, route in sorted(origin_table.items()):
                if destination == origin:
                    continue
                node_id = f"{mermaid_id(origin)}_{mermaid_id(destination)}"
                state = "unreachable" if route["next_hop"] is None else f"via {route['next_hop']}"
                lines.append(f'    {node_id}["{destination}\\ncost={route["cost"]}\\n{state}"]')
                lines.append(f"    {root} --> {node_id}")
        return "\n".join(lines)

    lines = ["digraph DistanceVectorRoutes {", "  rankdir=LR;"]
    for origin in selected:
        lines.append(f"  subgraph cluster_{mermaid_id(origin)} {{")
        lines.append(f"    label={quote_dot(f'Router {origin}')};")
        root = quote_dot(f"{origin}::root")
        lines.append(f"    {root} [label={quote_dot(origin)}, shape=doublecircle];")
        origin_table = tables[origin]
        for destination, route in sorted(origin_table.items()):
            if destination == origin:
                continue
            node_name = quote_dot(f"{origin}::{destination}")
            state = "unreachable" if route["next_hop"] is None else f"via {route['next_hop']}"
            label = f"{destination}\\ncost={route['cost']}\\n{state}"
            lines.append(f"    {node_name} [label={quote_dot(label)}, shape=box];")
            lines.append(f"    {root} -> {node_name};")
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines)


def render_failure_timeline(
    failure_simulation: Mapping[str, object],
    *,
    destination: str,
    diagram_format: str,
    routers: Sequence[str] | None = None,
) -> str:
    after = failure_simulation.get("after")
    if not isinstance(after, Mapping):
        raise ValueError("failure simulation must include an 'after' mapping")
    history = after.get("history")
    if not isinstance(history, list) or not history:
        raise ValueError("failure simulation 'after' payload must include non-empty history")

    available_routers = sorted(history[0]["tables"])
    selected_routers = available_routers if not routers else sorted(dict.fromkeys(routers))
    for router in selected_routers:
        if router not in history[0]["tables"]:
            raise ValueError(f"router {router!r} is not present in the failure history")
        if destination not in history[0]["tables"][router]:
            raise ValueError(f"destination {destination!r} is not present in router {router!r}'s table")

    if diagram_format == "mermaid":
        lines = ["sequenceDiagram"]
        for router in selected_routers:
            lines.append(f"    participant {mermaid_id(router)} as {router}")
        for step in history:
            round_index = step["round"]
            lines.append(f"    Note over {','.join(mermaid_id(router) for router in selected_routers)}: round {round_index}")
            for router in selected_routers:
                route = step["tables"][router][destination]
                next_hop = route["next_hop"] if route["next_hop"] is not None else "unreachable"
                note = f"{destination} cost={route['cost']} via {next_hop}"
                age = step.get("route_ages", {}).get(router, {}).get(destination)
                if age is not None:
                    note += f" age={age}"
                lines.append(f"    Note over {mermaid_id(router)}: {note}")
        return "\n".join(lines)

    lines = [
        "| round | " + " | ".join(f"{router} → {destination}" for router in selected_routers) + " |",
        "| --- | " + " | ".join("---" for _ in selected_routers) + " |",
    ]
    for step in history:
        row = [str(step["round"])]
        for router in selected_routers:
            route = step["tables"][router][destination]
            next_hop = route["next_hop"] if route["next_hop"] is not None else "unreachable"
            cell = f"cost={route['cost']}, via {next_hop}"
            age = step.get("route_ages", {}).get(router, {}).get(destination)
            if age is not None:
                cell += f", age={age}"
            row.append(cell)
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _tracked_route_metrics(
    history: Sequence[Mapping[str, object]],
    *,
    router: str,
    destination: str,
    infinity: int,
) -> dict[str, object]:
    if not history:
        raise ValueError("history must be non-empty")

    baseline_route = history[0]["tables"][router][destination]
    baseline_cost = int(baseline_route["cost"])
    baseline_next_hop = baseline_route["next_hop"]

    first_changed_round: int | None = None
    first_unreachable_round: int | None = None
    last_route_change_round = 0
    max_cost_seen = baseline_cost
    min_cost_seen = baseline_cost
    finite_costs = [baseline_cost] if baseline_cost < infinity else []

    previous_cost = baseline_cost
    previous_next_hop = baseline_next_hop

    for step in history:
        route = step["tables"][router][destination]
        round_index = int(step["round"])
        cost = int(route["cost"])
        next_hop = route["next_hop"]

        max_cost_seen = max(max_cost_seen, cost)
        min_cost_seen = min(min_cost_seen, cost)
        if cost < infinity:
            finite_costs.append(cost)

        if first_changed_round is None and (cost != baseline_cost or next_hop != baseline_next_hop):
            first_changed_round = round_index
        if first_unreachable_round is None and (next_hop is None or cost >= infinity):
            first_unreachable_round = round_index
        if round_index > 0 and (cost != previous_cost or next_hop != previous_next_hop):
            last_route_change_round = round_index

        previous_cost = cost
        previous_next_hop = next_hop

    final_route = history[-1]["tables"][router][destination]
    return {
        "baseline_cost": baseline_cost,
        "baseline_next_hop": baseline_next_hop,
        "final_cost": int(final_route["cost"]),
        "final_next_hop": final_route["next_hop"],
        "first_changed_round": first_changed_round,
        "first_unreachable_round": first_unreachable_round,
        "last_route_change_round": last_route_change_round,
        "max_cost_seen": max_cost_seen,
        "max_finite_cost_seen": max(finite_costs) if finite_costs else None,
        "min_cost_seen": min_cost_seen,
    }


def benchmark_failure_modes(
    topology: Mapping[str, Mapping[str, int]],
    left: str,
    right: str,
    *,
    router: str,
    destination: str,
    modes: Sequence[str] | None = None,
    update_strategies: Sequence[str] | None = None,
    infinity: int = INFINITY,
    max_rounds: int = 50,
    silent_routers: Sequence[str] | None = None,
    route_timeout: int | None = None,
) -> dict[str, object]:
    normalized = normalize_topology(topology)
    if router not in normalized:
        raise ValueError(f"router {router!r} is not present in the topology")
    if destination not in normalized:
        raise ValueError(f"destination {destination!r} is not present in the topology")

    selected_modes = tuple(dict.fromkeys(modes or ("classic", "split-horizon", "poison-reverse")))
    selected_update_strategies = tuple(dict.fromkeys(update_strategies or ("periodic", "triggered")))
    rows: list[dict[str, object]] = []

    for update_strategy in selected_update_strategies:
        for mode in selected_modes:
            failure = run_failure_simulation(
                normalized,
                left,
                right,
                mode=mode,
                infinity=infinity,
                max_rounds=max_rounds,
                update_strategy=update_strategy,
                silent_routers=silent_routers,
                route_timeout=route_timeout,
            )
            after = failure["after"]
            history = after["history"]
            metrics = _tracked_route_metrics(history, router=router, destination=destination, infinity=infinity)
            rows.append(
                {
                    "mode": mode,
                    "update_strategy": update_strategy,
                    "converged": bool(after["converged"]),
                    "rounds": int(after["rounds"]),
                    "changed_rounds": sum(1 for step in history[1:] if step["changed"]),
                    "active_steps": sum(1 for step in history[1:] if step["active_routers"]),
                    "baseline_cost": metrics["baseline_cost"],
                    "baseline_next_hop": metrics["baseline_next_hop"],
                    "final_cost": metrics["final_cost"],
                    "final_next_hop": metrics["final_next_hop"],
                    "first_changed_round": metrics["first_changed_round"],
                    "first_unreachable_round": metrics["first_unreachable_round"],
                    "last_route_change_round": metrics["last_route_change_round"],
                    "max_cost_seen": metrics["max_cost_seen"],
                    "max_finite_cost_seen": metrics["max_finite_cost_seen"],
                    "min_cost_seen": metrics["min_cost_seen"],
                }
            )

    fastest = min(
        rows,
        key=lambda row: (
            row["rounds"],
            row["last_route_change_round"],
            row["mode"],
            row["update_strategy"],
        ),
    )
    earliest_unreachable_candidates = [row for row in rows if row["first_unreachable_round"] is not None]
    earliest_unreachable = min(
        earliest_unreachable_candidates,
        key=lambda row: (
            row["first_unreachable_round"],
            row["rounds"],
            row["mode"],
            row["update_strategy"],
        ),
    ) if earliest_unreachable_candidates else None
    lowest_peak_cost = min(
        rows,
        key=lambda row: (
            row["max_finite_cost_seen"] if row["max_finite_cost_seen"] is not None else infinity,
            row["rounds"],
            row["mode"],
            row["update_strategy"],
        ),
    )

    return {
        "benchmark": "failure-mode-comparison",
        "topology": {router_id: dict(sorted(neighbors.items())) for router_id, neighbors in sorted(normalized.items())},
        "event": {"type": "remove-link", "left": left, "right": right},
        "tracked_route": {"router": router, "destination": destination},
        "modes": list(selected_modes),
        "update_strategies": list(selected_update_strategies),
        "rows": rows,
        "summary": {
            "fastest_reconvergence": {
                "mode": fastest["mode"],
                "update_strategy": fastest["update_strategy"],
                "rounds": fastest["rounds"],
                "last_route_change_round": fastest["last_route_change_round"],
            },
            "earliest_unreachable": None if earliest_unreachable is None else {
                "mode": earliest_unreachable["mode"],
                "update_strategy": earliest_unreachable["update_strategy"],
                "first_unreachable_round": earliest_unreachable["first_unreachable_round"],
            },
            "lowest_peak_cost": {
                "mode": lowest_peak_cost["mode"],
                "update_strategy": lowest_peak_cost["update_strategy"],
                "max_finite_cost_seen": lowest_peak_cost["max_finite_cost_seen"],
            },
        },
    }


def resolve_failure_scenarios(scenario_names: Sequence[str] | None = None) -> list[FailureScenario]:
    selected_names = tuple(dict.fromkeys(scenario_names or tuple(FAILURE_SCENARIOS)))
    if not selected_names:
        raise ValueError("at least one failure scenario must be selected")

    unknown = sorted(name for name in selected_names if name not in FAILURE_SCENARIOS)
    if unknown:
        raise ValueError(f"unknown failure scenarios: {', '.join(unknown)}")

    return [FAILURE_SCENARIOS[name] for name in selected_names]


def benchmark_failure_suite(
    *,
    scenario_names: Sequence[str] | None = None,
    modes: Sequence[str] | None = None,
    update_strategies: Sequence[str] | None = None,
    infinity: int = INFINITY,
    max_rounds: int = 50,
) -> dict[str, object]:
    scenarios = resolve_failure_scenarios(scenario_names)
    selected_modes = tuple(dict.fromkeys(modes or ("classic", "split-horizon", "poison-reverse")))
    selected_update_strategies = tuple(dict.fromkeys(update_strategies or ("periodic", "triggered")))

    combined_rows: list[dict[str, object]] = []
    scenario_results: list[dict[str, object]] = []
    aggregate: dict[tuple[str, str], dict[str, float | int]] = {}
    fastest_wins: dict[tuple[str, str], int] = {}
    earliest_unreachable_wins: dict[tuple[str, str], int] = {}
    lowest_peak_wins: dict[tuple[str, str], int] = {}

    for scenario in scenarios:
        left, right = scenario.remove_link
        benchmark = benchmark_failure_modes(
            scenario.topology,
            left,
            right,
            router=scenario.router,
            destination=scenario.destination,
            modes=selected_modes,
            update_strategies=selected_update_strategies,
            infinity=infinity,
            max_rounds=max_rounds,
        )
        scenario_results.append(
            {
                **scenario.to_dict(),
                "rows": benchmark["rows"],
                "summary": benchmark["summary"],
            }
        )

        summary = benchmark["summary"]
        fastest_key = (
            str(summary["fastest_reconvergence"]["mode"]),
            str(summary["fastest_reconvergence"]["update_strategy"]),
        )
        fastest_wins[fastest_key] = fastest_wins.get(fastest_key, 0) + 1

        earliest_unreachable = summary["earliest_unreachable"]
        if earliest_unreachable is not None:
            earliest_key = (
                str(earliest_unreachable["mode"]),
                str(earliest_unreachable["update_strategy"]),
            )
            earliest_unreachable_wins[earliest_key] = earliest_unreachable_wins.get(earliest_key, 0) + 1

        lowest_peak_key = (
            str(summary["lowest_peak_cost"]["mode"]),
            str(summary["lowest_peak_cost"]["update_strategy"]),
        )
        lowest_peak_wins[lowest_peak_key] = lowest_peak_wins.get(lowest_peak_key, 0) + 1

        for row in benchmark["rows"]:
            combined_row = {
                "scenario": scenario.name,
                "scenario_description": scenario.description,
                "tracked_router": scenario.router,
                "tracked_destination": scenario.destination,
                "removed_link": f"{left}<->{right}",
                **row,
            }
            combined_rows.append(combined_row)

            key = (str(row["mode"]), str(row["update_strategy"]))
            slot = aggregate.setdefault(
                key,
                {
                    "scenario_count": 0,
                    "non_converged_runs": 0,
                    "rounds_total": 0,
                    "last_route_change_total": 0,
                    "max_finite_cost_total": 0,
                    "max_finite_cost_count": 0,
                },
            )
            slot["scenario_count"] += 1
            if not row["converged"]:
                slot["non_converged_runs"] += 1
            slot["rounds_total"] += int(row["rounds"])
            slot["last_route_change_total"] += int(row["last_route_change_round"])
            if row["max_finite_cost_seen"] is not None:
                slot["max_finite_cost_total"] += int(row["max_finite_cost_seen"])
                slot["max_finite_cost_count"] += 1

    scorecard: list[dict[str, object]] = []
    for update_strategy in selected_update_strategies:
        for mode in selected_modes:
            key = (mode, update_strategy)
            slot = aggregate.get(key)
            if slot is None:
                continue
            scenario_count = int(slot["scenario_count"])
            finite_cost_count = int(slot["max_finite_cost_count"])
            scorecard.append(
                {
                    "mode": mode,
                    "update_strategy": update_strategy,
                    "scenario_count": scenario_count,
                    "non_converged_runs": int(slot["non_converged_runs"]),
                    "average_rounds": round(float(slot["rounds_total"]) / scenario_count, 2),
                    "average_last_route_change_round": round(
                        float(slot["last_route_change_total"]) / scenario_count,
                        2,
                    ),
                    "average_max_finite_cost": (
                        None
                        if finite_cost_count == 0
                        else round(float(slot["max_finite_cost_total"]) / finite_cost_count, 2)
                    ),
                    "fastest_reconvergence_wins": fastest_wins.get(key, 0),
                    "earliest_unreachable_wins": earliest_unreachable_wins.get(key, 0),
                    "lowest_peak_cost_wins": lowest_peak_wins.get(key, 0),
                }
            )

    return {
        "suite": "portfolio-failure-scenarios",
        "infinity": infinity,
        "max_rounds": max_rounds,
        "scenario_names": [scenario.name for scenario in scenarios],
        "modes": list(selected_modes),
        "update_strategies": list(selected_update_strategies),
        "rows": combined_rows,
        "scorecard": scorecard,
        "scenarios": scenario_results,
    }


def render_failure_benchmark(benchmark: Mapping[str, object], *, output_format: str) -> str:
    rows = benchmark["rows"]
    if not isinstance(rows, list):
        raise ValueError("benchmark rows payload must be a list")

    columns = [
        "mode",
        "update_strategy",
        "converged",
        "rounds",
        "changed_rounds",
        "active_steps",
        "baseline_cost",
        "baseline_next_hop",
        "final_cost",
        "final_next_hop",
        "first_changed_round",
        "first_unreachable_round",
        "last_route_change_round",
        "max_cost_seen",
        "max_finite_cost_seen",
    ]

    if output_format == "json":
        return json.dumps(benchmark, indent=2, sort_keys=True)

    if output_format == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            csv_row = {column: row.get(column) for column in columns}
            if csv_row["final_next_hop"] is None:
                csv_row["final_next_hop"] = "unreachable"
            writer.writerow(csv_row)
        return buffer.getvalue().rstrip()

    tracked_route = benchmark["tracked_route"]
    event = benchmark["event"]
    lines = [
        f"# Failure benchmark for {tracked_route['router']} → {tracked_route['destination']}",
        "",
        f"Link removal: `{event['left']} ↔ {event['right']}`",
        "",
        "| mode | update strategy | converged | rounds | changed rounds | active steps | baseline | final | first change | first unreachable | last route change | max cost | max finite cost |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        baseline = f"{row['baseline_cost']} via {row['baseline_next_hop']}"
        final_next_hop = row["final_next_hop"] if row["final_next_hop"] is not None else "unreachable"
        final = f"{row['final_cost']} via {final_next_hop}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["mode"]),
                    str(row["update_strategy"]),
                    str(row["converged"]),
                    str(row["rounds"]),
                    str(row["changed_rounds"]),
                    str(row["active_steps"]),
                    baseline,
                    final,
                    str(row["first_changed_round"]),
                    str(row["first_unreachable_round"]),
                    str(row["last_route_change_round"]),
                    str(row["max_cost_seen"]),
                    str(row["max_finite_cost_seen"]),
                ]
            )
            + " |"
        )

    summary = benchmark["summary"]
    lines.extend(
        [
            "",
            "## Summary",
            f"- fastest reconvergence: `{summary['fastest_reconvergence']['mode']}` + `{summary['fastest_reconvergence']['update_strategy']}` in {summary['fastest_reconvergence']['rounds']} rounds",
            (
                "- earliest unreachable: none"
                if summary["earliest_unreachable"] is None
                else f"- earliest unreachable: `{summary['earliest_unreachable']['mode']}` + `{summary['earliest_unreachable']['update_strategy']}` at round {summary['earliest_unreachable']['first_unreachable_round']}"
            ),
            f"- lowest peak finite tracked-route cost: `{summary['lowest_peak_cost']['mode']}` + `{summary['lowest_peak_cost']['update_strategy']}` with max finite cost {summary['lowest_peak_cost']['max_finite_cost_seen']}",
        ]
    )
    return "\n".join(lines)


def render_failure_benchmark_suite(suite: Mapping[str, object], *, output_format: str) -> str:
    rows = suite["rows"]
    scenarios = suite["scenarios"]
    scorecard = suite["scorecard"]
    if not isinstance(rows, list) or not isinstance(scenarios, list) or not isinstance(scorecard, list):
        raise ValueError("suite payload must include rows, scenarios, and scorecard lists")

    if output_format == "json":
        return json.dumps(suite, indent=2, sort_keys=True)

    if output_format == "csv":
        columns = [
            "scenario",
            "scenario_description",
            "removed_link",
            "tracked_router",
            "tracked_destination",
            "mode",
            "update_strategy",
            "converged",
            "rounds",
            "changed_rounds",
            "active_steps",
            "baseline_cost",
            "baseline_next_hop",
            "final_cost",
            "final_next_hop",
            "first_changed_round",
            "first_unreachable_round",
            "last_route_change_round",
            "max_cost_seen",
            "max_finite_cost_seen",
            "min_cost_seen",
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            csv_row = {column: row.get(column) for column in columns}
            if csv_row["final_next_hop"] is None:
                csv_row["final_next_hop"] = "unreachable"
            writer.writerow(csv_row)
        return buffer.getvalue().rstrip()

    lines = [
        "# Failure benchmark suite",
        "",
        f"Infinity metric: {suite['infinity']}, max rounds: {suite['max_rounds']}",
        "",
        f"Curated scenarios: {len(scenarios)}",
        "",
        "## Scenario roster",
        "",
        "| scenario | tracked route | link removal | description |",
        "| --- | --- | --- | --- |",
    ]
    for scenario in scenarios:
        tracked_route = scenario["tracked_route"]
        event = scenario["event"]
        lines.append(
            f"| {scenario['name']} | {tracked_route['router']} → {tracked_route['destination']} | {event['left']} ↔ {event['right']} | {scenario['description']} |"
        )

    lines.extend(
        [
            "",
            "## Strategy scorecard",
            "",
            "| mode | update strategy | scenarios | non-converged | avg rounds | avg last route change | avg max finite cost | fastest wins | earliest unreachable wins | lowest peak wins |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in scorecard:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["mode"]),
                    str(row["update_strategy"]),
                    str(row["scenario_count"]),
                    str(row["non_converged_runs"]),
                    str(row["average_rounds"]),
                    str(row["average_last_route_change_round"]),
                    str(row["average_max_finite_cost"]),
                    str(row["fastest_reconvergence_wins"]),
                    str(row["earliest_unreachable_wins"]),
                    str(row["lowest_peak_cost_wins"]),
                ]
            )
            + " |"
        )

    for scenario in scenarios:
        tracked_route = scenario["tracked_route"]
        event = scenario["event"]
        lines.extend(
            [
                "",
                f"## Scenario: {scenario['name']}",
                "",
                scenario["description"],
                "",
                f"- tracked route: `{tracked_route['router']} → {tracked_route['destination']}`",
                f"- link removal: `{event['left']} ↔ {event['right']}`",
                "",
                "| mode | update strategy | converged | rounds | changed rounds | active steps | baseline | final | first change | first unreachable | last route change | max cost | max finite cost |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for row in scenario["rows"]:
            baseline = f"{row['baseline_cost']} via {row['baseline_next_hop']}"
            final_next_hop = row["final_next_hop"] if row["final_next_hop"] is not None else "unreachable"
            final = f"{row['final_cost']} via {final_next_hop}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row["mode"]),
                        str(row["update_strategy"]),
                        str(row["converged"]),
                        str(row["rounds"]),
                        str(row["changed_rounds"]),
                        str(row["active_steps"]),
                        baseline,
                        final,
                        str(row["first_changed_round"]),
                        str(row["first_unreachable_round"]),
                        str(row["last_route_change_round"]),
                        str(row["max_cost_seen"]),
                        str(row["max_finite_cost_seen"]),
                    ]
                )
                + " |"
            )
        summary = scenario["summary"]
        lines.extend(
            [
                "",
                f"- fastest reconvergence: `{summary['fastest_reconvergence']['mode']}` + `{summary['fastest_reconvergence']['update_strategy']}` in {summary['fastest_reconvergence']['rounds']} rounds",
                (
                    "- earliest unreachable: none"
                    if summary["earliest_unreachable"] is None
                    else f"- earliest unreachable: `{summary['earliest_unreachable']['mode']}` + `{summary['earliest_unreachable']['update_strategy']}` at round {summary['earliest_unreachable']['first_unreachable_round']}"
                ),
                f"- lowest peak finite tracked-route cost: `{summary['lowest_peak_cost']['mode']}` + `{summary['lowest_peak_cost']['update_strategy']}` with max finite cost {summary['lowest_peak_cost']['max_finite_cost_seen']}",
            ]
        )

    return "\n".join(lines)


def export_diagram(
    topology: Mapping[str, Mapping[str, int]],
    *,
    snapshot: str,
    diagram_format: str,
    mode: str,
    infinity: int,
    max_rounds: int,
    update_strategy: str = "periodic",
    silent_routers: Sequence[str] | None = None,
    route_timeout: int | None = None,
    router: str | None,
) -> str:
    if snapshot == "topology":
        return render_topology_diagram(topology, diagram_format=diagram_format)
    simulation = run_simulation(
        topology,
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
        silent_routers=silent_routers,
        route_timeout=route_timeout,
    )
    return render_routes_diagram(simulation, router=router, diagram_format=diagram_format)


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
    simulate_parser.add_argument("--update-strategy", default="periodic", choices=["periodic", "triggered"])
    simulate_parser.add_argument("--silent-routers", nargs="*", default=[])
    simulate_parser.add_argument("--route-timeout", type=int)

    failure_parser = subparsers.add_parser("simulate-failure", help="remove one link and observe reconvergence")
    failure_parser.add_argument("--topology", required=True)
    failure_parser.add_argument("--remove-link", nargs=2, metavar=("LEFT", "RIGHT"), required=True)
    failure_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    failure_parser.add_argument("--infinity", type=int, default=INFINITY)
    failure_parser.add_argument("--max-rounds", type=int, default=50)
    failure_parser.add_argument("--update-strategy", default="periodic", choices=["periodic", "triggered"])
    failure_parser.add_argument("--silent-routers", nargs="*", default=[])
    failure_parser.add_argument("--route-timeout", type=int)

    outage_parser = subparsers.add_parser(
        "simulate-outage",
        help="treat one or more routers as silent and observe stale-route expiration from a converged state",
    )
    outage_parser.add_argument("--topology", required=True)
    outage_parser.add_argument("--silent-routers", nargs="+", required=True)
    outage_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    outage_parser.add_argument("--infinity", type=int, default=INFINITY)
    outage_parser.add_argument("--max-rounds", type=int, default=50)
    outage_parser.add_argument("--update-strategy", default="periodic", choices=["periodic", "triggered"])
    outage_parser.add_argument("--route-timeout", type=int)

    diagram_parser = subparsers.add_parser("export-diagram", help="render topology or routing tables as Mermaid or Graphviz")
    diagram_parser.add_argument("--topology", required=True)
    diagram_parser.add_argument("--snapshot", default="topology", choices=["topology", "routes"])
    diagram_parser.add_argument("--format", dest="diagram_format", default="mermaid", choices=["mermaid", "dot"])
    diagram_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    diagram_parser.add_argument("--infinity", type=int, default=INFINITY)
    diagram_parser.add_argument("--max-rounds", type=int, default=50)
    diagram_parser.add_argument("--update-strategy", default="periodic", choices=["periodic", "triggered"])
    diagram_parser.add_argument("--silent-routers", nargs="*", default=[])
    diagram_parser.add_argument("--route-timeout", type=int)
    diagram_parser.add_argument("--router", help="limit route snapshots to one router")

    timeline_parser = subparsers.add_parser(
        "export-timeline",
        help="render per-round failure reconvergence for one destination as Markdown or Mermaid",
    )
    timeline_parser.add_argument("--topology", required=True)
    timeline_parser.add_argument("--remove-link", nargs=2, metavar=("LEFT", "RIGHT"), required=True)
    timeline_parser.add_argument("--destination", required=True)
    timeline_parser.add_argument("--routers", nargs="*", help="optional router subset to include in the timeline")
    timeline_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    timeline_parser.add_argument("--format", dest="timeline_format", default="markdown", choices=["markdown", "mermaid"])
    timeline_parser.add_argument("--infinity", type=int, default=INFINITY)
    timeline_parser.add_argument("--max-rounds", type=int, default=50)
    timeline_parser.add_argument("--update-strategy", default="periodic", choices=["periodic", "triggered"])
    timeline_parser.add_argument("--silent-routers", nargs="*", default=[])
    timeline_parser.add_argument("--route-timeout", type=int)

    benchmark_parser = subparsers.add_parser(
        "benchmark-failure",
        help="compare failure reconvergence behavior across routing modes and update strategies",
    )
    benchmark_parser.add_argument("--topology", required=True)
    benchmark_parser.add_argument("--remove-link", nargs=2, metavar=("LEFT", "RIGHT"), required=True)
    benchmark_parser.add_argument("--router", required=True, help="router whose route should be tracked")
    benchmark_parser.add_argument("--destination", required=True, help="destination to follow during reconvergence")
    benchmark_parser.add_argument(
        "--modes",
        nargs="*",
        default=["classic", "split-horizon", "poison-reverse"],
        choices=["classic", "split-horizon", "poison-reverse"],
    )
    benchmark_parser.add_argument(
        "--update-strategies",
        nargs="*",
        default=["periodic", "triggered"],
        choices=["periodic", "triggered"],
    )
    benchmark_parser.add_argument("--format", dest="benchmark_format", default="json", choices=["json", "csv", "markdown"])
    benchmark_parser.add_argument("--infinity", type=int, default=INFINITY)
    benchmark_parser.add_argument("--max-rounds", type=int, default=50)
    benchmark_parser.add_argument("--silent-routers", nargs="*", default=[])
    benchmark_parser.add_argument("--route-timeout", type=int)

    suite_parser = subparsers.add_parser(
        "benchmark-failure-suite",
        help="run the built-in failure scenario suite across routing modes and update strategies",
    )
    suite_parser.add_argument(
        "--scenarios",
        nargs="*",
        default=list(FAILURE_SCENARIOS),
        choices=list(FAILURE_SCENARIOS),
        help="optional subset of built-in curated scenarios",
    )
    suite_parser.add_argument(
        "--modes",
        nargs="*",
        default=["classic", "split-horizon", "poison-reverse"],
        choices=["classic", "split-horizon", "poison-reverse"],
    )
    suite_parser.add_argument(
        "--update-strategies",
        nargs="*",
        default=["periodic", "triggered"],
        choices=["periodic", "triggered"],
    )
    suite_parser.add_argument("--format", dest="suite_format", default="json", choices=["json", "csv", "markdown"])
    suite_parser.add_argument("--infinity", type=int, default=INFINITY)
    suite_parser.add_argument("--max-rounds", type=int, default=50)

    return parser


def cli(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "infinity", INFINITY) <= 0:
        parser.error("--infinity must be positive")
    if getattr(args, "max_rounds", 1) <= 0:
        parser.error("--max-rounds must be positive")
    if getattr(args, "route_timeout", None) is not None and args.route_timeout <= 0:
        parser.error("--route-timeout must be positive")

    if args.command == "benchmark-failure-suite":
        suite = benchmark_failure_suite(
            scenario_names=args.scenarios,
            modes=args.modes,
            update_strategies=args.update_strategies,
            infinity=args.infinity,
            max_rounds=args.max_rounds,
        )
        payload = render_failure_benchmark_suite(suite, output_format=args.suite_format)
    else:
        topology = parse_topology(args.topology)

        if args.command == "simulate":
            payload: object = run_simulation(
                topology,
                mode=args.mode,
                infinity=args.infinity,
                max_rounds=args.max_rounds,
                update_strategy=args.update_strategy,
                silent_routers=args.silent_routers,
                route_timeout=args.route_timeout,
            )
        elif args.command == "simulate-failure":
            left, right = args.remove_link
            payload = run_failure_simulation(
                topology,
                left,
                right,
                mode=args.mode,
                infinity=args.infinity,
                max_rounds=args.max_rounds,
                update_strategy=args.update_strategy,
                silent_routers=args.silent_routers,
                route_timeout=args.route_timeout,
            )
        elif args.command == "simulate-outage":
            payload = run_outage_simulation(
                topology,
                silent_routers=args.silent_routers,
                mode=args.mode,
                infinity=args.infinity,
                max_rounds=args.max_rounds,
                update_strategy=args.update_strategy,
                route_timeout=args.route_timeout,
            )
        elif args.command == "export-timeline":
            left, right = args.remove_link
            failure = run_failure_simulation(
                topology,
                left,
                right,
                mode=args.mode,
                infinity=args.infinity,
                max_rounds=args.max_rounds,
                update_strategy=args.update_strategy,
                silent_routers=args.silent_routers,
                route_timeout=args.route_timeout,
            )
            payload = render_failure_timeline(
                failure,
                destination=args.destination,
                diagram_format=args.timeline_format,
                routers=args.routers,
            )
        elif args.command == "benchmark-failure":
            left, right = args.remove_link
            benchmark = benchmark_failure_modes(
                topology,
                left,
                right,
                router=args.router,
                destination=args.destination,
                modes=args.modes,
                update_strategies=args.update_strategies,
                infinity=args.infinity,
                max_rounds=args.max_rounds,
                silent_routers=args.silent_routers,
                route_timeout=args.route_timeout,
            )
            payload = render_failure_benchmark(benchmark, output_format=args.benchmark_format)
        else:
            payload = export_diagram(
                topology,
                snapshot=args.snapshot,
                diagram_format=args.diagram_format,
                mode=args.mode,
                infinity=args.infinity,
                max_rounds=args.max_rounds,
                update_strategy=args.update_strategy,
                silent_routers=args.silent_routers,
                route_timeout=args.route_timeout,
                router=args.router,
            )

    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
