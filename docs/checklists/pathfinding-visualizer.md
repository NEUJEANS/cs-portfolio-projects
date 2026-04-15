# Pathfinding Visualizer Checklist

## 2026-04-14 hardening slice
- [x] identify pathfinding-visualizer as the weakest current project
- [x] do brief search/design notes for a stronger vertical slice
- [x] do short algorithm/tool refresh and self-test
- [x] add robust map parsing and validation
- [x] support BFS and A* from the CLI
- [x] add weighted traversable tiles and path metrics
- [x] handle no-path cases cleanly
- [x] run tests
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-14 weighted-search baseline slice
- [x] re-check repo sync state before editing
- [x] capture brief search/design notes for Dijkstra vs A*
- [x] do a short weighted-path refresh and self-test
- [x] extend the CLI with Dijkstra as a weighted optimal baseline
- [x] update README usage/examples to explain BFS vs Dijkstra vs A*
- [x] run focused tests for pathfinding-visualizer
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-15 comparison-mode slice
- [x] re-check repo sync state before editing
- [x] do brief research on why admissible A* usually expands fewer nodes than Dijkstra
- [x] do a short pathfinding refresher and self-test for compare-mode metrics
- [x] add compare mode that runs BFS, Dijkstra, and A* on one map
- [x] surface cost-optimal-match summaries so weighted-map tradeoffs are obvious
- [x] update README examples for compare mode
- [x] run focused tests for pathfinding-visualizer
- [x] complete review pass 1 and fix issues
- [x] complete review pass 2 and fix issues
- [x] complete review pass 3 and fix issues
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
