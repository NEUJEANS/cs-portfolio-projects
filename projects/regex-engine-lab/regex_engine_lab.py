from __future__ import annotations

import argparse
import html
import json
import re
import string
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ASCII_DIGITS = frozenset(string.digits)
ASCII_WORD = frozenset(string.ascii_letters + string.digits + "_")
ASCII_WHITESPACE = frozenset(" \t\n\r\f\v")


class RegexSyntaxError(ValueError):
    """Raised when the simplified regex grammar is invalid."""


class BenchmarkSuiteError(ValueError):
    """Raised when a benchmark suite file is invalid."""


@dataclass(frozen=True)
class Literal:
    value: str


@dataclass(frozen=True)
class Dot:
    pass


@dataclass(frozen=True)
class CharacterClassTerm:
    chars: frozenset[str]
    negated: bool = False


@dataclass(frozen=True)
class CharacterClass:
    terms: tuple[CharacterClassTerm, ...]
    negated: bool = False


@dataclass(frozen=True)
class Concat:
    parts: tuple[object, ...]


@dataclass(frozen=True)
class Alternate:
    options: tuple[object, ...]


@dataclass(frozen=True)
class Repeat:
    node: object
    mode: str


@dataclass(frozen=True)
class Anchor:
    kind: str


@dataclass
class State:
    kind: str
    out1: int | None = None
    out2: int | None = None
    char: str | None = None
    class_terms: tuple[CharacterClassTerm, ...] | None = None
    negated: bool = False


@dataclass
class Fragment:
    start: int
    outs: list[tuple[int, str]] = field(default_factory=list)


@dataclass(frozen=True)
class BenchmarkCase:
    label: str
    pattern: str
    text: str
    mode: str = "fullmatch"
    tags: tuple[str, ...] = ()


DEFAULT_BENCHMARK_CASES: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        "anchored_id_fullmatch",
        r"^ID-\d\d\d\d-\w+$",
        "ID-2026-demo_user",
        tags=("interview-demo", "anchored", "shorthand"),
    ),
    BenchmarkCase(
        "pet_search",
        "(cat|dog)s?",
        "xxdogs walked by",
        mode="search",
        tags=("interview-demo", "search", "alternation"),
    ),
    BenchmarkCase(
        "release_token_search",
        r"\d+\s\w+",
        "build 2026 portfolio",
        mode="search",
        tags=("portfolio-batch", "search", "shorthand"),
    ),
)


class Parser:
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        self.index = 0

    def parse(self) -> object:
        if self.pattern == "":
            return Concat(())
        node = self.parse_alternation()
        if self.index != len(self.pattern):
            raise RegexSyntaxError(f"unexpected token at position {self.index}: {self.pattern[self.index]!r}")
        return node

    def parse_alternation(self) -> object:
        options = [self.parse_concatenation()]
        while self.peek() == "|":
            self.consume("|")
            options.append(self.parse_concatenation())
        if len(options) == 1:
            return options[0]
        return Alternate(tuple(options))

    def parse_concatenation(self) -> object:
        parts: list[object] = []
        while True:
            token = self.peek()
            if token is None or token in ")|":
                break
            parts.append(self.parse_quantified())
        if not parts:
            return Concat(())
        if len(parts) == 1:
            return parts[0]
        return Concat(tuple(parts))

    def parse_quantified(self) -> object:
        node = self.parse_atom()
        while True:
            token = self.peek()
            if token in {"*", "+", "?"}:
                self.index += 1
                node = Repeat(node, token)
                continue
            break
        return node

    def parse_atom(self) -> object:
        token = self.peek()
        if token is None:
            raise RegexSyntaxError("unexpected end of pattern")
        if token == "(":
            self.consume("(")
            node = self.parse_alternation()
            if self.peek() != ")":
                raise RegexSyntaxError("unclosed group")
            self.consume(")")
            return node
        if token == ".":
            self.consume(".")
            return Dot()
        if token == "[":
            return self.parse_character_class()
        if token == "^":
            self.consume("^")
            return Anchor("start")
        if token == "$":
            self.consume("$")
            return Anchor("end")
        if token == "\\":
            self.consume("\\")
            shorthand = self.parse_shorthand_class_token()
            if shorthand is not None:
                return CharacterClass((shorthand,), negated=False)
            return Literal(self.parse_escape_char(in_class=False))
        if token in {"*", "+", "?", ")", "|"}:
            raise RegexSyntaxError(f"unexpected token {token!r} at position {self.index}")
        self.index += 1
        return Literal(token)

    def parse_character_class(self) -> CharacterClass:
        self.consume("[")
        negated = False
        if self.peek() == "^":
            negated = True
            self.consume("^")

        terms: list[CharacterClassTerm] = []
        first = True
        while True:
            token = self.peek()
            if token is None:
                raise RegexSyntaxError("unclosed character class")
            if token == "]" and not first:
                self.consume("]")
                break
            first = False

            item = self.parse_class_item()
            if isinstance(item, CharacterClassTerm):
                terms.append(item)
                continue

            start = item
            if self.peek() == "-":
                self.consume("-")
                if self.peek() in {None, "]"}:
                    terms.append(CharacterClassTerm(frozenset({start})))
                    terms.append(CharacterClassTerm(frozenset({"-"})))
                    if self.peek() == "]":
                        self.consume("]")
                        break
                    continue
                end_item = self.parse_class_item()
                if isinstance(end_item, CharacterClassTerm):
                    raise RegexSyntaxError("character class ranges must use literal endpoints")
                if ord(start) > ord(end_item):
                    raise RegexSyntaxError(f"invalid range {start}-{end_item}")
                terms.append(
                    CharacterClassTerm(
                        frozenset(chr(code) for code in range(ord(start), ord(end_item) + 1))
                    )
                )
            else:
                terms.append(CharacterClassTerm(frozenset({start})))

        if not terms:
            raise RegexSyntaxError("empty character class")
        return CharacterClass(tuple(terms), negated=negated)

    def parse_class_item(self) -> str | CharacterClassTerm:
        token = self.peek()
        if token is None:
            raise RegexSyntaxError("unexpected end of character class")
        if token == "\\":
            self.consume("\\")
            shorthand = self.parse_shorthand_class_token()
            if shorthand is not None:
                return shorthand
            return self.parse_escape_char(in_class=True)
        self.index += 1
        return token

    def parse_shorthand_class_token(self) -> CharacterClassTerm | None:
        token = self.peek()
        if token is None:
            raise RegexSyntaxError("dangling escape")
        lookup = {
            "d": CharacterClassTerm(ASCII_DIGITS),
            "D": CharacterClassTerm(ASCII_DIGITS, negated=True),
            "w": CharacterClassTerm(ASCII_WORD),
            "W": CharacterClassTerm(ASCII_WORD, negated=True),
            "s": CharacterClassTerm(ASCII_WHITESPACE),
            "S": CharacterClassTerm(ASCII_WHITESPACE, negated=True),
        }
        shorthand = lookup.get(token)
        if shorthand is None:
            return None
        self.index += 1
        return shorthand

    def parse_escape_char(self, *, in_class: bool) -> str:
        token = self.peek()
        if token is None:
            raise RegexSyntaxError("dangling escape")
        self.index += 1
        mapping = {"n": "\n", "t": "\t", "r": "\r"}
        if token in mapping:
            return mapping[token]
        if token in {"\\", ".", "*", "+", "?", "|", "(", ")", "[", "]", "-", "^", "$"}:
            return token
        if in_class:
            return token
        return token

    def peek(self) -> str | None:
        if self.index >= len(self.pattern):
            return None
        return self.pattern[self.index]

    def consume(self, expected: str) -> None:
        actual = self.peek()
        if actual != expected:
            raise RegexSyntaxError(f"expected {expected!r}, got {actual!r}")
        self.index += 1


