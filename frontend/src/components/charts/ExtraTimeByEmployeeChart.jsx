import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { extraTimeByEmployeeData } from "../../data/mockCharts";
import { CHART_HEIGHT, COLORS } from "./chartConfig";
import { CustomTooltip } from "./ChartTooltip";

function ExtraTimeByEmployeeChart({ width }) {
  const topExtraTime = [...extraTimeByEmployeeData]
    .filter((item) => item.horasExtra > 0)
    .sort((a, b) => b.horasExtra - a.horasExtra)
    .slice(0, 10);

  const dynamicHeight = Math.max(CHART_HEIGHT, topExtraTime.length * 42);

  return (
    <BarChart
      width={width}
      height={dynamicHeight}
      data={topExtraTime}
      layout="vertical"
      margin={{ top: 20, right: 30, left: 80, bottom: 10 }}
    >
      <CartesianGrid strokeDasharray="3 3" horizontal={false} />

      <XAxis type="number" />

      <YAxis
        type="category"
        dataKey="employee"
        width={80}
      />

      <Tooltip content={<CustomTooltip />} />
      <Legend />

      <Bar
        dataKey="horasExtra"
        name="Horas extra"
        fill={COLORS.primary}
        radius={[0, 8, 8, 0]}
        isAnimationActive={false}
      />
    </BarChart>
  );
}

export default ExtraTimeByEmployeeChart;