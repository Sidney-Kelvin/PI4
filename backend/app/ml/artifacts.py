"""Persistência do modelo treinado.

Estrutura de models/sales_lstm/:
    model.pt           pesos da rede (state_dict do PyTorch)
    metadata.json      hiperparâmetros, features, escalonador, divisão temporal, versão
    metrics.json       métricas de teste (LSTM e baseline) e totais mensais
    evaluation.json    valores diários reais x previstos no período de teste
    history.json       perda de treino/validação por época
"""
import json
from dataclasses import dataclass
from pathlib import Path

ARQUIVO_MODELO = "model.pt"
ARQUIVO_METADADOS = "metadata.json"
ARQUIVO_METRICAS = "metrics.json"
ARQUIVO_AVALIACAO = "evaluation.json"
ARQUIVO_HISTORICO = "history.json"


class ModeloNaoTreinadoError(FileNotFoundError):
    """Ainda não existe modelo treinado na pasta configurada."""


def _escrever_json(caminho: Path, dados) -> None:
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def _ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def modelo_existe(pasta: str | Path) -> bool:
    pasta = Path(pasta)
    return (pasta / ARQUIVO_MODELO).is_file() and (pasta / ARQUIVO_METADADOS).is_file()


def salvar_artefatos(pasta: str | Path, estado_modelo: dict, metadados: dict, metricas: dict,
                     avaliacao: list[dict], historico: list[dict]) -> Path:
    import torch

    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    torch.save(estado_modelo, pasta / ARQUIVO_MODELO)
    _escrever_json(pasta / ARQUIVO_METRICAS, metricas)
    _escrever_json(pasta / ARQUIVO_AVALIACAO, avaliacao)
    _escrever_json(pasta / ARQUIVO_HISTORICO, historico)
    # Metadados por último: sua presença indica que o conjunto está completo
    _escrever_json(pasta / ARQUIVO_METADADOS, metadados)
    return pasta


@dataclass
class ArtefatosModelo:
    modelo: object  # SalesLSTM em modo de avaliação
    metadados: dict
    metricas: dict
    avaliacao: list[dict]
    historico: list[dict]


def carregar_metadados(pasta: str | Path) -> dict:
    pasta = Path(pasta)
    if not modelo_existe(pasta):
        raise ModeloNaoTreinadoError(str(pasta))
    return _ler_json(pasta / ARQUIVO_METADADOS)


def carregar_artefatos(pasta: str | Path) -> ArtefatosModelo:
    import torch
    from app.ml.model import SalesLSTM

    pasta = Path(pasta)
    metadados = carregar_metadados(pasta)
    config = metadados["config"]
    modelo = SalesLSTM(
        n_exogenas=len(metadados["features_exogenas"]),
        hidden_size=config["hidden_size"],
        num_layers=config["num_layers"],
        dropout=config["dropout"],
    )
    modelo.load_state_dict(torch.load(pasta / ARQUIVO_MODELO, map_location="cpu", weights_only=True))
    modelo.eval()

    def opcional(nome: str, padrao):
        caminho = pasta / nome
        return _ler_json(caminho) if caminho.is_file() else padrao

    return ArtefatosModelo(
        modelo=modelo,
        metadados=metadados,
        metricas=opcional(ARQUIVO_METRICAS, {}),
        avaliacao=opcional(ARQUIVO_AVALIACAO, []),
        historico=opcional(ARQUIVO_HISTORICO, []),
    )
