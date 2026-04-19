type SummaryCardProps = { heading: string; total: string; changeText: string; direction: 'up' | 'down' };

export function EngagementSummaryCard({ heading, total, changeText, direction }: SummaryCardProps) {
  const directionClass = direction === 'up' ? 'trendUp' : 'trendDown';
  return (
    <section className="cardShell">
      <header className="cardHeader">
        <h3>{heading}</h3>
        <span className={directionClass}>{changeText}</span>
      </header>
      <strong className="metricValue">{total}</strong>
      <p className="metricCaption">Refreshed from the newest analytics snapshot.</p>
    </section>
  );
}
