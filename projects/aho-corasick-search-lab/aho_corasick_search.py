from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence


@dataclass(slots=True)
class MatchContext:
    before: str
    match: str
    after: str = ""

    @property
    def excerpt(self) -> str:
        return f"{self.before}⟦{self.match}⟧{self.after}"


@dataclass(slots=True)
class Match:
    pattern: str
    start: int
    end: int
    line: int
    column: int
    context: MatchContext | None = None


@dataclass(slots=True)
class Node:
    transitions: Dict[str, int] = field(default_factory=dict)
    failure: int = 0
    outputs: List[str] = field(default_factory=list)


@dataclass(slots=True)
class PendingContext:
    match: Match
    remaining_after: int


def ensure_non_negative_context(context_chars: int) -> int:
    if context_chars < 0:
        raise ValueError("context_chars must be non-negative")
    return context_chars


class AhoCorasickAutomaton:
    def __init__(self, patterns: Sequence[str], *, case_sensitive: bool = True) -> None:
        cleaned = [pattern for pattern in patterns if pattern]
        if not cleaned:
            raise ValueError("at least one non-empty pattern is required")
        self.case_sensitive = case_sensitive
        self.patterns = list(dict.fromkeys(self._normalize(pattern) for pattern in cleaned))
        self.max_pattern_length = max(len(pattern) for pattern in self.patterns)
        self.nodes: List[Node] = [Node()]
        self._build_trie(self.patterns)
        self._build_failure_links()

    def _normalize(self, text: str) -> str:
        return text if self.case_sensitive else text.lower()

    def _build_trie(self, patterns: Sequence[str]) -> None:
        for pattern in patterns:
            node_index = 0
            for char in pattern:
                node = self.nodes[node_index]
                if char not in node.transitions:
                    node.transitions[char] = len(self.nodes)
                    self.nodes.append(Node())
                node_index = node.transitions[char]
            self.nodes[node_index].outputs.append(pattern)

    def _build_failure_links(self) -> None:
        queue: deque[int] = deque()
        root = self.nodes[0]
        for child_index in root.transitions.values():
            self.nodes[child_index].failure = 0
            queue.append(child_index)

        while queue:
            current = queue.popleft()
            current_node = self.nodes[current]
            for char, next_index in current_node.transitions.items():
                queue.append(next_index)
                fallback = current_node.failure
                while fallback and char not in self.nodes[fallback].transitions:
                    fallback = self.nodes[fallback].failure
                self.nodes[next_index].failure = self.nodes[fallback].transitions.get(char, 0)
                inherited = self.nodes[self.nodes[next_index].failure].outputs
                for pattern in inherited:
                    if pattern not in self.nodes[next_index].outputs:
                        self.nodes[next_index].outputs.append(pattern)

    def _trim_history(self, history: deque[str], *, max_history: int, history_start: int) -> int:
        while len(history) > max_history:
            history.popleft()
            history_start += 1
        return history_start

    def _context_before_and_match(
        self,
        history_chars: Sequence[str],
        *,
        history_start: int,
        start: int,
        end: int,
        context_chars: int,
    ) -> MatchContext:
        window_start = max(history_start, start - context_chars)
        start_index = start - history_start
        window_start_index = window_start - history_start
        end_index = end - history_start
        before = "".join(history_chars[window_start_index:start_index])
        matched = "".join(history_chars[start_index:end_index])
        return MatchContext(before=before, match=matched)

    def scan_chunks(self, chunks: Iterable[str], *, context_chars: int = 0) -> tuple[List[Match], int, int]:
        context_chars = ensure_non_negative_context(context_chars)
        line_starts = [0]
        matches: List[Match] = []
        state = 0
        offset = 0
        chunk_count = 0
        history: deque[str] = deque()
        history_start = 0
        max_history = self.max_pattern_length + max(context_chars, 0)
        pending_contexts: List[PendingContext] = []

        for chunk in chunks:
            if not chunk:
                continue
            chunk_count += 1
            normalized_chunk = self._normalize(chunk)
            for index, (raw_char, char) in enumerate(zip(chunk, normalized_chunk)):
                while state and char not in self.nodes[state].transitions:
                    state = self.nodes[state].failure
                state = self.nodes[state].transitions.get(char, 0)
                absolute_index = offset + index

                history.append(raw_char)
                history_start = self._trim_history(history, max_history=max_history, history_start=history_start)

                if pending_contexts:
                    still_pending: List[PendingContext] = []
                    for pending in pending_contexts:
                        context = pending.match.context
                        assert context is not None
                        if pending.remaining_after > 0:
                            context.after += raw_char
                            pending.remaining_after -= 1
                        if pending.remaining_after > 0:
                            still_pending.append(pending)
                    pending_contexts = still_pending

                history_chars = list(history) if context_chars > 0 and self.nodes[state].outputs else None
                for pattern in self.nodes[state].outputs:
                    start = absolute_index - len(pattern) + 1
                    line, column = offset_to_line_column(line_starts, start)
                    context = None
                    if context_chars > 0 and history_chars is not None:
                        context = self._context_before_and_match(
                            history_chars,
                            history_start=history_start,
                            start=start,
                            end=absolute_index + 1,
                            context_chars=context_chars,
                        )
                    match = Match(
                        pattern=pattern,
                        start=start,
                        end=absolute_index + 1,
                        line=line,
                        column=column,
                        context=context,
                    )
                    matches.append(match)
                    if context_chars > 0 and context is not None:
                        pending_contexts.append(PendingContext(match=match, remaining_after=context_chars))

                if raw_char == "\n":
                    line_starts.append(absolute_index + 1)
            offset += len(chunk)

        return matches, offset, chunk_count

    def find_matches(self, text: str, *, context_chars: int = 0) -> List[Match]:
        matches, _, _ = self.scan_chunks([text], context_chars=context_chars)
        return matches

    def find_matches_in_chunks(self, chunks: Iterable[str], *, context_chars: int = 0) -> List[Match]:
        matches, _, _ = self.scan_chunks(chunks, context_chars=context_chars)
        return matches


