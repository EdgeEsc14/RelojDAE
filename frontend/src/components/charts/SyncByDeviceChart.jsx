import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { syncByDeviceData } from "../../data/mockCharts";
import { CHART_HEIGHT, COLORS } from "./chartConfig";
import { CustomTooltip } from "./ChartTooltip";

function SyncByDeviceChart({ width }) {
  return (
    <BarChart
      width={width}
      height={CHART_HEIGHT}
      data={syncByDeviceData}
      margin={{ top: 20, right: 20, left: 0, bottom: 10 }}
    >
      <CartesianGrid strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey="device" />
      <YAxis allowDecimals={false} />
      <Tooltip content={<CustomTooltip />} />
      <Legend />

      <Bar
        dataKey="insertados"
        name="Insertados"
        fill={COLORS.success}
        radius={[8, 8, 0, 0]}
        isAnimationActive={false}
      />

      <Bar
        dataKey="duplicados"
        name="Duplicados"
        fill={COLORS.warning}
        radius={[8, 8, 0, 0]}
        isAnimationActive={false}
      />
    </BarChart>
  );
}

export default SyncByDeviceChart;