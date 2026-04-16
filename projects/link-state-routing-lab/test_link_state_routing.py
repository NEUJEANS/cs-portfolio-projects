from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from link_state_routing import (
    LinkStateAdvertisement,
    MAX_AGE,
    compare_with_distance_vector,
    compute_forwarding_tables,
    flood_lsas,
    normalize_topology,
    originate_lsas,
    render_mermaid,
    run_simulation,
)


TOPOLOGY = {
    "A": {"B": 1, "C": 4},
    "B": {"A": 1, "C": 2, "D": 7},
    "C": {"A": 4, "B": 2, "D": 1},
    "D": {"B": 7, "C": 1},
}


def test_run_simulation_builds_forwarding_tables() -> None:
    result = run_simulation(TOPOLOGY)

    a_to_d = result.routes["A"]["D"]
    assert a_to_d.cost == 4
    assert a_to_d.next_hop == "B"
    assert a_to_d.path == ("A", "B", "C", "D")

    d_to_a = result.routes["D"]["A"]
    assert d_to_a.cost == 4
    assert d_to_a.next_hop == "C"
    assert d_to_a.path == ("D", "C", "B", "A")


def test_stale_lsa_is_ignored_during_flooding() -> None:
    topology = normalize_topology(TOPOLOGY)
    initial = originate_lsas(topology)
    first_lsdb, _ = flood_lsas(topology, initial)

    stale = LinkStateAdvertisement(router="B", neighbors={"A": 9}, sequence=1, age=0)
    refreshed = LinkStateAdvertisement(router="B", neighbors={"A": 1, "C": 2, "D": 7}, sequence=2, age=0)
    lsdb, log = flood_lsas(topology, [stale, refreshed], initial_lsdb=first_lsdb)

    assert lsdb["B"].sequence == 2
    assert lsdb["B"].neighbors == {"A": 1, "C": 2, "D": 7}
    assert any(step.accepted is False and step.router == "B" and step.sequence == 1 for step in log)


def test_max_age_lsa_withdraws_router_entry() -> None:
    topology = normalize_topology(TOPOLOGY)
    initial = originate_lsas(topology)
    lsdb, _ = flood_lsas(topology, initial)

    withdrawn = LinkStateAdvertisement(router="C", neighbors={}, sequence=99, age=MAX_AGE)
    lsdb, _ = flood_lsas(topology, [withdrawn], initial_lsdb=lsdb)

    assert "C" not in lsdb


def test_reconverges_after_link_failure() -> None:
    initial = run_simulation(TOPOLOGY)
    changed_topology = {
        "A": {"B": 1, "C": 4},
        "B": {"A": 1, "C": 2, "D": 20},
        "C": {"A": 4, "B": 2, "D": 1},
        "D": {"B": 20, "C": 1},
    }

    updated = run_simulation(changed_topology, previous_lsdb=initial.lsdb)

    assert updated.routes["B"]["D"].cost == 3
    assert updated.routes["B"]["D"].path == ("B", "C", "D")
    assert updated.lsdb["B"].sequence == initial.lsdb["B"].sequence + 1
    assert updated.lsdb["D"].sequence == initial.lsdb["D"].sequence + 1


def test_render_mermaid_includes_weighted_edges_and_spf_tree() -> None:
    result = run_simulation(TOPOLOGY)

    diagram = render_mermaid(result, source="A")

    assert diagram.startswith("flowchart LR")
    assert 'A <-->|"1"| B' in diagram
    assert 'B <-->|"2"| C' in diagram
    assert 'A -->|"SPF 1"| B' in diagram
    assert 'B -->|"SPF 2"| C' in diagram
    assert 'C -->|"SPF 1"| D' in diagram
    assert 'class A root' in diagram


def test_cli_json_output(tmp_path: Path) -> None:
    topology_path = tmp_path / "topology.json"
    topology_path.write_text(json.dumps(TOPOLOGY), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "link_state_routing.py", str(topology_path), "--format", "json", "--source", "A"],
        cwd=Path(__file__).parent,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["routes"]["A"]["D"]["cost"] == 4
    assert payload["lsdb"]["A"]["sequence"] == 1


def test_cli_mermaid_output(tmp_path: Path) -> None:
    topology_path = tmp_path / "topology.json"
    topology_path.write_text(json.dumps(TOPOLOGY), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "link_state_routing.py", str(topology_path), "--format", "mermaid", "--source", "A"],
        cwd=Path(__file__).parent,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.startswith("flowchart LR")
    assert '%% SPF tree rooted at A' in result.stdout
    assert 'A -->|"SPF 1"| B' in result.stdout


def test_compute_forwarding_tables_requires_symmetric_lsdb() -> None:
    with pytest.raises(ValueError):
        compute_forwarding_tables(
            {
                "A": LinkStateAdvertisement(router="A", neighbors={"B": 1}, sequence=1),
                "B": LinkStateAdvertisement(router="B", neighbors={}, sequence=1),
            }
        )


def test_compare_with_distance_vector_reports_before_and_after_summary() -> None:
    comparison = compare_with_distance_vector(TOPOLOGY, remove_link=("B", "D"), max_rounds=20)

    assert comparison["before"]["link_state"]["flood_rounds"] >= 1
    assert comparison["before"]["distance_vector"]["rounds"] >= 1
    assert comparison["event"] == {"type": "remove-link", "left": "B", "right": "D"}
    assert set(comparison["after"]["link_state"]["changed_routers"]) == {"B", "D"}
    assert comparison["after"]["distance_vector"]["converged"] is True
    assert len(comparison["observations"]) >= 2


def test_cli_compare_distance_vector_json_output(tmp_path: Path) -> None:
    topology_path = tmp_path / "topology.json"
    topology_path.write_text(json.dumps(TOPOLOGY), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "link_state_routing.py",
            str(topology_path),
            "--compare-distance-vector",
            "--remove-link",
            "B",
            "D",
            "--distance-vector-mode",
            "poison-reverse",
            "--distance-vector-update-strategy",
            "triggered",
            "--max-rounds",
            "20",
        ],
        cwd=Path(__file__).parent,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["distance_vector_mode"] == "poison-reverse"
    assert payload["distance_vector_update_strategy"] == "triggered"
    assert payload["event"] == {"type": "remove-link", "left": "B", "right": "D"}
    assert payload["after"]["distance_vector"]["rounds"] >= 1