class Compiler:
    def __init__(self) -> None:
        self.states: list[State] = []

    def build(self, pattern: str) -> tuple[list[State], int, object]:
        ast = Parser(pattern).parse()
        fragment = self.compile(ast)
        match_index = self.new_state(State("MATCH"))
        self.patch(fragment.outs, match_index)
        return self.states, fragment.start, ast

    def compile(self, node: object) -> Fragment:
        if isinstance(node, Literal):
            index = self.new_state(State("CHAR", char=node.value))
            return Fragment(index, [(index, "out1")])
        if isinstance(node, Dot):
            index = self.new_state(State("ANY"))
            return Fragment(index, [(index, "out1")])
        if isinstance(node, CharacterClass):
            index = self.new_state(State("CLASS", class_terms=node.terms, negated=node.negated))
            return Fragment(index, [(index, "out1")])
        if isinstance(node, Anchor):
            kind = "BOL" if node.kind == "start" else "EOL"
            index = self.new_state(State(kind))
            return Fragment(index, [(index, "out1")])
        if isinstance(node, Concat):
            if not node.parts:
                index = self.new_state(State("EPSILON"))
                return Fragment(index, [(index, "out1")])
            current = self.compile(node.parts[0])
            for part in node.parts[1:]:
                next_fragment = self.compile(part)
                self.patch(current.outs, next_fragment.start)
                current = Fragment(current.start, next_fragment.outs)
            return current
        if isinstance(node, Alternate):
            options = [self.compile(option) for option in node.options]
            start = self.new_state(State("SPLIT", out1=options[0].start, out2=options[1].start if len(options) > 1 else None))
            outs = []
            for fragment in options:
                outs.extend(fragment.outs)
            current = Fragment(start, outs)
            for fragment in options[2:]:
                start = self.new_state(State("SPLIT", out1=current.start, out2=fragment.start))
                outs = current.outs + fragment.outs
                current = Fragment(start, outs)
            return current
        if isinstance(node, Repeat):
            fragment = self.compile(node.node)
            if node.mode == "*":
                split = self.new_state(State("SPLIT", out1=fragment.start))
                self.patch(fragment.outs, split)
                return Fragment(split, [(split, "out2")])
            if node.mode == "+":
                split = self.new_state(State("SPLIT", out1=fragment.start))
                self.patch(fragment.outs, split)
                return Fragment(fragment.start, [(split, "out2")])
            if node.mode == "?":
                split = self.new_state(State("SPLIT", out1=fragment.start))
                return Fragment(split, fragment.outs + [(split, "out2")])
        raise TypeError(f"unsupported AST node: {node!r}")

    def new_state(self, state: State) -> int:
        self.states.append(state)
        return len(self.states) - 1

    def patch(self, outs: Iterable[tuple[int, str]], target: int) -> None:
        for index, field_name in outs:
            setattr(self.states[index], field_name, target)


def ast_to_dict(node: object) -> object:
    if isinstance(node, Literal):
        return {"type": "literal", "value": node.value}
    if isinstance(node, Dot):
        return {"type": "dot"}
    if isinstance(node, CharacterClass):
        rendered_terms = [
            {"chars": "".join(sorted(term.chars)), "negated": term.negated}
            for term in node.terms
        ]
        payload: dict[str, object] = {"type": "class", "terms": rendered_terms, "negated": node.negated}
        if len(node.terms) == 1 and not node.terms[0].negated:
            payload["chars"] = "".join(sorted(node.terms[0].chars))
        return payload
    if isinstance(node, Concat):
        return {"type": "concat", "parts": [ast_to_dict(part) for part in node.parts]}
    if isinstance(node, Alternate):
        return {"type": "alternate", "options": [ast_to_dict(option) for option in node.options]}
    if isinstance(node, Repeat):
        return {"type": "repeat", "mode": node.mode, "node": ast_to_dict(node.node)}
    if isinstance(node, Anchor):
        return {"type": "anchor", "kind": node.kind}
    raise TypeError(f"unsupported AST node: {node!r}")


