# Research — Static Site Generator Upgrade (2026-04-14)

## Goal
Strengthen the weak static-site-generator project with a more portfolio-worthy vertical slice instead of leaving it as a single-file Markdown-to-HTML toy.

## Quick research takeaways
A minimal but credible static site generator for a student portfolio should usually support:
- Markdown content separated from page presentation
- metadata / front matter for title, description, tags, ordering, and slugs
- reusable layout / templating for consistent pages
- generated navigation so multiple pages feel like a real site
- deterministic output suitable for GitHub Pages or local hosting

## Decision for this slice
Implement a dependency-free version of the following:
1. front matter parsing
2. page ordering and slug-based output names
3. shared layout with navigation
4. tags and description metadata in the generated HTML
5. stronger automated tests proving multi-page generation behavior

## Why this is a good next step
It upgrades the project from a parsing demo into a small publishing pipeline, which better reflects real-world CS and portfolio engineering skills.
