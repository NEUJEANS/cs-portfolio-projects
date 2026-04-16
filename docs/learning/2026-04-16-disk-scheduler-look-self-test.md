# Disk Scheduler LOOK / C-LOOK Self-Test

## Hand-check scenario
- start: `50`
- max cylinder: `199`
- direction: `up`
- requests: `82 170 43 140 24 16 190`

## Expected reasoning
- LOOK order: service higher requests first, then reverse at `190` instead of sweeping to `199`.
- C-LOOK order: service higher requests first, then jump directly to `16` instead of going through `199 -> 0`.

## Expected totals
- LOOK path: `50 -> 82 -> 140 -> 170 -> 190 -> 43 -> 24 -> 16`
- LOOK total movement: `314`
- C-LOOK path: `50 -> 82 -> 140 -> 170 -> 190 -> 16 -> 24 -> 43`
- C-LOOK total movement: `341`

## Result
Implementation/tests should reproduce the same path and totals exactly.
