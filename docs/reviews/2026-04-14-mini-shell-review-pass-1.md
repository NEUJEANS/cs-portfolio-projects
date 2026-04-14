# Mini Shell Review Pass 1

Focus: runtime correctness and resource handling.

## Findings
- Initial pipeline implementation left process file handles open, causing a `ResourceWarning` during tests.

## Fixes made
- closed pipeline stdout/stderr handles in a `finally` block
- reran the mini-shell test suite successfully after the fix
