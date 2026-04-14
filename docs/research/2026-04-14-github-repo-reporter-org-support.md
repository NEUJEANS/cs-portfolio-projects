# GitHub Repo Reporter Research — org support

## Goal
Add a meaningful next slice to `github-repo-reporter` by supporting organization reporting in addition to user reporting.

## Brief findings
- GitHub REST exposes separate list endpoints for users and orgs.
- User repos: `GET /users/{username}/repos`
- Org repos: `GET /orgs/{org}/repos`
- Both support pagination via the `Link` header and `per_page=100`.
- This project already follows pagination cleanly, so org support fits the existing architecture with small, testable changes.

## Why this slice is worthwhile
- makes the project useful for student clubs, labs, startups, and team portfolios
- demonstrates API surface design beyond a single hard-coded endpoint
- adds stronger CLI ergonomics without introducing external dependencies

## Planned implementation
- add `buildOrgReposUrl(org, options)`
- add `--org` CLI flag to switch subject type
- update usage/help text and README examples
- extend tests for URL building, parsing, and main report flow assumptions
