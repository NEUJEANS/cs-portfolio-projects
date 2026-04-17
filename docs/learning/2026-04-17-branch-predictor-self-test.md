# 2026-04-17 branch-predictor refresh + self-test

## Refresh points
- Use `(pc >> 2)` for table indexing so aligned instruction addresses do not waste the low two always-zero bits.
- Model the classic 2-bit saturating states as `00`, `01` => predict not taken and `10`, `11` => predict taken.
- Update gshare history after each branch with `history = ((history << 1) | taken) & mask` so the predictor keeps only the configured history width.

## Self-test cases to encode in unit tests
- Repeating loop pattern `TTTTN` should hurt one-bit more than two-bit because one-bit flips immediately after the loop exit.
- Alternating `TNTN...` on one static branch should remain hard for a bimodal predictor but become learnable for gshare with one history bit.
- Empty/comment-only traces should fail loudly so the CLI does not silently report misleading zero-work results.
