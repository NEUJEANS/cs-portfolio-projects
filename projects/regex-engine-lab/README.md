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
- character classes like `[abc]`, `[a-z]`, and `[^0-9]`
- anchors `^` and `$`

## Project structure
- `regex_engine_lab.py` - parser, compiler, matcher, and CLI
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

### Inspect the AST and compiled NFA
```bash
python3 regex_engine_lab.py explain 'ab|c*'
```

## Testing
```bash
python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py' -v
```

## Interview talking points
- how recursive-descent parsing models regex operator precedence
- how patchable NFA fragments make Thompson construction compact
- why epsilon closure matters for zero-width transitions and assertions
- which modern regex features fall outside regular languages and were intentionally excluded here

## Future improvements
- add escape classes such as `\d`, `\w`, and `\s`
- expose step-by-step state tracing for debugging and teaching
- compile to DFA for faster repeated matching on the same pattern
- add a tiny benchmark comparing this engine with Python's `re` on safe regular-language patterns
