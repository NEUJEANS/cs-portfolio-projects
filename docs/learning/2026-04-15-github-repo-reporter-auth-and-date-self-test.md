# GitHub repo reporter auth/date self-test — 2026-04-15

## Refresh
- GitHub repository list endpoints do not provide a native `pushed_since` query parameter, so date filtering belongs in post-fetch filtering logic.
- Authenticated REST requests should send `Authorization: Bearer <token>` and keep the token outside the codebase.
- A CLI flag should point to an environment variable name, not the token value itself, so command history and wrap-up logs stay clean.

## Quick self-test
1. **Question:** Why is `--token-env GITHUB_TOKEN` safer than `--token ghp_...`?
   - **Answer:** It keeps the secret out of command history, docs, tests, and accidental screenshots while still allowing authenticated requests.
2. **Question:** Why should `--pushed-since` reject invalid dates early in argument parsing?
   - **Answer:** Failing fast gives the user a clear CLI error before any network requests or partial output happen.
3. **Question:** If a repo has `pushed_at = null`, should it pass a `--pushed-since` filter?
   - **Answer:** No. Without a push timestamp, it cannot satisfy a minimum recent-push constraint.
