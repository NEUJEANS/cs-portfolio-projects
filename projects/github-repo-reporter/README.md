# github-repo-reporter

## Overview
Fetch a GitHub user's or organization's public repositories, follow paginated results, and generate a richer portfolio-style summary.

## Why this is a stronger portfolio project
- demonstrates real HTTP API integration against GitHub's REST API
- handles pagination instead of silently stopping at the first 30 repos
- supports both individual and organization reporting for broader real-world usefulness
- supports filtering, topic analysis, and multiple output formats for CLI usability
- can save generated reports directly to disk for portfolio artifacts or periodic snapshots
- supports optional authenticated requests and recent-activity filtering for larger or rate-limited report runs
- includes pure helpers and tests for parsing, filtering, summarization, formatting, auth header construction, and file output

## Stack
- Node.js
- built-in `https`
- built-in `fs/promises`
- built-in `node:test`

## Features
- fetches all public repositories for a GitHub user or organization via pagination
- excludes forks and archived repositories by default for cleaner summaries
- optional filters for language, forks, archived repos, and minimum push date
- optional authenticated requests via a token stored in an environment variable
- JSON, plain-text, and Markdown report output
- optional `--out` flag to write the generated report to a file while still printing it
- summary includes repo count, star totals, fork/watcher/issue totals, code-size estimate, top repos, language mix, topic breakdown, and most recent push

## Usage
```bash
node reporter.js octocat
node reporter.js octocat --format text --top 3
node reporter.js openai --org --format markdown
node reporter.js openai --org --language Python --include-archived
node reporter.js openai --org --pushed-since 2026-01-01 --format markdown --out reports/openai-report.md
GITHUB_TOKEN="$YOUR_GITHUB_TOKEN" node reporter.js microsoft --org --token-env GITHUB_TOKEN --pushed-since 2026-03-01
```

Use `--org` when the subject is an organization rather than an individual user.
Use `--pushed-since` with an ISO date or datetime such as `2026-04-01` or `2026-04-01T12:00:00Z`.
Use `--token-env` to name an environment variable that contains a GitHub token when you need higher rate limits.

## Test
```bash
npm test
```

## Brief implementation notes
- uses `GET /users/{username}/repos` and `GET /orgs/{org}/repos`
- uses `per_page=100` support for fewer requests
- follows the REST API `Link` header to fetch additional pages safely
- relies on the repo list payload's `topics` field to compute topic trends without extra per-repo API calls
- sends `Accept: application/vnd.github+json` and `X-GitHub-Api-Version` headers, and optionally `Authorization: Bearer <token>`
- filters recent activity after fetch with `--pushed-since` so the reporter can narrow large result sets without changing API compatibility
- keeps summarization, formatting, auth header, and file-output logic separate from HTTP fetching for testability

## Future Improvements
- add date-window filters such as `--updated-since` and `--created-since`
- include contributor or license breakdowns
- cache fetched responses for repeated portfolio snapshots
