# github-repo-reporter

## Overview
Fetch a user's public GitHub repositories, follow paginated results, and generate a richer portfolio-style summary.

## Why this is a stronger portfolio project
- demonstrates real HTTP API integration against GitHub's REST API
- handles pagination instead of silently stopping at the first 30 repos
- supports filtering and multiple output formats for CLI usability
- includes pure helpers and tests for parsing, filtering, summarization, and formatting

## Stack
- Node.js
- built-in `https`
- built-in `node:test`

## Features
- fetches all public repositories for a GitHub user via pagination
- excludes forks and archived repositories by default for cleaner summaries
- optional filters for language, forks, and archived repos
- JSON, plain-text, and Markdown report output
- summary includes repo count, star totals, top repos, language mix, and most recent push

## Usage
```bash
node reporter.js octocat
node reporter.js octocat --format text --top 3
node reporter.js octocat --format markdown --include-forks
node reporter.js octocat --language Python --include-archived
```

## Test
```bash
npm test
```

## Brief implementation notes
- uses GitHub's `per_page=100` support for fewer requests
- follows the REST API `link` header to fetch additional pages safely
- keeps summarization and formatting logic separate from HTTP fetching for testability

## Future Improvements
- support authenticated requests for higher rate limits
- export report files directly to disk with `--out`
- add organization-level reporting and topic breakdowns
