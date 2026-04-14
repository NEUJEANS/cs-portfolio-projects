# Count-Min Sketch Refresh and Self-Test

## Quick refresh
- Count-Min Sketch stores counts in a `depth x width` table.
- Width is typically `ceil(e / epsilon)` and depth is `ceil(ln(1 / delta))`.
- Each incoming item updates one bucket per row.
- Querying uses the minimum bucket value across rows.
- Estimates never underestimate, but collisions can overestimate.
- Merge works by element-wise addition when sketch parameters match.

## Self-test
1. Why take the minimum across rows instead of the average?
   - To preserve the one-sided error guarantee and reduce collision noise.
2. What happens if two sketches use different seeds or widths?
   - Their buckets no longer correspond, so merging them would be invalid.
3. Why is CMS useful even if we keep `observed` items here?
   - The sketch still demonstrates compact approximate counting, while `observed` makes the lab easier to inspect and review.
