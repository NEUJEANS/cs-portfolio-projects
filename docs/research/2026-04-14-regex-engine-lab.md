# Regex Engine Lab research

## Goal
Add a project that shows compiler/runtime fundamentals through a tiny regular-expression engine instead of another CRUD-style app.

## Why this project
- strong CS signal: parsing, syntax trees, automata, epsilon closure, state machines
- portfolio-friendly: runnable locally with a compact CLI and test suite
- good interview story: trade-offs between backtracking engines and Thompson NFA simulation

## Quick notes from source refresh
- Russ Cox's classic article highlights why Thompson NFA simulation avoids catastrophic backtracking for classic regular-language features.
- A practical implementation path is: parse regex -> compile to epsilon-NFA fragments -> simulate active state sets over the input.
- Keep the supported syntax intentionally scoped so the project stays understandable.

## Planned feature slice
- literals and escapes
- concatenation
- alternation with `|`
- quantifiers `*`, `+`, `?`
- grouping with `(...)`
- wildcard `.`
- character classes like `[abc]`, `[a-z]`, and negated `[^0-9]`
- anchors `^` and `$`
- CLI commands for `search`, `fullmatch`, and `explain`

## Out of scope for this slice
- backreferences
- lookaround
- lazy quantifiers
- full POSIX/PCRE compatibility

## Portfolio angle
This can be framed as a miniature language-runtime project: tokenizer/parser + IR-like NFA + execution engine + developer-facing CLI.
