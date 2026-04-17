# branch-predictor-lab review pass 11

## Focus
Narrative accuracy in the generated Markdown/SVG talking points.

## Issue found
The first comparison-card draft always phrased the `two-bit` vs `one-bit` delta as if two-bit had won, which produced nonsense like a negative "better" delta on the tournament-style synthetic trace. It also picked the "best advanced predictor" using a tie-breaking rule that could disagree with the ranked table order.

## Fix applied
- made the talking-point generator switch wording depending on which predictor actually wins the head-to-head
- changed the advanced/simple baseline callouts to follow the existing ranked `results` order so the summary lines stay aligned with the visible ranking table
- regenerated the committed Markdown and SVG cards after the wording fix

## Result
The artifact commentary now matches the actual numbers in both the sample trace and the tournament-style synthetic trace.
