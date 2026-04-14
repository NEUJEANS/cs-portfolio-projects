# 2026-04-14 Disk Scheduler Refresh

## Quick refresh
- FCFS serves requests in arrival order and is the baseline for fairness-by-arrival.
- SSTF greedily serves the nearest cylinder next, which improves average seek distance but can starve distant requests.
- SCAN moves like an elevator toward one boundary, then reverses.
- C-SCAN moves in one direction, wraps to the opposite boundary, and continues, making wait times more uniform.

## Self-test
1. Why can SSTF starve requests? Because near-current requests can keep arriving or remain closer than far-out cylinders.
2. What is the practical difference between SCAN and LOOK? SCAN sweeps to a disk boundary; LOOK turns around at the furthest pending request.
3. Why might C-SCAN be preferable in teaching demos? Its one-direction service pattern makes fairness tradeoffs visually obvious.
