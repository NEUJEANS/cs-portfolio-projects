# 2026-04-14 Task Tracker CLI Tags/Search Refresh

## Quick refresh
- `argparse` with `action="append"` is the cleanest way to accept repeatable CLI flags.
- Dataclasses can safely carry `list[str]` metadata by using `field(default_factory=list)`.
- Normalizing inputs at the service boundary is better than sprinkling cleanup logic across CLI rendering code.

## Self-test
1. How do we avoid a shared mutable default for tags? Use `field(default_factory=list)`.
2. Where should comma-splitting and tag normalization happen? In one helper close to the domain layer.
3. Why let search scan both descriptions and tags? It matches how users naturally look for tasks in a CLI demo.
