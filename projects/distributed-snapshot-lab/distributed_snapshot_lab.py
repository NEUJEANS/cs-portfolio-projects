from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Transfer:
    sender: str
    receiver: str
    amount: int
    label: str

    def to_dict(self) -> dict[str, object]:
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "label": self.label,
        }


@dataclass
class SnapshotRecord:
    initiator: str
    balances: dict[str, int] = field(default_factory=dict)
    process_statuses: dict[str, str] = field(default_factory=dict)
    channel_messages: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    markers_seen: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    closed_channels: set[str] = field(default_factory=set)
    completed_processes: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, object]:
        return {
            "initiator": self.initiator,
            "balances": dict(sorted(self.balances.items())),
            "process_statuses": dict(sorted(self.process_statuses.items())),
            "channel_messages": {
                channel: messages for channel, messages in sorted(self.channel_messages.items())
            },
            "markers_seen": {
                process: sorted(senders) for process, senders in sorted(self.markers_seen.items())
            },
            "closed_channels": sorted(self.closed_channels),
            "completed_processes": sorted(self.completed_processes),
        }


class DistributedBank:
    def __init__(self, balances: dict[str, int]) -> None:
        if not balances:
            raise ValueError("balances must contain at least one process")
        if any(amount < 0 for amount in balances.values()):
            raise ValueError("balances must be non-negative")
        self.processes = tuple(sorted(balances))
        self.balances = {process: balances[process] for process in self.processes}
        self.process_statuses = {process: "up" for process in self.processes}
        self.in_flight: dict[str, deque[Transfer]] = {
            self.channel_name(sender, receiver): deque()
            for sender in self.processes
            for receiver in self.processes
            if sender != receiver
        }
        self.channel_statuses = {channel: "up" for channel in self.in_flight}
        self.timeline: list[dict[str, object]] = []

    @staticmethod
    def channel_name(sender: str, receiver: str) -> str:
        return f"{sender}->{receiver}"

    @staticmethod
    def parse_channel_name(channel: str) -> tuple[str, str]:
        sender, separator, receiver = channel.partition("->")
        if not separator or not sender or not receiver:
            raise ValueError("channel names must use sender->receiver format")
        return sender, receiver

    def fail_process(self, process: str, reason: str | None = None) -> None:
        self._require_process(process)
        if self.process_statuses[process] == "down":
            raise ValueError(f"process {process} is already down")
        self.process_statuses[process] = "down"
        event = {"event": "fail", "process": process, "process_statuses": self.current_process_statuses()}
        if reason:
            event["reason"] = reason
        self.timeline.append(event)

    def recover_process(self, process: str, reason: str | None = None) -> None:
        self._require_process(process)
        if self.process_statuses[process] == "up":
            raise ValueError(f"process {process} is already up")
        self.process_statuses[process] = "up"
        event = {"event": "recover", "process": process, "process_statuses": self.current_process_statuses()}
        if reason:
            event["reason"] = reason
        self.timeline.append(event)

    def fail_link(self, sender: str, receiver: str, reason: str | None = None) -> None:
        channel = self.channel_name(sender, receiver)
        self._require_channel_up(channel)
        self.channel_statuses[channel] = "down"
        event = {"event": "link_fail", "channel": channel, "channel_statuses": self.current_channel_statuses()}
        if reason:
            event["reason"] = reason
        self.timeline.append(event)

    def recover_link(self, sender: str, receiver: str, reason: str | None = None) -> None:
        channel = self.channel_name(sender, receiver)
        self._require_channel_known(channel)
        if self.channel_statuses[channel] == "up":
            raise ValueError(f"channel {channel} is already up")
        self.channel_statuses[channel] = "up"
        event = {"event": "link_recover", "channel": channel, "channel_statuses": self.current_channel_statuses()}
        if reason:
            event["reason"] = reason
        self.timeline.append(event)

    def transfer(self, sender: str, receiver: str, amount: int, label: str) -> Transfer:
        self._require_process(sender)
        self._require_process(receiver)
        self._require_process_up(sender)
        if sender == receiver:
            raise ValueError("sender and receiver must differ")
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._require_channel_up(self.channel_name(sender, receiver))
        if self.balances[sender] < amount:
            raise ValueError("sender has insufficient balance")
        transfer = Transfer(sender=sender, receiver=receiver, amount=amount, label=label)
        self.balances[sender] -= amount
        self.in_flight[self.channel_name(sender, receiver)].append(transfer)
        self.timeline.append(
            {
                "event": "send",
                **transfer.to_dict(),
                "balances": self.current_balances(),
                "process_statuses": self.current_process_statuses(),
                "channel_statuses": self.current_channel_statuses(),
            }
        )
        return transfer

    def deliver(self, sender: str, receiver: str) -> Transfer:
        self._require_process(sender)
        self._require_process(receiver)
        self._require_process_up(receiver)
        channel = self.channel_name(sender, receiver)
        self._require_channel_up(channel)
        queue = self.in_flight[channel]
        if not queue:
            raise ValueError(f"no in-flight transfer on channel {channel}")
        transfer = queue.popleft()
        self.balances[receiver] += transfer.amount
        self.timeline.append(
            {
                "event": "deliver",
                **transfer.to_dict(),
                "balances": self.current_balances(),
                "process_statuses": self.current_process_statuses(),
                "channel_statuses": self.current_channel_statuses(),
            }
        )
        return transfer

    def current_balances(self) -> dict[str, int]:
        return dict(sorted(self.balances.items()))

    def current_process_statuses(self) -> dict[str, str]:
        return dict(sorted(self.process_statuses.items()))

    def current_channel_statuses(self) -> dict[str, str]:
        return dict(sorted(self.channel_statuses.items()))

    def total_money(self) -> int:
        return sum(self.balances.values()) + sum(
            transfer.amount
            for queue in self.in_flight.values()
            for transfer in queue
        )

    def snapshot(self, initiator: str, marker_delay_overrides: dict[str, int] | None = None) -> dict[str, object]:
        self._require_process(initiator)
        self._require_process_up(initiator)
        record = SnapshotRecord(initiator=initiator)
        marker_delay_overrides = marker_delay_overrides or {}
        self._validate_marker_delay_overrides(marker_delay_overrides)
        incoming_channels = {
            process: [self.channel_name(sender, process) for sender in self.processes if sender != process]
            for process in self.processes
        }
        unavailable_incoming_channels = {
            process: {
                channel
                for channel in incoming_channels[process]
                if self.channel_statuses[channel] != "up"
            }
            for process in self.processes
        }
        marker_events: list[dict[str, object]] = []
        pending = deque([(0, initiator, None)])
        seen = set()

        while pending:
            time, process, marker_sender = pending.popleft()
            event_key = (time, process, marker_sender)
            if event_key in seen:
                continue
            seen.add(event_key)

            if process not in record.balances:
                record.balances[process] = self.balances[process]
                record.process_statuses[process] = self.process_statuses[process]
                if marker_sender is None:
                    closed = set()
                else:
                    closed = {self.channel_name(marker_sender, process)}
                    record.markers_seen[process].append(marker_sender)
                record.closed_channels.update(closed)
                record.closed_channels.update(unavailable_incoming_channels[process])
                if set(incoming_channels[process]) <= record.closed_channels:
                    record.completed_processes.add(process)
                if self.process_statuses[process] != "up":
                    continue
                for target in self.processes:
                    if target == process or self.process_statuses[target] != "up":
                        continue
                    channel = self.channel_name(process, target)
                    if self.channel_statuses[channel] != "up":
                        continue
                    delay = marker_delay_overrides.get(channel, 0)
                    marker_events.append(
                        {
                            "event": "marker_sent",
                            "time": time,
                            "sender": process,
                            "receiver": target,
                            "channel": channel,
                        }
                    )
                    pending.append((time + delay, target, process))
            else:
                if marker_sender is None:
                    continue
                record.markers_seen[process].append(marker_sender)
                record.closed_channels.add(self.channel_name(marker_sender, process))
                if set(incoming_channels[process]) <= record.closed_channels:
                    record.completed_processes.add(process)

        for process in self.processes:
            record.balances.setdefault(process, self.balances[process])
            record.process_statuses.setdefault(process, self.process_statuses[process])

        channel_messages: dict[str, list[dict[str, object]]] = {}
        adjusted_balances = dict(record.balances)
        for receiver in self.processes:
            receiver_marker_times = {}
            for sender in self.processes:
                if sender == receiver:
                    continue
                channel = self.channel_name(sender, receiver)
                receiver_marker_times[channel] = marker_delay_overrides.get(channel, 0)
            first_marker_time = min(receiver_marker_times.values(), default=0)
            for sender in self.processes:
                if sender == receiver:
                    continue
                channel = self.channel_name(sender, receiver)
                transfers = [transfer.to_dict() for transfer in self.in_flight[channel]]
                if receiver == initiator:
                    adjusted_balances[receiver] += sum(transfer["amount"] for transfer in transfers)
                    continue
                arrival_time = receiver_marker_times[channel]
                if arrival_time > first_marker_time:
                    if transfers:
                        channel_messages[channel] = transfers
                else:
                    adjusted_balances[receiver] += sum(transfer["amount"] for transfer in transfers)
        record.balances = adjusted_balances
        record.channel_messages = channel_messages
        snapshot_total = sum(record.balances.values()) + sum(
            message["amount"]
            for messages in record.channel_messages.values()
            for message in messages
        )
        return {
            "initiator": initiator,
            "balances": dict(sorted(record.balances.items())),
            "process_statuses": dict(sorted(record.process_statuses.items())),
            "channel_statuses": self.current_channel_statuses(),
            "channel_messages": record.channel_messages,
            "markers": sorted(
                marker_events,
                key=lambda event: (event["time"], event["sender"], event["receiver"]),
            ),
            "completed_processes": sorted(record.completed_processes),
            "snapshot_total": snapshot_total,
            "system_total": self.total_money(),
            "consistent": snapshot_total == self.total_money(),
            "timeline": list(self.timeline),
        }

    def concurrent_snapshots(
        self,
        snapshot_initiators: dict[str, str],
        marker_delay_overrides: dict[str, dict[str, int]] | None = None,
    ) -> dict[str, object]:
        if not snapshot_initiators:
            raise ValueError("snapshot_initiators must contain at least one snapshot")
        marker_delay_overrides = marker_delay_overrides or {}
        snapshots: dict[str, dict[str, object]] = {}
        for snapshot_id, initiator in sorted(snapshot_initiators.items()):
            if not snapshot_id.strip():
                raise ValueError("snapshot ids must be non-empty")
            self._require_process(initiator)
            per_snapshot_overrides = marker_delay_overrides.get(snapshot_id, {})
            result = self.snapshot(initiator, marker_delay_overrides=per_snapshot_overrides)
            result["snapshot_id"] = snapshot_id
            snapshots[snapshot_id] = result

        return {
            "snapshots": snapshots,
            "system_total": self.total_money(),
            "all_consistent": all(result["consistent"] for result in snapshots.values()),
            "timeline": list(self.timeline),
            "process_statuses": self.current_process_statuses(),
            "channel_statuses": self.current_channel_statuses(),
        }

    def run_script(
        self,
        operations: Sequence[dict[str, object]],
        marker_delay_overrides: dict[str, int] | None = None,
    ) -> dict[str, object]:
        snapshots: list[dict[str, object]] = []
        for index, operation in enumerate(operations, start=1):
            op = str(operation.get("op", "")).strip().lower()
            if op == "send":
                self.transfer(
                    str(operation["sender"]),
                    str(operation["receiver"]),
                    int(operation["amount"]),
                    str(operation["label"]),
                )
            elif op == "deliver":
                self.deliver(str(operation["sender"]), str(operation["receiver"]))
            elif op == "fail":
                self.fail_process(str(operation["process"]), reason=_optional_text(operation.get("reason")))
            elif op == "recover":
                self.recover_process(str(operation["process"]), reason=_optional_text(operation.get("reason")))
            elif op == "link-fail":
                self.fail_link(
                    str(operation["sender"]),
                    str(operation["receiver"]),
                    reason=_optional_text(operation.get("reason")),
                )
            elif op == "link-recover":
                self.recover_link(
                    str(operation["sender"]),
                    str(operation["receiver"]),
                    reason=_optional_text(operation.get("reason")),
                )
            elif op == "snapshot":
                initiator = str(operation["initiator"])
                snapshot_id = _optional_text(operation.get("snapshot_id")) or f"snapshot-{len(snapshots) + 1}"
                result = self.snapshot(initiator, marker_delay_overrides=marker_delay_overrides)
                result["snapshot_id"] = snapshot_id
                result["step"] = index
                snapshots.append(result)
            else:
                raise ValueError(f"unsupported script op: {op}")

        return {
            "operations": list(operations),
            "snapshots": snapshots,
            "balances": self.current_balances(),
            "process_statuses": self.current_process_statuses(),
            "channel_statuses": self.current_channel_statuses(),
            "in_flight": {
                channel: [transfer.to_dict() for transfer in queue]
                for channel, queue in sorted(self.in_flight.items())
                if queue
            },
            "system_total": self.total_money(),
            "timeline": list(self.timeline),
        }

    def _validate_marker_delay_overrides(self, marker_delay_overrides: dict[str, int]) -> None:
        for channel, delay in marker_delay_overrides.items():
            sender, receiver = self.parse_channel_name(channel)
            self._require_process(sender)
            self._require_process(receiver)
            if sender == receiver:
                raise ValueError("marker delays cannot target self channels")
            if delay < 0:
                raise ValueError("marker delay must be non-negative")

    def _require_process(self, process: str) -> None:
        if process not in self.balances:
            raise ValueError(f"unknown process: {process}")

    def _require_channel_known(self, channel: str) -> None:
        sender, receiver = self.parse_channel_name(channel)
        self._require_process(sender)
        self._require_process(receiver)
        if sender == receiver:
            raise ValueError("channels must connect two distinct processes")

    def _require_channel_up(self, channel: str) -> None:
        self._require_channel_known(channel)
        if self.channel_statuses[channel] != "up":
            raise ValueError(f"channel {channel} is down")

    def _require_process_up(self, process: str) -> None:
        self._require_process(process)
        if self.process_statuses[process] != "up":
            raise ValueError(f"process {process} is down")


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _safe_mermaid_text(value: object) -> str:
    text = str(value)
    return text.replace("\n", " ").replace('"', "'")


