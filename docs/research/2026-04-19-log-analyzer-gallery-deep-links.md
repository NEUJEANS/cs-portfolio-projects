# log-analyzer gallery deep-links research — 2026-04-19

## Goal
Add shareable deep links to the static facet-ranking gallery without introducing dependencies or turning the artifact into a non-portable app.

## Brief references checked
- MDN `History.replaceState()` — safe way to mirror UI state into the address bar without a page reload, but the URL must stay same-origin.
- MDN `URLSearchParams` — straightforward way to serialize search/filter/sort state into query params.
- MDN `hashchange` — fragment updates are a natural fit for focused per-card deep links, but `replaceState()` itself does not fire `hashchange`.

## Decision
Use a split URL model:
- query params for gallery controls (`q`, `sort`, `hide-empty`, and `facet-*` filters)
- hash fragments for one focused slice card

## Why this shape fits
- keeps the exported HTML self-contained and GitHub-Pages-friendly
- lets reviewers copy one URL that reopens the same search/filter/focus state
- avoids adding a router or any third-party JS
- deterministic fragment IDs make committed artifacts stable across regenerations from the same data

## Implementation notes
- generate one stable slug per facet card and de-duplicate collisions with numeric suffixes
- load initial state from `location.search` plus `location.hash`
- use `history.replaceState()` for non-reloading URL sync as controls change
- still listen for `hashchange` so manual fragment edits/back-forward navigation update the focused view

## Risks to watch
- clearing the hash must also clear focused-card state
- clipboard writes can fail even when `navigator.clipboard` exists, so copy-link UX needs a manual fallback
- tests should lock the shareable-view hooks so a future HTML cleanup does not silently drop them
