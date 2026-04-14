# URL Shortener HTTP Alias + Analytics Review — Pass 2

Date: 2026-04-14

## Focus
Routing edge cases.

## Issue found
- Route matching used the raw request path, so query strings could interfere with redirect and endpoint resolution.

## Fix applied
- Normalize requests through `urlsplit(...).path` before route dispatch.
- Verified redirects still update click analytics when query strings are present.

## Result
- Cleaner HTTP behavior and less surprising path handling.
