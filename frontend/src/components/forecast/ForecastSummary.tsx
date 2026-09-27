import { CalendarRange, TrendingDown, TrendingUp } from "lucide-react";
import type { PrevisaoProximoMes } from "../../types";
import { fmtData, fmtPct, fmtPeriodo, fmtValor } from "../../utils/format";

const FONTES = {
  planejamento: "calendário planejado (test.csv)",
  estimado: "calendário estimado pelas últimas 4 semanas",
  misto: "calendário planejado + estimado",
};

export default function ForecastSummary({ previsao }: { previsao: PrevisaoProximoMes }) {
  const variacao = previsao.variacao_percentual;
  const subiu = (variacao ?? 0) >= 0;
  const Seta = subiu ? TrendingUp : TrendingDown;

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white p-5">
        <p className="text-xs uppercase tracking-wide text-blue-100">
          Previsão de vendas — {fmtPeriodo(previsao.mes_referencia)}
        </p>
        <p className="text-3xl font-bold mt-2">{fmtValor(previsao.valor_previsto)}</p>
        <p className="text-xs text-blue-100 mt-2 flex items-center gap-1.5">
          <CalendarRange size={13} aria-hidden="true" />
          {fmtData(previsao.periodo_inicio)} a {fmtData(previsao.periodo_fim)} · {previsao.diario.length} dias
        </p>
      </div>

      <div className="rounded-lg border border-gray-100 p-5">
        <p className="text-xs uppercase tracking-wide text-gray-500">Variação estimada</p>
        <p className={`text-3xl font-bold mt-2 flex items-center gap-2 ${subiu ? "text-green-600" : "text-red-600"}`}>
          <Seta size={26} aria-hidden="true" />
          {fmtPct(variacao)}
        </p>
        <p className="text-xs text-gray-500 mt-2">
          em relação a {fmtPeriodo(previsao.ultimo_mes_real.periodo)} (real: {fmtValor(previsao.ultimo_mes_real.vendas)})
        </p>
      </div>

      <p className="sm:col-span-2 text-xs text-gray-500">
        Soma das previsões diárias do modelo LSTM para {previsao.lojas_referencia} lojas, usando{" "}
        {FONTES[previsao.fonte_calendario]}. Modelo versão {previsao.versao_modelo}. {previsao.observacao_moeda}
      </p>
    </div>
  );
}
