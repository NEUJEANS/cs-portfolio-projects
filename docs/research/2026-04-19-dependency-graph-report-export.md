# Dependency Graph Planner Research — 2026-04-19 report export slice

## Goal
Add a recruiter-friendly walkthrough report export that can live in GitHub alongside the existing Mermaid and DOT diagram artifacts.

## Brief references checked
- GitHub Docs — "Creating diagrams": GitHub renders Mermaid diagrams from fenced ```mermaid code blocks inside Markdown files, so a Markdown wrapper remains the most repo-friendly preview format for committed diagrams.
- GitHub Docs — "Getting permanent links to files": branch-head file URLs move over time; for stable sharing, it helps if generated reports link to committed companion artifacts in the repo and can later be shared with commit-specific permalinks.
- Lightweight portfolio-report examples/patterns: keep handoff docs short, summary-first, and explicit about commands/artifacts instead of relying on terminal screenshots.

## Notes carried into implementation
- keep the report as plain Markdown so it previews cleanly on GitHub and stays easy to diff
- generate relative links to companion Mermaid/DOT artifacts so the report bundle stays portable if it moves inside the repo
- keep the report deterministic by deriving every section from the existing plan/timing data instead of inventing new scheduling logic
- include a compact timing table plus layer windows and execution order so the artifact explains both parallelism and the critical path in one place
