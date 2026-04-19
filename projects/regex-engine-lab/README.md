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

### Benchmark against Python's `re`
```bash
python3 regex_engine_lab.py benchmark '^ID-\d\d\d\d-\w+$' 'ID-2026-demo_user' \
  --iterations 5000 --warmup 200 --label id-fullmatch

python3 regex_engine_lab.py benchmark --sample-suite \
  --iterations 3000 --warmup 200 \
  --json-out ../../docs/artifacts/regex-engine-lab/benchmark-sample-suite.json \
  --markdown-out ../../docs/artifacts/regex-engine-lab/benchmark-sample-suite.md

python3 regex_engine_lab.py benchmark \
  --suite-file ../../docs/examples/regex-engine-benchmark-suite.json \
  --iterations 2500 --warmup 200 \
  --json-out ../../docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.json \
  --markdown-out ../../docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.md
```

`benchmark` reuses one compiled lab engine and one compiled Python `re.Pattern`, measures both with `time.perf_counter()`, and reports whether the two engines agree on the chosen safe regular-language cases. The built-in suite stays intentionally ASCII-only so shorthand-class parity is about engine behavior, not Unicode-policy differences. `--suite-file` accepts a JSON object with a `suite_label` plus a `cases` list of `{label, pattern, text, mode?}` entries, and those case labels must stay unique so reports remain unambiguous. That makes reproducible workload bundles easy to ship in the repo without editing Python code.

## Sample artifacts
- `docs/artifacts/regex-engine-lab/trace-id-fullmatch.json` - fullmatch trace for a shorthand-heavy ID pattern
- `docs/artifacts/regex-engine-lab/trace-dogs-search.json` - search trace showing how the engine advances start offsets before landing on `dogs`
- `docs/artifacts/regex-engine-lab/benchmark-sample-suite.json` - JSON benchmark comparison report for the built-in safe sample suite
- `docs/artifacts/regex-engine-lab/benchmark-sample-suite.md` - reviewer-friendly Markdown summary of the same benchmark suite
- `docs/examples/regex-engine-benchmark-suite.json` - repo-committed JSON workload definition showing how to benchmark multiple named cases without editing code
- `docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.json` - committed report generated from the JSON-defined workload bundle
- `docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.md` - Markdown summary of the JSON-defined workload bundle for quick portfolio review

## Testing
```bash
python3 -m unittest discover -s projects/regex-engine-lab -p 'test_*.py' -v
```

## Interview talking points
- how recursive-descent parsing models regex operator precedence
- how patchable NFA fragments make Thompson construction compact
- why epsilon closure matters for zero-width transitions and assertions
- how trace output turns a black-box matcher into a teachable state-machine walkthrough
- how the new benchmark flow checks semantic agreement with Python's `re` while also giving a grounded performance story for a teaching-oriented engine
- which modern regex features fall outside regular languages and were intentionally excluded here

## Future improvements
- render trace output into a small HTML timeline or SVG teaching card
- compile to DFA for faster repeated matching on the same pattern
- add suite-level tags or filters so one JSON workload file can drive small interview demos and larger benchmark batches
- add optional Unicode-aware shorthand classes as a follow-on contrast with the current ASCII teaching mode
