import type { ReactNode } from "react";
import type { ApiError } from "../../api/errors";
import type { StatusPrevisao } from "../../types";
import Spinner from "../ui/Spinner";
import StateMessage from "../ui/StateMessage";

export const CMD_IMPORTAR = "docker compose exec backend python -m app.ml.ingest";
export const CMD_TREINAR = "docker compose exec backend python -m app.ml.train";

interface ForecastGateProps {
  status: StatusPrevisao | null;
  loading: boolean;
  error: ApiError | null;
  onRetry: () => void;
  exigirModelo?: boolean;
  children: ReactNode;
}

/** Só exibe o conteúdo quando os dados foram importados (e, se exigido, o modelo foi treinado). */
export default function ForecastGate({ status, loading, error, onRetry, exigirModelo = true, children }: ForecastGateProps) {
  if (loading) return <Spinner />;
  if (error) {
    return <StateMessage type="error" title="Não foi possível consultar a situação da previsão" message={error.message} onRetry={onRetry} />;
  }
  if (!status) return null;
  if (!status.dados_importados) {
    return (
      <StateMessage
        type="warning"
        title="Dados históricos de varejo ainda não importados"
        message="Baixe train.csv, store.csv e test.csv do Kaggle (Rossmann Store Sales), coloque-os em data/raw/ e execute a importação:"
        command={CMD_IMPORTAR}
        onRetry={onRetry}
      />
    );
  }
  if (exigirModelo && !status.modelo_treinado) {
    return (
      <StateMessage
        type="warning"
        title="Modelo de previsão ainda não treinado"
        message="Os dados já estão no banco. Treine o modelo LSTM (alguns minutos em CPU) e recarregue a página:"
        command={CMD_TREINAR}
        onRetry={onRetry}
      />
    );
  }
  return <>{children}</>;
}
