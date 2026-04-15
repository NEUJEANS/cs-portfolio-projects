# Tarjan SCC topological levels review — pass 1

- Checked whether level propagation was valid only on the condensation DAG, not the original cyclic graph.
- Verified the implementation computes SCCs first, then derives levels from cross-component edges only.
- Issue found: queue processing used `list.pop(0)`, which is noisier and less efficient than a deque.
- Fix applied: switched to `collections.deque` with `popleft()`.
