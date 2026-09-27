"""Orquestra a previsão: dados do PostgreSQL -> modelo LSTM treinado -> resultado persistido.

O treinamento NUNCA acontece aqui: a API apenas carrega o modelo salvo por
`python -m app.ml.train` e executa a inferência.
"""
import threading
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.artifacts import (
    ARQUIVO_METADADOS,
    ArtefatosModelo,
    ModeloNaoTreinadoError,
    carregar_artefatos,
    carregar_metadados,
)
from app.ml.predictor import DIAS_BASELINE, ResultadoPrevisao, prever_proximo_mes, primeiro_dia_proximo_mes
from app.models.varejo import VendaHistorica
from app.repositories.previsao_repository import PrevisaoRepository
from app.repositories.varejo_repository import VarejoRepository
from app.schemas.previsao import (
    AvaliacaoModelo,
    HistoricoVsPrevisao,
    MetricasModelo,
    PontoComparacao,
    PontoPrevisao,
    PrevisaoProximoMes,
    StatusPrevisao,
)
from app.schemas.varejo import TotalPeriodo
from app.services.varejo_service import MSG_SEM_DADOS

MSG_SEM_MODELO = (
    "O modelo de previsão ainda não foi treinado. Execute: docker compose exec backend python -m app.ml.train"
)

_trava = threading.Lock()
_cache_artefatos: dict[str, tuple[float, ArtefatosModelo]] = {}
_cache_previsoes: dict[tuple, ResultadoPrevisao] = {}


def _carregar_modelo() -> ArtefatosModelo:
    """Carrega o modelo do disco e o mantém em memória até que um novo treino o substitua."""
    pasta = Path(settings.model_dir)
    try:
        modificado = (pasta / ARQUIVO_METADADOS).stat().st_mtime
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MSG_SEM_MODELO)
    with _trava:
        em_cache = _cache_artefatos.get(str(pasta))
        if em_cache and em_cache[0] == modificado:
            return em_cache[1]
        try:
            artefatos = carregar_artefatos(pasta)
        except ModeloNaoTreinadoError:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MSG_SEM_MODELO)
        except Exception as erro:  # arquivo corrompido ou incompatível
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Não foi possível carregar o modelo treinado ({erro}). Treine novamente o modelo.",
            )
        _cache_artefatos[str(pasta)] = (modificado, artefatos)
        return artefatos


def _metricas(dados: dict) -> MetricasModelo:
    return MetricasModelo(**dados)


