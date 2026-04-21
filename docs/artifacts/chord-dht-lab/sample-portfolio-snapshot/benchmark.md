# Chord lookup benchmark

- Identifier bits: `8`
- Node count: `5`
- Start nodes benchmarked: `alpha`, `charlie`
- Key count: `5`
- Case count: `10`
- Average Chord hops: `1.2`
- Average linear hops: `2`
- Total hop savings: `8`
- Improved cases: `4`
- Tied cases: `6`
- Slower cases: `0`

| Start node | Key | Responsible node | Chord hops | Linear hops | Hop savings | Chord route | Linear route |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| `alpha` | `compiler` | `charlie` | 1 | 1 | 0 | alpha → charlie | alpha → charlie |
| `alpha` | `slides` | `alpha` | 0 | 0 | 0 | alpha | alpha |
| `alpha` | `final-project` | `alpha` | 0 | 0 | 0 | alpha | alpha |
| `alpha` | `report.pdf` | `alpha` | 0 | 0 | 0 | alpha | alpha |
| `alpha` | `internship-notes` | `bravo` | 2 | 4 | 2 | alpha → echo → bravo | alpha → charlie → delta → echo → bravo |
| `charlie` | `compiler` | `charlie` | 0 | 0 | 0 | charlie | charlie |
| `charlie` | `slides` | `alpha` | 2 | 4 | 2 | charlie → bravo → alpha | charlie → delta → echo → bravo → alpha |
| `charlie` | `final-project` | `alpha` | 2 | 4 | 2 | charlie → bravo → alpha | charlie → delta → echo → bravo → alpha |
| `charlie` | `report.pdf` | `alpha` | 2 | 4 | 2 | charlie → bravo → alpha | charlie → delta → echo → bravo → alpha |
| `charlie` | `internship-notes` | `bravo` | 3 | 3 | 0 | charlie → delta → echo → bravo | charlie → delta → echo → bravo |
