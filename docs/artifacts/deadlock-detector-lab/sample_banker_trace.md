# Banker's algorithm safety trace

- Source: `projects/deadlock-detector-lab/sample_banker_state.json`
- Safe: yes
- Safe sequence: `P1, P3, P4, P0, P2`
- Final work: `A=10, B=5, C=7`

## Safety trace steps

| Step | Chosen process | Runnable set | Work before | Remaining need | Allocation released | Work after |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `P1` | `P1, P3` | `A=3, B=3, C=2` | `A=1, B=2, C=2` | `A=2, B=0, C=0` | `A=5, B=3, C=2` |
| 2 | `P3` | `P3, P4` | `A=5, B=3, C=2` | `A=0, B=1, C=1` | `A=2, B=1, C=1` | `A=7, B=4, C=3` |
| 3 | `P4` | `P0, P2, P4` | `A=7, B=4, C=3` | `A=4, B=3, C=1` | `A=0, B=0, C=2` | `A=7, B=4, C=5` |
| 4 | `P0` | `P0, P2` | `A=7, B=4, C=5` | `A=7, B=4, C=3` | `A=0, B=1, C=0` | `A=7, B=5, C=5` |
| 5 | `P2` | `P2` | `A=7, B=5, C=5` | `A=6, B=0, C=0` | `A=3, B=0, C=2` | `A=10, B=5, C=7` |
