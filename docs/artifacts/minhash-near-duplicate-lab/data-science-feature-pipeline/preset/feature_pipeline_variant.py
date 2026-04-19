def build_features(events):
    normalized = []
    for sample in events:
        click_ratio = min(sample['clicks'], 500) / 500
        watch_ratio = min(sample['dwell_seconds'], 300) / 300
        normalized.append({'click_rate': click_ratio, 'dwell_rate': watch_ratio, 'converted': sample['converted']})
    return normalized
