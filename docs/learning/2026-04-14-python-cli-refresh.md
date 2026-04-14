# Python CLI / JSON Refresh

Date: 2026-04-14

## Refresher
- `argparse.ArgumentParser()` + `add_subparsers(dest=...)` is the clean pattern for command-based CLIs.
- `choices=` is useful for bounded inputs like status and priority.
- JSON persistence should be wrapped behind a storage layer instead of mixing file I/O into command handlers.
- Date validation is easier at the edge: accept `YYYY-MM-DD`, normalize once, store as strings.

## Self-test
1. How should a multi-command CLI be organized?  
   **Answer:** With subparsers and one handler per command.
2. Where should JSON file reads/writes live?  
   **Answer:** In a storage abstraction, not spread across CLI handlers.
3. Why keep portfolio projects stdlib-first when possible?  
   **Answer:** Easier setup, lower friction for reviewers, fewer environment issues.
