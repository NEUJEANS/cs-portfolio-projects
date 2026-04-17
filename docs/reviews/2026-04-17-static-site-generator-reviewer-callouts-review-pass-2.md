# Static-site-generator reviewer callouts review — pass 2

## Focus
Generated-page CSS compatibility and visual robustness.

## Issue found
- An early draft used `color-mix()` to tint callout borders/shadows. That is avoidable for a small dependency-free static generator and adds unnecessary browser-compatibility risk for student portfolio pages.

## Fix applied
- Simplified the callout panel styling to plain borders/background theme variables while keeping distinct reviewer/architecture/performance/etc. tones and dark-mode overrides.

## Result
- The callout styling stays polished without depending on newer CSS color-composition behavior.
