# Rate Limiter Lab Research

## Why this project
A rate limiter is a strong CS portfolio project because it combines:
- systems design concepts that show up in interviews and backend work
- tradeoffs between accuracy, burstiness, fairness, and memory use
- algorithmic reasoning with practical CLI/testing work

## Common algorithms worth demonstrating
1. **Fixed window**
   - simplest implementation
   - cheap state model
   - can allow boundary bursts near window edges
2. **Sliding log**
   - accurate but stores more timestamps
   - good for explaining space/time tradeoffs
3. **Token bucket**
   - supports controlled bursts while enforcing long-term average rate
   - common real-world shaping model

## Portfolio value
A student can discuss:
- algorithmic tradeoffs
- time-based simulation
- reproducible tests with a fake timeline
- how these models would scale to Redis or distributed coordination later

## Slice chosen for this run
Build a local CLI simulator that:
- runs fixed-window, sliding-log, and token-bucket limiters
- reads event timestamps from JSON or inline CLI arguments
- reports allow/deny decisions with a summary
- includes deterministic unit tests and a README with interview-ready explanations
