import api from "./client";
import type { AvaliacaoModelo, HistoricoVsPrevisao, PrevisaoProximoMes, StatusPrevisao } from "../types";

export const getStatusPrevisao = (): Promise<StatusPrevisao> =>
  api.get("/previsoes/status").then((r) => r.data);

export const getPrevisaoProximoMes = (): Promise<PrevisaoProximoMes> =>
  api.get("/previsoes/proximo-mes").then((r) => r.data);

export const getHistoricoVsPrevisao = (dias = 120): Promise<HistoricoVsPrevisao> =>
  api.get("/previsoes/historico-vs-previsao", { params: { dias } }).then((r) => r.data);

export const getAvaliacaoModelo = (): Promise<AvaliacaoModelo> =>
  api.get("/previsoes/avaliacao").then((r) => r.data);
