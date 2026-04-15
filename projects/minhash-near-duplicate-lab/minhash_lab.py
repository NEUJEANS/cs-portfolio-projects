from __future__ import annotations

import argparse
import csv
import hashlib
import json
import keyword
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Iterable

MAX_HASH = (1 << 64) - 1
TOKEN_RE = re.compile(r"[a-z0-9']+")
CODE_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|!=|<=|>=|//=|\*=|/=|%=|\+=|-=|\*\*|//|->|[{}()\[\].,:;+\-*/%<>=]")
PYTHON_KEYWORDS = set(keyword.kwlist)
INDEX_VERSION = 3


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


@dataclass(frozen=True)
class IndexedDocument:
    path: str
    signature: list[int]
    shingles: list[str]
    shingle_count: int
    byte_length: int
    content_sha256: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SignatureIndex:
    version: int
    created_at: str
    root: str
    glob_pattern: str
    shingle_size: int
    token_mode: str
    normalize_identifiers: bool
    num_hashes: int
    bands: int
    seed: int
    documents: list[IndexedDocument]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "root": self.root,
            "glob_pattern": self.glob_pattern,
            "shingle_size": self.shingle_size,
            "token_mode": self.token_mode,
            "normalize_identifiers": self.normalize_identifiers,
            "num_hashes": self.num_hashes,
            "bands": self.bands,
            "seed": self.seed,
            "documents": [document.to_dict() for document in self.documents],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SignatureIndex":
        if payload.get("version") != INDEX_VERSION:
            raise ValueError(f"unsupported index version: {payload.get('version')}")
        documents_payload = payload.get("documents")
        if not isinstance(documents_payload, list):
            raise ValueError("index documents must be a list")
        documents: list[IndexedDocument] = []
        for item in documents_payload:
            if not isinstance(item, dict):
                raise ValueError("index document entries must be objects")
            documents.append(
                IndexedDocument(
                    path=str(item["path"]),
                    signature=[int(value) for value in item["signature"]],
                    shingles=[str(value) for value in item["shingles"]],
                    shingle_count=int(item["shingle_count"]),
                    byte_length=int(item["byte_length"]),
                    content_sha256=str(item["content_sha256"]),
                )
            )
        return cls(
            version=int(payload["version"]),
            created_at=str(payload["created_at"]),
            root=str(payload["root"]),
            glob_pattern=str(payload["glob_pattern"]),
            shingle_size=int(payload["shingle_size"]),
            token_mode=str(payload.get("token_mode", "word")),
            normalize_identifiers=bool(payload.get("normalize_identifiers", False)),
            num_hashes=int(payload["num_hashes"]),
            bands=int(payload["bands"]),
            seed=int(payload["seed"]),
            documents=documents,
        )


def _normalize_code_token(token: str, *, normalize_identifiers: bool) -> str:
    lowered = token.lower()
    if not normalize_identifiers:
        return lowered
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token) and lowered not in PYTHON_KEYWORDS:
        return "<id>"
    return lowered


def normalize_text(text: str, *, token_mode: str = "word", normalize_identifiers: bool = False) -> list[str]:
    if token_mode == "word":
        return TOKEN_RE.findall(text.lower())
    if token_mode == "code":
        return [_normalize_code_token(token, normalize_identifiers=normalize_identifiers) for token in CODE_TOKEN_RE.findall(text)]
    if token_mode == "char":
        compact = re.sub(r"\s+", " ", text.lower()).strip()
        return list(compact)
    raise ValueError("token mode must be one of: word, code, char")


def build_shingles(text: str, size: int = 3, *, token_mode: str = "word", normalize_identifiers: bool = False) -> set[str]:
    if size <= 0:
        raise ValueError("shingle size must be positive")
    tokens = normalize_text(text, token_mode=token_mode, normalize_identifiers=normalize_identifiers)
    if not tokens:
        return set()
    joiner = "" if token_mode == "char" else " "
    if len(tokens) < size:
        return {joiner.join(tokens)}
    return {joiner.join(tokens[index : index + size]) for index in range(len(tokens) - size + 1)}


