export function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;

  return (
    <div className="chart-tooltip">
      <strong>{label}</strong>

      {payload.map((item) => (
        <span key={`${item.name}-${item.dataKey}`}>
          {item.name}: {item.value}
        </span>
      ))}
    </div>
  );
}

export function CustomPieTooltip({ active, payload }) {
  if (!active || !payload || payload.length === 0) return null;

  const item = payload[0];

  return (
    <div className="chart-tooltip">
      <strong>{item.name}</strong>
      <span>Valor: {item.value}</span>
    </div>
  );
}