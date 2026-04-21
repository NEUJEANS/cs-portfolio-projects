# Extendible hashing workload report

## Summary
- bucket capacity: `2`
- global depth: `3`
- directory slots: `8`
- bucket count: `4`
- entry count: `4`
- load factor: `0.5`

## Workload trace
| step | op | key | value | outcome | events | global depth | bucket count | entry count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | put | `user:1001` | `Ada` | inserted | steady-state | 0 | 1 | 1 |
| 2 | put | `user:1009` | `Grace` | inserted | steady-state | 0 | 1 | 2 |
| 3 | put | `user:1017` | `Linus` | inserted | 1 split, 1 directory growth | 1 | 2 | 3 |
| 4 | put | `user:1025` | `Barbara` | inserted | 1 split, 1 directory growth | 2 | 3 | 4 |
| 5 | get | `user:1009` | `` | found:Grace | steady-state | 2 | 3 | 4 |
| 6 | delete | `user:1017` | `` | deleted | steady-state | 2 | 3 | 3 |
| 7 | put | `user:1041` | `Margaret` | inserted | 1 split, 1 directory growth | 3 | 4 | 4 |

## Directory
| index | bits | bucket | local depth | entries |
| --- | --- | --- | --- | --- |
| 0 | `000` | 0 | 2 | user:1025=Barbara |
| 1 | `001` | 1 | 1 | _empty_ |
| 2 | `010` | 2 | 3 | user:1041=Margaret |
| 3 | `011` | 1 | 1 | _empty_ |
| 4 | `100` | 0 | 2 | user:1025=Barbara |
| 5 | `101` | 1 | 1 | _empty_ |
| 6 | `110` | 3 | 3 | user:1001=Ada<br>user:1009=Grace |
| 7 | `111` | 1 | 1 | _empty_ |

