# Review Pass 2 — deadlock-detector-lab Banker's slice

## Checks
- reviewed README and sample artifacts against the CLI contract
- manually ran `analyze-banker` and `request-banker`

## Issue found
- the project did not yet ship sample Banker's JSON files, which made the new commands harder to demo and weakened the README examples

## Fix applied
- added `sample_banker_state.json` and `sample_banker_request.json`
- expanded README usage and JSON format sections to cover both new commands
