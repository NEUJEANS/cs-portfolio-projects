# Chord churn export review - pass 1

- Scope reviewed: `projects/chord-dht-lab/chord_dht.py`, README churn export docs, churn export tests.
- Issue found: Markdown churn summary jumped straight into metrics without reminding the reader which ring the scenario started from and ended with.
- Fix applied: added `Starting nodes` and `Ending nodes` summary bullets so exported notes are self-contained in portfolio write-ups.
- Verification: `python3 -m unittest tests/test_chord_dht_lab.py`
