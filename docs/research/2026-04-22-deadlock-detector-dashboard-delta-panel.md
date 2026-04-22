# deadlock-detector-lab dashboard delta panel notes

## Why this slice
The main dashboard already showed one granted Banker's request trace, but the new request-gallery delta callout still lived on a separate page. The dashboard needs one compact comparison block so a recruiter can see, in one pass, why the safe request still works and why the unsafe request loses its first runnable option.

## Scope decision
- skip external web research because this slice extends the existing dashboard and Banker's gallery output directly
- keep the dashboard focused on one primary request plus one contrast request instead of embedding a full multi-card gallery
- reuse the existing delta-callout builder so JSON, Markdown, HTML, and tests all tell the same story

## Implementation notes
- add an optional `--banker-contrast-input` to the dashboard command instead of creating a second dashboard mode
- surface the delta callout as structured dashboard JSON so downstream renderers can reuse it
- keep the new dashboard section compact: shared slack spent, extra slack differences, first runnable-set change, lost runnable options, and denied blocking
