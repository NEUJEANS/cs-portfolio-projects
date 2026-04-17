# branch-predictor-lab review pass 5

## Focus
CLI/help-text consistency audit for the new synthetic generator.

## Issue found
The `generate` subcommand help text described the random workload as `random-bias`, while the actual workload name and README usage use `random-biased`.

## Fix applied
- updated the `generate` subcommand help text to use the exact workload name `random-biased`

## Result
CLI discovery, README examples, and test coverage now use the same workload vocabulary.
