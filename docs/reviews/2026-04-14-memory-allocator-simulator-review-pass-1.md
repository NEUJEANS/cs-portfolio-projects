# Review Pass 1 — memory-allocator-simulator

## Focus
Core allocator correctness and failure modes.

## Findings
1. Strategy validation originally happened only during allocation, so invalid configuration failed too late.
2. Basic strategy comparison scenarios were covered, but invalid-strategy behavior was not tested.

## Fixes applied
- validate strategy during allocator construction
- add a unit test for invalid strategy configuration

## Result
Constructor now fails fast on bad input and the test suite covers that contract.
