# File Integrity Monitor CI Exit Codes Refresh

- Standard CLI automation pattern: exit `0` for a clean diff, exit `1` when expected differences should fail CI, and reserve `2+` for usage/runtime errors.
- Keep the diff payload visible even when returning a non-zero code so shell scripts and CI logs preserve the actionable file list.
- Make opt-in failure behavior explicit with a flag like `--fail-on-changes` so interactive use still defaults to report-only mode.
