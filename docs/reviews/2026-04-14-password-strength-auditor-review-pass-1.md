# Review Pass 1 — password-strength-auditor — 2026-04-14

## Focus
Validate the upgraded scoring heuristics against the expanded test suite.

## What I checked
- ran `python3 -m unittest discover -s projects/password-strength-auditor -p 'test_*.py'`
- inspected the failing repeated/sequential-pattern expectation

## Issue found
- a password with multiple strong warning signs (`too short`, sequential pattern, repeated run) was still classified as `medium` because the numeric score alone outweighed the heuristic warnings

## Fix applied
- updated the rating logic so passwords with 3 or more warnings are forced to `weak`
- reran the full test suite afterward

## Result
- heuristic warnings now affect the final rating in a more realistic way
