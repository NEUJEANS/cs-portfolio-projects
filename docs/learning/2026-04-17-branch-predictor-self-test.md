# 2026-04-17 branch-predictor refresh + self-test

## Refresh points
- Use `(pc >> 2)` for table indexing so aligned instruction addresses do not waste the low two always-zero bits.
- Model the classic 2-bit saturating states as `00`, `01` => predict not taken and `10`, `11` => predict taken.
- Update gshare history after each branch with `history = ((history << 1) | taken) & mask` so the predictor keeps only the configured history width.
- A local-history predictor needs a per-PC history register plus a pattern table indexed by that short local history, which makes repeated branch-local motifs teachable without a full CPU simulator.
- A tournament predictor only needs a small chooser table to expose when the hybrid prefers local-history vs global-history behavior on the same trace.

## Self-test cases to encode in unit tests
- Repeating loop pattern `TTTTN` should hurt one-bit more than two-bit because one-bit flips immediately after the loop exit.
- Alternating `TNTN...` on one static branch should remain hard for a bimodal predictor but become learnable for both gshare and local-history with one history bit.
- A correlated two-branch driver/follower pattern should let deeper-history gshare and the tournament chooser beat plain local-history on at least one mixed trace.
- CLI JSON output for `simulate --predictor local-history` and `simulate --predictor tournament` should expose the advanced predictor state, not just the top-line accuracy.
- Empty/comment-only traces should fail loudly so the CLI does not silently report misleading zero-work results.