def _hash_value(shingle: str, salt: int) -> int:
    payload = f"{salt}:{shingle}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    token_mode: str = "word",
    normalize_identifiers: bool = False,
) -> SimilarityReport:
    left_shingles = build_shingles(left_text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers)
    right_shingles = build_shingles(right_text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers)
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


def _collect_candidate_names(signatures: dict[str, list[int]], bands: int) -> set[tuple[str, str]]:
    if not signatures:
        return set()
    rows = len(next(iter(signatures.values()))) // bands
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
    return candidate_names


def _reports_from_components(
    shingles_by_doc: dict[str, set[str]],
    signatures: dict[str, list[int]],
    *,
    bands: int,
    threshold: float,
    small_corpus_fallback: bool = True,
) -> list[SimilarityReport]:
    candidate_names = _collect_candidate_names(signatures, bands)
    if not candidate_names and small_corpus_fallback and len(shingles_by_doc) <= 50:
        candidate_names = set(combinations(sorted(shingles_by_doc), 2))

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


def find_candidate_pairs(
    documents: dict[str, str],
    *,
    shingle_size: int = 3,
    num_hashes: int = 64,
    bands: int = 8,
    threshold: float = 0.5,
    seed: int = 0,
    token_mode: str = "word",
    normalize_identifiers: bool = False,
) -> list[SimilarityReport]:
    if len(documents) < 2:
        return []
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if num_hashes % bands != 0:
        raise ValueError("signature length must be divisible by bands")

    shingles_by_doc = {
        name: build_shingles(text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers)
        for name, text in documents.items()
    }
    signatures = {
        name: minhash_signature(shingles, num_hashes=num_hashes, seed=seed)
        for name, shingles in shingles_by_doc.items()
    }
    return _reports_from_components(
        shingles_by_doc,
        signatures,
        bands=bands,
        threshold=threshold,
        small_corpus_fallback=True,
    )


def load_documents(paths: Iterable[Path]) -> dict[str, str]:
    documents: dict[str, str] = {}
    for path in paths:
        documents[str(path)] = path.read_text(encoding="utf-8")
    return documents


def _collect_paths(root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in root.rglob(pattern) if path.is_file())


def _indexed_document_from_text(
    path: Path,
    text: str,
    *,
    shingle_size: int,
    token_mode: str,
    normalize_identifiers: bool,
    num_hashes: int,
    seed: int,
) -> IndexedDocument:
    shingles = sorted(build_shingles(text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers))
    return IndexedDocument(
        path=str(path),
        signature=minhash_signature(set(shingles), num_hashes=num_hashes, seed=seed),
        shingles=shingles,
        shingle_count=len(shingles),
        byte_length=len(text.encode("utf-8")),
        content_sha256=_sha256_text(text),
    )


def build_signature_index(
    paths: Iterable[Path],
    *,
    root: Path,
    glob_pattern: str,
    shingle_size: int = 3,
    token_mode: str = "word",
    normalize_identifiers: bool = False,
    num_hashes: int = 64,
    bands: int = 8,
    seed: int = 0,
) -> SignatureIndex:
    documents = [
        _indexed_document_from_text(
            path,
            path.read_text(encoding="utf-8"),
            shingle_size=shingle_size,
            token_mode=token_mode,
            normalize_identifiers=normalize_identifiers,
            num_hashes=num_hashes,
            seed=seed,
        )
        for path in paths
    ]
    return SignatureIndex(
        version=INDEX_VERSION,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        root=str(root),
        glob_pattern=glob_pattern,
        shingle_size=shingle_size,
        token_mode=token_mode,
        normalize_identifiers=normalize_identifiers,
        num_hashes=num_hashes,
        bands=bands,
        seed=seed,
        documents=documents,
    )


