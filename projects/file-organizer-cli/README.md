# file-organizer-cli

## Overview
A Node.js CLI that organizes loose files into extension-based folders with collision-safe moves, dry-run previews, and optional recursive processing.

## Why it is portfolio-worthy
- demonstrates practical file-system automation with a real CLI workflow
- handles common edge cases such as name collisions and cross-device moves
- includes tests for dry-run behavior, recursive traversal, and summary output
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
- prints either a readable text report or structured JSON output

## Usage
```bash
node organizer.js ~/Downloads --dry-run
node organizer.js ~/Downloads --recursive
node organizer.js ~/Downloads --recursive --json
```

Example text output:
```text
root: /home/student/Downloads
mode: dry-run
recursive: yes
total moves: 3
renamed to avoid collisions: 1
bucket documents: 1
bucket images: 2
/home/student/Downloads/report.pdf -> /home/student/Downloads/documents/report.pdf
/home/student/Downloads/photo.png -> /home/student/Downloads/images/photo.png
/home/student/Downloads/photo-copy.png -> /home/student/Downloads/images/photo-copy (1).png [renamed]
```

## Test
```bash
npm test
```

## Future Improvements
- add config-driven custom buckets instead of hard-coded extension lists
- support an undo manifest for rolling back a bulk organize pass
- add file-type detection beyond extensions for better categorization
