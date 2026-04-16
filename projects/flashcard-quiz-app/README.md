# flashcard-quiz-app

## Overview
Load flashcards from CSV or normalized JSON decks and run a command-line study session with reproducible shuffling, focused deck limits, topic-tag filters, optional retry rounds, persistent JSON study history, and spaced-repetition recommendations.

## Stack
- Python
- standard library only (`argparse`, `csv`, `json`, `pathlib`, `random`, `unittest`)

## Features
- validates CSV and JSON deck structure before starting a session
- reproducible shuffle order via `--seed` for demos and testing
- focused study rounds via `--limit`
- optional tagged decks via a `tags` column or JSON field
- repeated `--tag` filters for topic-specific sessions
- optional retry loop for missed cards via `--retry-incorrect`
- weakest-tag summary based on missed questions in the current run
- persistent JSON history via `--history-path` to track repeated misses over time
- historical weakest-card summary via `--show-history-summary`
- study recommendations via `--show-recommendations` and `--recommend-limit`
- normalized JSON deck export via `--export-json` with optional `--export-only` conversion mode
- automated tests for validation, filtering, shuffle behavior, retry flow, history persistence, JSON import/export, and recommendation ranking

## Deck formats
### CSV
```csv
prompt,answer,tags
2+2,4,math
capital of France,Paris,geography
binary tree,node,"data-structures,trees"
```

The `tags` column is optional. When present, separate multiple tags with commas.

### JSON
```json
{
  "version": 1,
  "cards": [
    {"prompt": "2+2", "answer": "4", "tags": ["math"]},
    {"prompt": "capital of France", "answer": "Paris", "tags": ["geography", "capitals"]}
  ]
}
```

JSON decks may be either a top-level `cards` object wrapper or a plain list of card objects.

## Usage
```bash
python3 flashcards.py cards.csv --seed 7 --limit 5 --retry-incorrect
python3 flashcards.py cards.csv --tag algorithms --tag graphs --seed 3
python3 flashcards.py cards.json --history-path data/history.json --show-history-summary --show-recommendations
python3 flashcards.py cards.csv --export-json exported/cards.json --export-only
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
Recommendations:
- 2+2: relearn now — fragile memory (3 misses, streak 0)
- binary tree: review soon — needs reinforcement (2/4 correct overall)
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Data format
A history file created with `--history-path` is plain JSON and stores aggregate accuracy information per prompt:

```json
{
  "version": 2,
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
      "last_result": "incorrect",
      "streak": 0,
      "first_seen_at": "2026-04-14T18:00:00Z",
      "last_seen_at": "2026-04-14T20:00:00Z"
    }
  }
}
```

Card history entries are keyed by `prompt + tab + answer` so similarly worded prompts with different answers do not overwrite each other.

## Recommendation model
The recommendation engine is intentionally lightweight and interview-friendly:
- cards with recent misses or very low exposure are marked **relearn now**
- low-accuracy cards are marked **review soon**
- stable cards are marked **review later**
- consistently correct cards with strong streaks are marked **space out**

This keeps the project dependency-free while still demonstrating stateful study-planning logic.

## Future Improvements
- add Anki-style package export/import bridge for sharing with existing spaced-repetition tools
- support merging history across multiple decks
