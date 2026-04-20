# Tarjan SCC Lab

A graph-algorithms portfolio project that finds strongly connected components in directed graphs, builds the condensation DAG, and compares Tarjan vs. Kosaraju on the same fixtures.

## What it demonstrates
- Tarjan's linear-time SCC algorithm with DFS discovery indexes and low-link values
- parsing directed graphs from either adjacency-list or edge-list JSON
- condensation DAG generation for reasoning about cycles at the component level
- deterministic JSON/text CLI output suitable for demos, scripting, and interviews
- side-by-side Tarjan vs. Kosaraju comparison with repeatable timing output
- JSON, CSV, Markdown, HTML, and PNG benchmark-report exports for portfolio screenshots or static-site embeds
- a combined showcase landing page that links the explanation, condensation views, and benchmark bundle into one recruiter-friendly story
- focused automated tests for algorithm correctness, input validation, and CLI behavior

## Files
- `tarjan_scc_lab.py` — implementation and CLI
- `sample_graph.json` — demo graph with several SCCs
- `test_tarjan_scc_lab.py` — correctness and CLI tests

## Usage
```bash
cd projects/tarjan-scc-lab
python3 tarjan_scc_lab.py sample_graph.json scc
python3 tarjan_scc_lab.py sample_graph.json condensation
python3 tarjan_scc_lab.py sample_graph.json dot > condensation.dot
python3 tarjan_scc_lab.py sample_graph.json mermaid > condensation.mmd
python3 tarjan_scc_lab.py sample_graph.json compare --repeat 10
mkdir -p ../../docs/artifacts/tarjan-scc-lab
python3 tarjan_scc_lab.py sample_graph.json compare --repeat 10 \
  --json-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.json \
  --csv-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.csv \
  --markdown-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.md \
  --html-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.html \
  --png-output ../../docs/artifacts/tarjan-scc-lab/sample-compare.png
python3 tarjan_scc_lab.py sample_graph.json explain --limit 4
python3 tarjan_scc_lab.py sample_graph.json explain --limit 4 > ../../docs/artifacts/tarjan-scc-lab/sample-explain.txt
python3 tarjan_scc_lab.py sample_graph.json condensation > ../../docs/artifacts/tarjan-scc-lab/sample-condensation.json
python3 tarjan_scc_lab.py sample_graph.json dot > ../../docs/artifacts/tarjan-scc-lab/sample-condensation.dot
python3 tarjan_scc_lab.py sample_graph.json mermaid > ../../docs/artifacts/tarjan-scc-lab/sample-condensation.mmd
python3 tarjan_scc_lab.py sample_graph.json showcase-demo \
  --repeat 5 \
  --limit 4 \
  --markdown-output ../../docs/artifacts/tarjan-scc-lab/sample-showcase.md \
  --html-output ../../docs/artifacts/tarjan-scc-lab/sample-showcase.html \
  --explain-path ../../docs/artifacts/tarjan-scc-lab/sample-explain.txt \
  --condensation-json-path ../../docs/artifacts/tarjan-scc-lab/sample-condensation.json \
  --dot-path ../../docs/artifacts/tarjan-scc-lab/sample-condensation.dot \
  --mermaid-path ../../docs/artifacts/tarjan-scc-lab/sample-condensation.mmd \
  --compare-json-path ../../docs/artifacts/tarjan-scc-lab/sample-compare.json \
  --compare-csv-path ../../docs/artifacts/tarjan-scc-lab/sample-compare.csv \
  --compare-markdown-path ../../docs/artifacts/tarjan-scc-lab/sample-compare.md \
  --compare-html-path ../../docs/artifacts/tarjan-scc-lab/sample-compare.html \
  --compare-png-path ../../docs/artifacts/tarjan-scc-lab/sample-compare.png
../../.venv/bin/python -m pytest -q test_tarjan_scc_lab.py
```

`--png-output` captures a Chrome/Chromium headless screenshot from the generated HTML dashboard, so pair it with `--html-output` and optionally pass `--chrome-binary` when the browser is not on `PATH`.

When `showcase-demo` receives `--compare-json-path`, it reuses that committed benchmark payload for the embedded timing snapshot so the landing page stays numerically aligned with the linked benchmark bundle.

## Input formats
Adjacency list:
```json
{
  "A": ["B"],
  "B": ["C"],
  "C": ["A", "D"],
  "D": []
}
```

Edge list:
```json
{
  "nodes": ["A", "B", "C", "D"],
  "edges": [
    {"from": "A", "to": "B"},
    {"from": "B", "to": "C"},
    {"from": "C", "to": "A"},
    {"from": "C", "to": "D"}
  ]
}
```

## Why this is portfolio-worthy
Strongly connected components come up in dependency analysis, compiler passes, graph databases, package management, and distributed-systems reasoning. This project shows algorithm knowledge, clean interfaces, and the ability to turn theory into a reusable tool.

## Output details
The SCC summary and condensation DAG now annotate each component with a `topology_level`, plus lightweight bottleneck metadata that highlights whether a component behaves like a source, sink, bridge, or isolated SCC. The lab can also export both Graphviz DOT and Mermaid views for portfolio screenshots or markdown-native demos:
- level `0` means a source SCC in the condensation DAG
- higher levels indicate longer downstream dependency distance from any source SCC
- `incoming_component_count` / `outgoing_component_count` summarize how many other SCCs feed into or depend on a component
- `bottleneck_role` classifies each SCC as `source`, `sink`, `bridge`, or `isolated`
- these annotations make it easier to explain build pipelines, dependency cycles, and chokepoints in interviews

