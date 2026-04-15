#!/usr/bin/env python3
"""Merkle tree manifest builder, diff tool, sync plan generator, plan executor, and chunk-proof helper for directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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


def read_file_chunks(path: Path, chunk_size: int) -> list[bytes]:
    if chunk_size <= 0:
        raise ValueError("chunk size must be positive")
    chunks: list[bytes] = []
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            chunks.append(chunk)
    if not chunks:
        chunks.append(b"")
    return chunks


def merkle_parent_digest(left: str, right: str) -> str:
    return sha256_bytes(f"{left}:{right}".encode("utf-8"))


def build_chunk_proof(path: Path, chunk_size: int = 1024) -> dict:
    chunks = read_file_chunks(path, chunk_size)
    leaf_hashes = [sha256_bytes(chunk) for chunk in chunks]
    if not leaf_hashes:
        leaf_hashes = [sha256_bytes(b"")]

    levels: list[list[str]] = [leaf_hashes]
    current = leaf_hashes
    while len(current) > 1:
        next_level: list[str] = []
        for index in range(0, len(current), 2):
            left = current[index]
            right = current[index + 1] if index + 1 < len(current) else left
            next_level.append(merkle_parent_digest(left, right))
        levels.append(next_level)
        current = next_level

    chunk_records = []
    for index, chunk in enumerate(chunks):
        proof: list[dict[str, str]] = []
        node_index = index
        for level in levels[:-1]:
            is_right = node_index % 2 == 1
            sibling_index = node_index - 1 if is_right else node_index + 1
            sibling_hash = level[sibling_index] if sibling_index < len(level) else level[node_index]
            proof.append(
                {
                    "position": "left" if is_right else "right",
                    "digest": sibling_hash,
                }
            )
            node_index //= 2
        chunk_records.append(
            {
                "index": index,
                "offset": index * chunk_size,
                "size": len(chunk),
                "sha256": leaf_hashes[index],
                "proof": proof,
            }
        )

    return {
        "path": str(path.resolve()),
        "chunk_size": chunk_size,
        "file_size": path.stat().st_size,
        "chunk_count": len(chunks),
        "root_digest": levels[-1][0],
        "chunks": chunk_records,
    }


def verify_chunk_entry(root_digest: str, chunk_sha256: str, proof: list[dict[str, str]]) -> bool:
    current = chunk_sha256
    for entry in proof:
        if entry["position"] == "left":
            current = merkle_parent_digest(entry["digest"], current)
        elif entry["position"] == "right":
            current = merkle_parent_digest(current, entry["digest"])
        else:
            raise ValueError(f"invalid proof position: {entry['position']}")
    return current == root_digest


def diff_chunk_proofs(source_path: Path, target_path: Path, chunk_size: int = 1024) -> dict:
    source = build_chunk_proof(source_path, chunk_size=chunk_size)
    target = build_chunk_proof(target_path, chunk_size=chunk_size)

    limit = max(source["chunk_count"], target["chunk_count"])
    source_chunks = {entry["index"]: entry for entry in source["chunks"]}
    target_chunks = {entry["index"]: entry for entry in target["chunks"]}
    changed_chunks: list[dict[str, object]] = []

    for index in range(limit):
        left = source_chunks.get(index)
        right = target_chunks.get(index)
        if left and right and left["sha256"] == right["sha256"]:
            continue
        changed_chunks.append(
            {
                "index": index,
                "offset": index * chunk_size,
                "source_sha256": left["sha256"] if left else None,
                "target_sha256": right["sha256"] if right else None,
                "source_size": left["size"] if left else 0,
                "target_size": right["size"] if right else 0,
                "source_proof": left["proof"] if left else [],
            }
        )

    return {
        "source_path": str(source_path.resolve()),
        "target_path": str(target_path.resolve()),
        "chunk_size": chunk_size,
        "source_root_digest": source["root_digest"],
        "target_root_digest": target["root_digest"],
        "source_chunk_count": source["chunk_count"],
        "target_chunk_count": target["chunk_count"],
        "changed_chunk_count": len(changed_chunks),
        "changed_chunks": changed_chunks,
        "is_identical": not changed_chunks,
    }


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


def apply_plan(plan: dict, source_root: Path | None, execute: bool = False) -> dict:
    if execute and source_root is None:
        raise ValueError("applying changes requires a live source directory, not only a manifest")

    target_root = Path(plan["target_root"]).resolve()
    applied_operations: list[dict[str, object]] = []

    for operation in plan["operations"]:
        op = dict(operation)
        rel_path = Path(str(op["path"]))
        op["status"] = "planned"

        if execute:
            if op["op"] == "mkdir":
                (target_root / rel_path).mkdir(parents=True, exist_ok=True)
            elif op["op"] in {"copy", "update"}:
                assert source_root is not None
                source_path = source_root / rel_path
                target_path = target_root / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
            elif op["op"] == "delete":
                target_path = target_root / rel_path
                if target_path.exists():
                    target_path.unlink()
            else:
                raise ValueError(f"unsupported operation: {op['op']}")
            op["status"] = "applied"

        applied_operations.append(op)

    return {
        **plan,
        "mode": "execute" if execute else "dry-run",
        "source_root": str(source_root.resolve()) if source_root else plan["source_root"],
        "target_root": str(target_root),
        "applied_operation_count": sum(
            1 for operation in applied_operations if operation["status"] == "applied"
        ),
        "operations": applied_operations,
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


def print_human_apply(report: dict) -> None:
    print(f"mode: {report['mode']}")
    print_human_plan(report)
    print(f"applied operations: {report['applied_operation_count']}")
    for operation in report["operations"]:
        print(f"  - {operation['status']}: {operation['op']} {operation['path']}")


def print_human_chunk_diff(summary: dict) -> None:
    print(f"source file: {summary['source_path']}")
    print(f"target file: {summary['target_path']}")
    print(f"chunk size: {summary['chunk_size']}")
    print(f"identical: {summary['is_identical']}")
    print(
        f"root digests: {summary['source_root_digest']} -> {summary['target_root_digest']}"
    )
    print(f"changed chunks ({summary['changed_chunk_count']}):")
    for chunk in summary["changed_chunks"]:
        print(
            "  - "
            f"index={chunk['index']} offset={chunk['offset']} "
            f"source={str(chunk['source_sha256'])[:12]} target={str(chunk['target_sha256'])[:12]}"
        )


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

    apply_cmd = subparsers.add_parser(
        "apply",
        help="preview or execute a sync plan that makes a target directory match a source directory",
    )
    apply_cmd.add_argument("source", type=Path)
    apply_cmd.add_argument("target", type=Path)
    apply_cmd.add_argument("--execute", action="store_true", help="apply filesystem changes")
    apply_cmd.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    chunk_diff_cmd = subparsers.add_parser(
        "chunk-diff",
        help="compare two files at the chunk level and emit chunk proofs for changed source chunks",
    )
    chunk_diff_cmd.add_argument("source", type=Path)
    chunk_diff_cmd.add_argument("target", type=Path)
    chunk_diff_cmd.add_argument(
        "--chunk-size", type=int, default=1024, help="bytes per chunk for the file Merkle tree"
    )
    chunk_diff_cmd.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    verify_cmd = subparsers.add_parser(
        "verify-chunk",
        help="verify a single chunk proof against a root digest using a JSON payload",
    )
    verify_cmd.add_argument("proof_json", type=Path, help="JSON file from chunk-diff or build_chunk_proof")
    verify_cmd.add_argument("chunk_index", type=int)

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

    if args.command == "apply":
        source_root = args.source.resolve() if args.source.is_dir() else None
        plan = build_copy_plan(resolve_manifest(args.source), resolve_manifest(args.target))
        try:
            report = apply_plan(plan, source_root=source_root, execute=args.execute)
        except ValueError as exc:
            parser.exit(2, f"error: {exc}\n")
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_human_apply(report)
        return 0

    if args.command == "chunk-diff":
        summary = diff_chunk_proofs(args.source, args.target, chunk_size=args.chunk_size)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print_human_chunk_diff(summary)
        return 0

    if args.command == "verify-chunk":
        payload = load_manifest(args.proof_json)
        chunks = payload.get("chunks") or payload.get("changed_chunks")
        if chunks is None:
            parser.exit(2, "error: proof payload must contain 'chunks' or 'changed_chunks'\n")
        for chunk in chunks:
            if chunk["index"] == args.chunk_index:
                proof = chunk.get("proof") or chunk.get("source_proof") or []
                digest = chunk.get("sha256") or chunk.get("source_sha256")
                root_digest = payload.get("root_digest") or payload.get("source_root_digest")
                if digest is None or root_digest is None:
                    parser.exit(2, "error: proof payload is missing digest fields\n")
                print("valid" if verify_chunk_entry(root_digest, digest, proof) else "invalid")
                return 0
        parser.exit(2, f"error: chunk index {args.chunk_index} not found\n")

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
