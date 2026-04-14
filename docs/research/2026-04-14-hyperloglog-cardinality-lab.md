# HyperLogLog cardinality lab research

## Why this project
The existing portfolio set already covered Bloom filters, B-trees, LSM trees, cache simulation, hashing, and distributed clocks. A HyperLogLog project adds another high-signal probabilistic/data-infrastructure concept that is common in analytics and distributed systems interviews.

## Key notes
- HyperLogLog estimates distinct counts using many small registers instead of storing all unique values.
- The standard raw estimate is `alpha_m * m^2 / sum(2^-M[i])`, where `m = 2^p` registers.
- For small cardinalities, linear counting (`m * log(m / V)`) improves accuracy when there are still empty registers.
- Merge works by taking the register-wise maximum, which makes the structure attractive for sharded analytics pipelines.

## References
- Flajolet et al., *HyperLogLog: the analysis of a near-optimal cardinality estimation algorithm*
- engineering summaries covering `alpha_m`, small-range correction, and merge behavior
