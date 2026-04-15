# Chang-Roberts vs Le Lann baseline research

## Goal
Add one meaningful comparison slice to the existing Chang-Roberts portfolio lab so interviewers can see not just how the algorithm works, but why it improves over a simpler ring-election baseline.

## Notes
- Chang-Roberts suppresses weaker identifiers as soon as they encounter a stronger process id.
- A simple Le Lann-style baseline keeps circulating identifiers instead of replacing them early, so it is easy to explain but noisier in message count.
- For a portfolio repo, a side-by-side trace plus message-count summary is more valuable than a heavyweight second simulator with incompatible assumptions.

## Implementation choice
Use a single-initiator Le Lann baseline comparison mode in the same unidirectional ring model.
That keeps the comparison fair on ring order, active nodes, and failure filtering while making the trace difference obvious.

## Interview framing
- Same leader, different cost profile.
- Chang-Roberts wins by pruning smaller candidate ids during circulation.
- The comparison result is strongest when paired with Mermaid traces and message-count deltas.
