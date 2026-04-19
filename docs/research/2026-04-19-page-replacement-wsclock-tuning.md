# Research note — 2026-04-19 — page-replacement WSClock tuning

## Question
What is the smallest worthwhile next slice after dirty-page-aware WSClock so the project can tell a stronger systems story than “pick any `tau` and eyeball the result”?

## Brief references checked
- Gemini web search summary for WSClock `tau`, dirty-page writeback, and heuristic replacement tradeoffs
- NYU lecture notes on WSClock (`https://cs.nyu.edu/~gottlieb/courses/2000s/2008-09-fall/os/wsclock-davis.html`)
- Winona State WSClock overview (`https://cs.winona.edu/Francioni/cs405/wsclock.html`)

## Takeaways used for the implementation
- WSClock’s `tau` window is a tuning knob that approximates whether a page is still inside the working set.
- Old clean pages are the easiest eviction targets; old dirty pages often trigger cleaning first, so a useful teaching tool should show both page-fault cost and writeback cost.
- A deterministic simulator does not need to implement full background I/O scheduling to teach the main idea. A fixed weighted score over faults and writebacks is enough to surface why one `tau` beats another for a specific workload.
- The portfolio-friendly output is not just the winner. Students should also see the candidate sweep and the Pareto frontier so they can explain why nearby windows were rejected.

## Slice decision
- Add a dedicated `tune-wsclock` command instead of overloading `compare` or `study`.
- Keep the default auto window heuristic unchanged and treat the new command as an analysis/reporting helper.
- Export Markdown / CSV / JSON so the recommendation can be cited in README screenshots, spreadsheets, or future gallery pages.
