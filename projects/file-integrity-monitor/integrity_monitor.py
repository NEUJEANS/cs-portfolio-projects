import argparse
import fnmatch
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SUPPORTED_ALGORITHMS = {"sha256": hashlib.sha256, "sha1": hashlib.sha1, "md5": hashlib.md5}
SIGNATURE_ALGORITHM = "hmac-sha256"

EXIT_OK = 0
EXIT_CHANGES_FOUND = 1
EXIT_USAGE_ERROR = 2
EXIT_SIGNATURE_INVALID = 3


def hash_file(path: Path, algorithm: str = "sha256") -> str:
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hasher = SUPPORTED_ALGORITHMS[algorithm]()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def should_include(relative_path: str, ignore_patterns: Iterable[str] | None = None) -> bool:
    if not ignore_patterns:
        return True
    return not any(fnmatch.fnmatch(relative_path, pattern) for pattern in ignore_patterns)


def resolve_embedded_path(base: Path, candidate: Path | None) -> str | None:
    if candidate is None:
        return None

    try:
        return str(candidate.resolve().relative_to(base.resolve()))
    except ValueError:
        return None


def snapshot_dir(
    directory,
    algorithm: str = "sha256",
    ignore_patterns: Iterable[str] | None = None,
    embedded_paths: Iterable[str] | None = None,
):
    base = Path(directory).resolve()
    embedded = set(embedded_paths or [])
    data = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue

        relative = str(path.relative_to(base))
        if relative in embedded:
            continue
        if not should_include(relative, ignore_patterns):
            continue

        stat = path.stat()
        data[relative] = {
            "hash": hash_file(path, algorithm),
            "size": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }
    return data


def build_manifest(
    directory,
    algorithm: str = "sha256",
    ignore_patterns: Iterable[str] | None = None,
    embedded_paths: Iterable[str] | None = None,
):
    files = snapshot_dir(
        directory,
        algorithm=algorithm,
        ignore_patterns=ignore_patterns,
        embedded_paths=embedded_paths,
    )
    return {
        "version": 4,
        "algorithm": algorithm,
        "root": str(Path(directory).resolve()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ignore_patterns": list(ignore_patterns or []),
        "embedded_paths": sorted(embedded_paths or []),
        "file_count": len(files),
        "files": files,
    }


def canonicalize_manifest(manifest):
    payload = {key: value for key, value in manifest.items() if key != "signature"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_manifest(manifest, secret: str, key_id: str | None = None):
    if not secret:
        raise ValueError("Signing secret cannot be empty")

    signature = hmac.new(secret.encode("utf-8"), canonicalize_manifest(manifest), hashlib.sha256).hexdigest()
    signed_manifest = dict(manifest)
    signed_manifest["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "value": signature,
    }
    if key_id:
        signed_manifest["signature"]["key_id"] = key_id
    return signed_manifest


def verify_manifest_signature(manifest, secret: str) -> bool:
    signature = manifest.get("signature")
    if not signature:
        return False
    if signature.get("algorithm") != SIGNATURE_ALGORITHM:
        return False

    expected = hmac.new(secret.encode("utf-8"), canonicalize_manifest(manifest), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature.get("value", ""), expected)


def load_signing_secret(env_name: str | None):
    if not env_name:
        return None
    secret = os.environ.get(env_name)
    if secret is None:
        raise ValueError(f"Signing key env var {env_name!r} is not set")
    if not secret:
        raise ValueError(f"Signing key env var {env_name!r} is empty")
    return secret


def load_verification_secrets(env_names: Iterable[str] | None):
    secrets = []
    seen = set()
    for env_name in env_names or []:
        if env_name in seen:
            continue
        seen.add(env_name)
        secret = load_signing_secret(env_name)
        secrets.append((env_name, secret))
    return secrets


def parse_verification_envs(signing_key_env: str | None, verify_key_envs: Iterable[str] | None):
    env_names = []
    for env_name in verify_key_envs or []:
        if env_name and env_name not in env_names:
            env_names.append(env_name)
    if signing_key_env and signing_key_env not in env_names:
        env_names.append(signing_key_env)
    return env_names


def verify_manifest_with_secrets(manifest, verification_secrets):
    signature = manifest.get("signature") or {}
    desired_key_id = signature.get("key_id")
    matched_env = None

    for env_name, secret in verification_secrets:
        if desired_key_id and env_name != desired_key_id:
            continue
        if verify_manifest_signature(manifest, secret):
            matched_env = env_name
            break

    return {
        "verified": matched_env is not None,
        "algorithm": signature.get("algorithm"),
        "key_id": desired_key_id,
        "matched_env": matched_env,
    }


def _coerce_snapshot(data):
    if "files" in data and isinstance(data["files"], dict):
        return data["files"]
    return data


def _hash_value(entry):
    if isinstance(entry, dict):
        return entry.get("hash")
    return entry


def diff_snapshots(old, new):
    old_files = _coerce_snapshot(old)
    new_files = _coerce_snapshot(new)
    added = sorted(set(new_files) - set(old_files))
    removed = sorted(set(old_files) - set(new_files))
    changed = sorted(
        key
        for key in set(old_files) & set(new_files)
        if _hash_value(old_files[key]) != _hash_value(new_files[key])
    )
    unchanged = sorted(set(old_files) & set(new_files) - set(changed))
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": len(unchanged),
            "has_changes": bool(added or removed or changed),
        },
    }


