# Chang-Roberts Leader Election Lab

A distributed-systems portfolio project that simulates the Chang-Roberts leader election algorithm on a unidirectional ring, including a post-election leader announcement phase and optional failed-node filtering.

## Why this project is portfolio-worthy
- demonstrates a classic distributed-systems election protocol in runnable code
- makes message complexity tangible with a full step-by-step trace
- shows how ring topology and initiator choice affect routing behavior
- includes failure-aware simulation so you can discuss partial availability assumptions in interviews

## Features
- deterministic ring-order simulation for Chang-Roberts elections
- trace of each forwarded/replaced candidate message
- post-election leader announcement trace for the surviving ring
- failure filtering that removes inactive processes before the election starts
- JSON CLI output suitable for demos, scripts, and future visualizations
- unit + CLI coverage for core happy-path and validation scenarios

## Project structure
- `chang_roberts_leader_election.py` - simulator and CLI
- `test_chang_roberts_leader_election.py` - unit and CLI coverage

## Usage
```bash
python3 chang_roberts_leader_election.py --ring 8 3 12 6 --initiator 3 --pretty
python3 chang_roberts_leader_election.py --ring 10 4 15 7 --initiator 4 --failed 15 --pretty
```

## Testing
```bash
python3 -m unittest discover -s projects/chang-roberts-leader-election-lab -p 'test_*.py' -v
```

## Interview talking points
- why the highest live process id eventually dominates the circulating election messages
- how ring ordering affects the observed trace even though the final leader stays the same
- why Chang-Roberts has quadratic worst-case message complexity in the number of active nodes
- what assumptions break when links are bidirectional, lossy, or nodes fail mid-election

## Future improvements
- add Mermaid or Graphviz timeline export for the message trace
- support multi-initiator simultaneous elections for richer contention scenarios
- compare Chang-Roberts against Hirschberg-Sinclair or bully-election baselines
- inject mid-election failures and recovery events
