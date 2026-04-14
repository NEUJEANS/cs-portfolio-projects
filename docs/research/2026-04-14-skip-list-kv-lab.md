# Research - Skip List KV Lab

## Brief notes
- Skip lists are probabilistic ordered structures introduced by William Pugh that provide expected `O(log n)` search, insert, and delete behavior.
- Their practical appeal is simpler implementation than balanced search trees while still supporting ordered traversal and range queries.
- Typical implementations use repeated coin flips to assign a tower height per node; lower levels contain every element and higher levels act as express lanes.
- Deterministic seeds are useful in teaching/demo code so tests can exercise stable level distributions.

## Source used
- Wikipedia summary on skip lists (fetched 2026-04-14) for historical context, layered search intuition, and complexity reminders.

## Scope for this slice
- Build an interview-friendly in-memory ordered KV store.
- Expose CRUD, range query, and structural stats through a CLI.
- Keep persistence simple with a JSON fixture rather than overreaching into a disk-backed engine in one pass.
