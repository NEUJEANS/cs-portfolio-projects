# Review pass 2 — static-site-generator date archives

## What I checked
- archive opt-out behavior for dated but unpublished content
- generated archive HTML expectations vs. navigation state
- fixture realism for a dated draft page

## Issue found
- the draft fixture was excluded from the generated archive timeline but still appeared in navigation, which made the archive-page assertion fail for the wrong reason

## Fix applied
- marked the draft fixture with `nav: false` in the archive integration test
- kept `archive: false`, `rss: false`, and `sitemap: false` together so the test models a realistic unpublished dated entry
