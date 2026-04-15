# Union-Find vs BFS recomputation summary

> Reproducible connectivity-comparison artifact for `union-find-network-lab`.

## Headline
- Processed **10000** random edges across **1500** nodes with checkpoints every **1250** edges.
- Union-find finished in **23.421 ms** (**426971.354 edges/s**) versus **8440.719 ms** (**1184.733 edges/s**) for repeated BFS recomputation.
- Measured speedup: **360.395x**.
- Result parity: same component count = **True**, same largest component = **True**.

## Why it matters
Union-find is a strong fit for **incremental connectivity** workloads because each new edge updates component state directly, while the baseline must walk the graph again after every insertion. This artifact shows the algorithmic advantage with the exact same random edge stream.

## Result snapshot
- Union-find components: **1**
- Union-find largest component: **1500**
- Union-find cycle edges: **8501**
- Baseline components: **1**
- Baseline largest component: **1500**
- Baseline cycle edges: **8501**
- Sample input edges: `n663->n308`, `n808->n1333`, `n98->n148`

## Portfolio-ready takeaway
For streaming network links, service-dependency updates, or social-graph edge ingestion, union-find preserves the same final connectivity answer while avoiding the repeated full-graph scans that make naive recomputation collapse at scale.
