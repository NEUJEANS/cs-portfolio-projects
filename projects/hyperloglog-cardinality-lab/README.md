# hyperloglog-cardinality-lab

A portfolio-friendly Python project that implements a HyperLogLog sketch for approximate distinct counting.

## Why it is interesting
- demonstrates a classic probabilistic data structure used in analytics systems
- shows the tradeoff between memory usage and estimation accuracy
- includes sketch merge support, which maps well to distributed systems conversations
- stays practical: you can build sketches from files and inspect accuracy with simulations
- now supports counting distinct values from newline-delimited text, CSV exports, JSONL event streams, and JSON arrays without pre-cleaning the data by hand

## Features
- configurable precision (`2^p` registers)
- newline-delimited file ingestion into a reusable JSON sketch
- CSV field extraction for counting distinct values directly from exported analytics tables
- dotted-path JSON/JSONL field extraction for event logs such as `actor.id` or `event.visitor.id`
- extension-based input-format auto detection for `.txt`, `.csv`, `.jsonl`/`.ndjson`, and `.json` inputs
- distinct-count estimation with small-range correction
- sketch merge support for combining partial counts
- simulation mode to compare observed error with the theoretical error bound
- benchmark/report mode for precision-vs-error-vs-memory sweeps across multiple cardinalities
- CSV export for plotting or spreadsheet analysis of benchmark rows
- self-contained SVG chart export for portfolio screenshots, README embeds, or GitHub Pages assets

## Usage

Build a sketch from newline-delimited input:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py build \
  --input artifacts/users.txt \
  --output artifacts/users_hll.json \
  --precision 10
```

Build a sketch straight from a CSV export by selecting the user ID column:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py build \
  --input artifacts/events.csv \
  --output artifacts/events_users_hll.json \
  --precision 10 \
  --field user_id
```

Count distinct visitor IDs from a JSON Lines event log using a dotted field path:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py build \
  --input artifacts/events.jsonl \
  --output artifacts/events_visitors_hll.json \
  --precision 10 \
  --field event.visitor.id
```

Count distinct values from a JSON array as well:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py build \
  --input artifacts/events.json \
  --output artifacts/events_json_hll.json \
  --precision 10 \
  --field actor.id
```

Override the parser explicitly when the file extension is not enough:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py build \
  --input artifacts/export.data \
  --input-format csv \
  --csv-delimiter ';' \
  --field user_id \
  --output artifacts/export_hll.json
```

Inspect sketch statistics:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py stats --sketch artifacts/users_hll.json
```

Merge sketches from multiple shards (with the same precision):

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py merge \
  --output artifacts/merged_hll.json \
  artifacts/shard_a.json artifacts/shard_b.json artifacts/shard_c.json
```

Sample estimation accuracy:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py simulate \
  --precision 10 \
  --cardinality 5000 \
  --trials 20 \
  --seed 42
```

Generate a benchmark sweep and publish JSON, Markdown, CSV, plus an SVG chart:

```bash
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py benchmark \
  --precisions 8,10,12 \
  --cardinalities 200,2000,20000 \
  --trials 8 \
  --seed 7 \
  --json-output artifacts/hyperloglog-benchmark-report.json \
  --markdown-output docs/artifacts/hyperloglog-benchmark-report.md \
  --csv-output artifacts/hyperloglog-benchmark-report.csv \
  --svg-output docs/artifacts/hyperloglog-benchmark-report.svg
```

The generated Markdown report is handy for portfolio write-ups because it summarizes the lowest-error sampled precision for each target cardinality in a GitHub-friendly table. The CSV export feeds notebooks or spreadsheets, and the SVG chart is self-contained so it can be embedded directly into a README or GitHub Pages portfolio site without extra plotting dependencies.

## Example build output

```json
{
  "inserted": 4,
  "output": "artifacts/events_users_hll.json",
  "input_format": "csv",
  "field": "user_id",
  "records_read": 4,
  "records_with_values": 4,
  "records_skipped": 0,
  "precision": 10,
  "register_count": 1024,
  "zero_registers": 1020,
  "max_register": 2,
  "raw_estimate": 739.1637920942611,
  "estimate": 4.007832904843586,
  "rounded_estimate": 4,
  "relative_error_bound": 0.0325
}
```

## Test

```bash
python3 -m unittest projects/hyperloglog-cardinality-lab/test_hyperloglog.py
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py build --input artifacts/events.csv --field user_id --output artifacts/events_users_hll.json
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py build --input artifacts/events.jsonl --field event.visitor.id --output artifacts/events_visitors_hll.json
python3 projects/hyperloglog-cardinality-lab/hyperloglog.py benchmark --precisions 8,10 --cardinalities 200,2000 --trials 4 --seed 7 --csv-output artifacts/hyperloglog-benchmark-report.csv --svg-output docs/artifacts/hyperloglog-benchmark-report.svg
```

## Design notes
- The first `p` bits of the hash choose the register, and the remaining bits measure the first observed `1` via the leading-zero count.
- Small-range linear counting is used when many registers are still empty because the raw estimator is biased for tiny cardinalities.
- Merge works by taking the register-wise maximum, which mirrors how distributed analytics systems aggregate shard-local sketches.
- Build-mode field extraction intentionally accepts only scalar values so the count stays tied to a clear entity such as a user ID, session ID, or SKU.
- JSON field extraction supports dotted paths and numeric path segments, which makes nested event payloads usable without adding a separate preprocessing script.

## Future improvements
- add register compression to compare dense vs sparse storage
- add a tiny static HTML gallery that pairs the generated SVG chart with the Markdown benchmark summary
- add side-by-side Bloom filter and HyperLogLog demos for probabilistic data structure interviews
