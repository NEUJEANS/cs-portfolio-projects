# Review Pass 1 — file-integrity-monitor

- Focus: CLI behavior and automation semantics.
- Found: `--fail-on-changes` returned the right status for changed files, but missing `--baseline` still exited like a generic failure rather than a clear usage error.
- Fix made: route missing-baseline handling through an explicit usage-path that prints to stderr and exits with code `2`.
- Result: CLI semantics now better match standard automation expectations.
