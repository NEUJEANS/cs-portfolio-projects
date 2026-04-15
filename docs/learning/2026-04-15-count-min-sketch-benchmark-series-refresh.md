# Count-Min Sketch benchmark-series refresh

## Quick refresh
- Count-Min Sketch error bounds do not depend on the hash seed, but observed collision patterns in concrete samples still can.
- Re-running the same stream across several seeds is useful for demo honesty: it shows whether a nice single-run result was typical or lucky.
- JSON artifacts preserve full run metadata; CSV exports make quick charting and spreadsheet review easy.

## Self-test
1. Why repeat the same CMS benchmark across multiple seeds if epsilon/delta stay fixed?
   - Because theoretical bounds stay fixed, but concrete collision behavior and overestimation on sample items can still vary by hash layout.
2. Why keep both JSON and CSV outputs?
   - JSON preserves nested metadata and per-run structure; CSV is simpler for plotting, spreadsheeting, and resumable comparisons.
