# CPU Scheduler Simulator Learning Note — 2026-04-21 Fairness and Slowdown Self-Test

## Quick refresh
- Average waiting time alone can hide an ugly tail where one process waits much longer than the rest.
- Slowdown normalizes turnaround by burst length, which makes it easier to compare how "unfair" a schedule felt for short versus long jobs.
- A per-process visualization is often more honest than a single fairness score because the viewer can still inspect who was hurt and by how much.

## Self-test
1. **Q:** Why add slowdown instead of only another waiting-time average?  
   **A:** Because slowdown normalizes by service demand, so a short interactive task that waited too long becomes obviously expensive instead of getting lost inside raw totals.

2. **Q:** Why include both slowdown spread and waiting spread ideas in the dashboard?  
   **A:** Because slowdown shows relative pain while waiting time still shows the absolute wall-clock delay each process experienced.

3. **Q:** Why export SVG instead of only enriching the HTML table?  
   **A:** Because SVG is deterministic, easy to diff, and easy to drop into README screenshots or slide decks without opening a browser.