def state_to_dict(index: int, state: State) -> dict[str, object]:
    entry: dict[str, object] = {"index": index, "kind": state.kind}
    if state.char is not None:
        entry["char"] = state.char
    if state.class_terms is not None:
        entry["terms"] = [
            {"chars": "".join(sorted(term.chars)), "negated": term.negated}
            for term in state.class_terms
        ]
        if len(state.class_terms) == 1 and not state.class_terms[0].negated:
            entry["chars"] = "".join(sorted(state.class_terms[0].chars))
        entry["negated"] = state.negated
    if state.out1 is not None:
        entry["out1"] = state.out1
    if state.out2 is not None:
        entry["out2"] = state.out2
    return entry


def states_to_dict(states: list[State]) -> list[dict[str, object]]:
    return [state_to_dict(index, state) for index, state in enumerate(states)]


class RegexEngine:
    def __init__(self, pattern: str) -> None:
        compiler = Compiler()
        self.states, self.start, self.ast = compiler.build(pattern)
        self.pattern = pattern

    def _add_state(self, collection: set[int], index: int | None, pos: int, text: str, visited: set[int]) -> None:
        if index is None or index in visited:
            return
        visited.add(index)
        state = self.states[index]
        if state.kind in {"EPSILON", "SPLIT"}:
            self._add_state(collection, state.out1, pos, text, visited)
            self._add_state(collection, state.out2, pos, text, visited)
            return
        if state.kind == "BOL":
            if pos == 0:
                self._add_state(collection, state.out1, pos, text, visited)
            return
        if state.kind == "EOL":
            if pos == len(text):
                self._add_state(collection, state.out1, pos, text, visited)
            return
        collection.add(index)

    def _closure(self, indices: Iterable[int], pos: int, text: str) -> set[int]:
        result: set[int] = set()
        visited: set[int] = set()
        for index in indices:
            self._add_state(result, index, pos, text, visited)
        return result

    def _state_matches(self, state: State, char: str) -> bool:
        if state.kind == "CHAR":
            return state.char == char
        if state.kind == "ANY":
            return True
        if state.kind == "CLASS":
            matched = any(
                (char not in term.chars) if term.negated else (char in term.chars)
                for term in (state.class_terms or ())
            )
            if state.negated:
                matched = not matched
            return matched
        return False

    def _contains_match(self, indices: Iterable[int]) -> bool:
        return any(self.states[index].kind == "MATCH" for index in indices)

    def _render_state_set(self, indices: Iterable[int]) -> list[dict[str, object]]:
        return [state_to_dict(index, self.states[index]) for index in sorted(indices)]

    def _step(self, active: set[int], char: str, next_pos: int, text: str) -> set[int]:
        raw_next: set[int] = set()
        for index in active:
            state = self.states[index]
            if state.kind == "MATCH":
                continue
            if self._state_matches(state, char):
                raw_next.add(state.out1)  # type: ignore[arg-type]
        return self._closure(raw_next, next_pos, text)

    def _step_with_details(
        self,
        active: set[int],
        char: str,
        next_pos: int,
        text: str,
    ) -> tuple[set[int], list[dict[str, object]], list[int]]:
        raw_next: set[int] = set()
        transitions: list[dict[str, object]] = []
        for index in sorted(active):
            state = self.states[index]
            transition: dict[str, object] = {
                "state": state_to_dict(index, state),
                "matched": False,
            }
            if state.kind == "MATCH":
                transition["note"] = "accept state does not consume characters"
                transitions.append(transition)
                continue
            matched = self._state_matches(state, char)
            transition["matched"] = matched
            if matched:
                transition["target"] = state.out1
                raw_next.add(state.out1)  # type: ignore[arg-type]
            transitions.append(transition)
        next_active = self._closure(raw_next, next_pos, text)
        return next_active, transitions, sorted(raw_next)

    def fullmatch(self, text: str) -> bool:
        active = self._closure([self.start], 0, text)
        for position, char in enumerate(text, start=1):
            active = self._step(active, char, position, text)
            if not active:
                return False
        return self._contains_match(self._closure(active, len(text), text))

    def search(self, text: str) -> dict[str, object] | None:
        starts = [0] if self.pattern.startswith("^") else list(range(len(text) + 1))
        for start in starts:
            active = self._closure([self.start], start, text)
            best_end: int | None = start if self._contains_match(active) else None
            for end in range(start + 1, len(text) + 1):
                active = self._step(active, text[end - 1], end, text)
                if not active:
                    break
                if self._contains_match(active):
                    best_end = end
            if best_end is not None:
                return {"matched": True, "start": start, "end": best_end, "match": text[start:best_end]}
        return None

    def trace_fullmatch(self, text: str) -> dict[str, object]:
        active = self._closure([self.start], 0, text)
        steps: list[dict[str, object]] = [
            {
                "phase": "start",
                "position": 0,
                "active_states": self._render_state_set(active),
                "match_active": self._contains_match(active),
            }
        ]
        stopped_early = False
        final_position = 0
        for position, char in enumerate(text, start=1):
            previous_active = set(active)
            active, transitions, raw_next = self._step_with_details(active, char, position, text)
            final_position = position
            steps.append(
                {
                    "phase": "consume",
                    "position": position,
                    "char": char,
                    "from_active_states": self._render_state_set(previous_active),
                    "transitions": transitions,
                    "raw_next_indexes": raw_next,
                    "active_states": self._render_state_set(active),
                    "match_active": self._contains_match(active),
                }
            )
            if not active:
                stopped_early = True
                break
        if not stopped_early:
            final_position = len(text)
        final_closure = self._closure(active, final_position, text)
        matched = self._contains_match(final_closure)
        steps.append(
            {
                "phase": "final",
                "position": final_position,
                "active_states": self._render_state_set(active),
                "closure_states": self._render_state_set(final_closure),
                "matched": matched,
            }
        )
        return {
            "pattern": self.pattern,
            "mode": "fullmatch",
            "text": text,
            "matched": matched,
            "stopped_early": stopped_early,
            "states": states_to_dict(self.states),
            "steps": steps,
        }

    def trace_search(self, text: str) -> dict[str, object]:
        starts = [0] if self.pattern.startswith("^") else list(range(len(text) + 1))
        attempts: list[dict[str, object]] = []
        final_result: dict[str, object] | None = None
        for start in starts:
            active = self._closure([self.start], start, text)
            best_end: int | None = start if self._contains_match(active) else None
            steps: list[dict[str, object]] = [
                {
                    "phase": "start",
                    "start": start,
                    "position": start,
                    "active_states": self._render_state_set(active),
                    "match_active": self._contains_match(active),
                }
            ]
            stopped_early = False
            for end in range(start + 1, len(text) + 1):
                previous_active = set(active)
                active, transitions, raw_next = self._step_with_details(active, text[end - 1], end, text)
                match_active = self._contains_match(active)
                if match_active:
                    best_end = end
                steps.append(
                    {
                        "phase": "consume",
                        "start": start,
                        "position": end,
                        "char": text[end - 1],
                        "from_active_states": self._render_state_set(previous_active),
                        "transitions": transitions,
                        "raw_next_indexes": raw_next,
                        "active_states": self._render_state_set(active),
                        "match_active": match_active,
                    }
                )
                if not active:
                    stopped_early = True
                    break
            result: dict[str, object]
            if best_end is None:
                result = {"matched": False, "start": start}
            else:
                result = {
                    "matched": True,
                    "start": start,
                    "end": best_end,
                    "match": text[start:best_end],
                }
            attempts.append(
                {
                    "start": start,
                    "stopped_early": stopped_early,
                    "result": result,
                    "steps": steps,
                }
            )
            if best_end is not None:
                final_result = result
                break
        return {
            "pattern": self.pattern,
            "mode": "search",
            "text": text,
            "matched": final_result is not None,
            "result": final_result or {"matched": False},
            "states": states_to_dict(self.states),
            "attempts": attempts,
        }

    def trace(self, text: str, *, mode: str = "fullmatch") -> dict[str, object]:
        if mode == "fullmatch":
            return self.trace_fullmatch(text)
        if mode == "search":
            return self.trace_search(text)
        raise ValueError(f"unsupported trace mode: {mode}")

    def explain(self) -> dict[str, object]:
        return {"pattern": self.pattern, "ast": ast_to_dict(self.ast), "states": states_to_dict(self.states)}


