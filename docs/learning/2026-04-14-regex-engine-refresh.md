# Regex engine refresh and self-test

## Refresh
- recursive-descent parsing fits regex precedence well: alternation < concatenation < postfix quantifiers < atoms
- Thompson compilation builds fragments with patchable outgoing edges
- NFA simulation keeps a current state set and expands epsilon transitions eagerly
- anchors can be modeled as zero-width states checked against the current input position

## Self-test
1. Why prefer Thompson NFA for this project?
   - predictable performance for regular-language features and a clean state-machine story
2. Where does concatenation happen in parsing?
   - between adjacent atoms/quantified expressions until `|` or `)`
3. How do `*` and `+` differ in the compiled graph?
   - both add a loop; `*` allows skipping immediately, `+` requires one pass before the loop
4. What is the core runtime trick?
   - repeatedly expand epsilon-style transitions so the active set always contains concrete matching states plus any immediately reachable assertions
