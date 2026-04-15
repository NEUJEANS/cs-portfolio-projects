# Tarjan vs Kosaraju review pass 3

## Focus
README accuracy and demo-output review.

## Issue found
- The README example implied `faster_algorithm` would always be `tarjan`, which is not guaranteed across machines, interpreters, or tiny timing runs.

## Fix applied
- Reworded the example output so it shows the possible enum-style values (`tarjan | kosaraju | tie`) instead of presenting a machine-specific result as universal.

## Result
- The portfolio docs remain honest and portable while still showing the structure of the comparison output.
