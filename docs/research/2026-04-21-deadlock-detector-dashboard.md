# deadlock-detector-lab detection-vs-avoidance dashboard notes

## Why this slice
The project already explains each model separately, but the portfolio story is still fragmented. A recruiter-friendly artifact should show how cycle detection, allocation-progress detection, and Banker's avoidance relate to each other in one glance.

## Design notes
- Wait-for graphs answer, "is there already a cycle among processes?"
- Allocation-progress detection answers, "can any process still finish and release enough resources to unblock the rest?"
- Banker's algorithm answers, "should we grant this request if we want to stay in a safe state?"
- A useful combined report should keep the visuals deterministic and self-contained so the committed artifact is easy to review and regenerate.

## Scope for this slice
- add one combined CLI dashboard command fed by the existing sample inputs
- export both Markdown and HTML so the same story works in git and in a browser
- reuse the existing wait-for and allocation visuals instead of inventing a second visual vocabulary
- include both the Banker's safety trace and one sample request decision so avoidance feels concrete
