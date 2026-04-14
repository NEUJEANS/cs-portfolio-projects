# Python Refresh + Self-Test — CPU Scheduler Simulator

## Refreshed topics
- `dataclasses.dataclass(order=True)` style modeling is nice, but explicit sort keys are clearer here.
- `deque` is the right primitive for Round Robin ready queues.
- Deterministic simulation is easier when events are handled in a fixed order:
  1. enqueue arrivals up to current time
  2. if needed, jump to next arrival when idle
  3. run selected process
  4. record first-response and completion times

## Self-test prompts
1. If a process arrives at time 3, first runs at time 8, and finishes at time 12 with burst 4, what are response/wait/turnaround?
   - response = 5
   - turnaround = 9
   - waiting = 5
2. Why can Round Robin have the same turnaround but different response time compared with FCFS?
   - because first service can happen earlier even when total completion order stays similar
3. What deterministic tie-break is sensible for equal burst lengths in SJF?
   - earlier arrival, then stable process id
