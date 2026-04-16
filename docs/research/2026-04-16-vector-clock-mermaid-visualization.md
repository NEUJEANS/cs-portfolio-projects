# 2026-04-16 vector clock Mermaid visualization note

Goal: make the vector-clock lab feel more portfolio-ready by turning partition/heal events into a diagram students can paste into GitHub Markdown.

Key takeaways used for this slice:
- Mermaid sequence diagrams are a good fit for message/event timelines because GitHub renders them directly in Markdown.
- A partition scenario already has an ordered event list, replica names, and version payloads, so the existing simulation output can drive diagram generation without introducing a separate model.
- The most useful visualization is not every internal clock merge step, but the student-facing story: partition layout, isolated writes, anti-entropy heal, and optional conflict merge.
- For readability, notes should include both value and vector clock so the diagram reinforces causality rather than only showing messages.

Implementation direction:
- add a deterministic Mermaid renderer for partition simulation results
- expose it through a CLI command so students can generate a diagram from the same scenario used in tests and demos
- document a copy/paste workflow in the project README
