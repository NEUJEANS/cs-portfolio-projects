def reconciliation_plan(status_rows):
    actions = []
    for row in status_rows:
        lag = max(row['leader_offset'] - row['replica_offset'], 0)
        if lag == 0:
            actions.append((row['node'], 'healthy'))
        elif lag < 128:
            actions.append((row['node'], 'stream'))
        else:
            actions.append((row['node'], 'snapshot'))
    return actions
