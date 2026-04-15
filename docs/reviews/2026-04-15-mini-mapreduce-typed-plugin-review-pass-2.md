# Review pass 2 — mini-mapreduce typed plugin outputs

- Rechecked reducer bucket stats after allowing non-integer plugin outputs.
- Found issue: reducer `records` started counting only merged partial objects, which broke existing wordcount expectations and weakened skew metrics for numeric jobs.
- Fix: keep numeric buckets summing numeric partial values while falling back to merged-value counts for structured plugin states.
