from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class State:
    length: int = 0
    link: int = -1
    transitions: Dict[str, int] = field(default_factory=dict)
    occurrences: int = 0
    first_pos: int = -1


class SuffixAutomaton:
    def __init__(self) -> None:
        self.states: List[State] = [State()]
        self.last = 0
        self._propagated = False
        self._text = ""

    @classmethod
    def from_text(cls, text: str) -> "SuffixAutomaton":
        automaton = cls()
        automaton._text = text
        for index, char in enumerate(text):
            automaton.extend(char, index)
        automaton._propagate_occurrences()
        return automaton

    def extend(self, char: str, index: int) -> None:
        cur = len(self.states)
        self.states.append(State(length=self.states[self.last].length + 1, occurrences=1, first_pos=index))
        p = self.last

        while p >= 0 and char not in self.states[p].transitions:
            self.states[p].transitions[char] = cur
            p = self.states[p].link

        if p == -1:
            self.states[cur].link = 0
        else:
            q = self.states[p].transitions[char]
            if self.states[p].length + 1 == self.states[q].length:
                self.states[cur].link = q
            else:
                clone = len(self.states)
                self.states.append(
                    State(
                        length=self.states[p].length + 1,
                        link=self.states[q].link,
                        transitions=dict(self.states[q].transitions),
                        occurrences=0,
                        first_pos=self.states[q].first_pos,
                    )
                )
                while p >= 0 and self.states[p].transitions.get(char) == q:
                    self.states[p].transitions[char] = clone
                    p = self.states[p].link
                self.states[q].link = clone
                self.states[cur].link = clone

        self.last = cur
        self._propagated = False

    def _propagate_occurrences(self) -> None:
        if self._propagated:
            return
        order = sorted(range(1, len(self.states)), key=lambda idx: self.states[idx].length, reverse=True)
        for idx in order:
            link = self.states[idx].link
            if link >= 0:
                self.states[link].occurrences += self.states[idx].occurrences
        self._propagated = True

    def _walk(self, pattern: str) -> Optional[int]:
        state = 0
        for char in pattern:
            nxt = self.states[state].transitions.get(char)
            if nxt is None:
                return None
            state = nxt
        return state

    def contains(self, pattern: str) -> bool:
        if pattern == "":
            return True
        return self._walk(pattern) is not None

    def occurrence_count(self, pattern: str) -> int:
        if pattern == "":
            return len(self._text) + 1
        self._propagate_occurrences()
        state = self._walk(pattern)
        return 0 if state is None else self.states[state].occurrences

    def distinct_substring_count(self) -> int:
        return sum(self.states[idx].length - self.states[self.states[idx].link].length for idx in range(1, len(self.states)))

    def longest_repeated_substring(self, min_occurrences: int = 2) -> str:
        if min_occurrences < 2:
            raise ValueError("min_occurrences must be at least 2 for repeated substrings.")
        self._propagate_occurrences()
        best_state = 0
        best_length = 0
        for idx, state in enumerate(self.states):
            if state.occurrences >= min_occurrences and state.length > best_length:
                best_state = idx
                best_length = state.length
        if best_length == 0:
            return ""
        end = self.states[best_state].first_pos + 1
        start = end - best_length
        return self._text[start:end]

    def longest_common_substring(self, other: str) -> str:
        state = 0
        length = 0
        best_length = 0
        best_end = 0

        for index, char in enumerate(other):
            while state and char not in self.states[state].transitions:
                state = self.states[state].link
                length = self.states[state].length

            nxt = self.states[state].transitions.get(char)
            if nxt is not None:
                state = nxt
                length += 1
            else:
                state = 0
                length = 0

            if length > best_length:
                best_length = length
                best_end = index + 1

        return other[best_end - best_length : best_end]

    def summary(self) -> dict:
        return {
            "text_length": len(self._text),
            "state_count": len(self.states),
            "distinct_substrings": self.distinct_substring_count(),
            "longest_repeated_substring": self.longest_repeated_substring(),
        }


def load_text(text: Optional[str], file_path: Optional[str]) -> str:
    if text is not None and file_path is not None:
        raise ValueError("Provide either --text or --file, not both.")
    if file_path is not None:
        return Path(file_path).read_text(encoding="utf-8")
    if text is None:
        raise ValueError("Provide --text or --file.")
    return text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze strings with a suffix automaton.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_text_source(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--text")
        subparser.add_argument("--file")

    stats = subparsers.add_parser("stats", help="Show summary stats for a string.")
    add_text_source(stats)

    contains = subparsers.add_parser("contains", help="Check whether a pattern exists.")
    add_text_source(contains)
    contains.add_argument("pattern")

    count = subparsers.add_parser("count", help="Count substring occurrences.")
    add_text_source(count)
    count.add_argument("pattern")

    repeat = subparsers.add_parser("longest-repeat", help="Show the longest repeated substring.")
    add_text_source(repeat)
    repeat.add_argument("--min-occurrences", type=int, default=2)

    lcs = subparsers.add_parser("lcs", help="Find the longest common substring between two strings.")
    add_text_source(lcs)
    lcs.add_argument("--other", required=True)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    text = load_text(getattr(args, "text", None), getattr(args, "file", None))
    automaton = SuffixAutomaton.from_text(text)

    if args.command == "stats":
        print(json.dumps(automaton.summary(), indent=2))
    elif args.command == "contains":
        print("yes" if automaton.contains(args.pattern) else "no")
    elif args.command == "count":
        print(automaton.occurrence_count(args.pattern))
    elif args.command == "longest-repeat":
        try:
            print(automaton.longest_repeated_substring(min_occurrences=args.min_occurrences))
        except ValueError as error:
            parser.error(str(error))
    elif args.command == "lcs":
        print(automaton.longest_common_substring(args.other))
    else:
        parser.error(f"Unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
