import type { MetricasModelo } from "../../types";
import { fmtPct, fmtValor } from "../../utils/format";

interface ModelMetricsProps {
  lstm: MetricasModelo;
  baseline?: MetricasModelo;
}

const DESCRICOES = {
  mae: "Erro absoluto médio por dia",
  rmse: "Raiz do erro quadrático médio (penaliza erros grandes)",
  mape: "Erro percentual absoluto médio",
};

function Indicador({ sigla, valor, descricao, comparacao }: { sigla: string; valor: string; descricao: string; comparacao?: string }) {
  return (
    <div className="rounded-lg border border-gray-100 p-4">
      <p className="text-xs font-semibold text-gray-500">{sigla}</p>
      <p className="text-2xl font-bold text-gray-800 mt-1">{valor}</p>
      <p className="text-xs text-gray-500 mt-1">{descricao}</p>
      {comparacao && <p className="text-xs text-gray-400 mt-1">{comparacao}</p>}
    </div>
  );
}

/** Métricas reais calculadas pelo treino no período de teste (dados não usados no treinamento). */
export default function ModelMetrics({ lstm, baseline }: ModelMetricsProps) {
  const base = (valor: string) => (baseline ? `Baseline sazonal: ${valor}` : undefined);
  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Indicador sigla="MAE" valor={fmtValor(lstm.mae)} descricao={DESCRICOES.mae}
          comparacao={baseline && base(fmtValor(baseline.mae))} />
        <Indicador sigla="RMSE" valor={fmtValor(lstm.rmse)} descricao={DESCRICOES.rmse}
          comparacao={baseline && base(fmtValor(baseline.rmse))} />
        <Indicador sigla="MAPE" valor={fmtPct(lstm.mape, false)} descricao={DESCRICOES.mape}
          comparacao={baseline && base(fmtPct(baseline.mape, false))} />
      </div>
      <p className="text-xs text-gray-500 mt-3">
        Avaliação em {lstm.dias_avaliados} dias do período de teste, com previsão recursiva mês a mês.
        {lstm.dias_excluidos_mape > 0 &&
          ` ${lstm.dias_excluidos_mape} dia(s) com venda real igual a zero (lojas fechadas) foram excluídos do MAPE.`}
      </p>
    </div>
  );
}
