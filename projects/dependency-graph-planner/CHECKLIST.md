# dependency-graph-planner checklist

## Completed slices
- [x] Implement deterministic topological sorting, cycle detection, layer extraction, and critical-path timing analysis
- [x] Add Mermaid and Graphviz diagram exports for recruiter-friendly graph visuals
- [x] Add Markdown walkthrough reports with linked diagram artifacts and timing tables
- [x] Add worker-limited scheduling with queue-delay tracking and committed schedule JSON snapshots
- [x] Add renewable resource-capacity constraints for scarce runners such as GPUs or signing hosts
- [x] Add multi-capacity comparison reports so the same manifest can be compared under different worker limits
- [x] Add ready-queue strategy comparisons (`critical-first`, `fifo`, `longest-processing-time`) with committed artifact bundles
- [x] Add per-task multi-resource demand vectors plus per-resource allocation/peak-usage reporting
- [x] Commit dedicated single-resource and multi-resource showcase manifests and artifact bundles
- [x] Add batch benchmark-suite mode plus a committed portfolio benchmark report
- [x] Export CSV/JSON leaderboard snapshots for downstream plotting or notebook analysis
- [x] Export compact HTML report dashboards plus GitHub-friendly schedule SVG artifacts
- [x] Add synthetic manifest generators for CI, release, and data-pipeline bottleneck patterns
- [x] Export benchmark dashboard HTML artifacts with relative links to the Markdown, JSON, and CSV suite bundle
- [x] Add metadata-aware default report titles/descriptions so showcase manifests render recruiter-friendly case-study headings automatically
- [x] Add seeded stress-workload benchmark cases plus gap/ratio-to-critical-path reporting across Markdown, HTML, JSON, and CSV exports
- [x] Refresh README, tests, review notes, and wrap-up support so the new scheduler story is visible in-repo
- [x] Simulate stochastic duration changes to compare heuristic robustness under uncertainty

## Next candidate slices
- [ ] Surface manifest metadata inside Mermaid preview wrappers and schedule SVG captions for even more polished artifact storytelling
