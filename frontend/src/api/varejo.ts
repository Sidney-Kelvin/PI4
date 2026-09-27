import api from "./client";
import type { Agrupamento, ItemQuebra, PontoSerie, RankingLoja, ResumoVarejo } from "../types";

export const getResumoVarejo = (): Promise<ResumoVarejo> =>
  api.get("/varejo/resumo").then((r) => r.data);

export interface FiltroSerie {
  agrupamento: Agrupamento;
  loja_id?: number;
  inicio?: string;
  fim?: string;
}

export const getSerieVendas = (filtro: FiltroSerie): Promise<PontoSerie[]> =>
  api.get("/varejo/vendas/serie", { params: filtro }).then((r) => r.data);

export type TipoQuebra = "por-tipo-loja" | "por-sortimento" | "por-promocao" | "por-feriado" | "por-dia-semana";

export const getQuebra = (tipo: TipoQuebra): Promise<ItemQuebra[]> =>
  api.get(`/varejo/vendas/${tipo}`).then((r) => r.data);

export const getRankingLojas = (limite = 10, ordem: "maiores" | "menores" = "maiores"): Promise<RankingLoja[]> =>
  api.get("/varejo/lojas/ranking", { params: { limite, ordem } }).then((r) => r.data);
