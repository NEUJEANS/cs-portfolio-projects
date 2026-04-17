# file-organizer-cli

## Overview
A Node.js CLI that organizes loose files into extension-based folders with collision-safe moves, dry-run previews, optional recursive processing, and manifest-driven undo support.

## Why it is portfolio-worthy
- demonstrates practical file-system automation with a real CLI workflow
- handles common edge cases such as name collisions, cross-device moves, and safe rollback after a bulk organize pass
- includes tests for dry-run behavior, recursive traversal, manifest writing, and undo/restore flows
- easy to extend with custom rules or config-driven buckets

## Stack
- Node.js
- built-in `fs/promises`, `path`, and `node:test`

## Features
- groups files into `images`, `documents`, `audio`, `code`, `archives`, and `other`
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
node organizer.js ~/Downloads --recursive --manifest-out ./artifacts/downloads-run.json
node organizer.js --undo ./artifacts/downloads-run.json
node organizer.js --undo ./artifacts/downloads-run.json --dry-run --json
```

> Tip: if you redirect `--json` output to a file, write that file outside the directory being organized. Otherwise the redirected report file can become another candidate input during the same run.

Example organize output:
```text
root: /home/student/Downloads
action: organize
mode: apply
recursive: yes
total moves: 3
renamed to avoid collisions: 1
manifest: /home/student/Downloads/artifacts/downloads-run.json
bucket documents: 1
bucket images: 2
/home/student/Downloads/report.pdf -> /home/student/Downloads/documents/report.pdf
/home/student/Downloads/photo.png -> /home/student/Downloads/images/photo.png
/home/student/Downloads/photo-copy.png -> /home/student/Downloads/images/photo-copy (1).png [renamed]
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
bucket documents: 1
bucket images: 2
/home/student/Downloads/documents/report.pdf -> /home/student/Downloads/report.pdf
/home/student/Downloads/images/photo.png -> /home/student/Downloads/photo.png
/home/student/Downloads/images/photo-copy (1).png -> /home/student/Downloads/photo-copy.png
```

## Test
```bash
npm test
```

## Future Improvements
- add config-driven custom buckets instead of hard-coded extension lists
- add file-type detection beyond extensions for better categorization
- optionally sign or checksum manifests for tamper-evident bulk-operation history
