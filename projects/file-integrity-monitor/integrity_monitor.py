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
        "version": 3,
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


def sign_manifest(manifest, secret: str):
    if not secret:
        raise ValueError("Signing secret cannot be empty")

    signature = hmac.new(secret.encode("utf-8"), canonicalize_manifest(manifest), hashlib.sha256).hexdigest()
    signed_manifest = dict(manifest)
    signed_manifest["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "value": signature,
    }
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
        help="Environment variable containing the shared secret used to sign or verify manifests",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root_path = Path(args.path).resolve()
    baseline_path = Path(args.baseline).resolve() if args.baseline else None
    output_path = Path(args.output).resolve() if args.output else None

    try:
        signing_secret = load_signing_secret(args.signing_key_env)
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
            manifest = sign_manifest(manifest, signing_secret)
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
        if signing_secret is None:
            return fail_usage("verify requires --signing-key-env")
        if verify_manifest_signature(baseline, signing_secret):
            print(json.dumps({"verified": True, "algorithm": baseline["signature"]["algorithm"]}, indent=2))
            return EXIT_OK
        print(json.dumps({"verified": False, "reason": "signature mismatch"}, indent=2))
        return EXIT_SIGNATURE_INVALID

    if signature_present:
        if signing_secret is None:
            return fail_usage("diff requires --signing-key-env when the baseline is signed")
        if not verify_manifest_signature(baseline, signing_secret):
            print(json.dumps({"verified": False, "reason": "signature mismatch"}, indent=2))
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
