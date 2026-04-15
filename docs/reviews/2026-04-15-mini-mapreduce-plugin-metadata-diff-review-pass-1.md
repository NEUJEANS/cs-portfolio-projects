# Review pass 1 — mini-mapreduce plugin metadata diff slice

- audited the new `inspect-plugin --diff` flow for CLI misuse and backward compatibility
- issue found: the first draft needed a clean guard for `--diff` with only one `--plugin`, otherwise the flag would be ambiguous for users
- fix applied: added a parser-level validation with a targeted error message and test coverage in both project-level and repo-level suites