def format_text_report(diff_result):
    lines = ["Integrity diff summary:"]
    for key in ("added", "removed", "changed", "unchanged"):
        lines.append(f"- {key}: {diff_result['summary'][key]}")

    for key in ("added", "removed", "changed"):
        entries = diff_result[key]
        if entries:
            lines.append(f"\n{key.upper()}:")
            lines.extend(f"  - {entry}" for entry in entries)

    return "\n".join(lines)


def diff_exit_code(diff_result, fail_on_changes: bool) -> int:
    if fail_on_changes and diff_result["summary"]["has_changes"]:
        return EXIT_CHANGES_FOUND
    return EXIT_OK


def fail_usage(message: str) -> int:
    print(message, file=sys.stderr)
    return EXIT_USAGE_ERROR


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="File integrity monitor")
    parser.add_argument("command", choices=["scan", "diff", "verify"])
    parser.add_argument("path")
    parser.add_argument("--baseline", help="Path to a saved baseline manifest for diff or verify commands")
    parser.add_argument("--output", help="Write the scan manifest to a file")
    parser.add_argument("--algorithm", default="sha256", choices=sorted(SUPPORTED_ALGORITHMS))
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Glob pattern to ignore (repeat flag for multiple patterns)",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument(
        "--fail-on-changes",
        action="store_true",
        help="Exit with status 1 after a diff when added, removed, or changed files are detected",
    )
    parser.add_argument(
        "--signing-key-env",
        help="Environment variable containing the shared secret used to sign manifests and optionally verify them",
    )
    parser.add_argument(
        "--verify-key-env",
        action="append",
        default=[],
        help="Environment variable containing an accepted verification secret; repeat to support key rotation",
    )
    parser.add_argument(
        "--key-id",
        help="Stable key identifier to embed in the signature metadata (defaults to --signing-key-env when omitted)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root_path = Path(args.path).resolve()
    baseline_path = Path(args.baseline).resolve() if args.baseline else None
    output_path = Path(args.output).resolve() if args.output else None

    try:
        signing_secret = load_signing_secret(args.signing_key_env)
        verification_envs = parse_verification_envs(args.signing_key_env, args.verify_key_env)
        verification_secrets = load_verification_secrets(verification_envs)
    except ValueError as exc:
        return fail_usage(str(exc))

    if args.command == "scan":
        embedded_paths = []
        embedded_output = resolve_embedded_path(root_path, output_path)
        if embedded_output:
            embedded_paths.append(embedded_output)
        manifest = build_manifest(
            args.path,
            algorithm=args.algorithm,
            ignore_patterns=args.ignore,
            embedded_paths=embedded_paths,
        )
        if signing_secret:
            key_id = args.key_id or args.signing_key_env
            manifest = sign_manifest(manifest, signing_secret, key_id=key_id)
        payload = json.dumps(manifest, indent=2)
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(payload + "\n")
        print(payload)
        return EXIT_OK

    if baseline_path is None:
        return fail_usage(f"{args.command} requires --baseline")

    baseline = json.loads(baseline_path.read_text())
    signature_present = "signature" in baseline

    if args.command == "verify":
        if not signature_present:
            return fail_usage("verify requires a baseline with a signature")
        if not verification_secrets:
            return fail_usage("verify requires --signing-key-env or --verify-key-env")
        verification_result = verify_manifest_with_secrets(baseline, verification_secrets)
        if verification_result["verified"]:
            print(json.dumps(verification_result, indent=2))
            return EXIT_OK
        verification_result["reason"] = "signature mismatch"
        print(json.dumps(verification_result, indent=2))
        return EXIT_SIGNATURE_INVALID

    if signature_present:
        if not verification_secrets:
            return fail_usage("diff requires --signing-key-env or --verify-key-env when the baseline is signed")
        verification_result = verify_manifest_with_secrets(baseline, verification_secrets)
        if not verification_result["verified"]:
            verification_result["reason"] = "signature mismatch"
            print(json.dumps(verification_result, indent=2))
            return EXIT_SIGNATURE_INVALID

    algorithm = baseline.get("algorithm", args.algorithm)
    ignore_patterns = baseline.get("ignore_patterns", args.ignore)
    embedded_paths = set(baseline.get("embedded_paths", []))
    embedded_baseline = resolve_embedded_path(root_path, baseline_path)
    if embedded_baseline:
        embedded_paths.add(embedded_baseline)
    current = build_manifest(
        args.path,
        algorithm=algorithm,
        ignore_patterns=ignore_patterns,
        embedded_paths=sorted(embedded_paths),
    )
    diff_result = diff_snapshots(baseline, current)

    if args.format == "text":
        print(format_text_report(diff_result))
    else:
        print(json.dumps(diff_result, indent=2))

    return diff_exit_code(diff_result, fail_on_changes=args.fail_on_changes)


if __name__ == "__main__":
    raise SystemExit(main())
