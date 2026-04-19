# Web-dev component clone MinHash preset

A frontend-heavy portfolio preset that highlights duplicated dashboard cards, hooks, notes, and CSS assets.

- Preset key: `web-dev-component-clones`
- Files written: 8
- Extensions: .css=1, .md=3, .ts=2, .tsx=2
- Pairs detected at the recommended threshold: 2
- Recommended glob: `*.md,*.tsx,*.ts,*.css`
- Token mode: `code`
- Normalize identifiers: `True`
- Normalize literals: `True`
- Shingle size: `4` | Hashes: `64` | Bands: `8` | Threshold: `0.15`

## Suggested scan command

```bash
python3 projects/minhash-near-duplicate-lab/minhash_lab.py corpus '<preset-root>' --glob '*.md,*.tsx,*.ts,*.css' --token-mode code --shingle-size 4 --num-hashes 64 --bands 8 --threshold 0.15 --normalize-identifiers --normalize-literals --json
```

## File cards

### `README.md`
- Type: `.md`
- Bytes: `161`
- Preview: # Dashboard component notes

### `card-shell.css`
- Type: `.css`
- Bytes: `316`
- Preview: .cardShell {

### `dashboard_story.md`
- Type: `.md`
- Bytes: `164`
- Preview: # Dashboard refactor story

### `different_domain.md`
- Type: `.md`
- Bytes: `135`
- Preview: # Different topic

### `engagement_summary_card.tsx`
- Type: `.tsx`
- Bytes: `630`
- Preview: type SummaryCardProps = { heading: string; total: string; changeText: string; direction: 'up' | 'down' };

### `use_engagement_metrics.ts`
- Type: `.ts`
- Bytes: `442`
- Preview: export type EngagementPoint = { current: number; previous: number };

### `use_user_metrics.ts`
- Type: `.ts`
- Bytes: `435`
- Preview: export type MetricPoint = { current: number; previous: number };

### `user_stats_card.tsx`
- Type: `.tsx`
- Bytes: `594`
- Preview: type MetricsCardProps = { title: string; value: string; deltaLabel: string; trend: 'up' | 'down' };

## Top near-duplicate pairs

- `engagement_summary_card.tsx` <> `user_stats_card.tsx` | exact=1.0000 estimated=1.0000 shared_bands=8
- `use_engagement_metrics.ts` <> `use_user_metrics.ts` | exact=1.0000 estimated=1.0000 shared_bands=8

