# branch-predictor-lab 작업 정리

- Timestamp: 2026-04-18T03:04:41Z
- Project: `branch-predictor-lab`
- Implementation commit: `4a1064e`

## 이번 변경
- `compare`/`sweep` 흐름에 dynamic gshare alias summary를 추가해서 같은 live index가 서로 다른 PC와 global-history 문맥에서 어떻게 충돌하는지 바로 볼 수 있게 했다.
- 새 요약은 `history_before`, dominant bias, cross-address/history-spread collision 개수, 충돌 이벤트 수까지 집계해서 정적 PC-index aliasing만 보던 기존 카드보다 설명력이 커졌다.
- 샘플/alias-thrash/tournament/perceptron comparison 카드와 trace-family sweep 문서를 다시 생성해 artifact gallery가 새 동적 충돌 내러티브를 그대로 보여주도록 맞췄다.
- README, 프로젝트 체크리스트, repo 체크리스트를 업데이트하고 slice 체크리스트 + review pass 3개를 추가해 다음 cron run이 바로 다음 미완료 후보로 넘어갈 수 있게 했다.

## 실행한 테스트 / 리뷰
- `python3 -m py_compile projects/branch-predictor-lab/branch_predictor.py tests/test_branch_predictor_lab.py`
- `python3 -m unittest tests.test_branch_predictor_lab`
- `.venv/bin/pytest tests/test_branch_predictor_lab.py`
- `python3 projects/branch-predictor-lab/branch_predictor.py compare projects/branch-predictor-lab/sample_trace.txt --table-size 16 --history-bits 2 --markdown-out docs/artifacts/branch-predictor-lab/sample-trace-comparison.md --svg-out docs/artifacts/branch-predictor-lab/sample-trace-comparison.svg --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py compare artifacts/branch-predictor-lab/alias-thrash-seed7.trace --table-size 16 --history-bits 4 --markdown-out docs/artifacts/branch-predictor-lab/alias-thrash-comparison.md --svg-out docs/artifacts/branch-predictor-lab/alias-thrash-comparison.svg --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py compare artifacts/branch-predictor-lab/tournament-style-seed5.trace --table-size 16 --history-bits 4 --markdown-out docs/artifacts/branch-predictor-lab/tournament-style-comparison.md --svg-out docs/artifacts/branch-predictor-lab/tournament-style-comparison.svg --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py compare artifacts/branch-predictor-lab/perceptron-majority-seed13.trace --table-size 32 --history-bits 12 --markdown-out docs/artifacts/branch-predictor-lab/perceptron-majority-comparison.md --json`
- `python3 projects/branch-predictor-lab/branch_predictor.py sweep --trace-dir artifacts/branch-predictor-lab/sweep --markdown-out docs/artifacts/branch-predictor-lab/trace-family-sweep.md --svg-out docs/artifacts/branch-predictor-lab/trace-family-sweep.svg --json`
- review pass 1: talking-point 우선순위를 조정해 dynamic gshare aliasing이 카드 상단 bullet에 보이도록 수정
- review pass 2: README/checklist drift를 정리하고 slice 체크리스트를 추가해 재개 가능 상태로 정리
- review pass 3: committed artifact와 gallery wording을 재생성/수정해 새 output shape와 narrative를 일치시킴

## 다음 단계
- `branch-predictor-lab`의 다음 slice로 perceptron threshold/weight-limit sweep artifact를 추가해 neural predictor tuning trade-off도 gallery에서 바로 비교할 수 있게 한다.
