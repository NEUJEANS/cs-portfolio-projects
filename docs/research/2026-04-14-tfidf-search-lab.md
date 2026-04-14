# tfidf-search-lab research notes

## Goal
Build a compact CLI project that demonstrates core information-retrieval ideas in a portfolio-friendly way.

## Brief findings
- An inverted index maps terms to the documents containing them, which avoids scanning every document for each query.
- TF-IDF weighting keeps common terms from dominating rankings while rewarding terms that are distinctive inside the corpus.
- Cosine similarity is a simple, explainable way to rank query/document vectors once both are weighted into the same term space.
- Basic tokenization and stopword filtering are enough for a small educational search engine demo.
- Top-k result selection should be deterministic and easy to inspect.

## Implementation decisions for this slice
- Python 3, standard library only.
- Index `.txt` and `.md` files in one directory.
- Lowercase tokenization with alphanumeric terms plus apostrophes.
- Smoothed IDF: `log((1 + N) / (1 + df)) + 1`.
- L2-normalize document and query vectors, then rank with cosine similarity.
- Explain scores with matched terms and per-term weights to make the project interview-friendly.

## Good future extensions
- incremental index persistence
- phrase / boolean search
- BM25 ranking mode
- snippet extraction with highlighted matches
