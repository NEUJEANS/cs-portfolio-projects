# external-merge-sort-lab

A Python CLI that demonstrates external merge sort for integer datasets that are larger than memory by splitting the input into sorted runs and merging them with a configurable k-way fan-in.

## Why this project matters
- shows systems-aware algorithm design instead of only in-memory textbook sorting
- demonstrates chunking, temporary run generation, and heap-based k-way merge logic
- gives a portfolio-friendly example of performance trade-offs through `chunk_size` and `fan_in`

## Features
- parses integers from newline- or comma-separated text files
- supports comments with `# ...` in input files
- creates sorted runs in temporary storage and merges them in multiple rounds when needed
- prints machine-readable JSON stats for run count and merge rounds

## Usage
```bash
python3 external_merge_sort.py sample_numbers.txt sorted_numbers.txt --chunk-size 3 --fan-in 2 --stats
```

Example output:
```json
{
  "chunk_size": 3,
  "merge_fan_in": 2,
  "merge_rounds": 2,
  "runs_created": 4,
  "total_numbers": 10
}
```

## Test
```bash
python3 -m unittest discover -s . -p 'test_*.py'
```

## Future improvements
- stream values instead of loading the entire source file before run generation
- support CSV column selection and richer benchmark reporting
- compare external merge sort metrics against in-memory sort baselines
