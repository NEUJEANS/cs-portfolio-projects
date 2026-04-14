# flashcard-quiz-app

## Overview
Load CSV flashcards and run a command-line study session with reproducible shuffling, focused deck limits, and an optional retry round for missed cards.

## Stack
- Python
- standard library only (`argparse`, `csv`, `random`, `unittest`)

## Features
- validates CSV structure before starting a session
- reproducible shuffle order via `--seed` for demos and testing
- focused study rounds via `--limit`
- optional retry loop for missed cards via `--retry-incorrect`
- automated tests for validation, shuffle behavior, and retry flow

## CSV format
```csv
prompt,answer
2+2,4
capital of France,Paris
```

## Usage
```bash
python3 flashcards.py cards.csv --seed 7 --limit 5 --retry-incorrect
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
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- support tagged decks and filtered study sessions
- store study history to track weak cards over time
- add import/export support for JSON or Anki-style formats
