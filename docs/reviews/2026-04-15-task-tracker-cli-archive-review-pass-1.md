# Task Tracker CLI Archive Review - Pass 1

## Focus
Archive snapshot output structure and determinism.

## Checks
- Read archive service implementation and snapshot rendering paths.
- Ran a manual archive CLI smoke check with a temporary data file.

## Issue found
- Archive markdown originally embedded the full `# Task Export` document inside another archive document, which created a redundant nested top-level heading and made the snapshot look less polished.

## Fix applied
- Reworked archive markdown rendering to emit a dedicated `# Completed Task Archive` document with an `## Archived tasks` section and a direct table.

## Result
- Archive snapshots now read like first-class project artifacts instead of wrapped exports.
