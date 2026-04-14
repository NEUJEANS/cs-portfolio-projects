# Library Manager Review Pass 3 — 2026-04-14

## Focus
CLI usability and error clarity.

## Issue found
Invalid `overdue --date` input would surface a raw date parsing error instead of a clean user-facing message.

## Fix applied
Wrapped date parsing with a clearer `YYYY-MM-DD` guidance message and aligned the README examples with the stronger circulation workflow.

## Result
The CLI is easier to demo and less brittle during manual usage.
