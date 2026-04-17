# branch-predictor-lab review pass 10

## Focus
SVG validity for the new comparison-card renderer.

## Issue found
The first SVG export used a `font-family` attribute that embedded unescaped double quotes around `Segoe UI`, which made the committed SVG markup invalid XML.

## Fix applied
- simplified the shared SVG font stack in `projects/branch-predictor-lab/branch_predictor.py` so the attribute no longer embeds nested quotes
- regenerated both committed comparison-card SVG artifacts
- verified both SVG files parse cleanly with Python XML parsing

## Result
The comparison cards are now valid SVG/XML files instead of browser-tolerated-but-invalid markup.
