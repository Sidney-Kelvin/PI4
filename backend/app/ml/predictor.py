"""Previsão com o modelo treinado (usada pelo treino na avaliação e pela API).

A previsão é RECURSIVA: o modelo prevê o dia t a partir dos `janela` dias
anteriores; o valor previsto entra na janela para prever t+1, e assim por
diante até o fim do horizonte. Assim, nenhuma venda real do período previsto
é usada, exatamente como aconteceria numa previsão real do mês seguinte.
"""
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.ml.features import (
    COLUNAS_AGREGADAS,
    EscalonadorAlvo,
    features_exogenas,
    montar_entrada,
    preparar_serie_diaria,
)

DIAS_BASELINE = 28


def previsao_recursiva(modelo, escalonador: EscalonadorAlvo, alvo: np.ndarray, exogenas: np.ndarray,
                       abertas: np.ndarray, inicio: int, janela: int) -> np.ndarray:
    """Prevê o alvo (venda média por loja aberta) dos índices `inicio` até o fim.

    `alvo` só precisa ter valores reais antes de `inicio`; o restante é ignorado.
    Em dias sem nenhuma loja aberta a previsão é 0 (o modelo não foi treinado nesses dias).
    """
    import torch

    if inicio < janela:
        raise ValueError(f"São necessários pelo menos {janela} dias de histórico antes da previsão.")

    alvo_escalonado = escalonador.transformar(alvo.astype(float))
    previsoes = np.zeros(len(alvo) - inicio, dtype=float)
    with torch.no_grad():
        for passo, t in enumerate(range(inicio, len(alvo))):
            if abertas[t] <= 0:
                valor = 0.0
            else:
                sequencia, exog_dia = montar_entrada(alvo_escalonado, exogenas, t, janela)
                saida = modelo(torch.from_numpy(sequencia[None]), torch.from_numpy(exog_dia[None]))
                valor = max(float(escalonador.inverter(saida.numpy())[0]), 0.0)
            previsoes[passo] = valor
            alvo_escalonado[t] = escalonador.transformar(np.array([valor]))[0]
    return previsoes


def previsao_baseline(serie: pd.DataFrame, inicio: int) -> np.ndarray:
    """Baseline sazonal ingênuo para comparação: para cada dia previsto, usa a média
    do alvo no mesmo dia da semana nas 4 semanas anteriores ao início da previsão."""
    historico = serie.iloc[max(0, inicio - DIAS_BASELINE):inicio]
    historico = historico[historico["lojas_abertas"] > 0]
    dia_semana_hist = pd.to_datetime(historico["data"]).dt.dayofweek
    media_por_dia = historico.groupby(dia_semana_hist)["alvo"].mean()
    media_geral = float(historico["alvo"].mean()) if not historico.empty else 0.0

    futuro = serie.iloc[inicio:]
    dias = pd.to_datetime(futuro["data"]).dt.dayofweek
    valores = [float(media_por_dia.get(d, media_geral)) for d in dias]
    return np.where(futuro["lojas_abertas"].to_numpy() > 0, valores, 0.0)


