from __future__ import annotations

import argparse
import html
import json
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence


def write_text(path: str | Path, content: str) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    return output


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


@dataclass(slots=True)
class PatternGroup:
    name: str
    patterns: List[str]
    description: str = ""


@dataclass(slots=True)
class PatternPreset:
    name: str
    groups: List[PatternGroup]
    title: str | None = None
    description: str = ""


def ensure_non_negative_context(context_chars: int) -> int:
    if context_chars < 0:
        raise ValueError("context_chars must be non-negative")
    return context_chars


def dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(value for value in values if value))


def load_pattern_preset(path: str | Path, preset_name: str | None = None) -> PatternPreset:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    presets = payload.get("presets")
    if not isinstance(presets, list) or not presets:
        raise ValueError("preset file must contain a non-empty 'presets' list")

    resolved_payload = None
    if preset_name is None:
        if len(presets) != 1:
            raise ValueError("preset file contains multiple presets; provide --preset")
        resolved_payload = presets[0]
    else:
        for candidate in presets:
            if candidate.get("name") == preset_name:
                resolved_payload = candidate
                break
        if resolved_payload is None:
            raise ValueError(f"unknown preset: {preset_name}")

    name = resolved_payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("preset entries must include a non-empty string 'name'")

    raw_groups = resolved_payload.get("groups")
    if not isinstance(raw_groups, list) or not raw_groups:
        raise ValueError(f"preset '{name}' must include a non-empty 'groups' list")

    groups: List[PatternGroup] = []
    seen_group_names: set[str] = set()
    for raw_group in raw_groups:
        group_name = raw_group.get("name")
        if not isinstance(group_name, str) or not group_name.strip():
            raise ValueError(f"preset '{name}' contains a group without a valid name")
        if group_name in seen_group_names:
            raise ValueError(f"preset '{name}' repeats group name '{group_name}'")
        seen_group_names.add(group_name)

        raw_patterns = raw_group.get("patterns")
        if not isinstance(raw_patterns, list) or not raw_patterns:
            raise ValueError(f"group '{group_name}' in preset '{name}' must include patterns")
        patterns = dedupe_preserve_order(
            pattern.strip() for pattern in raw_patterns if isinstance(pattern, str) and pattern.strip()
        )
        if not patterns:
            raise ValueError(f"group '{group_name}' in preset '{name}' must include non-empty patterns")
        description = raw_group.get("description", "")
        if description is None:
            description = ""
        if not isinstance(description, str):
            raise ValueError(f"group '{group_name}' in preset '{name}' has a non-string description")
        groups.append(PatternGroup(name=group_name, patterns=patterns, description=description))

    title = resolved_payload.get("title")
    if title is not None and not isinstance(title, str):
        raise ValueError(f"preset '{name}' has a non-string title")
    description = resolved_payload.get("description", "")
    if description is None:
        description = ""
    if not isinstance(description, str):
        raise ValueError(f"preset '{name}' has a non-string description")

    return PatternPreset(name=name, groups=groups, title=title, description=description)


def patterns_from_preset(preset: PatternPreset) -> List[str]:
    return dedupe_preserve_order(pattern for group in preset.groups for pattern in group.patterns)


def build_pattern_group_map(
    groups: Sequence[PatternGroup],
    *,
    case_sensitive: bool,
) -> Dict[str, List[str]]:
    normalize = (lambda value: value) if case_sensitive else (lambda value: value.lower())
    pattern_groups: Dict[str, List[str]] = {}
    for group in groups:
        for pattern in group.patterns:
            normalized = normalize(pattern)
            pattern_groups.setdefault(normalized, [])
            if group.name not in pattern_groups[normalized]:
                pattern_groups[normalized].append(group.name)
    return pattern_groups


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
        max_history = self.max_pattern_length + context_chars
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
    unique = dedupe_preserve_order(merged)
    if not unique:
        raise ValueError("no patterns supplied")
    return unique


def serialize_match(match: Match, *, groups: Sequence[str] | None = None) -> dict:
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
    if groups:
        payload["groups"] = list(groups)
    return payload


