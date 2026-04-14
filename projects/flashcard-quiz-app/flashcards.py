import argparse
import csv
import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class Card:
    prompt: str
    answer: str
    tags: tuple[str, ...] = ()


REQUIRED_COLUMNS = {"prompt", "answer"}
OPTIONAL_COLUMNS = {"tags"}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


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
            'version': 2,
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
        'version': max(int(data.get('version', 1)), 2),
        'sessions_run': int(data.get('sessions_run', 0)),
        'total_attempts': int(data.get('total_attempts', 0)),
        'total_correct': int(data.get('total_correct', 0)),
        'cards': cards,
    }


def save_history(path: str | Path, history: dict) -> None:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(history, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def update_history(history: dict, card_results: Sequence[dict], *, now: str | None = None) -> dict:
    timestamp = now or utc_now_iso()
    updated = {
        'version': max(int(history.get('version', 1)), 2),
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
        previous_streak = int(card_entry.get('streak', 0))
        is_correct = bool(result['correct'])
        streak = previous_streak + 1 if is_correct else 0
        card_entry.update({
            'prompt': prompt,
            'answer': answer,
            'tags': list(result['tags']),
            'times_seen': int(card_entry.get('times_seen', 0)) + 1,
            'times_correct': int(card_entry.get('times_correct', 0)) + int(is_correct),
            'times_incorrect': int(card_entry.get('times_incorrect', 0)) + int(not is_correct),
            'last_result': 'correct' if is_correct else 'incorrect',
            'last_seen_at': timestamp,
            'streak': streak,
        })
        if 'first_seen_at' not in card_entry:
            card_entry['first_seen_at'] = timestamp
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


def build_recommendations(history: dict, limit: int = 5) -> list[dict]:
    recommendations: list[dict] = []
    for entry in history.get('cards', {}).values():
        prompt = str(entry.get('prompt', '')).strip()
        if not prompt:
            continue
        seen = int(entry.get('times_seen', 0))
        correct = int(entry.get('times_correct', 0))
        incorrect = int(entry.get('times_incorrect', 0))
        streak = int(entry.get('streak', 0))
        accuracy = correct / seen if seen else 0.0
        miss_rate = incorrect / seen if seen else 0.0
        score = (incorrect * 3) + ((1.0 - accuracy) * 4) + max(0, 2 - streak)

        if incorrect == 0 and streak >= 3 and accuracy >= 0.85:
            action = 'space out'
            reason = f'mastered recently ({correct}/{seen} correct, streak {streak})'
        elif entry.get('last_result') == 'incorrect' or (seen <= 2 and correct == 0):
            action = 'relearn now'
            reason = f'fragile memory ({incorrect} misses, streak {streak})'
            score += 2
        elif seen <= 2 or accuracy < 0.7 or streak == 0:
            action = 'review soon'
            reason = f'needs reinforcement ({correct}/{seen} correct overall)'
            score += 1
        else:
            action = 'review later'
            reason = f'stable but worth revisiting ({correct}/{seen} correct, streak {streak})'

        recommendations.append({
            'prompt': prompt,
            'action': action,
            'reason': reason,
            'score': score,
            'accuracy': accuracy,
            'times_seen': seen,
            'streak': streak,
        })

    action_priority = {
        'relearn now': 0,
        'review soon': 1,
        'review later': 2,
        'space out': 3,
    }
    recommendations.sort(
        key=lambda item: (
            action_priority.get(item['action'], 99),
            -item['score'],
            item['accuracy'],
            item['prompt'],
        )
    )
    return recommendations[:limit]


def print_recommendations(history: dict, limit: int = 5) -> None:
    recommendations = build_recommendations(history, limit=limit)
    if not recommendations:
        print('Recommendations: no history available yet')
        return
    print('Recommendations:')
    for item in recommendations:
        print(f"- {item['prompt']}: {item['action']} — {item['reason']}")


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
    p.add_argument('--show-recommendations', action='store_true', help='Print spaced-repetition study recommendations from history')
    p.add_argument('--recommend-limit', type=int, default=5, help='Number of study recommendations to print when enabled')
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

    missing_history_flags = []
    if args.show_history_summary:
        missing_history_flags.append('--show-history-summary')
    if args.show_recommendations:
        missing_history_flags.append('--show-recommendations')
    if missing_history_flags and not args.history_path:
        joined_flags = ' and '.join(missing_history_flags)
        p.exit(2, f'Error: {joined_flags} require --history-path\n')
    if args.recommend_limit <= 0:
        p.exit(2, 'Error: --recommend-limit must be a positive integer\n')

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
        if args.show_recommendations:
            print_recommendations(history, limit=args.recommend_limit)


if __name__ == '__main__':
    main()
