"""Verificação, carga e limpeza dos arquivos do dataset Rossmann Store Sales.

Fonte: https://www.kaggle.com/c/rossmann-store-sales/data
Os arquivos precisam ser baixados manualmente do Kaggle (exige login e aceite
das regras da competição) e colocados em data/raw/.
"""
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ARQUIVOS_OBRIGATORIOS = ("train.csv", "store.csv")
ARQUIVOS_OPCIONAIS = ("test.csv",)

FERIADOS_VALIDOS = {"0", "a", "b", "c"}


class DadosAusentesError(FileNotFoundError):
    """Algum CSV obrigatório não foi encontrado na pasta de dados."""


@dataclass
class VerificacaoArquivos:
    pasta: Path
    encontrados: list[str] = field(default_factory=list)
    ausentes_obrigatorios: list[str] = field(default_factory=list)
    ausentes_opcionais: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.ausentes_obrigatorios


def resolver_pasta_raw(data_dir: str | Path) -> Path:
    """Aceita tanto a pasta `data/` quanto `data/raw/`."""
    pasta = Path(data_dir)
    return pasta / "raw" if (pasta / "raw").is_dir() else pasta


def verificar_arquivos(data_dir: str | Path) -> VerificacaoArquivos:
    pasta = resolver_pasta_raw(data_dir)
    resultado = VerificacaoArquivos(pasta=pasta)
    for nome in ARQUIVOS_OBRIGATORIOS + ARQUIVOS_OPCIONAIS:
        if (pasta / nome).is_file():
            resultado.encontrados.append(nome)
        elif nome in ARQUIVOS_OBRIGATORIOS:
            resultado.ausentes_obrigatorios.append(nome)
        else:
            resultado.ausentes_opcionais.append(nome)
    return resultado


def _normalizar_feriado(serie: pd.Series) -> pd.Series:
    # No CSV original StateHoliday mistura o inteiro 0 e a string "0"
    normalizada = serie.astype(str).str.strip().str.lower().replace({"0.0": "0", "nan": "0", "": "0"})
    return normalizada.where(normalizada.isin(FERIADOS_VALIDOS), "0")


def carregar_lojas(pasta: Path) -> pd.DataFrame:
    """Carrega store.csv. Ausências são mantidas como nulas porque significam
    "não se aplica" ou "desconhecido" (ex.: loja sem Promo2 não tem data de adesão)."""
    df = pd.read_csv(pasta / "store.csv")
    df = df.drop_duplicates(subset="Store")
    lojas = pd.DataFrame({
        "id": df["Store"].astype(int),
        "tipo_loja": df["StoreType"].astype(str).str.lower(),
        "sortimento": df["Assortment"].astype(str).str.lower(),
        "distancia_concorrencia": df["CompetitionDistance"].round().astype("Int64"),
        "concorrencia_desde_mes": df["CompetitionOpenSinceMonth"].astype("Int64"),
        "concorrencia_desde_ano": df["CompetitionOpenSinceYear"].astype("Int64"),
        "promo2": df["Promo2"].fillna(0).astype(int).astype(bool),
        "promo2_desde_semana": df["Promo2SinceWeek"].astype("Int64"),
        "promo2_desde_ano": df["Promo2SinceYear"].astype("Int64"),
        "intervalo_promo2": df["PromoInterval"].where(df["PromoInterval"].notna(), None),
    })
    return lojas.sort_values("id").reset_index(drop=True)


