export type MetricPoint = { current: number; previous: number };

export function buildUserMetricsSummary(point: MetricPoint) {
  const delta = point.current - point.previous;
  const direction = delta >= 0 ? 'up' : 'down';
  const percent = point.previous === 0 ? 100 : Math.round((delta / point.previous) * 100);
  return {
    value: point.current.toLocaleString(),
    deltaLabel: `${percent}% vs last week`,
    direction,
  };
}
