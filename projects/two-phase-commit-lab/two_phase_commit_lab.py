from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class ScenarioError(ValueError):
    """Raised when a scenario JSON file is invalid."""


VALID_VOTES = {"commit", "abort", "timeout"}
VALID_CRASH_POINTS = {"none", "before-decision", "after-decision-log"}
VALID_SECOND_PHASE_DELIVERIES = {"deliver", "miss"}


@dataclass
class ParticipantPlan:
    name: str
    vote: str
    role: str = "participant"
    notes: str = ""
    second_phase_delivery: str = "deliver"
    reconnect_after_missed_decision: bool = False


@dataclass
class FailurePlan:
    coordinator_crash: str = "none"
    recover_after_crash: bool = False
    decision_deliveries_before_crash: int = 0


@dataclass
class Scenario:
    title: str
    description: str
    transaction_id: str
    participants: list[ParticipantPlan]
    failures: FailurePlan = field(default_factory=FailurePlan)


@dataclass
class SimulationResult:
    title: str
    description: str
    transaction_id: str
    outcome: str
    decision: str | None
    decision_durable: bool
    blocking_reason: str | None
    failures: dict[str, Any]
    participants: list[dict[str, Any]]
    trace: list[str]
    takeaways: list[str]
    termination_hint_summary: str | None
    termination_hints: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParticipantRuntime:
    plan: ParticipantPlan
    state: str = "new"
    acked_decision: bool = False
    prepared: bool = False
    missed_second_phase_delivery: bool = False
    recovered_after_reconnect: bool = False


@dataclass
class CoordinatorRuntime:
    state: str = "running"
    decision: str | None = None
    decision_durable: bool = False


@dataclass
class CatalogEntry:
    source_path: str
    report_path: str | None
    result: SimulationResult


@dataclass
class ProtocolComparison:
    protocol: str
    outcome: str
    coordination_model: str
    consistency_model: str
    atomicity: str
    blocking_behavior: str
    recovery_story: str
    participant_story: str
    interview_hook: str
    tradeoffs: list[str]


@dataclass
class ComparisonResult:
    title: str
    description: str
    transaction_id: str
    scenario_snapshot: dict[str, Any]
    comparisons: list[ProtocolComparison]
    interview_takeaways: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TerminationResolutionStep:
    participant: str
    role: str
    initial_state: str
    peer_query: str
    evidence: str
    final_state: str
    resolved: bool


@dataclass
class TerminationResolutionResult:
    title: str
    description: str
    transaction_id: str
    baseline_outcome: str
    baseline_decision: str | None
    baseline_termination_hint_summary: str | None
    resolution_outcome: str
    resolved_decision: str | None
    unresolved_participants: list[str]
    participants: list[TerminationResolutionStep]
    trace: list[str]
    takeaways: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_scenario(path: str | Path) -> Scenario:
    raw = json.loads(Path(path).read_text())
    return validate_scenario(raw)


def validate_scenario(raw: dict[str, Any]) -> Scenario:
    if not isinstance(raw, dict):
        raise ScenarioError("scenario must be a JSON object")

    title = _required_string(raw, "title")
    description = _required_string(raw, "description")
    transaction_id = _required_string(raw, "transaction_id")

    participants_raw = raw.get("participants")
    if not isinstance(participants_raw, list) or not participants_raw:
        raise ScenarioError("participants must be a non-empty list")

    participants: list[ParticipantPlan] = []
    seen_names: set[str] = set()
    commit_voter_count = 0
    for index, entry in enumerate(participants_raw, start=1):
        if not isinstance(entry, dict):
            raise ScenarioError(f"participant #{index} must be an object")
        name = _required_string(entry, "name")
        if name in seen_names:
            raise ScenarioError(f"duplicate participant name: {name}")
        seen_names.add(name)

        vote = _required_string(entry, "vote")
        if vote not in VALID_VOTES:
            raise ScenarioError(
                f"participant {name} vote must be one of {sorted(VALID_VOTES)}"
            )
        if vote == "commit":
            commit_voter_count += 1
        role = entry.get("role", "participant")
        if not isinstance(role, str) or not role.strip():
            raise ScenarioError(f"participant {name} role must be a non-empty string")
        notes = entry.get("notes", "")
        if not isinstance(notes, str):
            raise ScenarioError(f"participant {name} notes must be a string")
        second_phase_delivery = entry.get("second_phase_delivery", "deliver")
        if second_phase_delivery not in VALID_SECOND_PHASE_DELIVERIES:
            raise ScenarioError(
                f"participant {name} second_phase_delivery must be one of {sorted(VALID_SECOND_PHASE_DELIVERIES)}"
            )
        if second_phase_delivery == "miss" and vote != "commit":
            raise ScenarioError(
                f"participant {name} second_phase_delivery='miss' only makes sense for vote='commit'"
            )
        reconnect_after_missed_decision = entry.get(
            "reconnect_after_missed_decision",
            False,
        )
        if not isinstance(reconnect_after_missed_decision, bool):
            raise ScenarioError(
                f"participant {name} reconnect_after_missed_decision must be a boolean"
            )
        if second_phase_delivery != "miss" and reconnect_after_missed_decision:
            raise ScenarioError(
                f"participant {name} reconnect_after_missed_decision only makes sense when second_phase_delivery is 'miss'"
            )
        participants.append(
            ParticipantPlan(
                name=name,
                vote=vote,
                role=role.strip(),
                notes=notes.strip(),
                second_phase_delivery=second_phase_delivery,
                reconnect_after_missed_decision=reconnect_after_missed_decision,
            )
        )

    failures_raw = raw.get("failures", {})
    if failures_raw is None:
        failures_raw = {}
    if not isinstance(failures_raw, dict):
        raise ScenarioError("failures must be an object when provided")
    coordinator_crash = failures_raw.get("coordinator_crash", "none")
    if coordinator_crash not in VALID_CRASH_POINTS:
        raise ScenarioError(
            f"coordinator_crash must be one of {sorted(VALID_CRASH_POINTS)}"
        )
    recover_after_crash = failures_raw.get("recover_after_crash", False)
    if not isinstance(recover_after_crash, bool):
        raise ScenarioError("recover_after_crash must be a boolean")
    if coordinator_crash == "none" and recover_after_crash:
        raise ScenarioError("recover_after_crash only makes sense when a crash point exists")
    decision_deliveries_before_crash = failures_raw.get(
        "decision_deliveries_before_crash",
        0,
    )
    if not isinstance(decision_deliveries_before_crash, int):
        raise ScenarioError("decision_deliveries_before_crash must be an integer")
    if decision_deliveries_before_crash < 0:
        raise ScenarioError("decision_deliveries_before_crash must be >= 0")
    if (
        coordinator_crash != "after-decision-log"
        and decision_deliveries_before_crash
    ):
        raise ScenarioError(
            "decision_deliveries_before_crash only makes sense when coordinator_crash is 'after-decision-log'"
        )
    if decision_deliveries_before_crash > commit_voter_count:
        raise ScenarioError(
            "decision_deliveries_before_crash cannot exceed the number of commit-voting participants"
        )

    return Scenario(
        title=title,
        description=description,
        transaction_id=transaction_id,
        participants=participants,
        failures=FailurePlan(
            coordinator_crash=coordinator_crash,
            recover_after_crash=recover_after_crash,
            decision_deliveries_before_crash=decision_deliveries_before_crash,
        ),
    )


