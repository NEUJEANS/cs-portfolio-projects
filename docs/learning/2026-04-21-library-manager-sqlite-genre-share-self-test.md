# library-manager-sqlite genre share self-test

Date: 2026-04-21

## Quick refresh
- A normalized stacked bar chart is a composition view, not an absolute-load view. It should be paired with the daily total so the denominator stays visible.
- Keeping `genre-share` as a separate command is safer than stretching the heatmap or trend CSV into multiple incompatible roles.
- Tied-share days should not invent a dominant genre, because that turns a visual tie into misleading summary data.

## Self-test
1. Why not reuse the heatmap alone for genre composition?
   - Because the heatmap is anchored on absolute counts. It is great for intensity, but it does not make the relative subject mix as legible as a normalized stacked view.
2. Why include `share_start` and `share_end` in the CSV?
   - Because they make the stacked geometry reconstructable downstream without requiring consumers to recalculate cumulative positions.
3. Why keep count labels above the normalized bars?
   - Because a 100% stack hides the daily denominator. The labels preserve the total active-loan context so the composition chart does not flatten high-load and low-load days into the same story.
