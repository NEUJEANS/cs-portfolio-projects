# 2026-04-16 log-analyzer combined-log + latency refresh

Refresh points:
- Common Log Format stops after status code and response bytes; combined format adds quoted referrer and user-agent fields.
- A practical parser should treat referrer/user-agent as optional so older logs still parse unchanged.
- Request-time fields vary by stack, but decimal values are commonly seconds while integer `%D`-style values are commonly microseconds.
- Converting latency to milliseconds at parse time keeps percentile and text-report code simple.

Self-test:
1. Why not require referrer and user-agent on every parsed line?
   Because mixed or older logs would become invalid even though the common-prefix fields are still useful.
2. Why normalize integer and decimal latency tokens into one unit?
   So JSON output, percentiles, and README examples use one comparable scale instead of exposing format-specific timing units.
3. Why keep latency summary optional instead of always emitting zeros?
   Because missing timing fields mean “not logged,” which is different from “logged as 0 ms.”
