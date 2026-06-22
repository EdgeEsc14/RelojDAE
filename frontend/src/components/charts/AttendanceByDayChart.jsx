import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { attendanceByDayData } from "../../data/mockCharts";
import { CHART_HEIGHT, COLORS } from "./chartConfig";
import { CustomTooltip } from "./ChartTooltip";

function AttendanceByDayChart({ width }) {
  return (
    <BarChart
      width={width}
      height={CHART_HEIGHT}
      data={attendanceByDayData}
      margin={{ top: 20, right: 20, left: 0, bottom: 10 }}
    >
      <CartesianGrid strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey="day" />
      <YAxis allowDecimals={false} />
      <Tooltip content={<CustomTooltip />} />
      <Legend />

      <Bar
        dataKey="completos"
        name="Completos"
        fill={COLORS.success}
        radius={[8, 8, 0, 0]}
      />

      <Bar
        dataKey="retardos"
        name="Retardos"
        fill={COLORS.warning}
        radius={[8, 8, 0, 0]}
      />

      <Bar
        dataKey="faltas"
        name="Faltas"
        fill={COLORS.danger}
        radius={[8, 8, 0, 0]}
      />
    </BarChart>
  );
}

export default AttendanceByDayChart;