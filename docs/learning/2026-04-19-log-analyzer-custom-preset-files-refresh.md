# log-analyzer refresh — custom annotation preset files

## Why this slice
The current log-analyzer card exports already support manual annotations and built-in three-step stories, but repeated portfolio/demo runs still require hard-coded labels unless each command is edited by hand. A JSON-backed preset file keeps the CLI ergonomic while letting a student tailor stories to a specific service or incident.

## Short refresh / self-test plan
- stay inside the Python standard library (`json`, `pathlib`, existing argparse flow)
- keep the preset expansion path narrow: load custom definitions, merge with built-ins, then reuse the existing annotation normalization/rendering logic
- validate early and clearly: JSON parse errors, duplicate preset names, unsupported themes, blank labels, and oversized step lists
- prove both unit-level and CLI-level success paths with a real committed artifact regeneration

## Expected artifact shape
```json
{
  "presets": {
    "release-watch": [
      {"theme": "deploy", "label": "Canary deploy started"},
      {"theme": "incident", "label": "Error budget burn noticed"},
      {"theme": "recovery", "label": "Traffic stabilized"}
    ]
  }
}
```

## Guardrails
- normalize names to lowercase dash-case for predictable CLI lookup
- do not let custom files shadow built-in preset names silently
- cap each preset at 4 steps because the current card renderer supports at most 4 distinct markers per export
