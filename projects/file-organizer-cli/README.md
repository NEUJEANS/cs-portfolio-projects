# file-organizer-cli

## Overview
A Node.js CLI that organizes loose files into extension-based, basename-pattern-aware, and MIME-aware folders with collision-safe moves, dry-run previews, optional recursive processing, built-in/exportable bucket presets, config-driven custom buckets, CI-friendly config linting, checksum-backed manifests, detached manifest signatures, trusted signer policies with multi-signer quorums, and manifest-driven undo support.

## Why it is portfolio-worthy
- demonstrates practical file-system automation with a real CLI workflow
- handles common edge cases such as name collisions, cross-device moves, reusable preset/config workflows, custom extension + basename + MIME categorization rules, CI-ready config validation, checksum-backed audit manifests, detached signer proof, trusted signer-policy allowlists, multi-reviewer quorum checks, and safe rollback after a bulk organize pass
- includes tests for dry-run behavior, recursive traversal, preset export/import flows, config parsing/linting, MIME sniffing, basename-pattern matching, checksum-backed + detached-signed manifest writing, signer-policy quorum enforcement, and undo/restore flows
- easy to demo with realistic folders like `Downloads`, class assets, screenshots, or project exports
- now ships a reproducible demo artifact bundle under [`docs/artifacts/file-organizer-cli/`](../../docs/artifacts/file-organizer-cli/) so reviewers can see config cleanup, dry-run output, before/after trees, and undo proof without running the CLI first

## Stack
- Node.js
- built-in `crypto`, `fs/promises`, `path`, and `node:test`

