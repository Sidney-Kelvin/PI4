export interface Produto {
  id: number;
  nome: string;
  descricao?: string;
  preco: number;
  quantidade: number;
  categoria?: string;
  criado_em: string;
  atualizado_em?: string;
}

export interface ProdutoCreate {
  nome: string;
  descricao?: string;
  preco: number;
  quantidade: number;
  categoria?: string;
}

export interface Venda {
  id: number;
  produto_id: number;
  quantidade: number;
  preco_unitario: number;
  total: number;
  cliente?: string;
  observacao?: string;
  criado_em: string;
  produto?: Produto;
}

export interface VendaCreate {
  produto_id: number;
  quantidade: number;
  cliente?: string;
  observacao?: string;
}

export interface Despesa {
  id: number;
  descricao: string;
  valor: number;
  categoria?: string;
  data_despesa: string;
  criado_em: string;
}

export interface DespesaCreate {
  descricao: string;
  valor: number;
  categoria?: string;
  data_despesa?: string;
}

export interface Dashboard {
  faturamento_total: number;
  despesas_totais: number;
  saldo: number;
  total_vendas: number;
  produtos_cadastrados: number;
}

// ── Varejo (histórico Rossmann) ─────────────────────────────────────────
export interface TotalPeriodo {
  periodo: string;
  vendas: number;
}

export interface ResumoVarejo {
  dados_importados: boolean;
  faturamento_total: number;
  clientes_total: number;
  registros: number;
  total_lojas: number;
  data_inicio: string | null;
  data_fim: string | null;
  dias: number;
  media_diaria: number;
  ultimo_mes: TotalPeriodo | null;
  mes_anterior: TotalPeriodo | null;
  variacao_mensal_percentual: number | null;
  dias_planejados: number;
  observacao_moeda: string;
}

export type Agrupamento = "dia" | "mes" | "ano";

export interface PontoSerie {
  periodo: string;
  vendas: number;
  clientes: number;
  dias_loja_abertos: number;
}

export interface ItemQuebra {
  categoria: string;
  descricao: string;
  vendas_totais: number;
  dias_loja_abertos: number;
  media_por_dia_loja: number;
}

export interface RankingLoja {
  loja_id: number;
  tipo_loja: string;
  vendas_totais: number;
  dias_abertos: number;
  media_diaria: number;
}

// ── Previsões (LSTM) ────────────────────────────────────────────────────
export interface StatusPrevisao {
  dados_importados: boolean;
  planejamento_disponivel: boolean;
  modelo_treinado: boolean;
  versao_modelo: string | null;
  treinado_em: string | null;
  mensagem: string;
}

export interface MetricasModelo {
  mae: number;
  rmse: number;
  mape: number | null;
  dias_avaliados: number;
  dias_excluidos_mape: number;
}

export interface PontoPrevisao {
  data: string;
  vendas_previstas: number;
  lojas_abertas_estimadas: number;
  fonte_calendario: "planejamento" | "estimado";
}

export interface PrevisaoProximoMes {
  mes_referencia: string;
  periodo_inicio: string;
  periodo_fim: string;
  valor_previsto: number;
  ultimo_mes_real: TotalPeriodo;
  variacao_percentual: number | null;
  ultima_data_historico: string;
  lojas_referencia: number;
  fonte_calendario: "planejamento" | "estimado" | "misto";
  versao_modelo: string;
  metricas: MetricasModelo;
  diario: PontoPrevisao[];
  observacao_moeda: string;
}

export interface PontoComparacao {
  periodo: string;
  real: number | null;
  previsto: number | null;
}

export interface HistoricoVsPrevisao {
  mes_previsto: string;
  diario: PontoComparacao[];
  mensal: PontoComparacao[];
}

export interface AvaliacaoModelo {
  versao: string;
  treinado_em: string;
  arquitetura: string;
  parametros_treinaveis: number;
  config: Record<string, number>;
  features_exogenas: string[];
  divisao: { inicio: string; inicio_validacao: string; inicio_teste: string; fim: string };
  amostras: { treino: number; validacao: number; teste_dias: number };
  epocas_executadas: number;
  melhor_epoca: number;
  periodo_teste: { inicio: string; fim: string };
  metricas_lstm: MetricasModelo;
  metricas_baseline: MetricasModelo;
  meses: { mes: string; real: number; previsto: number; baseline: number; erro_percentual: number | null }[];
  diario: { data: string; real: number; previsto: number; baseline: number }[];
  historico_treino: { epoca: number; perda_treino: number; perda_validacao: number }[];
}