def build_result(
    automaton: AhoCorasickAutomaton,
    matches: Sequence[Match],
    *,
    characters_processed: int,
    chunk_count: int,
    chunk_size: int | None,
    context_chars: int = 0,
    group_definitions: Sequence[PatternGroup] = (),
    preset: PatternPreset | None = None,
) -> dict:
    counts = {pattern: 0 for pattern in automaton.patterns}
    for match in matches:
        counts[match.pattern] += 1

    pattern_groups = build_pattern_group_map(group_definitions, case_sensitive=automaton.case_sensitive)
    group_counts = {group.name: 0 for group in group_definitions}
    serialized_matches = []
    for match in matches:
        match_groups = pattern_groups.get(match.pattern, [])
        for group_name in match_groups:
            group_counts[group_name] += 1
        serialized_matches.append(serialize_match(match, groups=match_groups))

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

    result = {
        "pattern_count": len(automaton.patterns),
        "match_count": len(matches),
        "case_sensitive": automaton.case_sensitive,
        "counts": counts,
        "matches": serialized_matches,
        "input": input_meta,
    }

    if group_definitions:
        normalize = (lambda value: value) if automaton.case_sensitive else (lambda value: value.lower())
        result["groups"] = [
            {
                "name": group.name,
                "description": group.description,
                "patterns": dedupe_preserve_order(normalize(pattern) for pattern in group.patterns),
                "match_count": group_counts[group.name],
            }
            for group in group_definitions
        ]

    if preset is not None:
        result["preset"] = {
            "name": preset.name,
            "title": preset.title,
            "description": preset.description,
        }

    return result


def search_text(
    text: str,
    patterns: Sequence[str],
    *,
    case_sensitive: bool = True,
    context_chars: int = 0,
    group_definitions: Sequence[PatternGroup] = (),
    preset: PatternPreset | None = None,
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
        group_definitions=group_definitions,
        preset=preset,
    )


def search_chunks(
    chunks: Iterable[str],
    patterns: Sequence[str],
    *,
    case_sensitive: bool = True,
    chunk_size: int | None = None,
    context_chars: int = 0,
    group_definitions: Sequence[PatternGroup] = (),
    preset: PatternPreset | None = None,
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
        group_definitions=group_definitions,
        preset=preset,
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
    group_definitions: Sequence[PatternGroup] = (),
    preset: PatternPreset | None = None,
) -> tuple[str | None, dict]:
    context_chars = ensure_non_negative_context(context_chars)
    if chunk_size is None:
        text = Path(path).read_text(encoding="utf-8")
        return text, search_text(
            text,
            patterns,
            case_sensitive=case_sensitive,
            context_chars=context_chars,
            group_definitions=group_definitions,
            preset=preset,
        )
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    result = search_chunks(
        iter_file_chunks(path, chunk_size),
        patterns,
        case_sensitive=case_sensitive,
        chunk_size=chunk_size,
        context_chars=context_chars,
        group_definitions=group_definitions,
        preset=preset,
    )
    return None, result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search text with the Aho-Corasick multi-pattern algorithm")
    parser.add_argument("patterns", nargs="*", help="patterns to search for")
    parser.add_argument("--pattern-file", help="newline-delimited pattern file")
    parser.add_argument("--preset-file", help="JSON file containing grouped keyword presets")
    parser.add_argument("--preset", help="named preset to load from --preset-file")
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
    parser.add_argument("--report-title", help="optional title to use for Markdown/HTML report exports")
    parser.add_argument("--report-markdown-out", help="write a Markdown match report artifact")
    parser.add_argument("--report-html-out", help="write a static HTML match report artifact")
    return parser


def render_text_output(result: dict) -> str:
    lines = [
        f"patterns: {result['pattern_count']}",
        f"matches: {result['match_count']}",
    ]
    preset = result.get("preset")
    if preset:
        lines.append(f"preset: {preset['name']}")
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
    groups = result.get("groups") or []
    if groups:
        lines.append("group counts:")
        for group in groups:
            suffix = f" [{', '.join(group['patterns'])}]" if group.get("patterns") else ""
            lines.append(f"  - {group['name']}: {group['match_count']}{suffix}")
    if result["matches"]:
        lines.append("matches detail:")
        for item in result["matches"]:
            snippet = ""
            context = item.get("context")
            if context:
                snippet = f" | context={context['excerpt']!r}"
            group_suffix = ""
            if item.get("groups"):
                group_suffix = f" | groups={', '.join(item['groups'])}"
            lines.append(
                f"  - {item['pattern']} @ line {item['line']}, col {item['column']}"
                f" [{item['start']}:{item['end']}]" + group_suffix + snippet
            )
    return "\n".join(lines)


