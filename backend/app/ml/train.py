"""Treinamento, avaliação e salvamento do modelo LSTM de previsão de vendas.

Uso (dentro do container do backend, após importar os dados):
    python -m app.ml.train
    python -m app.ml.train --epocas 100 --janela 28

Fluxo:
    1. Lê do PostgreSQL a série diária agregada (vendas_historicas).
    2. Divide no tempo: treino | validação (2 meses) | teste (2 últimos meses).
    3. Ajusta o escalonador do alvo SOMENTE no treino.
    4. Treina a LSTM com parada antecipada pela perda de validação.
    5. Avalia no teste com previsão recursiva mês a mês (sem ver as vendas
       reais do mês previsto) e compara com um baseline sazonal ingênuo.
    6. Salva pesos, metadados, métricas e avaliação em MODEL_DIR.
"""
import argparse
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.config import settings
from app.ml.artifacts import salvar_artefatos
from app.ml.features import (
    FEATURES_EXOGENAS,
    EscalonadorAlvo,
    dividir_temporalmente,
    features_exogenas,
    montar_amostras,
    preparar_serie_diaria,
)
from app.ml.metrics import calcular_metricas
from app.ml.predictor import previsao_baseline, previsao_recursiva


@dataclass
class ConfigTreino:
    janela: int = 28  # dias de histórico observados pela LSTM
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    taxa_aprendizado: float = 1e-3
    tamanho_lote: int = 32
    epocas: int = 150  # máximo; a parada antecipada normalmente encerra antes
    paciencia: int = 15
    meses_validacao: int = 2
    meses_teste: int = 2
    semente: int = 42


def _fixar_sementes(semente: int) -> None:
    import torch

    random.seed(semente)
    np.random.seed(semente)
    torch.manual_seed(semente)


def _indices(serie: pd.DataFrame, inicio: pd.Timestamp | None, fim: pd.Timestamp | None) -> np.ndarray:
    """Índices de dias com lojas abertas no intervalo [inicio, fim)."""
    datas = pd.to_datetime(serie["data"])
    mascara = serie["lojas_abertas"] > 0
    if inicio is not None:
        mascara &= datas >= inicio
    if fim is not None:
        mascara &= datas < fim
    return np.flatnonzero(mascara.to_numpy())


def _avaliar_teste(modelo, escalonador, serie, exogenas, inicio_teste, janela):
    """Previsão recursiva de cada mês do teste, partindo do histórico real até o dia anterior ao mês."""
    datas = pd.to_datetime(serie["data"])
    meses = sorted(datas[datas >= pd.Timestamp(inicio_teste)].dt.to_period("M").unique())
    avaliacao, resumo_meses = [], []

    for mes in meses:
        inicio_mes = mes.to_timestamp()
        fim_mes = (mes + 1).to_timestamp()
        inicio = int(np.flatnonzero((datas >= inicio_mes).to_numpy())[0])
        fim = int(np.flatnonzero((datas < fim_mes).to_numpy())[-1]) + 1
        recorte = serie.iloc[:fim]

        alvo_lstm = previsao_recursiva(modelo, escalonador, recorte["alvo"].to_numpy(), exogenas[:fim],
                                       recorte["lojas_abertas"].to_numpy(), inicio, janela)
        alvo_base = previsao_baseline(recorte, inicio)

        abertas = recorte["lojas_abertas"].to_numpy()[inicio:]
        real = recorte["vendas_total"].to_numpy()[inicio:]
        prev_lstm = alvo_lstm * abertas
        prev_base = alvo_base * abertas

        for i, dia in enumerate(pd.to_datetime(recorte["data"].iloc[inicio:])):
            avaliacao.append({
                "data": dia.date().isoformat(),
                "real": round(float(real[i]), 2),
                "previsto": round(float(prev_lstm[i]), 2),
                "baseline": round(float(prev_base[i]), 2),
            })
        total_real = float(real.sum())
        total_prev = float(prev_lstm.sum())
        resumo_meses.append({
            "mes": str(mes),
            "real": round(total_real, 2),
            "previsto": round(total_prev, 2),
            "baseline": round(float(prev_base.sum()), 2),
            "erro_percentual": round((total_prev - total_real) / total_real * 100, 2) if total_real else None,
        })
    return avaliacao, resumo_meses


