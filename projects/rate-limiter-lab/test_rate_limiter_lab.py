import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rate_limiter_lab import (
    FixedWindowLimiter,
    SlidingLogLimiter,
    TokenBucketLimiter,
    parse_events,
    simulate,
    summarize,
)


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = PROJECT_DIR / "rate_limiter_lab.py"


class RateLimiterLabTests(unittest.TestCase):
    def test_fixed_window_boundary_burst_behavior(self):
        decisions = simulate(FixedWindowLimiter(limit=2, window_seconds=10), [0, 1, 9.9, 10.0, 10.1])
        self.assertEqual([item.allowed for item in decisions], [True, True, False, True, True])

    def test_sliding_log_prunes_old_events_precisely(self):
        decisions = simulate(SlidingLogLimiter(limit=2, window_seconds=10), [0, 1, 9.9, 10.1])
        self.assertEqual([item.allowed for item in decisions], [True, True, False, True])

    def test_token_bucket_refill_allows_later_request(self):
        limiter = TokenBucketLimiter(rate_per_second=1.0, capacity=2.0)
        decisions = simulate(limiter, [0.0, 0.0, 0.0, 1.0])
        self.assertEqual([item.allowed for item in decisions], [True, True, False, True])

    def test_parse_events_merges_inline_and_file_inputs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            events_file = Path(tmpdir) / "events.json"
            events_file.write_text(json.dumps([3, 1]))
            self.assertEqual(parse_events(["2"], str(events_file)), [1.0, 2.0, 3.0])

    def test_summary_counts_allowed_and_denied(self):
        decisions = simulate(FixedWindowLimiter(limit=1, window_seconds=5), [0, 1])
        self.assertEqual(summarize(decisions), {"total": 2, "allowed": 1, "denied": 1})

    def test_cli_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            events_path = Path(tmpdir) / "events.json"
            events_path.write_text(json.dumps([0, 0, 0, 1]))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "token-bucket",
                    "--rate",
                    "1",
                    "--capacity",
                    "2",
                    "--events-file",
                    str(events_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=PROJECT_DIR,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["summary"], {"total": 4, "allowed": 3, "denied": 1})
        self.assertIs(payload["decisions"][2]["allowed"], False)


if __name__ == "__main__":
    unittest.main()
