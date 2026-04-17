# Static-site-generator sitemap + RSS review — pass 2

## Focus
Generated XML output quality and regression coverage for page-level inclusion controls.

## Issue found
- Manual artifact inspection showed the RSS `<item>` blocks were emitted with shallow indentation, which made the generated feed harder to scan during reviews.
- The new sitemap path already supported `sitemap: false`, but the end-to-end test only asserted the existing `rss: false` draft behavior.

## Fix applied
- Indented RSS item blocks consistently under the channel node for cleaner generated output.
- Extended the end-to-end sitemap/RSS test fixture so the draft page sets `sitemap: false` and is explicitly excluded from the generated sitemap.

## Result
- The generated feed is easier to inspect manually, and the per-page sitemap opt-out now has direct regression coverage.
