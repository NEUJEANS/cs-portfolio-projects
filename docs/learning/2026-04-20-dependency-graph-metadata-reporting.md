# Dependency graph planner metadata reporting refresh — 2026-04-20

## Short refresh
- Validate optional metadata where manifests are already parsed so `validate`, `report`, and tests all share the same guardrails.
- Prefer a single report-title helper that resolves in this order: explicit CLI title, manifest metadata title, stem-based fallback.
- Treat metadata descriptions as intro copy, not just raw JSON fields, so the Markdown report and HTML dashboard tell the same story.
- When polishing committed artifacts, update the showcase manifests too; otherwise the new renderer behavior only helps generated manifests.
- Deterministic re-export checks are worth doing after copy/story changes because static dashboards can drift in subtle ways even when the underlying schedule math is unchanged.

## Self-test
1. Why validate metadata through the normal manifest parsing path?
   - So malformed `metadata.title` / `metadata.description` fail fast anywhere the manifest is used instead of only on one renderer path.
2. What should win if both `--report-title` and `metadata.title` exist?
   - The explicit CLI title should win; metadata is only the default.
3. Why add metadata to the hand-authored sample manifests too?
   - It proves the feature on the committed showcase set and makes the in-repo artifact bundle look intentionally curated instead of filename-derived.
