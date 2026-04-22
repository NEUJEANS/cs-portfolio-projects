# deadlock-detector-lab request delta-callout review log

## Pass 1, data-model audit
- reviewed the new gallery JSON output for whether the delta story was machine-readable instead of only prose
- found issue: the first implementation compared granted post-request availability against itself, so shared consumed slack incorrectly showed as empty
- fix: reconstructed the pre-request available vector for granted requests before calculating consumed slack

## Pass 2, portfolio-story audit
- reviewed the Markdown gallery artifact for whether the new callout actually answered what changed between the safe and unsafe request paths
- found issue: the callout needed to say which runnable option vanished, not just that the denied path had no runnable process
- fix: added explicit lost runnable options to the delta output and summary sentence

## Pass 3, HTML parity and determinism audit
- reviewed the HTML gallery export against the Markdown version and reran the gallery export twice to confirm the new delta callout section stayed deterministic
- result: HTML and Markdown now both include the same delta story, and repeated regeneration stayed byte-for-byte stable
