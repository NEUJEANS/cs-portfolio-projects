#!/usr/bin/env python3
"""MVCC isolation lab.

A compact simulator for comparing read committed, snapshot isolation,
and optimistic serializable validation on small hand-authored scenarios.
"""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SUPPORTED_ISOLATION_LEVELS = ("read-committed", "snapshot", "serializable")
SUPPORTED_STEP_OPS = {"read", "scan", "assert", "write"}
EVENT_COLORS = {
    "begin": "#dbe4ff",
    "read": "#d1fae5",
    "scan": "#fae8ff",
    "write": "#fde68a",
    "assert-ok": "#ddd6fe",
    "assert-failed": "#fecaca",
    "commit": "#bfdbfe",
    "aborted": "#fecaca",
}
MISSING = object()


class ScenarioError(ValueError):
    """Raised when a scenario is malformed."""


class EvaluationError(ValueError):
    """Raised when an expression uses unsupported syntax or names."""


@dataclass
class TransactionRuntime:
    name: str
    steps: List[Dict[str, Any]]
    start_version: int
    snapshot: Dict[str, Any]
    cursor: int = 0
    locals: Dict[str, Any] = field(default_factory=dict)
    read_set: set[str] = field(default_factory=set)
    write_set: set[str] = field(default_factory=set)
    writes: Dict[str, Any] = field(default_factory=dict)
    predicate_reads: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"
    abort_reason: Optional[str] = None

    @property
    def finished(self) -> bool:
        return self.status != "active" or self.cursor >= len(self.steps)


@dataclass
class SimulationResult:
    isolation_level: str
    title: str
    description: str
    final_state: Dict[str, Any]
    final_version: int
    transactions: List[Dict[str, Any]]
    invariants: List[Dict[str, Any]]
    trace: List[Dict[str, Any]]

    @property
    def invariant_violations(self) -> List[Dict[str, Any]]:
        return [item for item in self.invariants if not item["ok"]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "isolation_level": self.isolation_level,
            "title": self.title,
            "description": self.description,
            "final_state": self.final_state,
            "final_version": self.final_version,
            "transactions": self.transactions,
            "invariants": self.invariants,
            "trace": self.trace,
        }


class SafeEvaluator:
    """Very small expression evaluator for scenario assertions and writes."""

    def __init__(self, env: Dict[str, Any]):
        self.env = env

    def evaluate(self, expression: str) -> Any:
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise EvaluationError(f"invalid expression {expression!r}: {exc.msg}") from exc
        return self._eval(tree.body)

    def _eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in self.env:
                raise EvaluationError(f"unknown name {node.id!r}")
            return self.env[node.id]
        if isinstance(node, ast.Call):
            if node.keywords:
                raise EvaluationError("keyword arguments are not supported")
            function = self._eval(node.func)
            if not callable(function):
                raise EvaluationError("attempted to call a non-callable value")
            arguments = [self._eval(argument) for argument in node.args]
            try:
                return function(*arguments)
            except TypeError as exc:
                raise EvaluationError(str(exc)) from exc
        if isinstance(node, ast.BoolOp):
            values = [self._eval(value) for value in node.values]
            if isinstance(node.op, ast.And):
                result = values[0]
                for value in values[1:]:
                    result = result and value
                return result
            if isinstance(node.op, ast.Or):
                result = values[0]
                for value in values[1:]:
                    result = result or value
                return result
        if isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            if isinstance(node.op, ast.Not):
                return not operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.UAdd):
                return +operand
        if isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
        if isinstance(node, ast.Compare):
            left = self._eval(node.left)
            for operator, comparator in zip(node.ops, node.comparators):
                right = self._eval(comparator)
                if isinstance(operator, ast.Eq):
                    ok = left == right
                elif isinstance(operator, ast.NotEq):
                    ok = left != right
                elif isinstance(operator, ast.Lt):
                    ok = left < right
                elif isinstance(operator, ast.LtE):
                    ok = left <= right
                elif isinstance(operator, ast.Gt):
                    ok = left > right
                elif isinstance(operator, ast.GtE):
                    ok = left >= right
                else:
                    raise EvaluationError("unsupported comparison operator")
                if not ok:
                    return False
                left = right
            return True
        raise EvaluationError("unsupported expression syntax")


