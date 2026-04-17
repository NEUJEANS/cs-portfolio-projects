# Static-site-generator archive pagination review — pass 1

## Focus
CLI surface and regression coverage for the new page-size workflow.

## Issue found
- The implementation already threaded archive pagination through the renderer, but the test suite still only covered the non-paginated archive path and never exercised the new CLI flag or generated `page/<n>/index.html` routes.

## Fix applied
- Extended the CLI parsing test to cover `--archive-page-size`.
- Added focused helper coverage for archive page-size validation and paginated output naming.
- Added an end-to-end build test that verifies paginated archive index, yearly archive, and monthly archive pages.

## Result
- The new archive pagination path now has direct automated coverage instead of relying on manual inspection.
