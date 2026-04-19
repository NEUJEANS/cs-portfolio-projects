# Regex engine showcase explainer refresh and self-test — 2026-04-19

## Refresh
- reuse `RegexEngine(...).explain()` as the single source of truth for showcase explainers instead of inventing a second AST/NFA export path
- summarize AST structure with small counts/stories that are readable in one card, not a full recursive dump
- keep wording portable and recruiter-friendly: relative links, static HTML, no client-side JS, no build tooling
- watch for small presentation bugs when converting metrics to English labels (`class` -> `classes`, missing accept state fallback, repeated-token compression)

## Self-test
1. Why derive the explainer cards from `explain()` instead of hand-curated metadata?
   - because it keeps the showcase honest and reproducible: later runs regenerate from the real parser/compiler output.
2. Why summarize the AST as a short story instead of embedding the raw JSON tree?
   - the audience for the showcase page is browsing quickly; the raw JSON trace still exists, but the card should explain the shape in one glance.
3. What failure modes matter most here?
   - awkward wording/typos, fragile links, and misleading metrics when the AST or NFA summary formatting does not match the underlying explain payload.
