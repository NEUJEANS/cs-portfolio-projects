# 2026-04-16 distributed snapshot PNG assets refresh

## Quick refresh
- Reusing the project's SVG renderer keeps the vector and raster exports consistent instead of maintaining two drawing pipelines.
- Headless browser screenshots are a pragmatic optional dependency when you only need PNG output on demand, not for every simulation command.
- Matching the screenshot window size to the SVG root width/height avoids padding and keeps the committed PNG assets stable.

## Self-test
1. **Why generate PNG from SVG instead of duplicating the renderer in bitmap code?**  
   So one structured snapshot renderer stays authoritative and both export formats tell the same story.

2. **Why parse the SVG width and height before calling the browser?**  
   To make the screenshot crop exactly to the diagram canvas instead of capturing extra whitespace.

3. **Why keep SVG links in the walkthrough even after adding PNG export?**  
   SVG remains the crisp, diffable source artifact, while PNG is the compatibility fallback for tools that dislike vector embeds.