def normalize_search_result(match: re.Match[str] | None) -> dict[str, object]:
    if match is None:
        return {"matched": False}
    return {
        "matched": True,
        "start": match.start(),
        "end": match.end(),
        "match": match.group(0),
    }


def benchmark_case_to_dict(case: BenchmarkCase) -> dict[str, object]:
    return {
        "label": case.label,
        "pattern": case.pattern,
        "text": case.text,
        "mode": case.mode,
        "tags": list(case.tags),
    }


def normalize_benchmark_tag(raw_tag: object, *, context: str) -> str:
    if not isinstance(raw_tag, str) or not raw_tag.strip():
        raise BenchmarkSuiteError(f"{context} must be a non-empty string")
    return raw_tag.strip().lower()


def normalize_benchmark_tags(raw_tags: object, *, context: str) -> tuple[str, ...]:
    if raw_tags is None:
        return ()
    if not isinstance(raw_tags, list):
        raise BenchmarkSuiteError(f"{context} must be a list of non-empty strings when provided")

    normalized: list[str] = []
    seen: set[str] = set()
    for index, raw_tag in enumerate(raw_tags, start=1):
        tag = normalize_benchmark_tag(raw_tag, context=f"{context} entry #{index}")
        if tag in seen:
            raise BenchmarkSuiteError(f"{context} must not contain duplicate tags; found {tag!r}")
        seen.add(tag)
        normalized.append(tag)
    return tuple(normalized)


def filter_benchmark_cases(
    cases: Iterable[BenchmarkCase],
    *,
    include_tags: Iterable[str] = (),
    exclude_tags: Iterable[str] = (),
) -> tuple[list[BenchmarkCase], dict[str, list[str]] | None]:
    normalized_include = normalize_benchmark_tags(list(include_tags), context="--include-tag")
    normalized_exclude = normalize_benchmark_tags(list(exclude_tags), context="--exclude-tag")
    overlapping = sorted(set(normalized_include) & set(normalized_exclude))
    if overlapping:
        raise BenchmarkSuiteError(
            "benchmark filters cannot both include and exclude the same tag(s): " + ", ".join(overlapping)
        )

    selected = [
        case
        for case in cases
        if (not normalized_include or set(normalized_include).issubset(case.tags))
        and not (set(normalized_exclude) & set(case.tags))
    ]
    if (normalized_include or normalized_exclude) and not selected:
        raise BenchmarkSuiteError("benchmark filters removed all cases; adjust the requested tag filters")

    if not normalized_include and not normalized_exclude:
        return selected, None
    return selected, {
        "include_tags": list(normalized_include),
        "exclude_tags": list(normalized_exclude),
    }


