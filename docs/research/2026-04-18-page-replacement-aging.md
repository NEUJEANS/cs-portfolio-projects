# Research note — 2026-04-18 — page-replacement aging

## Question
How should the next `page-replacement-lab` realism slice approximate LRU without implementing exact recency stacks or timestamps?

## Brief references checked
- Gemini web search summary for the classic **aging page replacement** algorithm
- University notes from the University of Regina page-replacement overview (`https://www2.cs.uregina.ca/~anima/330/Notes/memory/page_replacement.html`)

## Takeaways used for the implementation
- Aging is a practical **LRU approximation** built around a per-page reference bit plus a small age register.
- On each refresh interval, the OS shifts the age register right, inserts the current reference bit into the high bit, and clears the reference bit.
- When eviction is needed, the page with the **smallest age value** is the coldest candidate.
- In this simulator, treating each reference as a refresh tick keeps the implementation deterministic and portfolio-friendly while still showing the intended recency-history behavior.

## Implementation choice
- Use an **8-bit age counter** per frame.
- Use the current reference access to set the frame's reference bit, then perform one aging tick at the end of the step.
- Break age-counter ties by oldest load time, then slot order, so the CLI and artifacts stay stable across runs.
