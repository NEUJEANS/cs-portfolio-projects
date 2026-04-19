def normalize_rows(rows):
    cleaned = []
    for row in rows:
        clicks = min(row['clicks'], 500) / 500
        dwell = min(row['dwell_seconds'], 300) / 300
        cleaned.append({'click_rate': clicks, 'dwell_rate': dwell, 'converted': row['converted']})
    return cleaned