## Features
- groups files into default `images`, `documents`, `audio`, `code`, `archives`, and `other` buckets
- supports `--preset <name>` for built-in portfolio-ready bucket presets such as `coursework`, `data-science`, and `frontend-assets`
- supports `--list-presets` and `--write-preset <name> <path>` so teams can export and share reusable bucket JSON files
- supports `--config buckets.json` for custom buckets, extension overrides, basename-pattern rules, MIME-aware rules, and custom fallback bucket names
- lets shared configs promote filename patterns like `Screenshot *` or `assignment-*` before MIME and extension fallback rules run
- supports `--lint-config buckets.json` so shared bucket JSON can be validated in CI before teammates run a real organize pass
- supports `--preview-normalized-config`, `--fix-config`, and `--write-normalized-config` so teams can review and then apply canonical shared-config cleanup across extension, basename, and MIME rule lists
- preserves existing files by renaming collisions like `notes (1).txt`
- supports `--dry-run` to preview work without changing the file system
- supports `--recursive` to organize nested folders while skipping already-organized bucket folders
- falls back from `rename` to copy-and-delete when a cross-device `EXDEV` move occurs
- optionally writes a JSON manifest with `--manifest-out` so the exact run can be audited or undone later
- supports `--manifest-checksum` to embed a SHA-256 checksum in the manifest for tamper-evident bulk-operation history
- supports `--undo manifest.json` to restore files from a saved non-dry-run organize manifest, including collision-safe restore names, empty bucket cleanup, automatic checksum verification, and optional detached-signature verification when authorship matters
- supports `--sign-manifest <private-key.pem>` plus `--verify-manifest-signature <public-key.pem>` for detached signer proof on checksum-backed manifests
- supports `--signer-policy trusted-signers.json` so shared teams can allowlist trusted signer fingerprints, attach reviewer labels/roles, and enforce multi-signer quorum rules during verification
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
node organizer.js ~/Downloads --config ./buckets.json --recursive --manifest-out ./artifacts/downloads-run.json --manifest-checksum
node organizer.js ~/Downloads --config ./buckets.json --recursive --manifest-out ./artifacts/downloads-run.json --manifest-checksum --sign-manifest ./keys/team.pem
node organizer.js ~/Downloads --config ./buckets.json --recursive --manifest-out ./artifacts/downloads-run.json --manifest-checksum --sign-manifest ./keys/team.pem --signer-policy ./keys/trusted-signers.json
node organizer.js ./artifacts/downloads-run.json --sign-manifest ./keys/reviewer.pem --signature-path ./artifacts/downloads-run.json.sig.json --signer-policy ./keys/trusted-signers.json
node organizer.js ~/Downloads --config ./pattern-buckets.json --dry-run
node organizer.js ~/Downloads --config ./mime-buckets.json --dry-run
node organizer.js --lint-config ./shared/coursework-buckets.json
node organizer.js --lint-config ./shared/coursework-buckets.json --json
node organizer.js --preview-normalized-config ./shared/coursework-buckets.json
node organizer.js --fix-config ./shared/coursework-buckets.json
node organizer.js --write-normalized-config ./shared/coursework-buckets.raw.json ./shared/coursework-buckets.json --force
node organizer.js --undo ./artifacts/downloads-run.json
node organizer.js --undo ./artifacts/downloads-run.json --dry-run --json
node organizer.js --undo ./artifacts/downloads-run.json --verify-manifest-signature ./keys/team.pub.pem
node organizer.js --undo ./artifacts/downloads-run.json --verify-manifest-signature ./keys/team.pub.pem --signature-path ./artifacts/downloads-run.sig.json
node organizer.js --undo ./artifacts/downloads-run.json --verify-manifest-signature ./keys/team.pub.pem --signature-path ./artifacts/downloads-run.sig.json --signer-policy ./keys/trusted-signers.json
node organizer.js --undo ./artifacts/downloads-run.json --signer-policy ./keys/trusted-signers.json
node organizer.js --undo ./artifacts/downloads-run.json --skip-manifest-verification
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
    "screenshots": {
      "basenamePatterns": ["Screenshot *", "screen shot *"]
    },
    "assignments": {
      "extensions": [".txt", ".md"],
      "basenamePatterns": ["assignment-*", "quiz-2026-04-1?"]
    },
    "data-dumps": {
      "mimeTypes": ["application/json"]
    },
    "vectorish": {
      "mimePrefixes": ["image/"]
    },
    "design": ["fig", ".sketch"]
  },
  "fallbackBucket": "misc",
  "extendDefaults": true
}
```

Notes:
- `extendDefaults: true` keeps the built-in buckets active after checking custom rules first.
- custom buckets can override default extension mappings, so `.json` can move into `datasets` instead of `other` or another default bucket.
- basename patterns match the filename without its extension, are case-insensitive, and support `*` (any run of characters) plus `?` (single character).
- MIME rules sniff up to the first 4096 bytes and recognize common signatures plus UTF-8 text shapes such as JSON, HTML, XML, and SVG.
- basename pattern matches run before MIME and extension fallback, so `Screenshot 2026-04-18.png` can land in `screenshots` even though `.png` normally maps to `images`.
- MIME type and MIME prefix matches run before extension fallback, so a misleading `report.txt` that actually contains JSON can land in `data-dumps` instead of `documents`.
- bucket names must be simple folder names, and each custom extension, basename pattern, MIME type, or MIME prefix can belong to only one custom bucket.
- `--preset` and `--config` are mutually exclusive; use `--preset` for the bundled quick-start presets or `--write-preset ...` + `--config` when you want a file you can share in Git.
- `--write-preset` refuses to overwrite existing files unless `--force` is provided.
- `--config` is only used for organize runs; undo replays the exact manifest paths that were recorded earlier.
- `--manifest-checksum` only applies when `--manifest-out` is also used; it stores a SHA-256 digest over the manifest payload so later edits show up during undo.
- `--sign-manifest` requires `--manifest-checksum`; it writes a detached sidecar file next to the manifest by default (for example `downloads-run.json.sig.json`) unless you override it with `--signature-path`.
- `--undo` verifies checksum metadata automatically when present and fails closed on tampered manifests unless you intentionally bypass it with `--skip-manifest-verification`.
- `--verify-manifest-signature` adds detached-signature verification on top of the checksum check so teams can require both integrity and authorship before files are restored.
- `--signer-policy` lets a shared team publish trusted signer fingerprints plus optional reviewer labels, roles, notes, and `approvalQuorum` rules; signing fails closed if the private key is not in the allowlist, and verification fails closed when trusted approvals or required roles are missing.
- the active config file and active signing inputs (manifest path, signature path, private key, signer policy) are skipped automatically if they live inside the directory being organized.

> Tip: if you redirect `--json` output to a file, write that file outside the directory being organized. Otherwise the redirected report file can become another candidate input during the same run.

Example organize output:
```text
root: /home/student/Downloads
action: organize
mode: apply
recursive: yes
total moves: 3
renamed to avoid collisions: 1
manifest checksum: sha256:0f6d2b9d1c6b0f72dff18fd8c80f0b841d8c17ce6bb0d6b6df85f9f2f44e6e74
config: /home/student/Downloads/buckets.json
manifest: /home/student/Downloads/artifacts/downloads-run.json
manifest signature: /home/student/Downloads/artifacts/downloads-run.json.sig.json
manifest signer fingerprint: sha256:3f55b9ec8c54d7d4a3d8a2037d6d00c6a17c8071c212dc8d1a8a6d0cc7f7f2f1
manifest signer label: TA laptop key
manifest signer roles: organize-approver, undo-approver
signer policy: Course staff signing policy
bucket data-dumps: 1
bucket datasets: 1
bucket images: 1
/home/student/Downloads/report.csv -> /home/student/Downloads/datasets/report.csv
/home/student/Downloads/report.txt -> /home/student/Downloads/data-dumps/report.txt [MIME type application/json; detected application/json]
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
- reports normalization warnings for bucket names, fallback buckets, extension spellings like `CSV` -> `.csv`, basename patterns like ` Screenshot * ` -> `screenshot *`, and MIME rules like ` Application/JSON ` -> `application/json` or ` image/* ` -> `image/`
- flags duplicate custom extensions, duplicate basename patterns, overlapping MIME rules, or invalid `extendDefaults` values before the config is used in a live organize run
- warns about unknown top-level keys or ignored per-bucket fields so teams notice stray metadata that the organizer will ignore

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
- lowercases/sorts basename patterns and MIME rule lists, removes duplicates, and rewrites mixed rule objects into stable canonical JSON
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
manifest checksum verified: yes
manifest checksum: sha256:0f6d2b9d1c6b0f72dff18fd8c80f0b841d8c17ce6bb0d6b6df85f9f2f44e6e74
manifest signature verified: yes
manifest signature file: /home/student/Downloads/artifacts/downloads-run.json.sig.json
manifest signer fingerprint: sha256:3f55b9ec8c54d7d4a3d8a2037d6d00c6a17c8071c212dc8d1a8a6d0cc7f7f2f1
manifest signer label: TA laptop key
manifest signer roles: organize-approver, undo-approver
signer policy: Course staff signing policy
bucket datasets: 1
bucket images: 2
/home/student/Downloads/datasets/report.csv -> /home/student/Downloads/report.csv
/home/student/Downloads/images/photo.png -> /home/student/Downloads/photo.png
/home/student/Downloads/images/photo-copy (1).png -> /home/student/Downloads/photo-copy.png
```

## Manifest integrity
Use `--manifest-checksum` when you want the manifest itself to become tamper-evident. The CLI writes a SHA-256 digest into the manifest, and later `--undo` runs automatically verify that digest before moving files back.

```bash
node organizer.js ~/Downloads --manifest-out ./artifacts/downloads-run.json --manifest-checksum
node organizer.js --undo ./artifacts/downloads-run.json
```

If a teammate or script edits the manifest afterward, undo fails with an integrity error instead of silently trusting the modified history. For deliberate recovery from a partially repaired manifest, you can opt out explicitly:

```bash
node organizer.js --undo ./artifacts/downloads-run.json --skip-manifest-verification
```

## Manifest authorship verification
Use detached signatures when the manifest should prove not only *what* changed, but also *who approved or produced* the organize run. The CLI signs the checksum-backed manifest payload with a private key, stores approvals in a sidecar JSON file, and lets undo verify those approvals with either an explicit public key or a trusted signer policy.

```bash
node organizer.js ~/Downloads --manifest-out ./artifacts/downloads-run.json --manifest-checksum --sign-manifest ./keys/team.pem
node organizer.js --undo ./artifacts/downloads-run.json --verify-manifest-signature ./keys/team.pub.pem
```

If a class team, lab staff group, or club repo shares several signing keys, add `--signer-policy trusted-signers.json` to either command. The policy file stores an allowlist of trusted signer fingerprints plus optional `label`, `roles`, and `notes` metadata, and it can also define an `approvalQuorum` so undo fails closed until enough trusted reviewers have signed the same manifest payload.

```json
{
  "name": "Course staff signing policy",
  "description": "Trusted signing keys for organizer undo approvals.",
  "approvalQuorum": {
    "minimumSigners": 2,
    "requiredRoles": ["organize-approver", "undo-approver"]
  },
  "trustedSigners": [
    {
      "fingerprint": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
      "label": "Organizer reviewer",
      "roles": ["organize-approver"],
      "notes": "Approves organize passes."
    },
    {
      "fingerprint": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
      "label": "Undo reviewer",
      "roles": ["undo-approver"],
      "notes": "Approves rollback operations."
    }
  ]
}
```

Append another approval later by passing the existing manifest path as the positional argument on a follow-up `--sign-manifest` run, then use `--undo ... --signer-policy trusted-signers.json` when you want the policy itself to verify the whole approval bundle.

```bash
node organizer.js ./artifacts/downloads-run.json --sign-manifest ./keys/undo-reviewer.pem --signature-path ./artifacts/downloads-run.json.sig.json --signer-policy ./keys/trusted-signers.json
node organizer.js --undo ./artifacts/downloads-run.json --signer-policy ./keys/trusted-signers.json
```

Use `--signature-path` if the sidecar should live somewhere other than the default `<manifest>.sig.json` location. The published demo bundle commits only public keys, the trusted signer policy, and the detached-signature proof artifacts — never the private keys.

## Demo artifact bundle
Generate the committed demo walkthrough bundle:

```bash
npm run demo:artifacts
```

Published bundle:
- [`demo summary`](../../docs/artifacts/file-organizer-cli/demo-summary.md)
- [`before tree`](../../docs/artifacts/file-organizer-cli/demo-source-tree.txt)
- [`config preview`](../../docs/artifacts/file-organizer-cli/demo-config.preview.txt)
- [`normalized config`](../../docs/artifacts/file-organizer-cli/demo-config.normalized.json)
- [`dry-run report`](../../docs/artifacts/file-organizer-cli/demo-dry-run-report.txt)
- [`apply report`](../../docs/artifacts/file-organizer-cli/demo-apply-report.txt)
- [`manifest payload`](../../docs/artifacts/file-organizer-cli/demo-manifest.json)
- [`detached signature`](../../docs/artifacts/file-organizer-cli/demo-manifest.sig.json)
- [`trusted signer policy`](../../docs/artifacts/file-organizer-cli/demo-trusted-signers.json)
- [`organize reviewer public key`](../../docs/artifacts/file-organizer-cli/demo-organize-approver.pub.pem)
- [`undo reviewer public key`](../../docs/artifacts/file-organizer-cli/demo-undo-approver.pub.pem)
- [`signature verification proof`](../../docs/artifacts/file-organizer-cli/demo-signature-verify.txt)
- [`after tree`](../../docs/artifacts/file-organizer-cli/demo-after-tree.txt)
- [`undo report`](../../docs/artifacts/file-organizer-cli/demo-undo-report.txt)
- [`restored tree`](../../docs/artifacts/file-organizer-cli/demo-restored-tree.txt)

The generator runs the organizer against an isolated temp folder, writes a warning-heavy raw config plus its canonical normalized version, captures dry-run/apply/undo reports with checksum-backed + detached multi-signer manifest approvals plus a trusted signer policy, exports sample public keys for both reviewers, and sanitizes the temp paths into a stable `/demo/file-organizer-cli` prefix for readable Git-tracked artifacts.

## Test
```bash
npm test
npm run demo:artifacts
```

## Future Improvements
- add approval expiry/freshness windows so stale multi-signer bundles can be rejected after a review deadline