def refresh_signature_index(index: SignatureIndex, paths: Iterable[Path]) -> tuple[SignatureIndex, dict[str, int]]:
    existing_by_path = {document.path: document for document in index.documents}
    refreshed_documents: list[IndexedDocument] = []
    reused = 0
    updated = 0
    added = 0
    seen_paths: set[str] = set()

    for path in paths:
        path_str = str(path)
        seen_paths.add(path_str)
        text = path.read_text(encoding="utf-8")
        content_sha256 = _sha256_text(text)
        previous = existing_by_path.get(path_str)
        if previous is not None and previous.content_sha256 == content_sha256:
            refreshed_documents.append(previous)
            reused += 1
            continue
        refreshed_documents.append(
            _indexed_document_from_text(
                path,
                text,
                shingle_size=index.shingle_size,
                token_mode=index.token_mode,
                normalize_identifiers=index.normalize_identifiers,
                num_hashes=index.num_hashes,
                seed=index.seed,
            )
        )
        if previous is None:
            added += 1
        else:
            updated += 1

    removed = sum(1 for path_str in existing_by_path if path_str not in seen_paths)
    refreshed = SignatureIndex(
        version=index.version,
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        root=index.root,
        glob_pattern=index.glob_pattern,
        shingle_size=index.shingle_size,
        token_mode=index.token_mode,
        normalize_identifiers=index.normalize_identifiers,
        num_hashes=index.num_hashes,
        bands=index.bands,
        seed=index.seed,
        documents=refreshed_documents,
    )
    stats = {
        "documents_seen": len(seen_paths),
        "reused": reused,
        "updated": updated,
        "added": added,
        "removed": removed,
    }
    return refreshed, stats


def save_signature_index(index: SignatureIndex, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_signature_index(path: Path) -> SignatureIndex:
    return SignatureIndex.from_dict(json.loads(path.read_text(encoding="utf-8")))


def find_candidate_pairs_from_index(index: SignatureIndex, *, threshold: float = 0.5) -> list[SimilarityReport]:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    shingles_by_doc = {document.path: set(document.shingles) for document in index.documents}
    signatures = {document.path: document.signature for document in index.documents}
    return _reports_from_components(
        shingles_by_doc,
        signatures,
        bands=index.bands,
        threshold=threshold,
        small_corpus_fallback=True,
    )


def benchmark_corpus(
    documents: dict[str, str],
    *,
    shingle_size: int = 3,
    num_hashes: int = 64,
    bands: int = 8,
    threshold: float = 0.5,
    seed: int = 0,
    token_mode: str = "word",
    normalize_identifiers: bool = False,
) -> dict[str, object]:
    if len(documents) < 2:
        raise ValueError("benchmark requires at least two documents")
    if num_hashes % bands != 0:
        raise ValueError("signature length must be divisible by bands")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    build_started = time.perf_counter()
    shingles_by_doc = {
        name: build_shingles(text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers)
        for name, text in documents.items()
    }
    signatures = {
        name: minhash_signature(shingles, num_hashes=num_hashes, seed=seed)
        for name, shingles in shingles_by_doc.items()
    }
    build_seconds = time.perf_counter() - build_started

    all_pairs = list(combinations(sorted(documents), 2))

    band_started = time.perf_counter()
    lsh_candidates = _collect_candidate_names(signatures, bands)
    lsh_seconds = time.perf_counter() - band_started

    exact_started = time.perf_counter()
    exact_matches: set[tuple[str, str]] = set()
    exact_match_reports: list[dict[str, object]] = []
    for left_name, right_name in all_pairs:
        exact_score = exact_jaccard(shingles_by_doc[left_name], shingles_by_doc[right_name])
        if exact_score >= threshold:
            exact_matches.add((left_name, right_name))
            exact_match_reports.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "exact_jaccard": round(exact_score, 4),
                    "estimated_jaccard": round(estimate_jaccard(signatures[left_name], signatures[right_name]), 4),
                    "shared_bands": shared_band_count(signatures[left_name], signatures[right_name], bands),
                }
            )
    exact_seconds = time.perf_counter() - exact_started

    candidate_reports = _reports_from_components(
        shingles_by_doc,
        signatures,
        bands=bands,
        threshold=threshold,
        small_corpus_fallback=False,
    )
    candidate_match_names = {(report.left, report.right) for report in candidate_reports}
    recovered_matches = len(exact_matches & candidate_match_names)

    return {
        "command": "benchmark",
        "documents_scanned": len(documents),
        "shingle_size": shingle_size,
        "token_mode": token_mode,
        "normalize_identifiers": normalize_identifiers,
        "num_hashes": num_hashes,
        "bands": bands,
        "threshold": threshold,
        "seed": seed,
        "all_pairs": len(all_pairs),
        "candidate_pairs": len(lsh_candidates),
        "exact_pairs_above_threshold": len(exact_matches),
        "lsh_pairs_above_threshold": len(candidate_reports),
        "lsh_recall_vs_exact": round(recovered_matches / len(exact_matches), 4) if exact_matches else 1.0,
        "candidate_reduction_ratio": round(1 - (len(lsh_candidates) / len(all_pairs) if all_pairs else 0), 4),
        "timings_seconds": {
            "build_signatures": round(build_seconds, 6),
            "lsh_candidate_generation": round(lsh_seconds, 6),
            "exact_all_pairs_scan": round(exact_seconds, 6),
        },
        "top_exact_pairs": exact_match_reports[:5],
        "top_lsh_pairs": [report.to_dict() for report in candidate_reports[:5]],
    }