Example condensation output excerpt:
```json
{
  "components": [
    {
      "id": "C0",
      "nodes": ["A", "B", "C"],
      "size": 3,
      "topology_level": 0,
      "incoming_component_count": 0,
      "outgoing_component_count": 1,
      "bottleneck_role": "source"
    },
    {
      "id": "C1",
      "nodes": ["D", "E"],
      "size": 2,
      "topology_level": 1,
      "incoming_component_count": 1,
      "outgoing_component_count": 1,
      "bottleneck_role": "bridge"
    }
  ],
  "edges": [{"from": "C0", "to": "C1"}],
  "edge_count": 1,
  "level_count": 2
}
```

Graphviz export example:
```dot
digraph condensation {
  rankdir=LR;
  node [shape=box, style="rounded,filled", fillcolor="#EAF2FF", color="#4C78A8"];
  C0 [label="C0\nlevel=0 | size=3\nA, B, C"];
  C1 [label="C1\nlevel=1 | size=2\nD, E"];
  C0 -> C1;
}
```


Mermaid export example:
```mermaid
flowchart LR
  subgraph level_0["topology level 0"]
    direction TB
    C0["C0<br/>level=0 | size=3<br/>A, B, C"]
  end
  subgraph level_1["topology level 1"]
    direction TB
    C1["C1<br/>level=1 | size=2<br/>D, E"]
  end
  C0 --> C1
```

This makes it easy to paste the condensation view directly into GitHub-flavored markdown that supports Mermaid.

The JSON `scc`, `condensation`, and text `explain` outputs also expose bottleneck summaries. That gives you quick interview talking points such as "this SCC is a bridge between two cycles" or "this singleton sink is where all paths converge" without manually inspecting the DAG.

The JSON outputs now also include `topology_groups`, which groups component payloads by topological level for downstream tooling, dashboards, or static-site portfolio embeds that want a layered SCC view without recomputing the grouping client-side.

Example `topology_groups` excerpt:
```json
[
  {
    "level": 0,
    "component_count": 1,
    "component_ids": ["C0"],
    "components": [
      {
        "id": "C0",
        "nodes": ["A", "B", "C"],
        "size": 3,
        "topology_level": 0,
        "incoming_component_count": 0,
        "outgoing_component_count": 1,
        "bottleneck_role": "source"
      }
    ]
  },
  {
    "level": 1,
    "component_count": 1,
    "component_ids": ["C1"],
    "components": [
      {
        "id": "C1",
        "nodes": ["D", "E"],
        "size": 2,
        "topology_level": 1,
        "incoming_component_count": 1,
        "outgoing_component_count": 1,
        "bottleneck_role": "bridge"
      }
    ]
  }
]
```

You can render the DOT file with Graphviz if installed:
```bash
dot -Tpng condensation.dot -o condensation.png
```

## Tarjan vs. Kosaraju comparison

The `compare` command runs both linear-time SCC algorithms against the same graph, checks whether they agree on the deterministic component ordering used by this project, and reports simple timing samples for interview talking points.

Example output excerpt:
```json
{
  "algorithms_match": true,
  "repeat": 10,
  "average_ms": {
    "tarjan": 0.031251,
    "kosaraju": 0.040812
  },
  "faster_algorithm": "tarjan | kosaraju | tie"
}
```

This gives the project a stronger "theory plus evaluation" story: one implementation is enough to solve the problem, but comparing both shows awareness of alternative SCC strategies and the trade-off of Kosaraju's transpose/pass structure.

The comparison flow can now also write portfolio-ready artifacts directly:
- `showcase-demo` adds a final recruiter-friendly landing page in Markdown/HTML that reuses the graph summary and, when `--compare-json-path` is supplied, the exact linked benchmark snapshot while linking the raw explain/condensation/benchmark artifacts together
- `--json-output` writes the compare payload to disk without relying on shell redirection, which makes artifact bundles easier to script and review
- `--csv-output` writes one row per timing run so you can chart variance in a spreadsheet or static site
- `--markdown-output` writes a report with graph metadata, average timings, per-run timing rows, a component roster, and ready-made interview talking points
- `--html-output` writes a static benchmark dashboard with summary cards, per-trial timing bars, a component gallery, and sibling artifact links
- `--png-output` drives a headless Chrome/Chromium capture of that dashboard so the same run can emit a slide-ready bitmap companion without a manual screenshot round-trip
- `--png-width`, `--png-height`, `--png-capture-ms`, and `--chrome-binary` let you tune the raster capture viewport, wait budget, and browser executable when needed
- the repo includes a checked-in sample bundle under `docs/artifacts/tarjan-scc-lab/` for screenshot-friendly demos

Example Markdown report excerpt:
```md
# Tarjan vs Kosaraju benchmark report

## Graph summary
| metric | value |
| --- | --- |
| graph file | `sample_graph.json` |
| node count | 8 |
| edge count | 10 |
| strongly connected components | 4 |

## Per-run timings (ms)
| trial | tarjan_ms | kosaraju_ms | delta_ms | winner |
| --- | ---: | ---: | ---: | --- |
| 1 | 0.031251 | 0.040812 | 0.009561 | tarjan |
```

The HTML dashboard is especially useful for portfolio hosting because it keeps the benchmark summary, trial-by-trial comparison, component roster, and links to the sibling JSON/CSV/Markdown/PNG artifacts together in one static page. The PNG helper builds directly on that dashboard so slide decks, chat uploads, and README thumbnails can reuse the same artifact bundle with one extra flag. The new showcase page sits one level above that bundle so reviewers can start with the text explanation and condensation layers, then click into the benchmark dashboard only when they want the deeper evidence.

## Future improvements
- stream very large graphs from edge lists instead of loading everything into memory first
- add a cross-graph landing page that compares multiple SCC fixtures side by side with shared topology and benchmark cards
