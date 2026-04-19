from collections import deque


def bfs_layers(graph, start):
    queue = deque([(start, 0)])
    seen = {start}
    order = []
    while queue:
        node, depth = queue.popleft()
        order.append((node, depth))
        for neighbor in graph.get(node, []):
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, depth + 1))
    return order
