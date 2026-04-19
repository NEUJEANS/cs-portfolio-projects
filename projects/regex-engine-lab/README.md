# Regex Engine Lab

A compact regular-expression engine that parses a small regex language, compiles it into a Thompson-style NFA, and simulates matches from a local CLI.

## Why this project is portfolio-worthy
- demonstrates parsing, syntax trees, finite automata, and zero-width assertions in one contained project
- gives a strong interview story around language runtimes and why Thompson NFA avoids catastrophic backtracking for regular-language features
- stays understandable enough for a hiring manager or interviewer to read in one sitting

## Supported syntax
- literals and escaped metacharacters
- concatenation
- alternation with `|`
- quantifiers `*`, `+`, `?`
- grouping with `(...)`
- wildcard `.`
- character classes like `[abc]`, `[a-z]`, `[^0-9]`, and mixed bracket forms such as `[A-F\d]`
- shorthand escape classes `\d`, `\D`, `\w`, `\W`, `\s`, and `\S` using an explicit ASCII teaching subset
- bracket-class ranges still require literal endpoints, so `[A-F\d]` is valid but `[A-\d]` is rejected as ambiguous
- anchors `^` and `$`

## Project structure
- `regex_engine_lab.py` - parser, compiler, matcher, trace helpers, and CLI
- `test_regex_engine_lab.py` - unit and CLI tests

## Usage
Run from this directory.

### Full-match a string
```bash
python3 regex_engine_lab.py fullmatch '^a.+z$' 'abcz'
```

### Search inside a string
```bash
python3 regex_engine_lab.py search '(cat|dog)s?' 'two dogs walked by'
```

`search` returns the leftmost match and prefers the longest match for that start position.

### Use shorthand classes for digits, words, and whitespace
```bash
python3 regex_engine_lab.py fullmatch '^ID-\d\d\d\d-\w+$' 'ID-2026-demo_user'
python3 regex_engine_lab.py search '\d+\s\w+' 'build 2026 portfolio'
```

### Inspect the AST and compiled NFA
```bash
python3 regex_engine_lab.py explain 'ab|c*'
```

### Trace step-by-step NFA execution
```bash
python3 regex_engine_lab.py trace '^ID-\d\d\d\d-\w+$' 'ID-2026-demo_user'
python3 regex_engine_lab.py trace '(cat|dog)s?' 'xxdogs' --mode search
```

`trace` emits JSON showing the active state set before matching, each consumed character, the concrete transitions that matched, and the final accepting closure. Search traces also show each start-offset attempt until the first leftmost match wins.

## Sample artifacts
- `docs/artifacts/regex-engine-lab/trace-id-fullmatch.json` - fullmatch trace for a shorthand-heavy ID pattern
- `docs/artifacts/regex-engine-lab/trace-dogs-search.json` - search trace showing how the engine advances start offsets before landing on `dogs`

## Testing
```bash
python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py' -v
```

## Interview talking points
- how recursive-descent parsing models regex operator precedence
- how patchable NFA fragments make Thompson construction compact
- why epsilon closure matters for zero-width transitions and assertions
- how trace output turns a black-box matcher into a teachable state-machine walkthrough
- which modern regex features fall outside regular languages and were intentionally excluded here

## Future improvements
- render trace output into a small HTML timeline or SVG teaching card
- compile to DFA for faster repeated matching on the same pattern
- add a tiny benchmark comparing this engine with Python's `re` on safe regular-language patterns
- add optional Unicode-aware shorthand classes as a follow-on contrast with the current ASCII teaching mode
