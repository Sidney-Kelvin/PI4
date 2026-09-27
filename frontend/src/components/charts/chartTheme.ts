// Cores e estilos compartilhados pelos gráficos. Real x previsto também diferem
// pelo traço (contínuo x tracejado), para não depender só da cor (acessibilidade).
export const CORES = {
  real: "#2563eb",
  previsto: "#ea580c",
  baseline: "#64748b",
  barra: "#3b82f6",
  grade: "#e5e7eb",
  eixo: "#6b7280",
};

export const TRACO_PREVISTO = "6 4";
export const TRACO_BASELINE = "2 3";

export const eixoProps = {
  tick: { fontSize: 11, fill: CORES.eixo },
  tickLine: false,
  axisLine: { stroke: CORES.grade },
};
