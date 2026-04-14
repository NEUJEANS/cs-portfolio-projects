# Regex engine lab review pass 1

## Focus
Behavior and edge-case smoke testing.

## Checks run
- alternation/group search for `(cat|dog)s?`
- quantifier handling for `a*` and `colou?r`
- anchor behavior for `^dog$`
- character-class handling for `[^a-c]+` and `[a-c-]+`
- escaped metacharacter handling for `a\+b`

## Findings
- Initial implementation bug: the engine assumed NFA start state index `0`, which broke alternation because the actual start state can be a later `SPLIT` node.
- Initial search implementation returned too early and produced shortest matches like `a` for `[a-z]+` in `123abc456`.

## Fixes applied
- stored the compiled fragment start index and used it as the real engine entry state
- changed `search` to keep the leftmost start but prefer the longest match at that start position

## Result
Core unit and CLI tests passed after the fixes.
