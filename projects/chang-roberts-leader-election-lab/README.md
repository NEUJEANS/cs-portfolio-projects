# Chang-Roberts Leader Election Lab

A distributed-systems portfolio project that simulates the Chang-Roberts leader election algorithm on a unidirectional ring, including a post-election leader announcement phase, optional failed-node filtering, Mermaid trace export, and a lockstep multi-initiator mode for contention demos.

## Why this project is portfolio-worthy
- demonstrates a classic distributed-systems election protocol in runnable code
- makes message complexity tangible with full step-by-step traces and per-round metadata
- shows how ring ordering and initiator choice affect routing behavior
- includes failure-aware simulation so you can discuss partial availability assumptions in interviews
- exports Mermaid sequence diagrams that turn raw traces into slide-ready artifacts
- now includes simultaneous initiator scenarios, which make contention and duplicate-candidate suppression easy to explain live

## Features
- deterministic ring-order simulation for Chang-Roberts elections
- trace of each forwarded/replaced candidate message
- post-election leader announcement trace for the surviving ring
- failure filtering that removes inactive processes before the election starts
- JSON CLI output suitable for demos, scripts, and future visualizations
- Mermaid sequence-diagram export for election + announcement flow review
- lockstep multi-initiator mode with per-round metadata for contention walkthroughs
- unit + CLI coverage for core happy-path, validation, and visualization scenarios

## Project structure
- `chang_roberts_leader_election.py` - simulator, CLI, and Mermaid renderer
- `test_chang_roberts_leader_election.py` - unit and CLI coverage

## Usage
```bash
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --initiator 3 --pretty
python3 chang_roberts_leader_election.py --ring 10 4 15 7 --initiator 4 --failed 15 --include-visualization --pretty
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --initiators 3 6 --include-visualization --pretty
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --initiators 3 6 --visualization-only mermaid
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

## Testing
```bash
python3 -m unittest discover -s projects/chang-roberts-leader-election-lab -p 'test_*.py' -v
```

## Interview talking points
- why the highest live process id eventually dominates the circulating election messages
- how ring ordering affects the observed trace even though the final leader stays the same
- why Chang-Roberts has quadratic worst-case message complexity in the number of active nodes
- what changes when several processes initiate at once instead of one process seeding the ring
- what assumptions break when links are bidirectional, lossy, or nodes fail mid-election
- how visualization export helps communicate algorithm state changes to non-specialists during demos

## Modeling note for multi-initiator runs
The multi-initiator mode uses a deterministic lockstep model: all chosen initiators inject a candidate in round 0, every in-flight message advances one hop per round, and each receiver keeps only the strongest outgoing candidate for the next round. That gives you a stable, presentation-friendly way to discuss concurrent starts without introducing network timing randomness.

## Future improvements
- compare Chang-Roberts against Hirschberg-Sinclair or bully-election baselines
- benchmark single-initiator and multi-initiator runs across larger rings
- inject mid-election failures and recovery events
- export Graphviz or animation-friendly timeline formats alongside Mermaid
