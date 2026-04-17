# Static Site Generator Checklist

## 2026-04-14 vertical slice: metadata-driven multi-page portfolio build
- [x] identify static-site-generator as an unfinished / weak portfolio project
- [x] do short web research on minimal static site generator features worth adding
- [x] do a short Node.js parsing and test refresh with a self-test note
- [x] add a project checklist for resumability
- [x] implement front matter parsing, metadata support, ordered navigation, and shared page layout
- [x] expand automated tests for parsing, rendering, sorting, and build output
- [x] update README with stronger portfolio framing and usage examples
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-15 vertical slice: asset pipeline and image support
- [x] identify the next weakest static-site-generator gap: realistic static assets and a stale failing test file
- [x] confirm the slice can be completed without extra web research or language refresh
- [x] add a resumable checklist for the slice
- [x] implement recursive asset copying so non-Markdown files ship with the built site
- [x] add Markdown image rendering for portfolio screenshots and diagrams
- [x] repair and expand the project test suite so `npm test` passes end-to-end
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-15 vertical slice: nested routes and relative page links
- [x] identify `static-site-generator` as the next unfinished project because nested page routes and internal markdown links were still missing
- [x] skip extra web research because the next slice was already clearly scoped in the local README/checklist
- [x] do a short Node/path handling refresh with a quick relative-path self-test
- [x] add a resumable checklist for the slice
- [x] preserve nested output paths for Markdown pages, including `index.md` -> `index.html`
- [x] rewrite internal `.md` links into working relative `.html` links across folders and keep nav links relative per page
- [x] expand automated tests for nested pages, relative nav links, and preserved assets
- [x] update README with nested-route behavior and new future follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-16 vertical slice: ordered lists and blockquotes
- [x] identify `static-site-generator` as still worth strengthening because richer narrative docs formatting was still missing
- [x] skip extra web research and language refresh because ordered-list and blockquote parsing fit the existing hand-rolled Markdown renderer
- [x] add a resumable checklist for the slice
- [x] implement ordered-list rendering with preserved non-1 start values
- [x] implement blockquote rendering that supports multi-paragraph quote bodies
- [x] style blockquotes in the shared layout for portfolio-ready callouts
- [x] expand automated tests for ordered lists, blockquotes, and end-to-end generated pages
- [x] update README and project checklist with the new formatting support
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-16 vertical slice: generated tag archive pages
- [x] identify `static-site-generator` as still weaker than the more mature portfolio projects because it lacked collection/archive navigation
- [x] skip extra web research and language refresh because tag-archive generation is a direct extension of the current front matter and template flow
- [x] add a resumable checklist for the slice
- [x] implement generated `tags/` index and per-tag archive pages from front matter metadata
- [x] link page-header tag pills into the generated archive pages and add a `Tags` nav entry when archives exist
- [x] expand automated tests for generated tag pages, deduplicated tags, and relative links from nested content
- [x] update README and project checklist with the new archive behavior
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-16 vertical slice: shared header/footer template partials
- [x] identify `static-site-generator` as the next unfinished project because reusable layout chrome still required copy-pasting header/footer HTML into every page
- [x] skip extra web research and language refresh because the slice extends the existing Node/CommonJS template pipeline directly
- [x] add a resumable checklist for the slice
- [x] reserve `content/_partials/` for shared `header.html` and `footer.html` templates
- [x] inject page-aware placeholders such as `{{rootPath}}`, `{{navigation}}`, `{{tags}}`, `{{sourcePath}}`, and `{{outputPath}}` into shared partials
- [x] keep `_partials/` out of page discovery and static-asset copying
- [x] expand automated tests for reserved partial directories, shared header/footer rendering, generated tag pages, and nested relative links
- [x] update README and project checklist with the new partial-template behavior
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-16 vertical slice: authoring watch mode
- [x] identify `static-site-generator` as still unfinished because local authoring required manually rerunning the build after every content or partial edit
- [x] skip extra web research and language refresh because a polling-based watch loop is a direct extension of the existing Node/CommonJS filesystem workflow
- [x] add a resumable checklist for the slice
- [x] implement CLI `--watch` mode with configurable `--watch-interval` parsing
- [x] rebuild when Markdown files, static assets, or shared `_partials/` templates change
- [x] keep watch mode dependency-free and Linux-friendly by using content snapshots instead of recursive native watchers
- [x] expand automated tests for CLI flag parsing, watch snapshots, and end-to-end watch rebuild behavior
- [x] update README and project checklist with the new watch-mode workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-16 vertical slice: local preview server with live reload
- [x] identify `static-site-generator` as still unfinished because authors could rebuild locally but still had no built-in way to browse the generated site
- [x] skip extra web research and language refresh because a tiny preview server fits the existing Node/CommonJS standard-library workflow directly
- [x] add a resumable checklist for the slice
- [x] implement CLI `--serve` mode with configurable preview ports
- [x] serve the generated `dist/` output with extensionless route handling for nested pages
- [x] inject browser auto-refresh only when preview mode runs alongside `--watch`
- [x] expand automated tests for preview routing, serve-only behavior, and watch+serve live reload flow
- [x] update README and project checklist with local preview usage plus the next missing-route follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-16 vertical slice: custom 404 pages and friendly preview misses
- [x] identify `static-site-generator` as still unfinished because missing routes still fell back to a plain-text preview error and no portfolio-ready `404.html` was generated by default
- [x] skip extra web research because the next slice was already explicitly called out in the local README/checklist
- [x] do a short Node/path handling refresh with a quick self-test for root-level `404.html` links and missing-route resolution
- [x] add a resumable checklist for the slice
- [x] generate a default `404.html` fallback page while letting authors override it with `404.md`
- [x] keep authored `404.md` pages out of navigation unless `nav: true` is set explicitly
- [x] make the preview server return HTML 404 pages instead of plain text when `404.html` exists
- [x] support preview-only placeholders such as `{{requestedPath}}`, `{{requestedUrl}}`, and `{{statusCode}}` inside custom 404 pages
- [x] expand automated tests for generated 404 pages, authored custom 404 pages, and preview missing-route responses
- [x] update README and project checklist with the new fallback-page workflow and the next code-block styling follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-17 vertical slice: richer code-block presentation
- [x] identify `static-site-generator` as still unfinished because fenced code blocks were plain `<pre>` dumps with no presentation polish
- [x] do brief web research on accessible syntax-highlighting / code-sample presentation patterns
- [x] skip extra language refresh because the slice stays inside the existing Node/CommonJS Markdown renderer
- [x] add a resumable checklist for the slice
- [x] parse fenced code-block metadata such as `title=` / `filename=`
- [x] render richer code-block frames with language badges and line-number gutters
- [x] keep the new code-block styling readable in both light and dark color schemes
- [x] expand automated tests for fence metadata parsing and rendered HTML output
- [x] update README and project checklist with the richer code-block workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-17 vertical slice: code-sample copy controls
- [x] identify `static-site-generator` as still unfinished because portfolio code samples looked polished but were not yet interactive
- [x] do brief web research on clipboard access constraints and accessible live-region status patterns
- [x] skip extra language refresh because the slice stays inside the existing Node/CommonJS renderer with a tiny inline browser helper
- [x] add a resumable checklist for the slice
- [x] add copy-to-clipboard controls plus polite status feedback to rendered fenced code blocks
- [x] provide a legacy copy fallback when `navigator.clipboard.writeText()` is unavailable
- [x] inject the copy helper only on pages that actually render code blocks
- [x] expand automated tests for copy-button markup, helper injection, and the synced duplicate test entrypoint
- [x] update README and project checklist with the interactive code-sample workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-17 vertical slice: reviewer + architecture callout panels
- [x] identify `static-site-generator` as still unfinished because the project checklist still had callout annotations open for code samples and architecture notes
- [x] do brief research on GitHub-style `[!TYPE]` blockquote markers to keep authoring lightweight and familiar
- [x] skip extra language refresh because the slice stays inside the existing Node/CommonJS Markdown renderer and test harness
- [x] add a resumable checklist for the slice
- [x] render focused callout panels for markers such as `[!REVIEWER]` and `[!ARCHITECTURE]` while preserving ordinary blockquotes
- [x] style the new callouts for light/dark themes without disturbing the existing blockquote presentation
- [x] expand automated tests for Markdown callout rendering, generated-page output, and the synced duplicate test entrypoint
- [x] update README and project checklist with the new callout workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
- [ ] consider side-by-side comparison blocks for before/after refactors or benchmark deltas in a future run

