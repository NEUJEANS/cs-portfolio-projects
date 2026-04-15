# raft-election-simulator

A portfolio-friendly distributed systems lab that simulates Raft leader election, deterministic timeout-driven failover, heartbeat stabilization, and a lightweight log-replication / commit-index flow.

## Why it is interesting
- demonstrates a core consensus-system building block instead of another CRUD app
- shows state-machine transitions across follower, candidate, and leader roles
- makes distributed-systems timing visible with deterministic scripted scenarios
- highlights both election safety and post-election command replication

## Features
- in-memory simulation of 3+ Raft nodes with per-node election timeouts
- deterministic event log for election starts, votes, leader wins, heartbeats, and commits
- lightweight log replication from leader to followers with commit-index tracking
- network-isolation actions to trigger split votes, unavailable leaders, and delayed replication
- timeout overrides for controlled retries in scripted experiments
- JSON scenario input and machine-readable JSON summary output

## Usage

Run the sample scenario:

```bash
python3 projects/raft-election-simulator/raft_election.py \
  --scenario projects/raft-election-simulator/sample_scenario.json \
  --pretty
```

Scenario format:

```json
{
  "nodes": ["n1", "n2", "n3"],
  "election_timeouts": {"n1": 3, "n2": 5, "n3": 7},
  "heartbeat_interval": 2,
  "steps": [
    {"action": "run", "ticks": 4},
    {"action": "client-write", "command": "set homepage-theme=dark"},
    {"action": "isolate", "node": "n1"},
    {"action": "run", "ticks": 4},
    {"action": "heal", "node": "n1"},
    {"action": "set-timeout", "node": "n2", "timeout": 3}
  ]
}
```

Supported step actions:
- `run` - advance simulated time by `ticks`
- `isolate` - partition a node from vote and heartbeat traffic
- `heal` - restore network access for a node
- `set-timeout` - change a node's election timeout for later ticks
- `client-write` - append a command to the current leader log and replicate it

## Test

```bash
python3 -m unittest projects/raft-election-simulator/test_raft_election.py
```

## Design notes
- Election success requires a majority of current votes.
- Followers and candidates step down when they see a higher term.
- Leaders send periodic heartbeats to keep followers from timing out.
- Commands become committed once a majority of logs contain the entry.
- The simulator intentionally keeps replication lightweight rather than modeling the full Raft log-matching protocol.

## Future improvements
- model prev-log-index / prev-log-term conflict repair more faithfully
- track applied state-machine values derived from committed commands
- export timeline visualizations for presentations or blog posts
