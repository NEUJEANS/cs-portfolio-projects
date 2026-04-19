# regex-engine-lab checklist

- [x] choose a new project that adds language-runtime and automata depth to the portfolio
- [x] capture compact research notes for a regex engine vertical slice
- [x] do a short parser/NFA refresh and self-test
- [x] implement parser + Thompson-style NFA compiler + CLI
- [x] add README and usage examples
- [x] add automated tests
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 shorthand escape class slice
- [x] inspect the regex engine lab and choose shorthand escape classes as the next portfolio-friendly upgrade
- [x] capture a compact research note on `\d` / `\w` / `\s` semantics and scope this lab to explicit ASCII teaching behavior
- [x] do a short parser/compiler refresh and self-test for escaped token handling inside and outside bracket classes
- [x] add a resumable slice checklist file for this upgrade
- [x] implement shorthand escape classes `\d`, `\D`, `\w`, `\W`, `\s`, and `\S` in the parser, AST, compiler, and matcher
- [x] support shorthand terms inside bracket classes and document the resulting syntax in the README
- [x] add regression coverage for positive/negative shorthand classes, bracket mixing, explain output, and CLI behavior
- [x] run tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up

## 2026-04-19 NFA trace slice
- [x] inspect the current regex engine lab and choose step-by-step NFA state tracing as the next portfolio-friendly upgrade
- [x] capture a brief research note on why Thompson-style active-state tracing is a strong teaching and debugging surface
- [x] do a short runtime refresh and self-test for epsilon closure, per-character transitions, and leftmost search attempts
- [x] add a resumable slice checklist file for this upgrade
- [x] implement JSON trace helpers for both `fullmatch` and `search`
- [x] expose the trace flow through a new CLI subcommand and keep explain/search/fullmatch behavior stable
- [x] add regression coverage for successful traces, early-stop traces, and leftmost-search attempt reporting
- [x] generate committed sample trace artifacts and document them in the README
- [x] run tests and smoke commands
- [x] complete review pass 1 and fix issues found
- [x] complete review pass 2 and fix issues found
- [x] complete review pass 3 and fix issues found
- [x] run secret scan
- [x] commit and push
- [x] append wrap-up
