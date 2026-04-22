# Deadlock detector Banker request delta self-test

## Quick refresh
- A granted Banker request spends some immediate slack and still leaves at least one runnable process, which allows a safe sequence to begin.
- A denied request may still fit current availability, but it fails because the trial state removes all runnable options.
- The cleanest delta story is: what slack got consumed, what first runnable options remained, and which of those options disappeared.

## Self-test
1. **What should a compact granted-vs-denied delta callout mention first?**
   - shared slack that both paths spend
   - any extra slack that only one path spends
   - the first runnable-set difference

2. **Why reconstruct the pre-request available vector for granted requests?**
   - because the successful request path stores the post-request trial availability, so reconstructing the starting slack keeps the comparison honest

3. **What is the most important disappearing option in the sample gallery?**
   - the granted sample still leaves `P1` runnable immediately, while the denied sample leaves no runnable process
