# mini-mapreduce-lab benchmark review pass 1

- Scope reviewed: benchmark API shape, deterministic fixture generation, reducer-skew metrics.
- Issue found: benchmark helper wrote to a predictable `/tmp` filename, which could collide across repeated cron runs.
- Fix applied: switched to `tempfile.NamedTemporaryFile(..., delete=False)` and explicit cleanup.
- Result: resumable/background runs are safer and less likely to trample each other.
