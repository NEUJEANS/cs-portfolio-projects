# Wrap-up — Chord DHT benchmark key variance

- Timestamp: 2026-04-16T04:48:50Z
- Project: `chord-dht-lab`
- What changed:
  - added per-key variance aggregation on top of seeded benchmark sample comparisons so the lab can show which lookups are most sensitive to start-node choice
  - added `benchmark-key-variance-export` Markdown/CSV CLI output for portfolio notes, charts, and spreadsheet pivots
  - updated the Chord README, checklist, and refresh note for the new per-key variance slice
- Tests/reviews run:
  - `python3 -m unittest tests/test_chord_dht_lab.py` (64 passed)
  - review pass 1: caught and fixed a newline-escaping syntax error in the first renderer insertion before rerunning the suite
  - review pass 2: exercised Markdown/CSV output from `benchmark-key-variance-export` and checked the reported sensitive-key ordering
  - review pass 3: reviewed the diff, ran `python3 -m py_compile projects/chord-dht-lab/chord_dht.py tests/test_chord_dht_lab.py`, and checked `benchmark-key-variance-export --help`
  - secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- Commit hash: `f33b4ee323d6313bbf46097d40c7feb117763548`
- Next step: add artifact-output flags so benchmark sample and per-key variance reports can be written directly to committed docs/examples without shell redirection.
