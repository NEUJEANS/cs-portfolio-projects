# 2026-04-15 suffix-tree-lab research: generalized suffix tree longest common substring

## Goal
Add a meaningful next slice to `suffix-tree-lab` by supporting longest common substring queries across two texts.

## Brief research summary
- A generalized suffix tree is built by concatenating multiple strings with **distinct sentinel terminators** so suffixes from one source cannot bleed into another source.
- To recover the **longest common substring (LCS)**, annotate each subtree with which source strings appear beneath it; the deepest path whose subtree covers both sources corresponds to the LCS.
- For this portfolio repo, a **naive compressed generalized suffix tree** is acceptable because the project already favors readability and interview discussion value over Ukkonen-level linear-time construction complexity.

## Applied design choice
Keep the existing educational compressed-tree insertion logic and add a small `GeneralizedSuffixTree` variant for two strings. Use safe single-character sentinels from the Unicode private-use range, track subtree source coverage, and expose a CLI command that prints the shared substring plus hit positions in both inputs.

## References
- Baeldung overview of generalized suffix trees and LCS
- Stanford / Gusfield-style lecture notes on suffix trees and common-substring traversal
- Standard sentinel rationale: one unique terminator per source string
