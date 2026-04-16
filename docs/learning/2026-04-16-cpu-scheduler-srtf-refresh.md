# CPU Scheduler Simulator SRTF Refresh — 2026-04-16

## Goal
Add shortest remaining time first (SRTF) support as a meaningful preemptive scheduling extension.

## Refresher notes
- SRTF is the preemptive version of shortest job first.
- At each scheduling decision point, the ready process with the smallest remaining burst should run next.
- When a new process arrives with a smaller remaining burst than the currently running process, the CPU should preempt.
- Useful tie-breakers for deterministic simulations: remaining time, then arrival time, then PID.
- Response time should still be measured from arrival until the first time the process gets CPU.

## Self-test
1. If `P1=(arrival=0, burst=8)` and `P2=(arrival=2, burst=2)`, should `P1` be preempted at time 2?
   - Yes. `P2` has smaller remaining work than `P1`'s remaining 6.
2. If two ready processes have the same remaining time, what keeps the simulator deterministic?
   - Stable tie-breaking on arrival time and PID.
3. Can SRTF increase total context switches compared with SJF?
   - Yes, because arrivals can trigger preemption mid-execution.
