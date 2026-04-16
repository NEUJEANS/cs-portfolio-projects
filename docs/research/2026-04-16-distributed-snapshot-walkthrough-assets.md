# 2026-04-16 distributed snapshot walkthrough assets research

## Goal
Finish the weakest remaining distributed-snapshot slice by making the partition/heal scenario easy to show in GitHub, a blog post, or an interview.

## Why this is the right next slice
- The lab already has JSON output, Mermaid snapshot diagrams, concurrent snapshots, and link-partition modeling.
- The remaining weakness is presentation: there is no committed artifact that tells a clean before/partition/heal/after story.
- A generated Markdown walkthrough is stronger than a one-off hand-written note because it stays reproducible from the simulator output.

## Asset requirements
- derive the walkthrough directly from the existing scripted scenario result so it stays deterministic and resumable
- keep the student-facing story compact: timeline, snapshot summaries, down-link state, and recorded in-flight messages
- embed Mermaid blocks instead of screenshots so GitHub can render the diagrams directly and the artifact can still be diffed in git
- support writing straight to a file so the project can ship a ready-made case-study artifact under `docs/artifacts/`

## Chosen implementation direction
- add a `walkthrough` CLI command beside `script`
- reuse the existing script runner and snapshot Mermaid renderer instead of inventing a second model
- generate one Markdown section per snapshot, including balances, statuses, down links, and recorded channel messages