def offset_to_line_column(line_starts: Sequence[int], offset: int) -> tuple[int, int]:
    low = 0
    high = len(line_starts) - 1
    while low <= high:
        mid = (low + high) // 2
        if line_starts[mid] <= offset:
            low = mid + 1
        else:
            high = mid - 1
    line_index = max(high, 0)
    return line_index + 1, offset - line_starts[line_index] + 1


def load_patterns(patterns: Sequence[str], pattern_file: str | None) -> List[str]:
    merged = list(patterns)
    if pattern_file:
        for line in Path(pattern_file).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                merged.append(stripped)
    unique = list(dict.fromkeys(merged))
    if not unique:
        raise ValueError("no patterns supplied")
    return unique


def serialize_match(match: Match) -> dict:
    payload = {
        "pattern": match.pattern,
        "start": match.start,
        "end": match.end,
        "line": match.line,
        "column": match.column,
    }
    if match.context is not None:
        payload["context"] = {
            **asdict(match.context),
            "excerpt": match.context.excerpt,
        }
    return payload


def build_result(
    automaton: AhoCorasickAutomaton,
    matches: Sequence[Match],
    *,
    characters_processed: int,
    chunk_count: int,
    chunk_size: int | None,
    context_chars: int = 0,
) -> dict:
    counts = {pattern: 0 for pattern in automaton.patterns}
    for match in matches:
        counts[match.pattern] += 1

    input_meta = {
        "mode": "stream" if chunk_size is not None else "memory",
        "characters_processed": characters_processed,
        "chunk_count": chunk_count,
    }
    if chunk_size is not None:
        input_meta["chunk_size"] = chunk_size
        input_meta["boundary_overlap"] = max(automaton.max_pattern_length - 1, 0)
    if context_chars > 0:
        input_meta["context_chars"] = context_chars
        if chunk_size is not None:
            input_meta["context_mode"] = "sampled"

    return {
        "pattern_count": len(automaton.patterns),
        "match_count": len(matches),
        "case_sensitive": automaton.case_sensitive,
        "counts": counts,
        "matches": [serialize_match(match) for match in matches],
        "input": input_meta,
    }


def search_text(
    text: str,
    patterns: Sequence[str],
    *,
    case_sensitive: bool = True,
    context_chars: int = 0,
) -> dict:
    context_chars = ensure_non_negative_context(context_chars)
    automaton = AhoCorasickAutomaton(patterns, case_sensitive=case_sensitive)
    matches, characters_processed, chunk_count = automaton.scan_chunks([text], context_chars=context_chars)
    return build_result(
        automaton,
        matches,
        characters_processed=characters_processed,
        chunk_count=chunk_count,
        chunk_size=None,
        context_chars=context_chars,
    )


