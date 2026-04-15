# Mini MapReduce plugin metadata diff refresh

## Goal
Add a resumable JSON diff view for batched plugin inspections without breaking the existing single-plugin JSON output or CSV snapshot flow.

## Quick refresh
- dataclasses are a good fit for diff payloads when the output needs explicit structure and stable JSON serialization through `as_dict()` helpers
- for a CLI flag that changes payload shape instead of file destinations, `action="store_true"` keeps argparse behavior simple and readable
- adjacent diffs are enough for a first portfolio-friendly comparison pass: compare plugin `n-1` to plugin `n` in the order provided so the output tells a simple review story

## Self-test before coding
- can I keep single-plugin `inspect-plugin` output unchanged when `--diff` is not used? yes
- what should happen if `--diff` is passed with only one plugin? fail fast with a clean parser error
- should CSV change too? no, keep CSV as a plain snapshot export and add diffs only to the JSON payload for now
