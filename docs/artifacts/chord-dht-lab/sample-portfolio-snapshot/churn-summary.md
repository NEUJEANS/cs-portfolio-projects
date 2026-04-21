# Chord churn summary

- Events processed: `3`
- Default rounds per event: `3`
- Finger repair mode: `all`
- Finger repair seed: `none`
- Starting nodes: `alpha`, `charlie`, `delta`, `echo`, `bravo`
- Ending nodes: `foxtrot`, `alpha`, `charlie`, `delta`, `echo`, `bravo`
- Fully stabilized steps: `3`
- Partially stabilized steps: `0`
- Max stabilized round: `1`
- Average stabilized round: `0.667`
- Final node count: `6`

| Step | Action | Node | Rounds | Stabilized round | Final finger progress | Final successor matches | Final predecessor matches |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `join` | `foxtrot` | 4 | 1 | 100.00% | 6/6 | 6/6 |
| 2 | `fail` | `charlie` | 3 | 0 | 100.00% | 5/5 | 5/5 |
| 3 | `recover` | `charlie` | 3 | 1 | 100.00% | 6/6 | 6/6 |
