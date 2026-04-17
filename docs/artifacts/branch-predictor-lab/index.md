# Branch predictor artifact gallery

A compact gallery of committed comparison cards for `branch-predictor-lab`, meant for README linking, recruiter screenshots, and quick before/after predictor discussions.

## Comparison cards

<table>
  <tr>
    <td valign="top" width="50%">
      <strong>Bundled sample trace</strong><br />
      <img src="./sample-trace-comparison.svg" alt="Sample trace branch predictor comparison card" />
      <br />
      <a href="./sample-trace-comparison.md">Markdown report</a>
    </td>
    <td valign="top" width="50%">
      <strong>`tournament-style` synthetic trace</strong><br />
      <img src="./tournament-style-comparison.svg" alt="Tournament-style synthetic branch predictor comparison card" />
      <br />
      <a href="./tournament-style-comparison.md">Markdown report</a>
    </td>
  </tr>
  <tr>
    <td valign="top" width="50%">
      <strong>`alias-thrash` synthetic trace</strong><br />
      <img src="./alias-thrash-comparison.svg" alt="Alias-thrash synthetic branch predictor comparison card" />
      <br />
      <a href="./alias-thrash-comparison.md">Markdown report</a>
    </td>
    <td valign="top" width="50%">
      <strong>What this new card highlights</strong><br />
      Static PC-index aliasing buckets, conflicting taken/not-taken biases, and why a larger table can improve even the same simple predictor.
    </td>
  </tr>
</table>

## Trace setup

- Bundled sample trace: `projects/branch-predictor-lab/sample_trace.txt` with `--table-size 16 --history-bits 2`
- Synthetic trace: `artifacts/branch-predictor-lab/tournament-style-seed5.trace` generated with `generate tournament-style --branches 48 --seed 5`, then compared with `--table-size 16 --history-bits 4`
- Alias trace: `artifacts/branch-predictor-lab/alias-thrash-seed7.trace` generated with `generate alias-thrash --branches 48 --seed 7`, then compared with `--table-size 16 --history-bits 4`

## Suggested portfolio usage

- Use the sample trace card when you want a clean teaching story for loop exits, alternating phases, and cache-ish branches.
- Use the `tournament-style` card when you want to show that local/global/hybrid predictors can tie or trade places depending on the trace family and history depth.
- Use the `alias-thrash` card when you want to explain table interference, conflicting branch biases, and why increasing table size can improve simple predictors without changing the trace.
- Pair the SVG card with its Markdown report when you need both a screenshot-friendly visual and a text artifact with exact rankings.
