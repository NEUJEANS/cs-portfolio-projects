# library-manager-sqlite genre share review log

Date: 2026-04-21

## Review pass 1, dominance-summary correctness
- Inspected the first snapshot logic and realized tied-share days were being assigned an arbitrary dominant genre based on ordering.
- Problem: that inflated `dominant_days` and `dominant_switches`, which made the summary stronger-sounding than the actual chart.
- Fix: only mark a day as dominant when exactly one genre owns the highest share for that day.

## Review pass 2, wording after the tie fix
- Re-read the SVG notes and table labels after fixing tie handling.
- Problem: the copy still implied every active day had a winner.
- Fix: updated the note text to say tied days do not force a winner, and renamed the summary column from `Dominant days` to `Lead days` so the wording matches the data better.

## Review pass 3, validation and determinism
- Re-ran `py_compile`, the full unittest suite, and a real CLI smoke that generated `sample_genre_share.csv` and `sample_genre_share.svg` twice from a seeded temporary database.
- Verified the repeated exports matched byte-for-byte for both files.
- Confirmed `git diff --check` stayed clean after the fixes.
