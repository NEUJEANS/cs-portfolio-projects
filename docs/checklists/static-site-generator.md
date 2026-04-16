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
- [ ] run secret scan
- [ ] commit and push
- [ ] append wrap-up
