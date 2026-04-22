# deadlock-detector-lab Banker visuals review log

## Pass 1, export-shape audit
- checked the new Banker SVG/HTML exports against the existing Markdown and JSON traces
- found issue: the request view still felt like a bare decision card and did not restate the actual question inside the visual itself
- fix: added explicit `Question answered` context to the request takeaway panel so the visual stands on its own

## Pass 2, markup cleanliness audit
- reviewed the generated SVG structure for unnecessary noise that would make the committed artifacts harder to diff and reason about
- found issue: spacer rows were emitted as empty `<text>` nodes inside the SVG output
- fix: changed multiline SVG rendering to preserve spacing without outputting empty text elements

## Pass 3, decision-label audit
- reviewed denied-request and pre-trial paths for clarity about which available vector the visual is showing
- found issue: the request metric always said `Evaluated available`, even when the request was rejected before any trial allocation existed
- fix: switched the label to `Trial available` when a trial state exists and `Current available` otherwise
