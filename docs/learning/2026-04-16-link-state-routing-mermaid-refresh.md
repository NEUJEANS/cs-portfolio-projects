# Link-State Routing Mermaid Refresh - 2026-04-16

## Quick refresh
- Mermaid flowcharts support labeled edges and link-level styling, which is enough for small routing demos.
- The topology view should stay symmetric and easy to read; emit each physical edge once.
- The SPF overlay should be source-specific and derived from chosen route paths, not recomputed separately with different tie-breaking.
- CLI export is more reusable than hard-coding a docs artifact because users can redirect output anywhere.

## Self-test
1. Why emit each topology edge only once?  
   To avoid duplicated visual links and make the diagram easier to read.
2. Why build SPF edges from final routes instead of a separate parent map?  
   It guarantees the highlighted tree matches the exact forwarding decisions already returned by the simulator.
3. Why keep Mermaid export text-based?  
   It stays GitHub-friendly, scriptable, and easy to save into Markdown or artifacts.
