export type EngagementPoint = { current: number; previous: number };

export function buildEngagementSummary(point: EngagementPoint) {
  const delta = point.current - point.previous;
  const direction = delta >= 0 ? 'up' : 'down';
  const percent = point.previous === 0 ? 100 : Math.round((delta / point.previous) * 100);
  return {
    total: point.current.toLocaleString(),
    changeText: `${percent}% vs last week`,
    direction,
  };
}
