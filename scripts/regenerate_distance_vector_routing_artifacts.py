from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = REPO_ROOT / "projects" / "distance-vector-routing-lab"
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "distance-vector-routing-lab"

sys.path.insert(0, str(PROJECT_DIR))

from distance_vector_routing import (  # noqa: E402
    FAILURE_SCENARIOS,
    benchmark_failure_modes,
    benchmark_failure_suite,
    render_failure_benchmark,
    render_failure_benchmark_suite,
)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    line = FAILURE_SCENARIOS["count-to-infinity-line"]
    benchmark = benchmark_failure_modes(
        line.topology,
        line.remove_link[0],
        line.remove_link[1],
        router=line.router,
        destination=line.destination,
        max_rounds=20,
    )
    (ARTIFACT_DIR / "failure-benchmark.json").write_text(
        render_failure_benchmark(benchmark, output_format="json") + "\n",
        encoding="utf-8",
    )
    (ARTIFACT_DIR / "failure-benchmark.csv").write_text(
        render_failure_benchmark(benchmark, output_format="csv") + "\n",
        encoding="utf-8",
    )
    (ARTIFACT_DIR / "failure-benchmark.md").write_text(
        render_failure_benchmark(benchmark, output_format="markdown") + "\n",
        encoding="utf-8",
    )

    suite = benchmark_failure_suite()
    (ARTIFACT_DIR / "failure-suite.json").write_text(
        render_failure_benchmark_suite(suite, output_format="json") + "\n",
        encoding="utf-8",
    )
    (ARTIFACT_DIR / "failure-suite.csv").write_text(
        render_failure_benchmark_suite(suite, output_format="csv") + "\n",
        encoding="utf-8",
    )
    (ARTIFACT_DIR / "failure-suite.md").write_text(
        render_failure_benchmark_suite(suite, output_format="markdown") + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
