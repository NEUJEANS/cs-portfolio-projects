# 2026-04-16 Link-State vs Distance-Vector Comparison Slice

- [x] confirm repo/branch/remote are in sync before edits
- [x] choose the next weakest unfinished slice: complete the planned cross-lab convergence comparison for link-state-routing-lab
- [x] do brief research/knowledge refresh on why link-state avoids count-to-infinity while distance-vector may need more propagation rounds
- [x] self-test the planned comparison API and failure-event shape before editing
- [x] add a comparison flow in `link_state_routing.py` that summarizes link-state flooding vs distance-vector convergence on the same topology
- [x] support optional link-failure comparison so the slice is meaningful beyond steady-state shortest paths
- [x] expand tests for direct API comparison and CLI JSON output
- [x] update README usage and roadmap notes
- [x] run at least 3 review passes and fix issues found
  - pass 1: `git diff --check` for whitespace/conflict sanity
  - pass 2: CLI smoke test for `--compare-distance-vector --remove-link B D`
  - pass 3: targeted diff review of changed files
  - fixes made: inserted dynamically loaded distance-vector module into `sys.modules` for Python 3.14 dataclass compatibility; tightened the link-state post-failure assertion to track changed routers rather than all re-originated sequence bumps
- [x] run secret scan before push
- [x] append a wrap-up note for resumability