def load_scenario(path: str | Path) -> Dict[str, Any]:
    scenario_path = Path(path)
    try:
        payload = json.loads(scenario_path.read_text())
    except FileNotFoundError as exc:
        raise ScenarioError(f"scenario not found: {scenario_path}") from exc
    except json.JSONDecodeError as exc:
        raise ScenarioError(f"invalid JSON in {scenario_path}: {exc}") from exc
    validate_scenario(payload)
    return payload


def validate_scenario(scenario: Dict[str, Any]) -> None:
    if not isinstance(scenario, dict):
        raise ScenarioError("scenario must be a JSON object")

    records = scenario.get("records")
    if not isinstance(records, dict) or not records:
        raise ScenarioError("scenario.records must be a non-empty object")

    transactions = scenario.get("transactions")
    if not isinstance(transactions, list) or not transactions:
        raise ScenarioError("scenario.transactions must be a non-empty list")

    names: set[str] = set()
    for transaction in transactions:
        if not isinstance(transaction, dict):
            raise ScenarioError("each transaction must be an object")
        name = transaction.get("name")
        steps = transaction.get("steps")
        if not isinstance(name, str) or not name.strip():
            raise ScenarioError("every transaction needs a non-empty name")
        if name in names:
            raise ScenarioError(f"duplicate transaction name: {name}")
        names.add(name)
        if not isinstance(steps, list) or not steps:
            raise ScenarioError(f"transaction {name!r} needs a non-empty steps list")
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                raise ScenarioError(f"transaction {name!r} step {index} must be an object")
            op = step.get("op")
            if op not in SUPPORTED_STEP_OPS:
                raise ScenarioError(
                    f"transaction {name!r} step {index} uses unsupported op {op!r}"
                )
            if op == "read":
                if not isinstance(step.get("key"), str) or not step["key"]:
                    raise ScenarioError(f"transaction {name!r} step {index} read needs key")
                alias = step.get("as")
                if alias is not None and (not isinstance(alias, str) or not alias.strip()):
                    raise ScenarioError(
                        f"transaction {name!r} step {index} read alias must be a non-empty string"
                    )
            elif op == "scan":
                if not isinstance(step.get("key_prefix"), str) or not step["key_prefix"]:
                    raise ScenarioError(
                        f"transaction {name!r} step {index} scan needs key_prefix"
                    )
                alias = step.get("as")
                if not isinstance(alias, str) or not alias.strip():
                    raise ScenarioError(
                        f"transaction {name!r} step {index} scan needs a non-empty as alias"
                    )
            elif op == "assert":
                if not isinstance(step.get("expr"), str) or not step["expr"].strip():
                    raise ScenarioError(
                        f"transaction {name!r} step {index} assert needs expr"
                    )
            elif op == "write":
                if not isinstance(step.get("key"), str) or not step["key"]:
                    raise ScenarioError(f"transaction {name!r} step {index} write needs key")
                if "expr" not in step and "value" not in step:
                    raise ScenarioError(
                        f"transaction {name!r} step {index} write needs expr or value"
                    )

    schedule = scenario.get("schedule")
    if not isinstance(schedule, list) or not schedule:
        raise ScenarioError("scenario.schedule must be a non-empty list")
    for entry in schedule:
        if entry not in names:
            raise ScenarioError(f"schedule references unknown transaction {entry!r}")

    invariants = scenario.get("invariants", [])
    if not isinstance(invariants, list):
        raise ScenarioError("scenario.invariants must be a list when present")
    for index, invariant in enumerate(invariants, start=1):
        if not isinstance(invariant, dict):
            raise ScenarioError(f"invariant {index} must be an object")
        if not isinstance(invariant.get("name"), str) or not invariant["name"].strip():
            raise ScenarioError(f"invariant {index} needs a non-empty name")
        if not isinstance(invariant.get("expr"), str) or not invariant["expr"].strip():
            raise ScenarioError(f"invariant {index} needs a non-empty expr")


def evaluate_expression(expression: str, env: Dict[str, Any]) -> Any:
    return SafeEvaluator(env).evaluate(expression)


def visible_state(
    transaction: TransactionRuntime,
    committed_state: Dict[str, Any],
    isolation_level: str,
) -> Dict[str, Any]:
    base = dict(committed_state if isolation_level == "read-committed" else transaction.snapshot)
    base.update(transaction.writes)
    return base


