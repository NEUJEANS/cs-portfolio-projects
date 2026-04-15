# Research — mini-mapreduce importable module plugins

## Goal
Let the portfolio runner load plugin jobs from reusable Python packages/modules, not only ad-hoc files.

## Notes
- `importlib.import_module("pkg.module")` respects normal Python import rules, so it works cleanly with installed packages or temporary `PYTHONPATH` entries.
- File-path loading still fits one-off local experiments; module loading is better when you want a reusable plugin library or separate benchmark package.
- The runner should preserve a stable `plugin` field in JSON output by recording the resolved module `__file__` when available.
- Error handling should stay user-friendly: if neither a real path nor an importable module exists, return one clear validation error.

## Portfolio angle
This makes the lab feel closer to a real data platform: teams can ship job libraries as versioned modules instead of copying one-off scripts around.
