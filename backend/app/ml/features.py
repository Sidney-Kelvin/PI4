"""Construção da série temporal e das variáveis (features) do modelo.

Série modelada
--------------
O modelo trabalha com a série DIÁRIA agregada de toda a rede. O alvo é a
**venda média por loja aberta** no dia:

    alvo(d) = soma das vendas do dia / número de lojas abertas no dia

Motivos:
* separa "quanto cada loja vende" de "quantas lojas abriram" (domingos e
  feriados têm poucas lojas abertas);
* é robusto ao período de 2014-07 a 2014-12, em que ~180 lojas não
  aparecem no train.csv (a soma bruta cairia artificialmente);
* a venda total é reconstruída como alvo × lojas abertas.

Features por dia (todas conhecidas ANTES do dia previsto)
---------------------------------------------------------
* dia da semana (one-hot, 7 colunas)
* mês e dia do ano (seno/cosseno, capturam sazonalidade anual)
* dia do mês (0..1, efeito de início/fim de mês)
* fração de lojas abertas, em promoção, em feriado estadual e em feriado escolar

`Customers` NÃO é usado: o número de clientes só é conhecido depois que o dia
acontece, então usá-lo para prever as vendas do mesmo dia seria vazamento de
dados (data leakage).
"""
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

COLUNAS_AGREGADAS = [
    "lojas_reportando",
    "lojas_abertas",
    "lojas_promo",
    "lojas_feriado_estadual",
    "lojas_feriado_escolar",
    "vendas_total",
]

DIAS_SEMANA = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]

FEATURES_EXOGENAS = DIAS_SEMANA + [
    "mes_sin",
    "mes_cos",
    "dia_ano_sin",
    "dia_ano_cos",
    "dia_mes",
    "frac_abertas",
    "frac_promo",
    "frac_feriado_estadual",
    "frac_feriado_escolar",
]


def preparar_serie_diaria(agregado: pd.DataFrame) -> pd.DataFrame:
    """Recebe o agregado diário (uma linha por data) e devolve a série contínua com o alvo.

    Datas ausentes no intervalo são preenchidas com zero lojas (tratadas como dia fechado).
    """
    if agregado.empty:
        raise ValueError("Não há dados históricos de vendas para montar a série.")

    df = agregado.copy()
    df["data"] = pd.to_datetime(df["data"])
    df = df.set_index("data").sort_index()
    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="D"))
    df[COLUNAS_AGREGADAS] = df[COLUNAS_AGREGADAS].fillna(0).astype(float)
    df.index.name = "data"

    abertas = df["lojas_abertas"]
    df["alvo"] = np.where(abertas > 0, df["vendas_total"] / abertas.where(abertas > 0, 1), 0.0)
    return df.reset_index()


