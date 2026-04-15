# Review Pass 2 - Distributed Snapshot Mermaid Export

## Focus
- copy-paste CLI usability
- README command correctness

## Findings
1. README examples used unquoted values like `A->B=0`; in a real shell, `>` is treated as redirection, so the example breaks when pasted.

## Fixes applied
- quoted marker-delay examples in README usage blocks
- verified the Mermaid output path manually with quoted arguments
