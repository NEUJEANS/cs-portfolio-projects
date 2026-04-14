# Flashcard Quiz App Research — Tagged Deck Slice (2026-04-14)

## Goal
Turn the flashcard quiz app from a one-off CSV runner into a more portfolio-worthy study tool by supporting tagged cards and focused study sessions.

## Brief design notes
- Keep the file format simple: optional `tags` CSV column avoids forcing a migration for existing decks.
- Normalize tags to lowercase and deduplicate them for predictable filtering and reporting.
- Support repeated `--tag` flags so users can compose focused sessions without changing deck files.
- Require all requested tags to match to make filters precise and useful for demoing topic-specific review.
- Report weak tags from missed questions so the CLI gives lightweight feedback beyond raw score.

## Slice chosen
- optional `tags` column in CSV loader
- repeated `--tag` CLI filter
- weakest-tag summary based on missed cards
- tests and docs for the new workflow

## Why this is a strong next step
It upgrades the project from a toy quiz loop into a study utility with content organization, targeted practice, and basic performance feedback.
