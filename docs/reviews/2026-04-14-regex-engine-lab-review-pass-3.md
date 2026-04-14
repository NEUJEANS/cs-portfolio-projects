# Regex engine lab review pass 3

## Focus
Regression and portfolio integration audit.

## Checks run
- added a direct fullmatch regression for `ab|cd`
- reran the project test suite
- verified repo-level README includes the new project entry

## Findings
- no new runtime bugs found after the pass-1 fixes
- portfolio index needed the new project listed at the repo root

## Fixes applied
- added `test_alternation_fullmatch`
- updated root `README.md` to include `regex-engine-lab`

## Result
The project is now covered by a direct alternation regression test and shows up in the top-level portfolio list.
