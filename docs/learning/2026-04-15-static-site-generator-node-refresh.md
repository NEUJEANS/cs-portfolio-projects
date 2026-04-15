# Static Site Generator Node Refresh — 2026-04-15

## Refresher
- Use `fs.readdirSync(..., { withFileTypes: true })` to filter Markdown files without extra `stat` calls.
- Keep CommonJS exports explicit so the CLI can be tested directly with `require()`.
- For deterministic builds, sort pages by explicit front matter order and then by slug.
- In a small dependency-free generator, a focused Markdown subset is enough if the supported syntax is documented clearly.

## Self-test
1. What keeps page output stable between runs?  
   Sorting by `order` and slug before rendering.
2. How do we hide a page from navigation but still publish it?  
   Set `nav: false` and still emit the HTML file.
3. Why return exported helpers from the CLI module?  
   So parsing and rendering logic can be unit tested without shelling out.
