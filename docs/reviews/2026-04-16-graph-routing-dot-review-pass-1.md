# Review pass 1 — graph-routing DOT slice

## Focus
Code-path review of the new DOT export helper and identifier/label handling.

## Issues found
1. Identifier sanitizing only replaced punctuation; it did not guard against empty identifiers or names starting with digits, which can produce awkward or invalid DOT IDs.

## Fixes applied
- hardened `_sanitize_identifier()` so empty values become `_` and digit-leading values gain a safe underscore prefix
- kept user-facing labels separate from internal IDs via `_dot_quote()` so DOT text stays deterministic and readable
