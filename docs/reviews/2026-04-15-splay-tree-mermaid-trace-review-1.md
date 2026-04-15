# Review 1 — splay-tree Mermaid trace export

- Checked `to_mermaid()` output shape against existing tree construction behavior.
- Issue found: my first assertion assumed `18 -> 7` was a direct edge, but the actual splayed tree path is `18 -> 15 -> 12 -> 7`.
- Fix applied: updated the unit test to assert a real deterministic edge (`12 --> 7`) instead of the incorrect shortcut.
