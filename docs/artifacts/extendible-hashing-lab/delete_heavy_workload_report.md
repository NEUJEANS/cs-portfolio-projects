# Extendible hashing delete-heavy merge/shrink report

## Summary
- bucket capacity: `2`
- global depth: `0`
- directory slots: `1`
- bucket count: `1`
- entry count: `2`
- load factor: `1.0`

## Workload trace
| step | op | key | value | outcome | global depth | bucket count | entry count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | put | `collision:2:0:1` | `zero-a` | inserted | 0 | 1 | 1 |
| 2 | put | `collision:2:1:3` | `one` | inserted | 0 | 1 | 2 |
| 3 | put | `collision:2:0:5` | `zero-b` | inserted | 1 | 2 | 3 |
| 4 | put | `collision:2:2:1` | `two` | inserted | 2 | 3 | 4 |
| 5 | delete | `collision:2:2:1` | `` | deleted | 1 | 2 | 3 |
| 6 | delete | `collision:2:1:3` | `` | deleted | 0 | 1 | 2 |

## Directory
| index | bits | bucket | local depth | entries |
| --- | --- | --- | --- | --- |
| 0 | `0` | 0 | 0 | collision:2:0:1=zero-a<br>collision:2:0:5=zero-b |

