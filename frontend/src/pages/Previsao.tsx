import { useState } from "react";
import { getAvaliacaoModelo, getHistoricoVsPrevisao, getPrevisaoProximoMes, getStatusPrevisao } from "../api/previsoes";
import { useApi } from "../hooks/useApi";
import type { AvaliacaoModelo } from "../types";
import Panel from "../components/ui/Panel";
import Spinner from "../components/ui/Spinner";
import StateMessage from "../components/ui/StateMessage";
import HistoryForecastChart from "../components/charts/HistoryForecastChart";
import RealVsPredictedChart from "../components/charts/RealVsPredictedChart";
import LossChart from "../components/charts/LossChart";
import ForecastSummary from "../components/forecast/ForecastSummary";
import ModelMetrics from "../components/forecast/ModelMetrics";
import ForecastGate, { CMD_TREINAR } from "../components/forecast/ForecastGate";
import { fmtData, fmtDataHora, fmtInteiro, fmtPct, fmtPeriodo, fmtValor } from "../utils/format";

const NOMES_FEATURES: Record<string, string> = {
  seg: "Segunda", ter: "Terça", qua: "Quarta", qui: "Quinta", sex: "Sexta", sab: "Sábado", dom: "Domingo",
  mes_sin: "Mês (seno)", mes_cos: "Mês (cosseno)", dia_ano_sin: "Dia do ano (seno)", dia_ano_cos: "Dia do ano (cosseno)",
  dia_mes: "Dia do mês", frac_abertas: "% lojas abertas", frac_promo: "% lojas em promoção",
  frac_feriado_estadual: "% lojas em feriado estadual", frac_feriado_escolar: "% lojas em feriado escolar",
};

