# CPU Scheduler Simulator Learning Note — 2026-04-21 Context-Switch Self-Test

## Quick refresh
- Context-switch time is scheduler overhead, not useful process progress.
- Preemptive policies usually trigger more switches than FCFS or non-preemptive SJF.
- If wall-clock time grows but total burst work stays fixed, waiting and turnaround rise while throughput and useful CPU utilization fall.

## Self-test
1. **Q:** Should a fixed switch cost change process burst lengths?  
   **A:** No. Burst time stays the same. The extra cost stretches wall-clock completion around the bursts.

2. **Q:** Why represent switch cost as timeline slices instead of just adding a final penalty?  
   **A:** Because recruiters can see where the cost happened, and per-process start/completion metrics can be recomputed correctly.

3. **Q:** Which existing algorithm in this project should show the biggest visible change from switch overhead?  
   **A:** Round Robin, because frequent time-slice rotation creates repeated dispatches.
