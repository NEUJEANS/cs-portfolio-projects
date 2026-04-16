# Review Pass 2 — file-integrity-monitor

## Focus
CLI ergonomics and documentation consistency.

## Findings
- README still described the project as standard-library-only even though asymmetric support now depends on the system OpenSSL binary.
- The README lacked concrete asymmetric usage and rotation examples.

## Fixes
- Updated the stack section to call out optional OpenSSL usage.
- Added RSA sign/verify and public-key rotation examples.
- Marked the checklist item complete.

## Result
- Docs now match the implemented feature set.
