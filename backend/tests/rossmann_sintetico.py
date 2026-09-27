"""Gera CSVs PEQUENOS e ARTIFICIAIS no mesmo formato do Rossmann Store Sales.

Uso exclusivo nos testes automatizados (validam o pipeline sem depender do
download do Kaggle). Nenhum resultado obtido com estes dados representa o
dataset real nem deve ser apresentado como métrica do modelo.
"""
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

LOJAS = [
    # Store, StoreType, Assortment, CompetitionDistance, Promo2
    (1, "c", "a", 1270.0, 0),
    (2, "a", "a", 570.0, 1),
    (3, "a", "c", None, 1),
    (4, "d", "c", 620.0, 0),
]


def gerar(pasta: Path, inicio: date = date(2013, 1, 1), fim: date = date(2014, 3, 31),
          dias_teste: int = 45, semente: int = 0) -> Path:
    rng = np.random.default_rng(semente)
    pasta.mkdir(parents=True, exist_ok=True)

    pd.DataFrame([
        {
            "Store": s, "StoreType": t, "Assortment": a, "CompetitionDistance": d,
            "CompetitionOpenSinceMonth": 9 if d else None, "CompetitionOpenSinceYear": 2008 if d else None,
            "Promo2": p, "Promo2SinceWeek": 13 if p else None, "Promo2SinceYear": 2010 if p else None,
            "PromoInterval": "Jan,Apr,Jul,Oct" if p else None,
        }
        for s, t, a, d, p in LOJAS
    ]).to_csv(pasta / "store.csv", index=False)

    linhas = []
    dia = inicio
    while dia <= fim:
        semana = dia.isocalendar()[1]
        promo = int(semana % 2 == 0 and dia.weekday() < 5)
        natal = dia.month == 12 and dia.day == 25
        for store, *_ in LOJAS:
            aberta = int(dia.weekday() != 6 and not natal)
            base = 4000 + 800 * store
            vendas = base * (1.2 if dia.weekday() == 0 else 1.0) * (1.25 if promo else 1.0)
            vendas *= 1 + 0.1 * np.sin(2 * np.pi * dia.timetuple().tm_yday / 365)
            vendas = int(max(0, vendas + rng.normal(0, 150))) if aberta else 0
            linhas.append({
                "Store": store, "DayOfWeek": dia.isoweekday(), "Date": dia.isoformat(), "Sales": vendas,
                "Customers": vendas // 9 if aberta else 0, "Open": aberta, "Promo": promo if aberta else 0,
                # Mistura inteiro e texto, como no arquivo original
                "StateHoliday": "c" if natal else 0, "SchoolHoliday": int(dia.month in (7, 8)),
            })
        dia += timedelta(days=1)
    # train.csv original vem em ordem decrescente de data
    pd.DataFrame(linhas[::-1]).to_csv(pasta / "train.csv", index=False)

    teste = []
    for i in range(1, dias_teste + 1):
        dia = fim + timedelta(days=i)
        for store, *_ in LOJAS[:3]:
            teste.append({
                "Id": len(teste) + 1, "Store": store, "DayOfWeek": dia.isoweekday(), "Date": dia.isoformat(),
                "Open": None if (store == 1 and i == 2) else int(dia.weekday() != 6),
                "Promo": int(dia.isocalendar()[1] % 2 == 0 and dia.weekday() < 5),
                "StateHoliday": "0", "SchoolHoliday": 0,
            })
    pd.DataFrame(teste).to_csv(pasta / "test.csv", index=False)
    return pasta
