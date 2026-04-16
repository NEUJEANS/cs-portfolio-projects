# Distributed Snapshot Lab Review Log — 2026-04-16 — Link Partitions Slice

## Review pass 1 — execution sanity
- Ran `python3 -m unittest -v projects/distributed-snapshot-lab/test_distributed_snapshot_lab.py`.
- Added coverage for down-link send/deliver blocking, snapshot marker skipping on blocked links, and scripted `link-fail` / `link-recover` flows.
- Result: slice worked end-to-end.

## Review pass 2 — code audit
- Checked that directed links stay separate from process liveness and that money conservation still uses queued channel state.
- Found a gap: snapshot outputs and script summaries needed explicit `channel_statuses` so partitions were visible outside the internal model.
- Fix applied: emitted `channel_statuses` in snapshot/script results and Mermaid notes.

## Review pass 3 — docs audit
- Reviewed project README, checklist, learning note, research note, and CLI examples.
- Found the README still framed process failure as the only failure model.
- Fix applied: documented directed link failures, added a one-way partition example, and updated future-slice notes.
