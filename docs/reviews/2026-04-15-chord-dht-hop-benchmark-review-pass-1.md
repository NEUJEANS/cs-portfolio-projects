# Chord DHT hop benchmark review — pass 1

## Focus
Project/docs completeness after adding the benchmark slice.

## Issue found
- The implementation gained a new benchmark capability, but the README and checklist still described the project as if routing traces and join previews were the newest artifacts.

## Fix applied
- Updated `projects/chord-dht-lab/README.md` with benchmark features, usage, and design notes.
- Updated `docs/checklists/chord-dht-lab.md` so the new slice is marked complete and the next follow-up remains explicit.

## Result
- The project narrative now matches the shipped CLI and tests.
