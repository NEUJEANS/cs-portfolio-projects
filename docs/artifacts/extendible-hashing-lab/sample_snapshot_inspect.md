# Extendible hashing snapshot

## Summary
- bucket capacity: `2`
- global depth: `3`
- directory slots: `8`
- bucket count: `4`
- entry count: `4`
- load factor: `0.5`

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

