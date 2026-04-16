# Link-State Routing Lab Research - 2026-04-16

## Goal
Add a networking project that complements the existing distance-vector routing lab with a stronger shortest-path-first / topology-flooding model.

## Brief findings
- Link-state routing protocols such as OSPF have each router advertise only its directly connected links.
- Routers flood LSAs so every node can build a synchronized link-state database (LSDB).
- Sequence numbers are the core defense against stale updates; newer LSAs replace older copies.
- Aging matters because stale topology data should eventually be withdrawn instead of living forever.
- Once the LSDB is synchronized, each router runs Dijkstra with itself as the root to compute forwarding entries.

## Scope chosen for this slice
Model the educational core, not full OSPF complexity:
- weighted symmetric topology input
- per-router LSA origination
- hop-by-hop flooding log
- stale-update rejection using sequence numbers
- max-age withdrawal behavior
- deterministic SPF forwarding tables

## References
- Web search summary on OSPF/link-state basics gathered in-session via OpenClaw web search
- General OSPF/link-state concepts cross-checked against common networking references (IBM docs, Wikipedia, Cisco/community tutorials surfaced by search)
