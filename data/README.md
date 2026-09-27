# Dados — Rossmann Store Sales

Esta pasta é montada no container do backend em `/data`.

```
data/
├── raw/         arquivos originais do Kaggle (NÃO versionados)
│   ├── train.csv     obrigatório
│   ├── store.csv     obrigatório
│   └── test.csv      recomendado (calendário planejado do período futuro)
├── processed/   gerados pelo pipeline (NÃO versionados)
│   ├── serie_diaria.csv           série diária agregada + features (gerada pelo treino)
│   └── vendas_integradas.csv.gz   train + store integrados (ingest --exportar-processado)
└── README.md
```

## Fonte e termos de uso

* Competição: https://www.kaggle.com/c/rossmann-store-sales
* Dados: https://www.kaggle.com/c/rossmann-store-sales/data
* Regras: https://www.kaggle.com/c/rossmann-store-sales/rules

Os dados estão sujeitos às **regras da competição no Kaggle**. Eles **não** são declarados aqui como domínio
público ou de licença livre. São usados apenas para **fins acadêmicos**, como base de demonstração do FinanTrack,
e **não são redistribuídos** neste repositório.

## Como obter

1. Faça login no Kaggle e aceite as regras em https://www.kaggle.com/c/rossmann-store-sales/rules.
2. Baixe `train.csv`, `store.csv` e `test.csv` em https://www.kaggle.com/c/rossmann-store-sales/data.
3. Coloque-os em `data/raw/`.
4. Verifique e importe:

```bash
docker compose exec backend python -m app.ml.ingest --verificar
docker compose exec backend python -m app.ml.ingest
```

O download não é automatizado porque exige autenticação e aceite individual das regras. Quem já tiver a
CLI do Kaggle configurada pode usar `kaggle competitions download -c rossmann-store-sales -p data/raw` e descompactar.

## Conteúdo esperado

| Arquivo | Linhas | Colunas principais |
|---|---:|---|
| train.csv | 1.017.209 | Store, DayOfWeek, Date, Sales, Customers, Open, Promo, StateHoliday, SchoolHoliday |
| store.csv | 1.115 | Store, StoreType, Assortment, CompetitionDistance, CompetitionOpenSince*, Promo2, Promo2Since*, PromoInterval |
| test.csv | 41.088 | Id, Store, DayOfWeek, Date, Open, Promo, StateHoliday, SchoolHoliday (sem Sales) |

Período do train.csv: 01/01/2013 a 31/07/2015. Período do test.csv: 01/08/2015 a 17/09/2015 (856 lojas).
Observação: 180 lojas não têm registros entre 01/07/2014 e 31/12/2014 no train.csv (característica do dataset).
