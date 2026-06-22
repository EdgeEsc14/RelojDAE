function MetricCard({ icon: Icon, title, value, description }) {
  return (
    <article className="metric-card">
      <div className="metric-icon">
        <Icon size={22} />
      </div>

      <div>
        <p>{title}</p>
        <strong>{value}</strong>
        <span>{description}</span>
      </div>
    </article>
  );
}

export default MetricCard;