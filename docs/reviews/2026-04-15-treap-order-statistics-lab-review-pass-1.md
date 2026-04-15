# Review pass 1 — treap-order-statistics-lab

## Checks
- read implementation for BST + heap-order invariants
- ran `python3 -m unittest projects/treap-order-statistics-lab/test_treap_order_statistics_lab.py`

## Findings
- found one incorrect test expectation: demo `rank_50` should be `5`, not `4`, because the default sample has five keys smaller than 50

## Fixes applied
- updated `test_cli_demo_outputs_valid_json` to expect `5`
