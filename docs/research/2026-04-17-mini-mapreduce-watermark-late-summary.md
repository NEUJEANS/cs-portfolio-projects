# Mini MapReduce watermark late-summary research

Date: 2026-04-17 21:03 UTC
Project: `mini-mapreduce-lab`

## Goal
Keep the new out-of-order stream-processing plugin aligned with recognizable event-time terminology instead of inventing portfolio-only wording.

## Notes
- Apache Beam’s programming guide describes a watermark as the system’s notion of when all data for a window can be expected to have arrived; once the watermark passes the end of a window, later arrivals for that window are considered late data.
- Beam also calls out `withAllowedLateness` as the way to keep accepting late data for some additional time after the window end instead of dropping everything immediately.
- Flink’s time docs frame `Watermark(t)` as a declaration that no more events with timestamps `<= t` should arrive, which is a good mental model for the reducer’s `watermark_before > window_close_at` drop decision.
- For a lightweight portfolio lab, it is enough to model event time, arrival time, a fixed watermark delay, and a bounded allowed-lateness grace period; that keeps the narrative concrete without pretending to be a full streaming engine.

## Chosen plugin story
- Input shape: `stream,event_time,arrival_time,value`
- Per-stream reducer output: accepted-event totals, late-accepted totals, dropped-late totals, final watermark, max watermark gap, and per-window summaries
- Benchmark families: `default` (calm baseline), `sensor-backfill` (utility-meter replay storm), and `live-replay` (chat/moderation replay pressure)
