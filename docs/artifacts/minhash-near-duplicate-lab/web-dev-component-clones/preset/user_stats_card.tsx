type MetricsCardProps = { title: string; value: string; deltaLabel: string; trend: 'up' | 'down' };

export function UserStatsCard({ title, value, deltaLabel, trend }: MetricsCardProps) {
  const trendClass = trend === 'up' ? 'trendUp' : 'trendDown';
  return (
    <section className="cardShell">
      <header className="cardHeader">
        <h3>{title}</h3>
        <span className={trendClass}>{deltaLabel}</span>
      </header>
      <strong className="metricValue">{value}</strong>
      <p className="metricCaption">Updated from the latest dashboard snapshot.</p>
    </section>
  );
}
