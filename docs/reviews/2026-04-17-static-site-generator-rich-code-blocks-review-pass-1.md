# Static-site-generator rich code blocks review - pass 1

## Focus
README and author-facing docs accuracy for the new fenced code-block metadata.

## Issue found
- The first README draft showed `title=` in the example but did not mention that the renderer also accepts the `file=` and `filename=` aliases added in code, which could leave authors guessing about the supported fence syntax.

## Fix applied
- Added an explicit README note that `title=`, `file=`, and `filename=` are all accepted in the fence info string.

## Result
- The documented authoring workflow now matches the implemented parser behavior.
