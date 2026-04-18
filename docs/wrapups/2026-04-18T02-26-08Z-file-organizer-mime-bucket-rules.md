# File organizer MIME-aware bucket rules slice

- **Timestamp:** 2026-04-18T02:26:08Z
- **Feature commit:** `bcaed07ec9bc15ba465313b43ca2bc55c34971b4` (`feat(file-organizer-cli): add MIME-aware bucket rules`)
- **What changed:**
  - added MIME-aware custom bucket rules via `mimeTypes` and `mimePrefixes`, with shared-config normalization, overlap detection, and canonical JSON writing support alongside the existing extension and basename-pattern rules
  - taught organize runs to sniff up to the first 4096 bytes for common binary/text signatures (PNG/JPEG/GIF/WEBP/PDF/ZIP/gzip/7z/RAR/FLAC/OGG/WAV/MP3 plus JSON/HTML/XML/SVG/plain text) so misleading filenames like `report.txt` can still route into the right bucket
  - recorded MIME matches in organize reports/manifests, refreshed the README/checklists, and added regression coverage for MIME config linting, file classification, organize behavior, and text-report annotations
  - review follow-up fixes in this pass kept the README config example on canonical `image/` prefix form and added an explicit report-format assertion for MIME annotation output
- **Tests / reviews run:**
  - safe-sync check before edit: verified local `main` tracked `origin/main`, fetched `origin`, and confirmed ahead/behind `0/0` before resuming work
  - project tests: `npm test --prefix projects/file-organizer-cli` (`40/40` passing)
  - review pass 1: preview-normalized-config smoke with a temp MIME config verified normalization warnings for `Application/JSON` and `image/*` plus the canonical rewrite summary
  - review pass 2: dry-run organize smoke on temp misleading-extension files verified MIME-prefix/type routing and human-readable text-report annotations for SVG/JSON samples
  - review pass 3: real organize + manifest + undo smoke restored the temp folder cleanly, then a docs/test audit fixed the non-canonical README `mimePrefixes` example and added a report-format regression assertion for MIME annotations
- **Next step:** add a small publishable demo artifact set that shows before/after folder trees and config preview output for the README and portfolio screenshots.
