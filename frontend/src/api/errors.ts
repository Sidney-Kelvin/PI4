import { isAxiosError } from "axios";

export interface ApiError {
  status: number | null;
  message: string;
}

/** Converte qualquer erro de chamada à API em uma mensagem clara em português. */
export function toApiError(err: unknown): ApiError {
  if (isAxiosError(err)) {
    if (!err.response) {
      return {
        status: null,
        message: "Não foi possível conectar à API. Verifique se o backend está em execução (docker compose ps).",
      };
    }
    const { status, data } = err.response;
    const detail = (data as { detail?: unknown })?.detail;
    if (typeof detail === "string") return { status, message: detail };
    if (Array.isArray(detail)) return { status, message: "Parâmetros inválidos na requisição." };
    if (status === 502 || status === 504) {
      return { status, message: "O servidor da API está indisponível ou reiniciando. Tente novamente em instantes." };
    }
    return { status, message: `Erro inesperado da API (HTTP ${status}).` };
  }
  return { status: null, message: "Erro inesperado ao carregar os dados." };
}
