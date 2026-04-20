# Dependency graph planner metadata reporting slice research — 2026-04-20

## Brief research
- No external web research was needed for this slice because the repo already had a local report/dashboard renderer pair and the generated manifests already carried useful `metadata.title` / `metadata.description` fields.
- The missing portfolio value was that default report/dashboard headings still came from file stems such as `generated_release_pipeline`, which undersold the case-study framing already present in the synthetic manifest metadata.
- The cleanest implementation is to validate manifest metadata centrally, then thread it into the existing report title/description defaults so Markdown and HTML stay aligned.

## Slice decision
Finish the next checklist item by:
- validating optional manifest metadata fields (`metadata.title`, `metadata.description`)
- using manifest metadata as the default report/dashboard heading and intro copy when `--report-title` is omitted
- backfilling metadata on the hand-authored showcase manifests so committed artifacts read more like portfolio case studies
- regenerating the committed report/dashboard artifacts to keep the repo resumable and demo-ready

Why this is the right next slice:
- it completes the exact follow-up left in `projects/dependency-graph-planner/CHECKLIST.md` and the previous benchmark-dashboard wrap-up
- it strengthens the recruiter-facing story without adding a second rendering pipeline or changing artifact filenames
- it stays easy to extend later if Mermaid previews or schedule SVG captions should also consume the same metadata
