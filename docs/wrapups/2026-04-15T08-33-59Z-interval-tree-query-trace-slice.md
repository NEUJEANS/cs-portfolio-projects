# Interval Tree Query Trace Slice Wrap-up

- Timestamp (UTC): 2026-04-15T08:33:59Z
- Project: interval-tree-lab
- What changed:
  - added Graphviz DOT query-trace export to visualize visited, pruned, and overlapping branches
  - added a new  CLI command and included trace output in the demo payload
  - updated README usage/design notes for the new trace workflow
  - added regression tests plus dated checklist, learning, and review notes for resumability
- Tests run:
  - 
  - {
  "all_overlaps": [
    {
      "end": 8,
      "label": "backup",
      "start": 5
    },
    {
      "end": 10,
      "label": "deploy",
      "start": 6
    },
    {
      "end": 23,
      "label": "analytics",
      "start": 15
    },
    {
      "end": 19,
      "label": "alerts",
      "start": 17
    }
  ],
  "command": "trace",
  "errors": [],
  "height": 3,
  "inorder": [
    {
      "end": 3,
      "label": "warmup",
      "start": 0
    },
    {
      "end": 8,
      "label": "backup",
      "start": 5
    },
    {
      "end": 10,
      "label": "deploy",
      "start": 6
    },
    {
      "end": 23,
      "label": "analytics",
      "start": 15
    },
    {
      "end": 19,
      "label": "alerts",
      "start": 17
    }
  ],
  "input": [
    "0-3:warmup",
    "5-8:backup",
    "6-10:deploy",
    "15-23:analytics",
    "17-19:alerts"
  ],
  "max_end": 23,
  "query": {
    "end": 18,
    "start": 7
  },
  "query_stats": {
    "nodes_visited": 4
  },
  "query_trace_dot": "digraph interval_tree_query_trace {\n  rankdir=\"TB\";\n  node [shape=record, fontname=\"Helvetica\"];\n  edge [fontname=\"Helvetica\"];\n  query [shape=note, style=\"filled\", fillcolor=\"#eef2ff\", label=\"query|[7, 18]\"];\n  node_0 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[6, 10]\\\\ndeploy|max_end=23\"];\n  query -> node_0 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_1 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[5, 8]\\\\nbackup|max_end=8\"];\n  query -> node_1 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_2 [style=\"filled\", fillcolor=\"#f8fafc\", penwidth=1, label=\"[0, 3]\\\\nwarmup|max_end=3\"];\n  node_1 -> node_2 [color=\"#94a3b8\", style=\"dashed\", label=\"pruned: left.max_end < query.start\"];\n  node_1 [xlabel=\"visited=1\"];\n  node_3 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[17, 19]\\\\nalerts|max_end=23\"];\n  query -> node_3 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_4 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[15, 23]\\\\nanalytics|max_end=23\"];\n  query -> node_4 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_3 -> node_4 [color=\"#2563eb\", style=\"solid\", label=\"search left\"];\n  node_0 -> node_1 [color=\"#2563eb\", style=\"solid\", label=\"search left\"];\n  node_0 -> node_3 [color=\"#2563eb\", style=\"solid\", label=\"search right\"];\n  root_anchor [shape=point, width=0.01, label=\"\"];\n  root_anchor -> node_0;\n}",
  "root": {
    "end": 10,
    "label": "deploy",
    "start": 6
  },
  "size": 5,
  "valid": true
}
  - {
  "all_overlaps": [
    {
      "end": 8,
      "label": "db-backup",
      "start": 5
    },
    {
      "end": 10,
      "label": "deploy",
      "start": 6
    },
    {
      "end": 9,
      "label": "qa",
      "start": 8
    },
    {
      "end": 23,
      "label": "analytics",
      "start": 15
    },
    {
      "end": 21,
      "label": "report",
      "start": 16
    },
    {
      "end": 19,
      "label": "alert-window",
      "start": 17
    }
  ],
  "any_overlap": {
    "end": 21,
    "label": "report",
    "start": 16
  },
  "command": "demo",
  "errors": [],
  "height": 4,
  "inorder": [
    {
      "end": 3,
      "label": "warmup",
      "start": 0
    },
    {
      "end": 8,
      "label": "db-backup",
      "start": 5
    },
    {
      "end": 10,
      "label": "deploy",
      "start": 6
    },
    {
      "end": 9,
      "label": "qa",
      "start": 8
    },
    {
      "end": 23,
      "label": "analytics",
      "start": 15
    },
    {
      "end": 21,
      "label": "report",
      "start": 16
    },
    {
      "end": 19,
      "label": "alert-window",
      "start": 17
    },
    {
      "end": 20,
      "label": "maintenance",
      "start": 19
    },
    {
      "end": 30,
      "label": "etl",
      "start": 25
    },
    {
      "end": 26,
      "label": "ping",
      "start": 26
    }
  ],
  "max_end": 30,
  "point": 26,
  "point_hits": [
    {
      "end": 30,
      "label": "etl",
      "start": 25
    },
    {
      "end": 26,
      "label": "ping",
      "start": 26
    }
  ],
  "query": {
    "end": 18,
    "label": "query",
    "start": 7
  },
  "query_trace_dot": "digraph interval_tree_query_trace {\n  rankdir=\"TB\";\n  node [shape=record, fontname=\"Helvetica\"];\n  edge [fontname=\"Helvetica\"];\n  query [shape=note, style=\"filled\", fillcolor=\"#eef2ff\", label=\"query|[7, 18]\\nquery\"];\n  node_0 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[16, 21]\\\\nreport|max_end=30\"];\n  query -> node_0 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_1 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[6, 10]\\\\ndeploy|max_end=23\"];\n  query -> node_1 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_2 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[5, 8]\\\\ndb-backup|max_end=8\"];\n  query -> node_2 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_3 [style=\"filled\", fillcolor=\"#f8fafc\", penwidth=1, label=\"[0, 3]\\\\nwarmup|max_end=3\"];\n  node_2 -> node_3 [color=\"#94a3b8\", style=\"dashed\", label=\"pruned: left.max_end < query.start\"];\n  node_2 [xlabel=\"visited=1\"];\n  node_4 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[15, 23]\\\\nanalytics|max_end=23\"];\n  query -> node_4 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_5 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[8, 9]\\\\nqa|max_end=9\"];\n  query -> node_5 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_4 -> node_5 [color=\"#2563eb\", style=\"solid\", label=\"search left\"];\n  node_1 -> node_2 [color=\"#2563eb\", style=\"solid\", label=\"search left\"];\n  node_1 -> node_4 [color=\"#2563eb\", style=\"solid\", label=\"search right\"];\n  node_6 [style=\"filled\", fillcolor=\"#f8fafc\", penwidth=2, label=\"[25, 30]\\\\netl|max_end=30\"];\n  node_7 [style=\"filled\", fillcolor=\"#f8fafc\", penwidth=2, label=\"[19, 20]\\\\nmaintenance|max_end=20\"];\n  node_8 [style=\"filled\", fillcolor=\"#dcfce7\", penwidth=2, label=\"[17, 19]\\\\nalert-window|max_end=19\"];\n  query -> node_8 [style=dashed, color=\"#16a34a\", label=\"overlap\"];\n  node_7 -> node_8 [color=\"#2563eb\", style=\"solid\", label=\"search left\"];\n  node_9 [style=\"filled\", fillcolor=\"#f8fafc\", penwidth=1, label=\"[26, 26]\\\\nping|max_end=26\"];\n  node_6 -> node_7 [color=\"#2563eb\", style=\"solid\", label=\"search left\"];\n  node_6 -> node_9 [color=\"#94a3b8\", style=\"dashed\", label=\"pruned: node.start > query.end\"];\n  node_6 [xlabel=\"visited=3\"];\n  node_0 -> node_1 [color=\"#2563eb\", style=\"solid\", label=\"search left\"];\n  node_0 -> node_6 [color=\"#2563eb\", style=\"solid\", label=\"search right\"];\n  root_anchor [shape=point, width=0.01, label=\"\"];\n  root_anchor -> node_0;\n}",
  "root": {
    "end": 21,
    "label": "report",
    "start": 16
  },
  "size": 10,
  "valid": true
}
- Reviews run:
  - pass 1: correctness + escaping fix
  - pass 2: readability/docs cleanup
  - pass 3: portfolio value + resumability check
- Secret scan:
  - 
- Commit hash: 8a83a01dbd8b184c4ded926c0b39850f74c9b735
- Next step:
  - add optional rendered SVG/PNG trace artifacts or query-step animation support for one or two canonical interval-search scenarios
