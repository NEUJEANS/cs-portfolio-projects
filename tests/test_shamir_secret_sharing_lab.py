from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "projects" / "shamir-secret-sharing-lab" / "shamir_secret_sharing_lab.py"

spec = importlib.util.spec_from_file_location("shamir_secret_sharing_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

Share = module.Share
lagrange_interpolate_at_zero = module.lagrange_interpolate_at_zero
load_shares = module.load_shares
recover_secret = module.recover_secret
save_shares = module.save_shares
split_secret = module.split_secret


class ShamirSecretSharingLabRepoTests(unittest.TestCase):
    def test_split_and_recover_round_trip(self) -> None:
        secret = "launch codes stay local 🔐".encode("utf-8")
        shares = split_secret(secret, threshold=3, total_shares=5)
        recovered = recover_secret([shares[0], shares[2], shares[4]], threshold=3)
        self.assertEqual(recovered, secret)

    def test_lagrange_interpolation_recovers_constant_term(self) -> None:
        secret_byte = 123
        y1 = (secret_byte + 50 * 1) % 257
        y2 = (secret_byte + 50 * 2) % 257
        recovered = lagrange_interpolate_at_zero([(1, y1), (2, y2)])
        self.assertEqual(recovered, secret_byte)

    def test_recover_rejects_mismatched_share_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "same payload length"):
            recover_secret([Share(1, [1, 2]), Share(2, [3])], threshold=2)

    def test_share_bundle_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "shares.json"
            shares = split_secret(b"portfolio", threshold=2, total_shares=3)
            save_shares(output, threshold=2, shares=shares)
            threshold, encoding, loaded = load_shares(output)
            self.assertEqual(threshold, 2)
            self.assertEqual(encoding, "utf-8")
            self.assertEqual([share.x for share in loaded], [1, 2, 3])
            self.assertEqual(recover_secret(loaded[:2], threshold=2), b"portfolio")

    def test_cli_split_inspect_and_recover(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "shares.json"
            split_result = subprocess.run(
                [sys.executable, str(MODULE_PATH), "split", "--secret", "distributed trust", "--threshold", "3", "--shares", "5", "--output", str(output)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(split_result.stdout)["share_count"], 5)

            inspect_result = subprocess.run(
                [sys.executable, str(MODULE_PATH), "inspect", "--input", str(output)],
                capture_output=True,
                text=True,
                check=True,
            )
            inspected = json.loads(inspect_result.stdout)
            self.assertEqual(inspected["threshold"], 3)
            self.assertEqual(inspected["share_ids"], [1, 2, 3, 4, 5])

            recover_result = subprocess.run(
                [sys.executable, str(MODULE_PATH), "recover", "--input", str(output), "--use", "1", "3", "5"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(recover_result.stdout)["secret"], "distributed trust")

    def test_recover_requires_threshold_count(self) -> None:
        secret = b"abc"
        shares = split_secret(secret, threshold=3, total_shares=5)
        with self.assertRaisesRegex(ValueError, "not enough shares"):
            recover_secret(shares[:2], threshold=3)


if __name__ == "__main__":
    unittest.main()
