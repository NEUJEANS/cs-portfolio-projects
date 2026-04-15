# Chang-Roberts Leader Election Lab

A distributed-systems portfolio project that simulates the Chang-Roberts leader election algorithm on a unidirectional ring, including a post-election leader announcement phase, optional failed-node filtering, Mermaid trace export, a lockstep multi-initiator mode for contention demos, a Le Lann baseline comparison mode, and a built-in contention benchmark that compares 1..n simultaneous initiators.

## Why this project is portfolio-worthy
- demonstrates a classic distributed-systems election protocol in runnable code
- makes message complexity tangible with full step-by-step traces and per-round metadata
- shows how ring ordering and initiator choice affect routing behavior
- includes failure-aware simulation so you can discuss partial-availability assumptions in interviews
- exports Mermaid sequence diagrams that turn raw traces into slide-ready artifacts
- now includes simultaneous initiator scenarios plus aggregate benchmarks, which makes contention trade-offs easy to explain live
- adds a Le Lann baseline comparison so you can quantify why Chang-Roberts cuts unnecessary election traffic

## Features
- deterministic ring-order simulation for Chang-Roberts elections
- trace of each forwarded/replaced candidate message
- post-election leader announcement trace for the surviving ring
- failure filtering that removes inactive processes before the election starts
- JSON CLI output suitable for demos, scripts, and future visualizations
- Mermaid sequence-diagram export for election + announcement flow review
- lockstep multi-initiator mode with per-round metadata for contention walkthroughs
- contention benchmark mode that evaluates every 1..n initiator combination on the active ring
- `--compare-baseline` mode that contrasts Chang-Roberts against a Le Lann single-initiator baseline on the same active ring
- JSON + CSV benchmark artifacts for slide-ready comparisons
- unit + CLI coverage for core happy-path, validation, visualization, benchmark, and baseline-comparison scenarios

## Project structure
- `chang_roberts_leader_election.py` - simulator, CLI, Mermaid renderer, and contention benchmarker
- `test_chang_roberts_leader_election.py` - unit and CLI coverage

## Usage
```bash
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --initiator 3 --pretty
python3 chang_roberts_leader_election.py --ring 10 4 15 7 --initiator 4 --failed 15 --include-visualization --pretty
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --initiators 3 6 --include-visualization --pretty
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --initiators 3 6 --visualization-only mermaid
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --compare-baseline 3 --include-visualization --pretty
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --benchmark-contention --pretty
```

Example Mermaid output snippet:

```mermaid
sequenceDiagram
    participant P8 as 8
    participant P3 as 3
    participant P12 as 12
    participant P6 as 6
    Note over P8: initiators=3, 6 (lockstep)
    P3->>P12: election #1: round 1, replace with 12 (hop 1)
    ...
```

## Baseline comparison
To compare Chang-Roberts with a simpler Le Lann-style baseline that circulates every identifier once before electing the maximum, run:

```bash
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --compare-baseline 3 --include-visualization --pretty
```

This mode returns both traces plus a summary block with message-count deltas, which gives you an interview-friendly explanation for why Chang-Roberts suppresses lower identifiers early.

## Benchmarking
For a compact comparison of how contention changes delivery cost, run:

```bash
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --benchmark-contention --pretty
```

On the sample ring above, one initiator gives the cheapest average message count, while adding more simultaneous initiators reduces rounds slightly but increases total election traffic.

Benchmark artifacts generated in this repo:
- `artifacts/chang-roberts-contention-benchmark.json`
- `artifacts/chang-roberts-contention-benchmark.csv`

## Testing
```bash
python3 -m unittest discover -s projects/chang-roberts-leader-election-lab -p 'test_*.py' -v
```

## Interview talking points
- why the highest live process id eventually dominates the circulating election messages
- how Chang-Roberts differs from a Le Lann baseline that keeps circulating lower ids instead of suppressing them early
- how ring ordering affects the observed trace even though the final leader stays the same
- why Chang-Roberts has quadratic worst-case message complexity in the number of active nodes
- what changes when several processes initiate at once instead of one process seeding the ring
- why simultaneous starts can reduce rounds while still increasing total delivery cost
- what assumptions break when links are bidirectional, lossy, or nodes fail mid-election
- how visualization export helps communicate algorithm state changes to non-specialists during demos

## Modeling note for multi-initiator runs
The multi-initiator mode uses a deterministic lockstep model: all chosen initiators inject a candidate in round 0, every in-flight message advances one hop per round, and each receiver keeps only the strongest outgoing candidate for the next round. That gives you a stable, presentation-friendly way to discuss concurrent starts without introducing network timing randomness.

## Future improvements
- extend the comparison mode to include Hirschberg-Sinclair or bully-election baselines
- scale the contention benchmark to larger rings and plot trend lines automatically
- inject mid-election failures and recovery events
- export Graphviz or animation-friendly timeline formats alongside Mermaid
