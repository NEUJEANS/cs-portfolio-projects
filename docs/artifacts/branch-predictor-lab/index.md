# Branch predictor artifact gallery

A compact gallery of committed comparison cards for `branch-predictor-lab`, meant for README linking, recruiter screenshots, and quick before/after predictor discussions.

## Sweep overview card

Use this when you want one artifact that summarizes how the best predictor changes across loop, bias, aliasing, hybrid-history, and perceptron-friendly traces.

<p>
  <strong>Trace-family sweep overview</strong><br />
  <img src="./trace-family-sweep.svg" alt="Branch predictor trace-family sweep overview card" />
  <br />
  <a href="./trace-family-sweep.md">Markdown report</a>
</p>

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
      <strong>`perceptron-majority` synthetic trace</strong><br />
      <img src="./perceptron-majority-comparison.svg" alt="Perceptron-majority synthetic branch predictor comparison card" />
      <br />
      <a href="./perceptron-majority-comparison.md">Markdown report</a>
    </td>
  </tr>
</table>

## Trace setup

- Sweep overview: `python3 projects/branch-predictor-lab/branch_predictor.py sweep --trace-dir artifacts/branch-predictor-lab/sweep --markdown-out docs/artifacts/branch-predictor-lab/trace-family-sweep.md --svg-out docs/artifacts/branch-predictor-lab/trace-family-sweep.svg`
- Bundled sample trace: `projects/branch-predictor-lab/sample_trace.txt` with `--table-size 16 --history-bits 2`
- Synthetic trace: `artifacts/branch-predictor-lab/tournament-style-seed5.trace` generated with `generate tournament-style --branches 48 --seed 5`, then compared with `--table-size 16 --history-bits 4`
- Alias trace: `artifacts/branch-predictor-lab/alias-thrash-seed7.trace` generated with `generate alias-thrash --branches 48 --seed 7`, then compared with `--table-size 16 --history-bits 4`
- Perceptron trace: `artifacts/branch-predictor-lab/perceptron-majority-seed13.trace` generated with `generate perceptron-majority --branches 96 --seed 13`, then compared with `--table-size 32 --history-bits 12`

## Suggested portfolio usage

- Use the sweep overview card when you want one slide that proves different workload families reward different predictors and configs.
- Use the sample trace card when you want a clean teaching story for loop exits, alternating phases, and cache-ish branches.
- Use the `tournament-style` card when you want to show that local/global/hybrid predictors can tie or trade places depending on the trace family and history depth.
- Use the `alias-thrash` card when you want to explain table interference, conflicting branch biases, and why increasing table size can improve simple predictors without changing the trace.
- Use the `perceptron-majority` card when you want to show a neural predictor beating classic local/global tables on a long-history, linearly separable workload.
- Pair the SVG card with its Markdown report when you need both a screenshot-friendly visual and a text artifact with exact rankings.
