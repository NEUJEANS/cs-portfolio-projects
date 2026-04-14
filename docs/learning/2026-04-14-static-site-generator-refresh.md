# Learning Refresh — Node.js Parsing and Self-Test (2026-04-14)

## Refresh points
- use simple front matter parsing before bringing in dependencies
- keep parsing deterministic and test edge cases directly
- sort generated pages with explicit `order` metadata first, then stable fallback by title
- escape HTML before injecting rendered content into templates
- return build outputs from the main build function to make tests stronger

## Self-test
1. What metadata fields matter most for a portfolio page generator?
   - title, description, order, slug, tags, nav visibility
2. Why return output filenames from `build()`?
   - it makes integration tests verify both file generation and page ordering behavior
3. What is the main safety issue in naive HTML generation?
   - unescaped content can break markup or introduce injection problems

## Result
Proceed with a dependency-free implementation that stays small but demonstrates real static-site-generation concepts.