def load_benchmark_suite(path_str: str) -> tuple[str, list[BenchmarkCase]]:
    path = Path(path_str)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise BenchmarkSuiteError(f"benchmark suite file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise BenchmarkSuiteError(
            f"invalid benchmark suite JSON in {path}: {error.msg} at line {error.lineno} column {error.colno}"
        ) from error

    if not isinstance(payload, dict):
        raise BenchmarkSuiteError("benchmark suite file must contain a top-level JSON object")

    suite_label = payload.get("suite_label", path.stem)
    if not isinstance(suite_label, str) or not suite_label.strip():
        raise BenchmarkSuiteError("benchmark suite field 'suite_label' must be a non-empty string when provided")

    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise BenchmarkSuiteError("benchmark suite field 'cases' must be a non-empty list")

    cases: list[BenchmarkCase] = []
    seen_labels: set[str] = set()
    for index, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            raise BenchmarkSuiteError(f"benchmark suite case #{index} must be a JSON object")

        label = raw_case.get("label")
        pattern = raw_case.get("pattern")
        text = raw_case.get("text")
        mode = raw_case.get("mode", "fullmatch")

        if not isinstance(label, str) or not label.strip():
            raise BenchmarkSuiteError(f"benchmark suite case #{index} field 'label' must be a non-empty string")
        normalized_label = label.strip()
        if normalized_label in seen_labels:
            raise BenchmarkSuiteError(f"benchmark suite case labels must be unique; found duplicate {normalized_label!r}")
        if not isinstance(pattern, str):
            raise BenchmarkSuiteError(f"benchmark suite case {normalized_label!r} field 'pattern' must be a string")
        if not isinstance(text, str):
            raise BenchmarkSuiteError(f"benchmark suite case {normalized_label!r} field 'text' must be a string")
        if mode not in {"fullmatch", "search"}:
            raise BenchmarkSuiteError(
                f"benchmark suite case {normalized_label!r} field 'mode' must be 'fullmatch' or 'search'"
            )
        tags = normalize_benchmark_tags(raw_case.get("tags"), context=f"benchmark suite case {normalized_label!r} field 'tags'")

        seen_labels.add(normalized_label)
        cases.append(BenchmarkCase(normalized_label, pattern, text, mode=mode, tags=tags))

    return suite_label.strip(), cases


def benchmark_callable(runner, *, iterations: int, warmup: int) -> dict[str, float | int | None]:
    for _ in range(warmup):
        runner()
    started_at = time.perf_counter()
    for _ in range(iterations):
        runner()
    elapsed_seconds = time.perf_counter() - started_at
    return {
        "iterations": iterations,
        "warmup": warmup,
        "elapsed_seconds": elapsed_seconds,
        "avg_seconds": elapsed_seconds / iterations if iterations else 0.0,
        "ops_per_second": (iterations / elapsed_seconds) if elapsed_seconds > 0 else None,
    }


def run_benchmark_case(case: BenchmarkCase, *, iterations: int, warmup: int) -> dict[str, object]:
    if case.mode not in {"fullmatch", "search"}:
        raise ValueError(f"unsupported benchmark mode: {case.mode}")

    engine = RegexEngine(case.pattern)
    compiled = re.compile(case.pattern)

    if case.mode == "fullmatch":
        def lab_runner() -> bool:
            return engine.fullmatch(case.text)

        def python_runner() -> re.Match[str] | None:
            return compiled.fullmatch(case.text)

        lab_result = {"matched": lab_runner()}
        python_result = {"matched": python_runner() is not None}
    else:
        def lab_runner() -> dict[str, object] | None:
            return engine.search(case.text)

        def python_runner() -> re.Match[str] | None:
            return compiled.search(case.text)

        lab_result = lab_runner() or {"matched": False}
        python_result = normalize_search_result(python_runner())

    lab_metrics = benchmark_callable(lab_runner, iterations=iterations, warmup=warmup)
    python_metrics = benchmark_callable(python_runner, iterations=iterations, warmup=warmup)
    lab_elapsed = float(lab_metrics["elapsed_seconds"])
    python_elapsed = float(python_metrics["elapsed_seconds"])
    faster_engine = "tie"
    if lab_elapsed < python_elapsed:
        faster_engine = "lab"
    elif python_elapsed < lab_elapsed:
        faster_engine = "python_re"

    return {
        "label": case.label,
        "mode": case.mode,
        "pattern": case.pattern,
        "text": case.text,
        "tags": list(case.tags),
        "pattern_length": len(case.pattern),
        "text_length": len(case.text),
        "agreement": lab_result == python_result,
        "lab_result": lab_result,
        "python_result": python_result,
        "lab": lab_metrics,
        "python_re": python_metrics,
        "faster_engine": faster_engine,
        "lab_vs_python_elapsed_ratio": (lab_elapsed / python_elapsed) if python_elapsed else None,
    }


def run_benchmark_report(
    cases: Iterable[BenchmarkCase],
    *,
    iterations: int,
    warmup: int,
    suite_label: str = "custom",
    suite_source: str | None = None,
    applied_filters: dict[str, list[str]] | None = None,
) -> dict[str, object]:
    benchmark_cases = list(cases)
    case_results = [run_benchmark_case(case, iterations=iterations, warmup=warmup) for case in benchmark_cases]
    report = {
        "suite_label": suite_label,
        "iterations": iterations,
        "warmup": warmup,
        "case_count": len(case_results),
        "all_cases_agree": all(case["agreement"] for case in case_results),
        "cases": case_results,
        "case_definitions": [benchmark_case_to_dict(case) for case in benchmark_cases],
        "suite_tags": sorted({tag for case in benchmark_cases for tag in case.tags}),
    }
    if suite_source is not None:
        report["suite_source"] = suite_source
    if applied_filters is not None:
        report["applied_filters"] = applied_filters
    return report


