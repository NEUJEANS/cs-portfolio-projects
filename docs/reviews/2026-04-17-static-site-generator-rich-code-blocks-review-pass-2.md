# Static-site-generator rich code blocks review - pass 2

## Focus
Code-sample readability and consistency across browsers / themes.

## Issue found
- The richer code-block frame relied on browser-default `<pre>` typography, which left the monospace stack, line height, and tab width implicit and could make screenshots / previews look inconsistent across environments.

## Fix applied
- Added an explicit monospace font stack plus `font-size`, `line-height`, and `tab-size` rules to `.code-block pre`.

## Result
- Rendered code samples now stay visually stable and easier to read in portfolio screenshots and local previews.
