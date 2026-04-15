from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CLI = PROJECT_DIR / "union_find_network.py"


def run(*args: str) -> None:
    subprocess.run([sys.executable, str(CLI), *args], check=True, cwd=PROJECT_DIR.parent.parent)


def main() -> int:
    run(
        "--chart-input",
        str(PROJECT_DIR / "sample_benchmark_report.json"),
        "--output-chart",
        str(PROJECT_DIR / "sample_benchmark_report.svg"),
        "--json",
    )
    run(
        "--chart-input",
        str(PROJECT_DIR / "sample_recompute_comparison.json"),
        "--output-chart",
        str(PROJECT_DIR / "sample_recompute_comparison.svg"),
        "--output-markdown",
        str(PROJECT_DIR / "sample_recompute_summary.md"),
        "--json",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
