from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import Iterable


class RegexSyntaxError(ValueError):
    """Raised when the simplified regex grammar is invalid."""


@dataclass(frozen=True)
class Literal:
    value: str


@dataclass(frozen=True)
class Dot:
    pass


@dataclass(frozen=True)
class CharacterClass:
    chars: frozenset[str]
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
    chars: frozenset[str] | None = None
    negated: bool = False


@dataclass
class Fragment:
    start: int
    outs: list[tuple[int, str]] = field(default_factory=list)


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
            return Literal(self.parse_escape(in_class=False))
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
        chars: set[str] = set()
        first = True
        while True:
            token = self.peek()
            if token is None:
                raise RegexSyntaxError("unclosed character class")
            if token == "]" and not first:
                self.consume("]")
                break
            first = False
            start = self.parse_class_char()
            if self.peek() == "-":
                saved_index = self.index
                self.consume("-")
                if self.peek() in {None, "]"}:
                    chars.add(start)
                    chars.add("-")
                    if self.peek() == "]":
                        self.consume("]")
                        break
                    continue
                end = self.parse_class_char()
                if ord(start) > ord(end):
                    raise RegexSyntaxError(f"invalid range {start}-{end}")
                chars.update(chr(code) for code in range(ord(start), ord(end) + 1))
            else:
                chars.add(start)
        if not chars:
            raise RegexSyntaxError("empty character class")
        return CharacterClass(frozenset(chars), negated=negated)

    def parse_class_char(self) -> str:
        token = self.peek()
        if token is None:
            raise RegexSyntaxError("unexpected end of character class")
        if token == "\\":
            self.consume("\\")
            return self.parse_escape(in_class=True)
        self.index += 1
        return token

    def parse_escape(self, *, in_class: bool) -> str:
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
            index = self.new_state(State("CLASS", chars=node.chars, negated=node.negated))
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
        return {"type": "class", "chars": "".join(sorted(node.chars)), "negated": node.negated}
    if isinstance(node, Concat):
        return {"type": "concat", "parts": [ast_to_dict(part) for part in node.parts]}
    if isinstance(node, Alternate):
        return {"type": "alternate", "options": [ast_to_dict(option) for option in node.options]}
    if isinstance(node, Repeat):
        return {"type": "repeat", "mode": node.mode, "node": ast_to_dict(node.node)}
    if isinstance(node, Anchor):
        return {"type": "anchor", "kind": node.kind}
    raise TypeError(f"unsupported AST node: {node!r}")


def states_to_dict(states: list[State]) -> list[dict[str, object]]:
    rendered: list[dict[str, object]] = []
    for index, state in enumerate(states):
        entry: dict[str, object] = {"index": index, "kind": state.kind}
        if state.char is not None:
            entry["char"] = state.char
        if state.chars is not None:
            entry["chars"] = "".join(sorted(state.chars))
            entry["negated"] = state.negated
        if state.out1 is not None:
            entry["out1"] = state.out1
        if state.out2 is not None:
            entry["out2"] = state.out2
        rendered.append(entry)
    return rendered


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

    def _step(self, active: set[int], char: str, next_pos: int, text: str) -> set[int]:
        raw_next: set[int] = set()
        for index in active:
            state = self.states[index]
            matched = False
            if state.kind == "CHAR":
                matched = state.char == char
            elif state.kind == "ANY":
                matched = True
            elif state.kind == "CLASS":
                contains = char in (state.chars or frozenset())
                matched = not contains if state.negated else contains
            elif state.kind == "MATCH":
                continue
            if matched:
                raw_next.add(state.out1)  # type: ignore[arg-type]
        return self._closure(raw_next, next_pos, text)

    def fullmatch(self, text: str) -> bool:
        active = self._closure([self.start], 0, text)
        for position, char in enumerate(text, start=1):
            active = self._step(active, char, position, text)
            if not active:
                return False
        return any(self.states[index].kind == "MATCH" for index in self._closure(active, len(text), text))

    def search(self, text: str) -> dict[str, object] | None:
        starts = [0] if self.pattern.startswith("^") else list(range(len(text) + 1))
        for start in starts:
            active = self._closure([self.start], start, text)
            best_end: int | None = start if any(self.states[index].kind == "MATCH" for index in active) else None
            for end in range(start + 1, len(text) + 1):
                active = self._step(active, text[end - 1], end, text)
                if not active:
                    break
                if any(self.states[index].kind == "MATCH" for index in active):
                    best_end = end
            if best_end is not None:
                return {"matched": True, "start": start, "end": best_end, "match": text[start:best_end]}
        return None

    def explain(self) -> dict[str, object]:
        return {"pattern": self.pattern, "ast": ast_to_dict(self.ast), "states": states_to_dict(self.states)}


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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
    except RegexSyntaxError as error:
        print(json.dumps({"error": str(error)}))
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
