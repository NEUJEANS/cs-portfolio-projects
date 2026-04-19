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
  --markdown-out ../../docs/artifacts/regex-engine-lab/benchmark-sample-suite.md \
  --html-out ../../docs/artifacts/regex-engine-lab/benchmark-sample-suite.html

python3 regex_engine_lab.py benchmark \
  --suite-file ../../docs/examples/regex-engine-benchmark-suite.json \
  --iterations 2500 --warmup 200 \
  --json-out ../../docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.json \
  --markdown-out ../../docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.md \
  --html-out ../../docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.html

python3 regex_engine_lab.py benchmark \
  --suite-file ../../docs/examples/regex-engine-benchmark-suite.json \
  --label interview-demo \
  --include-tag interview-demo \
  --iterations 2500 --warmup 200 \
  --json-out ../../docs/artifacts/regex-engine-lab/benchmark-interview-demo.json \
  --markdown-out ../../docs/artifacts/regex-engine-lab/benchmark-interview-demo.md \
  --html-out ../../docs/artifacts/regex-engine-lab/benchmark-interview-demo.html
```

`benchmark` reuses one compiled lab engine and one compiled Python `re.Pattern`, measures both with `time.perf_counter()`, and reports whether the two engines agree on the chosen safe regular-language cases. The built-in suite stays intentionally ASCII-only so shorthand-class parity is about engine behavior, not Unicode-policy differences. `--suite-file` accepts a JSON object with a `suite_label` plus a `cases` list of `{label, pattern, text, mode?, tags?}` entries, and those case labels must stay unique so reports remain unambiguous. Optional lowercase tags let one workload bundle drive both tiny interview-demo runs and broader portfolio batches via repeatable `--include-tag` / `--exclude-tag` filters. `--html-out` turns the same benchmark payload into a browser-friendly dashboard with summary cards, a case table, and per-case metric notes for recruiter-friendly screenshots or GitHub Pages browsing.

### Build a combined showcase page
```bash
python3 regex_engine_lab.py showcase-demo \
  --html-out ../../docs/artifacts/regex-engine-lab/showcase.html \
  --artifact-dir ../../docs/artifacts/regex-engine-lab
```

`showcase-demo` links the committed trace JSON artifacts to the benchmark dashboards that exercise the same patterns, so a reviewer can move from step-by-step NFA behavior into the broader performance story without digging through the repo tree.

## Sample artifacts
- `docs/artifacts/regex-engine-lab/trace-id-fullmatch.json` - fullmatch trace for a shorthand-heavy ID pattern
- `docs/artifacts/regex-engine-lab/trace-dogs-search.json` - search trace showing how the engine advances start offsets before landing on `dogs`
- `docs/artifacts/regex-engine-lab/benchmark-sample-suite.json` - JSON benchmark comparison report for the built-in safe sample suite
- `docs/artifacts/regex-engine-lab/benchmark-sample-suite.md` - reviewer-friendly Markdown summary of the same benchmark suite
- `docs/artifacts/regex-engine-lab/benchmark-sample-suite.html` - browser-friendly dashboard for the sample benchmark suite
- `docs/examples/regex-engine-benchmark-suite.json` - repo-committed JSON workload definition showing how to benchmark multiple named cases and tag them for different demo sizes
- `docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.json` - committed report generated from the full JSON-defined workload bundle
- `docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.md` - Markdown summary of the full JSON-defined workload bundle for quick portfolio review
- `docs/artifacts/regex-engine-lab/benchmark-portfolio-workload.html` - portfolio-ready dashboard view of the full tagged workload bundle
- `docs/artifacts/regex-engine-lab/benchmark-interview-demo.json` - filtered benchmark report generated from the same suite file with `--include-tag interview-demo`
- `docs/artifacts/regex-engine-lab/benchmark-interview-demo.md` - reviewer-friendly Markdown summary of the smaller interview-demo subset
- `docs/artifacts/regex-engine-lab/benchmark-interview-demo.html` - smaller dashboard view suited to recruiter or interview walkthroughs
- `docs/artifacts/regex-engine-lab/showcase.html` - combined landing page that cross-links the trace walkthroughs and benchmark dashboards in one browser-friendly hub

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
- how the HTML dashboard turns JSON/Markdown benchmark payloads into recruiter-friendly static artifacts without introducing a frontend build step
- how the combined showcase page ties low-level trace evidence to the higher-level benchmark story so the portfolio narrative flows in one click path
- which modern regex features fall outside regular languages and were intentionally excluded here

## Future improvements
- render trace output into a small HTML timeline or SVG teaching card
- compile to DFA for faster repeated matching on the same pattern
- add optional Unicode-aware shorthand classes as a follow-on contrast with the current ASCII teaching mode
- add a tiny AST/NFA explainer card that sits beside the trace and benchmark showcase page