def features_exogenas(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula as features exógenas de cada linha (requer colunas `data` e COLUNAS_AGREGADAS)."""
    datas = pd.to_datetime(df["data"])
    reportando = df["lojas_reportando"].astype(float).replace(0, np.nan)

    features = pd.DataFrame(index=df.index)
    for i, nome in enumerate(DIAS_SEMANA):
        features[nome] = (datas.dt.dayofweek == i).astype(float)

    mes = datas.dt.month - 1
    dia_ano = datas.dt.dayofyear - 1
    features["mes_sin"] = np.sin(2 * np.pi * mes / 12)
    features["mes_cos"] = np.cos(2 * np.pi * mes / 12)
    features["dia_ano_sin"] = np.sin(2 * np.pi * dia_ano / 365.25)
    features["dia_ano_cos"] = np.cos(2 * np.pi * dia_ano / 365.25)
    features["dia_mes"] = (datas.dt.day - 1) / 30.0

    features["frac_abertas"] = (df["lojas_abertas"] / reportando).fillna(0)
    features["frac_promo"] = (df["lojas_promo"] / reportando).fillna(0)
    features["frac_feriado_estadual"] = (df["lojas_feriado_estadual"] / reportando).fillna(0)
    features["frac_feriado_escolar"] = (df["lojas_feriado_escolar"] / reportando).fillna(0)
    return features[FEATURES_EXOGENAS].astype(np.float32)


@dataclass
class EscalonadorAlvo:
    """Padronização z-score do alvo. Ajustado SOMENTE com dados de treino."""

    media: float
    desvio: float

    @classmethod
    def ajustar(cls, valores: np.ndarray) -> "EscalonadorAlvo":
        valores = np.asarray(valores, dtype=float)
        desvio = float(valores.std())
        return cls(media=float(valores.mean()), desvio=desvio if desvio > 0 else 1.0)

    def transformar(self, valores: np.ndarray) -> np.ndarray:
        return ((np.asarray(valores, dtype=float) - self.media) / self.desvio).astype(np.float32)

    def inverter(self, valores: np.ndarray) -> np.ndarray:
        return np.asarray(valores, dtype=float) * self.desvio + self.media

    def para_dict(self) -> dict:
        return {"media": self.media, "desvio": self.desvio}

    @classmethod
    def de_dict(cls, dados: dict) -> "EscalonadorAlvo":
        return cls(media=float(dados["media"]), desvio=float(dados["desvio"]))


def montar_entrada(
    alvo_escalonado: np.ndarray, exogenas: np.ndarray, t: int, janela: int
) -> tuple[np.ndarray, np.ndarray]:
    """Entrada para prever o dia t: janela [t-janela, t-1] (alvo + exógenas) e as exógenas do dia t."""
    sequencia = np.concatenate(
        [alvo_escalonado[t - janela:t, None], exogenas[t - janela:t]], axis=1
    ).astype(np.float32)
    return sequencia, exogenas[t].astype(np.float32)


def montar_amostras(
    alvo_escalonado: np.ndarray, exogenas: np.ndarray, indices: np.ndarray, janela: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Gera (sequências, exógenas do dia alvo, alvo) para os índices informados."""
    sequencias, exog_alvo, y = [], [], []
    for t in indices:
        if t < janela:
            continue
        seq, ex = montar_entrada(alvo_escalonado, exogenas, t, janela)
        sequencias.append(seq)
        exog_alvo.append(ex)
        y.append(alvo_escalonado[t])
    n_features = 1 + exogenas.shape[1]
    if not y:
        return (np.empty((0, janela, n_features), np.float32), np.empty((0, exogenas.shape[1]), np.float32),
                np.empty((0,), np.float32))
    return np.stack(sequencias), np.stack(exog_alvo), np.asarray(y, dtype=np.float32)


@dataclass
class DivisaoTemporal:
    """Fronteiras da divisão temporal: treino < inicio_validacao <= validação < inicio_teste <= teste <= fim."""

    inicio: date
    inicio_validacao: date
    inicio_teste: date
    fim: date

    def para_dict(self) -> dict:
        return {chave: valor.isoformat() for chave, valor in self.__dict__.items()}


def dividir_temporalmente(datas: pd.Series, meses_validacao: int, meses_teste: int) -> DivisaoTemporal:
    """Divide pela ordem do tempo: os últimos `meses_teste` meses do calendário são teste,
    os `meses_validacao` meses anteriores são validação e todo o resto é treino.

    Não se usa divisão aleatória: numa série temporal ela colocaria dias futuros
    no treino e dias passados no teste, inflando artificialmente as métricas.
    """
    datas = pd.to_datetime(datas)
    fim = datas.max()
    inicio_teste = fim.to_period("M").to_timestamp() - pd.DateOffset(months=meses_teste - 1)
    inicio_validacao = inicio_teste - pd.DateOffset(months=meses_validacao)
    if inicio_validacao <= datas.min():
        raise ValueError("Histórico curto demais para a divisão treino/validação/teste solicitada.")
    return DivisaoTemporal(
        inicio=datas.min().date(),
        inicio_validacao=inicio_validacao.date(),
        inicio_teste=inicio_teste.date(),
        fim=fim.date(),
    )
