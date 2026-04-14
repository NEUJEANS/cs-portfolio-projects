# Review pass 3 - docs/usability audit

## Checks
- compared README commands against the current test runner
- re-read checklist and future-slice notes for consistency
- confirmed JSON output shape is documented by example

## Issues found
- README test command still referenced `pytest`, which is not guaranteed in this repo environment

## Fix applied
- updated README to use the working `python3 -m unittest ...` command