def export_benchmark_report(payload: dict[str, object], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix == ".json":
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output_path
    if suffix == ".csv":
        rows = [
            ("documents_scanned", payload["documents_scanned"]),
            ("shingle_size", payload["shingle_size"]),
            ("token_mode", payload["token_mode"]),
            ("normalize_identifiers", payload.get("normalize_identifiers", False)),
            ("num_hashes", payload["num_hashes"]),
            ("bands", payload["bands"]),
            ("threshold", payload["threshold"]),
            ("seed", payload["seed"]),
            ("all_pairs", payload["all_pairs"]),
            ("candidate_pairs", payload["candidate_pairs"]),
            ("exact_pairs_above_threshold", payload["exact_pairs_above_threshold"]),
            ("lsh_pairs_above_threshold", payload["lsh_pairs_above_threshold"]),
            ("lsh_recall_vs_exact", payload["lsh_recall_vs_exact"]),
            ("candidate_reduction_ratio", payload["candidate_reduction_ratio"]),
            ("build_signatures_seconds", payload["timings_seconds"]["build_signatures"]),
            ("lsh_candidate_generation_seconds", payload["timings_seconds"]["lsh_candidate_generation"]),
            ("exact_all_pairs_scan_seconds", payload["timings_seconds"]["exact_all_pairs_scan"]),
        ]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["metric", "value"])
            writer.writerows(rows)
        return output_path
    if suffix == ".md":
        timings = payload["timings_seconds"]
        top_lsh_pairs = payload.get("top_lsh_pairs", [])
        top_exact_pairs = payload.get("top_exact_pairs", [])
        lines = [
            "# MinHash benchmark summary",
            "",
            f"- Documents scanned: {payload['documents_scanned']}",
            f"- Shingle size: {payload['shingle_size']}",
            f"- Token mode: {payload['token_mode']}",
            f"- Normalize identifiers: {payload.get('normalize_identifiers', False)}",
            f"- Signature hashes: {payload['num_hashes']}",
            f"- Bands: {payload['bands']}",
            f"- Threshold: {payload['threshold']}",
            f"- Seed: {payload['seed']}",
            f"- All pairs: {payload['all_pairs']}",
            f"- Candidate pairs: {payload['candidate_pairs']}",
            f"- Exact pairs above threshold: {payload['exact_pairs_above_threshold']}",
            f"- LSH pairs above threshold: {payload['lsh_pairs_above_threshold']}",
            f"- LSH recall vs exact: {payload['lsh_recall_vs_exact']}",
            f"- Candidate reduction ratio: {payload['candidate_reduction_ratio']}",
            "",
            "## Timings",
            "",
            f"- Build signatures: {timings['build_signatures']:.6f}s",
            f"- LSH candidate generation: {timings['lsh_candidate_generation']:.6f}s",
            f"- Exact all-pairs scan: {timings['exact_all_pairs_scan']:.6f}s",
            "",
            "## Top exact matches",
            "",
        ]
        if top_exact_pairs:
            for pair in top_exact_pairs:
                lines.append(
                    f"- {pair['left']} <> {pair['right']} | exact={pair['exact_jaccard']:.4f} estimated={pair['estimated_jaccard']:.4f} shared_bands={pair['shared_bands']}"
                )
        else:
            lines.append("- None")
        lines.extend(["", "## Top LSH matches", ""])
        if top_lsh_pairs:
            for pair in top_lsh_pairs:
                lines.append(
                    f"- {pair['left']} <> {pair['right']} | exact={pair['exact_jaccard']:.4f} estimated={pair['estimated_jaccard']:.4f} shared_bands={pair['shared_bands']}"
                )
        else:
            lines.append("- None")
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path
    raise ValueError("benchmark export path must end with .json, .csv, or .md")


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

    index_parser = subparsers.add_parser("build-index", help="persist MinHash signatures for a corpus")
    index_parser.add_argument("root")
    index_parser.add_argument("output")
    index_parser.add_argument("--glob", default="*.txt", dest="glob_pattern")

    refresh_index_parser = subparsers.add_parser("refresh-index", help="refresh a saved signature index and reuse unchanged documents")
    refresh_index_parser.add_argument("index_path")

    scan_index_parser = subparsers.add_parser("scan-index", help="find candidate pairs from a saved signature index")
    scan_index_parser.add_argument("index_path")
    scan_index_parser.add_argument("--threshold", type=float, default=0.5)

    benchmark_parser = subparsers.add_parser("benchmark", help="benchmark LSH candidate generation vs exact all-pairs scanning")
    benchmark_parser.add_argument("root")
    benchmark_parser.add_argument("--glob", default="*.txt", dest="glob_pattern")
    benchmark_parser.add_argument("--threshold", type=float, default=0.5)
    benchmark_parser.add_argument("--output", help="write benchmark summary to .json, .csv, or .md")

    for subparser in (compare_parser, corpus_parser, index_parser, benchmark_parser):
        subparser.add_argument("--shingle-size", type=int, default=3)
        subparser.add_argument("--token-mode", choices=["word", "code", "char"], default="word")
        subparser.add_argument("--normalize-identifiers", action="store_true", help="collapse non-keyword identifiers in code mode")
        subparser.add_argument("--num-hashes", type=int, default=64)
        subparser.add_argument("--bands", type=int, default=8)
        subparser.add_argument("--seed", type=int, default=0)
        subparser.add_argument("--json", action="store_true")

    refresh_index_parser.add_argument("--json", action="store_true")
    scan_index_parser.add_argument("--json", action="store_true")

    return parser


