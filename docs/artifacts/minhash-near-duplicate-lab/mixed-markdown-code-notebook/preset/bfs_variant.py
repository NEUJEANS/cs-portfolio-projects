from collections import deque


def breadth_first_layers(adj, source):
    pending = deque([(source, 0)])
    visited = {source}
    trace = []
    while pending:
        vertex, level = pending.popleft()
        trace.append((vertex, level))
        for nxt in adj.get(vertex, []):
            if nxt not in visited:
                visited.add(nxt)
                pending.append((nxt, level + 1))
    return trace
