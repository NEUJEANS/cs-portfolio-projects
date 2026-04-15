# Static Site Generator Review — Pass 2

## Focus
Markdown rendering safety and malformed-link behavior.

## Findings
1. Inline link rendering used a simple regex that left stray `)` characters when URLs contained nested parentheses.
2. Unsafe protocols like `javascript:` needed an explicit allowlist path.

## Fixes applied
- Added `sanitizeHref()` to allow safe relative URLs, anchors, mailto, and HTTP(S) links while blocking unsafe protocols.
- Replaced one-shot regex link parsing with a small balanced-parentheses scanner.
- Added regression coverage for blocked `javascript:` links and safe URLs with nested parentheses.

## Status
Pass complete; output is cleaner and safer for portfolio demos.
