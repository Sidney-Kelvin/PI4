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
import { fmtCompacto, fmtPeriodo, fmtValor } from "../../utils/format";
import { CORES, TRACO_BASELINE, TRACO_PREVISTO, eixoProps } from "./chartTheme";

interface RealVsPredictedChartProps {
  data: { data: string; real: number; previsto: number; baseline: number }[];
  mostrarBaseline?: boolean;
  height?: number;
}

/** Comparação no período de teste (dados nunca vistos no treino): real x LSTM x baseline. */
export default function RealVsPredictedChart({ data, mostrarBaseline = true, height = 300 }: RealVsPredictedChartProps) {
  return (
    <div role="img" aria-label="Gráfico de vendas reais versus previstas no período de teste" style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 16, bottom: 5, left: 8 }}>
          <CartesianGrid stroke={CORES.grade} strokeDasharray="3 3" />
          <XAxis dataKey="data" tickFormatter={fmtPeriodo} minTickGap={24} {...eixoProps} />
          <YAxis tickFormatter={fmtCompacto} width={56} {...eixoProps} />
          <Tooltip formatter={(v, nome) => [fmtValor(Number(v)), nome]} labelFormatter={(l) => fmtPeriodo(String(l))} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line isAnimationActive={false} type="monotone" dataKey="real" name="Real" stroke={CORES.real} strokeWidth={2} dot={false} />
          <Line isAnimationActive={false} type="monotone" dataKey="previsto" name="Previsto (LSTM)" stroke={CORES.previsto} strokeWidth={2}
            strokeDasharray={TRACO_PREVISTO} dot={false} />
          {mostrarBaseline && (
            <Line isAnimationActive={false} type="monotone" dataKey="baseline" name="Baseline sazonal" stroke={CORES.baseline}
              strokeWidth={1.5} strokeDasharray={TRACO_BASELINE} dot={false} />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
