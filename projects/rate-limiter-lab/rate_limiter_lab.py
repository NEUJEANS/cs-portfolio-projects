from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Decision:
    timestamp: float
    allowed: bool
    detail: str


class BaseLimiter:
    def allow(self, timestamp: float) -> Decision:
        raise NotImplementedError


@dataclass
class FixedWindowLimiter(BaseLimiter):
    limit: int
    window_seconds: float
    counts: dict[int, int] = field(default_factory=dict)

    def allow(self, timestamp: float) -> Decision:
        window_index = int(timestamp // self.window_seconds)
        current = self.counts.get(window_index, 0)
        if current < self.limit:
            self.counts[window_index] = current + 1
            remaining = self.limit - self.counts[window_index]
            return Decision(timestamp, True, f"window={window_index} remaining={remaining}")
        return Decision(timestamp, False, f"window={window_index} remaining=0")


@dataclass
class SlidingLogLimiter(BaseLimiter):
    limit: int
    window_seconds: float
    events: deque[float] = field(default_factory=deque)

    def allow(self, timestamp: float) -> Decision:
        cutoff = timestamp - self.window_seconds
        while self.events and self.events[0] <= cutoff:
            self.events.popleft()
        if len(self.events) < self.limit:
            self.events.append(timestamp)
            remaining = self.limit - len(self.events)
            return Decision(timestamp, True, f"active_events={len(self.events)} remaining={remaining}")
        return Decision(timestamp, False, f"active_events={len(self.events)} remaining=0")


@dataclass
class TokenBucketLimiter(BaseLimiter):
    rate_per_second: float
    capacity: float
    tokens: float | None = None
    last_timestamp: float | None = None

    def allow(self, timestamp: float) -> Decision:
        if self.tokens is None:
            self.tokens = self.capacity
            self.last_timestamp = timestamp
        else:
            assert self.last_timestamp is not None
            elapsed = max(0.0, timestamp - self.last_timestamp)
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_second)
            self.last_timestamp = timestamp

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return Decision(timestamp, True, f"tokens={self.tokens:.3f}")
        return Decision(timestamp, False, f"tokens={self.tokens:.3f}")


ALGORITHMS = {
    "fixed-window": FixedWindowLimiter,
    "sliding-log": SlidingLogLimiter,
    "token-bucket": TokenBucketLimiter,
}


def parse_events(inline_events: Iterable[str], events_file: str | None) -> list[float]:
    events = [float(item) for item in inline_events]
    if events_file:
        data = json.loads(Path(events_file).read_text())
        if not isinstance(data, list):
            raise ValueError("events file must contain a JSON list of timestamps")
        events.extend(float(item) for item in data)
    return sorted(events)


def build_limiter(args: argparse.Namespace) -> BaseLimiter:
    if args.algorithm == "token-bucket":
        return TokenBucketLimiter(rate_per_second=args.rate, capacity=args.capacity)
    if args.limit <= 0 or args.window <= 0:
        raise ValueError("--limit and --window must be positive")
    if args.algorithm == "fixed-window":
        return FixedWindowLimiter(limit=args.limit, window_seconds=args.window)
    return SlidingLogLimiter(limit=args.limit, window_seconds=args.window)


def simulate(limiter: BaseLimiter, events: Iterable[float]) -> list[Decision]:
    return [limiter.allow(timestamp) for timestamp in events]


def summarize(decisions: Iterable[Decision]) -> dict[str, int]:
    decision_list = list(decisions)
    allowed = sum(1 for item in decision_list if item.allowed)
    denied = len(decision_list) - allowed
    return {"total": len(decision_list), "allowed": allowed, "denied": denied}


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulate common rate limiting algorithms")
    parser.add_argument("algorithm", choices=sorted(ALGORITHMS))
    parser.add_argument("--event", action="append", default=[], help="Event timestamp in seconds; repeat for multiple values")
    parser.add_argument("--events-file", help="Path to a JSON list of event timestamps")
    parser.add_argument("--limit", type=int, default=3, help="Max requests in a window (fixed/sliding)")
    parser.add_argument("--window", type=float, default=10.0, help="Window size in seconds (fixed/sliding)")
    parser.add_argument("--rate", type=float, default=1.0, help="Token refill rate per second (token bucket)")
    parser.add_argument("--capacity", type=float, default=3.0, help="Bucket capacity (token bucket)")
    parser.add_argument("--json", action="store_true", help="Emit JSON output instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.algorithm == "token-bucket":
        if args.rate <= 0 or args.capacity <= 0:
            raise ValueError("--rate and --capacity must be positive")

    events = parse_events(args.event, args.events_file)
    limiter = build_limiter(args)
    decisions = simulate(limiter, events)
    summary = summarize(decisions)

    if args.json:
        payload = {
            "algorithm": args.algorithm,
            "decisions": [decision.__dict__ for decision in decisions],
            "summary": summary,
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"algorithm: {args.algorithm}")
    for decision in decisions:
        status = "ALLOW" if decision.allowed else "DENY"
        print(f"{decision.timestamp:>8.3f}s  {status:<5}  {decision.detail}")
    print(f"summary: total={summary['total']} allowed={summary['allowed']} denied={summary['denied']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
