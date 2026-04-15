# Vector Clock Lab

A small distributed-systems simulation that shows how vector clocks capture causal history across replicas, detect concurrent updates, and merge conflicting versions in a replicated key-value store.

## Why this project is portfolio-worthy
- demonstrates a core distributed-systems concept used to reason about causality
- turns theory into a runnable CLI plus tested simulation logic
- surfaces tradeoffs around conflict detection and deterministic merge behavior
- now includes a network-partition healing scenario that feels much closer to a real eventually consistent system
- gives you concrete interview material for replication, eventual consistency, anti-entropy, and version metadata

## Features
- sparse vector clock implementation with compare/tick/merge helpers
- replica-local writes that create versioned values
- conflict detection when concurrent versions exist for the same key
- replication flow that imports a remote version and updates local causal knowledge
- deterministic merge command that resolves concurrent versions into a causally newer value
- partition simulation command that models diverging writes during a network split, anti-entropy healing, and post-heal conflict resolution

## Project structure
- `vector_clock_lab.py` - core data model, replica store, partition simulator, and CLI
- `test_vector_clock_lab.py` - unit + CLI tests

## Usage
Run from this directory.

### Compare two clocks
```bash
python3 vector_clock_lab.py compare '{"a": 1}' '{"a": 1, "b": 1}'
```

### Simulate sequential writes on one replica
```bash
python3 vector_clock_lab.py write --replicas a b --replica a --key profile --values draft published
```

### Create a conflict and merge it
```bash
python3 vector_clock_lab.py conflict \
  --replicas a b c \
  --key profile \
  --left-replica a --left-value draft-a \
  --right-replica b --right-value draft-b \
  --merge-replica c
```

### Apply a remote version into another replica
```bash
python3 vector_clock_lab.py replicate \
  --replicas a b \
  --target-replica b \
  --key profile \
  --version '{"value":"draft","clock":{"a":1},"replica":"a"}'
```

### Simulate a network partition, heal, and merge surviving conflicts
```bash
python3 vector_clock_lab.py partition \
  --replicas a b c \
  --key profile \
  --left-partition a b \
  --right-partition c \
  --left-write a:draft-a \
  --right-write c:draft-c \
  --heal-replica b
```

## Testing
```bash
python3 -m unittest discover -s projects/vector-clock-lab -p 'test_*.py' -v
```

## Interview talking points
- why vector clocks can detect concurrency while scalar logical clocks cannot
- how causally newer versions replace older ones for the same key
- why concurrent versions need resolution instead of blind overwrite
- how anti-entropy after a partition can preserve multiple causally concurrent versions until an explicit merge happens
- why deterministic merges simplify demos while real systems often need domain-specific conflict handling

## Future improvements
- add Lamport clock comparison as a contrast mode
- emit a timeline or Mermaid diagram for partition-heal scenarios
- support configurable merge strategies such as last-writer-wins or custom reducers
- expose a visualization of the version DAG for each key
