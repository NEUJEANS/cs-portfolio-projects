# Chord DHT stabilization comparison refresh

Date: 2026-04-15
Project: `chord-dht-lab`

## Refresher
- A good comparison report should keep the underlying per-mode data, not only the winning summary, so later tooling can render charts or deep links without re-running simulations.
- When comparing partial convergence, raw finger-match counts need a normalized ratio because different scenarios can have different live node counts.
- If a mode never fully converges within the round budget, `stabilized_round` should stay `null` instead of pretending convergence happened after the last round.

## Self-test
- Can I compute the first round that fully stabilizes by scanning each round summary? Yes.
- Can I rank unfinished runs fairly? Yes: keep `stabilized_round=null` and compare final normalized finger progress as a fallback signal.
- Should the CLI accept repeated `--mode` flags? Yes: that keeps the command composable while defaulting to all supported modes.
