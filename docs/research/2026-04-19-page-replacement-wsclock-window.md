# Research note — 2026-04-19 — page-replacement WSClock window

## Question
How should the next `page-replacement-lab` slice expose a tunable WSClock working-set window without making the simulator less explainable?

## Brief references checked
- Gemini web search summary for WSClock `tau` / working-set-window behavior
- NYU lecture note summary on WSClock (`https://cs.nyu.edu/~gottlieb/courses/2000s/2008-09-fall/os/wsclock-davis.html`)
- Winona State overview of WSClock (`https://cs.winona.edu/Francioni/cs405/wsclock.html`)

## Takeaways used for the implementation
- WSClock uses a tunable age threshold `tau` to decide whether a page still belongs to the current working set.
- Pages older than `tau` become stronger eviction candidates, while younger pages get passed over even if their reference bit is clear.
- The exact operating-system implementation is time-based and often interacts with dirty-bit cleaning, but a deterministic simulator can still capture the core trade-off with a per-reference age window.
- Keeping the default heuristic while adding an explicit override gives students both a sensible out-of-the-box demo and a controllable knob for experiments.

## Implementation choice
- Keep the existing default heuristic as `max(4, frames * 2)` so earlier runs stay stable.
- Add a `--wsclock-window` override to the relevant CLI commands rather than creating a separate WSClock-only subcommand.
- Persist the chosen mode and effective per-frame window into Markdown / CSV / JSON / SVG / HTML outputs so screenshots and downstream analysis stay reproducible.
