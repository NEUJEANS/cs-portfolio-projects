# Review pass 1 - config precedence audit

## Focus
- parser defaults vs trace-file defaults
- whether CLI flags can still override imported traces

## Issue found
- using parser defaults for `--strategy`, `--alignment`, and `--timeline-width` made it impossible to intentionally override a trace back to the default value (for example, forcing `first-fit` against a trace that stored `best-fit`)

## Fix applied
- changed those CLI arguments to default to `None`
- resolved effective settings in `main()` with explicit precedence: CLI flag -> trace value -> hardcoded fallback

## Result
- replay bundles remain resumable
- explicit CLI overrides now behave correctly even when they match the normal default values
