import argparse
import csv
import random
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class Card:
    prompt: str
    answer: str
    tags: tuple[str, ...] = ()


REQUIRED_COLUMNS = {"prompt", "answer"}
OPTIONAL_COLUMNS = {"tags"}


def parse_tags(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    seen: list[str] = []
    for part in raw.split(','):
        tag = part.strip().lower()
        if tag and tag not in seen:
            seen.append(tag)
    return tuple(seen)


def load_cards(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError('CSV file is empty or missing a header row')

        normalized_fieldnames = {name.strip() for name in reader.fieldnames if name and name.strip()}
        missing = REQUIRED_COLUMNS - normalized_fieldnames
        if missing:
            raise ValueError(f"CSV file missing required columns: {', '.join(sorted(missing))}")

        cards = []
        for index, row in enumerate(reader, start=2):
            prompt = (row.get('prompt') or '').strip()
            answer = (row.get('answer') or '').strip()
            if not prompt or not answer:
                raise ValueError(f'Row {index} must include non-empty prompt and answer values')
            cards.append(Card(prompt, answer, parse_tags(row.get('tags'))))

    if not cards:
        raise ValueError('CSV file must include at least one flashcard')

    return cards


def normalize_answer(value: str) -> str:
    return value.strip().lower()


def quiz(cards: Sequence[Card], answers: Iterable[str]):
    score = 0
    results = []
    for card, given in zip(cards, answers):
        ok = normalize_answer(card.answer) == normalize_answer(given)
        score += int(ok)
        results.append(ok)
    return score, results


def filter_cards(cards: Sequence[Card], include_tags: Optional[Sequence[str]] = None):
    if not include_tags:
        return list(cards)

    required = {tag.strip().lower() for tag in include_tags if tag and tag.strip()}
    if not required:
        return list(cards)

    filtered = [card for card in cards if required.issubset(set(card.tags))]
    if not filtered:
        raise ValueError(f"No cards matched tags: {', '.join(sorted(required))}")
    return filtered


def build_session(cards: Sequence[Card], limit: int | None = None, seed: int | None = None):
    session_cards = list(cards)
    rng = random.Random(seed)
    rng.shuffle(session_cards)
    if limit is not None:
        if limit <= 0:
            raise ValueError('limit must be a positive integer')
        session_cards = session_cards[:limit]
    return session_cards


def run_quiz(cards: Sequence[Card], *, retry_incorrect: bool = False):
    asked = 0
    correct = 0
    incorrect_cards = []
    tag_counter: dict[str, int] = {}

    for card in cards:
        asked += 1
        given = input(f'{card.prompt}: ')
        if normalize_answer(given) == normalize_answer(card.answer):
            correct += 1
            print('Correct!')
        else:
            incorrect_cards.append(card)
            for tag in card.tags:
                tag_counter[tag] = tag_counter.get(tag, 0) + 1
            print(f'Incorrect. Expected: {card.answer}')

    if retry_incorrect and incorrect_cards:
        print('\nRetry round for missed cards:')
        for card in incorrect_cards:
            asked += 1
            given = input(f'{card.prompt}: ')
            if normalize_answer(given) == normalize_answer(card.answer):
                correct += 1
                print('Correct!')
            else:
                print(f'Incorrect. Expected: {card.answer}')

    weakest_tags = [tag for tag, _ in sorted(tag_counter.items(), key=lambda item: (-item[1], item[0]))]
    return {
        'unique_cards': len(cards),
        'attempts': asked,
        'correct': correct,
        'incorrect': asked - correct,
        'weakest_tags': weakest_tags,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Flashcard quiz app')
    p.add_argument('csv_path')
    p.add_argument('--limit', type=int, help='Study only the first N cards from the shuffled deck')
    p.add_argument('--seed', type=int, help='Shuffle seed for reproducible study sessions')
    p.add_argument('--retry-incorrect', action='store_true', help='Ask missed cards one additional time')
    p.add_argument(
        '--tag',
        dest='tags',
        action='append',
        default=[],
        help='Require a tag to be present on a card. Repeat to require multiple tags.',
    )
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)

    try:
        cards = load_cards(args.csv_path)
        filtered_cards = filter_cards(cards, args.tags)
        session_cards = build_session(filtered_cards, limit=args.limit, seed=args.seed)
    except ValueError as exc:
        p.exit(2, f'Error: {exc}\n')

    summary = run_quiz(session_cards, retry_incorrect=args.retry_incorrect)
    print(
        f"Summary: {summary['correct']} correct / {summary['attempts']} attempts "
        f"across {summary['unique_cards']} unique cards"
    )
    if args.tags:
        print(f"Tag filter: {', '.join(args.tags)}")
    if summary['weakest_tags']:
        print(f"Weakest tags: {', '.join(summary['weakest_tags'])}")


if __name__ == '__main__':
    main()
