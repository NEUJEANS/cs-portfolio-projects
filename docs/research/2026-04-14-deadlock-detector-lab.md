# deadlock-detector-lab research

## Why this project
The current portfolio set is already broad, so the next meaningful slice should add another classic operating-systems artifact rather than another CRUD-style app. A deadlock detector is compact, demonstrably algorithmic, and easy to explain in interviews because it connects resource-allocation graphs, wait-for graphs, and cycle detection.

## Design notes
- For single-instance resources, deadlock detection can be modeled as cycle detection in a wait-for graph.
- For multiple resource instances, a practical student-friendly detector can simulate resource availability and repeatedly finish any process whose outstanding request can be satisfied by the current work vector.
- Useful portfolio output should explain *why* a process is blocked, not only whether the state is deadlocked.
- JSON input keeps the project scriptable and easy to test.

## Scope for this slice
- support wait-for graph analysis from explicit edges
- support resource-allocation analysis with `available`, `allocation`, and `request` maps
- emit machine-readable JSON summaries suitable for README examples
- include sample data and tests for safe, deadlocked, and malformed states

## Follow-up ideas
- visualize the wait-for graph with Graphviz output
- add step-by-step traces for classroom demos
- extend to prevention/avoidance examples such as Banker's algorithm