def montar_calendario_futuro(serie: pd.DataFrame, datas: list[date], planejamento: pd.DataFrame | None,
                             lojas_referencia: int) -> pd.DataFrame:
    """Monta as linhas agregadas dos dias futuros (sem vendas) na escala de `lojas_referencia`.

    Fonte das informações de cada dia:
    * "planejamento": calendário de test.csv (abertura, promoções e feriados planejados);
    * "estimado": sem planejamento, usa a fração média de lojas abertas/em promoção
      do mesmo dia da semana nas últimas 4 semanas e assume ausência de feriados.
    """
    plano = {}
    if planejamento is not None and not planejamento.empty:
        plano = {pd.Timestamp(linha["data"]).date(): linha for _, linha in planejamento.iterrows()}

    recentes = serie.tail(DIAS_BASELINE).copy()
    recentes["dow"] = pd.to_datetime(recentes["data"]).dt.dayofweek
    reportando = recentes["lojas_reportando"].replace(0, np.nan)
    recentes["frac_abertas"] = (recentes["lojas_abertas"] / reportando).fillna(0)
    recentes["frac_promo"] = (recentes["lojas_promo"] / reportando).fillna(0)
    perfil = recentes.groupby("dow")[["frac_abertas", "frac_promo"]].mean()

    linhas = []
    for dia in datas:
        if dia in plano and plano[dia]["lojas_reportando"] > 0:
            p = plano[dia]
            fator = lojas_referencia / float(p["lojas_reportando"])
            fracoes = {
                "lojas_abertas": p["lojas_abertas"] * fator,
                "lojas_promo": p["lojas_promo"] * fator,
                "lojas_feriado_estadual": p["lojas_feriado_estadual"] * fator,
                "lojas_feriado_escolar": p["lojas_feriado_escolar"] * fator,
            }
            fonte = "planejamento"
        else:
            dow = dia.weekday()
            abertas = perfil["frac_abertas"].get(dow, 0.0) if not perfil.empty else 0.0
            promo = perfil["frac_promo"].get(dow, 0.0) if not perfil.empty else 0.0
            fracoes = {
                "lojas_abertas": abertas * lojas_referencia,
                "lojas_promo": promo * lojas_referencia,
                "lojas_feriado_estadual": 0.0,
                "lojas_feriado_escolar": 0.0,
            }
            fonte = "estimado"
        linhas.append({
            "data": pd.Timestamp(dia),
            "lojas_reportando": float(lojas_referencia),
            **{k: float(round(v)) for k, v in fracoes.items()},
            "vendas_total": 0.0,
            "alvo": 0.0,
            "fonte_calendario": fonte,
        })
    return pd.DataFrame(linhas)


def primeiro_dia_proximo_mes(dia: date) -> date:
    return (pd.Timestamp(dia).to_period("M") + 1).to_timestamp().date()


@dataclass
class ResultadoPrevisao:
    mes_referencia: date
    diario: pd.DataFrame  # data, vendas_previstas, lojas_abertas_estimadas, fonte_calendario
    lojas_referencia: int
    ultima_data_historico: date


def prever_proximo_mes(modelo, metadados: dict, agregado_historico: pd.DataFrame,
                       agregado_planejamento: pd.DataFrame | None) -> ResultadoPrevisao:
    """Prevê, dia a dia, todo o mês seguinte ao último dia do histórico e devolve os totais diários."""
    janela = int(metadados["config"]["janela"])
    escalonador = EscalonadorAlvo.de_dict(metadados["escalonador"])

    serie = preparar_serie_diaria(agregado_historico)
    if len(serie) < janela:
        raise ValueError(f"Histórico insuficiente: são necessários ao menos {janela} dias.")

    ultima_data = pd.Timestamp(serie["data"].iloc[-1]).date()
    lojas_referencia = int(serie["lojas_reportando"].iloc[-1])
    mes_referencia = primeiro_dia_proximo_mes(ultima_data)
    fim_mes = primeiro_dia_proximo_mes(mes_referencia) - timedelta(days=1)
    datas_futuras = [ultima_data + timedelta(days=i) for i in range(1, (fim_mes - ultima_data).days + 1)]

    if agregado_planejamento is not None and not agregado_planejamento.empty:
        agregado_planejamento = agregado_planejamento.copy()
        agregado_planejamento[COLUNAS_AGREGADAS[:-1]] = agregado_planejamento[COLUNAS_AGREGADAS[:-1]].astype(float)

    futuro = montar_calendario_futuro(serie, datas_futuras, agregado_planejamento, lojas_referencia)
    completo = pd.concat([serie, futuro.drop(columns="fonte_calendario")], ignore_index=True)

    exogenas = features_exogenas(completo).to_numpy()
    inicio = len(serie)
    alvo_previsto = previsao_recursiva(
        modelo, escalonador, completo["alvo"].to_numpy(), exogenas,
        completo["lojas_abertas"].to_numpy(), inicio, janela,
    )

    futuro = futuro.assign(
        vendas_previstas=alvo_previsto * futuro["lojas_abertas"].to_numpy(),
        lojas_abertas_estimadas=futuro["lojas_abertas"].astype(int),
    )
    futuro["data"] = pd.to_datetime(futuro["data"]).dt.date
    diario = futuro[futuro["data"] >= mes_referencia][
        ["data", "vendas_previstas", "lojas_abertas_estimadas", "fonte_calendario"]
    ].reset_index(drop=True)

    return ResultadoPrevisao(
        mes_referencia=mes_referencia,
        diario=diario,
        lojas_referencia=lojas_referencia,
        ultima_data_historico=ultima_data,
    )
