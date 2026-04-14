# tfidf-search-lab refresh and self-test

## Refresh notes
- TF counts term frequency inside one document.
- DF counts in how many documents a term appears.
- IDF should shrink the impact of corpus-common terms.
- Cosine similarity compares normalized weighted vectors.
- An inverted index helps candidate generation and score explanation.

## Self-test
1. Why normalize vectors before cosine similarity?
   - To compare direction/relevance instead of rewarding longer documents just for having more terms.
2. Why use smoothed IDF?
   - To avoid divide-by-zero edge cases and keep the score stable for small corpora.
3. Why keep postings by unique terms per document for DF?
   - DF measures document presence, not repeated within-document occurrences.
4. Why expose per-term contributions in the CLI output?
   - It makes the ranking understandable and easier to demo in a portfolio review.