def _svg_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _slugify_filename(value: object) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")
    return normalized or "snapshot"


def _wrap_svg_text(text: object, *, max_chars: int = 30) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def parse_balances(raw: str) -> dict[str, int]:
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not payload:
        raise ValueError("balances must be a non-empty JSON object")
    return {str(process): int(amount) for process, amount in payload.items()}


def parse_transfer(raw: str) -> tuple[str, str, int, str]:
    parts = raw.split(":", 3)
    if len(parts) != 4:
        raise ValueError("transfers must use sender:receiver:amount:label")
    sender, receiver, amount_text, label = parts
    return sender, receiver, int(amount_text), label


def parse_marker_delay(raw: str) -> tuple[str, int]:
    channel, separator, delay_text = raw.partition("=")
    if not separator:
        raise ValueError("marker delay must use sender->receiver=delay format")
    delay = int(delay_text)
    if delay < 0:
        raise ValueError("marker delay must be non-negative")
    return channel, delay


def parse_snapshot_spec(raw: str) -> tuple[str, str]:
    snapshot_id, separator, initiator = raw.partition(":")
    if not separator or not snapshot_id.strip() or not initiator.strip():
        raise ValueError("snapshots must use snapshot_id:initiator format")
    return snapshot_id.strip(), initiator.strip()


