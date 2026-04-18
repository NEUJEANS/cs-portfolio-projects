# CRDT OR-Set Lab — preset detail-bundle self-test (2026-04-18)

## Refresh prompt
- What should the preset-suite summary page link to once a reviewer wants more than the top-level outcome table?
- How should those links be stored so both Markdown and HTML outputs stay portable?
- What is the narrowest CLI shape that finishes the follow-up without fragmenting the UX?

## Answers
- Each preset card should jump straight to the per-preset comparison page, OR-Set timeline, replay page, anti-entropy report, and raw snapshot JSON.
- Store a `detail_bundle` map on each preset and compute its values relative to the file being written so links remain correct from suite Markdown, suite HTML, and suite JSON outputs.
- Extend `compare-presets` with one `--detail-output-dir` flag instead of creating a separate export command.

## Implementation check
- Added `--detail-output-dir` to `compare-presets`.
- Added per-preset detail-bundle generation plus suite-level artifact links.
- Verified tests cover both rendered links and the real CLI artifact-writing path.