def carregar_vendas(pasta: Path) -> pd.DataFrame:
    """Carrega e limpa train.csv (histórico diário de vendas por loja)."""
    df = pd.read_csv(pasta / "train.csv", dtype={"StateHoliday": str}, low_memory=False)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Store", "Date", "Sales"])
    df = df.drop_duplicates(subset=["Store", "Date"], keep="last")

    vendas = pd.DataFrame({
        "loja_id": df["Store"].astype(int),
        "data": df["Date"].dt.date,
        "dia_semana": df["DayOfWeek"].astype(int),
        "vendas": df["Sales"].clip(lower=0).astype(float),
        "clientes": df["Customers"].fillna(0).clip(lower=0).astype(int),
        "aberta": df["Open"].fillna(0).astype(int).astype(bool),
        "promo": df["Promo"].fillna(0).astype(int).astype(bool),
        "feriado_estadual": _normalizar_feriado(df["StateHoliday"]),
        "feriado_escolar": df["SchoolHoliday"].fillna(0).astype(int).astype(bool),
    })
    return vendas.sort_values(["data", "loja_id"]).reset_index(drop=True)


def carregar_planejamento(pasta: Path) -> pd.DataFrame | None:
    """Carrega test.csv (período futuro sem vendas), se existir.

    O campo Open possui alguns valores ausentes no arquivo original; eles são
    tratados como loja aberta (1), já que ocorrem em dias úteis comuns.
    """
    caminho = pasta / "test.csv"
    if not caminho.is_file():
        return None
    df = pd.read_csv(caminho, dtype={"StateHoliday": str}, low_memory=False)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Store", "Date"]).drop_duplicates(subset=["Store", "Date"], keep="last")
    planejamento = pd.DataFrame({
        "loja_id": df["Store"].astype(int),
        "data": df["Date"].dt.date,
        "dia_semana": df["DayOfWeek"].astype(int),
        "aberta": df["Open"].fillna(1).astype(int).astype(bool),
        "promo": df["Promo"].fillna(0).astype(int).astype(bool),
        "feriado_estadual": _normalizar_feriado(df["StateHoliday"]),
        "feriado_escolar": df["SchoolHoliday"].fillna(0).astype(int).astype(bool),
    })
    return planejamento.sort_values(["data", "loja_id"]).reset_index(drop=True)


def integrar_vendas_lojas(vendas: pd.DataFrame, lojas: pd.DataFrame) -> pd.DataFrame:
    """Integra train.csv com store.csv e cria variáveis de calendário.

    Usado para validar a integridade referencial antes da gravação no banco e
    como visão analítica completa (salva em data/processed/).
    """
    lojas_desconhecidas = set(vendas["loja_id"]) - set(lojas["id"])
    if lojas_desconhecidas:
        raise ValueError(f"Vendas referenciam lojas inexistentes em store.csv: {sorted(lojas_desconhecidas)[:10]}")

    integrado = vendas.merge(lojas, left_on="loja_id", right_on="id", how="left").drop(columns="id")
    datas = pd.to_datetime(integrado["data"])
    integrado["ano"] = datas.dt.year
    integrado["mes"] = datas.dt.month
    integrado["dia_do_ano"] = datas.dt.dayofyear
    return integrado


@dataclass
class DadosRossmann:
    lojas: pd.DataFrame
    vendas: pd.DataFrame
    planejamento: pd.DataFrame | None


def preparar_dados(data_dir: str | Path) -> DadosRossmann:
    """Executa verificação, carga, limpeza e validação de todos os arquivos."""
    verificacao = verificar_arquivos(data_dir)
    if not verificacao.ok:
        raise DadosAusentesError(
            f"Arquivos obrigatórios ausentes em {verificacao.pasta}: "
            f"{', '.join(verificacao.ausentes_obrigatorios)}. "
            "Baixe-os em https://www.kaggle.com/c/rossmann-store-sales/data (veja data/README.md)."
        )

    lojas = carregar_lojas(verificacao.pasta)
    vendas = carregar_vendas(verificacao.pasta)
    integrar_vendas_lojas(vendas, lojas)  # valida integridade referencial

    planejamento = carregar_planejamento(verificacao.pasta)
    if planejamento is not None:
        planejamento = planejamento[planejamento["loja_id"].isin(lojas["id"])]
        # O planejamento só é útil para datas posteriores ao histórico
        planejamento = planejamento[planejamento["data"] > vendas["data"].max()].reset_index(drop=True)

    return DadosRossmann(lojas=lojas, vendas=vendas, planejamento=planejamento)
