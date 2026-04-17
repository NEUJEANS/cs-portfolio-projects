# static-site-generator

## Overview
Generate a small multi-page static website from Markdown files with optional front matter.

## Why it is portfolio-worthy
This project shows practical compiler-style text processing, file-system automation, deterministic build output, lightweight templating, and test-driven Node.js development.

## Stack
- Node.js
- CommonJS
- built-in `node:test`

## Features
- converts Markdown files into standalone HTML pages while preserving nested content folders
- supports front matter metadata such as `title`, `description`, `order`, `slug`, `tags`, and `nav`
- tag pills in each page header link into the generated archive pages so visitors can browse related work without an external CMS
- optional shared `_partials/header.html` and `_partials/footer.html` templates let authors reuse portfolio chrome while keeping page content in Markdown
- pages with `date` metadata automatically generate a dated `archives/` index plus yearly timeline pages for portfolio updates and project logs, with `archive: false` available for opt-outs
- optional root-level `_site.json` metadata can generate deploy-ready `sitemap.xml` and `rss.xml` files with absolute site URLs for portfolio/blog hosting
- presents fenced code blocks in richer portfolio-ready frames with language badges, optional file titles from fence metadata, line-number gutters, and copy-to-clipboard controls with accessible status feedback
- turns GitHub-style blockquote markers such as `[!REVIEWER]` and `[!ARCHITECTURE]` into focused portfolio callout panels so code samples can carry concise “why this matters” notes
- renders `::: comparison` blocks into responsive before/after/delta panels so portfolio pages can show refactors or benchmark wins at a glance
- supports a dependency-free `--watch` mode with a configurable polling interval so content edits, new files, and shared partial updates trigger rebuilds during local authoring
- can serve the generated `dist/` folder through a built-in local preview server, including browser auto-refresh when `--serve` is combined with `--watch`
- generates a default `404.html` fallback and lets authors override it with `404.md`, including preview-only placeholders such as `{{requestedPath}}`
- builds top navigation automatically from page metadata while allowing hidden pages via `nav: false`
- generates a `tags/` directory of archive pages from front matter tags, including a browsable tags index and per-tag page listings
- renders a focused Markdown subset: headings, paragraphs, bullet lists, ordered lists, blockquotes, links, images, inline code, fenced code blocks, bold, and italics
- recursively copies non-Markdown assets into the output directory so screenshots, CSS files, and downloadable artifacts ship with the site
- preserves nested page paths and rewrites internal Markdown `.md` links into working relative `.html` links across folders
- applies a clean shared HTML layout and inline stylesheet
- sorts pages by explicit order and slug for predictable portfolio presentation
- keeps output dependency-free and runnable locally

## Supported front matter
```yaml
---
title: Projects
description: Short summary shown in the page header
order: 2
slug: student-projects
tags: [node, portfolio]
nav: true
date: 2026-04-16T10:30:00Z
lastmod: 2026-04-16
changefreq: weekly
priority: 0.8
rss: true
archive: true
---
```

## Usage
Create a content directory with Markdown files. Nested folders are preserved in the generated site, so `guides/setup.md` becomes `guides/setup.html` and links like `[Home](../index.md)` are rewritten automatically:

```md
---
title: Home
order: 1
description: My CS portfolio
---
# Welcome

- systems projects
- web projects

1. polish screenshots
2. publish a project tour

> Add short pull quotes or callouts for internship-ready case studies.
```

Then build the site:

```bash
node sitegen.js content dist
```

For a faster edit-build-preview loop, keep the generator running in watch mode:

```bash
node sitegen.js content dist --watch --watch-interval 250
```

If you want to browse the generated site locally after a one-shot build, start the built-in preview server:

```bash
node sitegen.js content dist --serve --serve-port 4173
```

For the full local authoring loop, combine `--watch` and `--serve` so rebuilds automatically trigger browser refreshes through a tiny Server-Sent Events channel:

```bash
node sitegen.js content dist --watch --serve --watch-interval 250 --serve-port 4173
```

Watch mode uses a small polling snapshot instead of platform-specific recursive file watching, so it also catches newly added Markdown files and `_partials/` template edits on Linux without extra dependencies. When `--serve` is enabled without `--watch`, the preview server serves the current `dist/` snapshot without injecting the live-reload client.

The generator now always produces a root-level `404.html`. If you do nothing, it emits a default fallback page that points visitors back into the portfolio. If you want a branded fallback, add `content/404.md`; it renders to `404.html` automatically and stays out of navigation unless you explicitly set `nav: true`. During local preview, missing-route responses can interpolate `{{requestedPath}}`, `{{requestedUrl}}`, and `{{statusCode}}` inside that custom page so authors can show friendlier diagnostics while testing broken links.

If you want shared layout chrome across every page, add optional partials under `content/_partials/`:

