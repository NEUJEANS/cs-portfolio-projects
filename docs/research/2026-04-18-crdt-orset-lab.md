# CRDT OR-Set Lab Research Note — 2026-04-18

## Goal
Add a new portfolio project that covers eventually consistent replicated data structures, since the repo already has consensus, routing, clocks, and hashing labs but not a dedicated CRDT set example.

## Brief research summary
- CRDTs are designed so replicas can update independently and still converge after state merges.
- For a compact student portfolio slice, an **observed-remove set (OR-Set)** is a strong choice because it makes conflict resolution visible without needing a full collaborative editor.
- The most interview-useful behavior is that a remove only clears add-tags it has actually observed; a concurrent or later add can still survive after merge.

## Source notes
- Fetched the Wikipedia CRDT overview to refresh the state-based CRDT / strong eventual consistency framing.
- Tried the configured `web_search` first, but it was quota-limited during this run, so I kept the scope grounded in the fetched CRDT overview plus standard OR-Set semantics already familiar from distributed-systems coursework.

## Scope chosen for this slice
- new `crdt-orset-lab` project
- replica-local unique add tags like `a:1`
- observed-remove tombstone behavior
- associative/commutative/idempotent state merges
- scriptable multi-replica `add` / `remove` / `sync` scenarios for resumable demos

## Deferred
- visual timeline exports
- delta-state payload sizing
- side-by-side comparison with other CRDT families such as LWW-element-set or PN-counters
