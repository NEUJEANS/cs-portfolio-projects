# Review pass 1 — file-organizer demo artifacts — 2026-04-18

## Focus
Artifact inventory and README/demo-link consistency.

## Findings
1. **Docs drift:** the generated bundle already included `demo-normalized-write.txt` and `demo-manifest.json`, but the summary page and README link list did not mention them.

## Fixes made
- updated `generate_demo_artifacts.js` so `demo-summary.md` lists the normalized-write report and sanitized manifest payload
- updated `projects/file-organizer-cli/README.md` so the published bundle links cover the normalized config, apply report, and manifest payload as well
- regenerated the demo bundle after the doc-link fix

## Verification
- `npm run demo:artifacts --prefix projects/file-organizer-cli`
