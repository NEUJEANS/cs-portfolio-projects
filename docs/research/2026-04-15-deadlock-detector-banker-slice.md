# Deadlock Detector Banker's Algorithm Slice Research

## Goal
Add a deadlock-avoidance companion slice so the project can explain both detection and prevention during OS interviews.

## Brief research notes
- Banker's algorithm tracks `available`, `allocation`, `max`, and derived `need = max - allocation`.
- A state is safe when there exists at least one process order where each process's remaining `need` can be satisfied by current `work`, then its allocation is released back into `work`.
- A resource request is grantable only if it does not exceed both the process's remaining need and the currently available resources, and the simulated post-grant state is still safe.

## Sources
- Wikipedia overview of Banker's algorithm for the standard safety/request flow.
- General OS summaries cross-checked via web search results for safe-sequence and temporary-allocation rules.