## 2026-04-17 vertical slice: before/after comparison blocks
- [x] identify `static-site-generator` as still unfinished because the checklist still had side-by-side refactor and benchmark storytelling open
- [x] do brief research on extended Markdown containers and CSS grid layout patterns for lightweight responsive comparisons
- [x] skip extra language refresh because the slice stays inside the current Node/CommonJS Markdown renderer and existing test harness
- [x] add a resumable checklist for the slice
- [x] render `::: comparison` containers with `::before::`, `::after::`, and optional `::delta::` panels
- [x] keep the new comparison layout responsive in light/dark themes without injecting code-copy helpers on non-code pages
- [x] expand automated tests for fence metadata parsing, rendered Markdown output, generated-page output, and the synced duplicate test entrypoint
- [x] update README and project checklist with the new comparison-block workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
- [ ] consider sitemap.xml or RSS feed generation in a future run

## 2026-04-17 vertical slice: sitemap.xml and RSS feed generation
- [x] identify `static-site-generator` as still unfinished because the checklist still had sitemap/RSS generation open for blog-style portfolio posts
- [x] do brief research on the sitemap protocol plus RSS 2.0 channel/item requirements
- [x] skip extra language refresh because the slice stays inside the current Node/CommonJS build pipeline and test harness
- [x] add a resumable checklist for the slice
- [x] reserve root-level `_site.json` metadata for site URL + feed defaults without copying it into `dist/`
- [x] generate `sitemap.xml` for authored pages plus generated tag archives while excluding `404.html` and supporting `sitemap: false`
- [x] generate `rss.xml` for dated pages with optional `rss: false` opt-outs and absolute item links
- [x] expand automated tests for reserved `_site.json` handling, sitemap/RSS output, and the synced duplicate test entrypoint
- [x] update README and project checklist with the new site-metadata workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
- [x] consider date-based archive pages or timeline indexes in a future run

## 2026-04-17 vertical slice: dated archive index and yearly timeline pages
- [x] identify `static-site-generator` as still unfinished because dated entries were available for RSS but not yet browseable as on-site archive pages
- [x] do brief research on archive-page UX patterns for reverse-chronological year/month navigation
- [x] skip extra language refresh because the slice stays inside the existing Node/CommonJS generator and test harness
- [x] add a resumable checklist for the slice
- [x] generate `archives/index.html` and yearly `archives/<year>/index.html` pages from dated content
- [x] group yearly archive pages into reverse-chronological month sections with direct jump links
- [x] support `archive: false` so dated draft pages can stay out of generated archive timelines
- [x] expand automated tests for archive collection building, generated archive pages, and the synced duplicate test entrypoint
- [x] update README and project checklist with the new archive workflow and next follow-up
- [x] run project tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