def simulate_two_phase_commit(scenario: Scenario) -> SimulationResult:
    participants = [ParticipantRuntime(plan=plan) for plan in scenario.participants]
    coordinator = CoordinatorRuntime()
    trace: list[str] = []

    def log(message: str) -> None:
        trace.append(message)

    def finish_prepared_participant(
        participant: ParticipantRuntime,
        *,
        via_reconnect: bool = False,
    ) -> None:
        assert coordinator.decision is not None
        participant.acked_decision = True
        if via_reconnect:
            participant.recovered_after_reconnect = True
        if coordinator.decision == "commit":
            participant.state = "committed"
            if via_reconnect:
                log(
                    f"{participant.plan.name}: reconnects, learns the durable COMMIT decision, commits local work, and acknowledges COMMIT"
                )
            else:
                log(f"{participant.plan.name}: commits local work and acknowledges COMMIT")
        else:
            participant.state = "aborted"
            if via_reconnect:
                log(
                    f"{participant.plan.name}: reconnects, learns the durable ABORT decision, rolls back prepared work, and acknowledges ABORT"
                )
            else:
                log(f"{participant.plan.name}: rolls back prepared work and acknowledges ABORT")

    def deliver_decision_to_prepared_participant(
        participant: ParticipantRuntime,
        *,
        allow_reconnect: bool,
    ) -> bool:
        assert coordinator.decision is not None
        log(f"coordinator -> {participant.plan.name}: {coordinator.decision.upper()}")
        if (
            participant.plan.second_phase_delivery == "miss"
            and not participant.missed_second_phase_delivery
        ):
            participant.missed_second_phase_delivery = True
            participant.state = "prepared-awaiting-decision"
            log(
                f"{participant.plan.name}: misses the first {coordinator.decision.upper()} delivery while disconnected and stays PREPARED"
            )
            if allow_reconnect and participant.plan.reconnect_after_missed_decision:
                log(
                    f"{participant.plan.name}: times out in PREPARED, reconnects, and asks the coordinator to replay the durable decision"
                )
                finish_prepared_participant(participant, via_reconnect=True)
                return True
            if allow_reconnect:
                log(
                    f"{participant.plan.name}: remains in doubt until a coordinator retry, recovery, or peer hint reveals the final decision"
                )
            return False

        finish_prepared_participant(participant)
        return True

    def deliver_before_crash(max_successful_deliveries: int) -> int:
        if max_successful_deliveries <= 0:
            return 0
        successful_deliveries = 0
        for participant in participants:
            if not participant.prepared or participant.acked_decision:
                continue
            if successful_deliveries >= max_successful_deliveries:
                break
            if deliver_decision_to_prepared_participant(
                participant,
                allow_reconnect=False,
            ):
                successful_deliveries += 1
        return successful_deliveries

    log(
        f"coordinator starts 2PC for {scenario.transaction_id} with {len(participants)} participants"
    )

    any_abort = False
    any_timeout = False
    for participant in participants:
        log(f"coordinator -> {participant.plan.name}: PREPARE")
        if participant.plan.vote == "commit":
            participant.prepared = True
            participant.state = "prepared"
            log(f"{participant.plan.name}: writes PREPARED record and replies YES")
        elif participant.plan.vote == "abort":
            participant.state = "aborted"
            any_abort = True
            log(f"{participant.plan.name}: replies NO and requests global abort")
        else:
            participant.state = "timed_out"
            any_timeout = True
            log(f"{participant.plan.name}: does not reply before timeout window")

    wants_commit = not any_abort and not any_timeout
    crash_point = scenario.failures.coordinator_crash
    recover = scenario.failures.recover_after_crash
    blocking_reason: str | None = None
    successful_decision_deliveries_before_crash = 0

    if wants_commit and crash_point == "before-decision":
        coordinator.state = "crashed-before-decision"
        log("coordinator crashes after collecting YES votes but before writing a durable decision")
        if recover:
            coordinator.state = "recovered"
            coordinator.decision = "abort"
            coordinator.decision_durable = True
            log("recovery finds no durable COMMIT/ABORT record, so the safe outcome is ABORT")
        else:
            blocking_reason = (
                "all participants are prepared, but the coordinator crashed before a durable "
                "decision was recorded; prepared participants remain blocked awaiting recovery"
            )
            log("participants remain blocked in PREPARED because no coordinator decision is available")
            return _build_result(
                scenario,
                outcome="blocked",
                decision=None,
                decision_durable=False,
                blocking_reason=blocking_reason,
                participants=participants,
                coordinator=coordinator,
                trace=trace,
                successful_decision_deliveries_before_crash=successful_decision_deliveries_before_crash,
            )
    elif wants_commit:
        coordinator.decision = "commit"
        coordinator.decision_durable = True
        log("coordinator writes COMMIT decision to durable log")
    else:
        coordinator.decision = "abort"
        coordinator.decision_durable = True
        if any_abort:
            log("coordinator writes ABORT decision because at least one participant voted NO")
        else:
            log("coordinator writes ABORT decision because at least one participant timed out")

    if crash_point == "after-decision-log":
        successful_decision_deliveries_before_crash = deliver_before_crash(
            scenario.failures.decision_deliveries_before_crash
        )
        if successful_decision_deliveries_before_crash:
            log(
                f"coordinator reaches {successful_decision_deliveries_before_crash} participant(s) with the durable {coordinator.decision.upper()} decision before crashing"
            )
        coordinator.state = "crashed-after-decision"
        log("coordinator crashes after the durable decision is logged but before all participants hear it")
        if recover:
            coordinator.state = "recovered"
            log("recovery replays the durable decision log and resumes decision broadcast")
        else:
            unresolved_participants = [
                participant
                for participant in participants
                if participant.prepared and not participant.acked_decision
            ]
            if unresolved_participants:
                blocking_reason = _build_after_decision_blocking_reason(
                    participants,
                    coordinator.decision,
                )
                log(
                    "some prepared participants still lack the final decision and remain blocked until coordinator recovery or a termination-protocol exchange"
                )
                return _build_result(
                    scenario,
                    outcome="blocked",
                    decision=coordinator.decision,
                    decision_durable=True,
                    blocking_reason=blocking_reason,
                    participants=participants,
                    coordinator=coordinator,
                    trace=trace,
                    successful_decision_deliveries_before_crash=successful_decision_deliveries_before_crash,
                )
            log("every prepared participant heard the durable decision before the coordinator crashed")

    assert coordinator.decision is not None
    for participant in participants:
        if participant.acked_decision:
            log(
                f"{participant.plan.name}: already knows {coordinator.decision.upper()} from an earlier delivery"
            )
            continue
        if participant.prepared:
            deliver_decision_to_prepared_participant(
                participant,
                allow_reconnect=True,
            )
        elif participant.state == "timed_out":
            log(f"{participant.plan.name}: was unavailable during voting and never prepared local work")
        elif coordinator.decision == "commit":
            log(f"{participant.plan.name}: had already refused the transaction before COMMIT was possible")
        else:
            log(f"{participant.plan.name}: is already safely aborted")

    coordinator.state = "complete"
    log(f"transaction resolves as {coordinator.decision.upper()}")
    return _build_result(
        scenario,
        outcome=coordinator.decision,
        decision=coordinator.decision,
        decision_durable=coordinator.decision_durable,
        blocking_reason=None,
        participants=participants,
        coordinator=coordinator,
        trace=trace,
        successful_decision_deliveries_before_crash=successful_decision_deliveries_before_crash,
    )


