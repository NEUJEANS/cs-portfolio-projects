# 2026-04-14 flashcard history refresh

## Quick refresh
- `json.loads` / `json.dumps(..., indent=2, sort_keys=True)` are enough for human-readable persistence here.
- `pathlib.Path` simplifies optional file creation and parent directory setup.
- Keep CLI persistence optional so tests and demos remain deterministic.

## Self-check
1. What should happen if the history file does not exist yet?
   - Return a zeroed default structure.
2. What should happen if the history file exists but contains invalid JSON?
   - Exit cleanly with a clear validation error.
3. Why store aggregate counts per prompt?
   - It is easy to inspect, good enough for trend tracking, and avoids overengineering the first persistence slice.