def scan_value_equals(step: Dict[str, Any]) -> Any:
    return step["value_equals"] if "value_equals" in step else MISSING


def matches_scan_filter(key: str, value: Any, key_prefix: str, value_equals: Any = MISSING) -> bool:
    return key.startswith(key_prefix) and (value_equals is MISSING or value == value_equals)


def collect_scan_matches(
    state: Dict[str, Any],
    key_prefix: str,
    value_equals: Any = MISSING,
) -> List[tuple[str, Any]]:
    return [
        (key, state[key])
        for key in sorted(state)
        if matches_scan_filter(key, state[key], key_prefix, value_equals)
    ]


def count_prefix_matches(state: Dict[str, Any], prefix: Any, value: Any = MISSING) -> int:
    if not isinstance(prefix, str) or not prefix:
        raise EvaluationError("count_prefix expects a non-empty string prefix")
    return len(collect_scan_matches(state, prefix, value))


def build_evaluation_env(
    state: Dict[str, Any],
    local_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    env = dict(state)
    if local_values:
        env.update(local_values)
    env["count_prefix"] = lambda prefix, value=MISSING: count_prefix_matches(state, prefix, value)
    return env


def format_predicate_label(key_prefix: str, value_equals: Any = MISSING) -> str:
    if value_equals is MISSING:
        return f"prefix={key_prefix}"
    return f"prefix={key_prefix}, value={json.dumps(value_equals, sort_keys=True)}"


def summarize_match_set(matches: List[tuple[str, Any]]) -> str:
    if not matches:
        return "0 matches"
    keys = [key for key, _ in matches]
    if len(keys) <= 2:
        return ", ".join(keys)
    return f"{keys[0]}, {keys[1]}, +{len(keys) - 2} more"


def summarize_predicate_reads(predicate_reads: List[Dict[str, Any]]) -> List[str]:
    labels: List[str] = []
    seen: set[tuple[str, str, str]] = set()
    for predicate in predicate_reads:
        value_equals = predicate["value_equals"] if predicate["has_value_equals"] else MISSING
        label = format_predicate_label(predicate["key_prefix"], value_equals)
        marker = (
            predicate["key_prefix"],
            str(predicate["has_value_equals"]),
            json.dumps(predicate.get("value_equals"), sort_keys=True),
        )
        if marker in seen:
            continue
        seen.add(marker)
        labels.append(label)
    return labels


def collect_predicate_conflicts(
    predicate_reads: List[Dict[str, Any]],
    snapshot_state: Dict[str, Any],
    committed_state: Dict[str, Any],
) -> List[str]:
    conflicts: List[str] = []
    seen: set[tuple[str, str, str]] = set()
    for predicate in predicate_reads:
        marker = (
            predicate["key_prefix"],
            str(predicate["has_value_equals"]),
            json.dumps(predicate.get("value_equals"), sort_keys=True),
        )
        if marker in seen:
            continue
        seen.add(marker)
        value_equals = predicate["value_equals"] if predicate["has_value_equals"] else MISSING
        before_matches = collect_scan_matches(snapshot_state, predicate["key_prefix"], value_equals)
        after_matches = collect_scan_matches(committed_state, predicate["key_prefix"], value_equals)
        if before_matches != after_matches:
            conflicts.append(
                "{label} ({before} -> {after})".format(
                    label=format_predicate_label(predicate["key_prefix"], value_equals),
                    before=summarize_match_set(before_matches),
                    after=summarize_match_set(after_matches),
                )
            )
    return conflicts


def commit_transaction(
    transaction: TransactionRuntime,
    committed_state: Dict[str, Any],
    record_versions: Dict[str, int],
    current_version: int,
    isolation_level: str,
) -> tuple[bool, str, int]:
    changed_keys = {key for key, version in record_versions.items() if version > transaction.start_version}

    if isolation_level == "snapshot":
        conflicting_keys = sorted(transaction.write_set & changed_keys)
        if conflicting_keys:
            reason = "snapshot write-write conflict on " + ", ".join(conflicting_keys)
            transaction.status = "aborted"
            transaction.abort_reason = reason
            return False, reason, current_version
    elif isolation_level == "serializable":
        conflicting_keys = sorted((transaction.read_set | transaction.write_set) & changed_keys)
        predicate_conflicts = collect_predicate_conflicts(
            transaction.predicate_reads,
            transaction.snapshot,
            committed_state,
        )
        if conflicting_keys or predicate_conflicts:
            parts: List[str] = []
            if conflicting_keys:
                parts.append("serializable validation conflict on " + ", ".join(conflicting_keys))
            if predicate_conflicts:
                parts.append("predicate conflict on " + "; ".join(predicate_conflicts))
            reason = " | ".join(parts)
            transaction.status = "aborted"
            transaction.abort_reason = reason
            return False, reason, current_version

    if transaction.writes:
        current_version += 1
        for key, value in transaction.writes.items():
            committed_state[key] = value
            record_versions[key] = current_version

    transaction.status = "committed"
    return True, "committed", current_version


def run_simulation(scenario: Dict[str, Any], isolation_level: str) -> SimulationResult:
    if isolation_level not in SUPPORTED_ISOLATION_LEVELS:
        raise ScenarioError(
            f"unsupported isolation level {isolation_level!r}; expected one of {SUPPORTED_ISOLATION_LEVELS}"
        )

    validate_scenario(scenario)

    metadata = scenario.get("metadata", {})
    title = metadata.get("title", "Unnamed MVCC scenario")
    description = metadata.get("description", "")
    committed_state = dict(scenario["records"])
    record_versions = {key: 0 for key in committed_state}
    current_version = 0
    runtimes: Dict[str, TransactionRuntime] = {}
    transaction_specs = {item["name"]: item for item in scenario["transactions"]}
    trace: List[Dict[str, Any]] = []

    for tick, transaction_name in enumerate(scenario["schedule"], start=1):
        runtime = runtimes.get(transaction_name)
        if runtime is None:
            runtime = TransactionRuntime(
                name=transaction_name,
                steps=transaction_specs[transaction_name]["steps"],
                start_version=current_version,
                snapshot=dict(committed_state),
            )
            runtimes[transaction_name] = runtime
            trace.append(
                {
                    "event": "begin",
                    "tick": tick,
                    "transaction": transaction_name,
                    "start_version": current_version,
                }
            )

        if runtime.finished:
            raise ScenarioError(
                f"schedule references transaction {transaction_name!r} after it finished"
            )

        step = runtime.steps[runtime.cursor]
        op = step["op"]
        step_number = runtime.cursor + 1
        state_view = visible_state(runtime, committed_state, isolation_level)

        if op == "read":
            key = step["key"]
            if key not in state_view:
                raise ScenarioError(f"transaction {transaction_name!r} read missing key {key!r}")
            value = state_view[key]
            alias = step.get("as", key)
            runtime.locals[alias] = value
            runtime.read_set.add(key)
            trace.append(
                {
                    "event": "step",
                    "tick": tick,
                    "transaction": transaction_name,
                    "step": step_number,
                    "op": op,
                    "key": key,
                    "alias": alias,
                    "value": value,
                }
            )
        elif op == "scan":
            alias = step["as"]
            value_equals = scan_value_equals(step)
            matches = collect_scan_matches(state_view, step["key_prefix"], value_equals)
            count = len(matches)
            runtime.locals[alias] = count
            runtime.read_set.update(key for key, _ in matches)
            runtime.predicate_reads.append(
                {
                    "key_prefix": step["key_prefix"],
                    "has_value_equals": "value_equals" in step,
                    "value_equals": step.get("value_equals"),
                }
            )
            trace.append(
                {
                    "event": "step",
                    "tick": tick,
                    "transaction": transaction_name,
                    "step": step_number,
                    "op": op,
                    "key_prefix": step["key_prefix"],
                    "alias": alias,
                    "count": count,
                    "matched_keys": [key for key, _ in matches],
                    **({"value_equals": step["value_equals"]} if "value_equals" in step else {}),
                }
            )
        elif op == "assert":
            env = build_evaluation_env(state_view, runtime.locals)
            result = bool(evaluate_expression(step["expr"], env))
            trace.append(
                {
                    "event": "step",
                    "tick": tick,
                    "transaction": transaction_name,
                    "step": step_number,
                    "op": op,
                    "expr": step["expr"],
                    "result": result,
                }
            )
            if not result:
                runtime.status = "aborted"
                runtime.abort_reason = step.get(
                    "message", f"assertion failed: {step['expr']}"
                )
                trace.append(
                    {
                        "event": "commit",
                        "tick": tick,
                        "transaction": transaction_name,
                        "status": "aborted",
                        "reason": runtime.abort_reason,
                    }
                )
        elif op == "write":
            key = step["key"]
            env = build_evaluation_env(state_view, runtime.locals)
            value = step.get("value")
            if "expr" in step:
                value = evaluate_expression(step["expr"], env)
            runtime.writes[key] = value
            runtime.write_set.add(key)
            runtime.locals[key] = value
            trace.append(
                {
                    "event": "step",
                    "tick": tick,
                    "transaction": transaction_name,
                    "step": step_number,
                    "op": op,
                    "key": key,
                    "value": value,
                }
            )
        else:
            raise ScenarioError(f"unsupported step op {op!r}")

        runtime.cursor += 1
        if runtime.status == "active" and runtime.cursor == len(runtime.steps):
            committed, reason, current_version = commit_transaction(
                runtime,
                committed_state,
                record_versions,
                current_version,
                isolation_level,
            )
            trace.append(
                {
                    "event": "commit",
                    "tick": tick,
                    "transaction": transaction_name,
                    "status": runtime.status,
                    "reason": reason,
                    "version": current_version,
                    "writes": dict(runtime.writes),
                }
            )
            if not committed:
                continue

    transactions: List[Dict[str, Any]] = []
    for transaction in scenario["transactions"]:
        runtime = runtimes.get(transaction["name"])
        if runtime is None:
            runtime = TransactionRuntime(
                name=transaction["name"],
                steps=transaction["steps"],
                start_version=current_version,
                snapshot=dict(committed_state),
                status="not-started",
            )
        elif runtime.status == "active":
            runtime.status = "incomplete"
            runtime.abort_reason = "schedule ended before transaction finished"
        transactions.append(
            {
                "name": runtime.name,
                "status": runtime.status,
                "abort_reason": runtime.abort_reason,
                "reads": sorted(runtime.read_set),
                "predicate_reads": summarize_predicate_reads(runtime.predicate_reads),
                "writes": dict(runtime.writes),
                "start_version": runtime.start_version,
            }
        )

    invariants: List[Dict[str, Any]] = []
    for invariant in scenario.get("invariants", []):
        ok = bool(evaluate_expression(invariant["expr"], build_evaluation_env(dict(committed_state))))
        invariants.append(
            {
                "name": invariant["name"],
                "expr": invariant["expr"],
                "ok": ok,
                "message": invariant.get("message", ""),
            }
        )

    return SimulationResult(
        isolation_level=isolation_level,
        title=title,
        description=description,
        final_state=committed_state,
        final_version=current_version,
        transactions=transactions,
        invariants=invariants,
        trace=trace,
    )


def render_run_text(result: SimulationResult) -> str:
    lines = [
        f"Scenario: {result.title}",
        f"Isolation: {result.isolation_level}",
    ]
    if result.description:
        lines.append(f"Description: {result.description}")
    lines.append("Final state:")
    for key, value in result.final_state.items():
        lines.append(f"  - {key}: {value}")
    lines.append("Transactions:")
    for transaction in result.transactions:
        line = f"  - {transaction['name']}: {transaction['status']}"
        if transaction["abort_reason"]:
            line += f" ({transaction['abort_reason']})"
        if transaction["predicate_reads"]:
            line += f" predicate_reads={json.dumps(transaction['predicate_reads'])}"
        if transaction["writes"]:
            write_label = "writes" if transaction["status"] == "committed" else "buffered_writes"
            line += f" {write_label}={json.dumps(transaction['writes'], sort_keys=True)}"
        lines.append(line)
    if result.invariants:
        lines.append("Invariants:")
        for invariant in result.invariants:
            badge = "ok" if invariant["ok"] else "FAILED"
            lines.append(
                f"  - {invariant['name']}: {badge} ({invariant['expr']})"
            )
    return "\n".join(lines)


def compare_scenario(scenario: Dict[str, Any]) -> Dict[str, SimulationResult]:
    return {
        level: run_simulation(scenario, level)
        for level in SUPPORTED_ISOLATION_LEVELS
    }


def render_compare_text(results: Dict[str, SimulationResult]) -> str:
    lines = ["MVCC isolation comparison:"]
    for level in SUPPORTED_ISOLATION_LEVELS:
        result = results[level]
        violations = len(result.invariant_violations)
        aborted = sum(1 for item in result.transactions if item["status"] == "aborted")
        lines.append(
            f"- {level}: version={result.final_version}, aborted={aborted}, invariant_violations={violations}, final_state={json.dumps(result.final_state, sort_keys=True)}"
        )
    return "\n".join(lines)


def render_compare_markdown(results: Dict[str, SimulationResult]) -> str:
    scenario = next(iter(results.values()))
    lines = [f"# {scenario.title} — isolation comparison", ""]
    if scenario.description:
        lines.append(scenario.description)
        lines.append("")
    lines.append("| Isolation | Final version | Aborted txs | Invariant status | Final state |")
    lines.append("| --- | ---: | ---: | --- | --- |")
    for level in SUPPORTED_ISOLATION_LEVELS:
        result = results[level]
        aborted = sum(1 for item in result.transactions if item["status"] == "aborted")
        invariant_status = (
            "all pass"
            if not result.invariant_violations
            else ", ".join(item["name"] for item in result.invariant_violations)
        )
        lines.append(
            "| {level} | {version} | {aborted} | {status} | `{state}` |".format(
                level=level,
                version=result.final_version,
                aborted=aborted,
                status=invariant_status,
                state=json.dumps(result.final_state, sort_keys=True),
            )
        )
    lines.append("")
    for level in SUPPORTED_ISOLATION_LEVELS:
        result = results[level]
        lines.append(f"## {level}")
        lines.append("")
        for transaction in result.transactions:
            summary = f"- `{transaction['name']}` → **{transaction['status']}**"
            if transaction["abort_reason"]:
                summary += f" — {transaction['abort_reason']}"
            if transaction["predicate_reads"]:
                summary += f"; predicate reads `{json.dumps(transaction['predicate_reads'])}`"
            if transaction["writes"]:
                write_label = "writes" if transaction["status"] == "committed" else "buffered writes"
                summary += f"; {write_label} `{json.dumps(transaction['writes'], sort_keys=True)}`"
            lines.append(summary)
        if result.invariants:
            lines.append("")
            lines.append("Invariant checks:")
            for invariant in result.invariants:
                badge = "✅" if invariant["ok"] else "❌"
                detail = invariant["message"] or invariant["expr"]
                lines.append(f"- {badge} `{invariant['name']}` — {detail}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def truncate_text(value: Any, limit: int = 42) -> str:
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def svg_text_block(x: float, y: float, lines: List[str], css_class: str = "event-text") -> str:
    tspans = [
        f'<tspan x="{x:.1f}" dy="{14 if index else 0}">{escape(line)}</tspan>'
        for index, line in enumerate(lines)
    ]
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{css_class}">' + "".join(tspans) + "</text>"


def event_card_lines(event: Dict[str, Any]) -> tuple[str, List[str], str]:
    event_type = event["event"]
    if event_type == "begin":
        return "begin", [f"snapshot v{event['start_version']}"], EVENT_COLORS["begin"]
    if event_type == "step":
        op = event["op"]
        if op == "read":
            return (
                f"read {event['key']}",
                [f"{event['alias']} = {truncate_text(event['value'], 26)}"],
                EVENT_COLORS["read"],
            )
        if op == "scan":
            return (
                f"scan {truncate_text(event['key_prefix'], 18)}",
                [f"{event['alias']} = {event['count']}"],
                EVENT_COLORS["scan"],
            )
        if op == "write":
            return (
                f"write {event['key']}",
                [truncate_text(event['value'], 28)],
                EVENT_COLORS["write"],
            )
        if op == "assert":
            passed = bool(event["result"])
            label = "assert ✓" if passed else "assert ✕"
            detail = truncate_text(event["expr"], 28)
            color = EVENT_COLORS["assert-ok" if passed else "assert-failed"]
            return label, [detail], color
    if event_type == "commit":
        if event["status"] == "committed":
            detail = f"v{event['version']}"
            if event.get("writes"):
                detail += " · " + truncate_text(event["writes"], 22)
            return "commit ✓", [detail], EVENT_COLORS["commit"]
        return "abort", [truncate_text(event["reason"], 30)], EVENT_COLORS["aborted"]
    return event_type, [], "#e5e7eb"


def render_timeline_svg(result: SimulationResult) -> str:
    transactions = [item["name"] for item in result.transactions]
    trace = result.trace
    max_tick = max((item.get("tick", 0) for item in trace), default=0)
    tick_width = 176
    left_margin = 180
    right_margin = 48
    top_margin = 88
    row_height = 106
    event_width = 132
    event_height = 30
    event_gap = 8
    lane_map = {name: index for index, name in enumerate(transactions)}
    slot_counts: Dict[tuple[str, int], int] = {}
    for item in trace:
        key = (item["transaction"], item["tick"])
        slot_counts[key] = slot_counts.get(key, 0) + 1
    slot_offsets = {key: 0 for key in slot_counts}
    version_events = [
        item
        for item in trace
        if item["event"] == "commit" and item.get("status") == "committed" and item.get("writes")
    ]
    version_row_y = top_margin + len(transactions) * row_height + 18
    summary_y = version_row_y + 88
    summary_lines = [
        f"Final state: {json.dumps(result.final_state, sort_keys=True)}",
        "Invariants: "
        + (
            "; ".join(
                f"{item['name']}={'ok' if item['ok'] else 'FAILED'}" for item in result.invariants
            )
            if result.invariants
            else "none"
        ),
    ]
    width = left_margin + max(max_tick, 1) * tick_width + right_margin
    height = summary_y + 76 + max(0, len(summary_lines) - 1) * 16

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="timeline-title timeline-desc">',
        f"<title id=\"timeline-title\">{escape(result.title)} timeline</title>",
        f"<desc id=\"timeline-desc\">{escape(result.description or 'Transaction schedule timeline')}</desc>",
        "<style>"
        "text { font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; fill: #0f172a; }"
        ".title { font-size: 24px; font-weight: 700; }"
        ".subtitle { font-size: 13px; fill: #475569; }"
        ".lane-label { font-size: 13px; font-weight: 600; }"
        ".tick-label { font-size: 12px; fill: #64748b; }"
        ".event-text { font-size: 10.5px; font-weight: 600; }"
        ".summary-text { font-size: 12px; fill: #334155; }"
        ".grid { stroke: #e2e8f0; stroke-width: 1; }"
        ".lane { fill: #ffffff; stroke: #cbd5e1; stroke-width: 1; }"
        ".connector { fill: none; stroke: #94a3b8; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }"
        ".event-card { stroke: #475569; stroke-width: 1; }"
        ".version-band { fill: #eff6ff; stroke: #93c5fd; stroke-width: 1; }"
        "</style>",
        f'<text x="24" y="36" class="title">{escape(result.title)}</text>',
        f'<text x="24" y="58" class="subtitle">Isolation: {escape(result.isolation_level)} · ticks: {max_tick} · final version: {result.final_version}</text>',
    ]

    for tick in range(1, max(max_tick, 1) + 1):
        x = left_margin + (tick - 1) * tick_width + tick_width / 2
        parts.append(f'<line x1="{x:.1f}" y1="72" x2="{x:.1f}" y2="{summary_y - 16:.1f}" class="grid" />')
        parts.append(f'<text x="{x - 12:.1f}" y="82" class="tick-label">t{tick}</text>')

    for index, name in enumerate(transactions):
        y = top_margin + index * row_height
        parts.append(
            f'<rect x="16" y="{y:.1f}" width="{width - 32}" height="{row_height - 10}" class="lane" />'
        )
        parts.append(f'<text x="28" y="{y + 34:.1f}" class="lane-label">{escape(name)}</text>')

    connector_points: Dict[str, List[str]] = {name: [] for name in transactions}
    card_parts: List[str] = []
    for item in trace:
        tx_name = item["transaction"]
        lane_index = lane_map[tx_name]
        key = (tx_name, item["tick"])
        slot_index = slot_offsets[key]
        slot_offsets[key] += 1
        slot_base = top_margin + lane_index * row_height + 10
        box_x = left_margin + (item["tick"] - 1) * tick_width + (tick_width - event_width) / 2
        box_y = slot_base + slot_index * (event_height + event_gap)
        center_x = box_x + event_width / 2
        center_y = box_y + event_height / 2
        connector_points[tx_name].append(f"{center_x:.1f},{center_y:.1f}")
        header, details, color = event_card_lines(item)
        card_parts.append(
            f'<rect x="{box_x:.1f}" y="{box_y:.1f}" width="{event_width}" height="{event_height}" rx="10" ry="10" fill="{color}" class="event-card" />'
        )
        card_parts.append(svg_text_block(box_x + 8, box_y + 11, [header, *details]))

    for points in connector_points.values():
        if len(points) >= 2:
            parts.append(f'<polyline points="{" ".join(points)}" class="connector" />')
    parts.extend(card_parts)

    parts.append(
        f'<rect x="16" y="{version_row_y:.1f}" width="{width - 32}" height="56" rx="10" ry="10" class="version-band" />'
    )
    parts.append(f'<text x="28" y="{version_row_y + 24:.1f}" class="lane-label">Committed versions</text>')
    if version_events:
        for item in version_events:
            box_x = left_margin + (item["tick"] - 1) * tick_width + (tick_width - event_width) / 2
            parts.append(
                f'<rect x="{box_x:.1f}" y="{version_row_y + 7:.1f}" width="{event_width}" height="34" rx="10" ry="10" fill="#dbeafe" class="event-card" />'
            )
            version_lines = [f"v{item['version']}", truncate_text(item['writes'], 24)]
            parts.append(svg_text_block(box_x + 10, version_row_y + 20, version_lines))
    else:
        parts.append(f'<text x="200" y="{version_row_y + 28:.1f}" class="summary-text">No committed writes recorded.</text>')

    parts.append(f'<text x="24" y="{summary_y:.1f}" class="lane-label">Summary</text>')
    parts.append(svg_text_block(24, summary_y + 22, summary_lines, css_class="summary-text"))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_text_output(path: str | Path, contents: str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(contents)
    return output_path


def command_validate(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario)
    print(
        json.dumps(
            {
                "status": "ok",
                "transactions": [item["name"] for item in scenario["transactions"]],
                "schedule_length": len(scenario["schedule"]),
                "invariants": [item["name"] for item in scenario.get("invariants", [])],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def command_run(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario)
    result = run_simulation(scenario, args.isolation)
    payload = result.to_dict()
    timeline_output: Optional[Path] = None
    if args.timeline_svg_out:
        timeline_output = write_text_output(args.timeline_svg_out, render_timeline_svg(result))
        payload["_meta"] = {"timeline_svg_output": str(timeline_output)}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_run_text(result))
        if timeline_output:
            print(f"Timeline SVG: {timeline_output}")
    return 0


def command_compare(args: argparse.Namespace) -> int:
    scenario = load_scenario(args.scenario)
    results = compare_scenario(scenario)
    if args.markdown_out:
        write_text_output(args.markdown_out, render_compare_markdown(results))
    timeline_outputs: Dict[str, str] = {}
    if args.timeline_svg_dir:
        output_dir = Path(args.timeline_svg_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        scenario_stem = Path(args.scenario).stem
        for level, result in results.items():
            filename = f"{scenario_stem}_{level.replace('-', '_')}_timeline.svg"
            output_path = write_text_output(output_dir / filename, render_timeline_svg(result))
            timeline_outputs[level] = str(output_path)
    payload = {level: result.to_dict() for level, result in results.items()}
    if timeline_outputs:
        payload["_meta"] = {"timeline_svg_outputs": timeline_outputs}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_compare_text(results))
        if timeline_outputs:
            print("Timeline SVGs:")
            for level in SUPPORTED_ISOLATION_LEVELS:
                print(f"- {level}: {timeline_outputs[level]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MVCC isolation level simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate a scenario JSON file")
    validate_parser.add_argument("scenario")
    validate_parser.set_defaults(func=command_validate)

    run_parser = subparsers.add_parser("run", help="run one scenario under one isolation level")
    run_parser.add_argument("scenario")
    run_parser.add_argument(
        "--isolation",
        choices=SUPPORTED_ISOLATION_LEVELS,
        default="snapshot",
        help="isolation level to simulate",
    )
    run_parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    run_parser.add_argument(
        "--timeline-svg-out",
        help="optional path for a self-contained SVG schedule export",
    )
    run_parser.set_defaults(func=command_run)

    compare_parser = subparsers.add_parser(
        "compare", help="run the same scenario across all supported isolation levels"
    )
    compare_parser.add_argument("scenario")
    compare_parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    compare_parser.add_argument(
        "--markdown-out",
        help="optional path for a Markdown comparison report",
    )
    compare_parser.add_argument(
        "--timeline-svg-dir",
        help="optional directory for per-isolation SVG schedule exports",
    )
    compare_parser.set_defaults(func=command_compare)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