def _html_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _markdown_code(value: object) -> str:
    return f"`{str(value).replace('`', '\\`')}`"


def build_report_title(*, source_label: str, explicit_title: str | None = None) -> str:
    if explicit_title:
        return explicit_title
    return f"Aho-Corasick match report — {Path(source_label).name}"


def describe_input_mode(input_meta: dict) -> str:
    if input_meta.get("mode") == "stream":
        return (
            f"stream ({input_meta['chunk_count']} chunks @ {input_meta['chunk_size']} chars, "
            f"boundary overlap {input_meta['boundary_overlap']})"
        )
    return "memory"


def describe_context_mode(input_meta: dict) -> str:
    context_chars = input_meta.get("context_chars", 0)
    if context_chars <= 0:
        return "not requested"
    if input_meta.get("context_mode") == "sampled":
        return f"{context_chars} chars (sampled around matches)"
    return f"{context_chars} chars"


def render_report_markdown(
    result: dict,
    *,
    patterns: Sequence[str],
    source_label: str,
    title: str | None = None,
) -> str:
    input_meta = result.get("input") or {}
    resolved_title = build_report_title(source_label=source_label, explicit_title=title)
    preset = result.get("preset") or {}
    lines = [f"# {resolved_title}", ""]
    lines.extend(
        [
            f"- Source: {_markdown_code(source_label)}",
            f"- Preset: {_markdown_code(preset.get('name', 'ad hoc patterns'))}",
            f"- Input mode: {_markdown_code(describe_input_mode(input_meta))}",
            f"- Case sensitive: {_markdown_code('yes' if result['case_sensitive'] else 'no')}",
            f"- Characters processed: {_markdown_code(input_meta.get('characters_processed', 0))}",
            f"- Pattern count: {_markdown_code(result['pattern_count'])}",
            f"- Match count: {_markdown_code(result['match_count'])}",
            f"- Context mode: {_markdown_code(describe_context_mode(input_meta))}",
            f"- Patterns: {', '.join(_markdown_code(pattern) for pattern in patterns)}",
            "",
            "## Pattern counts",
            "",
            "| Pattern | Count |",
            "| --- | ---: |",
        ]
    )
    for pattern, count in result["counts"].items():
        lines.append(f"| {pattern.replace('|', '\\|')} | {count} |")

    groups = result.get("groups") or []
    if groups:
        lines.extend([
            "",
            "## Group counts",
            "",
            "| Group | Matches | Patterns |",
            "| --- | ---: | --- |",
        ])
        for group in groups:
            details = ", ".join(_markdown_code(pattern) for pattern in group["patterns"])
            if group.get("description"):
                details += f"<br><sub>{group['description']}</sub>"
            lines.append(f"| {group['name'].replace('|', '\\|')} | {group['match_count']} | {details} |")

    lines.extend(["", "## Match excerpts", ""])
    if not result["matches"]:
        lines.append("No matches found.")
        return "\n".join(lines) + "\n"

    for index, item in enumerate(result["matches"], start=1):
        context = item.get("context")
        lines.extend(
            [
                f"### Match {index} — {_markdown_code(item['pattern'])}",
                f"- Location: line {item['line']}, column {item['column']}",
                f"- Offsets: {_markdown_code(f'{item['start']}:{item['end']}')}",
            ]
        )
        if item.get("groups"):
            lines.append(f"- Groups: {', '.join(_markdown_code(group) for group in item['groups'])}")
        if context:
            lines.append("- Excerpt:")
            lines.append("```text")
            lines.append(context["excerpt"])
            lines.append("```")
            lines.append(
                "- Before / match / after: "
                f"{_markdown_code(json.dumps(context['before'], ensure_ascii=False))} · "
                f"{_markdown_code(json.dumps(context['match'], ensure_ascii=False))} · "
                f"{_markdown_code(json.dumps(context['after'], ensure_ascii=False))}"
            )
        else:
            lines.append("- Excerpt: context not requested")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_report_html(
    result: dict,
    *,
    patterns: Sequence[str],
    source_label: str,
    title: str | None = None,
) -> str:
    input_meta = result.get("input") or {}
    resolved_title = build_report_title(source_label=source_label, explicit_title=title)
    preset = result.get("preset") or {}
    summary_cards = [
        ("Patterns", str(result["pattern_count"]), "Unique keywords loaded into the automaton."),
        ("Matches", str(result["match_count"]), "Total emitted matches across the scan."),
        (
            "Preset",
            result.get("preset", {}).get("name", "ad hoc patterns"),
            "Preset bundles let one report summarize related incident or category keyword packs.",
        ),
        (
            "Input mode",
            describe_input_mode(input_meta),
            "Memory mode scans the whole text once; stream mode preserves matches across chunk boundaries.",
        ),
        (
            "Context",
            describe_context_mode(input_meta),
            "Sampled streaming contexts stay bounded instead of loading the full file.",
        ),
    ]
    summary_cards_html = "\n".join(
        f'''<article class="summary-card">
      <p class="eyebrow">{_html_escape(label)}</p>
      <strong>{_html_escape(value)}</strong>
      <p>{_html_escape(description)}</p>
    </article>'''
        for label, value, description in summary_cards
    )
    pattern_chip_html = "".join(
        f'<span class="chip">{_html_escape(pattern)} · {result["counts"][pattern]}</span>'
        for pattern in patterns
    )
    groups = result.get("groups") or []
    group_cards_html = "\n".join(
        f'''<article class="summary-card">
      <p class="eyebrow">Group</p>
      <strong>{_html_escape(group["name"])} · {_html_escape(group["match_count"])}</strong>
      <p>{_html_escape(group.get("description") or "Related keyword pack for grouped reporting.")}</p>
      <p class="group-patterns">{_html_escape(', '.join(group["patterns"]))}</p>
    </article>'''
        for group in groups
    )

    match_cards: list[str] = []
    for index, item in enumerate(result["matches"], start=1):
        context = item.get("context")
        excerpt = context["excerpt"] if context else "context not requested"
        before = context["before"] if context else ""
        matched = context["match"] if context else item["pattern"]
        after = context["after"] if context else ""
        match_cards.append(
            f'''<article class="match-card">
      <div class="match-header">
        <div>
          <p class="eyebrow">Match {index}</p>
          <h3><code>{_html_escape(item["pattern"])}</code></h3>
        </div>
        <span class="pill">line {item["line"]}, col {item["column"]}</span>
      </div>
      <p class="offsets">Offsets <code>{item["start"]}:{item["end"]}</code></p>
      {''.join(f'<span class="chip group-chip">{_html_escape(group)}</span>' for group in item.get("groups", []))}
      <pre>{_html_escape(excerpt)}</pre>
      <dl>
        <div><dt>Before</dt><dd><code>{_html_escape(before)}</code></dd></div>
        <div><dt>Match</dt><dd><code>{_html_escape(matched)}</code></dd></div>
        <div><dt>After</dt><dd><code>{_html_escape(after)}</code></dd></div>
      </dl>
    </article>'''
        )
    if not match_cards:
        match_cards.append(
            '<article class="match-card empty"><h3>No matches found</h3>'
            '<p>This report still captures the scan configuration and counts summary.</p></article>'
        )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_html_escape(resolved_title)}</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    h1, h2, h3 {{ line-height: 1.15; }}
    p, li, dd {{ line-height: 1.55; }}
    code, pre {{ font-family: "SFMono-Regular", ui-monospace, monospace; }}
    .hero {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.4rem; padding: 1.4rem; background: linear-gradient(135deg, rgba(224, 231, 255, 0.96), rgba(240, 253, 250, 0.96)); box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08); }}
    .hero p {{ max-width: 74ch; }}
    .eyebrow {{ margin: 0; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #4338ca; }}
    .hero-meta, .chip-row {{ display: flex; flex-wrap: wrap; gap: 0.65rem; }}
    .hero-meta {{ margin-top: 1rem; }}
    .chip, .pill {{ display: inline-flex; align-items: center; padding: 0.4rem 0.75rem; border-radius: 999px; font-size: 0.92rem; }}
    .chip {{ background: rgba(224, 231, 255, 0.85); border: 1px solid rgba(129, 140, 248, 0.28); color: #3730a3; }}
    .group-chip {{ margin-right: 0.45rem; margin-top: 0.8rem; background: rgba(240, 253, 244, 0.95); border-color: rgba(34, 197, 94, 0.22); color: #166534; }}
    .pill {{ background: rgba(219, 234, 254, 0.95); color: #1d4ed8; font-weight: 700; }}
    .summary-grid, .match-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-top: 1.4rem; }}
    .summary-card, .match-card {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.2rem; background: rgba(255, 255, 255, 0.92); box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06); }}
    .summary-card {{ padding: 1rem; }}
    .summary-card strong {{ display: block; margin-top: 0.3rem; font-size: 1.18rem; }}
    .group-patterns {{ color: #475569; font-size: 0.95rem; }}
    .section-title {{ margin: 1.8rem 0 0.8rem; }}
    .match-card {{ padding: 1rem; }}
    .match-header {{ display: flex; gap: 0.75rem; align-items: start; justify-content: space-between; }}
    .match-header h3 {{ margin: 0.15rem 0 0; }}
    .offsets {{ margin: 0.8rem 0 0; color: #475569; }}
    pre {{ margin: 0.8rem 0 0; padding: 0.9rem; border-radius: 0.9rem; background: #0f172a; color: #e2e8f0; white-space: pre-wrap; word-break: break-word; }}
    dl {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.8rem; margin: 1rem 0 0; }}
    dt {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }}
    dd {{ margin: 0.2rem 0 0; }}
    .empty {{ display: block; }}
    @media (max-width: 760px) {{
      main {{ padding: 1rem 0.75rem 2rem; }}
      dl {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">Aho-Corasick search lab</p>
      <h1>{_html_escape(resolved_title)}</h1>
      <p>Portfolio-friendly match report for the multi-pattern automaton. This view keeps the stream-vs-memory scan story, per-pattern counts, and sampled match excerpts together in one browser-friendly artifact.</p>
      {f'<p>{_html_escape(preset["description"])}</p>' if preset.get('description') else ''}
      <div class="hero-meta">
        <span class="chip">Source {_html_escape(source_label)}</span>
        <span class="chip">Characters {_html_escape(input_meta.get("characters_processed", 0))}</span>
        <span class="chip">Case sensitive {_html_escape('yes' if result['case_sensitive'] else 'no')}</span>
      </div>
      <div class="chip-row">{pattern_chip_html}</div>
    </section>
    <section class="summary-grid">
{summary_cards_html}
    </section>
    {f'<h2 class="section-title">Grouped keyword packs</h2><section class="summary-grid">{group_cards_html}</section>' if group_cards_html else ''}
    <h2 class="section-title">Match excerpts</h2>
    <section class="match-grid">
{''.join(match_cards)}
    </section>
  </main>
</body>
</html>
'''


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    preset = None
    preset_patterns: List[str] = []
    group_definitions: List[PatternGroup] = []
    if args.preset and not args.preset_file:
        parser.error("--preset requires --preset-file")
    if args.preset_file:
        try:
            preset = load_pattern_preset(args.preset_file, args.preset)
        except ValueError as exc:
            parser.error(str(exc))
        preset_patterns = patterns_from_preset(preset)
        group_definitions = list(preset.groups)

    explicit_patterns: List[str] = []
    if args.patterns or args.pattern_file:
        patterns = load_patterns(args.patterns, args.pattern_file)
        explicit_patterns.extend(patterns)

    patterns = dedupe_preserve_order([*preset_patterns, *explicit_patterns])

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
    if not patterns:
        parser.error("provide patterns directly, via --pattern-file, or via --preset-file")

    if args.input:
        _, result = search_file(
            args.input,
            patterns,
            case_sensitive=not args.ignore_case,
            chunk_size=args.chunk_size,
            context_chars=args.context,
            group_definitions=group_definitions,
            preset=preset,
        )
        source_label = args.input
    else:
        text = args.text
        assert text is not None
        result = search_text(
            text,
            patterns,
            case_sensitive=not args.ignore_case,
            context_chars=args.context,
            group_definitions=group_definitions,
            preset=preset,
        )
        source_label = "inline text"

    report_title = args.report_title or (preset.title if preset is not None else None)

    if args.report_markdown_out:
        write_text(
            args.report_markdown_out,
            render_report_markdown(result, patterns=patterns, source_label=source_label, title=report_title),
        )
    if args.report_html_out:
        write_text(
            args.report_html_out,
            render_report_html(result, patterns=patterns, source_label=source_label, title=report_title),
        )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_text_output(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
