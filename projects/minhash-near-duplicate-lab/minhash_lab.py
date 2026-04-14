from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable

MAX_HASH = (1 << 64) - 1
TOKEN_RE = re.compile(r"[a-z0-9']+")


@dataclass(frozen=True)
class SimilarityReport:
    left: str
    right: str
    exact_jaccard: float
    estimated_jaccard: float
    shared_bands: int
    left_shingles: int
    right_shingles: int

    def to_dict(self) -> dict[str, object]:
        return {
            "left": self.left,
            "right": self.right,
            "exact_jaccard": round(self.exact_jaccard, 4),
            "estimated_jaccard": round(self.estimated_jaccard, 4),
            "shared_bands": self.shared_bands,
            "left_shingles": self.left_shingles,
            "right_shingles": self.right_shingles,
        }


def normalize_text(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def build_shingles(text: str, size: int = 3) -> set[str]:
    if size <= 0:
        raise ValueError("shingle size must be positive")
    tokens = normalize_text(text)
    if not tokens:
        return set()
    if len(tokens) < size:
        return {" ".join(tokens)}
    return {" ".join(tokens[index : index + size]) for index in range(len(tokens) - size + 1)}


def _hash_value(shingle: str, salt: int) -> int:
    payload = f"{salt}:{shingle}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def minhash_signature(shingles: set[str], num_hashes: int = 64, seed: int = 0) -> list[int]:
    if num_hashes <= 0:
        raise ValueError("num_hashes must be positive")
    if not shingles:
        return [MAX_HASH] * num_hashes
    signature: list[int] = []
    for offset in range(num_hashes):
        salt = seed + offset
        signature.append(min(_hash_value(shingle, salt) for shingle in shingles))
    return signature


def exact_jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    if not union:
        return 1.0
    return len(left & right) / len(union)


def estimate_jaccard(left_signature: list[int], right_signature: list[int]) -> float:
    if len(left_signature) != len(right_signature):
        raise ValueError("signature lengths must match")
    if not left_signature:
        return 1.0
    matches = sum(1 for left, right in zip(left_signature, right_signature) if left == right)
    return matches / len(left_signature)


def shared_band_count(left_signature: list[int], right_signature: list[int], bands: int) -> int:
    if bands <= 0:
        raise ValueError("bands must be positive")
    if len(left_signature) != len(right_signature):
        raise ValueError("signature lengths must match")
    if len(left_signature) % bands != 0:
        raise ValueError("signature length must be divisible by bands")
    rows = len(left_signature) // bands
    shared = 0
    for band_index in range(bands):
        start = band_index * rows
        end = start + rows
        if left_signature[start:end] == right_signature[start:end]:
            shared += 1
    return shared


def compare_texts(
    left_text: str,
    right_text: str,
    *,
    left_name: str,
    right_name: str,
    shingle_size: int = 3,
    num_hashes: int = 64,
    bands: int = 8,
    seed: int = 0,
) -> SimilarityReport:
    left_shingles = build_shingles(left_text, shingle_size)
    right_shingles = build_shingles(right_text, shingle_size)
    left_signature = minhash_signature(left_shingles, num_hashes=num_hashes, seed=seed)
    right_signature = minhash_signature(right_shingles, num_hashes=num_hashes, seed=seed)
    return SimilarityReport(
        left=left_name,
        right=right_name,
        exact_jaccard=exact_jaccard(left_shingles, right_shingles),
        estimated_jaccard=estimate_jaccard(left_signature, right_signature),
        shared_bands=shared_band_count(left_signature, right_signature, bands),
        left_shingles=len(left_shingles),
        right_shingles=len(right_shingles),
    )


def find_candidate_pairs(
    documents: dict[str, str],
    *,
    shingle_size: int = 3,
    num_hashes: int = 64,
    bands: int = 8,
    threshold: float = 0.5,
    seed: int = 0,
) -> list[SimilarityReport]:
    if len(documents) < 2:
        return []
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if num_hashes % bands != 0:
        raise ValueError("signature length must be divisible by bands")

    shingles_by_doc = {name: build_shingles(text, shingle_size) for name, text in documents.items()}
    signatures = {
        name: minhash_signature(shingles, num_hashes=num_hashes, seed=seed)
        for name, shingles in shingles_by_doc.items()
    }

    rows = num_hashes // bands
    candidate_names: set[tuple[str, str]] = set()
    for band_index in range(bands):
        buckets: dict[str, list[str]] = {}
        start = band_index * rows
        end = start + rows
        for name, signature in signatures.items():
            band = signature[start:end]
            digest = hashlib.sha256(repr(band).encode("utf-8")).hexdigest()
            buckets.setdefault(digest, []).append(name)
        for names in buckets.values():
            if len(names) > 1:
                for pair in combinations(sorted(names), 2):
                    candidate_names.add(pair)

    if not candidate_names and len(documents) <= 50:
        candidate_names = set(combinations(sorted(documents), 2))

    reports: list[SimilarityReport] = []
    for left_name, right_name in sorted(candidate_names):
        report = SimilarityReport(
            left=left_name,
            right=right_name,
            exact_jaccard=exact_jaccard(shingles_by_doc[left_name], shingles_by_doc[right_name]),
            estimated_jaccard=estimate_jaccard(signatures[left_name], signatures[right_name]),
            shared_bands=shared_band_count(signatures[left_name], signatures[right_name], bands),
            left_shingles=len(shingles_by_doc[left_name]),
            right_shingles=len(shingles_by_doc[right_name]),
        )
        if report.estimated_jaccard >= threshold or report.exact_jaccard >= threshold:
            reports.append(report)
    reports.sort(key=lambda item: (item.exact_jaccard, item.estimated_jaccard, item.shared_bands), reverse=True)
    return reports


def load_documents(paths: Iterable[Path]) -> dict[str, str]:
    documents: dict[str, str] = {}
    for path in paths:
        documents[str(path)] = path.read_text(encoding="utf-8")
    return documents


def _collect_paths(root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in root.rglob(pattern) if path.is_file())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MinHash near-duplicate detection lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser("compare", help="compare two files")
    compare_parser.add_argument("left")
    compare_parser.add_argument("right")

    corpus_parser = subparsers.add_parser("corpus", help="scan a directory for near-duplicate documents")
    corpus_parser.add_argument("root")
    corpus_parser.add_argument("--glob", default="*.txt", dest="glob_pattern")
    corpus_parser.add_argument("--threshold", type=float, default=0.5)

    for subparser in (compare_parser, corpus_parser):
        subparser.add_argument("--shingle-size", type=int, default=3)
        subparser.add_argument("--num-hashes", type=int, default=64)
        subparser.add_argument("--bands", type=int, default=8)
        subparser.add_argument("--seed", type=int, default=0)
        subparser.add_argument("--json", action="store_true")

    return parser


def _emit(payload: dict[str, object], as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if payload.get("command") == "compare":
        print(f"Exact Jaccard: {payload['exact_jaccard']:.4f}")
        print(f"Estimated Jaccard: {payload['estimated_jaccard']:.4f}")
        print(f"Shared bands: {payload['shared_bands']}/{payload['bands']}")
        return 0
    pairs = payload.get("pairs", [])
    print(f"Candidate pairs: {len(pairs)}")
    for pair in pairs:
        print(
            f"- {pair['left']} <> {pair['right']} | exact={pair['exact_jaccard']:.4f} "
            f"estimated={pair['estimated_jaccard']:.4f} shared_bands={pair['shared_bands']}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.num_hashes % args.bands != 0:
        parser.error("--num-hashes must be divisible by --bands")

    if args.command == "compare":
        left = Path(args.left)
        right = Path(args.right)
        report = compare_texts(
            left.read_text(encoding="utf-8"),
            right.read_text(encoding="utf-8"),
            left_name=str(left),
            right_name=str(right),
            shingle_size=args.shingle_size,
            num_hashes=args.num_hashes,
            bands=args.bands,
            seed=args.seed,
        )
        return _emit({"command": "compare", "bands": args.bands, **report.to_dict()}, args.json)

    root = Path(args.root)
    paths = _collect_paths(root, args.glob_pattern)
    reports = find_candidate_pairs(
        load_documents(paths),
        shingle_size=args.shingle_size,
        num_hashes=args.num_hashes,
        bands=args.bands,
        threshold=args.threshold,
        seed=args.seed,
    )
    return _emit(
        {
            "command": "corpus",
            "root": str(root),
            "documents_scanned": len(paths),
            "threshold": args.threshold,
            "bands": args.bands,
            "pairs": [report.to_dict() for report in reports],
        },
        args.json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
