# Mini MapReduce GitHub source-link refresh

Date: 2026-04-16 05:21 UTC
Project: `mini-mapreduce-lab`

## Goal
Add publishable GitHub blob links to `inspect-plugin` artifacts without hard-coding repo-specific filesystem paths.

## Quick refresh
- `git rev-parse --show-toplevel` gives the repo root for relative-path calculation.
- `git config --get remote.origin.url` is enough to detect GitHub remotes in `https://github.com/owner/repo.git` and `git@github.com:owner/repo.git` forms.
- `git rev-parse --abbrev-ref HEAD` gives a branch-aware ref that works for publishable blob links before the new commit hash exists.
- Blob URL shape: `https://github.com/<owner>/<repo>/blob/<ref>/<path>#L<start>-L<end>`.

## Self-test
- Normalize `git@github.com:NEUJEANS/cs-portfolio-projects.git` to `https://github.com/NEUJEANS/cs-portfolio-projects`.
- For `projects/mini-mapreduce-lab/plugins_average_score.py` lines `7-13` on branch `main`, expected URL:
  - `https://github.com/NEUJEANS/cs-portfolio-projects/blob/main/projects/mini-mapreduce-lab/plugins_average_score.py#L7-L13`

## Coding guardrails
- If the plugin file is outside a GitHub-backed repo, emit `None` instead of failing.
- Keep JSON/CSV/Markdown/HTML outputs backward compatible aside from the added source-link fields.
