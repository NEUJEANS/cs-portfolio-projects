# Brief research — graph-routing SVG summary card

## Sources checked
- MDN: SVG `viewBox` attribute
- MDN: SVG `<title>` element

## Takeaways used in this slice
- `viewBox` should define the full logical drawing area so the exported card can scale cleanly in README thumbnails and slide decks.
- adding `preserveAspectRatio` makes the scaling behavior more predictable when the SVG is embedded in differently sized containers
- `<title>` should be present for accessible naming, and placing it first keeps the output aligned with SVG compatibility guidance
- keeping the SVG fully static and self-contained avoids browser/runtime differences that would make the checked-in artifact noisy across reruns
