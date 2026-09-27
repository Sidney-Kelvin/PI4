import { useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarDays,
  DollarSign,
  Package,
  ShoppingCart,
  Store,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { getDashboard } from "../api/dashboard";
import { getHistoricoVsPrevisao, getPrevisaoProximoMes, getStatusPrevisao } from "../api/previsoes";
import { getResumoVarejo, getSerieVendas } from "../api/varejo";
import { useApi } from "../hooks/useApi";
import Spinner from "../components/ui/Spinner";
import StatCard, { type StatCardProps } from "../components/ui/StatCard";
import Panel from "../components/ui/Panel";
import StateMessage from "../components/ui/StateMessage";
import SalesLineChart from "../components/charts/SalesLineChart";
import HistoryForecastChart from "../components/charts/HistoryForecastChart";
import ForecastSummary from "../components/forecast/ForecastSummary";
import ModelMetrics from "../components/forecast/ModelMetrics";
import ForecastGate from "../components/forecast/ForecastGate";
import { fmtBRL, fmtCompacto, fmtData, fmtInteiro, fmtPct, fmtPeriodo } from "../utils/format";

function SecaoOperacional() {
  const { data, loading, error, reload } = useApi(getDashboard);
  if (loading) return <Spinner />;
  if (error) return <StateMessage type="error" title="Indicadores operacionais indisponíveis" message={error.message} onRetry={reload} />;
  if (!data) return null;

  const cards: StatCardProps[] = [
    { title: "Faturamento (vendas registradas)", value: fmtBRL(data.faturamento_total), icon: DollarSign, color: "text-green-600", bg: "bg-green-50" },
    { title: "Despesas", value: fmtBRL(data.despesas_totais), icon: TrendingDown, color: "text-red-500", bg: "bg-red-50" },
    {
      title: "Saldo",
      value: fmtBRL(data.saldo),
      icon: Wallet,
      color: data.saldo >= 0 ? "text-blue-600" : "text-red-600",
      bg: data.saldo >= 0 ? "bg-blue-50" : "bg-red-50",
    },
    { title: "Vendas registradas", value: fmtInteiro(data.total_vendas), icon: ShoppingCart, color: "text-purple-600", bg: "bg-purple-50" },
    { title: "Produtos cadastrados", value: fmtInteiro(data.produtos_cadastrados), icon: Package, color: "text-orange-500", bg: "bg-orange-50" },
  ];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
      {cards.map((c) => <StatCard key={c.title} {...c} />)}
    </div>
  );
}

function SecaoVarejo({ habilitado }: { habilitado: boolean }) {
  const resumo = useApi(getResumoVarejo, "", habilitado);
  const serie = useApi(() => getSerieVendas({ agrupamento: "mes" }), "mes", habilitado);

  if (resumo.loading) return <Spinner />;
  if (resumo.error) return <StateMessage type="error" title="Histórico de vendas indisponível" message={resumo.error.message} onRetry={resumo.reload} />;
  const r = resumo.data;
  if (!r) return null;

  const variacao = r.variacao_mensal_percentual;
  const cards: StatCardProps[] = [
    {
      title: "Faturamento histórico",
      value: fmtCompacto(r.faturamento_total),
      icon: DollarSign, color: "text-green-600", bg: "bg-green-50",
      hint: r.data_inicio && r.data_fim ? `${fmtData(r.data_inicio)} a ${fmtData(r.data_fim)}` : undefined,
    },
    {
      title: r.ultimo_mes ? `Vendas em ${fmtPeriodo(r.ultimo_mes.periodo)}` : "Último mês",
      value: r.ultimo_mes ? fmtCompacto(r.ultimo_mes.vendas) : "—",
      icon: variacao !== null && variacao < 0 ? TrendingDown : TrendingUp,
      color: variacao !== null && variacao < 0 ? "text-red-500" : "text-blue-600",
      bg: variacao !== null && variacao < 0 ? "bg-red-50" : "bg-blue-50",
      hint: variacao !== null ? `${fmtPct(variacao)} vs. mês anterior` : undefined,
    },
    { title: "Média diária da rede", value: fmtCompacto(r.media_diaria), icon: CalendarDays, color: "text-purple-600", bg: "bg-purple-50", hint: `${fmtInteiro(r.dias)} dias de histórico` },
    { title: "Lojas", value: fmtInteiro(r.total_lojas), icon: Store, color: "text-orange-500", bg: "bg-orange-50", hint: `${fmtInteiro(r.registros)} registros loja × dia` },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {cards.map((c) => <StatCard key={c.title} {...c} />)}
      </div>
      <Panel title="Histórico de vendas" subtitle={`Faturamento mensal da rede. ${r.observacao_moeda}`}>
        {serie.loading && <Spinner />}
        {serie.error && <StateMessage type="error" title="Erro ao carregar a série" message={serie.error.message} onRetry={serie.reload} />}
        {serie.data && <SalesLineChart data={serie.data} ariaLabel="Faturamento mensal histórico" />}
      </Panel>
    </div>
  );
}

