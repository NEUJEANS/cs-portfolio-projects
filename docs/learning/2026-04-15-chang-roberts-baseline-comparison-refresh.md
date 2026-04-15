# Chang-Roberts baseline comparison refresh

## Quick refresh
- Le Lann-style ring election is a useful teaching baseline because it forwards identifiers more directly and makes the cost of redundant circulation obvious.
- Chang-Roberts improves practical behavior in a unidirectional ring by replacing weaker ids when a stronger process sees them.
- A good self-test is: if both algorithms run on the same active ring, they must elect the same maximum live id.

## Self-test
1. If the ring is `8 3 12 6` and process `3` starts, who should lead? `12`.
2. What should differ between the algorithms? Message counts and trace shape, not the elected leader.
3. What makes the comparison portfolio-worthy? It turns a textbook claim into runnable evidence.
