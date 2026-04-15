# Splay Tree Lab Research - 2026-04-15

## Goal
Add another portfolio-grade advanced data structure after the existing batches were fully checked off.

## Brief references
- Sleator and Tarjan's original self-adjusting binary search tree paper for the amortized-O(log n) framing.
- Standard lecture notes and references on zig, zig-zig, and zig-zag rotations.
- Typical split/join descriptions for future expansion after a first vertical slice.

## Product direction
Build a compact Python CLI lab that:
- explains self-adjusting tree behavior through runnable access sequences
- persists snapshots so a student can demo hot-key workloads over time
- records rotation and comparison counts to make interview discussion concrete
- leaves room for split/join and benchmark features in later slices
