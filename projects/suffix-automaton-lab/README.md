# Suffix Automaton Lab

A portfolio-ready string algorithms project that builds a suffix automaton for fast substring queries and repeated-pattern analysis.

## Why this project matters
- demonstrates a classic linear-time string data structure used in search, bioinformatics, and log analysis
- goes beyond toy matching by supporting substring counts, longest repeated substring, and longest common substring queries
- shows clean Python implementation plus a small CLI for reproducible demos

## Features
- build a suffix automaton from an input string
- test substring membership in `O(m)` for a query of length `m`
- count end-position occurrences of a substring
- compute the number of distinct substrings
- extract the longest repeated substring above a configurable occurrence threshold
- find the longest common substring between the indexed text and another string
- load text inline or from a file

## Usage
```bash
python3 suffix_automaton_lab.py stats --file sample_text.txt
python3 suffix_automaton_lab.py contains --text banana ana
python3 suffix_automaton_lab.py count --text banana ana
python3 suffix_automaton_lab.py longest-repeat --text banana --min-occurrences 2
python3 suffix_automaton_lab.py lcs --text abracadabra --other cadabrac
```

## Example output
```json
{
  "text_length": 6,
  "state_count": 10,
  "distinct_substrings": 15,
  "longest_repeated_substring": "ana"
}
```

## Testing
```bash
python3 -m pytest projects/suffix-automaton-lab/test_suffix_automaton_lab.py
```

## Future improvements
- add suffix-link visualization output for interview walkthroughs
- support top-k repeated substrings with tie-breaking controls
- benchmark against suffix arrays and trie-based substring search on larger corpora
