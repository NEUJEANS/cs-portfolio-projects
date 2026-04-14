# Rate Limiter Lab

A small simulation toolkit for comparing three classic rate limiting strategies:
- fixed window
- sliding log
- token bucket

This project is portfolio-friendly because it demonstrates algorithm tradeoffs, deterministic simulation, CLI design, and test coverage without requiring external services.

## Features
- simulate a sequence of request timestamps
- compare multiple rate limiter algorithms behind one interface
- load events from repeated CLI flags or a JSON file
- print a human-readable trace or structured JSON output

## Algorithms

### Fixed window
Counts requests inside coarse windows like `[0,10)`, `[10,20)`. Cheap and simple, but it can allow bursts across window boundaries.

### Sliding log
Stores recent timestamps and prunes anything outside the trailing window. More accurate than fixed window, but it uses more memory.

### Token bucket
Refills tokens over time and spends one token per allowed request. Good for smoothing traffic while still allowing controlled bursts.

## Usage

### Fixed window
```bash
python3 rate_limiter_lab.py fixed-window --limit 2 --window 10 --event 0 --event 1 --event 9.9 --event 10
```

### Sliding log with JSON output
```bash
python3 rate_limiter_lab.py sliding-log --limit 3 --window 5 --event 0 --event 1 --event 2 --event 4 --json
```

### Token bucket with file input
```bash
printf '[0, 0, 0, 1, 2.5]' > events.json
python3 rate_limiter_lab.py token-bucket --rate 1 --capacity 2 --events-file events.json
```

## Example output
```text
algorithm: token-bucket
   0.000s  ALLOW  tokens=1.000
   0.000s  ALLOW  tokens=0.000
   0.000s  DENY   tokens=0.000
   1.000s  ALLOW  tokens=0.000
summary: total=4 allowed=3 denied=1
```

## Testing
```bash
python3 projects/rate-limiter-lab/test_rate_limiter_lab.py
```

## Interview talking points
- explain why fixed windows can over-admit at boundaries
- compare the precision/memory tradeoff of sliding logs
- explain how token buckets allow bursts while preserving average throughput
- describe how the state model could move to Redis or a distributed system later

## Future improvements
- add a sliding-window counter approximation
- emit charts for decision timelines
- support per-user or per-endpoint keys in a multi-stream simulation
- add a Redis-backed adapter for real service integration
