# Chord stabilization export review pass 1

- Checked the new `compare-stabilize-export` CLI end-to-end.
- Issue found: CSV output used CRLF line endings from the default `csv.writer`, which is awkward for Unix shell pipelines and repo diffs.
- Fix applied: set `lineterminator="\n"` for stable Unix-friendly output.
