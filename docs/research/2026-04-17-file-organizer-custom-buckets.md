# File Organizer custom-buckets slice research — 2026-04-17

## Goal
Add a portfolio-worthy config layer to `file-organizer-cli` so a student can demonstrate custom categorization rules without editing source code.

## Brief findings
- Node's `fsPromises.readFile()` plus `JSON.parse()` is enough for a lightweight config-file path; there is no need for an extra parsing dependency.
- `path.extname()` is still the right primitive for the current extension-driven design, and lower-casing the extension keeps matching predictable.
- Config-driven rules should be explicit about precedence. Checking custom buckets before default buckets gives users a simple override story for extensions like `.json` or `.csv`.
- A config file can plausibly live inside the folder being organized, so the organizer should skip the active config file instead of treating it as another candidate input.

## Sources checked
- Node.js `fsPromises.readFile(...)` docs
- Node.js `path.extname(...)` docs

## Decisions for this slice
1. Add `--config <path>` with a simple JSON shape: `buckets`, optional `fallbackBucket`, and optional `extendDefaults`.
2. Normalize custom extensions case-insensitively and allow either `csv` or `.csv` in config files.
3. Let custom buckets override default extension mappings by evaluating custom rules first.
4. Reject ambiguous configs where the same custom extension is assigned to multiple custom buckets.
5. Skip the active config file during organize runs if it sits inside the target directory.
