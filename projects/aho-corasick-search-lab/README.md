# Aho-Corasick Search Lab

A portfolio-friendly algorithms project that implements the Aho-Corasick multi-pattern string matching algorithm with a practical CLI.

## Features
- builds a trie with failure links for efficient multi-pattern search
- reports exact line/column offsets for every match
- supports inline text or file input
- supports case-insensitive search and JSON output for tooling
- keeps pattern counts and detailed match listings in one pass through the input text
- supports chunked file scanning so large inputs can be streamed without losing matches that cross chunk boundaries
- supports sampled context windows in chunked mode so streamed searches can still show small excerpts without loading the entire file
- exports portfolio-friendly Markdown and HTML match reports for screenshot/demo use
- supports grouped incident/category presets so one scan can summarize several related keyword packs at once

## Why it is interesting
- demonstrates trie construction, BFS failure-link building, and suffix-output propagation
- shows how textbook string matching can become a usable developer tool
- adds a practical streaming mode that carries automaton state across chunk boundaries instead of re-reading overlap windows by hand
- shows how to layer small UX features like context windows onto a streaming pipeline with bounded memory
- demonstrates how plain keyword sets can become reusable incident-response presets with grouped summaries and richer report metadata
- gives interview-ready complexity discussion: `O(total_pattern_length + text_length + matches)` after preprocessing

## Usage
```bash
python3 projects/aho-corasick-search-lab/aho_corasick_search.py he she hers --text "ushers"
python3 projects/aho-corasick-search-lab/aho_corasick_search.py --pattern-file projects/aho-corasick-search-lab/sample_patterns.txt --input projects/aho-corasick-search-lab/sample_text.txt --json
python3 projects/aho-corasick-search-lab/aho_corasick_search.py alpha beta --text "Alpha beta" --ignore-case --context 4
python3 projects/aho-corasick-search-lab/aho_corasick_search.py warning critical --input logs/app.log --chunk-size 4096 --context 12
python3 projects/aho-corasick-search-lab/aho_corasick_search.py warning critical --input logs/app.log --chunk-size 4096 --context 12 --json
python3 projects/aho-corasick-search-lab/aho_corasick_search.py --pattern-file projects/aho-corasick-search-lab/sample_patterns.txt --input projects/aho-corasick-search-lab/sample_text.txt --chunk-size 8 --context 6 --json --report-title "Streaming incident keyword report" --report-markdown-out docs/artifacts/aho-corasick-search-lab/streaming-sample-report.md --report-html-out docs/artifacts/aho-corasick-search-lab/streaming-sample-report.html > docs/artifacts/aho-corasick-search-lab/streaming-sample-report.json
python3 projects/aho-corasick-search-lab/aho_corasick_search.py --preset-file projects/aho-corasick-search-lab/sample_incident_presets.json --preset incident-triage --input projects/aho-corasick-search-lab/sample_incident_log.txt --chunk-size 18 --context 10 --json --report-markdown-out docs/artifacts/aho-corasick-search-lab/incident-triage-report.md --report-html-out docs/artifacts/aho-corasick-search-lab/incident-triage-report.html > docs/artifacts/aho-corasick-search-lab/incident-triage-report.json
```

## Example output
```text
patterns: 2
matches: 2
input mode: stream (4 chunks @ 5 chars, boundary overlap 7)
context chars: 2 (sampled around matches)
counts:
  - warning: 1
  - critical: 1
matches detail:
  - warning @ line 2, col 1 [6:13] | context='r\n⟦warning⟧\nc'
  - critical @ line 3, col 1 [14:22] | context='g\n⟦critical⟧\n'
```

## Streaming notes
- `--chunk-size` only applies to `--input` mode
- chunked mode preserves cross-boundary matches by carrying the automaton state across chunks
- `--context` now works in both memory and chunked modes
- in chunked mode, context is emitted as a sampled window around each match instead of requiring the full file contents in memory
- `--report-markdown-out` and `--report-html-out` write screenshot-friendly artifacts while stdout can still stay machine-readable with `--json`
- JSON output includes `input.mode`, `input.chunk_count`, `input.chunk_size`, `input.boundary_overlap`, and optional per-match `context` payloads when `--context` is requested

## Preset bundles
- `--preset-file` loads grouped keyword packs from JSON so one scan can summarize related incident categories such as severity, customer impact, or security indicators
- `--preset` selects a preset by name when the JSON file contains more than one reusable pack
- preset-backed JSON/report output includes top-level preset metadata, per-group match totals, and per-match group labels
- ad hoc patterns from the CLI or `--pattern-file` can still be combined with preset patterns for one-off investigations

## Committed demo artifacts
- `docs/artifacts/aho-corasick-search-lab/streaming-sample-report.json`
- `docs/artifacts/aho-corasick-search-lab/streaming-sample-report.md`
- `docs/artifacts/aho-corasick-search-lab/streaming-sample-report.html`
- `docs/artifacts/aho-corasick-search-lab/incident-triage-report.json`
- `docs/artifacts/aho-corasick-search-lab/incident-triage-report.md`
- `docs/artifacts/aho-corasick-search-lab/incident-triage-report.html`

## Tests
```bash
python3 projects/aho-corasick-search-lab/test_aho_corasick_search.py
python3 -m unittest tests.test_aho_corasick_search_lab
```

## Future improvements
- support whole-word mode and pattern metadata tags
- expose automaton visualization data for teaching demos
- add preset-hit threshold rules or severity scoring so grouped packs can drive lightweight alert prioritization
