# Python Refresh + Self Tests

## Topics refreshed
- `argparse` subcommands and validation
- `dataclasses` for domain models
- `sqlite3` with placeholders and row factories
- file/path handling with `pathlib`
- hashing with `hashlib`
- small local servers with `http.server`
- testing with `unittest`

## Mini self-tests
### 1. argparse subcommands
Task: create `greet NAME --caps`.
Answer sketch:
- positional `name`
- optional `--caps`
- conditional output transform

### 2. sqlite3 safety
Task: insert a row safely.
Answer sketch:
- use `cursor.execute('INSERT INTO t(name) VALUES (?)', (name,))`
- never interpolate strings directly into SQL

### 3. dataclass mutable defaults
Task: store tags list safely.
Answer sketch:
- `field(default_factory=list)` instead of `tags=[]`

### 4. unittest AAA pattern
Task: verify function rejects negative input.
Answer sketch:
- arrange invalid input
- act inside `assertRaises`
- assert exception message when useful

### 5. http.server JSON response
Task: return JSON from `/health`.
Answer sketch:
- set status 200
- `Content-Type: application/json`
- `json.dumps({"ok": True})`

## Practical rules used in these projects
- prefer standard library unless extra dependency is clearly worth it
- keep I/O edges thin and business logic testable
- make storage locations explicit and overridable in tests