def _emit(payload: dict[str, object], as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    command = payload.get("command")
    if command == "compare":
        print(f"Exact Jaccard: {payload['exact_jaccard']:.4f}")
        print(f"Estimated Jaccard: {payload['estimated_jaccard']:.4f}")
        print(f"Shared bands: {payload['shared_bands']}/{payload['bands']}")
        return 0
    if command == "build-index":
        print(f"Indexed {payload['documents_indexed']} documents into {payload['output']}")
        return 0
    if command == "refresh-index":
        print(
            f"Refreshed {payload['documents_seen']} documents in {payload['index_path']} "
            f"(reused={payload['reused']}, updated={payload['updated']}, added={payload['added']}, removed={payload['removed']})"
        )
        return 0
    if command == "benchmark":
        print(f"Documents scanned: {payload['documents_scanned']}")
        print(f"All pairs: {payload['all_pairs']}")
        print(f"LSH candidate pairs: {payload['candidate_pairs']}")
        print(f"Exact pairs above threshold: {payload['exact_pairs_above_threshold']}")
        print(f"LSH pairs above threshold: {payload['lsh_pairs_above_threshold']}")
        print(f"LSH recall vs exact: {payload['lsh_recall_vs_exact']:.4f}")
        timings = payload["timings_seconds"]
        print(
            "Timing seconds: "
            f"build={timings['build_signatures']:.6f}, "
            f"lsh={timings['lsh_candidate_generation']:.6f}, "
            f"exact={timings['exact_all_pairs_scan']:.6f}"
        )
        if payload.get('output'):
            print(f"Saved report: {payload['output']}")
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

    if getattr(args, "command", None) in {"compare", "corpus", "build-index", "benchmark"}:
        if args.num_hashes % args.bands != 0:
            parser.error("--num-hashes must be divisible by --bands")
        if args.normalize_identifiers and args.token_mode != "code":
            parser.error("--normalize-identifiers requires --token-mode code")

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
            token_mode=args.token_mode,
            normalize_identifiers=args.normalize_identifiers,
        )
        return _emit(
            {
                "command": "compare",
                "bands": args.bands,
                "token_mode": args.token_mode,
                "normalize_identifiers": args.normalize_identifiers,
                **report.to_dict(),
            },
            args.json,
        )

    if args.command == "corpus":
        root = Path(args.root)
        paths = _collect_paths(root, args.glob_pattern)
        reports = find_candidate_pairs(
            load_documents(paths),
            shingle_size=args.shingle_size,
            num_hashes=args.num_hashes,
            bands=args.bands,
            threshold=args.threshold,
            seed=args.seed,
            token_mode=args.token_mode,
            normalize_identifiers=args.normalize_identifiers,
        )
        return _emit(
            {
                "command": "corpus",
                "root": str(root),
                "documents_scanned": len(paths),
                "threshold": args.threshold,
                "bands": args.bands,
                "token_mode": args.token_mode,
                "normalize_identifiers": args.normalize_identifiers,
                "pairs": [report.to_dict() for report in reports],
            },
            args.json,
        )

    if args.command == "build-index":
        root = Path(args.root)
        paths = _collect_paths(root, args.glob_pattern)
        index = build_signature_index(
            paths,
            root=root,
            glob_pattern=args.glob_pattern,
            shingle_size=args.shingle_size,
            token_mode=args.token_mode,
            normalize_identifiers=args.normalize_identifiers,
            num_hashes=args.num_hashes,
            bands=args.bands,
            seed=args.seed,
        )
        output = Path(args.output)
        save_signature_index(index, output)
        return _emit(
            {
                "command": "build-index",
                "output": str(output),
                "documents_indexed": len(index.documents),
                "bands": index.bands,
                "token_mode": index.token_mode,
                "normalize_identifiers": index.normalize_identifiers,
                "num_hashes": index.num_hashes,
                "shingle_size": index.shingle_size,
            },
            args.json,
        )

    if args.command == "refresh-index":
        index_path = Path(args.index_path)
        index = load_signature_index(index_path)
        paths = _collect_paths(Path(index.root), index.glob_pattern)
        refreshed_index, stats = refresh_signature_index(index, paths)
        save_signature_index(refreshed_index, index_path)
        return _emit(
            {
                "command": "refresh-index",
                "index_path": str(index_path),
                "token_mode": index.token_mode,
                "normalize_identifiers": index.normalize_identifiers,
                **stats,
            },
            args.json,
        )

    if args.command == "scan-index":
        index = load_signature_index(Path(args.index_path))
        reports = find_candidate_pairs_from_index(index, threshold=args.threshold)
        return _emit(
            {
                "command": "scan-index",
                "index_path": args.index_path,
                "documents_scanned": len(index.documents),
                "threshold": args.threshold,
                "bands": index.bands,
                "token_mode": index.token_mode,
                "normalize_identifiers": index.normalize_identifiers,
                "pairs": [report.to_dict() for report in reports],
            },
            args.json,
        )

    if args.command == "benchmark":
        root = Path(args.root)
        paths = _collect_paths(root, args.glob_pattern)
        payload = benchmark_corpus(
            load_documents(paths),
            shingle_size=args.shingle_size,
            num_hashes=args.num_hashes,
            bands=args.bands,
            threshold=args.threshold,
            seed=args.seed,
            token_mode=args.token_mode,
            normalize_identifiers=args.normalize_identifiers,
        )
        if args.output:
            output_path = export_benchmark_report(payload, Path(args.output))
            payload = {**payload, "output": str(output_path)}
        return _emit(payload, args.json)

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
