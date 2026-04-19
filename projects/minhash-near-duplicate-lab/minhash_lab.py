from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import keyword
import os
import re
import shlex
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Iterable

MAX_HASH = (1 << 64) - 1
TOKEN_RE = re.compile(r"[a-z0-9']+")
CODE_TOKEN_RE = re.compile(
    r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|[A-Za-z_][A-Za-z0-9_]*|(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+|\d+|==|!=|<=|>=|//=|\*=|/=|%=|\+=|-=|\*\*|//|->|[{}()\[\].,:;+\-*/%<>=]"
)
INTEGER_LITERAL_RE = re.compile(r"\d+")
FLOAT_LITERAL_RE = re.compile(r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+")
STRING_LITERAL_RE = re.compile(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"")
BOOLEAN_LITERAL_TOKENS = {"true", "false"}
NONE_LITERAL_TOKEN = "none"
PYTHON_KEYWORDS = set(keyword.kwlist)
INDEX_VERSION = 5

PRESET_CORPORA: dict[str, dict[str, str]] = {
    "mixed-markdown-code-notebook": {
        "README.md": "# Graph search notes\n\nBreadth-first search explores neighbors level by level and keeps a queue.\n",
        "portfolio_reflection.md": "# BFS study guide\n\nBreadth-first search visits nodes layer by layer, stores the frontier in a queue, and finds shortest unweighted paths.\n",
        "bfs_queue.py": "from collections import deque\n\n\ndef bfs_layers(graph, start):\n    queue = deque([(start, 0)])\n    seen = {start}\n    order = []\n    while queue:\n        node, depth = queue.popleft()\n        order.append((node, depth))\n        for neighbor in graph.get(node, []):\n            if neighbor not in seen:\n                seen.add(neighbor)\n                queue.append((neighbor, depth + 1))\n    return order\n",
        "bfs_variant.py": "from collections import deque\n\n\ndef breadth_first_layers(adj, source):\n    pending = deque([(source, 0)])\n    visited = {source}\n    trace = []\n    while pending:\n        vertex, level = pending.popleft()\n        trace.append((vertex, level))\n        for nxt in adj.get(vertex, []):\n            if nxt not in visited:\n                visited.add(nxt)\n                pending.append((nxt, level + 1))\n    return trace\n",
        "bfs_demo.ipynb": json.dumps({
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "# BFS notebook demo\n",
                        "Breadth-first search expands the frontier level by level with a queue.\n",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "from collections import deque\n",
                        "def bfs_path(graph, start):\n",
                        "    queue = deque([start])\n",
                        "    seen = {start}\n",
                        "    order = []\n",
                        "    while queue:\n",
                        "        node = queue.popleft()\n",
                        "        order.append(node)\n",
                        "        for neighbor in graph.get(node, []):\n",
                        "            if neighbor not in seen:\n",
                        "                seen.add(neighbor)\n",
                        "                queue.append(neighbor)\n",
                        "    return order\n",
                    ],
                },
            ],
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python", "version": "3.12"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }, indent=2) + "\n",
        "distant_topic.md": "# Different topic\n\nBalanced binary search trees rebalance inserts with rotations instead of using a queue frontier.\n",
    },
    "data-science-feature-pipeline": {
        "README.md": "# Feature engineering notes\n\nWe standardize numeric features, cap outliers, and keep a reproducible pipeline for training demos.\n",
        "feature_pipeline.py": "def normalize_rows(rows):\n    cleaned = []\n    for row in rows:\n        clicks = min(row['clicks'], 500) / 500\n        dwell = min(row['dwell_seconds'], 300) / 300\n        cleaned.append({'click_rate': clicks, 'dwell_rate': dwell, 'converted': row['converted']})\n    return cleaned\n",
        "feature_pipeline_variant.py": "def build_features(events):\n    normalized = []\n    for sample in events:\n        click_ratio = min(sample['clicks'], 500) / 500\n        watch_ratio = min(sample['dwell_seconds'], 300) / 300\n        normalized.append({'click_rate': click_ratio, 'dwell_rate': watch_ratio, 'converted': sample['converted']})\n    return normalized\n",
        "experiment_notes.md": "# Experiment notes\n\nThe pipeline trims large click spikes, rescales dwell time, and preserves the conversion label for modeling.\n",
        "feature_demo.ipynb": json.dumps({
            "cells": [
                {"cell_type": "markdown", "metadata": {}, "source": ["# Feature pipeline demo\n", "Notebook version of the same preprocessing steps for portfolio screenshots.\n"]},
                {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["def engineer_features(rows):\n", "    output = []\n", "    for row in rows:\n", "        click_rate = min(row['clicks'], 500) / 500\n", "        dwell_rate = min(row['dwell_seconds'], 300) / 300\n", "        output.append({'click_rate': click_rate, 'dwell_rate': dwell_rate, 'converted': row['converted']})\n", "    return output\n"]},
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3.12"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }, indent=2) + "\n",
        "outlier_memo.md": "# Different topic\n\nDecision trees can absorb raw thresholds directly without emphasizing the exact same scaling story.\n",
    },
    "systems-churn-reconciliation": {
        "README.md": "# Replica reconciliation notes\n\nA storage replica tracks WAL offsets, detects lag, and schedules catch-up work after a failover.\n",
        "replica_sync.py": "def reconciliation_plan(status_rows):\n    actions = []\n    for row in status_rows:\n        lag = max(row['leader_offset'] - row['replica_offset'], 0)\n        if lag == 0:\n            actions.append((row['node'], 'healthy'))\n        elif lag < 128:\n            actions.append((row['node'], 'stream'))\n        else:\n            actions.append((row['node'], 'snapshot'))\n    return actions\n",
        "replica_sync_variant.py": "def catchup_actions(nodes):\n    plan = []\n    for item in nodes:\n        lag = max(item['leader_offset'] - item['replica_offset'], 0)\n        if lag == 0:\n            plan.append((item['node'], 'healthy'))\n        elif lag < 128:\n            plan.append((item['node'], 'stream'))\n        else:\n            plan.append((item['node'], 'snapshot'))\n    return plan\n",
        "runbook.md": "# Replica lag runbook\n\nHealthy replicas keep up with the leader log, small lag streams missing entries, and large lag falls back to snapshot restore.\n",
        "incident_timeline.md": "# Incident timeline\n\nNode blue recovered by replaying missing WAL segments before requesting a full snapshot.\n",
        "lag_demo.json": json.dumps({
            "nodes": [
                {"node": "blue", "leader_offset": 1024, "replica_offset": 1001},
                {"node": "green", "leader_offset": 1024, "replica_offset": 740}
            ]
        }, indent=2) + "\n",
        "different_domain.md": "# Different topic\n\nBrowser layout thrashing and paint timing do not describe replica catch-up planning.\n",
    },
    "web-dev-component-clones": {
        "README.md": "# Dashboard component notes\n\nThis preset mimics a frontend portfolio where React dashboard cards, hooks, and notes drift into near-duplicate variants over time.\n",
        "dashboard_story.md": "# Dashboard refactor story\n\nA product metrics card and an engagement summary card share the same KPI, delta, and card-layout structure with only label-level edits.\n",
        "user_stats_card.tsx": "type MetricsCardProps = { title: string; value: string; deltaLabel: string; trend: 'up' | 'down' };\n\nexport function UserStatsCard({ title, value, deltaLabel, trend }: MetricsCardProps) {\n  const trendClass = trend === 'up' ? 'trendUp' : 'trendDown';\n  return (\n    <section className=\"cardShell\">\n      <header className=\"cardHeader\">\n        <h3>{title}</h3>\n        <span className={trendClass}>{deltaLabel}</span>\n      </header>\n      <strong className=\"metricValue\">{value}</strong>\n      <p className=\"metricCaption\">Updated from the latest dashboard snapshot.</p>\n    </section>\n  );\n}\n",
        "engagement_summary_card.tsx": "type SummaryCardProps = { heading: string; total: string; changeText: string; direction: 'up' | 'down' };\n\nexport function EngagementSummaryCard({ heading, total, changeText, direction }: SummaryCardProps) {\n  const directionClass = direction === 'up' ? 'trendUp' : 'trendDown';\n  return (\n    <section className=\"cardShell\">\n      <header className=\"cardHeader\">\n        <h3>{heading}</h3>\n        <span className={directionClass}>{changeText}</span>\n      </header>\n      <strong className=\"metricValue\">{total}</strong>\n      <p className=\"metricCaption\">Refreshed from the newest analytics snapshot.</p>\n    </section>\n  );\n}\n",
        "use_user_metrics.ts": "export type MetricPoint = { current: number; previous: number };\n\nexport function buildUserMetricsSummary(point: MetricPoint) {\n  const delta = point.current - point.previous;\n  const direction = delta >= 0 ? 'up' : 'down';\n  const percent = point.previous === 0 ? 100 : Math.round((delta / point.previous) * 100);\n  return {\n    value: point.current.toLocaleString(),\n    deltaLabel: `${percent}% vs last week`,\n    direction,\n  };\n}\n",
        "use_engagement_metrics.ts": "export type EngagementPoint = { current: number; previous: number };\n\nexport function buildEngagementSummary(point: EngagementPoint) {\n  const delta = point.current - point.previous;\n  const direction = delta >= 0 ? 'up' : 'down';\n  const percent = point.previous === 0 ? 100 : Math.round((delta / point.previous) * 100);\n  return {\n    total: point.current.toLocaleString(),\n    changeText: `${percent}% vs last week`,\n    direction,\n  };\n}\n",
        "card-shell.css": ".cardShell {\n  border-radius: 16px;\n  padding: 16px;\n  background: linear-gradient(180deg, #111827, #1f2937);\n  color: #f9fafb;\n}\n\n.cardHeader {\n  display: flex;\n  justify-content: space-between;\n  align-items: baseline;\n}\n\n.metricValue {\n  display: block;\n  font-size: 2rem;\n}\n\n.metricCaption {\n  color: #cbd5e1;\n}\n",
        "different_domain.md": "# Different topic\n\nA CPU scheduler trace explains quantum expiration and context switches rather than duplicated dashboard components.\n",
    },
}

PRESET_SCAN_CONFIGS: dict[str, dict[str, object]] = {
    "mixed-markdown-code-notebook": {
        "title": "Mixed Markdown, code, and notebook MinHash preset",
        "story": "A graph-search study bundle that intentionally duplicates the BFS story across Markdown, Python, and notebook files.",
        "glob_pattern": "*.md,*.py,*.ipynb",
        "token_mode": "code",
        "normalize_identifiers": True,
        "normalize_literals": True,
        "shingle_size": 4,
        "num_hashes": 64,
        "bands": 8,
        "threshold": 0.2,
    },
    "data-science-feature-pipeline": {
        "title": "Data-science feature pipeline MinHash preset",
        "story": "A feature-engineering portfolio pack with cloned preprocessing logic spread across Python, Markdown, and notebook artifacts.",
        "glob_pattern": "*.md,*.py,*.ipynb",
        "token_mode": "code",
        "normalize_identifiers": True,
        "normalize_literals": False,
        "shingle_size": 4,
        "num_hashes": 64,
        "bands": 8,
        "threshold": 0.15,
    },
    "systems-churn-reconciliation": {
        "title": "Systems reconciliation MinHash preset",
        "story": "A replica-lag and WAL catch-up corpus with code, runbook, and incident-story near-duplicates for systems design demos.",
        "glob_pattern": "*.md,*.py,*.json",
        "token_mode": "code",
        "normalize_identifiers": True,
        "normalize_literals": False,
        "shingle_size": 3,
        "num_hashes": 64,
        "bands": 8,
        "threshold": 0.15,
    },
    "web-dev-component-clones": {
        "title": "Web-dev component clone MinHash preset",
        "story": "A frontend-heavy portfolio preset that highlights duplicated dashboard cards, hooks, notes, and CSS assets.",
        "glob_pattern": "*.md,*.tsx,*.ts,*.css",
        "token_mode": "code",
        "normalize_identifiers": True,
        "normalize_literals": True,
        "shingle_size": 4,
        "num_hashes": 64,
        "bands": 8,
        "threshold": 0.15,
    },
}

PRESET_DISPLAY_ORDER = list(PRESET_CORPORA)
PRESET_ORDER_INDEX = {name: index for index, name in enumerate(PRESET_DISPLAY_ORDER)}


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
    normalize_literals: bool
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
            "normalize_literals": self.normalize_literals,
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
            normalize_literals=bool(payload.get("normalize_literals", False)),
            num_hashes=int(payload["num_hashes"]),
            bands=int(payload["bands"]),
            seed=int(payload["seed"]),
            documents=documents,
        )


def _normalize_code_token(token: str, *, normalize_identifiers: bool, normalize_literals: bool) -> str:
    lowered = token.lower()
    if normalize_literals:
        if STRING_LITERAL_RE.fullmatch(token):
            return "<str>"
        if FLOAT_LITERAL_RE.fullmatch(token):
            return "<float>"
        if INTEGER_LITERAL_RE.fullmatch(token):
            return "<num>"
        if lowered in BOOLEAN_LITERAL_TOKENS:
            return "<bool>"
        if lowered == NONE_LITERAL_TOKEN:
            return "<none>"
    if normalize_identifiers and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token) and lowered not in PYTHON_KEYWORDS:
        return "<id>"
    return lowered


def normalize_text(text: str, *, token_mode: str = "word", normalize_identifiers: bool = False, normalize_literals: bool = False) -> list[str]:
    if token_mode == "word":
        return TOKEN_RE.findall(text.lower())
    if token_mode == "code":
        return [
            _normalize_code_token(
                token,
                normalize_identifiers=normalize_identifiers,
                normalize_literals=normalize_literals,
            )
            for token in CODE_TOKEN_RE.findall(text)
        ]
    if token_mode == "char":
        compact = re.sub(r"\s+", " ", text.lower()).strip()
        return list(compact)
    raise ValueError("token mode must be one of: word, code, char")


def build_shingles(
    text: str,
    size: int = 3,
    *,
    token_mode: str = "word",
    normalize_identifiers: bool = False,
    normalize_literals: bool = False,
) -> set[str]:
    if size <= 0:
        raise ValueError("shingle size must be positive")
    tokens = normalize_text(
        text,
        token_mode=token_mode,
        normalize_identifiers=normalize_identifiers,
        normalize_literals=normalize_literals,
    )
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
    normalize_literals: bool = False,
) -> SimilarityReport:
    left_shingles = build_shingles(left_text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers, normalize_literals=normalize_literals)
    right_shingles = build_shingles(right_text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers, normalize_literals=normalize_literals)
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
    normalize_literals: bool = False,
) -> list[SimilarityReport]:
    if len(documents) < 2:
        return []
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if num_hashes % bands != 0:
        raise ValueError("signature length must be divisible by bands")

    shingles_by_doc = {
        name: build_shingles(text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers, normalize_literals=normalize_literals)
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


def _split_glob_patterns(patterns: str) -> list[str]:
    values = [part.strip() for part in patterns.split(",") if part.strip()]
    if not values:
        raise ValueError("glob pattern must not be empty")
    return values


def _collect_paths(root: Path, pattern: str) -> list[Path]:
    seen: dict[str, Path] = {}
    for item in _split_glob_patterns(pattern):
        for path in root.rglob(item):
            if path.is_file():
                seen[str(path)] = path
    return [seen[key] for key in sorted(seen)]


def write_preset_corpus(preset_name: str, destination: Path, *, force: bool = False) -> list[Path]:
    if preset_name not in PRESET_CORPORA:
        raise ValueError(f"unknown preset: {preset_name}")
    files = PRESET_CORPORA[preset_name]
    existing = [destination / relative for relative in files if (destination / relative).exists()]
    if existing and not force:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"destination already contains preset files: {joined}")
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for relative, content in files.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return sorted(written)


