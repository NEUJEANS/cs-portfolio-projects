# Review log — extendible-hashing-lab portfolio overview

## Pass 1 — portability / reproducibility
Issue found:
- the overview HTML's "Reproduce the committed bundle" command used absolute machine-specific paths derived from the current output target.

Fix:
- preserved repo-relative display paths for the command snippet and pointed the overview reproduction command at the committed `portfolio_overview.{html,png}` paths under the artifact directory.
- added a regression test to keep relative-path output portable.

## Pass 2 — visual density
Issue found:
- embedding the full-height trace PNGs inside each card made the overview screenshot too tall and shrank the text into something recruiters would skim past.

Fix:
- constrained the main preview frames to fixed heights with top-anchored cropping and gave the thumbnail-strip previews their own smaller fixed-height slot.
- also tightened the benchmark dashboard preview to a compact top-cropped panel.

## Pass 3 — screenshot polish
Issue found:
- the auto-captured overview PNG still had too much blank whitespace at the bottom because the DOM-height probe overshot the useful content height.

Fix:
- reduced the overview height heuristic and clamped the measured height so the PNG capture stays close to the real content height without cutting the final section.
- reran the committed overview export and deterministic rerender check after the sizing change.
