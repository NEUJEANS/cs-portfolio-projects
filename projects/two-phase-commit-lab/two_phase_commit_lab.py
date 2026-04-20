from __future__ import annotations

import argparse
import html
import json
import os
import sys
import textwrap
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
    comparison_markdown_path: str | None = None
    comparison_html_path: str | None = None
    termination_markdown_path: str | None = None
    termination_timeline_svg_path: str | None = None
    termination_timeline_html_path: str | None = None


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


def render_comparison_html(result: ComparisonResult) -> str:
    snapshot = result.scenario_snapshot
    saga_outcome = next(
        (comparison.outcome for comparison in result.comparisons if comparison.protocol.startswith('Saga')),
        'n/a',
    )
    if snapshot['acked_decision_participants']:
        acked_description = (
            f"{_format_name_list(snapshot['acked_decision_participants'])} "
            f"{_verb_for_count(snapshot['acked_decision_count'], 'already knows', 'already know')} the final 2PC outcome."
        )
    else:
        acked_description = 'No participant has learned the final 2PC outcome yet.'

    summary_cards = [
        (
            '2PC baseline',
            snapshot['two_phase_outcome'],
            'The coordinator-owned durable decision plus PREPARED participants determine whether the system commits, aborts, or blocks.',
            _comparison_outcome_tone(snapshot['two_phase_outcome']),
        ),
        (
            'Saga contrast',
            saga_outcome,
            'The orchestrated workflow stays off a global PREPARE barrier, so failures become pauses or compensations instead of prepared-lock blocking.',
            _comparison_outcome_tone(saga_outcome),
        ),
        (
            'Participant mix',
            f"{snapshot['participant_count']} total",
            f"{snapshot['commit_voters']} commit / {snapshot['abort_voters']} abort / {snapshot['timeout_voters']} timeout",
            'accent',
        ),
        (
            'Peers with the decision',
            str(snapshot['acked_decision_count']),
            acked_description,
            'accent',
        ),
    ]
    if snapshot['termination_hint_summary']:
        summary_cards.append(
            (
                'Termination hint',
                snapshot['termination_hint_summary'],
                'What a blocked PREPARED participant can safely ask peers or recovery for next.',
                'accent' if not snapshot['termination_hint_summary'].startswith('wait:') else 'warning',
            )
        )

    summary_cards_html = ''.join(
        f'''<article class="summary-card summary-card--{_html_escape(tone)}">
      <p class="summary-label">{_html_escape(label)}</p>
      <strong>{_html_escape(value)}</strong>
      <p>{_html_escape(description)}</p>
    </article>'''
        for label, value, description, tone in summary_cards
    )

    successful_delivery_text = (
        str(snapshot['successful_decision_deliveries_before_crash'])
        if snapshot['coordinator_crash'] == 'after-decision-log'
        else 'n/a (no post-log crash)'
    )
    snapshot_rows = [
        ('Transaction id', result.transaction_id),
        ('Coordinator crash point', snapshot['coordinator_crash']),
        ('Coordinator recovery', 'yes' if snapshot['recover_after_crash'] else 'no'),
        ('Commit voters', _format_name_list(snapshot['commit_participants']) or 'none'),
        ('Abort voters', _format_name_list(snapshot['abort_participants']) or 'none'),
        ('Timeout voters', _format_name_list(snapshot['timeout_participants']) or 'none'),
        ('Prepared participants', _format_name_list(snapshot['prepared_participants']) or 'none'),
        (
            'Participants that learned the final 2PC decision',
            _format_name_list(snapshot['acked_decision_participants']) or 'none yet',
        ),
        (
            'Configured missed second-phase deliveries',
            f"{snapshot['missed_second_phase_participants']} ({_format_name_list(snapshot['missed_second_phase_names']) or 'none'})",
        ),
        (
            'Successful pre-crash decision deliveries',
            successful_delivery_text,
        ),
    ]
    snapshot_rows_html = ''.join(
        f'''<div class="snapshot-row">
      <dt>{_html_escape(label)}</dt>
      <dd>{_html_escape(value)}</dd>
    </div>'''
        for label, value in snapshot_rows
    )

    protocol_cards_html = ''.join(
        _render_protocol_comparison_card_html(comparison)
        for comparison in result.comparisons
    )
    takeaways_html = ''.join(
        f'<li>{_html_escape(item)}</li>' for item in result.interview_takeaways
    )

    two_phase_chip_tone = _comparison_outcome_tone(snapshot['two_phase_outcome'])
    crash_chip_tone = 'warning' if snapshot['coordinator_crash'] != 'none' else 'accent'

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_html_escape(result.title)} protocol comparison dashboard</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f4f7fb;
        --panel: #ffffff;
        --border: #d6dfeb;
        --text: #132238;
        --muted: #526277;
        --accent: #2563eb;
        --accent-soft: #dbeafe;
        --success: #047857;
        --success-soft: #d1fae5;
        --warn: #b45309;
        --warn-soft: #fef3c7;
        --danger: #b91c1c;
        --danger-soft: #fee2e2;
        --shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(180deg, #ecf4ff 0%, var(--bg) 18rem); color: var(--text); }}
      main {{ max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }}
      .hero, .panel, .protocol-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 20px; box-shadow: var(--shadow); }}
      .hero {{ padding: 28px; margin-bottom: 20px; }}
      .eyebrow {{ margin: 0 0 8px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); }}
      h1, h2, h3 {{ margin: 0; }}
      .lede {{ margin: 14px 0 0; max-width: 76ch; color: var(--muted); line-height: 1.6; }}
      .meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }}
      .chip {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 6px 12px; font-size: 0.85rem; font-weight: 700; background: var(--accent-soft); color: var(--accent); }}
      .chip--warning {{ background: var(--warn-soft); color: var(--warn); }}
      .chip--danger {{ background: var(--danger-soft); color: var(--danger); }}
      .chip--success {{ background: var(--success-soft); color: var(--success); }}
      .summary-grid, .protocol-grid {{ display: grid; gap: 16px; }}
      .summary-grid {{ grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); margin-bottom: 20px; }}
      .summary-card {{ border-radius: 18px; border: 1px solid var(--border); padding: 18px; background: #fdfefe; }}
      .summary-card strong {{ display: block; margin-top: 8px; font-size: 1.5rem; line-height: 1.25; }}
      .summary-label {{ margin: 0; color: var(--muted); font-size: 0.92rem; }}
      .summary-card p:last-child {{ margin-bottom: 0; color: var(--muted); line-height: 1.5; }}
      .summary-card--success {{ background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%); border-color: #bbf7d0; }}
      .summary-card--warning {{ background: linear-gradient(180deg, #ffffff 0%, #fff7ed 100%); border-color: #fed7aa; }}
      .summary-card--danger {{ background: linear-gradient(180deg, #ffffff 0%, #fef2f2 100%); border-color: #fecaca; }}
      .summary-card--accent {{ background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%); border-color: #bfdbfe; }}
      .panel {{ padding: 24px; margin-bottom: 20px; }}
      .panel-header p {{ margin: 10px 0 0; color: var(--muted); line-height: 1.55; }}
      .snapshot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin-top: 18px; }}
      .snapshot-row {{ padding: 14px 16px; border-radius: 16px; background: #f8fbff; border: 1px solid #dbe7f5; }}
      .snapshot-row dt {{ margin: 0 0 6px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
      .snapshot-row dd {{ margin: 0; font-size: 1rem; line-height: 1.5; }}
      .protocol-grid {{ grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
      .protocol-card {{ padding: 22px; }}
      .protocol-card--primary {{ background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%); border-color: #bfdbfe; }}
      .protocol-card--secondary {{ background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); }}
      .protocol-card-header {{ display: flex; justify-content: space-between; gap: 12px; align-items: start; margin-bottom: 16px; }}
      .outcome-pill {{ display: inline-flex; align-items: center; border-radius: 999px; padding: 6px 12px; font-size: 0.82rem; font-weight: 800; letter-spacing: 0.02em; }}
      .outcome-pill--success {{ background: var(--success-soft); color: var(--success); }}
      .outcome-pill--warning {{ background: var(--warn-soft); color: var(--warn); }}
      .outcome-pill--danger {{ background: var(--danger-soft); color: var(--danger); }}
      .outcome-pill--accent {{ background: var(--accent-soft); color: var(--accent); }}
      .protocol-blurb {{ margin: 0 0 18px; color: var(--muted); line-height: 1.6; }}
      .metric-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0 0 18px; }}
      .metric-grid div {{ padding: 12px 14px; border-radius: 14px; background: rgba(255,255,255,0.78); border: 1px solid rgba(148, 163, 184, 0.28); }}
      .metric-grid dt {{ margin: 0 0 6px; font-size: 0.77rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }}
      .metric-grid dd {{ margin: 0; line-height: 1.5; }}
      .callout {{ border-radius: 16px; padding: 16px 18px; margin: 0 0 16px; border: 1px solid #dbe7f5; background: #f8fbff; }}
      .callout h3 {{ margin-bottom: 8px; font-size: 1rem; }}
      .callout p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
      ul {{ margin: 0; padding-left: 1.2rem; }}
      li + li {{ margin-top: 8px; }}
      .takeaway-list li {{ line-height: 1.6; }}
      @media (max-width: 820px) {{
        main {{ padding-inline: 14px; }}
        .hero, .panel, .protocol-card {{ border-radius: 16px; }}
        .protocol-card-header {{ flex-direction: column; align-items: start; }}
        .metric-grid {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">Protocol comparison dashboard</p>
        <h1>{_html_escape(result.title)}</h1>
        <p class="lede">{_html_escape(result.description)} This static dashboard makes the 2PC-versus-saga trade-off browsable in one recruiter-friendly artifact: what the coordinator logged, who got stuck in PREPARED, what a saga would do instead, and whether any peer already knows the durable decision.</p>
        <div class="meta">
          <span class="chip">transaction {_html_escape(result.transaction_id)}</span>
          <span class="chip chip--{_html_escape(two_phase_chip_tone)}">2PC {_html_escape(snapshot['two_phase_outcome'])}</span>
          <span class="chip chip--warning">saga {_html_escape(saga_outcome)}</span>
          <span class="chip chip--{_html_escape(crash_chip_tone)}">crash {_html_escape(snapshot['coordinator_crash'])}</span>
        </div>
      </section>

      <section class="summary-grid">
        {summary_cards_html}
      </section>

      <section class="panel">
        <div class="panel-header">
          <h2>Scenario snapshot</h2>
          <p>Keep the scenario facts separate from the protocol story: participant mix, crash point, informed peers, and missed second-phase deliveries all shape what the comparison means.</p>
        </div>
        <dl class="snapshot-grid">
          {snapshot_rows_html}
        </dl>
      </section>

      <section class="protocol-grid">
        {protocol_cards_html}
      </section>

      <section class="panel">
        <div class="panel-header">
          <h2>Interview takeaways</h2>
          <p>Use these bullets when explaining why the same business incident feels coordinator-blocking under 2PC but resumable or compensatable under saga orchestration.</p>
        </div>
        <ul class="takeaway-list">
          {takeaways_html}
        </ul>
      </section>
    </main>
  </body>
</html>
'''


def _render_protocol_comparison_card_html(comparison: ProtocolComparison) -> str:
    tone = _comparison_outcome_tone(comparison.outcome)
    protocol_variant = 'primary' if comparison.protocol == '2PC' else 'secondary'
    tradeoffs_html = ''.join(f'<li>{_html_escape(item)}</li>' for item in comparison.tradeoffs)
    return f'''<article class="protocol-card protocol-card--{protocol_variant}">
      <div class="protocol-card-header">
        <div>
          <p class="eyebrow">{_html_escape(comparison.protocol)}</p>
          <h2>{_html_escape(comparison.protocol)}</h2>
        </div>
        <span class="outcome-pill outcome-pill--{_html_escape(tone)}">{_html_escape(comparison.outcome)}</span>
      </div>
      <p class="protocol-blurb">{_html_escape(comparison.coordination_model)}</p>
      <dl class="metric-grid">
        <div><dt>Consistency model</dt><dd>{_html_escape(comparison.consistency_model)}</dd></div>
        <div><dt>Atomicity</dt><dd>{_html_escape(comparison.atomicity)}</dd></div>
        <div><dt>Blocking behavior</dt><dd>{_html_escape(comparison.blocking_behavior)}</dd></div>
        <div><dt>Recovery story</dt><dd>{_html_escape(comparison.recovery_story)}</dd></div>
      </dl>
      <section class="callout">
        <h3>Participant story</h3>
        <p>{_html_escape(comparison.participant_story)}</p>
      </section>
      <section class="callout">
        <h3>Interview hook</h3>
        <p>{_html_escape(comparison.interview_hook)}</p>
      </section>
      <section>
        <h3>Tradeoffs</h3>
        <ul>
          {tradeoffs_html}
        </ul>
      </section>
    </article>'''


def _comparison_outcome_tone(outcome: str) -> str:
    lowered = outcome.lower()
    if 'blocked' in lowered or 'paused' in lowered:
        return 'warning'
    if 'abort' in lowered or 'compensated' in lowered:
        return 'danger'
    if 'commit' in lowered:
        return 'success'
    return 'accent'


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


def render_termination_resolution_timeline_svg(result: TerminationResolutionResult) -> str:
    cards = _build_termination_timeline_cards(result)
    width = 1200
    margin_x = 48
    timeline_x = 110
    card_x = 160
    card_width = width - card_x - margin_x
    header_height = 186
    gap = 22

    layout_cards: list[dict[str, Any]] = []
    current_y = header_height
    for index, card in enumerate(cards, start=1):
        title_lines = _wrap_svg_text(card["title"], 34)
        body_lines = _wrap_svg_text(card["body"], 78)
        footer_lines = _wrap_svg_text(card["footer"], 78)
        card_height = 96 + (len(body_lines) * 22) + max(0, len(footer_lines) - 1) * 20
        layout_cards.append(
            {
                "index": index,
                "tone": card["tone"],
                "y": current_y,
                "height": card_height,
                "title_lines": title_lines,
                "body_lines": body_lines,
                "footer_lines": footer_lines,
            }
        )
        current_y += card_height + gap

    unresolved_label = _format_name_list(result.unresolved_participants) or "none"
    summary_cards = [
        (
            "Baseline",
            result.baseline_outcome.upper(),
            "warning" if result.baseline_outcome == "blocked" else _timeline_tone_for_state(result.baseline_outcome),
            f"Hint: {result.baseline_termination_hint_summary or 'none'}",
        ),
        (
            "Resolved decision",
            (result.resolved_decision or result.baseline_decision or "none").upper(),
            _timeline_tone_for_state(result.resolved_decision or result.baseline_decision or result.resolution_outcome),
            f"Outcome: {result.resolution_outcome}",
        ),
        (
            "Unresolved after peer exchange",
            unresolved_label,
            "warning" if result.unresolved_participants else "success",
            f"Participants still waiting: {len(result.unresolved_participants)}",
        ),
    ]

    bottom_height = 84 + (len(result.takeaways) * 20)
    total_height = current_y + bottom_height
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}" role="img" aria-labelledby="title desc">',
        f'  <title id="title">{_html_escape(result.title)} peer termination timeline</title>',
        f'  <desc id="desc">{_html_escape(result.description)}</desc>',
        '  <defs>',
        '    <style>',
        '      .title { font: 700 30px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #0f172a; }',
        '      .subtitle { font: 400 15px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #334155; }',
        '      .summary-label { font: 600 12px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; text-transform: uppercase; letter-spacing: 0.08em; fill: #475569; }',
        '      .summary-value { font: 700 22px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #0f172a; }',
        '      .summary-help { font: 400 12px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #475569; }',
        '      .step-label { font: 600 12px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; text-transform: uppercase; letter-spacing: 0.08em; fill: #475569; }',
        '      .step-title { font: 700 20px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #0f172a; }',
        '      .step-body { font: 400 14px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #334155; }',
        '      .step-footer { font: 600 13px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #0f172a; }',
        '      .step-number { font: 700 14px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: white; text-anchor: middle; dominant-baseline: middle; }',
        '      .takeaway-label { font: 700 14px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #0f172a; }',
        '      .takeaway-text { font: 400 13px system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: #334155; }',
        '    </style>',
        '  </defs>',
        '  <rect width="100%" height="100%" fill="#f8fafc" rx="28" ry="28" />',
        f'  <text class="title" x="{margin_x}" y="54">{_html_escape(result.title)} — peer termination timeline</text>',
        f'  <text class="subtitle" x="{margin_x}" y="84">transaction {_html_escape(result.transaction_id)} • baseline {_html_escape(result.baseline_outcome)} • peer resolution {_html_escape(result.resolution_outcome)}</text>',
        f'  <text class="subtitle" x="{margin_x}" y="110">{_html_escape(result.description)}</text>',
    ]

    summary_x = margin_x
    summary_y = 132
    summary_width = 344
    for label, value, tone, help_text in summary_cards:
        fill, border = _timeline_box_colors(tone)
        svg_parts.extend(
            [
                f'  <rect x="{summary_x}" y="{summary_y}" width="{summary_width}" height="80" rx="18" ry="18" fill="{fill}" stroke="{border}" stroke-width="2" />',
                f'  <text class="summary-label" x="{summary_x + 20}" y="{summary_y + 26}">{_html_escape(label)}</text>',
                f'  <text class="summary-value" x="{summary_x + 20}" y="{summary_y + 52}">{_html_escape(value)}</text>',
                f'  <text class="summary-help" x="{summary_x + 20}" y="{summary_y + 70}">{_html_escape(help_text)}</text>',
            ]
        )
        summary_x += summary_width + 12

    if layout_cards:
        first_center = layout_cards[0]["y"] + 24
        last_center = layout_cards[-1]["y"] + 24
        svg_parts.append(
            f'  <line x1="{timeline_x}" y1="{first_center}" x2="{timeline_x}" y2="{last_center}" stroke="#cbd5e1" stroke-width="6" stroke-linecap="round" />'
        )

    for card in layout_cards:
        fill, border = _timeline_box_colors(card["tone"])
        circle_fill = border
        top = card["y"]
        circle_y = top + 24
        svg_parts.extend(
            [
                f'  <circle cx="{timeline_x}" cy="{circle_y}" r="20" fill="{circle_fill}" />',
                f'  <text class="step-number" x="{timeline_x}" y="{circle_y}">{card["index"]}</text>',
                f'  <rect x="{card_x}" y="{top}" width="{card_width}" height="{card["height"]}" rx="22" ry="22" fill="{fill}" stroke="{border}" stroke-width="2" />',
            ]
        )
        text_x = card_x + 24
        text_y = top + 30
        svg_parts.append(f'  <text class="step-label" x="{text_x}" y="{text_y}">Step {card["index"]}</text>')
        text_y += 28
        for line in card["title_lines"]:
            svg_parts.append(f'  <text class="step-title" x="{text_x}" y="{text_y}">{_html_escape(line)}</text>')
            text_y += 24
        text_y += 8
        for line in card["body_lines"]:
            svg_parts.append(f'  <text class="step-body" x="{text_x}" y="{text_y}">{_html_escape(line)}</text>')
            text_y += 22
        text_y += 8
        for line in card["footer_lines"]:
            svg_parts.append(f'  <text class="step-footer" x="{text_x}" y="{text_y}">{_html_escape(line)}</text>')
            text_y += 20

    takeaway_y = current_y + 14
    svg_parts.append(
        f'  <text class="takeaway-label" x="{margin_x}" y="{takeaway_y}">Why this incident still teaches something</text>'
    )
    takeaway_y += 24
    for takeaway in result.takeaways:
        wrapped = _wrap_svg_text(f"• {takeaway}", 126)
        for line in wrapped:
            svg_parts.append(
                f'  <text class="takeaway-text" x="{margin_x}" y="{takeaway_y}">{_html_escape(line)}</text>'
            )
            takeaway_y += 18

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def render_termination_resolution_timeline_html(result: TerminationResolutionResult) -> str:
    svg = render_termination_resolution_timeline_svg(result)
    participant_rows = []
    for participant in result.participants:
        participant_rows.append(
            "<tr>"
            f"<td>{_html_escape(participant.participant)}</td>"
            f"<td>{_html_escape(participant.role)}</td>"
            f"<td>{_html_escape(participant.initial_state)}</td>"
            f"<td>{_html_escape(participant.peer_query)}</td>"
            f"<td>{_html_escape(participant.evidence)}</td>"
            f"<td>{_html_escape(participant.final_state)}</td>"
            f"<td>{'yes' if participant.resolved else 'no'}</td>"
            "</tr>"
        )
    trace_items = "".join(f"<li>{_html_escape(item)}</li>" for item in result.trace)
    takeaway_items = "".join(f"<li>{_html_escape(item)}</li>" for item in result.takeaways)
    unresolved_label = _format_name_list(result.unresolved_participants) or "none"
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{_html_escape(result.title)} peer termination timeline</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --border: #dbeafe;
        --text: #0f172a;
        --muted: #475569;
        --accent: #1d4ed8;
        --success: #166534;
        --warning: #9a3412;
        --danger: #991b1b;
      }}
      * {{ box-sizing: border-box; }}
      body {{ margin: 0; background: linear-gradient(180deg, #eff6ff 0%, var(--bg) 220px); color: var(--text); font: 16px/1.6 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
      main {{ max-width: 1240px; margin: 0 auto; padding: 32px 24px 48px; }}
      .hero, .panel {{ background: var(--panel); border: 1px solid var(--border); border-radius: 24px; box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06); }}
      .hero {{ padding: 28px; margin-bottom: 24px; }}
      .eyebrow {{ margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.78rem; color: var(--accent); font-weight: 700; }}
      h1, h2 {{ margin: 0 0 12px; line-height: 1.2; }}
      .lede {{ margin: 0; color: var(--muted); max-width: 88ch; }}
      .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 18px; }}
      .stat {{ border: 1px solid #dbeafe; border-radius: 18px; padding: 16px; background: #f8fbff; }}
      .stat strong {{ display: block; font-size: 1.25rem; margin-top: 4px; }}
      .grid {{ display: grid; gap: 24px; }}
      .panel {{ padding: 24px; }}
      .graphic svg {{ width: 100%; height: auto; display: block; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ text-align: left; vertical-align: top; border-bottom: 1px solid #e2e8f0; padding: 10px 8px; font-size: 0.95rem; }}
      th {{ color: var(--muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; }}
      ul, ol {{ margin: 0; padding-left: 20px; }}
      li + li {{ margin-top: 8px; }}
      code {{ background: #eff6ff; padding: 0.08rem 0.36rem; border-radius: 999px; }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">Two-phase commit termination timeline</p>
        <h1>{_html_escape(result.title)}</h1>
        <p class="lede">{_html_escape(result.description)} This static artifact keeps the peer-assisted termination story readable in one place: where the baseline 2PC run got stuck, which peers could answer, what evidence they shared, and whether the blocked participants converged on COMMIT/ABORT or stayed stuck.</p>
        <div class="stats">
          <article class="stat"><span>Baseline outcome</span><strong>{_html_escape(result.baseline_outcome)}</strong><div>Hint: {_html_escape(result.baseline_termination_hint_summary or 'none')}</div></article>
          <article class="stat"><span>Peer-resolution outcome</span><strong>{_html_escape(result.resolution_outcome)}</strong><div>Resolved decision: {_html_escape(result.resolved_decision or result.baseline_decision or 'none')}</div></article>
          <article class="stat"><span>Unresolved after exchange</span><strong>{_html_escape(unresolved_label)}</strong><div>{len(result.unresolved_participants)} participant(s) still waiting</div></article>
        </div>
      </section>
      <div class="grid">
        <section class="panel graphic">
          <h2>Timeline graphic</h2>
          {svg}
        </section>
        <section class="panel">
          <h2>Participant actions</h2>
          <table>
            <thead>
              <tr>
                <th>Participant</th>
                <th>Role</th>
                <th>Initial</th>
                <th>Peer query</th>
                <th>Evidence</th>
                <th>Final</th>
                <th>Resolved</th>
              </tr>
            </thead>
            <tbody>
              {''.join(participant_rows)}
            </tbody>
          </table>
        </section>
        <section class="panel">
          <h2>Resolution trace</h2>
          <ol>{trace_items}</ol>
        </section>
        <section class="panel">
          <h2>Interview takeaways</h2>
          <ul>{takeaway_items}</ul>
        </section>
      </div>
    </main>
  </body>
</html>
'''


def _build_termination_timeline_cards(result: TerminationResolutionResult) -> list[dict[str, str]]:
    baseline_decision = (result.baseline_decision or "none").upper()
    unresolved_label = _format_name_list(result.unresolved_participants) or "none"
    baseline_unresolved = [
        participant.participant
        for participant in result.participants
        if participant.initial_state.startswith("prepared")
    ]
    baseline_unresolved_label = _format_name_list(baseline_unresolved) or "none"
    cards: list[dict[str, str]] = [
        {
            "tone": "warning" if result.baseline_outcome == "blocked" else _timeline_tone_for_state(result.baseline_outcome),
            "title": "Baseline incident state",
            "body": (
                f"The baseline 2PC run ends as {result.baseline_outcome}. Durable decision: {baseline_decision}. "
                f"Termination hint: {result.baseline_termination_hint_summary or 'none'}. Unresolved after the plain run: {baseline_unresolved_label}."
            ),
            "footer": "Peer-assisted termination starts from these exact facts; it never invents a brand-new global outcome.",
        }
    ]
    for participant in result.participants:
        if participant.peer_query == "not needed":
            title = f"{participant.participant} needs no peer exchange"
            body = "The scenario already completed without extra peer-to-peer termination work for this participant."
        elif participant.peer_query.startswith("answer"):
            title = f"{participant.participant} acts as an evidence source"
            body = participant.evidence
        else:
            title = f"{participant.participant} starts a peer check"
            body = f"Query: {participant.peer_query}. Evidence: {participant.evidence}."
        cards.append(
            {
                "tone": _timeline_tone_for_step(participant),
                "title": title,
                "body": body,
                "footer": (
                    f"{participant.role}: {participant.initial_state} -> {participant.final_state} "
                    f"(resolved: {'yes' if participant.resolved else 'no'})."
                ),
            }
        )
    final_decision = (result.resolved_decision or result.baseline_decision or "none").upper()
    final_body = (
        f"Peer exchange finishes with outcome {result.resolution_outcome}. Final decision: {final_decision}. "
        f"Participants still blocked after the exchange: {unresolved_label}."
    )
    cards.append(
        {
            "tone": _timeline_tone_for_state(result.resolution_outcome),
            "title": "Resolution summary",
            "body": final_body,
            "footer": result.takeaways[0],
        }
    )
    return cards


def _timeline_tone_for_step(step: TerminationResolutionStep) -> str:
    if not step.resolved:
        return "warning"
    return _timeline_tone_for_state(step.final_state)


def _timeline_tone_for_state(state: str | None) -> str:
    lowered = (state or "none").lower()
    if "abort" in lowered:
        return "danger"
    if "commit" in lowered:
        return "success"
    if "block" in lowered or "prepare" in lowered or "wait" in lowered or lowered == "none":
        return "warning"
    return "accent"


def _timeline_box_colors(tone: str) -> tuple[str, str]:
    palette = {
        "success": ("#ecfdf5", "#16a34a"),
        "warning": ("#fff7ed", "#ea580c"),
        "danger": ("#fef2f2", "#dc2626"),
        "accent": ("#eff6ff", "#2563eb"),
    }
    return palette.get(tone, palette["accent"])


def _wrap_svg_text(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in str(text).splitlines() or [""]:
        wrapped = textwrap.wrap(paragraph, width=width) or [""]
        lines.extend(wrapped)
    return lines


def render_catalog_markdown(
    entries: list[CatalogEntry],
    incident_dashboard_path: str | None = None,
) -> str:
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
    comparison_dashboard_count = sum(1 for entry in entries if entry.comparison_html_path)
    termination_artifact_count = sum(1 for entry in entries if entry.termination_markdown_path)
    termination_timeline_count = sum(
        1
        for entry in entries
        if entry.termination_timeline_svg_path or entry.termination_timeline_html_path
    )

    comparison_lines = [
        "| Scenario | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Recovered after reconnect | Termination hint | Report | Compare | Termination | Timeline |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
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
        compare_links: list[str] = []
        if entry.comparison_html_path:
            compare_links.append(f"[html]({entry.comparison_html_path})")
        if entry.comparison_markdown_path:
            compare_links.append(f"[md]({entry.comparison_markdown_path})")
        termination_links: list[str] = []
        if entry.termination_markdown_path:
            termination_links.append(f"[md]({entry.termination_markdown_path})")
        timeline_links: list[str] = []
        if entry.termination_timeline_html_path:
            timeline_links.append(f"[html]({entry.termination_timeline_html_path})")
        if entry.termination_timeline_svg_path:
            timeline_links.append(f"[svg]({entry.termination_timeline_svg_path})")
        compare_cell = " / ".join(compare_links) if compare_links else "-"
        termination_artifact_cell = " / ".join(termination_links) if termination_links else "-"
        timeline_cell = " / ".join(timeline_links) if timeline_links else "-"
        reconnect_cell = f"`{recovered_count}/{missed_count}`" if missed_count else "`-`"
        termination_cell = result.termination_hint_summary or "-"
        comparison_lines.append(
            "| {title} | `{outcome}` | `{decision}` | `{durable}` | `{crash}` | `{recovery}` | `{prepared}/{total}` | `{acked}/{total}` | {reconnect} | {termination} | {report} | {compare} | {termination_artifact} | {timeline} |".format(
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
                compare=compare_cell,
                termination_artifact=termination_artifact_cell,
                timeline=timeline_cell,
            )
        )

        reconnect_snapshot = (
            f"`{recovered_count}/{missed_count}` recovered after missing the first second-phase delivery"
            if missed_count
            else "`-` (no participant missed the first second-phase delivery)"
        )
        related_artifacts: list[str] = []
        if entry.report_path:
            related_artifacts.append(f"[report]({entry.report_path})")
        if entry.comparison_html_path:
            related_artifacts.append(f"[compare html]({entry.comparison_html_path})")
        if entry.comparison_markdown_path:
            related_artifacts.append(f"[compare md]({entry.comparison_markdown_path})")
        if entry.termination_markdown_path:
            related_artifacts.append(f"[termination md]({entry.termination_markdown_path})")
        if entry.termination_timeline_html_path:
            related_artifacts.append(f"[timeline html]({entry.termination_timeline_html_path})")
        if entry.termination_timeline_svg_path:
            related_artifacts.append(f"[timeline svg]({entry.termination_timeline_svg_path})")
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
        if related_artifacts:
            snapshot_lines.append(f"- related artifacts: {' / '.join(related_artifacts)}")
        snapshot_lines.append("")

    incident_dashboard_lines: list[str] = []
    if incident_dashboard_path:
        incident_dashboard_lines = [
            "Need the blocked-case triage view first? Open the "
            f"[incident-response dashboard]({incident_dashboard_path}).",
            "",
        ]

    lines = [
        "# Two-phase commit scenario catalog",
        "",
        "A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, recovery, and peer-assisted incident-response cases.",
        "",
        *incident_dashboard_lines,
        "## Bundle summary",
        f"- scenarios: `{len(entries)}`",
        f"- outcomes: `{commit_count} commit`, `{abort_count} abort`, `{blocked_count} blocked`",
        f"- crash cases: `{crash_count}`",
        f"- coordinator recovery cases: `{recovery_count}`",
        f"- participant reconnect recoveries: `{reconnect_recovery_count}`",
        f"- blocked scenarios with actionable peer hints: `{actionable_termination_hint_count}`",
        f"- scenarios with protocol-comparison dashboards: `{comparison_dashboard_count}`",
        f"- scenarios with peer-termination walkthroughs: `{termination_artifact_count}`",
        f"- scenarios with peer-termination timeline visuals: `{termination_timeline_count}`",
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


def render_incident_response_html(
    entries: list[CatalogEntry],
    *,
    catalog_markdown_path: str | None = None,
) -> str:
    blocked_entries = [entry for entry in entries if entry.result.outcome == "blocked"]
    group_specs = [
        (
            "recovery",
            "Recovery-required / still blocked",
            "These incidents do not yet have decisive peer evidence, so the safe play is to wait for coordinator recovery or keep the transaction blocked.",
            "warning",
        ),
        (
            "commit-evidence",
            "Peer-visible COMMIT evidence",
            "At least one peer already knows the durable COMMIT, so the incident can pivot from blind waiting into a concrete peer-assisted resolution drill.",
            "success",
        ),
        (
            "abort-evidence",
            "Safe-ABORT evidence",
            "A peer that never reached PREPARED can safely prove rollback, which turns the incident into an evidence-backed ABORT response instead of indefinite doubt.",
            "danger",
        ),
    ]
    grouped_entries: dict[str, list[CatalogEntry]] = {key: [] for key, *_ in group_specs}
    for entry in blocked_entries:
        grouped_entries[_incident_response_group(entry.result)].append(entry)

    summary_cards = [
        (
            "Blocked incidents",
            str(len(blocked_entries)),
            "Baseline blocked scenarios in the current 2PC sample bundle.",
            "neutral",
        ),
        (
            "Recovery-required",
            str(len(grouped_entries["recovery"])),
            "No decisive peer evidence exists yet, so coordinator recovery still matters most.",
            "warning",
        ),
        (
            "Peer-visible COMMIT",
            str(len(grouped_entries["commit-evidence"])),
            "A participant already heard durable COMMIT before the crash.",
            "success",
        ),
        (
            "Safe-ABORT evidence",
            str(len(grouped_entries["abort-evidence"])),
            "A non-prepared peer can prove rollback safely.",
            "danger",
        ),
    ]
    summary_cards_html = "".join(
        f'''<article class="summary-card summary-card--{_html_escape(tone)}">
      <p class="summary-label">{_html_escape(label)}</p>
      <strong>{_html_escape(value)}</strong>
      <p>{_html_escape(description)}</p>
    </article>'''
        for label, value, description, tone in summary_cards
    )

    catalog_link_html = ""
    if catalog_markdown_path:
        catalog_link_html = (
            '<a class="catalog-link" href="'
            + _html_escape(catalog_markdown_path)
            + '">Open the full scenario catalog</a>'
        )

    if not blocked_entries:
        sections_html = """
        <section class="group group--neutral">
          <div class="group-header">
            <div>
              <p class="eyebrow">No blocked baselines</p>
              <h2>No incident-response cases yet</h2>
            </div>
            <span class="group-count">0</span>
          </div>
          <p class="group-description">Once a scenario blocks after PREPARE, this dashboard will group it by whether recovery, peer-visible COMMIT evidence, or safe-ABORT evidence drives the response.</p>
        </section>
        """
    else:
        section_parts: list[str] = []
        for key, heading, description, tone in group_specs:
            matches = grouped_entries[key]
            if not matches:
                continue
            cards_html = "".join(_render_incident_response_card_html(entry) for entry in matches)
            section_parts.append(
                f'''<section class="group group--{_html_escape(tone)}">
          <div class="group-header">
            <div>
              <p class="eyebrow">Blocked-case bucket</p>
              <h2>{_html_escape(heading)}</h2>
            </div>
            <span class="group-count">{len(matches)}</span>
          </div>
          <p class="group-description">{_html_escape(description)}</p>
          <div class="incident-grid">
            {cards_html}
          </div>
        </section>'''
            )
        sections_html = "\n".join(section_parts)

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Two-phase commit incident-response dashboard</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f5f7fb;
        --surface: #ffffff;
        --surface-alt: #eef2ff;
        --text: #172033;
        --muted: #5b6475;
        --border: #d7dfef;
        --shadow: 0 18px 40px rgba(23, 32, 51, 0.08);
        --warning: #8a5a00;
        --warning-bg: #fff4d6;
        --success: #1f6b3b;
        --success-bg: #ddf7e6;
        --danger: #9f1c1c;
        --danger-bg: #ffe0e0;
        --neutral: #3056d3;
        --neutral-bg: #e5edff;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: linear-gradient(180deg, #f8fbff 0%, var(--bg) 100%);
        color: var(--text);
      }}
      main {{ max-width: 1180px; margin: 0 auto; padding: 48px 20px 64px; }}
      .hero {{
        background: linear-gradient(140deg, #172033 0%, #274690 58%, #3155d4 100%);
        color: #fff;
        padding: 32px;
        border-radius: 28px;
        box-shadow: var(--shadow);
      }}
      .eyebrow {{
        margin: 0 0 10px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.76rem;
        font-weight: 700;
        opacity: 0.78;
      }}
      h1, h2, h3, p {{ margin-top: 0; }}
      h1 {{ font-size: clamp(2rem, 3vw, 3rem); margin-bottom: 14px; }}
      .lede {{ max-width: 78ch; line-height: 1.65; font-size: 1rem; margin-bottom: 18px; color: rgba(255,255,255,0.9); }}
      .hero-links {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
      .catalog-link {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 11px 16px;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.16);
        color: #fff;
        text-decoration: none;
        font-weight: 700;
      }}
      .summary-grid, .incident-grid {{
        display: grid;
        gap: 16px;
      }}
      .summary-grid {{
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        margin: 24px 0 0;
      }}
      .summary-card, .incident-card, .group {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 24px;
        box-shadow: var(--shadow);
      }}
      .summary-card {{ padding: 20px; }}
      .summary-card strong {{ display: block; font-size: 2rem; margin-bottom: 8px; }}
      .summary-card p {{ color: var(--muted); line-height: 1.5; margin-bottom: 0; }}
      .summary-label {{ font-size: 0.9rem; font-weight: 700; color: var(--text); margin-bottom: 8px; }}
      .summary-card--warning strong, .group--warning h2, .pill--warning {{ color: var(--warning); }}
      .summary-card--success strong, .group--success h2, .pill--success {{ color: var(--success); }}
      .summary-card--danger strong, .group--danger h2, .pill--danger {{ color: var(--danger); }}
      .summary-card--neutral strong, .group--neutral h2, .pill--neutral {{ color: var(--neutral); }}
      .group {{ padding: 24px; margin-top: 28px; }}
      .group-header {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 8px; }}
      .group-count {{
        min-width: 48px;
        padding: 10px 14px;
        border-radius: 999px;
        background: var(--surface-alt);
        text-align: center;
        font-weight: 800;
      }}
      .group--warning .group-count {{ background: var(--warning-bg); color: var(--warning); }}
      .group--success .group-count {{ background: var(--success-bg); color: var(--success); }}
      .group--danger .group-count {{ background: var(--danger-bg); color: var(--danger); }}
      .group--neutral .group-count {{ background: var(--neutral-bg); color: var(--neutral); }}
      .group-description {{ color: var(--muted); line-height: 1.6; max-width: 78ch; margin-bottom: 18px; }}
      .incident-grid {{ grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
      .incident-card {{ padding: 20px; }}
      .incident-card__header {{ display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 12px; }}
      .incident-card__header h3 {{ margin-bottom: 6px; font-size: 1.15rem; }}
      .incident-card__description {{ color: var(--muted); line-height: 1.55; margin-bottom: 14px; }}
      .pill {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 6px 12px;
        background: var(--surface-alt);
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }}
      .pill--warning {{ background: var(--warning-bg); }}
      .pill--success {{ background: var(--success-bg); }}
      .pill--danger {{ background: var(--danger-bg); }}
      .incident-facts {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px 14px;
        margin: 0 0 14px;
      }}
      .incident-facts div {{ background: #f8faff; border: 1px solid var(--border); border-radius: 16px; padding: 10px 12px; }}
      .incident-facts dt {{ margin: 0 0 6px; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }}
      .incident-facts dd {{ margin: 0; font-weight: 700; }}
      .incident-card__callout {{
        border-left: 4px solid var(--border);
        background: #fafcff;
        border-radius: 16px;
        padding: 12px 14px;
        margin-bottom: 12px;
        line-height: 1.55;
        color: var(--text);
      }}
      .incident-card__callout strong {{ display: block; margin-bottom: 4px; }}
      .artifact-links {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
      .artifact-link {{
        display: inline-flex;
        padding: 8px 12px;
        border-radius: 999px;
        background: var(--neutral-bg);
        color: var(--neutral);
        text-decoration: none;
        font-weight: 700;
      }}
      @media (max-width: 720px) {{
        .hero {{ padding: 24px; border-radius: 22px; }}
        .group {{ padding: 20px; }}
        .incident-facts {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <section class="hero">
        <p class="eyebrow">Two-phase commit incident-response dashboard</p>
        <h1>Blocked-case triage at a glance</h1>
        <p class="lede">This static dashboard strips the portfolio bundle down to the incidents that actually block after <code>PREPARE</code>. It groups them by the response story that matters most during triage: waiting for coordinator recovery, following peer-visible <code>COMMIT</code> evidence, or proving a safe <code>ABORT</code> from a peer that never reached <code>PREPARED</code>.</p>
        <div class="hero-links">
          {catalog_link_html}
        </div>
      </section>

      <section class="summary-grid">
        {summary_cards_html}
      </section>

      {sections_html}
    </main>
  </body>
</html>
'''


def _incident_response_group(result: SimulationResult) -> str:
    summary = result.termination_hint_summary or ""
    if summary.startswith("COMMIT visible"):
        return "commit-evidence"
    if summary.startswith("ABORT safe"):
        return "abort-evidence"
    return "recovery"


def _render_incident_response_card_html(entry: CatalogEntry) -> str:
    result = entry.result
    prepared_count = sum(1 for item in result.participants if item["prepared"])
    acked_count = sum(1 for item in result.participants if item["acked_decision"])
    blocked_count = sum(1 for item in result.participants if item["state"] == "prepared")
    decision_label = (result.decision or "none").upper()
    pill_tone = {
        "COMMIT": "success",
        "ABORT": "danger",
    }.get(decision_label, "warning")
    evidence_label = result.termination_hint_summary or "No decisive peer evidence yet"
    links: list[tuple[str, str]] = []
    if entry.report_path:
        links.append(("report", entry.report_path))
    if entry.termination_markdown_path:
        links.append(("termination md", entry.termination_markdown_path))
    if entry.termination_timeline_html_path:
        links.append(("timeline html", entry.termination_timeline_html_path))
    if entry.termination_timeline_svg_path:
        links.append(("timeline svg", entry.termination_timeline_svg_path))
    if entry.comparison_html_path:
        links.append(("compare html", entry.comparison_html_path))
    if entry.comparison_markdown_path:
        links.append(("compare md", entry.comparison_markdown_path))
    links_html = "".join(
        f'<a class="artifact-link" href="{_html_escape(path)}">{_html_escape(label)}</a>'
        for label, path in links
    )
    return f'''<article class="incident-card">
      <div class="incident-card__header">
        <div>
          <p class="eyebrow">transaction {_html_escape(result.transaction_id)}</p>
          <h3>{_html_escape(result.title)}</h3>
        </div>
        <span class="pill pill--{_html_escape(pill_tone)}">{_html_escape(decision_label)}</span>
      </div>
      <p class="incident-card__description">{_html_escape(result.description)}</p>
      <dl class="incident-facts">
        <div><dt>Crash point</dt><dd>{_html_escape(result.failures['coordinator_crash'])}</dd></div>
        <div><dt>Durable decision</dt><dd>{'yes' if result.decision_durable else 'no'}</dd></div>
        <div><dt>Prepared / total</dt><dd>{prepared_count}/{len(result.participants)}</dd></div>
        <div><dt>Acked / total</dt><dd>{acked_count}/{len(result.participants)}</dd></div>
        <div><dt>Still blocked</dt><dd>{blocked_count}</dd></div>
        <div><dt>Recovery configured</dt><dd>{'yes' if result.failures['recover_after_crash'] else 'no'}</dd></div>
      </dl>
      <div class="incident-card__callout">
        <strong>Evidence</strong>
        {_html_escape(evidence_label)}
      </div>
      <div class="incident-card__callout">
        <strong>Blocking story</strong>
        {_html_escape(result.blocking_reason or 'No blocking reason recorded.')}
      </div>
      <div class="artifact-links">
        {links_html}
      </div>
    </article>'''


def write_markdown_report(path: str | Path, result: SimulationResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(result))


def write_comparison_markdown(path: str | Path, result: ComparisonResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_comparison_markdown(result))


def write_comparison_html(path: str | Path, result: ComparisonResult) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_comparison_html(result))


def write_termination_resolution_markdown(
    path: str | Path,
    result: TerminationResolutionResult,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_termination_resolution_markdown(result))


def write_termination_timeline_svg(
    path: str | Path,
    result: TerminationResolutionResult,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_termination_resolution_timeline_svg(result))


def write_termination_timeline_html(
    path: str | Path,
    result: TerminationResolutionResult,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_termination_resolution_timeline_html(result))


def write_incident_response_dashboard(
    path: str | Path,
    entries: list[CatalogEntry],
    *,
    catalog_markdown_path: str | None = None,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_incident_response_html(
            entries,
            catalog_markdown_path=catalog_markdown_path,
        )
    )


def write_catalog(
    path: str | Path,
    entries: list[CatalogEntry],
    *,
    incident_dashboard_path: str | None = None,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_catalog_markdown(
            entries,
            incident_dashboard_path=incident_dashboard_path,
        )
    )


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


def _relative_artifact_path(path: Path, *, start: Path) -> str | None:
    if not path.exists():
        return None
    return os.path.relpath(path, start=start).replace(os.sep, "/")


def build_catalog_entries(
    scenario_paths: list[Path],
    *,
    catalog_path: Path,
    report_dir: Path | None = None,
) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    artifact_dir = report_dir or catalog_path.parent
    for scenario_path in scenario_paths:
        scenario = load_scenario(scenario_path)
        result = simulate_two_phase_commit(scenario)
        report_path: str | None = None
        report_file = artifact_dir / f"{scenario_path.stem}_report.md"
        termination_markdown_file = artifact_dir / f"{scenario_path.stem}_termination.md"
        termination_timeline_svg_file = artifact_dir / f"{scenario_path.stem}_termination_timeline.svg"
        termination_timeline_html_file = artifact_dir / f"{scenario_path.stem}_termination_timeline.html"
        if report_dir is not None:
            write_markdown_report(report_file, result)
            if result.outcome == "blocked":
                termination_result = build_peer_termination_resolution(scenario)
                write_termination_resolution_markdown(
                    termination_markdown_file,
                    termination_result,
                )
                write_termination_timeline_svg(
                    termination_timeline_svg_file,
                    termination_result,
                )
                write_termination_timeline_html(
                    termination_timeline_html_file,
                    termination_result,
                )
        report_path = _relative_artifact_path(report_file, start=catalog_path.parent)
        comparison_markdown_path = _relative_artifact_path(
            artifact_dir / f"{scenario_path.stem}_protocol_compare.md",
            start=catalog_path.parent,
        )
        comparison_html_path = _relative_artifact_path(
            artifact_dir / f"{scenario_path.stem}_protocol_compare.html",
            start=catalog_path.parent,
        )
        termination_markdown_path = _relative_artifact_path(
            termination_markdown_file,
            start=catalog_path.parent,
        )
        termination_timeline_svg_path = _relative_artifact_path(
            termination_timeline_svg_file,
            start=catalog_path.parent,
        )
        termination_timeline_html_path = _relative_artifact_path(
            termination_timeline_html_file,
            start=catalog_path.parent,
        )
        entries.append(
            CatalogEntry(
                source_path=str(scenario_path).replace(os.sep, "/"),
                report_path=report_path,
                comparison_markdown_path=comparison_markdown_path,
                comparison_html_path=comparison_html_path,
                termination_markdown_path=termination_markdown_path,
                termination_timeline_svg_path=termination_timeline_svg_path,
                termination_timeline_html_path=termination_timeline_html_path,
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
    compare_parser.add_argument(
        "--html-out",
        type=Path,
        help="optional path for a static HTML comparison dashboard",
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
    terminate_parser.add_argument(
        "--timeline-svg-out",
        type=Path,
        help="optional path for a standalone SVG peer-resolution timeline artifact",
    )
    terminate_parser.add_argument(
        "--timeline-html-out",
        type=Path,
        help="optional path for a standalone HTML peer-resolution timeline artifact",
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
        stream = sys.stderr if args.json else sys.stdout
        if args.markdown_out:
            write_comparison_markdown(args.markdown_out, result)
            print(f"wrote Markdown comparison to {args.markdown_out}", file=stream)
        if args.html_out:
            write_comparison_html(args.html_out, result)
            print(f"wrote HTML comparison dashboard to {args.html_out}", file=stream)
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
        stream = sys.stderr if args.json else sys.stdout
        if args.markdown_out:
            write_termination_resolution_markdown(args.markdown_out, result)
            print(f"wrote Markdown peer-resolution artifact to {args.markdown_out}", file=stream)
        if args.timeline_svg_out:
            write_termination_timeline_svg(args.timeline_svg_out, result)
            print(f"wrote SVG peer-resolution timeline to {args.timeline_svg_out}", file=stream)
        if args.timeline_html_out:
            write_termination_timeline_html(args.timeline_html_out, result)
            print(f"wrote HTML peer-resolution timeline to {args.timeline_html_out}", file=stream)
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
        incident_dashboard_path = args.markdown_out.parent / "incident_response_dashboard.html"
        incident_dashboard_relative_path = _relative_artifact_path(
            incident_dashboard_path,
            start=args.markdown_out.parent,
        ) or incident_dashboard_path.name
        write_incident_response_dashboard(
            incident_dashboard_path,
            entries,
            catalog_markdown_path=args.markdown_out.name,
        )
        write_catalog(
            args.markdown_out,
            entries,
            incident_dashboard_path=incident_dashboard_relative_path,
        )
        if args.report_dir:
            print(f"wrote {len(entries)} scenario reports to {args.report_dir}")
        print(f"wrote incident-response dashboard to {incident_dashboard_path}")
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


def _html_escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


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