def _preset_scan_command(preset_name: str) -> str:
    config = PRESET_SCAN_CONFIGS[preset_name]
    command = [
        "python3",
        "projects/minhash-near-duplicate-lab/minhash_lab.py",
        "corpus",
        "<preset-root>",
        "--glob",
        str(config["glob_pattern"]),
        "--token-mode",
        str(config["token_mode"]),
        "--shingle-size",
        str(config["shingle_size"]),
        "--num-hashes",
        str(config["num_hashes"]),
        "--bands",
        str(config["bands"]),
        "--threshold",
        str(config["threshold"]),
    ]
    if config.get("normalize_identifiers"):
        command.append("--normalize-identifiers")
    if config.get("normalize_literals"):
        command.append("--normalize-literals")
    command.append("--json")
    return " ".join(shlex.quote(part) for part in command)


def _compact_preview(text: str) -> str:
    compact = " ".join(text.split())
    if len(compact) <= 120:
        return compact
    return compact[:117] + "..."


def _preview_text_for_bundle(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".ipynb":
        try:
            notebook = json.loads(text)
            for cell in notebook.get("cells", []):
                source = cell.get("source", [])
                if isinstance(source, str):
                    preview = _compact_preview(source.strip())
                    if preview:
                        return preview
                if isinstance(source, list):
                    preview = _compact_preview(" ".join(str(item).strip() for item in source if str(item).strip()))
                    if preview:
                        return preview
        except json.JSONDecodeError:
            pass
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return _compact_preview(stripped)
    return "(empty file)"


def _preset_file_cards(written: Iterable[Path], destination: Path) -> list[dict[str, object]]:
    cards: list[dict[str, object]] = []
    for path in sorted(written):
        relative = path.relative_to(destination).as_posix()
        cards.append(
            {
                "path": relative,
                "suffix": path.suffix.lower() or "<none>",
                "bytes": path.stat().st_size,
                "preview": _preview_text_for_bundle(path),
            }
        )
    return cards


def _extension_counts(cards: Iterable[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for card in cards:
        suffix = str(card["suffix"])
        counts[suffix] = counts.get(suffix, 0) + 1
    return {suffix: counts[suffix] for suffix in sorted(counts)}


def _select_bundle_scan_paths(written: Iterable[Path], destination: Path, glob_pattern: str) -> list[Path]:
    patterns = _split_glob_patterns(glob_pattern)
    selected: list[Path] = []
    for path in sorted(written):
        relative = path.relative_to(destination)
        if any(relative.match(pattern) for pattern in patterns):
            selected.append(path)
    return selected


def build_preset_artifact_bundle(preset_name: str, destination: Path, written: Iterable[Path]) -> dict[str, object]:
    if preset_name not in PRESET_SCAN_CONFIGS:
        raise ValueError(f"missing scan config for preset: {preset_name}")
    config = PRESET_SCAN_CONFIGS[preset_name]
    written_paths = sorted(written)
    cards = _preset_file_cards(written_paths, destination)
    scan_paths = _select_bundle_scan_paths(written_paths, destination, str(config["glob_pattern"]))
    documents = {
        path.relative_to(destination).as_posix(): path.read_text(encoding="utf-8")
        for path in scan_paths
    }
    reports = find_candidate_pairs(
        documents,
        shingle_size=int(config["shingle_size"]),
        num_hashes=int(config["num_hashes"]),
        bands=int(config["bands"]),
        threshold=float(config["threshold"]),
        token_mode=str(config["token_mode"]),
        normalize_identifiers=bool(config.get("normalize_identifiers", False)),
        normalize_literals=bool(config.get("normalize_literals", False)),
    )
    top_pairs = [report.to_dict() for report in reports[:8]]
    return {
        "preset_name": preset_name,
        "title": str(config["title"]),
        "story": str(config["story"]),
        "files_written": len(written_paths),
        "pairs_detected": len(reports),
        "extensions": _extension_counts(cards),
        "recommended_scan": {
            "glob_pattern": str(config["glob_pattern"]),
            "token_mode": str(config["token_mode"]),
            "normalize_identifiers": bool(config.get("normalize_identifiers", False)),
            "normalize_literals": bool(config.get("normalize_literals", False)),
            "shingle_size": int(config["shingle_size"]),
            "num_hashes": int(config["num_hashes"]),
            "bands": int(config["bands"]),
            "threshold": float(config["threshold"]),
            "command": _preset_scan_command(preset_name),
        },
        "files": cards,
        "top_pairs": top_pairs,
    }


def _preset_bundle_markdown(payload: dict[str, object]) -> str:
    scan = payload["recommended_scan"]
    lines = [
        f"# {payload['title']}",
        "",
        str(payload["story"]),
        "",
        f"- Preset key: `{payload['preset_name']}`",
        f"- Files written: {payload['files_written']}",
        f"- Extensions: {', '.join(f'{suffix}={count}' for suffix, count in payload['extensions'].items())}",
        f"- Pairs detected at the recommended threshold: {payload['pairs_detected']}",
        f"- Recommended glob: `{scan['glob_pattern']}`",
        f"- Token mode: `{scan['token_mode']}`",
        f"- Normalize identifiers: `{scan['normalize_identifiers']}`",
        f"- Normalize literals: `{scan['normalize_literals']}`",
        f"- Shingle size: `{scan['shingle_size']}` | Hashes: `{scan['num_hashes']}` | Bands: `{scan['bands']}` | Threshold: `{scan['threshold']}`",
        "",
        "## Suggested scan command",
        "",
        "```bash",
        str(scan["command"]),
        "```",
        "",
        "## File cards",
        "",
    ]
    for card in payload["files"]:
        lines.extend(
            [
                f"### `{card['path']}`",
                f"- Type: `{card['suffix']}`",
                f"- Bytes: `{card['bytes']}`",
                f"- Preview: {card['preview']}",
                "",
            ]
        )
    lines.extend(["## Top near-duplicate pairs", ""])
    pairs = payload["top_pairs"]
    if pairs:
        for pair in pairs:
            lines.append(
                f"- `{pair['left']}` <> `{pair['right']}` | exact={pair['exact_jaccard']:.4f} estimated={pair['estimated_jaccard']:.4f} shared_bands={pair['shared_bands']}"
            )
    else:
        lines.append("- None above the recommended threshold yet.")
    lines.append("")
    return "\n".join(lines)


def _preset_bundle_html(payload: dict[str, object]) -> str:
    scan = payload["recommended_scan"]
    file_cards = "\n".join(
        (
            "<article class=\"card\">"
            f"<h3>{html.escape(str(card['path']))}</h3>"
            f"<p class=\"meta\">{html.escape(str(card['suffix']))} · {card['bytes']} bytes</p>"
            f"<p>{html.escape(str(card['preview']))}</p>"
            "</article>"
        )
        for card in payload["files"]
    )
    pairs = payload["top_pairs"]
    pair_cards = "\n".join(
        (
            "<article class=\"card pair\">"
            f"<h3>{html.escape(str(pair['left']))} ↔ {html.escape(str(pair['right']))}</h3>"
            f"<p class=\"meta\">exact={pair['exact_jaccard']:.4f} · estimated={pair['estimated_jaccard']:.4f} · shared bands={pair['shared_bands']}</p>"
            "</article>"
        )
        for pair in pairs
    ) or "<article class=\"card pair\"><h3>No pairs yet</h3><p class=\"meta\">Nothing crossed the recommended threshold.</p></article>"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>{html.escape(str(payload['title']))}</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 48px; }}
    h1, h2, h3 {{ margin-top: 0; }}
    .hero, .panel {{ background: #111827; border: 1px solid #334155; border-radius: 18px; padding: 20px; margin-bottom: 20px; box-shadow: 0 14px 32px rgba(15, 23, 42, 0.28); }}
    .grid {{ display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
    .card {{ background: linear-gradient(180deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98)); border-radius: 16px; padding: 16px; border: 1px solid #334155; min-height: 150px; }}
    .meta {{ color: #93c5fd; font-size: 0.95rem; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #020617; padding: 14px; border-radius: 12px; border: 1px solid #1e293b; }}
    ul {{ padding-left: 20px; }}
  </style>
</head>
<body>
  <main>
    <section class=\"hero\">
      <h1>{html.escape(str(payload['title']))}</h1>
      <p>{html.escape(str(payload['story']))}</p>
      <ul>
        <li>Preset key: <code>{html.escape(str(payload['preset_name']))}</code></li>
        <li>Files written: <strong>{payload['files_written']}</strong></li>
        <li>Pairs detected at the recommended threshold: <strong>{payload['pairs_detected']}</strong></li>
        <li>Extensions: {html.escape(', '.join(f'{suffix}={count}' for suffix, count in payload['extensions'].items()))}</li>
      </ul>
    </section>
    <section class=\"panel\">
      <h2>Suggested scan command</h2>
      <pre>{html.escape(str(scan['command']))}</pre>
    </section>
    <section class=\"panel\">
      <h2>Preset file cards</h2>
      <div class=\"grid\">{file_cards}</div>
    </section>
    <section class=\"panel\">
      <h2>Top near-duplicate pairs</h2>
      <div class=\"grid\">{pair_cards}</div>
    </section>
  </main>
</body>
</html>
"""


def write_preset_artifact_bundle(preset_name: str, destination: Path, bundle_dir: Path, written: Iterable[Path]) -> dict[str, object]:
    payload = build_preset_artifact_bundle(preset_name, destination, written)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    summary_json = bundle_dir / "preset-bundle-summary.json"
    summary_md = bundle_dir / "preset-bundle-summary.md"
    gallery_html = bundle_dir / "preset-gallery.html"
    summary_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_md.write_text(_preset_bundle_markdown(payload) + "\n", encoding="utf-8")
    gallery_html.write_text(_preset_bundle_html(payload), encoding="utf-8")
    return {
        "directory": str(bundle_dir),
        "summary_json": str(summary_json),
        "summary_md": str(summary_md),
        "gallery_html": str(gallery_html),
        "pairs_detected": payload["pairs_detected"],
        "files_written": payload["files_written"],
        "recommended_command": payload["recommended_scan"]["command"],
    }


def _landing_relative_path(target: Path, base_dir: Path) -> str:
    return Path(os.path.relpath(target.resolve(), start=base_dir.resolve())).as_posix()


def _load_bundle_summary(summary_path: Path) -> dict[str, object]:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"bundle summary must contain an object: {summary_path}")
    if "preset_name" not in payload:
        raise ValueError(f"bundle summary missing preset_name: {summary_path}")
    return payload


def build_preset_bundle_landing(summary_paths: Iterable[Path], output_dir: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for summary_path in sorted(summary_paths):
        payload = _load_bundle_summary(summary_path)
        preset_name = str(payload["preset_name"])
        bundle_dir = summary_path.parent
        summary_md = bundle_dir / "preset-bundle-summary.md"
        gallery_html = bundle_dir / "preset-gallery.html"
        top_pairs = payload.get("top_pairs", [])
        top_pair = top_pairs[0] if isinstance(top_pairs, list) and top_pairs else None
        recommended_scan = payload.get("recommended_scan", {})
        if not isinstance(recommended_scan, dict):
            raise ValueError(f"recommended_scan must be an object: {summary_path}")
        entries.append(
            {
                "preset_name": preset_name,
                "title": str(payload.get("title", preset_name)),
                "story": str(payload.get("story", "")),
                "files_written": int(payload.get("files_written", 0)),
                "pairs_detected": int(payload.get("pairs_detected", 0)),
                "extensions": payload.get("extensions", {}),
                "recommended_scan": recommended_scan,
                "summary_json": _landing_relative_path(summary_path, output_dir),
                "summary_md": _landing_relative_path(summary_md, output_dir),
                "gallery_html": _landing_relative_path(gallery_html, output_dir),
                "top_pair": top_pair,
            }
        )
    if not entries:
        raise ValueError("no preset bundle summaries found")
    entries.sort(key=lambda entry: (PRESET_ORDER_INDEX.get(str(entry["preset_name"]), len(PRESET_ORDER_INDEX)), str(entry["preset_name"])))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "preset_count": len(entries),
        "preset_names": [entry["preset_name"] for entry in entries],
        "total_files_written": sum(int(entry["files_written"]) for entry in entries),
        "total_pairs_detected": sum(int(entry["pairs_detected"]) for entry in entries),
        "presets": entries,
    }


def _preset_landing_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# MinHash preset bundle landing page",
        "",
        "A side-by-side landing page for the curated mixed-language, data-science, systems, and web-dev MinHash demo bundles.",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Presets compared: {payload['preset_count']}",
        f"- Total files across bundles: {payload['total_files_written']}",
        f"- Total near-duplicate pairs across bundles: {payload['total_pairs_detected']}",
        "",
        "## Preset comparison cards",
        "",
    ]
    for entry in payload["presets"]:
        scan = entry["recommended_scan"]
        extensions = entry["extensions"]
        extension_summary = ", ".join(f"{suffix}={count}" for suffix, count in sorted(extensions.items())) if isinstance(extensions, dict) else "n/a"
        lines.extend(
            [
                f"### {entry['title']}",
                "",
                str(entry["story"]),
                "",
                f"- Preset key: `{entry['preset_name']}`",
                f"- Files written: {entry['files_written']}",
                f"- Pairs detected: {entry['pairs_detected']}",
                f"- Extensions: {extension_summary}",
                f"- Recommended glob: `{scan.get('glob_pattern', 'n/a')}`",
                f"- Token mode: `{scan.get('token_mode', 'n/a')}` | normalize identifiers: `{scan.get('normalize_identifiers', False)}` | normalize literals: `{scan.get('normalize_literals', False)}`",
                f"- Suggested command: `{scan.get('command', 'n/a')}`",
                f"- Bundle links: [summary json]({entry['summary_json']}), [summary md]({entry['summary_md']}), [gallery html]({entry['gallery_html']})",
            ]
        )
        top_pair = entry.get("top_pair")
        if isinstance(top_pair, dict):
            lines.append(
                f"- Top pair: `{top_pair['left']}` <> `{top_pair['right']}` | exact={top_pair['exact_jaccard']:.4f} estimated={top_pair['estimated_jaccard']:.4f}"
            )
        else:
            lines.append("- Top pair: none above the recommended threshold yet")
        lines.append("")
    return "\n".join(lines)


def _preset_landing_html(payload: dict[str, object]) -> str:
    cards = []
    for entry in payload["presets"]:
        scan = entry["recommended_scan"]
        extensions = entry["extensions"]
        extension_summary = ", ".join(f"{suffix}={count}" for suffix, count in sorted(extensions.items())) if isinstance(extensions, dict) else "n/a"
        top_pair = entry.get("top_pair")
        if isinstance(top_pair, dict):
            top_pair_html = (
                f"<p class=\"meta\">Top pair: {html.escape(str(top_pair['left']))} ↔ {html.escape(str(top_pair['right']))}</p>"
                f"<p>exact={top_pair['exact_jaccard']:.4f} · estimated={top_pair['estimated_jaccard']:.4f}</p>"
            )
        else:
            top_pair_html = "<p class=\"meta\">Top pair: none above the recommended threshold yet</p>"
        cards.append(
            "<article class=\"card\">"
            f"<h2>{html.escape(str(entry['title']))}</h2>"
            f"<p>{html.escape(str(entry['story']))}</p>"
            "<ul>"
            f"<li>Preset key: <code>{html.escape(str(entry['preset_name']))}</code></li>"
            f"<li>Files written: <strong>{entry['files_written']}</strong></li>"
            f"<li>Pairs detected: <strong>{entry['pairs_detected']}</strong></li>"
            f"<li>Extensions: {html.escape(extension_summary)}</li>"
            f"<li>Recommended glob: <code>{html.escape(str(scan.get('glob_pattern', 'n/a')))}</code></li>"
            "</ul>"
            f"<pre>{html.escape(str(scan.get('command', 'n/a')))}</pre>"
            f"{top_pair_html}"
            "<p class=\"links\">"
            f"<a href=\"{html.escape(str(entry['summary_json']))}\">summary json</a> · "
            f"<a href=\"{html.escape(str(entry['summary_md']))}\">summary md</a> · "
            f"<a href=\"{html.escape(str(entry['gallery_html']))}\">gallery html</a>"
            "</p>"
            "</article>"
        )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>MinHash preset bundle landing page</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 0; background: #020617; color: #e2e8f0; }}
    main {{ max-width: 1280px; margin: 0 auto; padding: 32px 20px 56px; }}
    .hero, .card {{ background: #0f172a; border: 1px solid #334155; border-radius: 18px; box-shadow: 0 16px 40px rgba(15, 23, 42, 0.32); }}
    .hero {{ padding: 24px; margin-bottom: 24px; }}
    .grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .card {{ padding: 20px; }}
    h1, h2 {{ margin-top: 0; }}
    .meta, .links {{ color: #93c5fd; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #020617; padding: 14px; border-radius: 12px; border: 1px solid #1e293b; }}
    ul {{ padding-left: 20px; }}
    a {{ color: #38bdf8; }}
  </style>
</head>
<body>
  <main>
    <section class=\"hero\">
      <h1>MinHash preset bundle landing page</h1>
      <p>A side-by-side comparison of the curated mixed-language, data-science, systems, and web-dev demo bundles.</p>
      <ul>
        <li>Generated at: <code>{html.escape(str(payload['generated_at']))}</code></li>
        <li>Presets compared: <strong>{payload['preset_count']}</strong></li>
        <li>Total files across bundles: <strong>{payload['total_files_written']}</strong></li>
        <li>Total near-duplicate pairs across bundles: <strong>{payload['total_pairs_detected']}</strong></li>
      </ul>
    </section>
    <section class=\"grid\">{''.join(cards)}</section>
  </main>
</body>
</html>
"""


def write_preset_bundle_landing(bundle_root: Path, output_dir: Path) -> dict[str, object]:
    summary_paths = sorted(bundle_root.rglob("preset-bundle-summary.json"))
    payload = build_preset_bundle_landing(summary_paths, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "preset-landing-summary.json"
    summary_md = output_dir / "preset-landing.md"
    landing_html = output_dir / "preset-landing.html"
    summary_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_md.write_text(_preset_landing_markdown(payload) + "\n", encoding="utf-8")
    landing_html.write_text(_preset_landing_html(payload), encoding="utf-8")
    return {
        "directory": str(output_dir),
        "summary_json": str(summary_json),
        "summary_md": str(summary_md),
        "landing_html": str(landing_html),
        "preset_count": payload["preset_count"],
        "preset_names": payload["preset_names"],
        "total_files_written": payload["total_files_written"],
        "total_pairs_detected": payload["total_pairs_detected"],
    }


def _indexed_document_from_text(
    path: Path,
    text: str,
    *,
    shingle_size: int,
    token_mode: str,
    normalize_identifiers: bool,
    normalize_literals: bool,
    num_hashes: int,
    seed: int,
) -> IndexedDocument:
    shingles = sorted(build_shingles(text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers, normalize_literals=normalize_literals))
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
    normalize_literals: bool = False,
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
            normalize_literals=normalize_literals,
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
        normalize_literals=normalize_literals,
        num_hashes=num_hashes,
        bands=bands,
        seed=seed,
        documents=documents,
    )


def summarize_index_refresh(index: SignatureIndex, paths: Iterable[Path]) -> dict[str, object]:
    existing_by_path = {document.path: document for document in index.documents}
    seen_paths: list[str] = []
    reused_paths: list[str] = []
    updated_paths: list[str] = []
    added_paths: list[str] = []

    for path in paths:
        path_str = str(path)
        seen_paths.append(path_str)
        text = path.read_text(encoding="utf-8")
        content_sha256 = _sha256_text(text)
        previous = existing_by_path.get(path_str)
        if previous is not None and previous.content_sha256 == content_sha256:
            reused_paths.append(path_str)
        elif previous is None:
            added_paths.append(path_str)
        else:
            updated_paths.append(path_str)

    seen_set = set(seen_paths)
    removed_paths = sorted(path_str for path_str in existing_by_path if path_str not in seen_set)
    return {
        "documents_seen": len(seen_paths),
        "reused": len(reused_paths),
        "updated": len(updated_paths),
        "added": len(added_paths),
        "removed": len(removed_paths),
        "reused_paths": reused_paths,
        "updated_paths": updated_paths,
        "added_paths": added_paths,
        "removed_paths": removed_paths,
        "unchanged_ratio": round((len(reused_paths) / len(seen_paths)), 4) if seen_paths else 1.0,
    }


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
                normalize_literals=index.normalize_literals,
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
        normalize_literals=index.normalize_literals,
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
    normalize_literals: bool = False,
) -> dict[str, object]:
    if len(documents) < 2:
        raise ValueError("benchmark requires at least two documents")
    if num_hashes % bands != 0:
        raise ValueError("signature length must be divisible by bands")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")

    build_started = time.perf_counter()
    shingles_by_doc = {
        name: build_shingles(text, shingle_size, token_mode=token_mode, normalize_identifiers=normalize_identifiers, normalize_literals=normalize_literals)
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
        "normalize_literals": normalize_literals,
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
            ("normalize_literals", payload.get("normalize_literals", False)),
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
            f"- Normalize literals: {payload.get('normalize_literals', False)}",
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
    refresh_index_parser.add_argument("--dry-run", action="store_true", help="preview added/updated/removed files without rewriting the index")

    scan_index_parser = subparsers.add_parser("scan-index", help="find candidate pairs from a saved signature index")
    scan_index_parser.add_argument("index_path")
    scan_index_parser.add_argument("--threshold", type=float, default=0.5)

    benchmark_parser = subparsers.add_parser("benchmark", help="benchmark LSH candidate generation vs exact all-pairs scanning")
    benchmark_parser.add_argument("root")
    benchmark_parser.add_argument("--glob", default="*.txt", dest="glob_pattern")
    benchmark_parser.add_argument("--threshold", type=float, default=0.5)
    benchmark_parser.add_argument("--output", help="write benchmark summary to .json, .csv, or .md")

    preset_parser = subparsers.add_parser("write-preset", help="write a curated mixed-language demo corpus")
    preset_parser.add_argument("preset_name", choices=sorted(PRESET_CORPORA))
    preset_parser.add_argument("destination")
    preset_parser.add_argument("--force", action="store_true", help="overwrite preset files if they already exist")
    preset_parser.add_argument("--artifact-bundle-dir", help="optional directory for markdown/json/html portfolio bundle artifacts")
    preset_parser.add_argument("--json", action="store_true")

    preset_landing_parser = subparsers.add_parser(
        "write-preset-landing",
        help="build a cross-preset landing page from existing preset bundle summaries",
    )
    preset_landing_parser.add_argument("bundle_root")
    preset_landing_parser.add_argument("output_dir")
    preset_landing_parser.add_argument("--json", action="store_true")

    for subparser in (compare_parser, corpus_parser, index_parser, benchmark_parser):
        subparser.add_argument("--shingle-size", type=int, default=3)
        subparser.add_argument("--token-mode", choices=["word", "code", "char"], default="word")
        subparser.add_argument("--normalize-identifiers", action="store_true", help="collapse non-keyword identifiers in code mode")
        subparser.add_argument("--normalize-literals", action="store_true", help="collapse numeric, string, boolean, and None literals in code mode")
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
        prefix = "Dry-run summary" if payload.get("dry_run") else "Refreshed"
        print(
            f"{prefix} for {payload['documents_seen']} documents in {payload['index_path']} "
            f"(reused={payload['reused']}, updated={payload['updated']}, added={payload['added']}, removed={payload['removed']})"
        )
        for label in ("updated_paths", "added_paths", "removed_paths"):
            values = payload.get(label, [])
            if values:
                print(f"{label.replace('_', ' ').title()}:")
                for value in values:
                    print(f"- {value}")
        return 0
    if command == "write-preset":
        print(f"Wrote preset {payload['preset_name']} with {payload['files_written']} files to {payload['destination']}")
        artifact_bundle = payload.get("artifact_bundle")
        if isinstance(artifact_bundle, dict) and artifact_bundle.get("directory"):
            print(f"Saved artifact bundle: {artifact_bundle['directory']}")
        return 0
    if command == "write-preset-landing":
        print(
            f"Wrote preset landing page for {payload['preset_count']} presets to {payload['directory']} "
            f"(files={payload['total_files_written']}, pairs={payload['total_pairs_detected']})"
        )
        print(f"Landing HTML: {payload['landing_html']}")
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
        if args.normalize_literals and args.token_mode != "code":
            parser.error("--normalize-literals requires --token-mode code")

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
            normalize_literals=args.normalize_literals,
        )
        return _emit(
            {
                "command": "compare",
                "bands": args.bands,
                "token_mode": args.token_mode,
                "normalize_identifiers": args.normalize_identifiers,
                "normalize_literals": args.normalize_literals,
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
            normalize_literals=args.normalize_literals,
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
                "normalize_literals": args.normalize_literals,
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
            normalize_literals=args.normalize_literals,
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
                "normalize_literals": index.normalize_literals,
                "num_hashes": index.num_hashes,
                "shingle_size": index.shingle_size,
            },
            args.json,
        )

    if args.command == "refresh-index":
        index_path = Path(args.index_path)
        index = load_signature_index(index_path)
        paths = _collect_paths(Path(index.root), index.glob_pattern)
        summary = summarize_index_refresh(index, paths)
        if args.dry_run:
            return _emit(
                {
                    "command": "refresh-index",
                    "index_path": str(index_path),
                    "token_mode": index.token_mode,
                    "normalize_identifiers": index.normalize_identifiers,
                    "normalize_literals": index.normalize_literals,
                    "dry_run": True,
                    **summary,
                },
                args.json,
            )
        refreshed_index, stats = refresh_signature_index(index, paths)
        save_signature_index(refreshed_index, index_path)
        return _emit(
            {
                "command": "refresh-index",
                "index_path": str(index_path),
                "token_mode": index.token_mode,
                "normalize_identifiers": index.normalize_identifiers,
                "normalize_literals": index.normalize_literals,
                "dry_run": False,
                "updated_paths": summary["updated_paths"],
                "added_paths": summary["added_paths"],
                "removed_paths": summary["removed_paths"],
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
                "normalize_literals": index.normalize_literals,
                "pairs": [report.to_dict() for report in reports],
            },
            args.json,
        )

    if args.command == "write-preset":
        destination = Path(args.destination)
        written = write_preset_corpus(args.preset_name, destination, force=args.force)
        payload = {
            "command": "write-preset",
            "preset_name": args.preset_name,
            "destination": str(destination),
            "files_written": len(written),
            "files": [str(path) for path in written],
        }
        if args.artifact_bundle_dir:
            payload["artifact_bundle"] = write_preset_artifact_bundle(
                args.preset_name,
                destination,
                Path(args.artifact_bundle_dir),
                written,
            )
        return _emit(payload, args.json)

    if args.command == "write-preset-landing":
        payload = {
            "command": "write-preset-landing",
            **write_preset_bundle_landing(Path(args.bundle_root), Path(args.output_dir)),
        }
        return _emit(payload, args.json)

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
            normalize_literals=args.normalize_literals,
        )
        if args.output:
            output_path = export_benchmark_report(payload, Path(args.output))
            payload = {**payload, "output": str(output_path)}
        return _emit(payload, args.json)

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
