# Page Replacement Lab research — dirty-page-aware WSClock

Date: 2026-04-19

## Goal
Add a stronger WSClock slice that can show not just page-fault counts, but also the writeback cost of evicting dirty pages.

## Brief external research
- Winona State / course notes on WSClock: dirty pages that are outside the working set should be scheduled for cleaning instead of being reclaimed immediately when a clean victim is still preferable.
- NYU course notes on WSClock: the algorithm combines a Clock scan with a working-set age check (`tau`) and uses dirty bits to defer eviction until writeback has been requested or completed.
- Common teaching summaries of Carr/Hennessy WSClock: the useful portfolio story is that WSClock trades off two resources at once — memory pressure and disk write pressure.

## Implementation takeaways
1. Keep the current simplified synchronous simulator model, but expose the real teaching signal:
   - page becomes dirty on access if its page number is in a configured dirty-page set
   - old dirty pages schedule a writeback when the hand scans them
   - clean old pages are preferred for immediate eviction
2. Track writebacks separately from page faults so the portfolio output can discuss why two runs with similar fault counts may still differ operationally.
3. Thread dirty-page metadata through every exported artifact so screenshots and JSON bundles stay self-explanatory later.

## Local sanity experiments
Using `compiler-phase-shift` with `--frames 5 --wsclock-window 1`:
- no dirty pages: WSClock faults 54, writebacks 0
- dirty pages `1..6`: WSClock faults 55, writebacks 15
- dirty pages `4..6`: WSClock faults 55, writebacks 9

## Slice decision
Use a sample dirty-page file with pages `1..6` for the committed artifact bundle because it reliably produces visible writeback pressure on the compiler benchmark.
