# Bloom filter binary export refresh — 2026-04-14

## Quick refresh
- Bloom filters are naturally binary-friendly because the core state is either a bitset or an array of counters.
- A good pragmatic format is: magic bytes + version + variant + metadata length + payload length + metadata JSON + raw payload.
- Binary does not have to mean opaque; compact metadata keeps inspection and forward migration manageable.
- Counting Bloom filters pay a substantial space premium for delete support.

## Self-check
- Can I reload a binary artifact through the normal `check` and `stats` commands? Yes.
- Does removal preserve the original artifact type? Yes; `.bf` counting artifacts are rewritten in binary after deletion.
- Do tests cover both standard and counting round trips plus CLI flows? Yes.
