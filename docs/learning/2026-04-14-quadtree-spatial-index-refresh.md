# Quadtree Refresh + Self-Test

## Refresh notes
- A quadtree recursively partitions 2D space into four quadrants.
- For a point-region quadtree, each node owns a rectangle and stores up to `capacity` points before subdivision.
- Range query uses rectangle-intersection pruning.
- Nearest-neighbor search improves by exploring the child whose bounding box is closest first, then pruning boxes that cannot beat the best current distance.

## Self-test
1. Why is rectangle intersection pruning important?
   - It avoids descending into quadrants that cannot contain matching points.
2. After subdivision, what should happen to existing leaf points?
   - Reinsert or redistribute them into children so future queries stay local.
3. How can nearest-neighbor search prune work?
   - If the minimum possible distance from the query point to a quadrant's bounding box is already worse than the best known point, skip that quadrant.
4. What boundary rule keeps insertion deterministic?
   - Use inclusive lower bounds and inclusive upper bounds at the node level, while checking child rectangles in fixed order so a point on a split line routes consistently.
