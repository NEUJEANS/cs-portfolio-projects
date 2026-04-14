# Count-Min Sketch memory refresh

1. Why compare `sketch_core_bytes` separately from the full sketch object?
   - Because the lab stores observed items for demo-heavy-hitter reporting, which is not required by the core probabilistic data structure itself.

2. Why can a Count-Min Sketch still overestimate top items in the benchmark output?
   - Different items can collide in the same counters, so each row count may include noise from other keys.

3. What makes the benchmark still useful even if Python object overhead is imperfect?
   - It gives a realistic local comparison under the same runtime and makes the space trade-off visible to a student reviewer or interviewer.
