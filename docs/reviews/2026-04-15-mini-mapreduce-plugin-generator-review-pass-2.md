# Review pass 2 - failure modes

- Inspected invalid plugin-generator behavior and confirmed a bad hook could otherwise silently underfill benchmark input.
- Fix kept: benchmark generation now raises if the plugin does not return exactly `records` lines or returns non-string rows.
- Confirmed the new repo/project tests cover both the happy path and invalid-shape failures.