def treinar(agregado: pd.DataFrame, config: ConfigTreino, pasta_saida: str | Path, verbose: bool = True) -> dict:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, TensorDataset

    from app.ml.model import SalesLSTM, contar_parametros

    inicio_execucao = time.perf_counter()
    _fixar_sementes(config.semente)
    torch.set_num_threads(max(1, min(8, torch.get_num_threads())))

    serie = preparar_serie_diaria(agregado)
    divisao = dividir_temporalmente(serie["data"], config.meses_validacao, config.meses_teste)
    inicio_val = pd.Timestamp(divisao.inicio_validacao)
    inicio_teste = pd.Timestamp(divisao.inicio_teste)

    idx_treino = _indices(serie, None, inicio_val)
    idx_val = _indices(serie, inicio_val, inicio_teste)

    # Escalonador ajustado apenas com o alvo dos dias de TREINO (evita vazamento)
    escalonador = EscalonadorAlvo.ajustar(serie["alvo"].to_numpy()[idx_treino])
    alvo_escalonado = escalonador.transformar(serie["alvo"].to_numpy())
    exogenas = features_exogenas(serie).to_numpy()

    x_treino, e_treino, y_treino = montar_amostras(alvo_escalonado, exogenas, idx_treino, config.janela)
    x_val, e_val, y_val = montar_amostras(alvo_escalonado, exogenas, idx_val, config.janela)
    if len(y_treino) == 0 or len(y_val) == 0:
        raise ValueError("Dados insuficientes para gerar amostras de treino e validação.")

    # Embaralhar as JANELAS de treino é seguro: cada janela já contém apenas dias
    # anteriores ao seu alvo, e nenhuma janela de treino alcança a validação/teste.
    carregador = DataLoader(
        TensorDataset(torch.from_numpy(x_treino), torch.from_numpy(e_treino), torch.from_numpy(y_treino)),
        batch_size=config.tamanho_lote, shuffle=True,
        generator=torch.Generator().manual_seed(config.semente),
    )
    x_val_t, e_val_t, y_val_t = map(torch.from_numpy, (x_val, e_val, y_val))

    modelo = SalesLSTM(len(FEATURES_EXOGENAS), config.hidden_size, config.num_layers, config.dropout)
    otimizador = torch.optim.Adam(modelo.parameters(), lr=config.taxa_aprendizado)
    criterio = nn.MSELoss()

    melhor_perda, melhor_estado, melhor_epoca, sem_melhora = float("inf"), None, 0, 0
    historico = []
    for epoca in range(1, config.epocas + 1):
        modelo.train()
        soma = 0.0
        for seq, exog, alvo in carregador:
            otimizador.zero_grad()
            perda = criterio(modelo(seq, exog), alvo)
            perda.backward()
            nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            otimizador.step()
            soma += perda.item() * len(alvo)
        perda_treino = soma / len(y_treino)

        modelo.eval()
        with torch.no_grad():
            perda_val = criterio(modelo(x_val_t, e_val_t), y_val_t).item()
        historico.append({
            "epoca": epoca, "perda_treino": round(perda_treino, 6), "perda_validacao": round(perda_val, 6)
        })

        if perda_val < melhor_perda - 1e-6:
            melhor_perda, melhor_epoca, sem_melhora = perda_val, epoca, 0
            melhor_estado = {k: v.detach().clone() for k, v in modelo.state_dict().items()}
        else:
            sem_melhora += 1
        if verbose and (epoca == 1 or epoca % 10 == 0):
            print(f"  época {epoca:3d} | perda treino {perda_treino:.4f} | perda validação {perda_val:.4f}")
        if sem_melhora >= config.paciencia:
            if verbose:
                print(f"  parada antecipada na época {epoca} (melhor época: {melhor_epoca})")
            break

    modelo.load_state_dict(melhor_estado)
    modelo.eval()

    avaliacao, resumo_meses = _avaliar_teste(modelo, escalonador, serie, exogenas, divisao.inicio_teste, config.janela)
    real = np.array([a["real"] for a in avaliacao])
    metricas = {
        "periodo_teste": {"inicio": divisao.inicio_teste.isoformat(), "fim": divisao.fim.isoformat()},
        "unidade": "vendas totais diárias da rede",
        "lstm": calcular_metricas(real, np.array([a["previsto"] for a in avaliacao])),
        "baseline": calcular_metricas(real, np.array([a["baseline"] for a in avaliacao])),
        "meses": resumo_meses,
    }

    versao = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    metadados = {
        "versao": versao,
        "treinado_em": datetime.now(timezone.utc).isoformat(),
        "arquitetura": (f"LSTM({config.num_layers} camadas, {config.hidden_size} unidades) "
                        f"+ Densa(32, ReLU) + Densa(1)"),
        "parametros_treinaveis": contar_parametros(modelo),
        "config": asdict(config),
        "features_exogenas": FEATURES_EXOGENAS,
        "escalonador": escalonador.para_dict(),
        "divisao": divisao.para_dict(),
        "amostras": {"treino": int(len(y_treino)), "validacao": int(len(y_val)), "teste_dias": len(avaliacao)},
        "epocas_executadas": len(historico),
        "melhor_epoca": melhor_epoca,
        "perda_validacao": round(melhor_perda, 6),
        "lojas_ultimo_dia": int(serie["lojas_reportando"].iloc[-1]),
        "duracao_segundos": round(time.perf_counter() - inicio_execucao, 1),
    }
    salvar_artefatos(pasta_saida, melhor_estado, metadados, metricas, avaliacao, historico)
    return {"metadados": metadados, "metricas": metricas, "serie": serie}


