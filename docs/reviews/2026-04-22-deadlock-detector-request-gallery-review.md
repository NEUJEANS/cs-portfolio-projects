# deadlock-detector-lab Banker request gallery review log

## Pass 1, portfolio-story audit
- reviewed the new gallery outputs for whether the safe and unsafe request difference was obvious in one glance
- found issue: the gallery summarized decision and safe sequence but did not explicitly surface whether any process was runnable right after each trial
- fix: added `First runnable set` to the Markdown table, HTML comparison table, and per-request cards

## Pass 2, unsafe-path audit
- reviewed the denied-request card and highlight copy for whether the unsafe path explanation was concrete enough
- found issue: the top-level highlight mentioned denial and blocking but still buried the most important contrast, that the unsafe trial leaves no runnable process
- fix: updated gallery highlight copy to say that the denied trial leaves no runnable process before listing shortages

## Pass 3, determinism audit
- reran the unsafe trace and comparison gallery exports into a temporary directory and compared Markdown, SVG, HTML, and JSON outputs with `cmp`
- result: all regenerated artifacts matched byte-for-byte, so the committed samples are deterministic and resumable
