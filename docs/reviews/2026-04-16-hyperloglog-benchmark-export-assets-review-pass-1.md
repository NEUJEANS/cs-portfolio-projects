# HyperLogLog benchmark export assets review - pass 1

## Focus
SVG validity and portability.

## Issue found
- The first SVG export used a `font-family` attribute with nested double quotes around `"Segoe UI"`, which produced invalid XML for strict parsers.

## Fix applied
- Switched the generated `font-family` attribute to a single-quoted attribute value.
- Added an XML parse assertion in the SVG renderer test so malformed SVG markup now fails the test suite.

## Result
- The SVG output is now parseable as XML and safer to embed in static portfolio pages.
