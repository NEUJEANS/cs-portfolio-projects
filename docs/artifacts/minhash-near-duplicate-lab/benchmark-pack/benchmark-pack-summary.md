# MinHash benchmark scenario pack

A committed benchmark pack with tiny, medium, and noisy corpora so you can demo expected recall behavior without hand-building test data each time.

- Generated at: `2026-04-21T21:11:36.911719+00:00`
- Scenario count: 3
- Total files written: 20
- Scenarios matching expected recall: 3/3

## Scenario summaries

### Tiny high-recall benchmark scenario

A tiny corpus with one obvious near-duplicate pair and two unrelated distractors so LSH should recover the true match cleanly.

- Scenario key: `tiny-high-recall`
- Scenario root: `tiny-high-recall`
- Files written: 4
- Exact pairs above threshold: 1
- Candidate pairs: 1
- Observed recall vs exact: 1.0000
- Expected recall range: 1.0000 to 1.0000
- Matches expectation: True
- Candidate reduction ratio: 0.8333
- Teaching note: Good for showing the happy path where a small corpus still keeps strong recall while reducing candidate comparisons.
- Report files: [json](tiny-high-recall-benchmark-report.json), [csv](tiny-high-recall-benchmark-report.csv), [markdown](tiny-high-recall-benchmark-report.md)

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py benchmark '<scenario-root>' --glob '*.txt' --token-mode word --shingle-size 2 --num-hashes 64 --bands 8 --threshold 0.3 --json
```

- Strongest exact pair: `docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/tiny-high-recall/plan_a.txt` <> `docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/tiny-high-recall/plan_b.txt` | exact=0.6000 estimated=0.6094

### Medium balanced-recall benchmark scenario

A medium corpus with multiple topical clusters where one pair is easy for banding and another sits near the threshold, illustrating recall tradeoffs.

- Scenario key: `medium-balanced`
- Scenario root: `medium-balanced`
- Files written: 8
- Exact pairs above threshold: 2
- Candidate pairs: 1
- Observed recall vs exact: 0.5000
- Expected recall range: 0.5000 to 0.5000
- Matches expectation: True
- Candidate reduction ratio: 0.9643
- Teaching note: Useful for interview discussion about how a realistic portfolio corpus can recover the strongest duplicates while still missing weaker overlaps without retuning.
- Report files: [json](medium-balanced-benchmark-report.json), [csv](medium-balanced-benchmark-report.csv), [markdown](medium-balanced-benchmark-report.md)

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py benchmark '<scenario-root>' --glob '*.txt' --token-mode word --shingle-size 3 --num-hashes 64 --bands 8 --threshold 0.25 --json
```

- Strongest exact pair: `docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/frontend_a.txt` <> `docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/medium-balanced/frontend_b.txt` | exact=0.7333 estimated=0.7188

### Noisy low-recall benchmark scenario

A noisy corpus where one partial near-duplicate pair exists but the default banding parameters miss it, creating a concrete tuning story instead of a perfect demo.

- Scenario key: `noisy-low-recall`
- Scenario root: `noisy-low-recall`
- Files written: 8
- Exact pairs above threshold: 1
- Candidate pairs: 0
- Observed recall vs exact: 0.0000
- Expected recall range: 0.0000 to 0.0000
- Matches expectation: True
- Candidate reduction ratio: 1.0000
- Teaching note: Shows why LSH parameter tuning matters, especially when only one pair overlaps and the rest of the corpus is unrelated noise.
- Report files: [json](noisy-low-recall-benchmark-report.json), [csv](noisy-low-recall-benchmark-report.csv), [markdown](noisy-low-recall-benchmark-report.md)

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py benchmark '<scenario-root>' --glob '*.txt' --token-mode word --shingle-size 3 --num-hashes 32 --bands 8 --threshold 0.2 --json
```

- Strongest exact pair: `docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/noisy-low-recall/partial_a.txt` <> `docs/artifacts/minhash-near-duplicate-lab/benchmark-pack/noisy-low-recall/partial_b.txt` | exact=0.5294 estimated=0.3438

