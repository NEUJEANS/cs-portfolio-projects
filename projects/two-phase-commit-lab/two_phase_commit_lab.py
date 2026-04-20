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


@dataclass
class ParticipantPlan:
    name: str
    vote: str
    role: str = "participant"
    notes: str = ""


@dataclass
class FailurePlan:
    coordinator_crash: str = "none"
    recover_after_crash: bool = False


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ParticipantRuntime:
    plan: ParticipantPlan
    state: str = "new"
    acked_decision: bool = False
    prepared: bool = False


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
        role = entry.get("role", "participant")
        if not isinstance(role, str) or not role.strip():
            raise ScenarioError(f"participant {name} role must be a non-empty string")
        notes = entry.get("notes", "")
        if not isinstance(notes, str):
            raise ScenarioError(f"participant {name} notes must be a string")
        participants.append(
            ParticipantPlan(name=name, vote=vote, role=role.strip(), notes=notes.strip())
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

    return Scenario(
        title=title,
        description=description,
        transaction_id=transaction_id,
        participants=participants,
        failures=FailurePlan(
            coordinator_crash=coordinator_crash,
            recover_after_crash=recover_after_crash,
        ),
    )


def simulate_two_phase_commit(scenario: Scenario) -> SimulationResult:
    participants = [ParticipantRuntime(plan=plan) for plan in scenario.participants]
    coordinator = CoordinatorRuntime()
    trace: list[str] = []

    def log(message: str) -> None:
        trace.append(message)

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
        coordinator.state = "crashed-after-decision"
        log("coordinator crashes after the durable decision is logged but before all participants hear it")
        if recover:
            coordinator.state = "recovered"
            log("recovery replays the durable decision log and resumes decision broadcast")
        else:
            blocking_reason = (
                f"the durable {coordinator.decision.upper()} decision exists, but the coordinator crashed "
                "before completing the second phase; prepared participants stay in doubt until recovery"
            )
            log("prepared participants stay blocked until the coordinator recovers and replays its log")
            return _build_result(
                scenario,
                outcome="blocked",
                decision=coordinator.decision,
                decision_durable=True,
                blocking_reason=blocking_reason,
                participants=participants,
                coordinator=coordinator,
                trace=trace,
            )

    assert coordinator.decision is not None
    for participant in participants:
        log(f"coordinator -> {participant.plan.name}: {coordinator.decision.upper()}")
        if coordinator.decision == "commit":
            if participant.prepared:
                participant.state = "committed"
                participant.acked_decision = True
                log(f"{participant.plan.name}: commits local work and acknowledges COMMIT")
            elif participant.state == "timed_out":
                log(f"{participant.plan.name}: was unavailable during voting and never prepared local work")
            else:
                log(f"{participant.plan.name}: had already refused the transaction before COMMIT was possible")
        else:
            if participant.prepared:
                participant.state = "aborted"
                participant.acked_decision = True
                log(f"{participant.plan.name}: rolls back prepared work and acknowledges ABORT")
            elif participant.state == "timed_out":
                log(f"{participant.plan.name}: times out without preparing any local work")
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
    )


def render_markdown_report(result: SimulationResult) -> str:
    participant_lines = [
        "| Participant | Role | Planned vote | Final state | Acked decision | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for participant in result.participants:
        participant_lines.append(
            "| {name} | {role} | {planned_vote} | {state} | {acked_decision} | {notes} |".format(
                name=participant["name"],
                role=participant["role"],
                planned_vote=participant["planned_vote"],
                state=participant["state"],
                acked_decision="yes" if participant["acked_decision"] else "no",
                notes=participant["notes"] or "-",
            )
        )

    trace_lines = [f"{index}. {entry}" for index, entry in enumerate(result.trace, start=1)]
    takeaway_lines = [f"- {entry}" for entry in result.takeaways]

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
    ]
    if result.blocking_reason:
        lines.append(f"- blocking reason: {result.blocking_reason}")
    lines.extend(
        [
            "",
            "## Participant summary",
            *participant_lines,
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

    comparison_lines = [
        "| Scenario | Outcome | Decision | Durable decision | Crash point | Recovery | Prepared | Acked | Report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    snapshot_lines: list[str] = []
    for entry in entries:
        result = entry.result
        prepared_count = sum(1 for item in result.participants if item["prepared"])
        acked_count = sum(1 for item in result.participants if item["acked_decision"])
        title_cell = result.title
        report_cell = "-"
        if entry.report_path:
            title_cell = f"[{result.title}]({entry.report_path})"
            report_cell = f"[report]({entry.report_path})"
        comparison_lines.append(
            "| {title} | `{outcome}` | `{decision}` | `{durable}` | `{crash}` | `{recovery}` | `{prepared}/{total}` | `{acked}/{total}` | {report} |".format(
                title=title_cell,
                outcome=result.outcome,
                decision=result.decision or "none",
                durable="yes" if result.decision_durable else "no",
                crash=result.failures["coordinator_crash"],
                recovery="yes" if result.failures["recover_after_crash"] else "no",
                prepared=prepared_count,
                acked=acked_count,
                total=len(result.participants),
                report=report_cell,
            )
        )

        snapshot_lines.extend(
            [
                f"### {result.title}",
                f"- source: `{entry.source_path}`",
                f"- description: {result.description}",
                f"- outcome: `{result.outcome}` with decision `{result.decision or 'none'}`",
                f"- participants prepared/acked: `{prepared_count}/{len(result.participants)}` prepared, `{acked_count}/{len(result.participants)}` acked",
                f"- why it matters: {_primary_takeaway(result)}",
            ]
        )
        if entry.report_path:
            snapshot_lines.append(f"- deep dive: [{entry.report_path}]({entry.report_path})")
        snapshot_lines.append("")

    lines = [
        "# Two-phase commit scenario catalog",
        "",
        "A recruiter-friendly landing page for the committed 2PC scenarios, showing how the same protocol behaves across happy-path, veto, blocking, and recovery cases.",
        "",
        "## Bundle summary",
        f"- scenarios: `{len(entries)}`",
        f"- outcomes: `{commit_count} commit`, `{abort_count} abort`, `{blocked_count} blocked`",
        f"- crash cases: `{crash_count}`",
        f"- recovery cases: `{recovery_count}`",
        "",
        "## Scenario comparison",
        *comparison_lines,
        "",
        "## Interview talking points",
        "- plain 2PC is easy to explain because every scenario pivots on the coordinator's durable decision log.",
        "- blocking shows up when participants are already prepared but cannot prove the final outcome after a coordinator crash.",
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
            print(f"participants={len(result.participants)} trace_events={len(result.trace)}")
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
) -> SimulationResult:
    participant_rows = [
        {
            "name": participant.plan.name,
            "role": participant.plan.role,
            "planned_vote": participant.plan.vote,
            "state": participant.state,
            "prepared": participant.prepared,
            "acked_decision": participant.acked_decision,
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
        },
        participants=participant_rows,
        trace=trace,
        takeaways=takeaways,
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
    lines = [
        f"{yes_count} participants were willing to commit, {abort_count} voted abort, and {timeout_count} timed out.",
        f"{prepared_count} participants reached PREPARED before the transaction finished.",
    ]
    if blocking_reason:
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


def _primary_takeaway(result: SimulationResult) -> str:
    if result.blocking_reason:
        return result.blocking_reason
    for entry in result.takeaways:
        if entry.startswith("2PC "):
            return entry
    return result.takeaways[-1]


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScenarioError(f"{key} must be a non-empty string")
    return value.strip()


if __name__ == "__main__":
    raise SystemExit(main())
