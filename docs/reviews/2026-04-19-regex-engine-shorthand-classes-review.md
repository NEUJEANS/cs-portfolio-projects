# Regex engine shorthand escape classes review log — 2026-04-19

## Pass 1 — explain/state output compatibility audit
- looked for places where the new term-based character-class model could make the JSON explain output less useful or silently break existing artifact consumers
- issue found: `states_to_dict(...)` had moved to `terms`-only output, which dropped the simple `chars` field older positive-class consumers may expect
- fix applied: restored `chars` in state JSON when the state still represents a single positive class term and added regression coverage in `test_explain_contains_ast_and_states`

## Pass 2 — syntax/docs clarity audit
- re-read the README examples against the parser rules for mixed bracket classes and class ranges
- issue found: the docs introduced shorthand classes inside brackets but did not explain that range endpoints still have to be literal, which makes `[A-\d]` intentionally invalid
- fix applied: documented the valid/invalid contrast directly in the supported-syntax section and kept the parser/test guard for ambiguous shorthand ranges

## Pass 3 — smoke + regression audit
- reran compile, unit, CLI, and `git diff --check` validation after the review fixes
- checked the new CLI examples against real output to ensure the docs and implementation still matched
- result: no additional issues found after the pass-1 and pass-2 fixes
