import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CORES, TRACO_PREVISTO, eixoProps } from "./chartTheme";

interface LossChartProps {
  data: { epoca: number; perda_treino: number; perda_validacao: number }[];
  melhorEpoca: number;
}

/** Curva de aprendizado: perda (MSE na escala padronizada) de treino e validação por época. */
export default function LossChart({ data, melhorEpoca }: LossChartProps) {
  return (
    <div role="img" aria-label={`Curva de perda por época; melhor época ${melhorEpoca}`} style={{ width: "100%", height: 220 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 16, bottom: 5, left: 0 }}>
          <CartesianGrid stroke={CORES.grade} strokeDasharray="3 3" />
          <XAxis dataKey="epoca" {...eixoProps} />
          <YAxis width={48} tickFormatter={(v) => Number(v).toFixed(2)} {...eixoProps} />
          <Tooltip formatter={(v, nome) => [Number(v).toFixed(4), nome]} labelFormatter={(l) => `Época ${l}`} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line isAnimationActive={false} dataKey="perda_treino" name="Treino" stroke={CORES.real} dot={false} strokeWidth={2} />
          <Line isAnimationActive={false} dataKey="perda_validacao" name="Validação" stroke={CORES.previsto} dot={false} strokeWidth={2}
            strokeDasharray={TRACO_PREVISTO} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
