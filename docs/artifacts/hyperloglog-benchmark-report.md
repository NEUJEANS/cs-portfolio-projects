# HyperLogLog benchmark report

- Precisions: 8, 10, 12
- Cardinalities: 200, 2000, 20000
- Trials per combination: 8
- Seed: 7
- Dense register bytes assume one byte per register in this educational implementation.

## Cardinality 200

Lowest observed mean error in this sweep: precision `12` at `4096` dense bytes with mean relative error `0.60%`.

| precision | registers | dense bytes | mean estimate | mean abs error | mean rel error | max rel error | theory bound |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 256 | 256 | 204.34 | 12.05 | 6.02% | 10.27% | 6.50% |
| 10 | 1024 | 1024 | 202.07 | 4.00 | 2.00% | 4.47% | 3.25% |
| 12 | 4096 | 4096 | 200.58 | 1.21 | 0.60% | 1.47% | 1.62% |

## Cardinality 2000

Lowest observed mean error in this sweep: precision `12` at `4096` dense bytes with mean relative error `0.89%`.

| precision | registers | dense bytes | mean estimate | mean abs error | mean rel error | max rel error | theory bound |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 256 | 256 | 2024.06 | 88.38 | 4.42% | 13.57% | 6.50% |
| 10 | 1024 | 1024 | 2010.38 | 56.13 | 2.81% | 6.47% | 3.25% |
| 12 | 4096 | 4096 | 2013.51 | 17.88 | 0.89% | 1.52% | 1.62% |

## Cardinality 20000

Lowest observed mean error in this sweep: precision `12` at `4096` dense bytes with mean relative error `1.12%`.

| precision | registers | dense bytes | mean estimate | mean abs error | mean rel error | max rel error | theory bound |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 256 | 256 | 19969.53 | 462.66 | 2.31% | 5.42% | 6.50% |
| 10 | 1024 | 1024 | 20137.10 | 363.12 | 1.82% | 4.58% | 3.25% |
| 12 | 4096 | 4096 | 20037.84 | 223.37 | 1.12% | 2.85% | 1.62% |

