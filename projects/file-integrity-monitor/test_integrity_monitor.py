import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from integrity_monitor import (
    EXIT_CHANGES_FOUND,
    EXIT_OK,
    EXIT_SIGNATURE_INVALID,
    build_manifest,
    diff_exit_code,
    diff_snapshots,
    format_text_report,
    parse_public_key_envs,
    parse_verification_envs,
    sign_manifest,
    sign_manifest_with_private_key,
    verify_manifest_signature,
    verify_manifest_signature_with_public_key,
    verify_manifest_with_public_keys,
    verify_manifest_with_secrets,
)

SCRIPT = Path(__file__).with_name("integrity_monitor.py")
OPENSSL = subprocess.run(["openssl", "version"], capture_output=True, text=True)
HAS_OPENSSL = OPENSSL.returncode == 0


class IntegrityMonitorTests(unittest.TestCase):
    def test_detect_added_removed_and_changed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("hello")
            (root / "b.txt").write_text("keep")
            old = build_manifest(root)

            (root / "a.txt").write_text("bye")
            (root / "b.txt").unlink()
            (root / "c.txt").write_text("new")
            new = build_manifest(root)

            diff = diff_snapshots(old, new)
            self.assertEqual(diff["changed"], ["a.txt"])
            self.assertEqual(diff["removed"], ["b.txt"])
            self.assertEqual(diff["added"], ["c.txt"])
            self.assertEqual(
                diff["summary"],
                {"added": 1, "removed": 1, "changed": 1, "unchanged": 0, "has_changes": True},
            )

    def test_ignore_patterns_exclude_matching_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "keep.txt").write_text("keep")
            (root / "skip.log").write_text("skip")

            manifest = build_manifest(root, ignore_patterns=["*.log"])
            self.assertIn("keep.txt", manifest["files"])
            self.assertNotIn("skip.log", manifest["files"])

    def test_text_report_contains_summary_and_sections(self):
        diff = {
            "added": ["new.txt"],
            "removed": ["old.txt"],
            "changed": ["config.json"],
            "unchanged": ["same.txt"],
            "summary": {"added": 1, "removed": 1, "changed": 1, "unchanged": 1, "has_changes": True},
        }
        report = format_text_report(diff)
        self.assertIn("Integrity diff summary", report)
        self.assertIn("ADDED", report)
        self.assertIn("config.json", report)

    def test_legacy_snapshot_format_remains_supported(self):
        old = {"a.txt": "oldhash"}
        new = {"a.txt": "newhash", "b.txt": "same"}
        diff = diff_snapshots(old, new)
        self.assertEqual(diff["changed"], ["a.txt"])
        self.assertEqual(diff["added"], ["b.txt"])

    def test_diff_exit_code_respects_fail_on_changes_flag(self):
        clean_diff = {
            "added": [],
            "removed": [],
            "changed": [],
            "unchanged": ["same.txt"],
            "summary": {"added": 0, "removed": 0, "changed": 0, "unchanged": 1, "has_changes": False},
        }
        changed_diff = {
            "added": ["new.txt"],
            "removed": [],
            "changed": [],
            "unchanged": [],
            "summary": {"added": 1, "removed": 0, "changed": 0, "unchanged": 0, "has_changes": True},
        }
        self.assertEqual(diff_exit_code(clean_diff, fail_on_changes=False), EXIT_OK)
        self.assertEqual(diff_exit_code(changed_diff, fail_on_changes=False), EXIT_OK)
        self.assertEqual(diff_exit_code(changed_diff, fail_on_changes=True), EXIT_CHANGES_FOUND)

    def test_sign_manifest_and_verify_signature(self):
        manifest = build_manifest(Path(__file__).parent)
        signed = sign_manifest(manifest, "secret-key", key_id="integrity-v1")
        self.assertIn("signature", signed)
        self.assertEqual(signed["signature"]["key_id"], "integrity-v1")
        self.assertTrue(verify_manifest_signature(signed, "secret-key"))
        self.assertFalse(verify_manifest_signature(signed, "wrong-key"))

    def test_parse_verification_envs_prefers_unique_entries(self):
        self.assertEqual(
            parse_verification_envs("CURRENT_KEY", ["OLD_KEY", "CURRENT_KEY", "OLD_KEY"]),
            ["OLD_KEY", "CURRENT_KEY"],
        )

    def test_parse_public_key_envs_prefers_unique_entries(self):
        self.assertEqual(
            parse_public_key_envs("CURRENT_PUB", ["OLD_PUB", "CURRENT_PUB", "OLD_PUB"]),
            ["OLD_PUB", "CURRENT_PUB"],
        )

    def test_verify_manifest_with_secrets_uses_key_id_to_match_rotated_keys(self):
        manifest = sign_manifest(build_manifest(Path(__file__).parent), "old-secret", key_id="OLD_KEY")
        result = verify_manifest_with_secrets(
            manifest,
            [("CURRENT_KEY", "new-secret"), ("OLD_KEY", "old-secret")],
        )
        self.assertTrue(result["verified"])
        self.assertEqual(result["matched_env"], "OLD_KEY")
        self.assertEqual(result["key_id"], "OLD_KEY")

    @unittest.skipUnless(HAS_OPENSSL, "OpenSSL is required for RSA signature tests")
    def test_sign_manifest_with_private_key_and_verify_with_public_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_key = root / "private.pem"
            public_key = root / "public.pem"
            self._generate_rsa_keypair(private_key, public_key)

            manifest = build_manifest(Path(__file__).parent)
            signed = sign_manifest_with_private_key(manifest, private_key, key_id="INTEGRITY_PUB_V1")
            self.assertEqual(signed["signature"]["algorithm"], "rsa-sha256")
            self.assertTrue(verify_manifest_signature_with_public_key(signed, public_key))

            other_private = root / "other-private.pem"
            other_public = root / "other-public.pem"
            self._generate_rsa_keypair(other_private, other_public)
            self.assertFalse(verify_manifest_signature_with_public_key(signed, other_public))

    @unittest.skipUnless(HAS_OPENSSL, "OpenSSL is required for RSA signature tests")
    def test_verify_manifest_with_public_keys_uses_key_id_to_match_rotated_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_private = root / "old-private.pem"
            old_public = root / "old-public.pem"
            new_private = root / "new-private.pem"
            new_public = root / "new-public.pem"
            self._generate_rsa_keypair(old_private, old_public)
            self._generate_rsa_keypair(new_private, new_public)

            manifest = sign_manifest_with_private_key(
                build_manifest(Path(__file__).parent),
                old_private,
                key_id="INTEGRITY_PUB_V1",
            )
            result = verify_manifest_with_public_keys(
                manifest,
                [("INTEGRITY_PUB_V2", new_public), ("INTEGRITY_PUB_V1", old_public)],
            )
            self.assertTrue(result["verified"])
            self.assertEqual(result["matched_env"], "INTEGRITY_PUB_V1")

    def test_cli_scan_output_and_diff_text_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "snapshots" / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")
            (data_path / "ignore.tmp").write_text("tmp")

            scan = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "scan",
                    str(data_path),
                    "--ignore",
                    "*.tmp",
                    "--output",
                    str(baseline_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = json.loads(scan.stdout)
            self.assertEqual(manifest["algorithm"], "sha256")
            self.assertEqual(manifest["file_count"], 1)
            self.assertEqual(manifest["embedded_paths"], [])
            self.assertTrue(baseline_path.exists())

            (data_path / "alpha.txt").write_text("updated")
            (data_path / "beta.txt").write_text("beta")

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--format",
                    "text",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("changed: 1", diff.stdout)
            self.assertIn("added: 1", diff.stdout)
            self.assertIn("beta.txt", diff.stdout)

    def test_cli_signed_baseline_verifies_and_diffs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")

            env = os.environ | {"INTEGRITY_SECRET": "super-secret"}
            scan = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "scan",
                    str(data_path),
                    "--output",
                    str(baseline_path),
                    "--signing-key-env",
                    "INTEGRITY_SECRET",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            manifest = json.loads(scan.stdout)
            self.assertEqual(manifest["signature"]["algorithm"], "hmac-sha256")
            self.assertEqual(manifest["signature"]["key_id"], "INTEGRITY_SECRET")

            verify = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "verify",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--signing-key-env",
                    "INTEGRITY_SECRET",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertIn('"verified": true', verify.stdout)
            self.assertIn('"matched_env": "INTEGRITY_SECRET"', verify.stdout)

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--signing-key-env",
                    "INTEGRITY_SECRET",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertIn('"has_changes": false', diff.stdout)

    def test_cli_supports_key_rotation_with_multiple_verification_envs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")

            signing_env = os.environ | {"INTEGRITY_SECRET_V1": "legacy-secret"}
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "scan",
                    str(data_path),
                    "--output",
                    str(baseline_path),
                    "--signing-key-env",
                    "INTEGRITY_SECRET_V1",
                    "--key-id",
                    "INTEGRITY_SECRET_V1",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=signing_env,
            )

            rotated_env = os.environ | {
                "INTEGRITY_SECRET_V1": "legacy-secret",
                "INTEGRITY_SECRET_V2": "new-secret",
            }
            verify = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "verify",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--verify-key-env",
                    "INTEGRITY_SECRET_V2",
                    "--verify-key-env",
                    "INTEGRITY_SECRET_V1",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=rotated_env,
            )
            self.assertIn('"verified": true', verify.stdout)
            self.assertIn('"matched_env": "INTEGRITY_SECRET_V1"', verify.stdout)

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--verify-key-env",
                    "INTEGRITY_SECRET_V2",
                    "--verify-key-env",
                    "INTEGRITY_SECRET_V1",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=rotated_env,
            )
            self.assertIn('"has_changes": false', diff.stdout)

    @unittest.skipUnless(HAS_OPENSSL, "OpenSSL is required for RSA signature tests")
    def test_cli_supports_asymmetric_signed_baselines_and_public_key_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")

            old_private = root / "old-private.pem"
            old_public = root / "old-public.pem"
            new_private = root / "new-private.pem"
            new_public = root / "new-public.pem"
            self._generate_rsa_keypair(old_private, old_public)
            self._generate_rsa_keypair(new_private, new_public)

            signing_env = os.environ | {"INTEGRITY_PRIV_V1": str(old_private)}
            scan = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "scan",
                    str(data_path),
                    "--output",
                    str(baseline_path),
                    "--private-key-env",
                    "INTEGRITY_PRIV_V1",
                    "--key-id",
                    "INTEGRITY_PUB_V1",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=signing_env,
            )
            manifest = json.loads(scan.stdout)
            self.assertEqual(manifest["signature"]["algorithm"], "rsa-sha256")
            self.assertEqual(manifest["signature"]["key_id"], "INTEGRITY_PUB_V1")

            verify_env = os.environ | {
                "INTEGRITY_PUB_V1": str(old_public),
                "INTEGRITY_PUB_V2": str(new_public),
            }
            verify = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "verify",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--public-key-env",
                    "INTEGRITY_PUB_V2",
                    "--public-key-env",
                    "INTEGRITY_PUB_V1",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=verify_env,
            )
            self.assertIn('"verified": true', verify.stdout)
            self.assertIn('"matched_env": "INTEGRITY_PUB_V1"', verify.stdout)

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--public-key-env",
                    "INTEGRITY_PUB_V2",
                    "--public-key-env",
                    "INTEGRITY_PUB_V1",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=verify_env,
            )
            self.assertIn('"has_changes": false', diff.stdout)

    def test_scan_and_diff_ignore_embedded_baseline_inside_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "alpha.txt").write_text("alpha")
            baseline_path = root / "baseline.json"

            scan = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "scan",
                    str(root),
                    "--output",
                    str(baseline_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            manifest = json.loads(scan.stdout)
            self.assertEqual(manifest["embedded_paths"], ["baseline.json"])

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(root),
                    "--baseline",
                    str(baseline_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('"has_changes": false', diff.stdout)

    def test_cli_signed_baseline_requires_valid_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")

            env = os.environ | {"INTEGRITY_SECRET": "super-secret"}
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "scan",
                    str(data_path),
                    "--output",
                    str(baseline_path),
                    "--signing-key-env",
                    "INTEGRITY_SECRET",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )

            missing_secret = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(missing_secret.returncode, 2)
            self.assertIn(
                "diff requires --signing-key-env/--verify-key-env or --private-key-env/--public-key-env",
                missing_secret.stderr,
            )

            wrong_secret_env = os.environ | {"WRONG_SECRET": "bad-secret"}
            wrong_secret = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "verify",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--signing-key-env",
                    "WRONG_SECRET",
                ],
                capture_output=True,
                text=True,
                env=wrong_secret_env,
            )
            self.assertEqual(wrong_secret.returncode, EXIT_SIGNATURE_INVALID)
            self.assertIn('"verified": false', wrong_secret.stdout)

    def test_cli_fail_on_changes_returns_exit_code_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")

            subprocess.run(
                [sys.executable, str(SCRIPT), "scan", str(data_path), "--output", str(baseline_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            (data_path / "alpha.txt").write_text("updated")

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--fail-on-changes",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(diff.returncode, EXIT_CHANGES_FOUND)
            self.assertIn('"has_changes": true', diff.stdout)

    def test_cli_fail_on_changes_stays_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            baseline_path = root / "baseline.json"
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")

            subprocess.run(
                [sys.executable, str(SCRIPT), "scan", str(data_path), "--output", str(baseline_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            diff = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "diff",
                    str(data_path),
                    "--baseline",
                    str(baseline_path),
                    "--fail-on-changes",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(diff.returncode, EXIT_OK)
            self.assertIn('"has_changes": false', diff.stdout)

    def test_cli_missing_baseline_returns_usage_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_path = root / "data"
            data_path.mkdir()
            (data_path / "alpha.txt").write_text("alpha")

            diff = subprocess.run(
                [sys.executable, str(SCRIPT), "diff", str(data_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(diff.returncode, 2)
            self.assertIn("diff requires --baseline", diff.stderr)

    @staticmethod
    def _generate_rsa_keypair(private_key: Path, public_key: Path):
        subprocess.run(
            [
                "openssl",
                "genpkey",
                "-algorithm",
                "RSA",
                "-pkeyopt",
                "rsa_keygen_bits:2048",
                "-out",
                str(private_key),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["openssl", "rsa", "-pubout", "-in", str(private_key), "-out", str(public_key)],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
