#!/usr/bin/env python3
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "projects/interval-tree-lab/README.md"

COMMANDS = [
    "python3 projects/interval-tree-lab/interval_tree_lab.py demo",
    "python3 projects/interval-tree-lab/interval_tree_lab.py build 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics",
    "python3 projects/interval-tree-lab/interval_tree_lab.py overlap 7-18 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics 17-19:alerts",
    "python3 projects/interval-tree-lab/interval_tree_lab.py point 26 15-23:analytics 19-20:maintenance 25-30:etl 26-26:ping",
    "python3 projects/interval-tree-lab/interval_tree_lab.py insert 8-12:patch 0-3:warmup 5-8:backup 15-23:analytics",
    "python3 projects/interval-tree-lab/interval_tree_lab.py delete 8-12:patch 0-3:warmup 5-8:backup 8-12:patch 15-23:analytics",
    "python3 projects/interval-tree-lab/interval_tree_lab.py benchmark --intervals 800 --queries 400 --seed 11",
    "python3 projects/interval-tree-lab/interval_tree_lab.py benchmark-series --interval-counts 100,250,500,1000 --queries 250 --output-json artifacts/interval-tree-benchmark-series.json --output-csv artifacts/interval-tree-benchmark-series.csv",
    "python3 projects/interval-tree-lab/interval_tree_lab.py trace 7-18 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics 17-19:alerts",
    "python3 projects/interval-tree-lab/interval_tree_lab.py trace 7-18 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics 17-19:alerts --output docs/artifacts/interval-tree-trace.dot --format dot",
    "python3 projects/interval-tree-lab/interval_tree_lab.py explain 7-18 0-3:warmup 5-8:backup 6-10:deploy 15-23:analytics 17-19:alerts",
]

ARTIFACT_PATHS = [
    REPO_ROOT / "artifacts/interval-tree-benchmark-series.json",
    REPO_ROOT / "artifacts/interval-tree-benchmark-series.csv",
    REPO_ROOT / "docs/artifacts/interval-tree-trace.dot",
]


def _snapshot_artifacts() -> dict[Path, bytes | None]:
    snapshot: dict[Path, bytes | None] = {}
    for path in ARTIFACT_PATHS:
        snapshot[path] = path.read_bytes() if path.exists() else None
    return snapshot


def _restore_artifacts(snapshot: dict[Path, bytes | None]) -> None:
    for path, previous in snapshot.items():
        if previous is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(previous)


def main() -> int:
    failures: list[str] = []
    readme_text = README_PATH.read_text(encoding="utf-8")
    for command in COMMANDS:
        if command not in readme_text:
            failures.append(f"README is missing documented command: {command}")
            continue
        snapshot = _snapshot_artifacts()
        try:
            completed = subprocess.run(
                shlex.split(command),
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            _restore_artifacts(snapshot)
        if completed.returncode != 0:
            failures.append(
                f"Command failed ({completed.returncode}): {command}\nSTDERR: {completed.stderr.strip()}\nSTDOUT: {completed.stdout.strip()}"
            )
    if failures:
        sys.stderr.write("\n\n".join(failures) + "\n")
        return 1
    print(f"README command audit passed for {len(COMMANDS)} commands: {README_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
