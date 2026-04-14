# github-repo-reporter review pass 3

## Focus
Resumability and test coverage.

## Findings
- Good: new URL builders and argument parsing are covered by tests.
- Issue found: no explicit test checked the help/usage message for org mode.

## Fix applied
- add a failing-case assertion that the usage text documents `--org`
