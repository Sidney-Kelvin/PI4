"""Métricas de avaliação da previsão.

MAPE e dias com venda zero: quando todas as lojas fecham (ex.: Natal), a venda
real é 0 e o erro percentual |real - previsto| / real fica indefinido (divisão
por zero). Esses dias são EXCLUÍDOS do MAPE e a quantidade excluída é
informada junto com a métrica. MAE e RMSE usam todos os dias.
"""
import numpy as np


def mae(real: np.ndarray, previsto: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(real) - np.asarray(previsto))))


def rmse(real: np.ndarray, previsto: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(real) - np.asarray(previsto)) ** 2)))


def mape(real: np.ndarray, previsto: np.ndarray) -> tuple[float | None, int]:
    """Retorna (MAPE em %, número de dias excluídos por venda real igual a zero)."""
    real = np.asarray(real, dtype=float)
    previsto = np.asarray(previsto, dtype=float)
    validos = real != 0
    excluidos = int((~validos).sum())
    if not validos.any():
        return None, excluidos
    erro = np.abs((real[validos] - previsto[validos]) / real[validos])
    return float(np.mean(erro) * 100), excluidos


def calcular_metricas(real: np.ndarray, previsto: np.ndarray) -> dict:
    valor_mape, excluidos = mape(real, previsto)
    return {
        "mae": mae(real, previsto),
        "rmse": rmse(real, previsto),
        "mape": valor_mape,
        "dias_avaliados": int(len(real)),
        "dias_excluidos_mape": excluidos,
    }
