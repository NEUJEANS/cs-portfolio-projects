from __future__ import annotations

import argparse
import json
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

    def to_dict(self) -> dict[str, object]:
        return {
            "round": self.round_index,
            "changed": self.changed,
            "active_routers": list(self.active_routers),
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
        table: dict[str, Route] = {router: Route(destination=router, cost=0, next_hop=router)}
        for neighbor, cost in sorted(neighbors.items()):
            table[neighbor] = Route(destination=neighbor, cost=cost, next_hop=neighbor)
        tables[router] = table
    return tables


def advertised_cost(route: Route, *, recipient: str, mode: str, infinity: int) -> int | None:
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
        new_table: dict[str, Route] = {router: Route(destination=router, cost=0, next_hop=router)}
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


def run_rounds(
    topology: Mapping[str, Mapping[str, int]],
    initial_tables: Mapping[str, Mapping[str, Route]],
    *,
    mode: str,
    infinity: int,
    max_rounds: int,
    update_strategy: str,
) -> tuple[dict[str, dict[str, Route]], list[RoundState], bool]:
    tables = {router: dict(table) for router, table in initial_tables.items()}
    routers = tuple(sorted(topology))
    history: list[RoundState] = [RoundState(round_index=0, changed=False, tables=tables, active_routers=routers)]

    if update_strategy == "periodic":
        converged = False
        for round_index in range(1, max_rounds + 1):
            tables, changed = update_once(topology, tables, mode=mode, infinity=infinity)
            history.append(RoundState(round_index=round_index, changed=changed, tables=tables, active_routers=routers))
            if not changed:
                converged = True
                break
        return tables, history, converged

    if update_strategy != "triggered":
        raise ValueError("update_strategy must be periodic or triggered")

    converged = False
    pending = deque(routers)
    queued = set(routers)

    for round_index in range(1, max_rounds + 1):
        if not pending:
            history.append(RoundState(round_index=round_index, changed=False, tables=tables, active_routers=()))
            converged = True
            break

        active_router = pending.popleft()
        queued.remove(active_router)
        changed_routers: list[str] = []
        next_tables = {router: dict(table) for router, table in tables.items()}

        for router in sorted(topology[active_router]):
            current = tables[router]
            new_table: dict[str, Route] = {router: Route(destination=router, cost=0, next_hop=router)}
            for destination in routers:
                if destination == router:
                    continue
                candidates: list[Route] = []
                direct_cost = topology[router].get(destination)
                if direct_cost is not None:
                    candidates.append(Route(destination=destination, cost=direct_cost, next_hop=destination))
                for neighbor, link_cost in sorted(topology[router].items()):
                    if neighbor != active_router:
                        neighbor_route = tables[neighbor].get(destination)
                    else:
                        neighbor_route = tables[active_router].get(destination)
                    if neighbor_route is None:
                        continue
                    advertised = advertised_cost(
                        neighbor_route,
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
            if serialize_table(current) != serialize_table(new_table):
                next_tables[router] = new_table
                changed_routers.append(router)

        tables = next_tables
        for router in sorted(changed_routers):
            for neighbor in sorted(topology[router]):
                if neighbor not in queued:
                    pending.append(neighbor)
                    queued.add(neighbor)
        history.append(
            RoundState(
                round_index=round_index,
                changed=bool(changed_routers),
                tables=tables,
                active_routers=(active_router,),
            )
        )
        if not pending and not changed_routers:
            converged = True
            break

    return tables, history, converged


def run_simulation(
    topology: Mapping[str, Mapping[str, int]],
    *,
    mode: str = "classic",
    infinity: int = INFINITY,
    max_rounds: int = 50,
    update_strategy: str = "periodic",
) -> dict[str, object]:
    if mode not in {"classic", "split-horizon", "poison-reverse"}:
        raise ValueError("mode must be classic, split-horizon, or poison-reverse")
    if update_strategy not in {"periodic", "triggered"}:
        raise ValueError("update_strategy must be periodic or triggered")
    normalized = normalize_topology(topology)
    tables, history, converged = run_rounds(
        normalized,
        initialize_tables(normalized),
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
    )

    return {
        "mode": mode,
        "infinity": infinity,
        "update_strategy": update_strategy,
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


def run_failure_simulation(
    topology: Mapping[str, Mapping[str, int]],
    left: str,
    right: str,
    *,
    mode: str = "classic",
    infinity: int = INFINITY,
    max_rounds: int = 50,
    update_strategy: str = "periodic",
) -> dict[str, object]:
    normalized = normalize_topology(topology)
    before = run_simulation(
        normalized,
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
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
    after_tables, failure_history, converged = run_rounds(
        updated_topology,
        initial_tables,
        mode=mode,
        infinity=infinity,
        max_rounds=max_rounds,
        update_strategy=update_strategy,
    )
    return {
        "event": {"type": "remove-link", "left": left, "right": right},
        "before": before,
        "after": {
            "mode": mode,
            "infinity": infinity,
            "update_strategy": update_strategy,
            "topology": {
                router: dict(sorted(neighbors.items())) for router, neighbors in sorted(updated_topology.items())
            },
            "converged": converged,
            "rounds": len(failure_history) - 1,
            "tables": serialize_tables(after_tables),
            "history": [entry.to_dict() for entry in failure_history],
            "starts_from_converged_before_failure": True,
        },
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
                lines.append(
                    f"    Note over {mermaid_id(router)}: {destination} cost={route['cost']} via {next_hop}"
                )
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
            row.append(f"cost={route['cost']}, via {next_hop}")
        lines.append("| " + " | ".join(row) + " |")
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

    failure_parser = subparsers.add_parser("simulate-failure", help="remove one link and observe reconvergence")
    failure_parser.add_argument("--topology", required=True)
    failure_parser.add_argument("--remove-link", nargs=2, metavar=("LEFT", "RIGHT"), required=True)
    failure_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    failure_parser.add_argument("--infinity", type=int, default=INFINITY)
    failure_parser.add_argument("--max-rounds", type=int, default=50)
    failure_parser.add_argument("--update-strategy", default="periodic", choices=["periodic", "triggered"])

    diagram_parser = subparsers.add_parser("export-diagram", help="render topology or routing tables as Mermaid or Graphviz")
    diagram_parser.add_argument("--topology", required=True)
    diagram_parser.add_argument("--snapshot", default="topology", choices=["topology", "routes"])
    diagram_parser.add_argument("--format", dest="diagram_format", default="mermaid", choices=["mermaid", "dot"])
    diagram_parser.add_argument("--mode", default="classic", choices=["classic", "split-horizon", "poison-reverse"])
    diagram_parser.add_argument("--infinity", type=int, default=INFINITY)
    diagram_parser.add_argument("--max-rounds", type=int, default=50)
    diagram_parser.add_argument("--update-strategy", default="periodic", choices=["periodic", "triggered"])
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

    return parser


def cli(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "infinity", INFINITY) <= 0:
        parser.error("--infinity must be positive")
    if getattr(args, "max_rounds", 1) <= 0:
        parser.error("--max-rounds must be positive")

    topology = parse_topology(args.topology)
    if args.command == "simulate":
        payload: object = run_simulation(
            topology,
            mode=args.mode,
            infinity=args.infinity,
            max_rounds=args.max_rounds,
            update_strategy=args.update_strategy,
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
        )
        payload = render_failure_timeline(
            failure,
            destination=args.destination,
            diagram_format=args.timeline_format,
            routers=args.routers,
        )
    else:
        payload = export_diagram(
            topology,
            snapshot=args.snapshot,
            diagram_format=args.diagram_format,
            mode=args.mode,
            infinity=args.infinity,
            max_rounds=args.max_rounds,
            update_strategy=args.update_strategy,
            router=args.router,
        )

    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
