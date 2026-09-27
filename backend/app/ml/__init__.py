"""Pipeline de dados e Deep Learning (LSTM) do FinanTrack.

Etapas e módulos:
    data_preparation  -> verificação, carga e limpeza dos CSVs do Rossmann
    ingest            -> CLI que grava os dados limpos no PostgreSQL
    features          -> série diária agregada + variáveis do modelo + escalonamento
    model             -> arquitetura LSTM (PyTorch)
    metrics           -> MAE, RMSE, MAPE
    train             -> CLI de treino com divisão temporal, avaliação e salvamento
    artifacts         -> salvar/carregar o modelo treinado
    predictor         -> previsão recursiva usada pela API
"""
