# log-analyzer gallery deep-links refresh — 2026-04-19

## Quick refresh
- the facet-ranking gallery now treats URL state as part of the artifact UX: query params mirror search/sort/filter/hide-empty controls, and the hash points at one focused slice card.
- each card gets a deterministic `facet-...` fragment ID generated from the facet label, with numeric suffixes if labels ever collide after slugging.
- `history.replaceState()` keeps the address bar synced without reloading the page, while `hashchange` still handles manual fragment navigation.
- copy-link UX should not assume clipboard writes always succeed; browser permissions can fail even when the API exists.

## Self-test checklist
- open the committed gallery and confirm the default view shows all slices with no focus state
- set a focused hash and verify visible count drops to one and the “Show all slices” control appears
- clear the hash and verify the gallery returns to the unfocused multi-card view
- confirm query params survive reload and rehydrate the selected search/filter/sort state
- if clipboard write is blocked, confirm the copy-link flow falls back to a manual prompt instead of failing silently
