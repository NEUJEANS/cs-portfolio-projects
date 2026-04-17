# 2026-04-17 static-site-generator sitemap + RSS slice

- [x] confirm repo sync before editing
- [x] identify `static-site-generator` as the next worthwhile slice because the project checklist still had sitemap/RSS generation open
- [x] do brief research on the sitemap protocol and RSS 2.0 channel/item requirements
- [x] skip extra language refresh because the slice stays inside the existing Node/CommonJS generator and test harness
- [x] update/add checklist docs so the slice is resumable
- [x] reserve root-level `_site.json` metadata without copying it into `dist/`
- [x] generate `sitemap.xml` with absolute URLs plus optional `lastmod`, `changefreq`, `priority`, and `sitemap: false`
- [x] generate `rss.xml` for dated pages with absolute item links plus optional `rss: false`
- [x] expand automated tests for reserved config handling, sitemap/RSS output, and the mirrored legacy test entrypoint
- [x] update README and project checklist with the new site-metadata workflow
- [x] run tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit, push, and append wrap-up
