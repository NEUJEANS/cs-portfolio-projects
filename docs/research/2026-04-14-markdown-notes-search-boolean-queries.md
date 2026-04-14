# Markdown Notes Search: Boolean Query Slice Research

Date: 2026-04-14

## Goal
Add a portfolio-worthy search upgrade that moves the project beyond plain substring matching.

## Brief notes
- Boolean search is a classic information retrieval pattern: `AND` maps to set intersection, `OR` to union, and `NOT` to exclusion.
- Standard precedence is `NOT` > `AND` > `OR`, with parentheses used to override grouping.
- Quoted phrases are a practical UX upgrade for note-search tools because users often search for exact multi-word concepts.
- For this project's current size, an in-memory parser/evaluator is enough; a persistent inverted index can remain a future slice.

## Slice decision
Implement:
- quoted phrase search like `"systems design"`
- boolean operators `AND`, `OR`, `NOT`
- parenthesized grouping
- implicit `AND` between adjacent terms/phrases for ergonomic CLI usage

## Sources consulted
- Web search summary on boolean query parsing and operator precedence
- boolean_parser docs: https://boolean-parser.readthedocs.io/en/latest/intro.html
