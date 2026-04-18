# crdt-orset-lab research — 2026-04-18 — replay-controls slice

## Goal
Add faster classroom/demo controls to the generated replay page without turning the artifact into a framework app or breaking the accessibility work from the previous replay slice.

## Brief references checked
- MDN `<input type="range">`: useful reminder that native range inputs already provide bounded numeric stepping and browser fallback behavior, so the replay scrubber can stay a standard control instead of a custom drag widget.
- MDN `aria-live`: reaffirmed that dynamic status text should update a dedicated live region with short messages and should not steal focus while the page changes.

## Decision
Keep the replay page static and generated, but add:
1. prev/next sync jump buttons built from the existing timeline step indexes
2. a native `<select>` for playback speed presets
3. a small sync-status note that explains the nearest sync checkpoint in plain language
4. the existing polite live-region announcement flow for step changes

## Why
- native controls stay keyboard-friendly and lightweight on GitHub Pages / local static hosting
- sync jumps solve the real demo problem: reviewers mostly care about reconciliation moments, not every local mutation in between
- playback presets are enough for demos without adding complicated free-form timing UI
- the replay artifact still derives from the same snapshot/timeline data as the rest of the CLI outputs

## Implementation note
Use frame `op == "sync"` metadata already present in the replay frames instead of inventing a second sync-index file or browser-only model.