def build_protocol_comparison(scenario: Scenario) -> ComparisonResult:
    two_phase_result = simulate_two_phase_commit(scenario)
    snapshot = _build_scenario_snapshot(scenario, two_phase_result)
    comparisons = [
        _build_two_phase_protocol_comparison(two_phase_result),
        _build_saga_protocol_comparison(scenario, snapshot),
    ]
    interview_takeaways = _build_comparison_takeaways(snapshot, two_phase_result)
    return ComparisonResult(
        title=scenario.title,
        description=scenario.description,
        transaction_id=scenario.transaction_id,
        scenario_snapshot=snapshot,
        comparisons=comparisons,
        interview_takeaways=interview_takeaways,
    )


def build_peer_termination_resolution(scenario: Scenario) -> TerminationResolutionResult:
    baseline = simulate_two_phase_commit(scenario)
    informed_peers = [item["name"] for item in baseline.participants if item["acked_decision"]]
    non_prepared_peers = [
        item["name"]
        for item in baseline.participants
        if not item["prepared"] and item["state"] in {"aborted", "timed_out"}
    ]
    resolution_steps: list[TerminationResolutionStep] = []
    trace: list[str] = []
    unresolved_participants: list[str] = []

    if baseline.outcome != "blocked":
        trace.append(
            "baseline run already reached a final outcome, so peer-to-peer termination is unnecessary in this scenario"
        )
        for participant in baseline.participants:
            resolution_steps.append(
                TerminationResolutionStep(
                    participant=participant["name"],
                    role=participant["role"],
                    initial_state=participant["state"],
                    peer_query="not needed",
                    evidence="the coordinator already finished the transaction",
                    final_state=participant["state"],
                    resolved=True,
                )
            )
        return TerminationResolutionResult(
            title=baseline.title,
            description=baseline.description,
            transaction_id=baseline.transaction_id,
            baseline_outcome=baseline.outcome,
            baseline_decision=baseline.decision,
            baseline_termination_hint_summary=baseline.termination_hint_summary,
            resolution_outcome=baseline.outcome,
            resolved_decision=baseline.decision,
            unresolved_participants=[],
            participants=resolution_steps,
            trace=trace,
            takeaways=[
                "Peer-to-peer termination matters only when plain 2PC leaves a participant in doubt after PREPARED.",
                f"This scenario already completed as `{baseline.outcome}`, so there is no extra peer-resolution step to perform.",
            ],
        )

    for participant in baseline.participants:
        if participant["prepared"] and not participant["acked_decision"]:
            if informed_peers and baseline.decision is not None:
                final_state = "committed" if baseline.decision == "commit" else "aborted"
                evidence = (
                    f"{_format_name_list(informed_peers)} already {_verb_for_count(len(informed_peers), 'knows', 'know')} the durable {baseline.decision.upper()} decision"
                )
                peer_query = f"ask {_format_name_list(informed_peers)} for the final decision"
                trace.append(
                    f"{participant['name']}: asks {_format_name_list(informed_peers)} about the missing outcome, learns {baseline.decision.upper()}, and finishes as {final_state.upper()}"
                )
                resolution_steps.append(
                    TerminationResolutionStep(
                        participant=participant["name"],
                        role=participant["role"],
                        initial_state=participant["state"],
                        peer_query=peer_query,
                        evidence=evidence,
                        final_state=final_state,
                        resolved=True,
                    )
                )
                continue

            if non_prepared_peers:
                evidence = (
                    f"{_format_name_list(non_prepared_peers)} {_verb_for_count(len(non_prepared_peers), 'never prepared', 'never prepared')} local work, so ABORT is the only safe outcome"
                )
                peer_query = f"ask {_format_name_list(non_prepared_peers)} whether anyone never reached PREPARED"
                trace.append(
                    f"{participant['name']}: asks {_format_name_list(non_prepared_peers)} about PREPARED state, proves ABORT safely, and rolls back local work"
                )
                resolution_steps.append(
                    TerminationResolutionStep(
                        participant=participant["name"],
                        role=participant["role"],
                        initial_state=participant["state"],
                        peer_query=peer_query,
                        evidence=evidence,
                        final_state="aborted",
                        resolved=True,
                    )
                )
                continue

            unresolved_participants.append(participant["name"])
            evidence = "every reachable peer is still PREPARED/in doubt, so no safe local conclusion exists yet"
            peer_query = "ask peers whether anyone knows the final decision or never reached PREPARED"
            trace.append(
                f"{participant['name']}: asks peers for the final outcome, but everyone reachable is still uncertain, so the participant stays PREPARED"
            )
            resolution_steps.append(
                TerminationResolutionStep(
                    participant=participant["name"],
                    role=participant["role"],
                    initial_state=participant["state"],
                    peer_query=peer_query,
                    evidence=evidence,
                    final_state=participant["state"],
                    resolved=False,
                )
            )
            continue

        if participant["acked_decision"] and baseline.decision is not None:
            evidence = f"already knows the durable {baseline.decision.upper()} decision"
            peer_query = "answer peer termination requests"
        elif not participant["prepared"]:
            evidence = "never reached PREPARED, so this peer can help prove ABORT"
            peer_query = "answer whether local work ever reached PREPARED"
        else:
            evidence = "already final"
            peer_query = "not needed"
        resolution_steps.append(
            TerminationResolutionStep(
                participant=participant["name"],
                role=participant["role"],
                initial_state=participant["state"],
                peer_query=peer_query,
                evidence=evidence,
                final_state=participant["state"],
                resolved=True,
            )
        )

    resolved_decision: str | None = None
    resolution_outcome = "still-blocked"
    if not unresolved_participants:
        resolved_decision = baseline.decision or ("abort" if non_prepared_peers else None)
        resolution_outcome = resolved_decision or "still-blocked"

    takeaways = [
        "Classic 2PC remains blocking until a PREPARED participant either reaches the coordinator or learns an authoritative fact from a peer.",
    ]
    if resolution_outcome in {"commit", "abort"}:
        takeaways.append(
            f"This scenario's peer-to-peer termination exchange resolves the blocked participants to `{resolution_outcome}` without inventing a brand-new outcome locally."
        )
    else:
        takeaways.append(
            "The peer check still cannot finish the protocol here because every reachable peer is just as uncertain as the blocked participant."
        )
    if informed_peers and baseline.decision is not None:
        takeaways.append(
            f"Once {_format_name_list(informed_peers)} already knows `{baseline.decision.upper()}`, that peer can act as the decisive witness for the remaining PREPARED participants."
        )
    elif non_prepared_peers:
        takeaways.append(
            f"Seeing that {_format_name_list(non_prepared_peers)} never reached PREPARED is enough to conclude `ABORT` safely."
        )
    else:
        takeaways.append(
            "When no peer knows COMMIT/ABORT and no peer can prove a missing PREPARED record, plain 2PC stays blocked until coordinator recovery."
        )

    return TerminationResolutionResult(
        title=baseline.title,
        description=baseline.description,
        transaction_id=baseline.transaction_id,
        baseline_outcome=baseline.outcome,
        baseline_decision=baseline.decision,
        baseline_termination_hint_summary=baseline.termination_hint_summary,
        resolution_outcome=resolution_outcome,
        resolved_decision=resolved_decision,
        unresolved_participants=unresolved_participants,
        participants=resolution_steps,
        trace=trace,
        takeaways=takeaways,
    )


