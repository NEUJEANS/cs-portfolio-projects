# Static-site-generator comparison blocks review — pass 2

## Focus
End-to-end generated-page coverage for the new comparison block workflow.

## Issue found
- The first generated-page test assumed the output file would be named from the page title (`refactor-notes.html`), but the generator only uses front-matter `slug` overrides or the source-path default. That made the comparison-block integration test fail even though the renderer itself worked.

## Fix applied
- Added an explicit `slug: refactor-notes` field to the generated-page fixture in both maintained test entrypoints.
- Re-ran `npm test` and the legacy `node --test test_static_site_generator.js` entrypoint after the fix.

## Result
- The end-to-end comparison-block test now matches the generator’s real output rules and passes reliably.
