# flashcard-quiz-app

## Overview
Load CSV flashcards and run a command-line study session with reproducible shuffling, focused deck limits, topic-tag filters, optional retry rounds, and persistent JSON study history.

## Stack
- Python
- standard library only (`argparse`, `csv`, `json`, `pathlib`, `random`, `unittest`)

## Features
- validates CSV structure before starting a session
- reproducible shuffle order via `--seed` for demos and testing
- focused study rounds via `--limit`
- optional tagged decks via a `tags` CSV column
- repeated `--tag` filters for topic-specific sessions
- optional retry loop for missed cards via `--retry-incorrect`
- weakest-tag summary based on missed questions in the current run
- persistent JSON history via `--history-path` to track repeated misses over time
- historical weakest-card summary via `--show-history-summary`
- automated tests for validation, filtering, shuffle behavior, retry flow, and history persistence

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
python3 flashcards.py cards.csv --history-path data/history.json --show-history-summary
```

Example session output:
```text
2+2: 5
Incorrect. Expected: 4
capital of France: Paris
Correct!

Summary: 1 correct / 2 attempts across 2 unique cards
Weakest tags: math
History: 7 correct / 10 attempts across 4 sessions
Historically weakest cards: 2+2 (3 misses), binary tree (2 misses)
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Data format
A history file created with `--history-path` is plain JSON and stores aggregate accuracy information per prompt:

```json
{
  "version": 1,
  "sessions_run": 4,
  "total_attempts": 10,
  "total_correct": 7,
  "cards": {
    "2+2\t4": {
      "prompt": "2+2",
      "answer": "4",
      "tags": ["math"],
      "times_seen": 4,
      "times_correct": 1,
      "times_incorrect": 3,
      "last_result": "incorrect"
    }
  }
}
```

Card history entries are keyed by `prompt + tab + answer` so similarly worded prompts with different answers do not overwrite each other.

## Future Improvements
- add import/export support for JSON or Anki-style formats
- add spaced-repetition scheduling recommendations
- support merging history across multiple decks
