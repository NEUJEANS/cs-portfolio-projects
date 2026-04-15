# GitHub repo reporter research — 2026-04-15

## Goal
Pick one meaningful slice to make `github-repo-reporter` stronger for portfolio use.

## Findings
- GitHub REST docs recommend `Accept: application/vnd.github+json` for repository list requests.
- GitHub REST docs recommend sending `Authorization: Bearer <token>` when using authenticated requests.
- Repository list endpoints support standard pagination, sorting, and `per_page=100`, but they do not expose a direct `pushed_since` filter on the list call.
- Because `pushed_since` is not a native query parameter on the list endpoint, the safest compatible design is to fetch paginated results normally and then filter by `pushed_at` locally.

## Slice chosen
- add `--token-env <ENV_VAR>` so the CLI can opt into authenticated requests without hardcoding secrets
- add `--pushed-since <ISO date>` so the report can focus on recent work and stay useful for portfolio snapshots

## Why this slice
- improves the realism of the project by addressing API rate limits and real reporting workflows
- stays testable because auth-header construction and date filtering can be covered with pure unit tests
- leaves room for future follow-ups like `--updated-since`, caching, or contributor/license analysis
