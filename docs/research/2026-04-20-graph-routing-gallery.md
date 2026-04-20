# Brief research — graph-routing gallery landing page

## Sources checked
- MDN: HTML `<article>` element
- MDN: HTML `<dl>` element

## Takeaways used in this slice
- `<article>` is a good fit for each scenario card because MDN describes it as self-contained, independently reusable content; that matches a static portfolio gallery where each routing incident/story should stand on its own.
- `<dl>` works well for compact metric summaries when the page needs term/value pairs like changed routes, changed edges, or cycle state without bloating the layout into a wide table.
- keeping artifact links relative makes the gallery portable as a checked-in static bundle under `docs/artifacts/`, so the Markdown/HTML outputs can move together without breaking local navigation.
- the landing page should summarize several distinct routing stories, not just one happy-path diff, so the committed bundle now mixes same-cost reroutes, a negative-cycle incident, and a reachability failure.
