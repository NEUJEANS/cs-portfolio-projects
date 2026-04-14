import argparse
import fnmatch
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SUPPORTED_ALGORITHMS = {"sha256": hashlib.sha256, "sha1": hashlib.sha1, "md5": hashlib.md5}


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


def snapshot_dir(directory, algorithm: str = "sha256", ignore_patterns: Iterable[str] | None = None):
    base = Path(directory).resolve()
    data = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue

        relative = str(path.relative_to(base))
        if not should_include(relative, ignore_patterns):
            continue

        stat = path.stat()
        data[relative] = {
            "hash": hash_file(path, algorithm),
            "size": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }
    return data


def build_manifest(directory, algorithm: str = "sha256", ignore_patterns: Iterable[str] | None = None):
    files = snapshot_dir(directory, algorithm=algorithm, ignore_patterns=ignore_patterns)
    return {
        "version": 2,
        "algorithm": algorithm,
        "root": str(Path(directory).resolve()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ignore_patterns": list(ignore_patterns or []),
        "file_count": len(files),
        "files": files,
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="File integrity monitor")
    parser.add_argument("command", choices=["scan", "diff"])
    parser.add_argument("path")
    parser.add_argument("--baseline", help="Path to a saved baseline manifest for diff commands")
    parser.add_argument("--output", help="Write the scan manifest to a file")
    parser.add_argument("--algorithm", default="sha256", choices=sorted(SUPPORTED_ALGORITHMS))
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Glob pattern to ignore (repeat flag for multiple patterns)",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.command == "scan":
        manifest = build_manifest(args.path, algorithm=args.algorithm, ignore_patterns=args.ignore)
        payload = json.dumps(manifest, indent=2)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(payload + "\n")
        print(payload)
        return

    baseline_path = Path(args.baseline) if args.baseline else None
    if baseline_path is None:
        raise SystemExit("diff requires --baseline")

    baseline = json.loads(baseline_path.read_text())
    algorithm = baseline.get("algorithm", args.algorithm)
    ignore_patterns = baseline.get("ignore_patterns", args.ignore)
    current = build_manifest(args.path, algorithm=algorithm, ignore_patterns=ignore_patterns)
    diff_result = diff_snapshots(baseline, current)

    if args.format == "text":
        print(format_text_report(diff_result))
    else:
        print(json.dumps(diff_result, indent=2))


if __name__ == "__main__":
    main()