def render_benchmark_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Regex engine benchmark report",
        "",
        f"- suite: `{report['suite_label']}`",
        f"- iterations per engine: `{report['iterations']}`",
        f"- warmup iterations per engine: `{report['warmup']}`",
        f"- agreement across all cases: `{report['all_cases_agree']}`",
        f"- suite tags present: `{', '.join(report['suite_tags']) if report['suite_tags'] else 'none'}`",
    ]
    if report.get("suite_source"):
        lines.append(f"- suite source: `{report['suite_source']}`")
    if report.get("applied_filters"):
        filters = report["applied_filters"]
        lines.append(
            f"- applied filters: include `{', '.join(filters['include_tags']) if filters['include_tags'] else 'none'}`; "
            f"exclude `{', '.join(filters['exclude_tags']) if filters['exclude_tags'] else 'none'}`"
        )
    lines.extend(
        [
            "",
            "| case | mode | tags | agreement | lab ms | python re ms | lab ops/s | python ops/s | faster |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for case in report["cases"]:
        lab_ops = case["lab"]["ops_per_second"]
        python_ops = case["python_re"]["ops_per_second"]
        lines.append(
            "| {label} | {mode} | {tags} | {agreement} | {lab_ms:.3f} | {python_ms:.3f} | {lab_ops} | {python_ops} | {faster} |".format(
                label=case["label"],
                mode=case["mode"],
                tags=", ".join(case.get("tags", [])) or "—",
                agreement="yes" if case["agreement"] else "no",
                lab_ms=float(case["lab"]["elapsed_seconds"]) * 1000.0,
                python_ms=float(case["python_re"]["elapsed_seconds"]) * 1000.0,
                lab_ops=f"{float(lab_ops):.1f}" if lab_ops is not None else "n/a",
                python_ops=f"{float(python_ops):.1f}" if python_ops is not None else "n/a",
                faster=case["faster_engine"],
            )
        )
    lines.extend(["", "## Case notes", ""])
    for case in report["cases"]:
        lines.extend(
            [
                f"### {case['label']}",
                f"- mode: `{case['mode']}`",
                f"- tags: `{', '.join(case.get('tags', [])) if case.get('tags') else 'none'}`",
                f"- pattern: `{case['pattern']}`",
                f"- text: `{case['text']}`",
                f"- agreement: `{case['agreement']}`",
                f"- lab result: `{json.dumps(case['lab_result'], ensure_ascii=False)}`",
                f"- python result: `{json.dumps(case['python_result'], ensure_ascii=False)}`",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _html_escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_benchmark_html(report: dict[str, object]) -> str:
    cases = list(report["cases"])
    mode_counts = {"fullmatch": 0, "search": 0}
    faster_counts = {"lab": 0, "python_re": 0, "tie": 0}
    tag_counts: dict[str, int] = {}
    ratio_values: list[float] = []
    for case in cases:
        mode_counts[str(case["mode"])] = mode_counts.get(str(case["mode"]), 0) + 1
        faster_counts[str(case["faster_engine"])] = faster_counts.get(str(case["faster_engine"]), 0) + 1
        for tag in case.get("tags", []):
            tag_counts[str(tag)] = tag_counts.get(str(tag), 0) + 1
        ratio = case.get("lab_vs_python_elapsed_ratio")
        if isinstance(ratio, (int, float)):
            ratio_values.append(float(ratio))

    avg_ratio = sum(ratio_values) / len(ratio_values) if ratio_values else None
    generated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    filters = report.get("applied_filters")
    filter_text = "None"
    if filters:
        filter_text = (
            f"include {', '.join(filters['include_tags']) if filters['include_tags'] else 'none'} · "
            f"exclude {', '.join(filters['exclude_tags']) if filters['exclude_tags'] else 'none'}"
        )
    tag_chip_html = "".join(
        f'<span class="chip">{_html_escape(tag)} · {count}</span>' for tag, count in sorted(tag_counts.items())
    ) or '<span class="chip muted">No tags</span>'

    summary_cards = [
        ("Cases", str(report["case_count"]), "Named benchmark cases included in this report."),
        ("Agreement", "All cases agree" if report["all_cases_agree"] else "Mismatch present", "Whether the lab and Python re returned the same semantic result."),
        ("Modes", f"{mode_counts.get('fullmatch', 0)} fullmatch · {mode_counts.get('search', 0)} search", "Split between anchored whole-string checks and substring searches."),
        (
            "Speed ratio",
            f"{avg_ratio:.1f}× lab/python elapsed" if avg_ratio is not None else "n/a",
            "Average elapsed-time ratio across the cases in this suite.",
        ),
    ]
    summary_cards_html = "\n".join(
        f'''<article class="summary-card">
      <p class="summary-label">{_html_escape(label)}</p>
      <strong>{_html_escape(value)}</strong>
      <p>{_html_escape(description)}</p>
    </article>'''
        for label, value, description in summary_cards
    )

    case_rows = []
    case_cards = []
    for case in cases:
        lab_elapsed_ms = float(case["lab"]["elapsed_seconds"]) * 1000.0
        python_elapsed_ms = float(case["python_re"]["elapsed_seconds"]) * 1000.0
        lab_ops = case["lab"]["ops_per_second"]
        python_ops = case["python_re"]["ops_per_second"]
        ratio = case.get("lab_vs_python_elapsed_ratio")
        agreement_text = "yes" if case["agreement"] else "no"
        faster_engine = str(case["faster_engine"]).replace("python_re", "python re")
        row_class = "agree" if case["agreement"] else "disagree"
        lab_ops_text = f"{float(lab_ops):.1f}" if lab_ops is not None else "n/a"
        python_ops_text = f"{float(python_ops):.1f}" if python_ops is not None else "n/a"
        ratio_text = f"{float(ratio):.1f}×" if ratio is not None else "n/a"
        ratio_detail_text = f"{float(ratio):.1f}× lab/python" if ratio is not None else "n/a"
        case_tag_html = "".join(f'<span class="chip">{_html_escape(tag)}</span>' for tag in case.get("tags", [])) or '<span class="chip muted">untagged</span>'
        case_rows.append(
            f'''<tr class="{row_class}">
        <td><code>{_html_escape(case['label'])}</code></td>
        <td>{_html_escape(case['mode'])}</td>
        <td>{case_tag_html}</td>
        <td>{_html_escape(agreement_text)}</td>
        <td>{lab_elapsed_ms:.3f}</td>
        <td>{python_elapsed_ms:.3f}</td>
        <td>{lab_ops_text}</td>
        <td>{python_ops_text}</td>
        <td>{_html_escape(faster_engine)}</td>
        <td>{ratio_text}</td>
      </tr>'''
        )
        case_cards.append(
            f'''<article class="case-card">
      <div class="case-header">
        <div>
          <p class="eyebrow">{_html_escape(case['mode'])}</p>
          <h3><code>{_html_escape(case['label'])}</code></h3>
        </div>
        <span class="pill {row_class}">{_html_escape('agreement: ' + agreement_text)}</span>
      </div>
      <p class="case-copy">Pattern and sample text stay visible here so reviewers can talk through the benchmark without opening the raw JSON first.</p>
      <dl class="metric-grid">
        <div><dt>Pattern</dt><dd><code>{_html_escape(case['pattern'])}</code></dd></div>
        <div><dt>Text</dt><dd><code>{_html_escape(case['text'])}</code></dd></div>
        <div><dt>Lab elapsed</dt><dd>{lab_elapsed_ms:.3f} ms</dd></div>
        <div><dt>Python re elapsed</dt><dd>{python_elapsed_ms:.3f} ms</dd></div>
        <div><dt>Lab ops/s</dt><dd>{lab_ops_text}</dd></div>
        <div><dt>Python re ops/s</dt><dd>{python_ops_text}</dd></div>
        <div><dt>Faster engine</dt><dd>{_html_escape(faster_engine)}</dd></div>
        <div><dt>Elapsed ratio</dt><dd>{ratio_detail_text}</dd></div>
        <div><dt>Lab result</dt><dd><code>{_html_escape(json.dumps(case['lab_result'], ensure_ascii=False))}</code></dd></div>
        <div><dt>Python result</dt><dd><code>{_html_escape(json.dumps(case['python_result'], ensure_ascii=False))}</code></dd></div>
      </dl>
      <div class="chip-row">{case_tag_html}</div>
    </article>'''
        )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Regex engine benchmark dashboard — {_html_escape(report['suite_label'])}</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #f8fafc; color: #0f172a; }}
    main {{ max-width: 1380px; margin: 0 auto; padding: 2rem 1rem 3rem; }}
    h1, h2, h3 {{ line-height: 1.15; }}
    p, li, dd {{ line-height: 1.55; }}
    code {{ font-family: "SFMono-Regular", ui-monospace, monospace; word-break: break-word; }}
    .hero {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.4rem; padding: 1.4rem; background: linear-gradient(135deg, rgba(224, 231, 255, 0.96), rgba(240, 253, 250, 0.96)); box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08); }}
    .hero p {{ max-width: 78ch; }}
    .hero-meta, .chip-row {{ display: flex; flex-wrap: wrap; gap: 0.65rem; }}
    .hero-meta {{ margin-top: 1rem; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-top: 1.5rem; }}
    .summary-card, .table-shell, .case-card {{ border: 1px solid rgba(148, 163, 184, 0.28); border-radius: 1.2rem; background: rgba(255, 255, 255, 0.92); box-shadow: 0 16px 42px rgba(15, 23, 42, 0.06); }}
    .summary-card {{ padding: 1rem; }}
    .summary-label, .eyebrow {{ margin: 0; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #4338ca; }}
    .summary-card strong {{ display: block; margin-top: 0.3rem; font-size: 1.18rem; }}
    .section-title {{ margin: 1.8rem 0 0.8rem; }}
    .chip {{ display: inline-flex; align-items: center; padding: 0.4rem 0.7rem; border-radius: 999px; background: rgba(224, 231, 255, 0.85); border: 1px solid rgba(129, 140, 248, 0.28); color: #3730a3; font-size: 0.92rem; }}
    .chip.muted {{ background: rgba(226, 232, 240, 0.7); border-color: rgba(148, 163, 184, 0.3); color: #475569; }}
    .table-shell {{ overflow-x: auto; padding: 1rem; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 960px; }}
    th, td {{ padding: 0.75rem 0.65rem; border-bottom: 1px solid rgba(226, 232, 240, 0.9); text-align: left; vertical-align: top; }}
    th {{ font-size: 0.84rem; text-transform: uppercase; letter-spacing: 0.05em; color: #475569; }}
    tr.agree td {{ background: rgba(236, 253, 245, 0.45); }}
    tr.disagree td {{ background: rgba(254, 242, 242, 0.65); }}
    .case-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; margin-top: 1rem; }}
    .case-card {{ padding: 1rem; }}
    .case-header {{ display: flex; gap: 0.75rem; align-items: start; justify-content: space-between; }}
    .case-header h3 {{ margin: 0.15rem 0 0; }}
    .pill {{ display: inline-flex; align-items: center; padding: 0.4rem 0.75rem; border-radius: 999px; font-weight: 700; font-size: 0.88rem; }}
    .pill.agree {{ background: rgba(220, 252, 231, 0.9); color: #166534; }}
    .pill.disagree {{ background: rgba(254, 226, 226, 0.95); color: #b91c1c; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.85rem 1rem; margin: 1rem 0; }}
    .metric-grid dt {{ font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }}
    .metric-grid dd {{ margin: 0.15rem 0 0; }}
    .case-copy {{ margin-top: 0.8rem; }}
    @media (max-width: 820px) {{
      main {{ padding: 1rem 0.75rem 2rem; }}
      .metric-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">Regex engine lab</p>
      <h1>Benchmark dashboard — {_html_escape(report['suite_label'])}</h1>
      <p>Browser-friendly performance companion for the Thompson-NFA teaching engine. Use this page when you want the tagged benchmark suites to feel like a portfolio artifact instead of a raw terminal transcript.</p>
      <div class="hero-meta">
        <span class="chip">Generated {_html_escape(generated)}</span>
        <span class="chip">Iterations {report['iterations']}</span>
        <span class="chip">Warmup {report['warmup']}</span>
        <span class="chip">Python re faster in {faster_counts.get('python_re', 0)} case(s)</span>
        <span class="chip">Lab faster in {faster_counts.get('lab', 0)} case(s)</span>
        <span class="chip">Ties {faster_counts.get('tie', 0)}</span>
      </div>
      <p><strong>Suite source:</strong> <code>{_html_escape(report.get('suite_source', 'built-in/default or ad-hoc CLI case'))}</code><br><strong>Applied filters:</strong> <code>{_html_escape(filter_text)}</code></p>
      <div class="chip-row">{tag_chip_html}</div>
    </section>
    <section class="summary-grid">
{summary_cards_html}
    </section>
    <h2 class="section-title">Case-by-case table</h2>
    <section class="table-shell">
      <table>
        <thead>
          <tr>
            <th>Case</th>
            <th>Mode</th>
            <th>Tags</th>
            <th>Agree?</th>
            <th>Lab ms</th>
            <th>Python ms</th>
            <th>Lab ops/s</th>
            <th>Python ops/s</th>
            <th>Faster</th>
            <th>Ratio</th>
          </tr>
        </thead>
        <tbody>
{''.join(case_rows)}
        </tbody>
      </table>
    </section>
    <h2 class="section-title">Case notes</h2>
    <section class="case-grid">
{''.join(case_cards)}
    </section>
  </main>
</body>
</html>
'''


def write_text(path_str: str, content: str) -> None:
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tiny Thompson-NFA regex engine lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fullmatch_parser = subparsers.add_parser("fullmatch", help="require the pattern to match the whole string")
    fullmatch_parser.add_argument("pattern")
    fullmatch_parser.add_argument("text")

    search_parser = subparsers.add_parser("search", help="find the first match inside the string")
    search_parser.add_argument("pattern")
    search_parser.add_argument("text")

    explain_parser = subparsers.add_parser("explain", help="print AST and NFA states as JSON")
    explain_parser.add_argument("pattern")

    trace_parser = subparsers.add_parser("trace", help="print a step-by-step NFA trace as JSON")
    trace_parser.add_argument("pattern")
    trace_parser.add_argument("text")
    trace_parser.add_argument(
        "--mode",
        choices=("fullmatch", "search"),
        default="fullmatch",
        help="trace either fullmatch execution or search attempts",
    )

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="compare the lab against Python's re on one case or the built-in sample suite",
    )
    benchmark_parser.add_argument("pattern", nargs="?")
    benchmark_parser.add_argument("text", nargs="?")
    benchmark_parser.add_argument(
        "--mode",
        choices=("fullmatch", "search"),
        default="fullmatch",
        help="benchmark either fullmatch or search semantics for a custom case",
    )
    benchmark_parser.add_argument("--label", default="custom")
    benchmark_parser.add_argument(
        "--sample-suite",
        action="store_true",
        help="run the built-in ASCII-safe sample benchmark cases instead of a single custom case",
    )
    benchmark_parser.add_argument(
        "--suite-file",
        help="load a JSON benchmark suite file with one or more named cases",
    )
    benchmark_parser.add_argument(
        "--include-tag",
        action="append",
        default=[],
        help="keep only suite cases whose tags include every requested tag (repeatable; suite modes only)",
    )
    benchmark_parser.add_argument(
        "--exclude-tag",
        action="append",
        default=[],
        help="drop suite cases whose tags include any requested tag (repeatable; suite modes only)",
    )
    benchmark_parser.add_argument("--iterations", type=int, default=2000)
    benchmark_parser.add_argument("--warmup", type=int, default=200)
    benchmark_parser.add_argument("--json-out")
    benchmark_parser.add_argument("--markdown-out")
    benchmark_parser.add_argument("--html-out")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "benchmark":
        if args.iterations < 1:
            parser.error("--iterations must be >= 1")
        if args.warmup < 0:
            parser.error("--warmup must be >= 0")
        if args.sample_suite and args.suite_file:
            parser.error("benchmark cannot combine --sample-suite with --suite-file")

        suite_source = None
        applied_filters = None
        try:
            if args.sample_suite:
                if args.pattern is not None or args.text is not None:
                    parser.error("benchmark does not accept PATTERN/TEXT when --sample-suite is used")
                cases, applied_filters = filter_benchmark_cases(
                    DEFAULT_BENCHMARK_CASES,
                    include_tags=args.include_tag,
                    exclude_tags=args.exclude_tag,
                )
                suite_label = "sample-suite"
                suite_source = "built-in defaults"
            elif args.suite_file:
                if args.pattern is not None or args.text is not None:
                    parser.error("benchmark does not accept PATTERN/TEXT when --suite-file is used")
                suite_label, loaded_cases = load_benchmark_suite(args.suite_file)
                cases, applied_filters = filter_benchmark_cases(
                    loaded_cases,
                    include_tags=args.include_tag,
                    exclude_tags=args.exclude_tag,
                )
                if args.label != "custom":
                    suite_label = args.label
                suite_source = args.suite_file
            else:
                if args.include_tag or args.exclude_tag:
                    parser.error("benchmark tag filters require --sample-suite or --suite-file")
                if args.pattern is None or args.text is None:
                    parser.error("benchmark requires PATTERN and TEXT unless --sample-suite or --suite-file is used")
                cases = [BenchmarkCase(args.label, args.pattern, args.text, mode=args.mode)]
                suite_label = args.label
        except BenchmarkSuiteError as error:
            print(json.dumps({"error": str(error)}))
            return 2

        try:
            report = run_benchmark_report(
                cases,
                iterations=args.iterations,
                warmup=args.warmup,
                suite_label=suite_label,
                suite_source=suite_source,
                applied_filters=applied_filters,
            )
        except RegexSyntaxError as error:
            print(json.dumps({"error": str(error)}))
            return 2
        if args.json_out:
            write_text(args.json_out, json.dumps(report, indent=2) + "\n")
        if args.markdown_out:
            write_text(args.markdown_out, render_benchmark_markdown(report))
        if args.html_out:
            write_text(args.html_out, render_benchmark_html(report))
        print(json.dumps(report, indent=2))
        return 0

    try:
        engine = RegexEngine(args.pattern)
        if args.command == "fullmatch":
            print(json.dumps({"matched": engine.fullmatch(args.text)}))
            return 0
        if args.command == "search":
            result = engine.search(args.text)
            print(json.dumps(result or {"matched": False}))
            return 0
        if args.command == "explain":
            print(json.dumps(engine.explain(), indent=2))
            return 0
        if args.command == "trace":
            print(json.dumps(engine.trace(args.text, mode=args.mode), indent=2))
            return 0
    except RegexSyntaxError as error:
        print(json.dumps({"error": str(error)}))
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
