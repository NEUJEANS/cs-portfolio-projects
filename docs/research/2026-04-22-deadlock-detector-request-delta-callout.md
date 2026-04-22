# deadlock-detector-lab request delta-callout notes

## Why this slice
The request gallery already showed granted versus denied trials side by side, but the comparison still made readers mentally diff the two cards to understand what changed. A compact delta callout is the missing recruiter-friendly explanation layer.

## Scope decision
- skip external web research because this slice extends the existing Banker request gallery directly
- keep the comparison anchored on immediate post-request slack and the first runnable set because those are the fastest signals for why one path stays safe and the other does not
- expose the same delta story in JSON, Markdown, and HTML so committed artifacts and tests stay aligned

## Implementation notes
- derive consumed slack by reconstructing the pre-request available vector for granted requests, then comparing it with the evaluated post-request vector
- compare each denied request against the best matching granted request in the gallery so larger galleries still get one compact callout per denied path
- surface the exact runnable options lost when the denied path removes the first runnable set
