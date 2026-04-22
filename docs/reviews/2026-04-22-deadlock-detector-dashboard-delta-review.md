# deadlock-detector-lab dashboard delta review log

## Pass 1, dashboard data-model audit
- reviewed the dashboard JSON shape to make sure the new comparison insight was machine-readable instead of being trapped in prose only
- found issue: the first draft only rendered the delta in the dashboard views and did not expose it as structured dashboard JSON
- fix: added `banker_request_contrast` and `banker_request_delta_callout` to the dashboard model and JSON output

## Pass 2, CLI and portfolio-story audit
- reviewed the new dashboard flow for whether the optional contrast input was safe and whether the delta section stayed compact enough for a recruiter-facing artifact
- found issues:
  - the CLI needed a guardrail so `--banker-contrast-input` could not be used without the primary request input
  - the delta section initially showed full repo paths inside the comparison card, which made the story noisier than it needed to be
- fixes:
  - added a dashboard CLI validation error for contrast-without-primary usage
  - rendered granted and denied request labels with compact basenames inside the dashboard delta section while keeping the full input list above

## Pass 3, parity and determinism audit
- regenerated the dashboard Markdown, HTML, and JSON artifacts twice and compared them byte-for-byte
- result: the new delta section stayed consistent across dashboard JSON, Markdown, and HTML, and repeated regeneration remained deterministic
