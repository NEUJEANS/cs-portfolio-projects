# 2026-04-17 static-site-generator sitemap + RSS research

## Brief takeaways
- The sitemaps.org protocol keeps the core XML surface intentionally small: `<urlset>` with one `<url>` per page, a required `<loc>`, and optional `<lastmod>`, `<changefreq>`, and `<priority>` values.
- RSS 2.0 requires channel-level `title`, `link`, and `description`, while dated post-style items map cleanly onto per-page `title`, `description`, and `date` metadata.
- For a portfolio generator, a tiny root-level site config is enough to derive absolute URLs and feed defaults without adding a full CMS or extra dependencies.

## Slice decision
- add a reserved root `_site.json` file for `siteUrl` plus optional feed metadata
- emit `sitemap.xml` for built pages and generated tag archives while excluding fallback `404.html`
- emit `rss.xml` only for dated pages, with per-page `rss: false` / `sitemap: false` escape hatches for drafts or private write-ups
