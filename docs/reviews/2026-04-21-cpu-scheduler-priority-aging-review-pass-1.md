# Review pass 1 - cpu-scheduler priority aging slice

## Focus
Code-path audit for scheduling semantics, tie-breaking, and backward compatibility.

## Checks
- verified priority scheduling stays non-preemptive, matching the implementation slice and the refresher note
- verified aging only affects ready jobs at dispatch boundaries via `effective_priority()`
- verified workloads without `priority` still default to `0`

## Issue found
- README feature list said `Priority scheduling`, which could be misread as preemptive priority scheduling.

## Fix applied
- clarified the README feature list to say `non-preemptive Priority scheduling`.

## Result
Pass complete after doc clarification.
