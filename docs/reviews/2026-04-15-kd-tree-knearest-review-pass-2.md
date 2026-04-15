# Review Pass 2 — KD-Tree k-Nearest Slice

## Focus
- heap ordering edge cases in top-k maintenance

## Issue found
- duplicate points with identical coordinates/labels could force heap tuple comparison down to raw `Point` instances, which is unsafe and can raise comparison errors

## Fix applied
- added a monotonic sequence number to heap entries so all heap comparisons remain well-defined
- added a duplicate-point regression test covering this case
