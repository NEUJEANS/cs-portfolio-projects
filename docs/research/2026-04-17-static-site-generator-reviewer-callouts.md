# 2026-04-17 static-site-generator reviewer callouts research

## Brief takeaways
- GitHub’s Markdown docs/examples already expose the `> [!TYPE]` blockquote marker style (for example `> [!TIP]`), so the syntax is familiar to developers without adding a heavier Markdown extension surface.
- Reusing blockquote-based markers keeps authored content readable in raw Markdown and degrades cleanly when a renderer does not understand the enhanced callout treatment.
- For this slice, the most portfolio-relevant variants are reviewer/architecture-oriented notes that explain *why* a code sample matters, not just what it does.

## Slice decision
- implement lightweight callout detection on top of existing blockquote parsing
- support focused portfolio variants such as `REVIEWER` and `ARCHITECTURE`, while leaving normal `>` blockquotes untouched