def _exportar_serie_processada(serie: pd.DataFrame, data_dir: str) -> Path | None:
    """Salva a série diária + features usada no treino em data/processed/ (para inspeção)."""
    try:
        pasta = Path(data_dir) / "processed"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / "serie_diaria.csv"
        pd.concat([serie, features_exogenas(serie)], axis=1).to_csv(caminho, index=False)
        return caminho
    except OSError:
        return None


def _formatar(valor: float | None, sufixo: str = "") -> str:
    return "n/d" if valor is None else f"{valor:,.2f}{sufixo}".replace(",", "X").replace(".", ",").replace("X", ".")


def main(argv: list[str] | None = None) -> int:
    padrao = ConfigTreino()
    parser = argparse.ArgumentParser(description="Treina o modelo LSTM de previsão de vendas do FinanTrack.")
    parser.add_argument("--epocas", type=int, default=padrao.epocas)
    parser.add_argument("--janela", type=int, default=padrao.janela)
    parser.add_argument("--paciencia", type=int, default=padrao.paciencia)
    parser.add_argument("--semente", type=int, default=padrao.semente)
    parser.add_argument("--saida", default=settings.model_dir, help="Pasta de saída (padrão: MODEL_DIR)")
    args = parser.parse_args(argv)

    from app.core.database import SessionLocal
    from app.repositories.varejo_repository import VarejoRepository

    config = ConfigTreino(epocas=args.epocas, janela=args.janela, paciencia=args.paciencia, semente=args.semente)
    print("Carregando série diária agregada do PostgreSQL...")
    with SessionLocal() as sessao:
        agregado = VarejoRepository(sessao).agregado_diario()
    if agregado.empty:
        print("ERRO: não há dados em vendas_historicas. Execute antes: python -m app.ml.ingest")
        return 1
    print(f"  {len(agregado)} dias ({agregado['data'].min()} a {agregado['data'].max()})")

    print("Treinando LSTM...")
    try:
        resultado = treinar(agregado, config, args.saida)
    except ValueError as erro:
        print(f"ERRO: {erro}")
        return 1

    caminho = _exportar_serie_processada(resultado["serie"], settings.data_dir)
    meta, metricas = resultado["metadados"], resultado["metricas"]
    print("\nModelo salvo em:", Path(args.saida).resolve())
    if caminho:
        print("Série processada salva em:", caminho.resolve())
    print(f"Versão: {meta['versao']} | épocas: {meta['epocas_executadas']} (melhor: {meta['melhor_epoca']})")
    print(f"Divisão temporal: {meta['divisao']}")
    print(f"\nAvaliação no teste ({metricas['periodo_teste']['inicio']} a {metricas['periodo_teste']['fim']}), "
          "vendas totais diárias:")
    for nome in ("lstm", "baseline"):
        m = metricas[nome]
        print(f"  {nome.upper():8s} MAE {_formatar(m['mae'])} | RMSE {_formatar(m['rmse'])} | "
              f"MAPE {_formatar(m['mape'], '%')} ({m['dias_excluidos_mape']} dia(s) com venda zero excluído(s))")
    for mes in metricas["meses"]:
        print(f"  {mes['mes']}: real {_formatar(mes['real'])} | LSTM {_formatar(mes['previsto'])} "
              f"| erro {_formatar(mes['erro_percentual'], '%')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
