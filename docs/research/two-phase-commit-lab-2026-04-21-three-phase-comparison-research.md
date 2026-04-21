# Two-phase commit lab research note — 2026-04-21 — 3PC comparison slice

## Goal
Add one meaningful next slice to the protocol-comparison artifacts by covering textbook three-phase commit alongside the existing 2PC and saga views.

## Brief research summary
- Wikipedia's 3PC summary is enough for this portfolio slice: 3PC adds an extra phase intended to avoid indefinite blocking compared with 2PC.
- The key caveat is the important one for interviews: that non-blocking story depends on stronger timing assumptions such as bounded delays and no network partition.
- That makes 3PC a strong teaching contrast even though real production systems more often choose consensus-backed coordination or saga-style workflows instead.

## Scope chosen for this slice
- extend the compare command and artifacts from 2PC-vs-saga to 2PC-vs-3PC-vs-saga
- keep 3PC as an explanatory comparison layer, not a full second simulator
- make the HTML and Markdown artifacts explicitly call out the bounded-delay/no-partition assumption so the portfolio story stays honest

## Sources used
- https://en.wikipedia.org/api/rest_v1/page/summary/Three-phase_commit_protocol
- https://en.wikipedia.org/api/rest_v1/page/summary/Two-phase_commit_protocol

## Deferred
- a full executable 3PC simulator with canCommit / preCommit / doCommit traces
- consensus-based comparison against Paxos/Raft-backed commit paths
