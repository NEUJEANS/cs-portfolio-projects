# Review pass 1 - red-black benchmark slice

## Focus
Code-path review of the new benchmark helper and module loading.

## Findings
1. `_benchmark_sequence()` reloaded the AVL module for each case, which was unnecessary churn for a deterministic benchmark command.

## Fixes applied
- added `_AVL_MODULE` caching so the AVL implementation is loaded once and reused across benchmark cases

## Result
- benchmark behavior stays the same but avoids repeated dynamic imports during a single run
