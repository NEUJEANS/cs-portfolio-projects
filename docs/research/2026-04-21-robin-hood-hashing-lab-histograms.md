# robin-hood-hashing-lab histogram slice research notes

## Brief reference refresh
- Code Capsule's Robin Hood hashing write-up highlights the main interview-friendly claim: Robin Hood hashing aims to keep probe sequence length / distance variance small and comparatively stable even as load rises.
- The backward-shift deletion follow-up emphasizes that deletions should shift later entries backward until an empty slot or distance-0 entry appears, which keeps mean and variance from drifting upward the way tombstones do.
- For this slice, the useful portfolio implication is that averages alone hide the real story. A student should be able to point at the distribution of probe distances and show where the long tail shrinks relative to linear probing.

## Design choice for this slice
- keep the implementation standard-library-only and deterministic
- record per-run probe-distance histograms inside benchmark outputs so CSV/JSON stay machine-readable
- aggregate those histograms into Markdown and self-contained HTML reports to make the variance story screenshot-friendly
- prefer static tables plus proportional bars over JS chart libraries so the artifacts remain commit-friendly and robust on GitHub

## References
- https://codecapsule.com/2013/11/11/robin-hood-hashing/
- https://codecapsule.com/2013/11/17/robin-hood-hashing-backward-shift-deletion/
