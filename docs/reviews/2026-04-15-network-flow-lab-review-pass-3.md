# Review pass 3 - network-flow-lab

- Checked input validation and resume safety.
- Issue found: malformed graph payloads or negative capacities would create confusing failures.
- Fix applied: added explicit graph validation plus tests for invalid capacities and disconnected graphs.
