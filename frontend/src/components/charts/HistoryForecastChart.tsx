import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PontoComparacao } from "../../types";
import { fmtCompacto, fmtPeriodo, fmtValor } from "../../utils/format";
import { CORES, TRACO_PREVISTO, eixoProps } from "./chartTheme";

interface HistoryForecastChartProps {
  data: PontoComparacao[];
  height?: number;
}

/** Histórico real (linha contínua) seguido da previsão do modelo (linha tracejada). */
export default function HistoryForecastChart({ data, height = 300 }: HistoryForecastChartProps) {
  return (
    <div role="img" aria-label="Gráfico de vendas históricas seguidas da previsão" style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 16, bottom: 5, left: 8 }}>
          <CartesianGrid stroke={CORES.grade} strokeDasharray="3 3" />
          <XAxis dataKey="periodo" tickFormatter={fmtPeriodo} minTickGap={24} {...eixoProps} />
          <YAxis tickFormatter={fmtCompacto} width={56} {...eixoProps} />
          <Tooltip
            formatter={(v, nome) => [v === null || v === undefined ? "—" : fmtValor(Number(v)), nome]}
            labelFormatter={(l) => fmtPeriodo(String(l))}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line isAnimationActive={false} type="monotone" dataKey="real" name="Real" stroke={CORES.real} strokeWidth={2} dot={false}
            connectNulls={false} />
          <Line isAnimationActive={false} type="monotone" dataKey="previsto" name="Previsão LSTM" stroke={CORES.previsto} strokeWidth={2}
            strokeDasharray={TRACO_PREVISTO} dot={false} connectNulls={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
