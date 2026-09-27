import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtCompacto, fmtPeriodo, fmtValor } from "../../utils/format";
import { CORES, eixoProps } from "./chartTheme";

interface SalesLineChartProps {
  data: { periodo: string; vendas: number }[];
  height?: number;
  ariaLabel?: string;
}

export default function SalesLineChart({ data, height = 280, ariaLabel = "Gráfico de vendas históricas" }: SalesLineChartProps) {
  return (
    <div role="img" aria-label={ariaLabel} style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 16, bottom: 5, left: 8 }}>
          <CartesianGrid stroke={CORES.grade} strokeDasharray="3 3" />
          <XAxis dataKey="periodo" tickFormatter={fmtPeriodo} minTickGap={24} {...eixoProps} />
          <YAxis tickFormatter={fmtCompacto} width={56} {...eixoProps} />
          <Tooltip
            formatter={(v) => [fmtValor(Number(v)), "Vendas"]}
            labelFormatter={(l) => fmtPeriodo(String(l))}
          />
          <Line isAnimationActive={false} type="monotone" dataKey="vendas" name="Vendas" stroke={CORES.real} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
