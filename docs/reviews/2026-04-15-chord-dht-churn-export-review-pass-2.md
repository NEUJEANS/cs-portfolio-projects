# Chord churn export review - pass 2

- Scope reviewed: CSV export usefulness for spreadsheets/charts.
- Issue found: CSV rows did not record the finger repair mode, so exported data lost an important experimental variable once separated from the command invocation.
- Fix applied: added a `finger_repair_mode` column to churn CSV output and updated CLI/tests accordingly.
- Verification: `python3 -m unittest tests/test_chord_dht_lab.py`
