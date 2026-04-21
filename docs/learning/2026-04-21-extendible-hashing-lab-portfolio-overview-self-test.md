# Learning / self-test — extendible-hashing-lab portfolio overview

## Quick refresh before coding
1. What should a recruiter-facing artifact page optimize for?
   - fast orientation first, deep links second, minimal scrolling before the main visual story is clear.
2. What should stay deterministic for this repo?
   - the overview HTML structure, relative artifact links, and the generated PNG screenshot from headless Chrome.
3. What is the biggest failure mode for generated portfolio pages?
   - they become too tall/noisy, or they accidentally embed machine-specific paths that break portability.

## Notes after implementation
- fixed-height preview frames work better than full-height screenshots inside the overview cards because they keep the overall PNG readable.
- the reproduce-command section should target the committed artifact paths, not the caller-specific temp output path, otherwise repeated exports drift and the page stops being portable.
- overview PNG capture needs a tighter height clamp than the raw DOM height probe, otherwise Chrome captures a lot of blank whitespace below the last section.
