import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { delaysByEmployeeData } from "../../data/mockCharts";
import { CHART_HEIGHT, COLORS } from "./chartConfig";
import { CustomTooltip } from "./ChartTooltip";

function DelaysByEmployeeChart({ width }) {
  const topDelays = [...delaysByEmployeeData]
    .filter((item) => item.retardos > 0)
    .sort((a, b) => b.retardos - a.retardos)
    .slice(0, 10);

  const dynamicHeight = Math.max(CHART_HEIGHT, topDelays.length * 42);

  return (
    <BarChart
      width={width}
      height={dynamicHeight}
      data={topDelays}
      layout="vertical"
      margin={{ top: 20, right: 30, left: 80, bottom: 10 }}
    >
      <CartesianGrid strokeDasharray="3 3" horizontal={false} />

      <XAxis type="number" allowDecimals={false} />

      <YAxis
        type="category"
        dataKey="employee"
        width={80}
      />

      <Tooltip content={<CustomTooltip />} />
      <Legend />

      <Bar
        dataKey="retardos"
        name="Retardos"
        fill={COLORS.warning}
        radius={[0, 8, 8, 0]}
        isAnimationActive={false}
      />
    </BarChart>
  );
}

export default DelaysByEmployeeChart;