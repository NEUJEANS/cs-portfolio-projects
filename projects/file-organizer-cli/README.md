# file-organizer-cli

## Overview
A Node.js CLI that organizes loose files into extension-based folders with collision-safe moves, dry-run previews, optional recursive processing, built-in/exportable bucket presets, config-driven custom buckets, CI-friendly config linting, and manifest-driven undo support.

## Why it is portfolio-worthy
- demonstrates practical file-system automation with a real CLI workflow
- handles common edge cases such as name collisions, cross-device moves, reusable preset/config workflows, custom categorization rules, CI-ready config validation, and safe rollback after a bulk organize pass
- includes tests for dry-run behavior, recursive traversal, preset export/import flows, config parsing/linting, manifest writing, and undo/restore flows
- easy to demo with realistic folders like `Downloads`, class assets, screenshots, or project exports

## Stack
- Node.js
- built-in `fs/promises`, `path`, and `node:test`

## Features
- groups files into default `images`, `documents`, `audio`, `code`, `archives`, and `other` buckets
- supports `--preset <name>` for built-in portfolio-ready bucket presets such as `coursework`, `data-science`, and `frontend-assets`
- supports `--list-presets` and `--write-preset <name> <path>` so teams can export and share reusable bucket JSON files
- supports `--config buckets.json` for custom buckets, extension overrides, and custom fallback bucket names
- supports `--lint-config buckets.json` so shared bucket JSON can be validated in CI before teammates run a real organize pass
- supports `--preview-normalized-config`, `--fix-config`, and `--write-normalized-config` so teams can review and then apply canonical shared-config cleanup
- preserves existing files by renaming collisions like `notes (1).txt`
- supports `--dry-run` to preview work without changing the file system
- supports `--recursive` to organize nested folders while skipping already-organized bucket folders
- falls back from `rename` to copy-and-delete when a cross-device `EXDEV` move occurs
- optionally writes a JSON manifest with `--manifest-out` so the exact run can be audited or undone later
- supports `--undo manifest.json` to restore files from a saved non-dry-run organize manifest, including collision-safe restore names and empty bucket cleanup
- prints either a readable text report or structured JSON output

## Usage
```bash
node organizer.js ~/Downloads --dry-run
node organizer.js ~/Downloads --recursive
node organizer.js ~/Downloads --preset coursework --recursive
node organizer.js --list-presets
node organizer.js --write-preset data-science ./presets/data-science.json
node organizer.js --write-preset data-science ./presets/data-science.json --force
node organizer.js ~/Downloads --config ./buckets.json --recursive
node organizer.js ~/Downloads --config ./buckets.json --recursive --manifest-out ./artifacts/downloads-run.json
node organizer.js --lint-config ./shared/coursework-buckets.json
node organizer.js --lint-config ./shared/coursework-buckets.json --json
node organizer.js --preview-normalized-config ./shared/coursework-buckets.json
node organizer.js --fix-config ./shared/coursework-buckets.json
node organizer.js --write-normalized-config ./shared/coursework-buckets.raw.json ./shared/coursework-buckets.json --force
node organizer.js --undo ./artifacts/downloads-run.json
node organizer.js --undo ./artifacts/downloads-run.json --dry-run --json
```

## Built-in presets
Inspect the preset catalog:

```bash
node organizer.js --list-presets
```

Use a preset directly for a quick one-off organize run:

```bash
node organizer.js ~/Downloads --preset coursework --recursive
```

Export a sharable preset config, commit it in a repo, and reuse the same JSON later with `--config`:

```bash
node organizer.js --write-preset coursework ./shared/coursework-buckets.json
node organizer.js --write-preset coursework ./shared/coursework-buckets.json --force
node organizer.js ~/Downloads --config ./shared/coursework-buckets.json --recursive
```

Current presets:
- `coursework` — separates datasets, notebooks, slides, and diagrams for class/project submissions
- `data-science` — emphasizes datasets, notebooks, figures, and experiment manifests
- `frontend-assets` — groups design mockups, vector files, screen recordings, and handoff docs

## Custom bucket config
Example `buckets.json`:

```json
{
  "buckets": {
    "datasets": ["csv", ".tsv", ".json"],
    "slides": ["ppt", ".pptx", ".key"],
    "design": ["fig", ".sketch"]
  },
  "fallbackBucket": "misc",
  "extendDefaults": true
}
```

Notes:
- `extendDefaults: true` keeps the built-in buckets active after checking custom rules first.
- custom buckets can override default extension mappings, so `.json` can move into `datasets` instead of `other` or another default bucket.
- bucket names must be simple folder names, and each custom extension can belong to only one custom bucket.
- `--preset` and `--config` are mutually exclusive; use `--preset` for the bundled quick-start presets or `--write-preset ...` + `--config` when you want a file you can share in Git.
- `--write-preset` refuses to overwrite existing files unless `--force` is provided.
- `--config` is only used for organize runs; undo replays the exact manifest paths that were recorded earlier.
- the active config file is skipped automatically if it lives inside the directory being organized.

> Tip: if you redirect `--json` output to a file, write that file outside the directory being organized. Otherwise the redirected report file can become another candidate input during the same run.

