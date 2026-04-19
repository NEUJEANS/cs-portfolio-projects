def catchup_actions(nodes):
    plan = []
    for item in nodes:
        lag = max(item['leader_offset'] - item['replica_offset'], 0)
        if lag == 0:
            plan.append((item['node'], 'healthy'))
        elif lag < 128:
            plan.append((item['node'], 'stream'))
        else:
            plan.append((item['node'], 'snapshot'))
    return plan
