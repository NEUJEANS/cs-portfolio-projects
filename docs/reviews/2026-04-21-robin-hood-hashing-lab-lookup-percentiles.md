# robin-hood-hashing-lab lookup percentile review log

Date: 2026-04-21

## Review pass 1, p95 delta sign was backwards
- The first lookup-tail comparison table computed `hit/miss p95 delta vs linear` as `robin - linear`.
- Problem found: that made Robin Hood wins show up as negative deltas, which read backwards next to the winner labels.
- Fix: flipped the delta to `linear - robin` so positive values consistently mean Robin Hood had the shorter tail.

## Review pass 2, the HTML detail cards were noisy
- The first draft listed average successful and unsuccessful lookup probes twice, once alone and once inside the new `avg / p50 / p95 / max` callouts.
- Problem found: the repeated lines made the card harder to scan and diluted the new percentile story.
- Fix: collapsed each lookup mode into one compact side-by-side percentile line, while keeping the stddev and other supporting metrics below it.

## Review pass 3, the HTML tail-winner panel was too fragile
- The first HTML implementation embedded a nested conditional f-string directly inside the big page template.
- Problem found: it worked, but it was brittle and harder to maintain during future dashboard edits.
- Fix: extracted the optional tail-winner section into a dedicated `lookup_tail_panel_html` block before the final page template assembly.
