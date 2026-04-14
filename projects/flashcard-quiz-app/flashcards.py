import argparse
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
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


def build_history_key(prompt: str, answer: str) -> str:
    return f'{prompt}\t{answer}'


def load_history(path: str | Path) -> dict:
    history_path = Path(path)
    if not history_path.exists():
        return {
            'version': 1,
            'sessions_run': 0,
            'total_attempts': 0,
            'total_correct': 0,
            'cards': {},
        }

    try:
        data = json.loads(history_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise ValueError(f'History file is not valid JSON: {history_path}') from exc

    if not isinstance(data, dict):
        raise ValueError('History file must contain a JSON object')

    cards = data.get('cards', {})
    if not isinstance(cards, dict):
        raise ValueError('History file cards entry must be an object')

    return {
        'version': int(data.get('version', 1)),
        'sessions_run': int(data.get('sessions_run', 0)),
        'total_attempts': int(data.get('total_attempts', 0)),
        'total_correct': int(data.get('total_correct', 0)),
        'cards': cards,
    }


def save_history(path: str | Path, history: dict) -> None:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def update_history(history: dict, card_results: Sequence[dict]) -> dict:
    updated = {
        'version': int(history.get('version', 1)),
        'sessions_run': int(history.get('sessions_run', 0)) + 1,
        'total_attempts': int(history.get('total_attempts', 0)),
        'total_correct': int(history.get('total_correct', 0)),
        'cards': dict(history.get('cards', {})),
    }

    for result in card_results:
        updated['total_attempts'] += 1
        updated['total_correct'] += int(result['correct'])
        prompt = result['prompt']
        answer = result['answer']
        history_key = build_history_key(prompt, answer)
        card_entry = dict(updated['cards'].get(history_key, {}))
        card_entry.update({
            'prompt': prompt,
            'answer': answer,
            'tags': list(result['tags']),
            'times_seen': int(card_entry.get('times_seen', 0)) + 1,
            'times_correct': int(card_entry.get('times_correct', 0)) + int(result['correct']),
            'times_incorrect': int(card_entry.get('times_incorrect', 0)) + int(not result['correct']),
            'last_result': 'correct' if result['correct'] else 'incorrect',
        })
        updated['cards'][history_key] = card_entry

    return updated


def summarize_history(history: dict, limit: int = 3) -> dict:
    total_attempts = int(history.get('total_attempts', 0))
    total_correct = int(history.get('total_correct', 0))
    cards = []
    for entry in history.get('cards', {}).values():
        seen = int(entry.get('times_seen', 0))
        correct = int(entry.get('times_correct', 0))
        incorrect = int(entry.get('times_incorrect', 0))
        accuracy = correct / seen if seen else 0.0
        cards.append({
            'prompt': entry.get('prompt', ''),
            'times_seen': seen,
            'times_correct': correct,
            'times_incorrect': incorrect,
            'accuracy': accuracy,
        })

    weakest_cards = sorted(cards, key=lambda item: (-item['times_incorrect'], item['accuracy'], item['prompt']))[:limit]
    return {
        'sessions_run': int(history.get('sessions_run', 0)),
        'total_attempts': total_attempts,
        'total_correct': total_correct,
        'accuracy': (total_correct / total_attempts) if total_attempts else 0.0,
        'weakest_cards': weakest_cards,
    }


def run_quiz(cards: Sequence[Card], *, retry_incorrect: bool = False):
    asked = 0
    correct = 0
    incorrect_cards = []
    tag_counter: dict[str, int] = {}
    card_results: list[dict] = []

    for card in cards:
        asked += 1
        given = input(f'{card.prompt}: ')
        is_correct = normalize_answer(given) == normalize_answer(card.answer)
        card_results.append({
            'prompt': card.prompt,
            'answer': card.answer,
            'tags': card.tags,
            'correct': is_correct,
        })
        if is_correct:
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
            is_correct = normalize_answer(given) == normalize_answer(card.answer)
            card_results.append({
                'prompt': card.prompt,
                'answer': card.answer,
                'tags': card.tags,
                'correct': is_correct,
            })
            if is_correct:
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
        'card_results': card_results,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='Flashcard quiz app')
    p.add_argument('csv_path')
    p.add_argument('--limit', type=int, help='Study only the first N cards from the shuffled deck')
    p.add_argument('--seed', type=int, help='Shuffle seed for reproducible study sessions')
    p.add_argument('--retry-incorrect', action='store_true', help='Ask missed cards one additional time')
    p.add_argument('--history-path', help='Optional JSON file for persistent study history across sessions')
    p.add_argument('--show-history-summary', action='store_true', help='Print the persistent history summary after the session')
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

    if args.show_history_summary and not args.history_path:
        p.exit(2, 'Error: --show-history-summary requires --history-path\n')

    try:
        cards = load_cards(args.csv_path)
        filtered_cards = filter_cards(cards, args.tags)
        session_cards = build_session(filtered_cards, limit=args.limit, seed=args.seed)
        history = load_history(args.history_path) if args.history_path else None
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

    if history is not None:
        history = update_history(history, summary['card_results'])
        save_history(args.history_path, history)
        if args.show_history_summary:
            history_summary = summarize_history(history)
            print(
                f"History: {history_summary['total_correct']} correct / {history_summary['total_attempts']} attempts "
                f"across {history_summary['sessions_run']} sessions "
                f"({history_summary['accuracy']:.0%} accuracy)"
            )
            if history_summary['weakest_cards']:
                weakest = ', '.join(
                    f"{card['prompt']} ({card['times_incorrect']} misses)"
                    for card in history_summary['weakest_cards']
                )
                print(f'Historically weakest cards: {weakest}')


if __name__ == '__main__':
    main()
