import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { auditEventsByModuleData } from "../../data/mockCharts";
import { CHART_HEIGHT, COLORS } from "./chartConfig";
import { CustomTooltip } from "./ChartTooltip";

function AuditEventsByModuleChart({ width }) {
  return (
    <AreaChart
      width={width}
      height={CHART_HEIGHT}
      data={auditEventsByModuleData}
      margin={{ top: 20, right: 20, left: 0, bottom: 10 }}
    >
      <CartesianGrid strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey="module" />
      <YAxis allowDecimals={false} />
      <Tooltip content={<CustomTooltip />} />
      <Legend />

      <Area
        type="monotone"
        dataKey="eventos"
        name="Eventos"
        stroke={COLORS.primary}
        fill={COLORS.primaryLight}
        fillOpacity={0.28}
        strokeWidth={3}
        isAnimationActive={false}
      />
    </AreaChart>
  );
}

export default AuditEventsByModuleChart;