function PrevisaoDiaria() {
  const [dias, setDias] = useState(120);
  const comparacao = useApi(() => getHistoricoVsPrevisao(dias), String(dias));
  const previsao = useApi(getPrevisaoProximoMes);

  return (
    <>
      <Panel title="Previsão do próximo mês">
        {previsao.loading && <Spinner />}
        {previsao.error && <StateMessage type="error" title="Previsão indisponível" message={previsao.error.message} onRetry={previsao.reload} />}
        {previsao.data && <ForecastSummary previsao={previsao.data} />}
      </Panel>

      <Panel
        title="Histórico × previsão diária"
        subtitle="Vendas totais da rede por dia: histórico real (contínuo) e previsão recursiva do modelo (tracejado)"
        actions={
          <label className="text-xs text-gray-600 flex items-center gap-2">
            Histórico exibido
            <select className="border border-gray-200 rounded-lg px-2 py-1 text-xs" value={dias}
              onChange={(e) => setDias(Number(e.target.value))}>
              <option value={60}>60 dias</option>
              <option value={120}>120 dias</option>
              <option value={365}>1 ano</option>
            </select>
          </label>
        }
      >
        {comparacao.loading && <Spinner />}
        {comparacao.error && <StateMessage type="error" title="Erro ao carregar o gráfico" message={comparacao.error.message} onRetry={comparacao.reload} />}
        {comparacao.data && <HistoryForecastChart data={comparacao.data.diario} height={320} />}
      </Panel>

      {previsao.data && (
        <Panel title="Previsão dia a dia" subtitle="Valores gravados também na tabela previsoes_vendas">
          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 sticky top-0">
                <tr>
                  <th className="text-left px-3 py-2 font-medium">Data</th>
                  <th className="text-right px-3 py-2 font-medium">Lojas abertas (estimadas)</th>
                  <th className="text-right px-3 py-2 font-medium">Vendas previstas</th>
                  <th className="text-left px-3 py-2 font-medium">Calendário</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {previsao.data.diario.map((d) => (
                  <tr key={d.data}>
                    <td className="px-3 py-1.5">{fmtData(d.data)}</td>
                    <td className="px-3 py-1.5 text-right text-gray-600">{fmtInteiro(d.lojas_abertas_estimadas)}</td>
                    <td className="px-3 py-1.5 text-right font-medium">{fmtValor(d.vendas_previstas)}</td>
                    <td className="px-3 py-1.5 text-gray-500">{d.fonte_calendario === "planejamento" ? "Planejado" : "Estimado"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </>
  );
}

function Avaliacao({ a }: { a: AvaliacaoModelo }) {
  return (
    <>
      <Panel title="Qualidade do modelo" subtitle={`Período de teste: ${fmtData(a.periodo_teste.inicio)} a ${fmtData(a.periodo_teste.fim)} (não usado no treino)`}>
        <ModelMetrics lstm={a.metricas_lstm} baseline={a.metricas_baseline} />
      </Panel>

      <Panel title="Vendas reais × previstas (teste)" subtitle="Cada mês do teste é previsto a partir apenas do histórico anterior a ele">
        <RealVsPredictedChart data={a.diario} />
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-3 py-2 font-medium">Mês</th>
                <th className="text-right px-3 py-2 font-medium">Real</th>
                <th className="text-right px-3 py-2 font-medium">Previsto (LSTM)</th>
                <th className="text-right px-3 py-2 font-medium">Erro do total</th>
                <th className="text-right px-3 py-2 font-medium">Baseline</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {a.meses.map((m) => (
                <tr key={m.mes}>
                  <td className="px-3 py-2">{fmtPeriodo(m.mes)}</td>
                  <td className="px-3 py-2 text-right">{fmtValor(m.real)}</td>
                  <td className="px-3 py-2 text-right font-medium">{fmtValor(m.previsto)}</td>
                  <td className="px-3 py-2 text-right">{fmtPct(m.erro_percentual)}</td>
                  <td className="px-3 py-2 text-right text-gray-500">{fmtValor(m.baseline)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Modelo" subtitle={`Versão ${a.versao} · treinado em ${fmtDataHora(a.treinado_em)}`}>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <dt className="text-gray-500">Arquitetura</dt><dd className="text-gray-800">{a.arquitetura}</dd>
            <dt className="text-gray-500">Parâmetros treináveis</dt><dd>{fmtInteiro(a.parametros_treinaveis)}</dd>
            <dt className="text-gray-500">Janela de entrada</dt><dd>{a.config.janela} dias</dd>
            <dt className="text-gray-500">Treino</dt><dd>{fmtData(a.divisao.inicio)} a {fmtData(a.divisao.inicio_validacao)} (exclusive) · {fmtInteiro(a.amostras.treino)} amostras</dd>
            <dt className="text-gray-500">Validação</dt><dd>{fmtData(a.divisao.inicio_validacao)} a {fmtData(a.divisao.inicio_teste)} (exclusive) · {fmtInteiro(a.amostras.validacao)} amostras</dd>
            <dt className="text-gray-500">Teste</dt><dd>{fmtData(a.divisao.inicio_teste)} a {fmtData(a.divisao.fim)} · {a.amostras.teste_dias} dias</dd>
            <dt className="text-gray-500">Épocas</dt><dd>{a.epocas_executadas} (melhor: {a.melhor_epoca}, parada antecipada)</dd>
          </dl>
          <p className="text-xs font-semibold text-gray-500 mt-4 mb-2">Features de cada dia</p>
          <div className="flex flex-wrap gap-1.5">
            <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-xs">Venda média por loja aberta (histórico)</span>
            {a.features_exogenas.map((f) => (
              <span key={f} className="px-2 py-0.5 rounded bg-gray-100 text-gray-700 text-xs">{NOMES_FEATURES[f] ?? f}</span>
            ))}
          </div>
        </Panel>
        <Panel title="Curva de aprendizado" subtitle="Perda MSE (escala padronizada) por época">
          <LossChart data={a.historico_treino} melhorEpoca={a.melhor_epoca} />
        </Panel>
      </div>

      <Panel title="Como a previsão é feita e limitações">
        <ul className="list-disc pl-5 space-y-1.5 text-sm text-gray-600">
          <li>O alvo é a venda média por loja aberta; o total do dia é esse valor multiplicado pelo número de lojas abertas.</li>
          <li>A LSTM lê os últimos {a.config.janela} dias e prevê o dia seguinte; a previsão entra na janela para prever o próximo dia (previsão recursiva), até completar o mês.</li>
          <li>Abertura de lojas, promoções e feriados do mês previsto vêm do calendário planejado (test.csv); na ausência dele, são estimados pelas últimas 4 semanas.</li>
          <li>O número de clientes não é usado: ele só é conhecido depois do dia acontecer (vazamento de dados).</li>
          <li>O modelo prevê a rede como um todo, não cada loja, e não considera fatores externos (economia, clima, concorrência nova).</li>
          <li>O baseline sazonal (média do mesmo dia da semana nas 4 semanas anteriores) serve de referência mínima de desempenho.</li>
        </ul>
      </Panel>
    </>
  );
}

function AvaliacaoSecao() {
  const { data, loading, error, reload } = useApi(getAvaliacaoModelo);
  if (loading) return <Spinner />;
  if (error) return <StateMessage type="error" title="Avaliação indisponível" message={error.message} command={error.status === 503 ? CMD_TREINAR : undefined} onRetry={reload} />;
  return data ? <Avaliacao a={data} /> : null;
}

export default function PrevisaoPage() {
  const status = useApi(getStatusPrevisao);
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Previsão de vendas com uma rede neural LSTM treinada localmente sobre o histórico diário do Rossmann Store Sales.
      </p>
      <ForecastGate status={status.data} loading={status.loading} error={status.error} onRetry={status.reload}>
        <PrevisaoDiaria />
        <AvaliacaoSecao />
      </ForecastGate>
    </div>
  );
}
