# Flashcard Quiz App Checklist

## Status
- [x] baseline CLI quiz loads CSV cards and scores answers
- [x] validate malformed or incomplete CSV input clearly
- [x] support reproducible session ordering for demos/tests
- [x] support limiting session size for focused study rounds
- [x] support retrying incorrect cards in a follow-up round
- [x] support tagged decks via an optional `tags` CSV column
- [x] support repeated `--tag` filters for topic-focused sessions
- [x] report weakest missed tags in the session summary
- [x] expand automated test coverage for new behaviors
- [x] review implementation in 3 passes and capture fixes
- [ ] add persistent study history to track weak cards over time
- [ ] add import/export support for JSON or Anki-style formats
