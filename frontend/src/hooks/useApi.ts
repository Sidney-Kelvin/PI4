import { useCallback, useEffect, useState } from "react";
import { toApiError, type ApiError } from "../api/errors";

interface Resultado<T> {
  chave: string;
  data: T | null;
  error: ApiError | null;
}

/**
 * Executa uma chamada à API controlando carregamento e erro.
 * `key` identifica os parâmetros da chamada: quando muda, a chamada é refeita.
 * Com `enabled = false` nada é carregado (útil quando falta um pré-requisito).
 */
export function useApi<T>(loader: () => Promise<T>, key: string = "", enabled: boolean = true) {
  const [tentativa, setTentativa] = useState(0);
  const [resultado, setResultado] = useState<Resultado<T> | null>(null);
  const chave = `${key}#${tentativa}`;

  useEffect(() => {
    if (!enabled) return;
    let ativo = true;
    loader()
      .then((data) => ativo && setResultado({ chave, data, error: null }))
      .catch((err) => ativo && setResultado({ chave, data: null, error: toApiError(err) }));
    return () => {
      ativo = false;
    };
    // `loader` muda a cada render; a chamada depende apenas da chave informada
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave, enabled]);

  const atual = enabled && resultado?.chave === chave ? resultado : null;
  const reload = useCallback(() => setTentativa((t) => t + 1), []);
  return { data: atual?.data ?? null, loading: enabled && !atual, error: atual?.error ?? null, reload };
}
