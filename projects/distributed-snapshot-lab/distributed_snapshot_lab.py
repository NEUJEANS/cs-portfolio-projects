from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
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
    channel_messages: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    markers_seen: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    closed_channels: set[str] = field(default_factory=set)
    completed_processes: set[str] = field(default_factory=set)

    def to_dict(self) -> dict[str, object]:
        return {
            "initiator": self.initiator,
            "balances": dict(sorted(self.balances.items())),
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
        self.in_flight: dict[str, deque[Transfer]] = {
            self.channel_name(sender, receiver): deque()
            for sender in self.processes
            for receiver in self.processes
            if sender != receiver
        }
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

    def transfer(self, sender: str, receiver: str, amount: int, label: str) -> Transfer:
        self._require_process(sender)
        self._require_process(receiver)
        if sender == receiver:
            raise ValueError("sender and receiver must differ")
        if amount <= 0:
            raise ValueError("amount must be positive")
        if self.balances[sender] < amount:
            raise ValueError("sender has insufficient balance")
        transfer = Transfer(sender=sender, receiver=receiver, amount=amount, label=label)
        self.balances[sender] -= amount
        self.in_flight[self.channel_name(sender, receiver)].append(transfer)
        self.timeline.append({"event": "send", **transfer.to_dict(), "balances": self.current_balances()})
        return transfer

    def deliver(self, sender: str, receiver: str) -> Transfer:
        channel = self.channel_name(sender, receiver)
        queue = self.in_flight[channel]
        if not queue:
            raise ValueError(f"no in-flight transfer on channel {channel}")
        transfer = queue.popleft()
        self.balances[receiver] += transfer.amount
        self.timeline.append({"event": "deliver", **transfer.to_dict(), "balances": self.current_balances()})
        return transfer

    def current_balances(self) -> dict[str, int]:
        return dict(sorted(self.balances.items()))

    def total_money(self) -> int:
        return sum(self.balances.values()) + sum(
            transfer.amount
            for queue in self.in_flight.values()
            for transfer in queue
        )

    def snapshot(self, initiator: str, marker_delay_overrides: dict[str, int] | None = None) -> dict[str, object]:
        self._require_process(initiator)
        record = SnapshotRecord(initiator=initiator)
        marker_delay_overrides = marker_delay_overrides or {}
        for channel, delay in marker_delay_overrides.items():
            sender, receiver = self.parse_channel_name(channel)
            self._require_process(sender)
            self._require_process(receiver)
            if sender == receiver:
                raise ValueError("marker delays cannot target self channels")
            if delay < 0:
                raise ValueError("marker delay must be non-negative")
        incoming_channels = {
            process: [self.channel_name(sender, process) for sender in self.processes if sender != process]
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
                if marker_sender is None:
                    closed = set()
                else:
                    closed = {self.channel_name(marker_sender, process)}
                    record.markers_seen[process].append(marker_sender)
                record.closed_channels.update(closed)
                if set(incoming_channels[process]) <= record.closed_channels:
                    record.completed_processes.add(process)
                for target in self.processes:
                    if target == process:
                        continue
                    channel = self.channel_name(process, target)
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

    def _require_process(self, process: str) -> None:
        if process not in self.balances:
            raise ValueError(f"unknown process: {process}")


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


def _safe_mermaid_text(value: object) -> str:
    text = str(value)
    return text.replace("\n", " ").replace('"', "'")


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

    initiator = _safe_mermaid_text(result["initiator"])
    lines.append(f"    Note over {initiator}: snapshot starts")

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Distributed snapshot lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    simulate = subparsers.add_parser("simulate", help="run transfers, optionally deliver some, and capture a snapshot")
    simulate.add_argument("--balances", required=True, help='JSON object like {"A": 10, "B": 10}')
    simulate.add_argument("--send", action="append", default=[], help="sender:receiver:amount:label")
    simulate.add_argument("--deliver", action="append", default=[], help="sender:receiver")
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "simulate":
        raise ValueError(f"unsupported command: {args.command}")

    bank = DistributedBank(parse_balances(args.balances))
    for raw in args.send:
        sender, receiver, amount, label = parse_transfer(raw)
        bank.transfer(sender, receiver, amount, label)
    for raw in args.deliver:
        sender, receiver = raw.split(":", 1)
        bank.deliver(sender, receiver)
    marker_delays = dict(parse_marker_delay(raw) for raw in args.marker_delay)
    result = bank.snapshot(args.snapshot, marker_delay_overrides=marker_delays)
    if args.output == "mermaid":
        print(render_mermaid(result, bank.processes), end="")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
