# flashcard-quiz-app

## Overview
Load CSV flashcards and run a command-line study session with reproducible shuffling, focused deck limits, topic-tag filters, and an optional retry round for missed cards.

## Stack
- Python
- standard library only (`argparse`, `csv`, `random`, `unittest`)

## Features
- validates CSV structure before starting a session
- reproducible shuffle order via `--seed` for demos and testing
- focused study rounds via `--limit`
- optional tagged decks via a `tags` CSV column
- repeated `--tag` filters for topic-specific sessions
- optional retry loop for missed cards via `--retry-incorrect`
- weakest-tag summary based on missed questions
- automated tests for validation, filtering, shuffle behavior, and retry flow

## CSV format
```csv
prompt,answer,tags
2+2,4,math
capital of France,Paris,geography
binary tree,node,"data-structures,trees"
```

The `tags` column is optional. When present, separate multiple tags with commas.

## Usage
```bash
python3 flashcards.py cards.csv --seed 7 --limit 5 --retry-incorrect
python3 flashcards.py cards.csv --tag algorithms --tag graphs --seed 3
```

Example session output:
```text
2+2: 5
Incorrect. Expected: 4
capital of France: Paris
Correct!

Retry round for missed cards:
2+2: 4
Correct!
Summary: 2 correct / 3 attempts across 2 unique cards
Weakest tags: math
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- store study history to track weak cards over time
- add import/export support for JSON or Anki-style formats
- add spaced-repetition scheduling recommendations
