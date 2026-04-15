# Review Pass 1 — Raft state-machine application

- Checked whether the new slice actually closed the loop from replication to visible state.
- Found that the simulator summary needed explicit `last_applied`, `state_machine`, and `applied_commands` fields to make the improvement portfolio-visible.
- Fix applied: exposed those fields and updated the README/checklist so the project now describes the end-to-end flow accurately.
