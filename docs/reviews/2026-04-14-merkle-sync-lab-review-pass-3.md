# Review Pass 3 - merkle-sync-lab

## Focus
Test ergonomics and docs clarity.

## Findings
- Tests cannot import through a hyphenated project directory as a normal package.
- The manifest should ignore cache metadata like `__pycache__` so demo output stays meaningful.
- README should emphasize the Git/content-addressed-storage connection for portfolio storytelling.

## Fixes applied
- switched tests to import the module through `importlib.util`
- ignored common cache directories during traversal and added coverage for that behavior
- clarified README positioning, usage, and future extension ideas
