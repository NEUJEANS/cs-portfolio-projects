# branch-predictor-lab 작업 정리

- Timestamp: 2026-04-18T03:31:46Z
- Project: `branch-predictor-lab`
- Implementation commit: `66a3984`

## 이번 변경
- `perceptron-sweep` CLI를 추가해서 하나의 trace에서 perceptron threshold/weight-limit 조합을 배치로 비교하고, best/default/saturation 상태를 JSON·Markdown·SVG로 바로 남길 수 있게 했다.
- `simulate --predictor perceptron`에 `--threshold` / `--weight-limit` 오버라이드를 붙여서 sweep에서 찾은 설정을 단일 실행으로 재현할 수 있게 했다.
- `perceptron-majority` seeded trace 기준으로 committed tuning artifact(`docs/artifacts/branch-predictor-lab/perceptron-tuning-sweep.{md,svg}`)를 생성했고, gallery/README/checklist도 새 neural tuning slice에 맞게 갱신했다.
- 이번 grid에서는 default heuristic(`threshold=37`, `weight_limit=74`)보다 낮은 threshold(`19`)가 1개 misprediction을 줄였고, 낮은 clamp에서 saturation이 어디서 생기는지도 artifact에서 바로 보이게 정리했다.

## 실행한 테스트 / 리뷰
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py perceptron-sweep artifacts/branch-predictor-lab/perceptron-majority-seed13.trace --table-size 32 --history-bits 12 --thresholds 19 28 37 46 55 --weight-limits 18 37 74 148 --markdown-out docs/artifacts/branch-predictor-lab/perceptron-tuning-sweep.md --svg-out docs/artifacts/branch-predictor-lab/perceptron-tuning-sweep.svg --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py simulate artifacts/branch-predictor-lab/perceptron-majority-seed13.trace --predictor perceptron --table-size 32 --history-bits 12 --threshold 37 --weight-limit 74 --json`
- secret scan: `/home/user1_admin/.openclaw/workspace/.bin/trufflehog git "file://$PWD" --results=verified,unknown --fail`
- review pass 1: string-escape 회귀로 생긴 syntax error 2개를 수정하고 compile/test green으로 복구
- review pass 2: tuning SVG footer가 canvas 바깥으로 내려가던 문제와 Markdown 표 헤더의 raw `|` 문제를 수정
- review pass 3: README에 tuned perceptron simulate / committed perceptron-sweep 재현 명령이 빠져 있던 drift를 찾아 보강

## 다음 단계
- 다음 cron run에서는 `branch-predictor-lab`의 남은 후보인 budget-normalized sweep을 추가해서 predictor별 state-bit budget 비교까지 artifact gallery에서 이어서 보여주면 된다.
