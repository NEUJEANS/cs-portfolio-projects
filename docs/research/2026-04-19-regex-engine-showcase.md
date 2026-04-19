# Regex engine combined showcase slice research — 2026-04-19

## Brief refresh
- No external web research was necessary for this slice; the missing work was a repo-local showcase layer over already committed trace and benchmark artifacts.
- The strongest portfolio story here is not another raw artifact format by itself, but a single click path that starts with step-by-step NFA behavior and then broadens into benchmark evidence.
- Because the existing artifacts are already committed as JSON/Markdown/HTML files, the showcase should stay static and relative-link-based rather than introducing a frontend build, asset pipeline, or server dependency.

## Slice decision
Add `showcase-demo` as a tiny static landing-page generator that reads the committed trace JSON plus benchmark JSON/HTML/Markdown artifacts and emits one combined HTML hub.

Why this is the right next slice:
- it completes the exact follow-up left in the README/checklist after the benchmark dashboard slice
- it improves portfolio readability without touching the regex engine core semantics
- it keeps the repo resumable because later runs can regenerate the showcase from committed artifacts instead of hand-editing HTML
