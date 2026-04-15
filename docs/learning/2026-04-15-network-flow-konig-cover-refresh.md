# 2026-04-15 network-flow König cover refresh

- In bipartite graphs, König's theorem gives `|maximum matching| = |minimum vertex cover|`.
- Construct the minimum vertex cover from a maximum matching by starting at unmatched left vertices and following alternating paths:
  - left -> right across unmatched edges
  - right -> left across matched edges
- If `Z` is the set of reachable vertices, the minimum vertex cover is `(Left - Z) U (Right ∩ Z)`.
- This is a strong portfolio extension because it turns the solver into a richer explainer: matching, unmatched vertices, and the dual witness all come out of one run.
