import argparse
import json
import math
import string
from typing import Dict, List

COMMON = {"password", "123456", "qwerty", "letmein", "admin"}
SEQUENTIAL_RUNS = (
    "0123456789",
    "9876543210",
    "abcdefghijklmnopqrstuvwxyz",
    "zyxwvutsrqponmlkjihgfedcba",
    "qwertyuiop",
    "poiuytrewq",
    "asdfghjkl",
    "lkjhgfdsa",
    "zxcvbnm",
    "mnbvcxz",
)


def count_character_set_pool(password: str) -> int:
    pool = 0
    if any(c.islower() for c in password):
        pool += 26
    if any(c.isupper() for c in password):
        pool += 26
    if any(c.isdigit() for c in password):
        pool += 10
    if any(c in string.punctuation for c in password):
        pool += len(string.punctuation)
    if any(c.isspace() for c in password):
        pool += 1
    return pool


def longest_repeated_run(password: str) -> int:
    if not password:
        return 0
    longest = current = 1
    for index in range(1, len(password)):
        if password[index] == password[index - 1]:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def has_sequential_pattern(password: str, min_length: int = 4) -> bool:
    lowered = password.lower()
    for run in SEQUENTIAL_RUNS:
        for start in range(0, len(run) - min_length + 1):
            candidate = run[start : start + min_length]
            if candidate in lowered:
                return True
    return False


def build_suggestions(reasons: List[str]) -> List[str]:
    suggestions = []
    mapping = {
        "too short": "Use at least 12-16 characters.",
        "missing lowercase": "Add lowercase letters.",
        "missing uppercase": "Add uppercase letters.",
        "missing digits": "Add digits.",
        "missing symbols": "Add symbols.",
        "common password": "Avoid common passwords or slight variations of them.",
        "contains repeated characters": "Break up repeated characters or repeated punctuation runs.",
        "contains sequential keyboard/alphabet pattern": "Avoid predictable sequences like 1234, abcd, or qwerty.",
    }
    for reason in reasons:
        suggestion = mapping.get(reason)
        if suggestion and suggestion not in suggestions:
            suggestions.append(suggestion)
    if not suggestions:
        suggestions.append("Password looks solid; store it in a password manager.")
    return suggestions


def evaluate(password: str) -> Dict[str, object]:
    reasons: List[str] = []
    categories = {
        "lowercase": any(c.islower() for c in password),
        "uppercase": any(c.isupper() for c in password),
        "digits": any(c.isdigit() for c in password),
        "symbols": any(c in string.punctuation for c in password),
    }
    pool = count_character_set_pool(password)
    entropy = round(len(password) * math.log2(max(pool, 1)), 2) if pool else 0.0

    if len(password) < 12:
        reasons.append("too short")
    for name, ok in categories.items():
        if not ok:
            reasons.append(f"missing {name}")
    if password.lower() in COMMON:
        reasons.append("common password")
    if longest_repeated_run(password) >= 3:
        reasons.append("contains repeated characters")
    if has_sequential_pattern(password):
        reasons.append("contains sequential keyboard/alphabet pattern")

    score = min(4, sum(categories.values()))
    if len(password) >= 12:
        score += 2
    elif len(password) >= 10:
        score += 1
    if entropy >= 60:
        score += 2
    elif entropy >= 45:
        score += 1
    if password.lower() in COMMON:
        score -= 3
    if longest_repeated_run(password) >= 3:
        score -= 1
    if has_sequential_pattern(password):
        score -= 1
    score = max(0, min(score, 8))

    if len(reasons) >= 3:
        rating = "weak"
    elif score >= 7:
        rating = "strong"
    elif score >= 4:
        rating = "medium"
    else:
        rating = "weak"

    return {
        "rating": rating,
        "score": score,
        "max_score": 8,
        "entropy_bits": entropy,
        "length": len(password),
        "character_sets": categories,
        "reasons": reasons,
        "suggestions": build_suggestions(reasons),
    }


def format_text_report(result: Dict[str, object]) -> str:
    lines = [
        f"Rating: {result['rating']}",
        f"Score: {result['score']}/{result['max_score']}",
        f"Entropy (estimated bits): {result['entropy_bits']}",
        f"Length: {result['length']}",
        "Character sets:",
    ]
    for key, enabled in result["character_sets"].items():
        lines.append(f"- {key}: {'yes' if enabled else 'no'}")
    if result["reasons"]:
        lines.append("Reasons:")
        lines.extend(f"- {reason}" for reason in result["reasons"])
    lines.append("Suggestions:")
    lines.extend(f"- {item}" for item in result["suggestions"])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Password strength auditor")
    parser.add_argument("password", help="Password to evaluate")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)
    result = evaluate(args.password)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(format_text_report(result))


if __name__ == "__main__":
    main()