def parse_snapshot_specs(raw_values: Sequence[str]) -> dict[str, str]:
    snapshot_initiators: dict[str, str] = {}
    for raw in raw_values:
        snapshot_id, initiator = parse_snapshot_spec(raw)
        if snapshot_id in snapshot_initiators:
            raise ValueError(f"duplicate snapshot id: {snapshot_id}")
        snapshot_initiators[snapshot_id] = initiator
    return snapshot_initiators


def parse_scoped_marker_delay(raw: str) -> tuple[str, str, int]:
    snapshot_id, separator, remainder = raw.partition(":")
    if not separator or not snapshot_id.strip():
        raise ValueError("scoped marker delay must use snapshot_id:sender->receiver=delay format")
    channel, delay = parse_marker_delay(remainder)
    return snapshot_id.strip(), channel, delay


def parse_script(raw: str) -> list[dict[str, object]]:
    payload = json.loads(raw)
    if not isinstance(payload, list) or not payload:
        raise ValueError("script must be a non-empty JSON array")
    normalized: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("each script operation must be a JSON object")
        normalized.append(item)
    return normalized


def render_mermaid(result: dict[str, object], processes: Iterable[str]) -> str:
    ordered_processes = list(sorted(set(str(process) for process in processes)))
    lines = ["sequenceDiagram"]
    for process in ordered_processes:
        lines.append(f"    participant {process}")

    for event in result.get("timeline", []):
        if event.get("event") == "send":
            sender = _safe_mermaid_text(event["sender"])
            receiver = _safe_mermaid_text(event["receiver"])
            label = _safe_mermaid_text(event["label"])
            amount = event["amount"]
            lines.append(f"    {sender}->>{receiver}: transfer {amount} ({label})")
        elif event.get("event") == "deliver":
            sender = _safe_mermaid_text(event["sender"])
            receiver = _safe_mermaid_text(event["receiver"])
            label = _safe_mermaid_text(event["label"])
            amount = event["amount"]
            lines.append(f"    Note over {receiver}: apply {amount} from {sender} ({label})")
        elif event.get("event") == "fail":
            process = _safe_mermaid_text(event["process"])
            reason = _optional_text(event.get("reason"))
            suffix = f" ({_safe_mermaid_text(reason)})" if reason else ""
            lines.append(f"    Note over {process}: FAIL{suffix}")
        elif event.get("event") == "recover":
            process = _safe_mermaid_text(event["process"])
            reason = _optional_text(event.get("reason"))
            suffix = f" ({_safe_mermaid_text(reason)})" if reason else ""
            lines.append(f"    Note over {process}: RECOVER{suffix}")
        elif event.get("event") == "link_fail":
            sender, receiver = str(event["channel"]).split("->", 1)
            reason = _optional_text(event.get("reason"))
            suffix = f" ({_safe_mermaid_text(reason)})" if reason else ""
            lines.append(f"    Note over {sender},{receiver}: LINK FAIL{suffix}")
        elif event.get("event") == "link_recover":
            sender, receiver = str(event["channel"]).split("->", 1)
            reason = _optional_text(event.get("reason"))
            suffix = f" ({_safe_mermaid_text(reason)})" if reason else ""
            lines.append(f"    Note over {sender},{receiver}: LINK RECOVER{suffix}")

    snapshot_label = _safe_mermaid_text(result.get("snapshot_id", "snapshot"))
    initiator = _safe_mermaid_text(result["initiator"])
    lines.append(f"    Note over {initiator}: {snapshot_label} starts")

    for marker in result.get("markers", []):
        sender = _safe_mermaid_text(marker["sender"])
        receiver = _safe_mermaid_text(marker["receiver"])
        time = marker["time"]
        lines.append(f"    {sender}-->>{receiver}: marker t={time}")

    balances = ", ".join(
        f"{process}={balance}"
        for process, balance in sorted((result.get("balances") or {}).items())
    )
    lines.append(f"    Note over {','.join(ordered_processes)}: snapshot balances {balances}")

    process_statuses = result.get("process_statuses") or {}
    if process_statuses:
        status_summary = ", ".join(
            f"{process}={status}"
            for process, status in sorted(process_statuses.items())
        )
        lines.append(f"    Note over {','.join(ordered_processes)}: process status {status_summary}")

    channel_statuses = result.get("channel_statuses") or {}
    down_channels = [channel for channel, status in sorted(channel_statuses.items()) if status != "up"]
    if down_channels:
        lines.append(f"    Note over {','.join(ordered_processes)}: down links {', '.join(down_channels)}")

    channel_messages = result.get("channel_messages") or {}
    if channel_messages:
        for channel, messages in sorted(channel_messages.items()):
            sender, receiver = channel.split("->", 1)
            message_summary = ", ".join(
                f"{message['amount']} ({_safe_mermaid_text(message['label'])})"
                for message in messages
            )
            lines.append(
                f"    Note over {_safe_mermaid_text(sender)},{_safe_mermaid_text(receiver)}: recorded in-flight on {channel} {message_summary}"
            )
    else:
        lines.append("    Note over " + ",".join(ordered_processes) + ": no recorded in-flight channel messages")

    lines.append(
        f"    Note over {','.join(ordered_processes)}: consistent={result['consistent']} snapshot_total={result['snapshot_total']} system_total={result['system_total']}"
    )
    return "\n".join(lines) + "\n"


