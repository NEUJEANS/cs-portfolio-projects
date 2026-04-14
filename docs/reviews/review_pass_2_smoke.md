# Review Pass 2 - Smoke Runs

Date: 2026-03-27 UTC

## Commands smoke-tested
- task tracker add/list
- expense tracker add/summary
- password auditor evaluation
- file integrity scan
- markdown notes search
- github repo reporter against `octocat`

## Findings
- all selected representative commands ran successfully
- one operator mistake during smoke test: `file-organizer-cli` was pointed at its own source folder, so it reorganized its own files

## Fix applied
- restored moved source files to original locations
- reran `npm test` for `file-organizer-cli` successfully

## Learned edge case
- organizer should ideally gain a dry-run mode and a guard against reorganizing directories that contain its own source/package metadata