function SecaoPrevisao({ habilitado }: { habilitado: boolean }) {
  const [visao, setVisao] = useState<"mensal" | "diario">("mensal");
  const previsao = useApi(getPrevisaoProximoMes, "", habilitado);
  const comparacao = useApi(() => getHistoricoVsPrevisao(120), "", habilitado);

  if (previsao.loading) return <Spinner />;
  if (previsao.error) return <StateMessage type="error" title="Previsão indisponível" message={previsao.error.message} onRetry={previsao.reload} />;
  if (!previsao.data) return null;

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Panel title="Previsão de vendas" subtitle="Próximo mês após o fim do histórico">
        <ForecastSummary previsao={previsao.data} />
      </Panel>

      <Panel
        title="Qualidade do modelo"
        subtitle="Métricas do período de teste"
        actions={<Link to="/previsao" className="text-xs font-medium text-blue-600 hover:underline">Ver análise completa →</Link>}
      >
        <ModelMetrics lstm={previsao.data.metricas} />
      </Panel>

      <Panel
        className="xl:col-span-2"
        title="Histórico × previsão"
        subtitle={visao === "mensal" ? "Faturamento mensal real e total previsto do próximo mês" : "Últimos 120 dias reais e previsão diária do próximo mês"}
        actions={
          <div className="inline-flex rounded-lg border border-gray-200 p-0.5 text-xs" role="group" aria-label="Escala do gráfico">
            {(["mensal", "diario"] as const).map((v) => (
              <button
                key={v}
                onClick={() => setVisao(v)}
                aria-pressed={visao === v}
                className={`px-3 py-1 rounded-md font-medium ${visao === v ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-50"}`}
              >
                {v === "mensal" ? "Mensal" : "Diário"}
              </button>
            ))}
          </div>
        }
      >
        {comparacao.loading && <Spinner />}
        {comparacao.error && <StateMessage type="error" title="Erro ao carregar o gráfico" message={comparacao.error.message} onRetry={comparacao.reload} />}
        {comparacao.data && <HistoryForecastChart data={visao === "mensal" ? comparacao.data.mensal : comparacao.data.diario} />}
      </Panel>
    </div>
  );
}

export default function DashboardPage() {
  const status = useApi(getStatusPrevisao);
  const dados = status.data?.dados_importados ?? false;
  const modelo = status.data?.modelo_treinado ?? false;

  return (
    <div className="space-y-8">
      <p className="text-sm text-gray-500">
        Acompanhamento financeiro do FinanTrack: operação cadastrada, histórico de vendas do varejo e previsão com Deep Learning.
      </p>

      <section aria-labelledby="titulo-operacao" className="space-y-3">
        <h2 id="titulo-operacao" className="text-base font-semibold text-gray-800">Operação</h2>
        <p className="text-xs text-gray-500 -mt-2">Produtos, vendas e despesas cadastrados no sistema (valores em R$).</p>
        <SecaoOperacional />
      </section>

      <section aria-labelledby="titulo-varejo" className="space-y-3">
        <h2 id="titulo-varejo" className="text-base font-semibold text-gray-800">Varejo — histórico Rossmann</h2>
        <ForecastGate status={status.data} loading={status.loading} error={status.error} onRetry={status.reload} exigirModelo={false}>
          <SecaoVarejo habilitado={dados} />
        </ForecastGate>
      </section>

      <section aria-labelledby="titulo-previsao" className="space-y-3">
        <h2 id="titulo-previsao" className="text-base font-semibold text-gray-800">Análise preditiva (LSTM)</h2>
        <ForecastGate status={status.data} loading={status.loading} error={status.error} onRetry={status.reload}>
          <SecaoPrevisao habilitado={dados && modelo} />
        </ForecastGate>
      </section>
    </div>
  );
}
