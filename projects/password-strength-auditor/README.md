# password-strength-auditor

A small Python CLI that evaluates password strength, estimates entropy, and explains *why* a password is risky. It is designed as a portfolio-friendly security-flavored project: simple enough to read in one sitting, but substantial enough to discuss scoring heuristics, defensive validation, and test coverage in interviews.

## Highlights
- estimates entropy from detected character sets
- scores passwords on a simple 8-point rubric
- flags short passwords, common passwords, repeated-character runs, and predictable sequences such as `1234`, `abcd`, or `qwerty`
- returns actionable suggestions instead of only a label
- supports both human-readable and JSON output
- includes unit tests plus a subprocess CLI test

## Files
- `password_auditor.py` — scoring logic and CLI
- `test_password_auditor.py` — unit and CLI coverage

## Usage

### Text output
```bash
python3 password_auditor.py "M0on!River!2026"
```

### JSON output
```bash
python3 password_auditor.py "Abcd1111!!" --json
```

## Example output
```text
Rating: medium
Score: 5/8
Entropy (estimated bits): 65.55
Length: 10
Character sets:
- lowercase: yes
- uppercase: yes
- digits: yes
- symbols: yes
Reasons:
- too short
- contains repeated characters
- contains sequential keyboard/alphabet pattern
Suggestions:
- Use at least 12-16 characters.
- Break up repeated characters or repeated punctuation runs.
- Avoid predictable sequences like 1234, abcd, or qwerty.
```

## Test
```bash
python3 -m unittest discover -s . -p "test_*.py"
```

## Interview talking points
- balancing entropy estimation with heuristic checks for common human patterns
- designing a scoring rubric that stays readable and explainable
- testing both pure functions and CLI behavior
- limitations of homegrown password scoring compared with mature estimators like zxcvbn

## Future improvements
- detect dictionary-word substitutions more robustly
- add batch auditing from stdin or files
- compare multiple candidate passwords side by side
- add packaging metadata and a console-script entry point
