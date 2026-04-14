#!/usr/bin/env python3
"""Merkle tree manifest builder, diff tool, and sync plan generator for directories."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FileRecord:
    path: str
    sha256: str
    size: int


@dataclass(frozen=True)
class DirectoryNode:
    path: str
    digest: str
    children: tuple[str, ...]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path, chunk_size: int = 65536) -> tuple[str, int]:
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            size += len(chunk)
            hasher.update(chunk)
    return hasher.hexdigest(), size


def should_ignore(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    ignored = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache"}
    return any(part in ignored for part in rel_parts)


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and not should_ignore(path, root):
            yield path


def build_manifest(root: Path) -> dict:
    root = root.resolve()
    files: list[FileRecord] = []
    directory_children: dict[str, list[str]] = {".": []}

    for file_path in iter_files(root):
        rel_path = file_path.relative_to(root).as_posix()
        digest, size = hash_file(file_path)
        files.append(FileRecord(path=rel_path, sha256=digest, size=size))

        parts = rel_path.split("/")
        for index in range(len(parts) - 1):
            directory = "." if index == 0 else "/".join(parts[:index])
            child_dir = "/".join(parts[: index + 1])
            directory_children.setdefault(directory, [])
            if child_dir not in directory_children[directory]:
                directory_children[directory].append(child_dir)
            directory_children.setdefault(child_dir, [])

        parent = "." if len(parts) == 1 else "/".join(parts[:-1])
        directory_children.setdefault(parent, []).append(rel_path)

    normalized_children = {
        key: sorted(set(value)) for key, value in directory_children.items()
    }
    directories = build_directory_nodes(
        normalized_children, {record.path: record.sha256 for record in files}
    )

    return {
        "root": str(root),
        "algorithm": "sha256",
        "file_count": len(files),
        "files": [record.__dict__ for record in files],
        "directories": [node.__dict__ for node in directories],
        "root_digest": next(node.digest for node in directories if node.path == "."),
    }


def build_directory_nodes(
    children_map: dict[str, list[str]], file_hashes: dict[str, str]
) -> list[DirectoryNode]:
    cache: dict[str, DirectoryNode] = {}

    def compute(directory: str) -> DirectoryNode:
        if directory in cache:
            return cache[directory]

        child_names = tuple(sorted(children_map.get(directory, [])))
        child_pairs: list[str] = []
        for child in child_names:
            if child in children_map:
                child_pairs.append(f"dir:{child}:{compute(child).digest}")
            else:
                child_pairs.append(f"file:{child}:{file_hashes[child]}")

        digest = sha256_bytes("\n".join(child_pairs).encode("utf-8"))
        node = DirectoryNode(path=directory, digest=digest, children=child_names)
        cache[directory] = node
        return node

    for directory in sorted(children_map.keys(), key=lambda value: (value.count("/"), value)):
        compute(directory)

    return sorted(cache.values(), key=lambda node: (node.path.count("/"), node.path))


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_diff(left: dict, right: dict) -> dict:
    left_files = {entry["path"]: entry for entry in left["files"]}
    right_files = {entry["path"]: entry for entry in right["files"]}

    added = sorted(path for path in right_files if path not in left_files)
    removed = sorted(path for path in left_files if path not in right_files)
    changed = sorted(
        path
        for path in left_files.keys() & right_files.keys()
        if left_files[path]["sha256"] != right_files[path]["sha256"]
    )

    left_dirs = {entry["path"]: entry["digest"] for entry in left["directories"]}
    right_dirs = {entry["path"]: entry["digest"] for entry in right["directories"]}
    changed_directories = sorted(
        path
        for path in left_dirs.keys() & right_dirs.keys()
        if left_dirs[path] != right_dirs[path]
    )

    return {
        "left_root": left["root"],
        "right_root": right["root"],
        "left_root_digest": left["root_digest"],
        "right_root_digest": right["root_digest"],
        "added": added,
        "removed": removed,
        "changed": changed,
        "changed_directories": changed_directories,
        "is_identical": not (added or removed or changed),
    }


def build_copy_plan(source: dict, target: dict) -> dict:
    source_files = {entry["path"]: entry for entry in source["files"]}
    target_files = {entry["path"]: entry for entry in target["files"]}

    mkdir_paths = collect_parent_directories(
        sorted(path for path in source_files if path not in target_files)
    )
    copy_paths = sorted(path for path in source_files if path not in target_files)
    update_paths = sorted(
        path
        for path in source_files.keys() & target_files.keys()
        if source_files[path]["sha256"] != target_files[path]["sha256"]
    )
    delete_paths = sorted(path for path in target_files if path not in source_files)

    operations: list[dict[str, object]] = []
    for path in mkdir_paths:
        operations.append({"op": "mkdir", "path": path})
    for path in copy_paths:
        operations.append(
            {
                "op": "copy",
                "path": path,
                "size": source_files[path]["size"],
                "sha256": source_files[path]["sha256"],
            }
        )
    for path in update_paths:
        operations.append(
            {
                "op": "update",
                "path": path,
                "size": source_files[path]["size"],
                "sha256": source_files[path]["sha256"],
                "previous_sha256": target_files[path]["sha256"],
            }
        )
    for path in delete_paths:
        operations.append(
            {
                "op": "delete",
                "path": path,
                "size": target_files[path]["size"],
                "sha256": target_files[path]["sha256"],
            }
        )

    return {
        "source_root": source["root"],
        "target_root": target["root"],
        "mkdir_count": len(mkdir_paths),
        "copy_count": len(copy_paths),
        "update_count": len(update_paths),
        "delete_count": len(delete_paths),
        "bytes_to_copy": sum(source_files[path]["size"] for path in copy_paths),
        "bytes_to_update": sum(source_files[path]["size"] for path in update_paths),
        "operations": operations,
    }


def collect_parent_directories(file_paths: list[str]) -> list[str]:
    directories: set[str] = set()
    for file_path in file_paths:
        parts = file_path.split("/")[:-1]
        for index in range(1, len(parts) + 1):
            directories.add("/".join(parts[:index]))
    return sorted(directories, key=lambda value: (value.count("/"), value))


def print_human_diff(summary: dict) -> None:
    print(f"left:  {summary['left_root']}")
    print(f"right: {summary['right_root']}")
    print(f"identical: {summary['is_identical']}")
    print(f"root digests: {summary['left_root_digest']} -> {summary['right_root_digest']}")
    for label in ("added", "removed", "changed", "changed_directories"):
        values = summary[label]
        print(f"{label} ({len(values)}):")
        for value in values:
            print(f"  - {value}")


def print_human_plan(plan: dict) -> None:
    print(f"source: {plan['source_root']}")
    print(f"target: {plan['target_root']}")
    print(
        "operations: "
        f"mkdir={plan['mkdir_count']} copy={plan['copy_count']} "
        f"update={plan['update_count']} delete={plan['delete_count']}"
    )
    print(
        f"bytes scheduled: copy={plan['bytes_to_copy']} update={plan['bytes_to_update']}"
    )
    for operation in plan["operations"]:
        label = operation["op"]
        path = operation["path"]
        if label == "mkdir":
            print(f"  - mkdir {path}")
            continue
        details = []
        if "size" in operation:
            details.append(f"size={operation['size']}")
        if "sha256" in operation:
            details.append(f"sha256={operation['sha256'][:12]}")
        if "previous_sha256" in operation:
            details.append(f"prev={operation['previous_sha256'][:12]}")
        suffix = f" ({', '.join(details)})" if details else ""
        print(f"  - {label} {path}{suffix}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_cmd = subparsers.add_parser("build", help="build a Merkle manifest for a directory")
    build_cmd.add_argument("root", type=Path)
    build_cmd.add_argument("--output", type=Path, help="write manifest JSON to a file")

    diff_cmd = subparsers.add_parser("diff", help="diff two directories or manifest JSON files")
    diff_cmd.add_argument("left", type=Path)
    diff_cmd.add_argument("right", type=Path)
    diff_cmd.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    plan_cmd = subparsers.add_parser(
        "plan", help="build a copy/update/delete plan to sync a target with a source"
    )
    plan_cmd.add_argument("source", type=Path)
    plan_cmd.add_argument("target", type=Path)
    plan_cmd.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    return parser


def resolve_manifest(path: Path) -> dict:
    if path.is_dir():
        return build_manifest(path)
    return load_manifest(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "build":
        manifest = build_manifest(args.root)
        payload = json.dumps(manifest, indent=2)
        if args.output:
            args.output.write_text(payload + "\n", encoding="utf-8")
        else:
            print(payload)
        return 0

    if args.command == "diff":
        summary = summarize_diff(resolve_manifest(args.left), resolve_manifest(args.right))
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print_human_diff(summary)
        return 0

    if args.command == "plan":
        plan = build_copy_plan(resolve_manifest(args.source), resolve_manifest(args.target))
        if args.json:
            print(json.dumps(plan, indent=2))
        else:
            print_human_plan(plan)
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
