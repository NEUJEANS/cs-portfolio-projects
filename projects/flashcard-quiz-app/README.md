# flashcard-quiz-app

## Overview
Load CSV flashcards and run a study quiz session.

## Stack
- Python
- no extra runtime dependency required for the default path

## Features
- focused scope suitable for a CS student portfolio
- runnable locally from the command line
- core behavior covered by tests
- clear v2 expansion path

## Usage
```bash
python3 flashcards.py cards.csv
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Future Improvements
- richer validation and edge-case handling
- packaging / release automation
- more integration or end-to-end tests
