import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { punchesByHourData } from "../../data/mockCharts";
import { CHART_HEIGHT, COLORS } from "./chartConfig";
import { CustomTooltip } from "./ChartTooltip";

function PunchesByHourChart({ width }) {
  return (
    <LineChart
      width={width}
      height={CHART_HEIGHT}
      data={punchesByHourData}
      margin={{ top: 20, right: 20, left: 0, bottom: 10 }}
    >
      <CartesianGrid strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey="hour" />
      <YAxis allowDecimals={false} />
      <Tooltip content={<CustomTooltip />} />
      <Legend />

      <Line
        type="monotone"
        dataKey="entradas"
        name="Entradas"
        stroke={COLORS.primary}
        strokeWidth={3}
        dot={{ r: 4 }}
        isAnimationActive={false}
      />

      <Line
        type="monotone"
        dataKey="salidas"
        name="Salidas"
        stroke={COLORS.accent}
        strokeWidth={3}
        dot={{ r: 4 }}
        isAnimationActive={false}
      />
    </LineChart>
  );
}

export default PunchesByHourChart;