def search_chunks(
    chunks: Iterable[str],
    patterns: Sequence[str],
    *,
    case_sensitive: bool = True,
    chunk_size: int | None = None,
    context_chars: int = 0,
) -> dict:
    context_chars = ensure_non_negative_context(context_chars)
    automaton = AhoCorasickAutomaton(patterns, case_sensitive=case_sensitive)
    matches, characters_processed, chunk_count = automaton.scan_chunks(chunks, context_chars=context_chars)
    return build_result(
        automaton,
        matches,
        characters_processed=characters_processed,
        chunk_count=chunk_count,
        chunk_size=chunk_size,
        context_chars=context_chars,
    )


def iter_file_chunks(path: str | Path, chunk_size: int) -> Iterator[str]:
    with Path(path).open("r", encoding="utf-8") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            yield chunk


def search_file(
    path: str | Path,
    patterns: Sequence[str],
    *,
    case_sensitive: bool = True,
    chunk_size: int | None = None,
    context_chars: int = 0,
) -> tuple[str | None, dict]:
    context_chars = ensure_non_negative_context(context_chars)
    if chunk_size is None:
        text = Path(path).read_text(encoding="utf-8")
        return text, search_text(text, patterns, case_sensitive=case_sensitive, context_chars=context_chars)
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    result = search_chunks(
        iter_file_chunks(path, chunk_size),
        patterns,
        case_sensitive=case_sensitive,
        chunk_size=chunk_size,
        context_chars=context_chars,
    )
    return None, result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search text with the Aho-Corasick multi-pattern algorithm")
    parser.add_argument("patterns", nargs="*", help="patterns to search for")
    parser.add_argument("--pattern-file", help="newline-delimited pattern file")
    parser.add_argument("--text", help="inline text to search")
    parser.add_argument("--input", help="path to a text file to search")
    parser.add_argument("--ignore-case", action="store_true", help="perform case-insensitive matching")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--context",
        type=int,
        default=0,
        help="include N context chars around each match; chunked mode emits sampled windows without loading the full file",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="read file input in fixed-size character chunks while preserving cross-chunk matches",
    )
    return parser


def render_text_output(result: dict) -> str:
    lines = [
        f"patterns: {result['pattern_count']}",
        f"matches: {result['match_count']}",
    ]
    input_meta = result.get("input") or {}
    if input_meta.get("mode") == "stream":
        lines.append(
            "input mode: stream"
            f" ({input_meta['chunk_count']} chunks @ {input_meta['chunk_size']} chars,"
            f" boundary overlap {input_meta['boundary_overlap']})"
        )
    if input_meta.get("context_chars", 0) > 0:
        context_line = f"context chars: {input_meta['context_chars']}"
        if input_meta.get("context_mode") == "sampled":
            context_line += " (sampled around matches)"
        lines.append(context_line)
    lines.append("counts:")
    for pattern, count in result["counts"].items():
        lines.append(f"  - {pattern}: {count}")
    if result["matches"]:
        lines.append("matches detail:")
        for item in result["matches"]:
            snippet = ""
            context = item.get("context")
            if context:
                snippet = f" | context={context['excerpt']!r}"
            lines.append(
                f"  - {item['pattern']} @ line {item['line']}, col {item['column']}"
                f" [{item['start']}:{item['end']}]" + snippet
            )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    patterns = load_patterns(args.patterns, args.pattern_file)

    if not args.text and not args.input:
        parser.error("provide --text or --input")
    if args.text and args.input:
        parser.error("choose either --text or --input")
    if args.chunk_size is not None and not args.input:
        parser.error("--chunk-size requires --input")
    if args.chunk_size is not None and args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")
    if args.context < 0:
        parser.error("--context must be non-negative")

    if args.input:
        _, result = search_file(
            args.input,
            patterns,
            case_sensitive=not args.ignore_case,
            chunk_size=args.chunk_size,
            context_chars=args.context,
        )
    else:
        text = args.text
        assert text is not None
        result = search_text(
            text,
            patterns,
            case_sensitive=not args.ignore_case,
            context_chars=args.context,
        )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_text_output(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
