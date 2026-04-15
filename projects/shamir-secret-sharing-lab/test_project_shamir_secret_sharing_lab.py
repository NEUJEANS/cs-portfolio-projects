import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from shamir_secret_sharing_lab import (
    Share,
    attach_authentication,
    build_bundle_payload,
    lagrange_interpolate_at_zero,
    load_shares,
    recover_secret,
    save_shares,
    split_secret,
    verify_bundle_authentication,
)

SCRIPT = ROOT / "shamir_secret_sharing_lab.py"


class ShamirSecretSharingLabTests(unittest.TestCase):
    def test_split_and_recover_round_trip(self):
        secret = "launch codes stay local 🔐".encode("utf-8")
        shares = split_secret(secret, threshold=3, total_shares=5)
        recovered = recover_secret([shares[0], shares[2], shares[4]], threshold=3)
        self.assertEqual(recovered, secret)

    def test_two_shares_reveal_linear_secret(self):
        secret_byte = 123
        y1 = (secret_byte + 50 * 1) % 257
        y2 = (secret_byte + 50 * 2) % 257
        recovered = lagrange_interpolate_at_zero([(1, y1), (2, y2)])
        self.assertEqual(recovered, secret_byte)

    def test_recover_rejects_mismatched_share_lengths(self):
        with self.assertRaisesRegex(ValueError, "same payload length"):
            recover_secret([Share(1, [1, 2]), Share(2, [3])], threshold=2)

    def test_share_bundle_round_trip(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            output = temp_dir / "shares.json"
            shares = split_secret(b"portfolio", threshold=2, total_shares=3)
            save_shares(output, threshold=2, shares=shares)
            threshold, encoding, loaded, authentication, _ = load_shares(output)
            self.assertEqual(threshold, 2)
            self.assertEqual(encoding, "utf-8")
            self.assertIsNone(authentication)
            self.assertEqual([share.x for share in loaded], [1, 2, 3])
            self.assertEqual(recover_secret(loaded[:2], threshold=2), b"portfolio")
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_authenticated_bundle_verifies_and_round_trips(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            output = temp_dir / "shares.json"
            shares = split_secret(b"portfolio", threshold=3, total_shares=5)
            save_shares(output, threshold=3, shares=shares, auth_passphrase="swordfish")
            threshold, _, loaded, authentication, payload = load_shares(output)
            self.assertEqual(threshold, 3)
            self.assertIsNotNone(authentication)
            verify_bundle_authentication(payload, "swordfish")
            self.assertEqual(recover_secret([loaded[0], loaded[2], loaded[4]], threshold=3), b"portfolio")
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_authenticated_bundle_rejects_wrong_passphrase(self):
        payload = attach_authentication(build_bundle_payload(2, split_secret(b"abc", threshold=2, total_shares=3)), "right-pass")
        with self.assertRaisesRegex(ValueError, "authentication failed"):
            verify_bundle_authentication(payload, "wrong-pass")

    def test_load_rejects_mismatched_share_count_metadata(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            output = temp_dir / "shares.json"
            shares = split_secret(b"portfolio", threshold=2, total_shares=3)
            save_shares(output, threshold=2, shares=shares)
            payload = json.loads(output.read_text(encoding="utf-8"))
            payload["share_count"] = 99
            output.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "share_count"):
                load_shares(output)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_cli_split_inspect_and_recover(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            output = temp_dir / "shares.json"
            split_result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
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
                [sys.executable, str(SCRIPT), "inspect", "--input", str(output), "--auth-passphrase", "demo-pass"],
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
                    str(SCRIPT),
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
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_authenticated_recover_requires_passphrase(self):
        temp_dir = ROOT / self._testMethodName
        temp_dir.mkdir(exist_ok=True)
        try:
            output = temp_dir / "shares.json"
            shares = split_secret(b"portfolio", threshold=2, total_shares=3)
            save_shares(output, threshold=2, shares=shares, auth_passphrase="required-pass")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "recover", "--input", str(output), "--use", "1", "2"],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("require --auth-passphrase", result.stderr)
        finally:
            for child in temp_dir.iterdir():
                child.unlink()
            temp_dir.rmdir()

    def test_corrupted_share_is_detected(self):
        secret = b"abc"
        shares = split_secret(secret, threshold=3, total_shares=5)
        corrupted = [Share(shares[0].x, shares[0].values[:-1]), shares[1], shares[2]]
        with self.assertRaisesRegex(ValueError, "same payload length"):
            recover_secret(corrupted, threshold=3)


if __name__ == "__main__":
    unittest.main()
