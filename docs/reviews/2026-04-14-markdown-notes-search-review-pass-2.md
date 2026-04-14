# Markdown Notes Search Review Pass 2

Date: 2026-04-14

## Checks
- reviewed parser flow for precedence and implicit `AND`
- verified README examples align with supported query syntax
- re-ran unit tests after parser audit

## Issue found
- README had not yet documented operator precedence and implicit `AND`, which would make the feature harder to understand in portfolio review

## Fix applied
- expanded README query notes and examples to explain `NOT > AND > OR`, parentheses, phrases, and implicit `AND`

## Result
- code and docs now describe the same behavior clearly