def render_snapshot_svg(
    result: dict[str, object],
    processes: Iterable[str],
    *,
    title: str | None = None,
) -> str:
    ordered_processes = list(sorted(set(str(process) for process in processes)))
    lane_gap = 180
    lane_header_width = 84
    margin_x = 72
    header_top = 56
    header_height = 32
    row_gap = 56
    summary_line_height = 18
    summary_padding = 18
    lane_positions = {
        process: margin_x + index * lane_gap
        for index, process in enumerate(ordered_processes)
    }
    width = margin_x * 2 + lane_gap * max(len(ordered_processes) - 1, 0)
    width += lane_header_width

    body: list[str] = []
    y = header_top + header_height + 36

    def add_text(
        x: float,
        y_pos: float,
        text: object,
        *,
        anchor: str = "middle",
        size: int = 13,
        weight: str = "400",
        fill: str = "#0f172a",
    ) -> str:
        return (
            f'<text x="{x:.1f}" y="{y_pos:.1f}" text-anchor="{anchor}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}">{_svg_escape(text)}</text>'
        )

    def add_multiline_text(
        x: float,
        y_pos: float,
        lines: Sequence[str],
        *,
        anchor: str = "middle",
        size: int = 13,
        fill: str = "#0f172a",
    ) -> str:
        tspans = []
        for index, line in enumerate(lines):
            dy = 0 if index == 0 else size + 5
            tspans.append(
                f'<tspan x="{x:.1f}" dy="{dy}">{_svg_escape(line)}</tspan>'
            )
        return (
            f'<text x="{x:.1f}" y="{y_pos:.1f}" text-anchor="{anchor}" '
            f'font-size="{size}" fill="{fill}">' + "".join(tspans) + "</text>"
        )

    def estimate_box_width(lines: Sequence[str], minimum: int = 140, maximum: int = 260) -> int:
        longest = max((len(line) for line in lines), default=0)
        return min(maximum, max(minimum, longest * 7 + 28))

    def add_note(center_x: float, center_y: float, text: object, *, fill: str = "#dbeafe", stroke: str = "#2563eb") -> None:
        wrapped = _wrap_svg_text(text, max_chars=28)
        box_width = estimate_box_width(wrapped)
        box_height = 18 + len(wrapped) * 18
        x = center_x - box_width / 2
        x = max(18, min(x, width - box_width - 18))
        text_x = x + box_width / 2
        y_top = center_y - box_height / 2
        body.append(
            f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{box_width:.1f}" height="{box_height:.1f}" '
            f'rx="12" ry="12" fill="{fill}" stroke="{stroke}" stroke-width="1.5" />'
        )
        body.append(add_multiline_text(text_x, y_top + 18, wrapped, size=12))

    def add_arrow(
        sender: str,
        receiver: str,
        y_pos: float,
        label: str,
        *,
        dashed: bool = False,
        color: str = "#1d4ed8",
    ) -> None:
        x1 = lane_positions[sender]
        x2 = lane_positions[receiver]
        body.append(
            f'<line x1="{x1:.1f}" y1="{y_pos:.1f}" x2="{x2:.1f}" y2="{y_pos:.1f}" '
            f'stroke="{color}" stroke-width="2.2" marker-end="url(#arrowhead)" '
            f'{"stroke-dasharray=\"8 6\"" if dashed else ""} />'
        )
        label_x = (x1 + x2) / 2
        label_width = min(280, max(120, len(label) * 7 + 18))
        body.append(
            f'<rect x="{label_x - label_width / 2:.1f}" y="{y_pos - 22:.1f}" width="{label_width:.1f}" height="18" '
            f'rx="9" ry="9" fill="#ffffff" opacity="0.88" />'
        )
        body.append(add_text(label_x, y_pos - 9, label, size=11))

    for event in result.get("timeline", []):
        kind = str(event.get("event", "")).strip().lower()
        if kind == "send":
            add_arrow(
                str(event["sender"]),
                str(event["receiver"]),
                y,
                f"transfer {event['amount']} ({event['label']})",
            )
        elif kind == "deliver":
            add_note(
                lane_positions[str(event["receiver"])],
                y,
                f"apply {event['amount']} from {event['sender']} ({event['label']})",
                fill="#ecfccb",
                stroke="#65a30d",
            )
        elif kind == "fail":
            reason = _optional_text(event.get("reason"))
            suffix = f" ({reason})" if reason else ""
            add_note(
                lane_positions[str(event["process"])],
                y,
                f"FAIL{suffix}",
                fill="#fee2e2",
                stroke="#dc2626",
            )
        elif kind == "recover":
            reason = _optional_text(event.get("reason"))
            suffix = f" ({reason})" if reason else ""
            add_note(
                lane_positions[str(event["process"])],
                y,
                f"RECOVER{suffix}",
                fill="#dcfce7",
                stroke="#16a34a",
            )
        elif kind == "link_fail":
            sender, receiver = str(event["channel"]).split("->", 1)
            reason = _optional_text(event.get("reason"))
            suffix = f" ({reason})" if reason else ""
            add_note(
                (lane_positions[sender] + lane_positions[receiver]) / 2,
                y,
                f"LINK FAIL{suffix}",
                fill="#fee2e2",
                stroke="#dc2626",
            )
        elif kind == "link_recover":
            sender, receiver = str(event["channel"]).split("->", 1)
            reason = _optional_text(event.get("reason"))
            suffix = f" ({reason})" if reason else ""
            add_note(
                (lane_positions[sender] + lane_positions[receiver]) / 2,
                y,
                f"LINK RECOVER{suffix}",
                fill="#dcfce7",
                stroke="#16a34a",
            )
        y += row_gap

    snapshot_label = _optional_text(result.get("snapshot_id")) or "snapshot"
    add_note(
        lane_positions[str(result["initiator"])],
        y,
        f"{snapshot_label} starts",
        fill="#ede9fe",
        stroke="#7c3aed",
    )
    y += row_gap

    for marker in result.get("markers", []):
        add_arrow(
            str(marker["sender"]),
            str(marker["receiver"]),
            y,
            f"marker t={marker['time']}",
            dashed=True,
            color="#475569",
        )
        y += row_gap - 4

    balances = ", ".join(
        f"{process}={balance}"
        for process, balance in sorted((result.get("balances") or {}).items())
    ) or "none"
    process_statuses = ", ".join(
        f"{process}={status}"
        for process, status in sorted((result.get("process_statuses") or {}).items())
    ) or "none"
    down_channels = [
        channel for channel, status in sorted((result.get("channel_statuses") or {}).items()) if status != "up"
    ]
    channel_messages = result.get("channel_messages") or {}
    if channel_messages:
        message_summary = "; ".join(
            f"{channel} = " + ", ".join(
                f"{message['amount']} ({message['label']})" for message in messages
            )
            for channel, messages in sorted(channel_messages.items())
        )
    else:
        message_summary = "none"

    summary_lines = [
        f"Balances: {balances}",
        f"Process status: {process_statuses}",
        f"Down links: {', '.join(down_channels) if down_channels else 'none'}",
        f"Recorded in-flight: {message_summary}",
        f"Totals: consistent={result['consistent']} snapshot_total={result['snapshot_total']} system_total={result['system_total']}",
    ]
    summary_height = summary_padding * 2 + summary_line_height * len(summary_lines)
    summary_y = y + 8
    body.append(
        f'<rect x="36" y="{summary_y:.1f}" width="{width - 72:.1f}" height="{summary_height:.1f}" '
        f'rx="16" ry="16" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" />'
    )
    body.append(add_text(56, summary_y + 24, "Snapshot summary", anchor="start", size=14, weight="700"))
    summary_text_y = summary_y + 46
    for line in summary_lines:
        body.append(add_text(56, summary_text_y, line, anchor="start", size=12))
        summary_text_y += summary_line_height

    height = int(summary_y + summary_height + 40)
    title_text = title or f"Distributed Snapshot — {snapshot_label}"
    lane_bottom = summary_y - 18

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{_svg_escape(title_text)}</title>",
        f"<desc id=\"desc\">{_svg_escape('Distributed snapshot sequence diagram rendered as SVG.')}</desc>",
        "<defs>",
        '  <marker id="arrowhead" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto" markerUnits="strokeWidth">',
        '    <path d="M0,0 L10,4 L0,8 Z" fill="#1f2937" />',
        "  </marker>",
        "</defs>",
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff" />',
        f'<text x="36" y="30" font-size="18" font-weight="700" fill="#0f172a">{_svg_escape(title_text)}</text>',
    ]

    for process, x in lane_positions.items():
        svg_lines.append(
            f'<rect x="{x - lane_header_width / 2:.1f}" y="{header_top:.1f}" width="{lane_header_width:.1f}" height="{header_height:.1f}" '
            f'rx="10" ry="10" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1.2" />'
        )
        svg_lines.append(add_text(x, header_top + 21, process, size=13, weight="700"))
        svg_lines.append(
            f'<line x1="{x:.1f}" y1="{header_top + header_height:.1f}" x2="{x:.1f}" y2="{lane_bottom:.1f}" '
            f'stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="6 6" />'
        )

    svg_lines.extend(body)
    svg_lines.append("</svg>")
    return "\n".join(svg_lines) + "\n"


_HEADLESS_BROWSER_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)


def _extract_svg_dimensions(svg_text: str) -> tuple[int, int]:
    match = re.search(
        r"<svg[^>]*\bwidth=\"([0-9]+(?:\.[0-9]+)?)\"[^>]*\bheight=\"([0-9]+(?:\.[0-9]+)?)\"",
        svg_text,
    )
    if match is None:
        raise ValueError("could not determine SVG dimensions for PNG export")
    width = max(1, int(float(match.group(1))))
    height = max(1, int(float(match.group(2))))
    return width, height


def _find_headless_browser() -> str | None:
    for candidate in _HEADLESS_BROWSER_CANDIDATES:
        browser = shutil.which(candidate)
        if browser is not None:
            return browser
    return None


