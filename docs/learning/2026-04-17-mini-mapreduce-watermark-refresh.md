# Mini MapReduce watermark refresh

Date: 2026-04-17 21:05 UTC
Project: `mini-mapreduce-lab`

## Refresh
- Event time and arrival time need to stay separate all the way through the plugin; otherwise you cannot explain lateness or replay handling cleanly.
- A deterministic demo can approximate a watermark with `max_seen_event_time - fixed_delay`, then compare each arriving event against that watermark before updating the max-seen event time.
- Allowed lateness is easiest to explain in the lab as `window_end + grace_period`; late events before that cutoff are still accepted, and later ones are counted as dropped.
- Sorting shard-local batches by `(arrived_at, event_at, value)` keeps reducer behavior deterministic across test runs and artifact regeneration.

## Quick self-check
- If the reducer evaluates lateness against the watermark *before* advancing `max_seen_event_time`, a newly arrived replay is judged against prior event-time progress rather than its own timestamp.
- If each window summary stores both `events_seen` and `accepted_events`, the report can explain why drop rate rose even when the stream kept receiving records.
- If benchmark generators sort by arrival time before returning lines, the synthetic fixtures read like a real replay stream instead of a pre-sorted event-time trace.
