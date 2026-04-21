# Research — library-manager-sqlite dashboard export slice — 2026-04-21

## Goal
Add a small recruiter-friendly dashboard export to `library-manager-sqlite` without turning the project into a web app.

## Sources checked
- MDN table accessibility guide: `https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content/Table_accessibility`
- MDN `<time>` element reference: `https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/time`

## Notes
- A visible `<caption>` gives readers and screen-reader users a quick summary of what each table represents, which fits a static portfolio artifact better than hidden descriptions.
- `<thead>` / `<tbody>` grouping and explicit `scope="col"` headers keep the HTML dashboard structured and CSS-friendly without adding framework overhead.
- The HTML `<time>` element expects machine-readable ISO-style timestamps, so the export should store a normalized snapshot time rather than free-form prose.
- For a portfolio-friendly slice, one shared snapshot model can drive both Markdown and HTML output, which keeps the CLI lightweight while still producing screenshot-ready artifacts.

## Decision
Implement a single dashboard snapshot builder that powers:
- Markdown output for quick README/docs embedding
- HTML output with semantic tables, captions, and timestamp metadata
- a reproducible `generated_at` field so committed artifacts can be regenerated cleanly
