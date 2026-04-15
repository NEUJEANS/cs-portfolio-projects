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
attach_authentication = module.attach_authentication
build_bundle_payload = module.build_bundle_payload
lagrange_interpolate_at_zero = module.lagrange_interpolate_at_zero
load_shares = module.load_shares
recover_secret = module.recover_secret
save_shares = module.save_shares
split_secret = module.split_secret
verify_bundle_authentication = module.verify_bundle_authentication


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
            threshold, encoding, loaded, authentication, _ = load_shares(output)
            self.assertEqual(threshold, 2)
            self.assertEqual(encoding, "utf-8")
            self.assertIsNone(authentication)
            self.assertEqual([share.x for share in loaded], [1, 2, 3])
            self.assertEqual(recover_secret(loaded[:2], threshold=2), b"portfolio")

    def test_authenticated_bundle_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "shares.json"
            shares = split_secret(b"portfolio", threshold=3, total_shares=5)
            save_shares(output, threshold=3, shares=shares, auth_passphrase="swordfish")
            threshold, encoding, loaded, authentication, payload = load_shares(output)
            self.assertEqual(threshold, 3)
            self.assertEqual(encoding, "utf-8")
            self.assertIsNotNone(authentication)
            verify_bundle_authentication(payload, "swordfish")
            self.assertEqual(recover_secret([loaded[0], loaded[2], loaded[4]], threshold=3), b"portfolio")

    def test_authenticated_bundle_rejects_wrong_passphrase(self) -> None:
        payload = attach_authentication(build_bundle_payload(2, split_secret(b"abc", threshold=2, total_shares=3)), "right-pass")
        with self.assertRaisesRegex(ValueError, "authentication failed"):
            verify_bundle_authentication(payload, "wrong-pass")

    def test_load_rejects_mismatched_share_count_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "shares.json"
            shares = split_secret(b"portfolio", threshold=2, total_shares=3)
            save_shares(output, threshold=2, shares=shares)
            payload = json.loads(output.read_text(encoding="utf-8"))
            payload["share_count"] = 99
            output.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "share_count"):
                load_shares(output)

    def test_cli_split_inspect_and_recover(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "shares.json"
            split_result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "split",
                    "--secret",
                    "distributed trust",
                    "--threshold",
                    "3",
                    "--shares",
                    "5",
                    "--output",
                    str(output),
                    "--auth-passphrase",
                    "demo-pass",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertTrue(json.loads(split_result.stdout)["authenticated"])

            inspect_result = subprocess.run(
                [sys.executable, str(MODULE_PATH), "inspect", "--input", str(output), "--auth-passphrase", "demo-pass"],
                capture_output=True,
                text=True,
                check=True,
            )
            inspected = json.loads(inspect_result.stdout)
            self.assertEqual(inspected["threshold"], 3)
            self.assertEqual(inspected["share_ids"], [1, 2, 3, 4, 5])
            self.assertTrue(inspected["authenticated"])
            self.assertTrue(inspected["authentication_verified"])

            recover_result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "recover",
                    "--input",
                    str(output),
                    "--use",
                    "1",
                    "3",
                    "5",
                    "--auth-passphrase",
                    "demo-pass",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            recovered = json.loads(recover_result.stdout)
            self.assertEqual(recovered["secret"], "distributed trust")
            self.assertTrue(recovered["authenticated"])

    def test_authenticated_recover_requires_threshold_count(self) -> None:
        secret = b"abc"
        shares = split_secret(secret, threshold=3, total_shares=5)
        with self.assertRaisesRegex(ValueError, "not enough shares"):
            recover_secret(shares[:2], threshold=3)

    def test_authenticated_bundle_requires_passphrase_for_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "shares.json"
            shares = split_secret(b"portfolio", threshold=2, total_shares=3)
            save_shares(output, threshold=2, shares=shares, auth_passphrase="required-pass")
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), "recover", "--input", str(output), "--use", "1", "2"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("require --auth-passphrase", result.stderr)


if __name__ == "__main__":
    unittest.main()
