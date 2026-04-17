# 2026-04-17 static-site-generator archive pagination research

## Brief takeaways
- Accessible pagination patterns are small but important: wrap controls in a labelled `<nav>`, expose the current page with `aria-current="page"`, and keep explicit previous/next links for keyboard and screen-reader users.
- For portfolio-style archives, a simple `page/<n>/index.html` route structure keeps pagination predictable without introducing query-string routing or extra dependencies.
- Large archive timelines should keep page 1 biased toward the newest and most important entries, so pinned / featured content should stay on the first page while older items spill onto later pages.

## Slice decision
- add a CLI `--archive-page-size <count>` option that paginates generated archive index, yearly archive, and monthly archive pages
- keep the first month archive page special by preserving pinned content plus the featured newest entry before pagination continues
- add direct regression coverage for paginated output names, CLI parsing, and the generated page-to-page navigation links