```html
<!-- content/_partials/header.html -->
<p class="brand"><a href="{{rootPath}}index.html">Student Portfolio</a></p>
{{navigation}}
<div class="hero">
  <h1>{{title}}</h1>
  <p>{{description}}</p>
  {{tags}}
</div>
```

```html
<!-- content/_partials/footer.html -->
<p>Source: <code>{{sourcePath}}</code></p>
<p><a href="{{rootPath}}assets/resume.pdf">Resume</a></p>
```

Available partial placeholders are `{{rootPath}}`, `{{navigation}}`, `{{title}}`, `{{description}}`, `{{tags}}`, `{{sourcePath}}`, and `{{outputPath}}`. The reserved `_partials/` directory is ignored during page discovery and static-asset copying, so those template files never leak into the generated site.

If pages include `tags`, the generator also creates `dist/tags/index.html` plus one archive page per tag, and the page-header tag pills link into those generated archives automatically. When tag archives are generated, `tags/` becomes reserved output space, so the builder will raise an error instead of silently overwriting an authored page or static asset that would land at the same path.

Ordered steps and pull-quote style callouts are also preserved, so project pages can mix tutorials, release notes, and narrative case studies without extra tooling.

For reviewer-style annotations around code or design decisions, use GitHub-style blockquote markers:

```md
> [!REVIEWER] Why this snippet matters
> This parser keeps output deterministic so review diffs stay compact.

> [!ARCHITECTURE]
> `loadPages()` stays separate from rendering so tests can verify discovery independently.
```

The renderer keeps ordinary blockquotes as blockquotes, but recognized markers such as `REVIEWER`, `ARCHITECTURE`, `PERFORMANCE`, `TRADEOFF`, `TESTING`, `TIP`, `NOTE`, and `WARNING` become styled callout panels in the generated page.

For refactor stories or benchmark write-ups, use a `::: comparison` block with `::before::`, `::after::`, and optional `::delta::` sections:

```md
::: comparison title="Tokenizer refactor" summary="Same output, less work."
Quick reviewer snapshot.

::before:: Legacy parser
- rescanned every file on each preview request
- duplicated slug normalization in two paths

::after:: Incremental parser
- reuses page metadata between rebuilds
- keeps link rewriting in one helper

::delta:: Benchmark delta
- rebuild time: **1.8s** -> **0.9s**
:::
```

The generated page keeps the before/after panels side-by-side on wider screens, stacks them on narrow screens, and gives the optional delta panel its own follow-up emphasis for quick reviewer scans.

Fenced code blocks are preserved for technical write-ups and can carry a title straight from the fence info string:

~~~md
```python title="scripts/build_portfolio.py"
from pathlib import Path
print(Path('portfolio').resolve())
```
~~~

Rendered code samples now show a language badge, an optional file/title pill, line numbers, and a copy button so walkthrough-style portfolio posts feel closer to polished docs than raw plain-text dumps. The renderer accepts `title=`, `file=`, or `filename=` in the fence info string, and the generated pages announce copy success/failure through a polite status region while falling back to a legacy copy path if the async Clipboard API is unavailable.

If you want deploy-ready discovery metadata for a hosted portfolio or blog, add an optional `content/_site.json` file:

```json
{
  "siteUrl": "https://example.com/portfolio",
  "title": "Student Portfolio Updates",
  "description": "New project write-ups and shipped improvements.",
  "language": "en-us"
}
```

When `_site.json` is present, each build also emits `dist/sitemap.xml` plus `dist/rss.xml`. Sitemap entries use absolute URLs derived from `siteUrl`, exclude the generated `404.html` page, honor optional front matter such as `lastmod`, `changefreq`, and `priority`, and can opt individual pages out with `sitemap: false`. RSS items are generated from pages that include a `date` value, can be suppressed per page with `rss: false`, and inherit the channel title/description from `_site.json` (falling back to the home page when omitted). The reserved `_site.json` file is ignored during page discovery and static-asset copying.

Pages with `date` metadata also generate `dist/archives/index.html` plus one yearly archive page under `dist/archives/<year>/index.html`. Those pages group entries into reverse-chronological month sections so portfolio updates, devlogs, and shipped slices are easier to browse. If a dated page should stay out of the generated timeline, set `archive: false` in front matter.

Generated files are written to `dist/` and the CLI prints a short build summary. In watch mode, the same summary is reprinted after each detected rebuild so authors can confirm which pages were regenerated.

## Test
```bash
npm test
```

If you need to run the legacy mirrored entrypoint directly, `node --test test_static_site_generator.js` stays in sync with `sitegen.test.js` for compatibility with older repo scripts.

## Example portfolio use cases
- personal project showcase
- class project microsite
- internship application portfolio
- learning journal or technical blog prototype

## Future Improvements
- optional theme presets or custom CSS hooks for different portfolio styles
- richer archive layouts such as monthly landing pages, featured entries, or excerpt cards
