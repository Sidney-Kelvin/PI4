import { useState } from "react";
import { getStatusPrevisao } from "../api/previsoes";
import { getQuebra, getRankingLojas, getSerieVendas, type FiltroSerie, type TipoQuebra } from "../api/varejo";
import { useApi } from "../hooks/useApi";
import type { Agrupamento } from "../types";
import Panel from "../components/ui/Panel";
import Spinner from "../components/ui/Spinner";
import StateMessage from "../components/ui/StateMessage";
import SalesLineChart from "../components/charts/SalesLineChart";
import CategoryBarChart from "../components/charts/CategoryBarChart";
import ForecastGate from "../components/forecast/ForecastGate";
import { fmtCompacto, fmtInteiro, fmtValor } from "../utils/format";

const QUEBRAS: { tipo: TipoQuebra; titulo: string }[] = [
  { tipo: "por-dia-semana", titulo: "Por dia da semana" },
  { tipo: "por-promocao", titulo: "Por promoção" },
  { tipo: "por-feriado", titulo: "Por feriado" },
  { tipo: "por-tipo-loja", titulo: "Por tipo de loja" },
  { tipo: "por-sortimento", titulo: "Por sortimento" },
];

const inputCls =
  "border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

function QuebraPanel({ tipo, titulo }: { tipo: TipoQuebra; titulo: string }) {
  const { data, loading, error, reload } = useApi(() => getQuebra(tipo), tipo);
  return (
    <Panel title={titulo} subtitle="Venda média de uma loja aberta por dia">
      {loading && <Spinner />}
      {error && <StateMessage type="error" title="Erro ao carregar" message={error.message} onRetry={reload} />}
      {data && (
        <CategoryBarChart
          nomeValor="Média por loja/dia"
          data={data.map((i) => ({
            rotulo: i.descricao,
            valor: i.media_por_dia_loja,
            detalhe: `total ${fmtCompacto(i.vendas_totais)} em ${fmtInteiro(i.dias_loja_abertos)} dias-loja`,
          }))}
        />
      )}
    </Panel>
  );
}

function SerieFiltrada() {
  const [filtro, setFiltro] = useState<FiltroSerie>({ agrupamento: "mes" });
  const [lojaTexto, setLojaTexto] = useState("");
  const chave = JSON.stringify(filtro);
  const { data, loading, error, reload } = useApi(() => getSerieVendas(filtro), chave);

  const aplicarLoja = () => {
    const id = Number(lojaTexto);
    setFiltro((f) => ({ ...f, loja_id: lojaTexto && id > 0 ? id : undefined }));
  };

  return (
    <Panel
      title="Vendas no tempo"
      subtitle="Agrupe por dia, mês ou ano e filtre por loja e período"
      actions={
        <div className="flex flex-wrap items-end gap-2 text-xs">
          <label className="flex flex-col gap-1 text-gray-600">
            Agrupamento
            <select
              className={inputCls}
              value={filtro.agrupamento}
              onChange={(e) => setFiltro((f) => ({ ...f, agrupamento: e.target.value as Agrupamento }))}
            >
              <option value="dia">Dia</option>
              <option value="mes">Mês</option>
              <option value="ano">Ano</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-gray-600">
            Loja (nº)
            <input
              className={`${inputCls} w-24`}
              inputMode="numeric"
              placeholder="Todas"
              value={lojaTexto}
              onChange={(e) => setLojaTexto(e.target.value.replace(/\D/g, ""))}
              onBlur={aplicarLoja}
              onKeyDown={(e) => e.key === "Enter" && aplicarLoja()}
            />
          </label>
          <label className="flex flex-col gap-1 text-gray-600">
            Início
            <input type="date" className={inputCls} value={filtro.inicio ?? ""}
              onChange={(e) => setFiltro((f) => ({ ...f, inicio: e.target.value || undefined }))} />
          </label>
          <label className="flex flex-col gap-1 text-gray-600">
            Fim
            <input type="date" className={inputCls} value={filtro.fim ?? ""}
              onChange={(e) => setFiltro((f) => ({ ...f, fim: e.target.value || undefined }))} />
          </label>
        </div>
      }
    >
      {loading && <Spinner />}
      {error && <StateMessage type="error" title="Erro ao carregar a série" message={error.message} onRetry={reload} />}
      {data && data.length === 0 && (
        <StateMessage title="Nenhuma venda no filtro selecionado" message="Ajuste o período ou a loja." />
      )}
      {data && data.length > 0 && <SalesLineChart data={data} height={300} />}
    </Panel>
  );
}

function RankingPanel() {
  const { data, loading, error, reload } = useApi(() => getRankingLojas(10));
  return (
    <Panel title="Lojas com maior faturamento" subtitle="Total histórico nos dias em que a loja esteve aberta">
      {loading && <Spinner />}
      {error && <StateMessage type="error" title="Erro ao carregar o ranking" message={error.message} onRetry={reload} />}
      {data && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-3 py-2 font-medium">#</th>
                <th className="text-left px-3 py-2 font-medium">Loja</th>
                <th className="text-left px-3 py-2 font-medium">Tipo</th>
                <th className="text-right px-3 py-2 font-medium">Faturamento</th>
                <th className="text-right px-3 py-2 font-medium">Média diária</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {data.map((l, i) => (
                <tr key={l.loja_id}>
                  <td className="px-3 py-2 text-gray-400">{i + 1}</td>
                  <td className="px-3 py-2 font-medium text-gray-800">{l.loja_id}</td>
                  <td className="px-3 py-2 text-gray-500">{l.tipo_loja}</td>
                  <td className="px-3 py-2 text-right">{fmtValor(l.vendas_totais)}</td>
                  <td className="px-3 py-2 text-right text-gray-600">{fmtValor(l.media_diaria)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

export default function VarejoPage() {
  const status = useApi(getStatusPrevisao);
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        Análise do histórico diário de vendas das lojas do dataset Rossmann Store Sales (1.115 lojas). Valores na unidade
        monetária original do dataset.
      </p>
      <ForecastGate status={status.data} loading={status.loading} error={status.error} onRetry={status.reload} exigirModelo={false}>
        <SerieFiltrada />
        <div className="grid gap-4 lg:grid-cols-2">
          {QUEBRAS.map((q) => <QuebraPanel key={q.tipo} {...q} />)}
          <RankingPanel />
        </div>
      </ForecastGate>
    </div>
  );
}
