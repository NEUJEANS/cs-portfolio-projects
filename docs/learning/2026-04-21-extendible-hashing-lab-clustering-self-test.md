# extendible-hashing-lab clustering-preset self-test — 2026-04-21

## Quick refresh
- primary clustering in linear probing means contiguous occupied runs keep getting longer, so successful and unsuccessful lookups both pay with more probes
- tombstones preserve correctness for later lookups, but they also keep miss paths expensive until a rebuild clears them out
- a good benchmark preset should be deterministic and legible: a short scripted key stream beats a huge opaque random workload
- for this repo, the committed artifact bundle has to make the story visible in JSON, Markdown, HTML, and CSV without extra explanation

## Self-test
1. **Q:** Why add a focused scenario instead of just increasing the number of existing benchmark operations?
   **A:** A focused scenario isolates the linear-probing failure mode, so higher probe counts and cleanup rebuilds are attributable to clustering rather than to generic suite growth.
2. **Q:** What signals should spike if the preset is doing its job?
   **A:** Linear average probe count, linear max probe count, and at least one rebuild triggered by tombstone pressure.
3. **Q:** Why keep the scenario deterministic across trials?
   **A:** The committed artifacts need to stay reproducible and resumable, so repeated exports and recruiter demos show the same story every time.
