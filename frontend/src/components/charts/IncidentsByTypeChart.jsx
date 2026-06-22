import { Cell, Legend, Pie, PieChart, Tooltip } from "recharts";

import { incidentsByTypeData } from "../../data/mockCharts";
import { CHART_HEIGHT, PIE_COLORS } from "./chartConfig";
import { CustomPieTooltip } from "./ChartTooltip";

function IncidentsByTypeChart({ width }) {
  return (
    <PieChart width={width} height={CHART_HEIGHT}>
      <Pie
        data={incidentsByTypeData}
        dataKey="value"
        nameKey="name"
        cx="50%"
        cy="43%"
        innerRadius={65}
        outerRadius={105}
        paddingAngle={4}
        labelLine={false}
        label={({ name, value }) => `${name}: ${value}`}
        isAnimationActive={false}
      >
        {incidentsByTypeData.map((entry, index) => (
          <Cell
            key={`incident-${entry.name}`}
            fill={PIE_COLORS[index % PIE_COLORS.length]}
          />
        ))}
      </Pie>

      <Tooltip content={<CustomPieTooltip />} />
      <Legend verticalAlign="bottom" height={40} />
    </PieChart>
  );
}

export default IncidentsByTypeChart;