def render_markdown_report(result: SimulationResult) -> str:
    participant_lines = [
        "| Participant | Role | Planned vote | 2nd-phase delivery | Final state | Acked decision | Recovered after reconnect | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for participant in result.participants:
        participant_lines.append(
            "| {name} | {role} | {planned_vote} | {delivery} | {state} | {acked_decision} | {recovered} | {notes} |".format(
                name=participant["name"],
                role=participant["role"],
                planned_vote=participant["planned_vote"],
                delivery=participant["second_phase_delivery"],
                state=participant["state"],
                acked_decision="yes" if participant["acked_decision"] else "no",
                recovered="yes" if participant["recovered_after_reconnect"] else "no",
                notes=participant["notes"] or "-",
            )
        )

    trace_lines = [f"{index}. {entry}" for index, entry in enumerate(result.trace, start=1)]
    takeaway_lines = [f"- {entry}" for entry in result.takeaways]
    termination_lines = [f"- {entry}" for entry in result.termination_hints]

    lines = [
        f"# {result.title}",
        "",
        result.description,
        "",
        "## Outcome",
        f"- transaction id: `{result.transaction_id}`",
        f"- final outcome: `{result.outcome}`",
        f"- durable decision recorded: `{'yes' if result.decision_durable else 'no'}`",
        f"- coordinator crash point: `{result.failures['coordinator_crash']}`",
        f"- coordinator recovery simulated: `{'yes' if result.failures['recover_after_crash'] else 'no'}`",
        f"- configured decision deliveries before crash: `{result.failures['decision_deliveries_before_crash']}`",
        f"- successful decision deliveries before crash: `{result.failures['successful_decision_deliveries_before_crash']}`",
    ]
    if result.blocking_reason:
        lines.append(f"- blocking reason: {result.blocking_reason}")
    if result.termination_hint_summary:
        lines.append(f"- termination hint summary: {result.termination_hint_summary}")
    lines.extend(
        [
            "",
            "## Participant summary",
            *participant_lines,
        ]
    )
    if termination_lines:
        lines.extend(
            [
                "",
                "## Termination protocol hints",
                *termination_lines,
            ]
        )
    lines.extend(
        [
            "",
            "## Trace",
            *trace_lines,
            "",
            "## Takeaways",
            *takeaway_lines,
            "",
        ]
    )
    return "\n".join(lines)


def render_comparison_markdown(result: ComparisonResult) -> str:
    snapshot = result.scenario_snapshot
    comparison_lines = [
        "| Protocol | Outcome in this scenario | Consistency model | Atomicity | Blocking behavior | Recovery story |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    detail_lines: list[str] = []
    for comparison in result.comparisons:
        comparison_lines.append(
            "| {protocol} | `{outcome}` | {consistency} | {atomicity} | {blocking} | {recovery} |".format(
                protocol=comparison.protocol,
                outcome=comparison.outcome,
                consistency=comparison.consistency_model,
                atomicity=comparison.atomicity,
                blocking=comparison.blocking_behavior,
                recovery=comparison.recovery_story,
            )
        )
        detail_lines.extend(
            [
                f"### {comparison.protocol}",
                f"- coordination model: {comparison.coordination_model}",
                f"- participant story: {comparison.participant_story}",
                f"- interview hook: {comparison.interview_hook}",
                "- tradeoffs:",
                *[f"  - {entry}" for entry in comparison.tradeoffs],
                "",
            ]
        )

    missed_names = _format_name_list(snapshot["missed_second_phase_names"]) or "none"
    informed_names = _format_name_list(snapshot["acked_decision_participants"]) or "none yet"
    lines = [
        f"# {result.title} protocol comparison",
        "",
        result.description,
        "",
        "## Scenario snapshot",
        f"- transaction id: `{result.transaction_id}`",
        f"- participants: `{snapshot['participant_count']}` total (`{snapshot['commit_voters']}` commit, `{snapshot['abort_voters']}` abort, `{snapshot['timeout_voters']}` timeout)",
        f"- coordinator crash point: `{snapshot['coordinator_crash']}`",
        f"- coordinator recovery simulated: `{'yes' if snapshot['recover_after_crash'] else 'no'}`",
        f"- participant-configured missed second-phase deliveries: `{snapshot['missed_second_phase_participants']}` ({missed_names})",
        f"- participants that learned the final 2PC decision: `{snapshot['acked_decision_count']}` ({informed_names})",
        f"- 2PC baseline outcome: `{snapshot['two_phase_outcome']}`",
    ]
    if snapshot["coordinator_crash"] == "after-decision-log":
        lines.append(
            f"- successful second-phase deliveries before the crash: `{snapshot['successful_decision_deliveries_before_crash']}`"
        )
    if snapshot["termination_hint_summary"]:
        lines.append(
            f"- termination hint in the 2PC baseline: {snapshot['termination_hint_summary']}"
        )
    lines.extend(
        [
            "",
            "## Protocol contrast",
            *comparison_lines,
            "",
            "## Protocol notes",
            *detail_lines,
            "## Interview takeaways",
            *[f"- {entry}" for entry in result.interview_takeaways],
            "",
        ]
    )
    return "\n".join(lines)


def render_termination_resolution_markdown(result: TerminationResolutionResult) -> str:
    participant_lines = [
        "| Participant | Role | Initial state | Peer query | Evidence | Final state | Resolved |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for participant in result.participants:
        participant_lines.append(
            "| {participant} | {role} | {initial_state} | {peer_query} | {evidence} | {final_state} | {resolved} |".format(
                participant=participant.participant,
                role=participant.role,
                initial_state=participant.initial_state,
                peer_query=participant.peer_query,
                evidence=participant.evidence,
                final_state=participant.final_state,
                resolved="yes" if participant.resolved else "no",
            )
        )

    trace_lines = [f"{index}. {entry}" for index, entry in enumerate(result.trace, start=1)]
    unresolved = _format_name_list(result.unresolved_participants) or "none"
    takeaways = [f"- {entry}" for entry in result.takeaways]

    lines = [
        f"# {result.title} peer-to-peer termination resolution",
        "",
        result.description,
        "",
        "## Baseline 2PC state",
        f"- transaction id: `{result.transaction_id}`",
        f"- baseline outcome: `{result.baseline_outcome}`",
        f"- baseline decision: `{result.baseline_decision or 'none'}`",
        f"- baseline termination hint: {result.baseline_termination_hint_summary or '-'}",
        "",
        "## Peer-to-peer resolution result",
        f"- resolution outcome: `{result.resolution_outcome}`",
        f"- resolved decision: `{result.resolved_decision or 'none'}`",
        f"- unresolved participants after peer exchange: `{unresolved}`",
        "",
        "## Participant actions",
        *participant_lines,
        "",
        "## Resolution trace",
        *trace_lines,
        "",
        "## Takeaways",
        *takeaways,
        "",
    ]
    return "\n".join(lines)


def render_catalog_markdown(entries: list[CatalogEntry]) -> str:
    if not entries:
        raise ScenarioError("catalog requires at least one scenario")

    commit_count = sum(1 for entry in entries if entry.result.outcome == "commit")
    abort_count = sum(1 for entry in entries if entry.result.outcome == "abort")
    blocked_count = sum(1 for entry in entries if entry.result.outcome == "blocked")
    crash_count = sum(
        1
        for entry in entries
        if entry.result.failures["coordinator_crash"] != "none"
    )
    recovery_count = sum(
        1
        for entry in entries
        if entry.result.failures["recover_after_crash"]
    )
    reconnect_recovery_count = sum(
        1
        for entry in entries
        for participant in entry.result.participants
        if participant["recovered_after_reconnect"]
    )
    actionable_termination_hint_count = sum(
        1
        for entry in entries
        if entry.result.termination_hint_summary
        and not entry.result.termination_hint_summary.startswith("wait:")
    )

    comparison_lines = [
        "| Scenario | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Termination hint | Report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    snapshot_lines: list[str] = []
    for entry in entries:
        result = entry.result
        prepared_count = sum(1 for item in result.participants if item["prepared"])
        acked_count = sum(1 for item in result.participants if item["acked_decision"])
        recovered_count = sum(
            1 for item in result.participants if item["recovered_after_reconnect"]
        )
        missed_count = sum(
            1 for item in result.participants if item["missed_second_phase_delivery"]
        )
        title_cell = result.title
        report_cell = "-"
        if entry.report_path:
            title_cell = f"[{result.title}]({entry.report_path})"
            report_cell = f"[report]({entry.report_path})"
        reconnect_cell = f"`{recovered_count}/{missed_count}`" if missed_count else "`-`"
        termination_cell = result.termination_hint_summary or "-"
        comparison_lines.append(
            "| {title} | `{outcome}` | `{decision}` | `{durable}` | `{crash}` | `{recovery}` | `{prepared}/{total}` | `{acked}/{total}` | {reconnect} | {termination} | {report} |".format(
                title=title_cell,
                outcome=result.outcome,
                decision=result.decision or "none",
                durable="yes" if result.decision_durable else "no",
                crash=result.failures["coordinator_crash"],
                recovery="yes" if result.failures["recover_after_crash"] else "no",
                prepared=prepared_count,
                acked=acked_count,
                reconnect=reconnect_cell,
                termination=termination_cell,
                total=len(result.participants),
                report=report_cell,
            )
        )

        reconnect_snapshot = (
            f"`{recovered_count}/{missed_count}` recovered after missing the first second-phase delivery"
            if missed_count
            else "`-` (no participant missed the first second-phase delivery)"
        )
        snapshot_lines.extend(
            [
                f"### {result.title}",
                f"- source: `{entry.source_path}`",
                f"- description: {result.description}",
                f"- outcome: `{result.outcome}` with decision `{result.decision or 'none'}`",
                f"- participants prepared/acked: `{prepared_count}/{len(result.participants)}` prepared, `{acked_count}/{len(result.participants)}` acked",
                f"- participant reconnect recovery: {reconnect_snapshot}",
                f"- termination hint: {result.termination_hint_summary or '-'}",
                f"- why it matters: {_primary_takeaway(result)}",
            ]
        )
        if entry.report_path:
            snapshot_lines.append(f"- deep dive: [{entry.report_path}]({entry.report_path})")
        snapshot_lines.append("")

    lines = [
        "# Two-phase commit scenario catalog",
        "",
        "A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, recovery, and peer-assisted incident-response cases.",
        "",
        "## Bundle summary",
        f"- scenarios: `{len(entries)}`",
        f"- outcomes: `{commit_count} commit`, `{abort_count} abort`, `{blocked_count} blocked`",
        f"- crash cases: `{crash_count}`",
        f"- coordinator recovery cases: `{recovery_count}`",
        f"- participant reconnect recoveries: `{reconnect_recovery_count}`",
        f"- blocked scenarios with actionable peer hints: `{actionable_termination_hint_count}`",
        "",
        "## Scenario comparison",
        *comparison_lines,
        "",
        "## Interview talking points",
        "- plain 2PC is easy to explain because every scenario pivots on the coordinator's durable decision log.",
        "- blocking shows up when participants are already prepared but cannot prove the final outcome after a coordinator crash.",
        "- participant-side reconnects matter too: even with a durable decision, a prepared participant can stay in doubt until the coordinator retries or recovery answers the query.",
        "- when the coordinator is down, participants can still ask peers whether anyone already knows the durable decision or never reached PREPARED; otherwise the protocol remains blocked.",
        "- recovery is operationally different from blocking: once the decision is durable, replay can safely finish phase two.",
        "",
        "## Scenario snapshots",
        *snapshot_lines,
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(path: str | Path, result: SimulationResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(result))


def write_comparison_markdown(path: str | Path, result: ComparisonResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_comparison_markdown(result))


def write_termination_resolution_markdown(
    path: str | Path,
    result: TerminationResolutionResult,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_termination_resolution_markdown(result))


def write_catalog(path: str | Path, entries: list[CatalogEntry]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_catalog_markdown(entries))


def collect_scenario_paths(paths: list[Path]) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path.is_dir():
            candidates = sorted(candidate for candidate in path.iterdir() if candidate.suffix == ".json")
        elif path.is_file():
            candidates = [path]
        else:
            raise ScenarioError(f"path does not exist: {path}")

        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            collected.append(candidate)

    if not collected:
        joined = ", ".join(str(path) for path in paths)
        raise ScenarioError(f"no scenario JSON files found in: {joined}")
    return collected


def build_catalog_entries(
    scenario_paths: list[Path],
    *,
    catalog_path: Path,
    report_dir: Path | None = None,
) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    for scenario_path in scenario_paths:
        result = simulate_two_phase_commit(load_scenario(scenario_path))
        report_path: str | None = None
        if report_dir is not None:
            report_file = report_dir / f"{scenario_path.stem}_report.md"
            write_markdown_report(report_file, result)
            report_path = os.path.relpath(report_file, start=catalog_path.parent).replace(os.sep, "/")
        entries.append(
            CatalogEntry(
                source_path=str(scenario_path).replace(os.sep, "/"),
                report_path=report_path,
                result=result,
            )
        )
    return entries


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Two-phase commit teaching simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate a scenario file")
    validate_parser.add_argument("scenario", type=Path)

    run_parser = subparsers.add_parser("run", help="simulate a scenario")
    run_parser.add_argument("scenario", type=Path)
    run_parser.add_argument("--json", action="store_true", help="emit full JSON output")
    run_parser.add_argument(
        "--markdown-out",
        type=Path,
        help="optional path for a Markdown report artifact",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="contrast 2PC with a saga-style alternative for the same scenario",
    )
    compare_parser.add_argument("scenario", type=Path)
    compare_parser.add_argument("--json", action="store_true", help="emit full JSON output")
    compare_parser.add_argument(
        "--markdown-out",
        type=Path,
        help="optional path for a Markdown comparison artifact",
    )

    terminate_parser = subparsers.add_parser(
        "terminate",
        help="simulate a participant-to-peer termination-protocol exchange after a blocked 2PC run",
    )
    terminate_parser.add_argument("scenario", type=Path)
    terminate_parser.add_argument("--json", action="store_true", help="emit full JSON output")
    terminate_parser.add_argument(
        "--markdown-out",
        type=Path,
        help="optional path for a Markdown peer-resolution artifact",
    )

    catalog_parser = subparsers.add_parser(
        "catalog",
        help="build a multi-scenario Markdown catalog and optional per-scenario reports",
    )
    catalog_parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="scenario JSON files or directories containing scenario JSON files",
    )
    catalog_parser.add_argument(
        "--markdown-out",
        type=Path,
        required=True,
        help="path for the catalog Markdown artifact",
    )
    catalog_parser.add_argument(
        "--report-dir",
        type=Path,
        help="optional directory for regenerated per-scenario Markdown reports",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        scenario = load_scenario(args.scenario)
        print(
            f"validated {scenario.title} ({len(scenario.participants)} participants, crash={scenario.failures.coordinator_crash})"
        )
        return 0

    if args.command == "run":
        result = simulate_two_phase_commit(load_scenario(args.scenario))
        if args.markdown_out:
            write_markdown_report(args.markdown_out, result)
            stream = sys.stderr if args.json else sys.stdout
            print(f"wrote Markdown report to {args.markdown_out}", file=stream)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"{result.title}: outcome={result.outcome} decision={result.decision or 'none'}")
            if result.blocking_reason:
                print(f"blocking_reason={result.blocking_reason}")
            if result.termination_hint_summary:
                print(f"termination_hint={result.termination_hint_summary}")
            print(f"participants={len(result.participants)} trace_events={len(result.trace)}")
        return 0

    if args.command == "compare":
        result = build_protocol_comparison(load_scenario(args.scenario))
        if args.markdown_out:
            write_comparison_markdown(args.markdown_out, result)
            stream = sys.stderr if args.json else sys.stdout
            print(f"wrote Markdown comparison to {args.markdown_out}", file=stream)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"{result.title}: compared {len(result.comparisons)} protocols")
            for comparison in result.comparisons:
                print(
                    f"{comparison.protocol}: outcome={comparison.outcome} blocking={comparison.blocking_behavior}"
                )
        return 0

    if args.command == "terminate":
        result = build_peer_termination_resolution(load_scenario(args.scenario))
        if args.markdown_out:
            write_termination_resolution_markdown(args.markdown_out, result)
            stream = sys.stderr if args.json else sys.stdout
            print(f"wrote Markdown peer-resolution artifact to {args.markdown_out}", file=stream)
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(
                f"{result.title}: baseline={result.baseline_outcome} peer_resolution={result.resolution_outcome}"
            )
            if result.resolved_decision:
                print(f"resolved_decision={result.resolved_decision}")
            if result.unresolved_participants:
                print(
                    "unresolved_participants="
                    + ",".join(result.unresolved_participants)
                )
        return 0

    if args.command == "catalog":
        scenario_paths = collect_scenario_paths(args.paths)
        entries = build_catalog_entries(
            scenario_paths,
            catalog_path=args.markdown_out,
            report_dir=args.report_dir,
        )
        write_catalog(args.markdown_out, entries)
        if args.report_dir:
            print(f"wrote {len(entries)} scenario reports to {args.report_dir}")
        print(f"wrote catalog to {args.markdown_out}")
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


def _build_result(
    scenario: Scenario,
    *,
    outcome: str,
    decision: str | None,
    decision_durable: bool,
    blocking_reason: str | None,
    participants: list[ParticipantRuntime],
    coordinator: CoordinatorRuntime,
    trace: list[str],
    successful_decision_deliveries_before_crash: int,
) -> SimulationResult:
    participant_rows = [
        {
            "name": participant.plan.name,
            "role": participant.plan.role,
            "planned_vote": participant.plan.vote,
            "second_phase_delivery": participant.plan.second_phase_delivery,
            "reconnect_after_missed_decision": participant.plan.reconnect_after_missed_decision,
            "state": participant.state,
            "prepared": participant.prepared,
            "acked_decision": participant.acked_decision,
            "missed_second_phase_delivery": participant.missed_second_phase_delivery,
            "recovered_after_reconnect": participant.recovered_after_reconnect,
            "notes": participant.plan.notes,
        }
        for participant in participants
    ]
    takeaways = _build_takeaways(
        outcome=outcome,
        decision=decision,
        blocking_reason=blocking_reason,
        participants=participant_rows,
        coordinator=coordinator,
    )
    termination_hint_summary, termination_hints = _build_termination_guidance(
        blocking_reason=blocking_reason,
        decision=decision,
        participants=participant_rows,
    )
    return SimulationResult(
        title=scenario.title,
        description=scenario.description,
        transaction_id=scenario.transaction_id,
        outcome=outcome,
        decision=decision,
        decision_durable=decision_durable,
        blocking_reason=blocking_reason,
        failures={
            "coordinator_crash": scenario.failures.coordinator_crash,
            "recover_after_crash": scenario.failures.recover_after_crash,
            "decision_deliveries_before_crash": scenario.failures.decision_deliveries_before_crash,
            "successful_decision_deliveries_before_crash": successful_decision_deliveries_before_crash,
        },
        participants=participant_rows,
        trace=trace,
        takeaways=takeaways,
        termination_hint_summary=termination_hint_summary,
        termination_hints=termination_hints,
    )


def _build_takeaways(
    *,
    outcome: str,
    decision: str | None,
    blocking_reason: str | None,
    participants: list[dict[str, Any]],
    coordinator: CoordinatorRuntime,
) -> list[str]:
    yes_count = sum(1 for item in participants if item["planned_vote"] == "commit")
    abort_count = sum(1 for item in participants if item["planned_vote"] == "abort")
    timeout_count = sum(1 for item in participants if item["planned_vote"] == "timeout")
    prepared_count = sum(1 for item in participants if item["prepared"])
    missed_count = sum(1 for item in participants if item["missed_second_phase_delivery"])
    recovered_count = sum(1 for item in participants if item["recovered_after_reconnect"])
    acked_count = sum(1 for item in participants if item["acked_decision"])
    lines = [
        f"{_count_phrase(yes_count, 'participant')} were willing to commit, {abort_count} voted abort, and {timeout_count} timed out.",
        f"{_count_phrase(prepared_count, 'participant')} reached PREPARED before the transaction finished.",
    ]
    if missed_count:
        lines.append(
            f"{_count_phrase(missed_count, 'participant')} missed the first second-phase delivery, and {_count_phrase(recovered_count, 'participant')} later recovered by reconnecting for the durable decision."
        )
    if blocking_reason:
        if decision is not None:
            lines.append(
                f"{_count_phrase(acked_count, 'participant')} already {_verb_for_count(acked_count, 'knows', 'know')} the durable {decision.upper()} while other prepared peers remain blocked."
            )
        lines.append(blocking_reason)
    elif decision == "commit":
        lines.append(
            "2PC commits only because every participant voted YES and the coordinator recorded a durable COMMIT decision."
        )
    else:
        lines.append(
            "2PC aborts whenever a participant refuses, times out, or recovery cannot prove a durable COMMIT record."
        )
    lines.append(f"Final coordinator state: {coordinator.state}.")
    return lines


def _build_termination_guidance(
    *,
    blocking_reason: str | None,
    decision: str | None,
    participants: list[dict[str, Any]],
) -> tuple[str | None, list[str]]:
    if not blocking_reason:
        return None, []

    informed_peers = [item["name"] for item in participants if item["acked_decision"]]
    uncertain_peers = [
        item["name"]
        for item in participants
        if item["prepared"] and not item["acked_decision"]
    ]
    non_prepared_peers = [
        item["name"]
        for item in participants
        if not item["prepared"] and item["state"] in {"aborted", "timed_out"}
    ]

    if informed_peers and decision is not None:
        informed_names = _format_name_list(informed_peers)
        uncertain_names = _format_name_list(uncertain_peers) or "the remaining prepared peers"
        summary = f"{decision.upper()} visible via {informed_names}"
        hints = [
            f"Ask reachable peers whether anyone already knows the final decision. Here, {informed_names} {_verb_for_count(len(informed_peers), 'already knows', 'already know')} `{decision.upper()}` and can relay it to {uncertain_names}.",
            "Treat the peer answer as evidence of the coordinator's durable outcome, not permission to invent a brand-new one locally.",
            "If no informed peer is reachable, the unresolved participants still need coordinator recovery or another authoritative replay.",
        ]
        return summary, hints

    if non_prepared_peers:
        peer_names = _format_name_list(non_prepared_peers)
        summary = f"ABORT safe via {peer_names}"
        hints = [
            f"Ask whether any peer never reached PREPARED. Here, {peer_names} {_verb_for_count(len(non_prepared_peers), 'never prepared', 'never prepared')} local work, so the classic termination protocol can safely conclude `ABORT`.",
            "This is the normal escape hatch when a participant can prove the transaction never reached unanimous PREPARED state.",
            "If every reachable peer is instead still PREPARED/in doubt, the block remains.",
        ]
        return summary, hints

    uncertain_names = _format_name_list(uncertain_peers) or "every reachable peer"
    if decision is not None:
        summary = f"wait: durable {decision.upper()} exists but no peer can prove it yet"
        hints = [
            "Ask reachable peers whether anyone already heard the final decision from the coordinator.",
            f"In this run, {uncertain_names} {_verb_for_count(len(uncertain_peers), 'is', 'are')} still PREPARED/in doubt, so no peer can yet prove `{decision.upper()}`.",
            "Keep waiting for coordinator recovery or an authoritative retry; do not invent a local outcome.",
        ]
        return summary, hints

    summary = "wait: all prepared peers are still uncertain"
    hints = [
        "Ask reachable peers whether anyone already knows COMMIT/ABORT or never reached PREPARED.",
        f"In this run, {uncertain_names} {_verb_for_count(len(uncertain_peers), 'is', 'are')} still PREPARED/in doubt, so the classic termination protocol cannot finish safely yet.",
        "Keep waiting for coordinator recovery; plain 2PC stays blocked when every reachable participant is uncertain.",
    ]
    return summary, hints


def _build_after_decision_blocking_reason(
    participants: list[ParticipantRuntime],
    decision: str | None,
) -> str:
    assert decision is not None
    informed_names = [participant.plan.name for participant in participants if participant.acked_decision]
    unresolved_names = [
        participant.plan.name
        for participant in participants
        if participant.prepared and not participant.acked_decision
    ]
    if informed_names:
        return (
            f"the durable {decision.upper()} decision exists and {_format_name_list(informed_names)} "
            f"{_verb_for_count(len(informed_names), 'already knows', 'already know')} it, but "
            f"{_format_name_list(unresolved_names)} remain in doubt until coordinator recovery or a peer-to-peer termination check"
        )
    return (
        f"the durable {decision.upper()} decision exists, but no prepared participant has learned it yet; "
        "prepared participants stay in doubt until recovery or a termination-protocol exchange"
    )


def _build_scenario_snapshot(
    scenario: Scenario,
    two_phase_result: SimulationResult,
) -> dict[str, Any]:
    commit_names = [plan.name for plan in scenario.participants if plan.vote == "commit"]
    abort_names = [plan.name for plan in scenario.participants if plan.vote == "abort"]
    timeout_names = [plan.name for plan in scenario.participants if plan.vote == "timeout"]
    missed_names = [
        plan.name
        for plan in scenario.participants
        if plan.second_phase_delivery == "miss"
    ]
    prepared_names = [
        item["name"] for item in two_phase_result.participants if item["prepared"]
    ]
    acked_names = [
        item["name"] for item in two_phase_result.participants if item["acked_decision"]
    ]
    return {
        "participant_count": len(scenario.participants),
        "commit_voters": len(commit_names),
        "commit_participants": commit_names,
        "abort_voters": len(abort_names),
        "abort_participants": abort_names,
        "timeout_voters": len(timeout_names),
        "timeout_participants": timeout_names,
        "prepared_participants": prepared_names,
        "missed_second_phase_participants": len(missed_names),
        "missed_second_phase_names": missed_names,
        "acked_decision_count": len(acked_names),
        "acked_decision_participants": acked_names,
        "coordinator_crash": scenario.failures.coordinator_crash,
        "recover_after_crash": scenario.failures.recover_after_crash,
        "decision_deliveries_before_crash": scenario.failures.decision_deliveries_before_crash,
        "successful_decision_deliveries_before_crash": two_phase_result.failures["successful_decision_deliveries_before_crash"],
        "two_phase_outcome": two_phase_result.outcome,
        "two_phase_decision": two_phase_result.decision,
        "termination_hint_summary": two_phase_result.termination_hint_summary,
    }


def _build_two_phase_protocol_comparison(result: SimulationResult) -> ProtocolComparison:
    prepared_count = sum(1 for item in result.participants if item["prepared"])
    acked_count = sum(1 for item in result.participants if item["acked_decision"])
    if result.outcome == "blocked":
        blocking_behavior = "blocking once PREPARED participants cannot prove the coordinator's final decision"
        recovery_story = (
            "needs coordinator recovery or a safe termination-protocol answer from an authoritative peer"
        )
        interview_hook = "2PC buys atomic all-or-nothing semantics, but the price is visible coordinator-centered blocking in outage scenarios."
    elif result.outcome == "commit":
        blocking_behavior = "not blocked in this run, but PREPARED participants would wait if the coordinator failed mid-decision"
        recovery_story = "durable decision logging lets the coordinator replay COMMIT and finish phase two after a restart"
        interview_hook = "2PC's happy path is easy to reason about because one durable COMMIT record drives every participant to the same final state."
    else:
        blocking_behavior = "not blocked in this run because a NO vote or timeout forced a global ABORT before commit"
        recovery_story = "ABORT is broadcast from the coordinator; participants roll back PREPARED work instead of compensating later"
        interview_hook = "2PC gives a crisp all-or-nothing ABORT story, but it still depends on a central coordinator to publish the decision."

    return ProtocolComparison(
        protocol="2PC",
        outcome=result.outcome,
        coordination_model="single coordinator with PREPARE and COMMIT/ABORT phases over durable decision logging",
        consistency_model="strong atomic commit when the decision completes; every participant follows the same global outcome",
        atomicity="global all-or-nothing across participants once the coordinator's durable decision is known",
        blocking_behavior=blocking_behavior,
        recovery_story=recovery_story,
        participant_story=(
            f"{prepared_count}/{len(result.participants)} participants reached PREPARED and {acked_count}/{len(result.participants)} learned the final decision in this run"
        ),
        interview_hook=interview_hook,
        tradeoffs=[
            "easy to explain when interviewers ask how a durable decision log enforces atomic commit",
            "participants may hold PREPARED state while waiting on the coordinator or an authoritative replay",
            "fits tightly coupled all-or-nothing workflows better than high-availability microservice traffic",
        ],
    )


def _build_saga_protocol_comparison(
    scenario: Scenario,
    snapshot: dict[str, Any],
) -> ProtocolComparison:
    abort_names = snapshot["abort_participants"]
    timeout_names = snapshot["timeout_participants"]
    crash_point = scenario.failures.coordinator_crash
    recover = scenario.failures.recover_after_crash

    if abort_names or timeout_names:
        blocked_names = abort_names + timeout_names
        outcome = "compensated-abort"
        recovery_story = "earlier local steps compensate in reverse order; retry the failing step later if the business flow should continue"
        participant_story = (
            f"participants before {_format_name_list(blocked_names)} may need compensating transactions, but no peer waits in PREPARED limbo"
        )
        interview_hook = "Saga keeps services available on failure, but you trade a single crisp ABORT decision for compensation design and temporary inconsistency."
    elif crash_point != "none" and not recover:
        outcome = "paused-not-blocked"
        recovery_story = "resume from the last durable saga step or compensate the already-finished steps; no global prepare barrier needs to be unblocked"
        participant_story = (
            "already-finished local transactions stay committed, unfinished steps pause for orchestrator recovery or operator action, and peers continue serving other work"
        )
        interview_hook = "A saga can still stall operationally, but it stalls as resumable workflow state instead of coordinator-driven prepared-lock blocking."
    elif crash_point != "none" and recover:
        outcome = "resumed-eventual-commit"
        recovery_story = "a durable orchestration log or outbox can replay the next command and finish the remaining local transactions after restart"
        participant_story = (
            "completed local steps remain committed and the recovered orchestrator continues from the last durable checkpoint"
        )
        interview_hook = "Saga recovery is about replaying idempotent local steps or compensations, not re-running a global COMMIT decision across prepared peers."
    else:
        outcome = "eventual-commit"
        recovery_story = "no compensation is needed because every local transaction succeeds and the workflow reaches the terminal success state"
        participant_story = "each service commits its own local transaction in sequence; no participant enters PREPARED lock-wait state"
        interview_hook = "Saga trades strict cross-service atomicity for availability: local commits happen independently and the workflow converges through messaging/orchestration."

    return ProtocolComparison(
        protocol="Saga (orchestrated)",
        outcome=outcome,
        coordination_model="ordered local transactions plus compensating actions, typically driven by an orchestrator or event flow",
        consistency_model="eventual consistency across services, with explicit compensations when later steps fail",
        atomicity="no single global atomic commit; earlier local success is repaired by compensation instead of a shared PREPARE/COMMIT barrier",
        blocking_behavior="non-blocking for participant resources; the workflow can pause, but services do not sit on PREPARED locks waiting for a global decision",
        recovery_story=recovery_story,
        participant_story=participant_story,
        interview_hook=interview_hook,
        tradeoffs=[
            "fits database-per-service architectures because each step owns only its local database transaction",
            "developers must design idempotent retries and compensating actions instead of relying on automatic rollback",
            "availability is usually better than plain 2PC, but isolation is weaker and temporary anomalies are possible",
        ],
    )


def _build_comparison_takeaways(
    snapshot: dict[str, Any],
    two_phase_result: SimulationResult,
) -> list[str]:
    lines = [
        f"In this scenario, plain 2PC resolves as `{two_phase_result.outcome}`, which is driven by one coordinator-owned durable decision and the PREPARED states around it.",
        "An orchestrated saga would avoid PREPARED lock blocking by committing local work independently and using retries/compensations instead of a global commit barrier.",
    ]
    if two_phase_result.outcome == "blocked":
        lines.append(
            "Use this comparison to explain why high-availability microservice systems often choose sagas when temporary inconsistency is acceptable but indefinite coordinator blocking is not."
        )
    elif two_phase_result.outcome == "abort":
        lines.append(
            "This is a good interview story for contrasting immediate atomic ABORT in 2PC with compensation-based unwind logic in saga-style workflows."
        )
    else:
        lines.append(
            "Even on a clean commit path, the comparison shows the core trade-off: 2PC keeps stronger atomic semantics, while saga keeps participants looser and easier to recover operationally."
        )
    if snapshot["successful_decision_deliveries_before_crash"] and two_phase_result.decision:
        lines.append(
            f"Here, {_count_phrase(snapshot['successful_decision_deliveries_before_crash'], 'participant')} already heard the durable {two_phase_result.decision.upper()} before the crash, so the blocked 2PC case becomes a peer-assisted incident-response story rather than pure blind waiting."
        )
    if (
        snapshot["termination_hint_summary"]
        and not snapshot["termination_hint_summary"].startswith("wait:")
    ):
        lines.append(
            f"The simulator's termination hint (`{snapshot['termination_hint_summary']}`) makes that concrete: a prepared participant can ask an informed peer instead of inventing a local outcome."
        )
    if snapshot["coordinator_crash"] != "none":
        lines.append(
            f"The configured crash point (`{snapshot['coordinator_crash']}`) is the teaching lever here: it shows that the same business transaction can become either coordinator-blocked (2PC) or resumable/compensatable (saga)."
        )
    return lines


def _primary_takeaway(result: SimulationResult) -> str:
    if result.termination_hint_summary and not result.termination_hint_summary.startswith("wait:"):
        return f"blocked does not always mean blind waiting: {result.termination_hint_summary}."
    if result.blocking_reason:
        return result.blocking_reason
    for entry in result.takeaways:
        if "reconnecting for the durable decision" in entry:
            return entry
    for entry in result.takeaways:
        if entry.startswith("2PC "):
            return entry
    return result.takeaways[-1]


def _count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    if plural is None:
        plural = f"{singular}s"
    noun = singular if count == 1 else plural
    return f"{count} {noun}"


def _format_name_list(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])}, and {names[-1]}"


def _verb_for_count(count: int, singular: str, plural: str) -> str:
    return singular if count == 1 else plural


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioError(f"{key} must be a non-empty string")
    return value.strip()


if __name__ == "__main__":
    raise SystemExit(main())
