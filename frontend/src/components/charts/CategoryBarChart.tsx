import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtCompacto, fmtValor } from "../../utils/format";
import { CORES, eixoProps } from "./chartTheme";

export interface BarItem {
  rotulo: string;
  valor: number;
  detalhe?: string;
}

interface CategoryBarChartProps {
  data: BarItem[];
  nomeValor: string;
  height?: number;
}

export default function CategoryBarChart({ data, nomeValor, height = 220 }: CategoryBarChartProps) {
  return (
    <div role="img" aria-label={`Gráfico de barras: ${nomeValor}`} style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 5, right: 8, bottom: 5, left: 8 }}>
          <CartesianGrid stroke={CORES.grade} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="rotulo" interval={0} {...eixoProps} />
          <YAxis tickFormatter={fmtCompacto} width={52} {...eixoProps} />
          <Tooltip
            formatter={(v) => [fmtValor(Number(v)), nomeValor]}
            labelFormatter={(l, itens) => {
              const detalhe = (itens?.[0]?.payload as BarItem | undefined)?.detalhe;
              return detalhe ? `${l} — ${detalhe}` : String(l);
            }}
          />
          <Bar isAnimationActive={false} dataKey="valor" name={nomeValor} fill={CORES.barra} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