Example organize output:
```text
root: /home/student/Downloads
action: organize
mode: apply
recursive: yes
config: /home/student/Downloads/buckets.json
total moves: 3
renamed to avoid collisions: 1
manifest: /home/student/Downloads/artifacts/downloads-run.json
bucket datasets: 1
bucket images: 2
/home/student/Downloads/report.csv -> /home/student/Downloads/datasets/report.csv
/home/student/Downloads/photo.png -> /home/student/Downloads/images/photo.png
/home/student/Downloads/photo-copy.png -> /home/student/Downloads/images/photo-copy (1).png [renamed]
```

## Shared config linting
Use `--lint-config` to validate a shareable bucket JSON file without touching any real folders. This is useful in CI, pre-commit hooks, or review scripts before someone runs the organizer on a real `Downloads/` or project asset directory.

```bash
node organizer.js --lint-config ./shared/coursework-buckets.json
node organizer.js --lint-config ./shared/coursework-buckets.json --json
```

The lint report:
- exits cleanly for valid configs and returns exit code `1` for invalid configs
- reports normalization warnings for bucket names, fallback buckets, and extension spellings like `CSV` -> `.csv`
- flags duplicate custom extensions or invalid `extendDefaults` values before the config is used in a live organize run
- warns about unknown top-level keys so teams notice stray metadata that the organizer will ignore

Example lint output:
```text
action: lint-config
config: /home/student/shared/coursework-buckets.json
status: valid
warnings: 2
errors: 0
normalized fallback bucket: misc
extends defaults: yes
custom buckets: datasets, slides
warning 1: Bucket datasets extension "CSV" will normalize to ".csv".
warning 2: Unknown top-level key "owner" will be ignored by the organizer.
No errors found.
```

## Normalization preview
Use `--preview-normalized-config` when you want a review-friendly summary of what the canonical rewrite would change before touching the file. This is useful in code review, CI notes, or teammate handoffs where you want to inspect the cleanup plan first.

```bash
node organizer.js --preview-normalized-config ./shared/coursework-buckets.json
node organizer.js --preview-normalized-config ./shared/coursework-buckets.json --json
```

The preview report highlights:
- whether a rewrite is needed at all
- which keys, bucket names, or extensions will change or disappear
- the canonical fallback bucket, bucket list, and `extendDefaults` value that a real write would produce
- whether you should follow up with `--fix-config` or `--write-normalized-config`

Example preview output:
```text
action: preview-normalized-config
config: /home/student/shared/coursework-buckets.json
status: valid
rewrite needed: yes
changes: 4
warnings: 3
errors: 0
normalized fallback bucket: misc
extends defaults: yes
custom buckets: datasets, slides
change 1: Remove unknown top-level key "owner".
change 2: Normalize fallback bucket " misc " -> "misc".
change 3: Normalize extension for bucket datasets: "CSV" -> ".csv".
change 4: Add default extendDefaults=true.
Preview only. Use --fix-config or --write-normalized-config to apply these changes.
```

## Normalized config writers
Use the normalized-config helpers when you want the CLI to clean up a warning-heavy shared config before it gets committed.

```bash
node organizer.js --fix-config ./shared/coursework-buckets.json
node organizer.js --write-normalized-config ./shared/coursework-buckets.raw.json ./shared/coursework-buckets.json --force
```

The normalized writer:
- trims bucket and fallback names into canonical folder-safe values
- lowercases and dot-prefixes extensions while removing duplicates
- strips unknown top-level keys so the saved JSON matches what the organizer actually reads
- writes stable key ordering for cleaner code review diffs across teammates
- refuses to normalize invalid configs until the real errors are fixed

> Tip: keep raw review artifacts (like `write.json` or an un-fixed `raw.json`) outside the directory you plan to organize. Only the active `--config` path is auto-skipped during an organize run.

Example normalized-config output:
```text
action: write-normalized-config
config: /home/student/shared/coursework-buckets.raw.json
destination: /home/student/shared/coursework-buckets.json
mode: copy
resolved warnings: 2
fallback bucket: misc
extends defaults: yes
custom buckets: datasets, slides
resolved warning 1: Unknown top-level key "owner" will be ignored by the organizer.
resolved warning 2: Bucket datasets extension "CSV" will normalize to ".csv".
Normalized config written.
```

Example undo output:
```text
root: /home/student/Downloads
action: undo
mode: apply
manifest: /home/student/Downloads/artifacts/downloads-run.json
total manifest entries: 3
restored files: 3
missing current files: 0
renamed to avoid restore collisions: 0
removed empty directories: 2
bucket datasets: 1
bucket images: 2
/home/student/Downloads/datasets/report.csv -> /home/student/Downloads/report.csv
/home/student/Downloads/images/photo.png -> /home/student/Downloads/photo.png
/home/student/Downloads/images/photo-copy (1).png -> /home/student/Downloads/photo-copy.png
```

## Test
```bash
npm test
```

## Future Improvements
- support richer matching rules beyond extensions, such as basename patterns or MIME-aware detection
- add small publishable demo artifacts that show config preview output beside before/after folder trees
- optionally sign or checksum manifests for tamper-evident bulk-operation history
