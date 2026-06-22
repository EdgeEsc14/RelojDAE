import { Cell, Legend, Pie, PieChart, Tooltip } from "recharts";

import { deviceStatusData } from "../../data/mockCharts";
import { CHART_HEIGHT, PIE_COLORS } from "./chartConfig";
import { CustomPieTooltip } from "./ChartTooltip";

function DeviceStatusChart({ width }) {
  return (
    <PieChart width={width} height={CHART_HEIGHT}>
      <Pie
        data={deviceStatusData}
        dataKey="value"
        nameKey="name"
        cx="50%"
        cy="43%"
        outerRadius={105}
        labelLine={false}
        label={({ name, value }) => `${name}: ${value}`}
        isAnimationActive={false}
      >
        {deviceStatusData.map((entry, index) => (
          <Cell
            key={`device-${entry.name}`}
            fill={PIE_COLORS[index % PIE_COLORS.length]}
          />
        ))}
      </Pie>

      <Tooltip content={<CustomPieTooltip />} />
      <Legend verticalAlign="bottom" height={40} />
    </PieChart>
  );
}

export default DeviceStatusChart;