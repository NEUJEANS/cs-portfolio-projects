import argparse, csv, random
from dataclasses import dataclass

@dataclass
class Card:
    prompt: str
    answer: str


def load_cards(path):
    with open(path, newline='', encoding='utf-8') as f:
        return [Card(row['prompt'], row['answer']) for row in csv.DictReader(f)]


def quiz(cards, answers):
    score = 0
    results = []
    for card, given in zip(cards, answers):
        ok = card.answer.strip().lower() == given.strip().lower()
        score += int(ok)
        results.append(ok)
    return score, results


def main(argv=None):
    p = argparse.ArgumentParser(description='Flashcard quiz app')
    p.add_argument('csv_path')
    args = p.parse_args(argv)
    cards = load_cards(args.csv_path)
    random.shuffle(cards)
    score = 0
    for card in cards:
        given = input(f'{card.prompt}: ')
        if given.strip().lower() == card.answer.strip().lower():
            score += 1
    print(f'{score}/{len(cards)}')

if __name__ == '__main__':
    main()
