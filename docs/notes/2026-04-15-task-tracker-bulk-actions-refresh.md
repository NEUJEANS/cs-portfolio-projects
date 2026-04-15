# Task Tracker CLI bulk-actions refresh

Quick refresh before implementing the slice:

- Reuse the existing `add_list_arguments(...)` filter surface so `bulk` stays consistent with `list` and `export`.
- Keep business logic in `TaskService`; let the CLI focus on parsing, confirmation rules, and rendering.
- For recurring tasks, preserve the existing `done` behavior by spawning the next occurrence during bulk completion too.
- Destructive operations should be explicit in the CLI. Requiring `--yes` for bulk delete keeps the portfolio project safer and easier to demo.

Self-test checklist:

- Can I bulk-complete all `--tag demo` tasks? Yes.
- Will recurring matches spawn the next dated task? Yes.
- Can bulk delete run accidentally without a confirmation flag? No.
- Can the command print a machine-readable summary for demos/tests? Yes, via `--json`.
