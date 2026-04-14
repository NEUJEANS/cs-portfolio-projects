# Research — minhash-near-duplicate-lab

## Brief notes
- shingling turns a document into overlapping token windows so local ordering still influences similarity
- exact Jaccard similarity is the clean baseline: intersection size divided by union size over shingle sets
- MinHash compresses a set into a signature whose coordinate match rate approximates Jaccard similarity
- LSH banding splits a signature into groups so likely-similar documents collide in at least one band and become candidate pairs

## Design choices for this slice
- use word shingles instead of character shingles to keep the portfolio story readable
- keep the implementation standard-library-only so the project is easy to run locally
- provide both exact pairwise comparison and a simple corpus candidate search so the project demonstrates more than one mode
- use deterministic salted SHA-256 hashing for reproducible signatures across runs

## Follow-up opportunities
- add benchmark notes comparing naive all-pairs scanning vs candidate generation
- extend the lab to code-token or character-shingle modes for source-code plagiarism demos
