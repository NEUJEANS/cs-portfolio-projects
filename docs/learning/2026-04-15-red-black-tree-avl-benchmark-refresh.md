# 2026-04-15 red-black vs AVL benchmark refresh

## Quick refresh
- AVL trees keep a stricter height bound than red-black trees, so they often end up a little shorter after the same insert workload.
- Red-black trees usually spend fewer rotations during updates because they allow looser balance and can repair some cases with recoloring alone.
- For a teaching benchmark, deterministic input orders matter more than wall-clock timings because the structural trade-off is the point: height versus repair work.
- Rotation counts are a useful proxy for balancing work when the code already exposes trace hooks.

## Self-test
1. Why compare ascending, descending, and shuffled inputs instead of only random input?
   - They surface worst-looking insertion orders and show whether both trees stay balanced under adversarial and typical cases.
2. Why is deterministic benchmarking more helpful than microsecond timing here?
   - Heights and rotation counts stay stable across runs and are easier to discuss in interviews and README examples.
3. Why might AVL rotate more often than red-black on the same insert sequence?
   - AVL enforces a tighter balance condition, so it performs more repair work to keep height differences within one.
