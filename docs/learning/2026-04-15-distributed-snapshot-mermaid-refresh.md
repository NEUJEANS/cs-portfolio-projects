# Distributed Snapshot Mermaid Refresh

## Refresher points
- Mermaid `sequenceDiagram` renders participants in declaration order, so explicitly listing processes keeps the output stable.
- Normal message arrows like `A->>B:` work well for transfers, while dashed arrows like `A-->>B:` read naturally for marker/control traffic.
- `Note over A,B,C:` is a compact way to show recorded balances and consistency summaries without inventing extra diagram syntax.
- Keep diagram text simple and sanitized because quotes and line breaks can make generated Mermaid harder to embed in markdown.

## Self-test
1. Why explicitly declare all participants instead of relying on implicit order?
   - It keeps diagram order deterministic and presentation-friendly.
2. Why use a dashed arrow for markers?
   - It visually separates protocol-control messages from bank-transfer data messages.
3. Why include a final consistency note in the diagram?
   - It ties the visual execution trace back to the key invariant the project is demonstrating.
