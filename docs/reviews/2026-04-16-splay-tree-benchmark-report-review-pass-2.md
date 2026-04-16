# Splay tree benchmark report review pass 2

- Focus: fallback behavior when the user writes only the Markdown report without saving JSON/CSV artifacts.
- Issue found: the talking-points section always claimed the report linked to committed JSON/CSV artifacts, even when no artifact paths were provided.
- Fix applied: made the final talking point conditional so no-artifact runs now suggest `--json-output/--csv-output` instead of claiming links already exist.