class PrevisaoService:
    def __init__(self, db: Session):
        self.db = db
        self.varejo_repo = VarejoRepository(db)
        self.previsao_repo = PrevisaoRepository(db)

    def _ultima_data(self) -> date | None:
        return self.db.execute(select(func.max(VendaHistorica.data))).scalar_one_or_none()

    def status(self) -> StatusPrevisao:
        ultima = self._ultima_data()
        planejamento = self.varejo_repo.possui_planejamento() if ultima else False
        try:
            metadados = carregar_metadados(settings.model_dir)
        except (ModeloNaoTreinadoError, ValueError):
            metadados = None

        if not ultima:
            mensagem = MSG_SEM_DADOS
        elif not metadados:
            mensagem = MSG_SEM_MODELO
        else:
            mensagem = "Dados importados e modelo treinado. Previsão disponível."
        return StatusPrevisao(
            dados_importados=ultima is not None,
            planejamento_disponivel=planejamento,
            modelo_treinado=metadados is not None,
            versao_modelo=metadados.get("versao") if metadados else None,
            treinado_em=metadados.get("treinado_em") if metadados else None,
            mensagem=mensagem,
        )

    def _prever(self) -> tuple[ResultadoPrevisao, ArtefatosModelo]:
        ultima = self._ultima_data()
        if ultima is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MSG_SEM_DADOS)
        artefatos = _carregar_modelo()
        versao = artefatos.metadados["versao"]

        chave = (versao, ultima)
        if chave in _cache_previsoes:
            return _cache_previsoes[chave], artefatos

        janela = int(artefatos.metadados["config"]["janela"])
        desde = ultima - timedelta(days=max(janela, DIAS_BASELINE) + 14)
        historico = self.varejo_repo.agregado_diario(desde=desde)
        fim_previsao = primeiro_dia_proximo_mes(primeiro_dia_proximo_mes(ultima)) - timedelta(days=1)
        planejamento = self.varejo_repo.agregado_planejamento(ultima + timedelta(days=1), fim_previsao)

        try:
            resultado = prever_proximo_mes(artefatos.modelo, artefatos.metadados, historico, planejamento)
        except ValueError as erro:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro))

        self.previsao_repo.salvar(resultado.mes_referencia, versao, resultado.diario.to_dict("records"))
        _cache_previsoes.clear()
        _cache_previsoes[chave] = resultado
        return resultado, artefatos

    def proximo_mes(self) -> PrevisaoProximoMes:
        resultado, artefatos = self._prever()
        diario = resultado.diario
        valor_previsto = float(diario["vendas_previstas"].sum())

        ultima = resultado.ultima_data_historico
        inicio_ultimo_mes = ultima.replace(day=1)
        total_ultimo_mes = self.varejo_repo.total_periodo(inicio_ultimo_mes, ultima)

        fontes = set(diario["fonte_calendario"])
        return PrevisaoProximoMes(
            mes_referencia=resultado.mes_referencia.strftime("%Y-%m"),
            periodo_inicio=diario["data"].iloc[0],
            periodo_fim=diario["data"].iloc[-1],
            valor_previsto=valor_previsto,
            ultimo_mes_real=TotalPeriodo(periodo=inicio_ultimo_mes.strftime("%Y-%m"), vendas=total_ultimo_mes),
            variacao_percentual=(valor_previsto - total_ultimo_mes) / total_ultimo_mes * 100
            if total_ultimo_mes else None,
            ultima_data_historico=ultima,
            lojas_referencia=resultado.lojas_referencia,
            fonte_calendario=fontes.pop() if len(fontes) == 1 else "misto",
            versao_modelo=artefatos.metadados["versao"],
            metricas=_metricas(artefatos.metricas["lstm"]),
            diario=[PontoPrevisao(**linha) for linha in diario.to_dict("records")],
        )

    def historico_vs_previsao(self, dias: int) -> HistoricoVsPrevisao:
        resultado, _ = self._prever()
        ultima = resultado.ultima_data_historico

        historico = self.varejo_repo.agregado_diario(desde=ultima - timedelta(days=dias - 1))
        diario = [
            PontoComparacao(periodo=pd.Timestamp(d).date().isoformat(), real=float(v))
            for d, v in zip(historico["data"], historico["vendas_total"])
        ]
        # Conecta as duas linhas no gráfico: o último ponto real também inicia a linha prevista
        if diario:
            diario[-1].previsto = diario[-1].real
        diario += [
            PontoComparacao(periodo=linha["data"].isoformat(), previsto=float(linha["vendas_previstas"]))
            for linha in resultado.diario.to_dict("records")
        ]

        mensal = [PontoComparacao(periodo=p["periodo"], real=p["vendas"]) for p in self.varejo_repo.serie("mes")]
        if mensal:
            mensal[-1].previsto = mensal[-1].real
        mensal.append(PontoComparacao(
            periodo=resultado.mes_referencia.strftime("%Y-%m"),
            previsto=float(resultado.diario["vendas_previstas"].sum()),
        ))
        return HistoricoVsPrevisao(
            mes_previsto=resultado.mes_referencia.strftime("%Y-%m"), diario=diario, mensal=mensal
        )

    def avaliacao(self) -> AvaliacaoModelo:
        artefatos = _carregar_modelo()
        meta, metricas = artefatos.metadados, artefatos.metricas
        return AvaliacaoModelo(
            versao=meta["versao"],
            treinado_em=meta["treinado_em"],
            arquitetura=meta["arquitetura"],
            parametros_treinaveis=meta["parametros_treinaveis"],
            config=meta["config"],
            features_exogenas=meta["features_exogenas"],
            divisao=meta["divisao"],
            amostras=meta["amostras"],
            epocas_executadas=meta["epocas_executadas"],
            melhor_epoca=meta["melhor_epoca"],
            periodo_teste=metricas["periodo_teste"],
            metricas_lstm=_metricas(metricas["lstm"]),
            metricas_baseline=_metricas(metricas["baseline"]),
            meses=metricas["meses"],
            diario=artefatos.avaliacao,
            historico_treino=artefatos.historico,
        )
