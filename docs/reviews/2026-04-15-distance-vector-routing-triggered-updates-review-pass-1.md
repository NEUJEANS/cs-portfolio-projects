# Review Pass 1 — Distance Vector Routing Triggered Updates

## Focus
API compatibility and test coverage after adding `update_strategy`.

## Issues found
1. `export_diagram(...)` became backwards-incompatible because the new keyword argument had no default.

## Fixes applied
- Restored compatibility by defaulting `update_strategy` to `periodic` in `export_diagram`.
- Re-ran the project unit tests after the fix.
