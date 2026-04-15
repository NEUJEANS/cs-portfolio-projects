# Mini MapReduce inspection batch refresh — 2026-04-15

## Why this slice
The next unfinished Mini MapReduce follow-up was multi-plugin inspection batches, so the main risk was extending CLI ergonomics without breaking the existing single-plugin JSON shape.

## Quick refresh
- `argparse` with `action="append"` is the simplest way to support repeated `--plugin` flags while keeping the CLI readable.
- CSV export should stay row-oriented, so a shared renderer that writes one header plus N plugin rows is cleaner than special-casing single vs multi-plugin paths.
- Backward compatibility matters for portfolio repos: single-plugin `inspect-plugin --output ...` should keep emitting the original object shape, while multi-plugin mode can emit a wrapper object with `plugin_count` and `plugins`.

## Self-test before coding
1. If `args.plugin` becomes a list, `inspect_plugin()` must not receive the raw list directly.
2. Single-plugin JSON output should still deserialize as an object with `name`, `mapper`, and `available_dataset_families` at top level.
3. Multi-plugin CSV output should produce exactly one header row and one row per inspected plugin.
4. The batch helper should work with both file-based plugins already in the project.
