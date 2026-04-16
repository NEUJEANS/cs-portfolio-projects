# Tarjan topology-groups review pass 2

- Focus: docs and learning-note alignment after the JSON shape change.
- Checked: project README example and the refresh/self-test note for the slice.
- Issue found: the learning note still described the grouped view as payload-only after `component_ids` was added.
- Fix applied: updated the self-test note to reflect the final API shape: full grouped payloads plus lightweight `component_ids`.
