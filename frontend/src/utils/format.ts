const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

export const fmtBRL = (n: number) => n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

/** Valor monetário sem símbolo (dados do Rossmann estão na moeda original do dataset). */
export const fmtValor = (n: number) =>
  n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const fmtInteiro = (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 0 });

export const fmtCompacto = (n: number) =>
  new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 }).format(n);

export const fmtPct = (n: number | null | undefined, sinal = true) =>
  n === null || n === undefined
    ? "—"
    : `${sinal && n > 0 ? "+" : ""}${n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;

/** "2015-07-31" -> "31/07/2015" (sem conversão de fuso horário). */
export const fmtData = (iso: string) => {
  const [a, m, d] = iso.slice(0, 10).split("-");
  return d ? `${d}/${m}/${a}` : iso;
};

/** "2015-07" -> "jul/2015"; "2015-07-31" -> "31/07"; "2015" -> "2015". */
export const fmtPeriodo = (periodo: string) => {
  const partes = periodo.split("-");
  if (partes.length === 2) return `${MESES[Number(partes[1]) - 1]}/${partes[0]}`;
  if (partes.length === 3) return `${partes[2]}/${partes[1]}`;
  return periodo;
};

export const fmtDataHora = (iso: string) =>
  new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
