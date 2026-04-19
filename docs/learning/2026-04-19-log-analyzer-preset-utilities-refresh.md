# log-analyzer refresh — preset utilities

## Why this slice
The previous custom-preset-file slice made reusable card stories possible, but inspecting those presets still required opening JSON or mentally expanding timestamps on the CLI. A small utility mode keeps the main export path untouched while making README/demo workflows easier to understand and safer to rerun.

## Short refresh / self-test plan
- stay inside the existing Python standard-library path (`argparse`, `json`, reusable preset normalization helpers)
- treat list/preview as utility modes that can exit before logfile parsing so they remain fast and no-logfile friendly
- keep one source of truth for preset definitions, then derive both export expansion and utility output from that shared catalog
- prove success with unit coverage, CLI smoke commands, and committed sample catalog/preview artifacts

## Guardrails
- keep built-in and custom preset names normalized and collision-checked in one place
- preserve existing card export behavior when a logfile is present
- make the no-logfile helper output work in both text and JSON formats so docs and scripts can reuse it