def render_svg_to_png(
    svg_text: str,
    output_path: Path,
    *,
    browser_binary: str | None = None,
) -> Path:
    browser = browser_binary or _find_headless_browser()
    if browser is None:
        raise ValueError(
            "PNG export requires a headless browser such as google-chrome, google-chrome-stable, or chromium on PATH"
        )

    width, height = _extract_svg_dimensions(svg_text)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="distributed-snapshot-png-") as temp_dir:
        svg_path = Path(temp_dir) / "snapshot.svg"
        svg_path.write_text(svg_text, encoding="utf-8")
        completed = subprocess.run(
            [
                browser,
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--default-background-color=ffffff",
                f"--window-size={width},{height}",
                f"--screenshot={output_path}",
                svg_path.as_uri(),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown headless-browser error"
        raise ValueError(f"PNG export failed: {stderr}")
    if not output_path.exists():
        raise ValueError("PNG export failed: browser did not produce an output file")
    return output_path


def _format_mapping(mapping: dict[str, object]) -> str:
    if not mapping:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(mapping.items()))


def _format_in_flight(in_flight: dict[str, list[dict[str, object]]]) -> list[str]:
    lines: list[str] = []
    for channel, messages in sorted(in_flight.items()):
        summary = ", ".join(
            f"{message['amount']} ({_safe_mermaid_text(message['label'])})" for message in messages
        )
        lines.append(f"- `{channel}`: {summary}")
    return lines


def _describe_timeline_event(event: dict[str, object]) -> str:
    kind = str(event.get("event", "")).strip().lower()
    if kind == "send":
        return (
            f"sent `{event['label']}` carrying {event['amount']} from `{event['sender']}` to `{event['receiver']}`; "
            f"balances now {_format_mapping(event.get('balances') or {})}"
        )
    if kind == "deliver":
        return (
            f"delivered `{event['label']}` from `{event['sender']}` to `{event['receiver']}`; "
            f"balances now {_format_mapping(event.get('balances') or {})}"
        )
    if kind == "fail":
        reason = _optional_text(event.get("reason"))
        suffix = f" ({reason})" if reason else ""
        return f"process `{event['process']}` failed{suffix}; statuses now {_format_mapping(event.get('process_statuses') or {})}"
    if kind == "recover":
        reason = _optional_text(event.get("reason"))
        suffix = f" ({reason})" if reason else ""
        return f"process `{event['process']}` recovered{suffix}; statuses now {_format_mapping(event.get('process_statuses') or {})}"
    if kind == "link_fail":
        reason = _optional_text(event.get("reason"))
        suffix = f" ({reason})" if reason else ""
        return f"link `{event['channel']}` failed{suffix}; channel statuses now {_format_mapping(event.get('channel_statuses') or {})}"
    if kind == "link_recover":
        reason = _optional_text(event.get("reason"))
        suffix = f" ({reason})" if reason else ""
        return f"link `{event['channel']}` recovered{suffix}; channel statuses now {_format_mapping(event.get('channel_statuses') or {})}"
    return json.dumps(event, sort_keys=True)


def generate_walkthrough_svg_assets(
    result: dict[str, object],
    processes: Iterable[str],
    *,
    output_dir: Path,
    title: str = "Distributed Snapshot Walkthrough",
    markdown_path: Path | None = None,
    filename_prefix: str | None = None,
) -> dict[str, dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = _slugify_filename(filename_prefix or title)
    assets: dict[str, dict[str, str]] = {}
    for index, snapshot in enumerate(result.get("snapshots") or [], start=1):
        snapshot_id = _optional_text(snapshot.get("snapshot_id")) or f"snapshot-{index}"
        filename = f"{prefix}-{index:02d}-{_slugify_filename(snapshot_id)}.svg"
        path = output_dir / filename
        svg_title = f"{title} — {snapshot_id}"
        path.write_text(render_snapshot_svg(snapshot, processes, title=svg_title), encoding="utf-8")
        if markdown_path is not None:
            link = Path(os.path.relpath(path, markdown_path.parent)).as_posix()
        else:
            link = path.as_posix()
        assets[snapshot_id] = {
            "filename": filename,
            "path": path.as_posix(),
            "link": link,
            "title": svg_title,
        }
    return assets


def generate_walkthrough_png_assets(
    result: dict[str, object],
    processes: Iterable[str],
    *,
    output_dir: Path,
    title: str = "Distributed Snapshot Walkthrough",
    markdown_path: Path | None = None,
    filename_prefix: str | None = None,
    browser_binary: str | None = None,
) -> dict[str, dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = _slugify_filename(filename_prefix or title)
    assets: dict[str, dict[str, str]] = {}
    for index, snapshot in enumerate(result.get("snapshots") or [], start=1):
        snapshot_id = _optional_text(snapshot.get("snapshot_id")) or f"snapshot-{index}"
        filename = f"{prefix}-{index:02d}-{_slugify_filename(snapshot_id)}.png"
        path = output_dir / filename
        png_title = f"{title} — {snapshot_id}"
        render_svg_to_png(
            render_snapshot_svg(snapshot, processes, title=png_title),
            path,
            browser_binary=browser_binary,
        )
        if markdown_path is not None:
            link = Path(os.path.relpath(path, markdown_path.parent)).as_posix()
        else:
            link = path.as_posix()
        assets[snapshot_id] = {
            "filename": filename,
            "path": path.as_posix(),
            "link": link,
            "title": png_title,
        }
    return assets


def _resolve_asset_href(
    asset: dict[str, str] | None,
    *,
    reference_path: Path | None = None,
) -> str | None:
    if not asset:
        return None
    raw_path = _optional_text(asset.get("path"))
    fallback = _optional_text(asset.get("link"))
    if raw_path is None:
        return fallback

    asset_path = Path(raw_path)
    if reference_path is None:
        return fallback or asset_path.as_posix()

    cwd = Path.cwd()
    asset_anchor = asset_path if asset_path.is_absolute() else cwd / asset_path
    reference_anchor = reference_path if reference_path.is_absolute() else cwd / reference_path
    try:
        return Path(os.path.relpath(asset_anchor, reference_anchor.parent)).as_posix()
    except ValueError:
        return fallback or asset_path.as_posix()


def render_script_walkthrough(
    result: dict[str, object],
    processes: Iterable[str],
    *,
    title: str = "Distributed Snapshot Walkthrough",
    svg_assets: dict[str, dict[str, str]] | None = None,
    png_assets: dict[str, dict[str, str]] | None = None,
) -> str:
    ordered_processes = list(sorted(set(str(process) for process in processes)))
    final_channel_statuses = result.get("channel_statuses") or {}
    final_down_channels = [
        channel for channel, status in sorted(final_channel_statuses.items()) if status != "up"
    ]
    in_flight = result.get("in_flight") or {}
    snapshots = list(result.get("snapshots") or [])

    lines = [
        f"# {title}",
        "",
        "## Scenario summary",
        f"- processes: {', '.join(ordered_processes)}",
        f"- snapshots captured: {len(snapshots)}",
        f"- final balances: {_format_mapping(result.get('balances') or {})}",
        f"- final process statuses: {_format_mapping(result.get('process_statuses') or {})}",
        f"- final down links: {', '.join(final_down_channels) if final_down_channels else 'none'}",
        f"- system total: {result.get('system_total')}",
        "",
        "## Timeline",
    ]

    timeline = list(result.get("timeline") or [])
    operations = list(result.get("operations") or [])
    snapshots_by_step = {
        int(snapshot["step"]): snapshot
        for snapshot in snapshots
        if snapshot.get("step") is not None
    }
    if operations:
        timeline_iter = iter(timeline)
        for index, operation in enumerate(operations, start=1):
            op = str(operation.get("op", "")).strip().lower()
            if op == "snapshot":
                snapshot = snapshots_by_step.get(index, {})
                snapshot_id = _safe_mermaid_text(
                    snapshot.get("snapshot_id")
                    or _optional_text(operation.get("snapshot_id"))
                    or f"snapshot-{index}"
                )
                initiator = _safe_mermaid_text(snapshot.get("initiator") or operation.get("initiator") or "")
                consistency = snapshot.get("consistent")
                consistency_text = f"; consistent={consistency}" if consistency is not None else ""
                lines.append(
                    f"{index}. captured snapshot `{snapshot_id}` from `{initiator}`{consistency_text}"
                )
                continue
            event = next(timeline_iter, None)
            if event is None:
                lines.append(f"{index}. {json.dumps(operation, sort_keys=True)}")
            else:
                lines.append(f"{index}. {_describe_timeline_event(event)}")
    elif timeline:
        for index, event in enumerate(timeline, start=1):
            lines.append(f"{index}. {_describe_timeline_event(event)}")
    else:
        lines.append("- no events recorded")

    if in_flight:
        lines.extend(["", "## Remaining in-flight messages"])
        lines.extend(_format_in_flight(in_flight))

    if snapshots:
        lines.extend(["", "## Snapshot walkthrough"])
        for snapshot in snapshots:
            raw_snapshot_id = _optional_text(snapshot.get("snapshot_id")) or "snapshot"
            snapshot_id = _safe_mermaid_text(raw_snapshot_id)
            step = snapshot.get("step")
            step_suffix = f" (script step {step})" if step is not None else ""
            snapshot_channel_statuses = snapshot.get("channel_statuses") or {}
            snapshot_down_channels = [
                channel
                for channel, status in sorted(snapshot_channel_statuses.items())
                if status != "up"
            ]
            svg_asset = (svg_assets or {}).get(raw_snapshot_id)
            png_asset = (png_assets or {}).get(raw_snapshot_id)
            lines.extend(
                [
                    "",
                    f"### Snapshot `{snapshot_id}`{step_suffix}",
                    f"- initiator: `{snapshot['initiator']}`",
                    f"- balances: {_format_mapping(snapshot.get('balances') or {})}",
                    f"- process statuses: {_format_mapping(snapshot.get('process_statuses') or {})}",
                    f"- down links: {', '.join(snapshot_down_channels) if snapshot_down_channels else 'none'}",
                    f"- consistent totals: `{snapshot['consistent']}` ({snapshot['snapshot_total']} vs {snapshot['system_total']})",
                ]
            )
            if svg_asset:
                lines.append(f"- SVG asset: [{svg_asset['filename']}]({svg_asset['link']})")
            if png_asset:
                lines.append(f"- PNG asset: [{png_asset['filename']}]({png_asset['link']})")
            channel_messages = snapshot.get("channel_messages") or {}
            if channel_messages:
                lines.append("- recorded in-flight messages:")
                for channel, messages in sorted(channel_messages.items()):
                    summary = ", ".join(
                        f"{message['amount']} ({_safe_mermaid_text(message['label'])})"
                        for message in messages
                    )
                    lines.append(f"  - `{channel}`: {summary}")
            else:
                lines.append("- recorded in-flight messages: none")
            if svg_asset:
                lines.extend(["", f"![{snapshot_id} SVG]({svg_asset['link']})"])
            elif png_asset:
                lines.extend(["", f"![{snapshot_id} PNG]({png_asset['link']})"])
            lines.extend(["", "```mermaid", render_mermaid(snapshot, ordered_processes).rstrip(), "```"])
    else:
        lines.extend(["", "## Snapshot walkthrough", "- no snapshots were captured by this script"])

    return "\n".join(lines) + "\n"


def render_script_walkthrough_html(
    result: dict[str, object],
    processes: Iterable[str],
    *,
    title: str = "Distributed Snapshot Walkthrough",
    svg_assets: dict[str, dict[str, str]] | None = None,
    png_assets: dict[str, dict[str, str]] | None = None,
    output_path: Path | None = None,
) -> str:
    ordered_processes = list(sorted(set(str(process) for process in processes)))
    final_channel_statuses = result.get("channel_statuses") or {}
    final_down_channels = [
        channel for channel, status in sorted(final_channel_statuses.items()) if status != "up"
    ]
    in_flight = result.get("in_flight") or {}
    snapshots = list(result.get("snapshots") or [])
    operations = list(result.get("operations") or [])
    timeline = list(result.get("timeline") or [])
    snapshots_by_step = {
        int(snapshot["step"]): snapshot
        for snapshot in snapshots
        if snapshot.get("step") is not None
    }

    def escape(value: object) -> str:
        return html.escape(str(value), quote=True)

    def format_message_summary(messages: list[dict[str, object]]) -> str:
        return ", ".join(f"{message['amount']} ({message['label']})" for message in messages)

    timeline_items: list[str] = []
    if operations:
        timeline_iter = iter(timeline)
        for index, operation in enumerate(operations, start=1):
            op = str(operation.get("op", "")).strip().lower()
            if op == "snapshot":
                snapshot = snapshots_by_step.get(index, {})
                snapshot_id = (
                    snapshot.get("snapshot_id")
                    or _optional_text(operation.get("snapshot_id"))
                    or f"snapshot-{index}"
                )
                initiator = snapshot.get("initiator") or operation.get("initiator") or ""
                consistency = snapshot.get("consistent")
                consistency_text = f"; consistent={consistency}" if consistency is not None else ""
                description = f"captured snapshot `{snapshot_id}` from `{initiator}`{consistency_text}"
            else:
                event = next(timeline_iter, None)
                description = (
                    _describe_timeline_event(event)
                    if event is not None
                    else json.dumps(operation, sort_keys=True)
                )
            timeline_items.append(
                f'<li><span class="step-index">{index}.</span> {escape(description)}</li>'
            )
    elif timeline:
        for index, event in enumerate(timeline, start=1):
            timeline_items.append(
                f'<li><span class="step-index">{index}.</span> {escape(_describe_timeline_event(event))}</li>'
            )
    else:
        timeline_items.append("<li>No events recorded.</li>")

    remaining_in_flight_items = [
        f'<li><code>{escape(channel)}</code>: {escape(format_message_summary(messages))}</li>'
        for channel, messages in sorted(in_flight.items())
    ]

    snapshot_sections: list[str] = []
    for snapshot in snapshots:
        raw_snapshot_id = _optional_text(snapshot.get("snapshot_id")) or "snapshot"
        step = snapshot.get("step")
        step_suffix = f"Step {step}" if step is not None else "Snapshot"
        snapshot_channel_statuses = snapshot.get("channel_statuses") or {}
        snapshot_down_channels = [
            channel
            for channel, status in sorted(snapshot_channel_statuses.items())
            if status != "up"
        ]
        svg_asset = (svg_assets or {}).get(raw_snapshot_id)
        png_asset = (png_assets or {}).get(raw_snapshot_id)
        svg_href = _resolve_asset_href(svg_asset, reference_path=output_path)
        png_href = _resolve_asset_href(png_asset, reference_path=output_path)
        primary_href = svg_href or png_href
        asset_links: list[str] = []
        if svg_href:
            svg_label = escape(svg_asset["filename"] if svg_asset else "SVG asset")
            asset_links.append(
                f'<a href="{escape(svg_href)}">Open SVG</a> <span class="muted">({svg_label})</span>'
            )
        if png_href:
            png_label = escape(png_asset["filename"] if png_asset else "PNG asset")
            asset_links.append(
                f'<a href="{escape(png_href)}">Open PNG</a> <span class="muted">({png_label})</span>'
            )

        media_block = ""
        if primary_href:
            if svg_href and png_href:
                media = (
                    f'<picture><source srcset="{escape(svg_href)}" type="image/svg+xml" />'
                    f'<img src="{escape(png_href)}" alt="{escape(raw_snapshot_id)} snapshot diagram" loading="lazy" /></picture>'
                )
            else:
                media = f'<img src="{escape(primary_href)}" alt="{escape(raw_snapshot_id)} snapshot diagram" loading="lazy" />'
            caption = f"<strong>{escape(raw_snapshot_id)}</strong> snapshot diagram"
            if asset_links:
                caption = caption + " · " + " · ".join(asset_links)
            media_block = (
                '<figure class="snapshot-figure">'
                f"{media}"
                f"<figcaption>{caption}</figcaption>"
                "</figure>"
            )

        channel_messages = snapshot.get("channel_messages") or {}
        if channel_messages:
            channel_message_items = "".join(
                f'<li><code>{escape(channel)}</code>: {escape(format_message_summary(messages))}</li>'
                for channel, messages in sorted(channel_messages.items())
            )
            channel_messages_html = f'<ul class="meta-list compact">{channel_message_items}</ul>'
        else:
            channel_messages_html = '<p class="muted">No recorded in-flight messages.</p>'

        balances_text = _format_mapping(snapshot.get("balances") or {})
        process_status_text = _format_mapping(snapshot.get("process_statuses") or {})
        down_links_text = ", ".join(snapshot_down_channels) if snapshot_down_channels else "none"
        consistency_text = f"{snapshot['consistent']} ({snapshot['snapshot_total']} vs {snapshot['system_total']})"
        mermaid_source = escape(render_mermaid(snapshot, ordered_processes).rstrip())

        snapshot_sections.append(
            "".join(
                [
                    '<section class="snapshot-card">',
                    f'<div class="section-eyebrow">{escape(step_suffix)}</div>',
                    f'<h2>{escape(raw_snapshot_id)}</h2>',
                    '<div class="snapshot-layout">',
                    '<div class="snapshot-meta">',
                    '<ul class="meta-list">',
                    f'<li><strong>Initiator:</strong> <code>{escape(snapshot["initiator"])}</code></li>',
                    f'<li><strong>Balances:</strong> {escape(balances_text)}</li>',
                    f'<li><strong>Process status:</strong> {escape(process_status_text)}</li>',
                    f'<li><strong>Down links:</strong> {escape(down_links_text)}</li>',
                    f'<li><strong>Consistency:</strong> {escape(consistency_text)}</li>',
                    '</ul>',
                    '<h3>Recorded in-flight messages</h3>',
                    channel_messages_html,
                    '</div>',
                    '<div class="snapshot-visuals">',
                    media_block or '<div class="empty-media">No committed SVG/PNG asset supplied for this snapshot yet.</div>',
                    '<details class="mermaid-source">',
                    '<summary>Mermaid source</summary>',
                    f'<pre><code>{mermaid_source}</code></pre>',
                    '</details>',
                    '</div>',
                    '</div>',
                    '</section>',
                ]
            )
        )

    if not snapshot_sections:
        snapshot_sections.append(
            '<section class="snapshot-card"><h2>No snapshots captured</h2><p class="muted">This script run did not record any snapshots.</p></section>'
        )

    summary_cards = [
        ("Processes", ", ".join(ordered_processes)),
        ("Snapshots captured", str(len(snapshots))),
        ("Final balances", _format_mapping(result.get("balances") or {})),
        ("Final process statuses", _format_mapping(result.get("process_statuses") or {})),
        ("Final down links", ", ".join(final_down_channels) if final_down_channels else "none"),
        ("System total", str(result.get("system_total"))),
    ]
    summary_cards_html = "".join(
        f'<article class="summary-card"><div class="summary-label">{escape(label)}</div><div class="summary-value">{escape(value)}</div></article>'
        for label, value in summary_cards
    )
    if remaining_in_flight_items:
        summary_cards_html += (
            '<article class="summary-card summary-card-wide"><div class="summary-label">Remaining in-flight messages</div>'
            f'<ul class="meta-list compact">{"".join(remaining_in_flight_items)}</ul></article>'
        )

    return "\n".join(
        [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="utf-8" />',
            '<meta name="viewport" content="width=device-width, initial-scale=1" />',
            f'<title>{escape(title)}</title>',
            '<style>',
            '  :root { color-scheme: light; --bg: #f8fafc; --card: #ffffff; --ink: #0f172a; --muted: #475569; --line: #cbd5e1; --accent: #2563eb; }',
            '  * { box-sizing: border-box; }',
            '  body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); }',
            '  main { max-width: 1180px; margin: 0 auto; padding: 32px 20px 56px; }',
            '  header { margin-bottom: 28px; }',
            '  h1, h2, h3 { margin: 0 0 12px; line-height: 1.2; }',
            '  h1 { font-size: clamp(2rem, 4vw, 2.8rem); }',
            '  h2 { font-size: 1.4rem; }',
            '  h3 { font-size: 1rem; margin-top: 20px; }',
            '  p { line-height: 1.65; }',
            '  code, pre { font-family: "SFMono-Regular", SFMono-Regular, ui-monospace, Menlo, Consolas, monospace; }',
            '  code { background: #e2e8f0; border-radius: 6px; padding: 0.12rem 0.35rem; }',
            '  .lede { max-width: 72ch; color: var(--muted); font-size: 1.02rem; }',
            '  .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin: 24px 0 32px; }',
            '  .summary-card, .snapshot-card, .timeline-card { background: var(--card); border: 1px solid var(--line); border-radius: 20px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06); }',
            '  .summary-card { padding: 18px 18px 16px; }',
            '  .summary-card-wide { grid-column: 1 / -1; }',
            '  .summary-label { font-size: 0.8rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); margin-bottom: 8px; }',
            '  .summary-value { font-size: 1rem; line-height: 1.5; }',
            '  .timeline-card { padding: 22px; margin-bottom: 24px; }',
            '  .timeline { margin: 0; padding-left: 0; list-style: none; display: grid; gap: 10px; }',
            '  .timeline li { line-height: 1.55; color: var(--ink); }',
            '  .step-index { color: var(--accent); font-weight: 700; display: inline-block; min-width: 2.1rem; }',
            '  .snapshot-stack { display: grid; gap: 20px; }',
            '  .snapshot-card { padding: 24px; }',
            '  .section-eyebrow { text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.76rem; font-weight: 700; color: var(--accent); margin-bottom: 10px; }',
            '  .snapshot-layout { display: grid; grid-template-columns: minmax(260px, 360px) minmax(0, 1fr); gap: 22px; align-items: start; }',
            '  .meta-list { margin: 0; padding-left: 18px; display: grid; gap: 8px; }',
            '  .meta-list.compact { gap: 6px; }',
            '  .snapshot-figure { margin: 0; background: #f8fafc; border: 1px solid var(--line); border-radius: 18px; padding: 14px; }',
            '  .snapshot-figure img { display: block; width: 100%; height: auto; border-radius: 12px; background: #fff; border: 1px solid #e2e8f0; }',
            '  .snapshot-figure figcaption { margin-top: 10px; color: var(--muted); line-height: 1.5; }',
            '  .snapshot-figure a { color: var(--accent); text-decoration: none; }',
            '  .snapshot-figure a:hover { text-decoration: underline; }',
            '  .empty-media { border: 1px dashed var(--line); border-radius: 18px; padding: 18px; color: var(--muted); background: #f8fafc; }',
            '  .mermaid-source { margin-top: 14px; }',
            '  .mermaid-source summary { cursor: pointer; font-weight: 600; color: var(--accent); }',
            '  pre { margin: 10px 0 0; background: #0f172a; color: #e2e8f0; border-radius: 16px; padding: 16px; overflow-x: auto; line-height: 1.45; }',
            '  .muted { color: var(--muted); }',
            '  footer { margin-top: 32px; color: var(--muted); font-size: 0.95rem; }',
            '  @media (max-width: 860px) { .snapshot-layout { grid-template-columns: 1fr; } main { padding-left: 16px; padding-right: 16px; } }',
            '</style>',
            '</head>',
            '<body>',
            '<main>',
            '<header>',
            f'<h1>{escape(title)}</h1>',
            '<p class="lede">A single-page handout for the distributed snapshot partition/heal scenario. It bundles the scenario summary, ordered timeline, per-snapshot analysis, and links to the committed SVG/PNG artifacts so the lab is easy to publish or review without opening multiple files.</p>',
            '</header>',
            f'<section class="summary-grid">{summary_cards_html}</section>',
            '<section class="timeline-card">',
            '<div class="section-eyebrow">Scenario timeline</div>',
            '<h2>Ordered execution</h2>',
            f'<ol class="timeline">{"".join(timeline_items)}</ol>',
            '</section>',
            '<section class="snapshot-stack">',
            '<div class="section-eyebrow">Snapshot breakdown</div>',
            '<h2>Per-snapshot walkthrough</h2>',
            ''.join(snapshot_sections),
            '</section>',
            '<footer>Generated from the same structured walkthrough result used by the CLI and tests, so the handout stays reproducible across reruns.</footer>',
            '</main>',
            '</body>',
            '</html>',
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Distributed snapshot lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="run transfers, optionally deliver some, and capture a snapshot")
    simulate.add_argument("--balances", required=True, help='JSON object like {"A": 10, "B": 10}')
    simulate.add_argument("--send", action="append", default=[], help="sender:receiver:amount:label")
    simulate.add_argument("--deliver", action="append", default=[], help="sender:receiver")
    simulate.add_argument("--fail", action="append", default=[], help="process to mark down before the snapshot")
    simulate.add_argument("--recover", action="append", default=[], help="process to recover before the snapshot")
    simulate.add_argument("--link-fail", action="append", default=[], help="directed link sender:receiver to mark down before the snapshot")
    simulate.add_argument("--link-recover", action="append", default=[], help="directed link sender:receiver to recover before the snapshot")
    simulate.add_argument("--snapshot", required=True, help="process that initiates the snapshot")
    simulate.add_argument(
        "--marker-delay",
        action="append",
        default=[],
        help="override marker arrival ordering with sender->receiver=delay; larger values keep that incoming channel recording longer",
    )
    simulate.add_argument(
        "--output",
        choices=("json", "mermaid"),
        default="json",
        help="render the result as JSON or as a Mermaid sequence diagram",
    )

    concurrent = subparsers.add_parser(
        "concurrent",
        help="capture multiple named snapshots over the same simulated execution",
    )
    concurrent.add_argument("--balances", required=True, help='JSON object like {"A": 10, "B": 10}')
    concurrent.add_argument("--send", action="append", default=[], help="sender:receiver:amount:label")
    concurrent.add_argument("--deliver", action="append", default=[], help="sender:receiver")
    concurrent.add_argument("--fail", action="append", default=[], help="process to mark down before capturing snapshots")
    concurrent.add_argument("--recover", action="append", default=[], help="process to recover before capturing snapshots")
    concurrent.add_argument("--link-fail", action="append", default=[], help="directed link sender:receiver to mark down before capturing snapshots")
    concurrent.add_argument("--link-recover", action="append", default=[], help="directed link sender:receiver to recover before capturing snapshots")
    concurrent.add_argument(
        "--snapshot",
        action="append",
        required=True,
        default=[],
        help="named snapshot in snapshot_id:initiator format",
    )
    concurrent.add_argument(
        "--marker-delay",
        action="append",
        default=[],
        help="per-snapshot marker delay in snapshot_id:sender->receiver=delay format",
    )

    script = subparsers.add_parser(
        "script",
        help="run a scripted sequence of send/deliver/fail/recover/link-fail/link-recover/snapshot operations",
    )
    script.add_argument("--balances", required=True, help='JSON object like {"A": 10, "B": 10}')
    script.add_argument(
        "--script",
        required=True,
        help="JSON array of operation objects such as send/deliver/fail/recover/snapshot",
    )
    script.add_argument(
        "--marker-delay",
        action="append",
        default=[],
        help="sender->receiver=delay values applied to script snapshot steps",
    )

    walkthrough = subparsers.add_parser(
        "walkthrough",
        help="turn a scripted scenario into a Markdown walkthrough with embedded Mermaid diagrams",
    )
    walkthrough.add_argument("--balances", required=True, help='JSON object like {"A": 10, "B": 10}')
    walkthrough.add_argument(
        "--script",
        required=True,
        help="JSON array of operation objects such as send/deliver/fail/recover/snapshot",
    )
    walkthrough.add_argument(
        "--marker-delay",
        action="append",
        default=[],
        help="sender->receiver=delay values applied to script snapshot steps",
    )
    walkthrough.add_argument(
        "--title",
        default="Distributed Snapshot Walkthrough",
        help="Markdown heading used at the top of the walkthrough",
    )
    walkthrough.add_argument(
        "--output",
        help="optional Markdown file path for the generated walkthrough",
    )
    walkthrough.add_argument(
        "--html-output",
        help="optional single-page HTML handout path generated from the same walkthrough result",
    )
    walkthrough.add_argument(
        "--svg-dir",
        help="optional directory where one SVG snapshot asset per walkthrough section will be written",
    )
    walkthrough.add_argument(
        "--svg-prefix",
        help="optional filename prefix for generated SVG asset names",
    )
    walkthrough.add_argument(
        "--png-dir",
        help="optional directory where one PNG snapshot asset per walkthrough section will be written (requires google-chrome or chromium on PATH)",
    )
    walkthrough.add_argument(
        "--png-prefix",
        help="optional filename prefix for generated PNG asset names",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    bank = DistributedBank(parse_balances(args.balances))
    for raw in getattr(args, "send", []):
        sender, receiver, amount, label = parse_transfer(raw)
        bank.transfer(sender, receiver, amount, label)
    for raw in getattr(args, "deliver", []):
        sender, receiver = raw.split(":", 1)
        bank.deliver(sender, receiver)
    for process in getattr(args, "fail", []):
        bank.fail_process(process)
    for process in getattr(args, "recover", []):
        bank.recover_process(process)
    for raw in getattr(args, "link_fail", []):
        sender, receiver = raw.split(":", 1)
        bank.fail_link(sender, receiver)
    for raw in getattr(args, "link_recover", []):
        sender, receiver = raw.split(":", 1)
        bank.recover_link(sender, receiver)

    if args.command == "simulate":
        marker_delays = dict(parse_marker_delay(raw) for raw in args.marker_delay)
        result = bank.snapshot(args.snapshot, marker_delay_overrides=marker_delays)
        if args.output == "mermaid":
            print(render_mermaid(result, bank.processes), end="")
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command == "concurrent":
        snapshot_initiators = parse_snapshot_specs(args.snapshot)
        marker_delays: dict[str, dict[str, int]] = defaultdict(dict)
        for raw in args.marker_delay:
            snapshot_id, channel, delay = parse_scoped_marker_delay(raw)
            if snapshot_id not in snapshot_initiators:
                raise ValueError(f"marker delay references unknown snapshot id: {snapshot_id}")
            marker_delays[snapshot_id][channel] = delay
        result = bank.concurrent_snapshots(snapshot_initiators, marker_delay_overrides=dict(marker_delays))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    if args.command in {"script", "walkthrough"}:
        operations = parse_script(args.script)
        marker_delays = dict(parse_marker_delay(raw) for raw in args.marker_delay)
        result = bank.run_script(operations, marker_delay_overrides=marker_delays)
        if args.command == "walkthrough":
            output_path_text = _optional_text(getattr(args, "output", None))
            output_path = Path(output_path_text) if output_path_text else None
            html_output_text = _optional_text(getattr(args, "html_output", None))
            html_output_path = Path(html_output_text) if html_output_text else None
            svg_assets = None
            svg_dir_text = _optional_text(getattr(args, "svg_dir", None))
            svg_prefix = _optional_text(getattr(args, "svg_prefix", None))
            if svg_dir_text:
                svg_assets = generate_walkthrough_svg_assets(
                    result,
                    bank.processes,
                    output_dir=Path(svg_dir_text),
                    title=args.title,
                    markdown_path=output_path,
                    filename_prefix=svg_prefix,
                )
            png_assets = None
            png_dir_text = _optional_text(getattr(args, "png_dir", None))
            png_prefix = _optional_text(getattr(args, "png_prefix", None)) or svg_prefix
            if png_dir_text:
                png_assets = generate_walkthrough_png_assets(
                    result,
                    bank.processes,
                    output_dir=Path(png_dir_text),
                    title=args.title,
                    markdown_path=output_path,
                    filename_prefix=png_prefix,
                )
            markdown = render_script_walkthrough(
                result,
                bank.processes,
                title=args.title,
                svg_assets=svg_assets,
                png_assets=png_assets,
            )
            if output_path is not None:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(markdown, encoding="utf-8")
            if html_output_path is not None:
                html_output_path.parent.mkdir(parents=True, exist_ok=True)
                html_output_path.write_text(
                    render_script_walkthrough_html(
                        result,
                        bank.processes,
                        title=args.title,
                        svg_assets=svg_assets,
                        png_assets=png_assets,
                        output_path=html_output_path,
                    ),
                    encoding="utf-8",
                )
            print(markdown, end="")
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
