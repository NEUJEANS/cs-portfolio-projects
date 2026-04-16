# Mini Shell Redirection Review — Pass 2

## Findings
1. Pipeline failures only surfaced stderr from the last process.
2. If an earlier stage failed first, the shell fell back to a generic exit-code message and hid the useful error text.

## Fixes applied
- collected stderr from earlier pipeline stages after they exit
- joined the captured stderr snippets into the raised runtime error
- added a regression test where the first stage fails and emits `boom`

## Result
Pipeline error reporting is now more useful for demos and debugging, especially in teaching scenarios where the failing stage is not the last command.
