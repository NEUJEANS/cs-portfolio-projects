# 2026-04-15 — shamir-secret-sharing-lab review pass 1

## Focus
Initial implementation and test layout sanity check.

## Issue found
- The first version used the same `test_shamir_secret_sharing_lab.py` basename in both the project folder and top-level `tests/`, which caused pytest import-file mismatch errors.

## Fix applied
- Renamed the project-local test module to `test_project_shamir_secret_sharing_lab.py`.
- Re-ran unittest plus targeted pytest to confirm the collision was removed for this project.
