import argparse
import csv
import random
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Card:
    prompt: str
    answer: str


REQUIRED_COLUMNS = {"prompt", "answer"}


def load_cards(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError('CSV file is empty or missing a header row')

        fieldnames = {name.strip() for name in reader.fieldnames if name and name.strip()}
        missing = REQUIRED_COLUMNS - fieldnames
        if missing:
            raise ValueError(f"CSV file missing required columns: {', '.join(sorted(missing))}")

        cards = []
        for index, row in enumerate(reader, start=2):
            prompt = (row.get('prompt') or '').strip()
            answer = (row.get('answer') or '').strip()
            if not prompt or not answer:
                raise ValueError(f'Row {index} must include non-empty prompt and answer values')
            cards.append(Card(prompt, answer))

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

    for card in cards:
        asked += 1
        given = input(f'{card.prompt}: ')
        if normalize_answer(given) == normalize_answer(card.answer):
            correct += 1
            print('Correct!')
        else:
            incorrect_cards.append(card)
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

    return {
        'unique_cards': len(cards),
        'attempts': asked,
        'correct': correct,
        'incorrect': asked - correct,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description='Flashcard quiz app')
    p.add_argument('csv_path')
    p.add_argument('--limit', type=int, help='Study only the first N cards from the shuffled deck')
    p.add_argument('--seed', type=int, help='Shuffle seed for reproducible study sessions')
    p.add_argument('--retry-incorrect', action='store_true', help='Ask missed cards one additional time')
    args = p.parse_args(argv)

    try:
        cards = load_cards(args.csv_path)
        session_cards = build_session(cards, limit=args.limit, seed=args.seed)
    except ValueError as exc:
        p.exit(2, f'Error: {exc}\n')

    summary = run_quiz(session_cards, retry_incorrect=args.retry_incorrect)
    print(
        f"Summary: {summary['correct']} correct / {summary['attempts']} attempts "
        f"across {summary['unique_cards']} unique cards"
    )


if __name__ == '__main__':
    main()
