# deadlock-detector-lab Banker visuals notes

## Why this slice
The deadlock-detector lab already had strong wait-for and allocation diagrams, but the avoidance side still read like a text-only appendix. The next weak spot was giving Banker's safety and request traces the same screenshot-friendly visual weight.

## Scope decision
- skip external web research for this slice
- reuse the existing deterministic export flow instead of inventing a second rendering pipeline
- keep the visuals static, self-contained, and easy to commit under `docs/artifacts/`

## Visual goals
- make the safety state answer obvious in one glance: safe or unsafe, safe sequence, final work, unfinished processes
- make the request trial answer obvious in one glance: granted or denied, why, and what work vector was evaluated
- show the same per-step work evolution that the Markdown traces already expose so the visuals stay faithful to the JSON output
- thread the Banker visuals into the combined dashboard HTML so detection and avoidance both have diagram-first storytelling
