# Frontend — FinanTrack (PI4)

Interface web em **React 19 + TypeScript + Vite + Tailwind CSS**, com gráficos em **Recharts**.
Visão geral do projeto: veja o [README principal](../README.md).

## Páginas

| Rota | Página |
|---|---|
| `/` | Dashboard: operação (R$), histórico de varejo, previsão do próximo mês, métricas do modelo, histórico × previsão |
| `/varejo` | Histórico de varejo: série por dia/mês/ano com filtros, quebras (dia da semana, promoção, feriado, tipo de loja, sortimento), ranking de lojas |
| `/previsao` | Análise preditiva: previsão diária, real × previsto no teste, métricas vs. baseline, detalhes e curva de aprendizado do modelo |
| `/vendas`, `/despesas`, `/estoque`, `/empresa` | Módulos herdados do PI3 |

## Estrutura

```
src/
├── api/            cliente Axios (baseURL = VITE_API_URL, padrão /api) e funções por recurso
│                   (dashboard, produtos, vendas, despesas, external, varejo, previsoes, errors)
├── components/
│   ├── layout/     Sidebar, Header (acessibilidade), Layout
│   ├── ui/         StatCard, Panel, StateMessage, Alert, Modal, Spinner, CepSearch
│   ├── charts/     SalesLineChart, HistoryForecastChart, RealVsPredictedChart, CategoryBarChart, LossChart
│   └── forecast/   ForecastSummary, ModelMetrics, ForecastGate (avisos de dados/modelo ausentes)
├── hooks/useApi.ts carregamento + erro padronizados
├── context/        AccessibilityContext (alto contraste e filtros de daltonismo)
├── pages/          Dashboard, Varejo, Previsao, Vendas, Despesas, Estoque, Empresa
├── types/          tipos TypeScript espelhando os schemas da API
└── utils/format.ts formatação pt-BR (moeda, números compactos, datas, períodos)
```

## Comunicação com o backend

No Docker, o nginx do container serve o build e faz proxy de `/api/*` para `http://backend:8080/*` (rede interna).
O navegador acessa apenas `http://localhost:3000`. Todos os valores de previsão e métricas vêm da API.

## Executar

Oficialmente pelo Docker Compose, na raiz do projeto: `docker compose up -d --build` → http://localhost:3000

Desenvolvimento com hot reload (opcional, requer Node.js 20+ e o backend em `localhost:8080`):

```bash
cd frontend
npm install
echo VITE_API_URL=http://localhost:8080 > .env
npm run dev          # http://localhost:5173
npm run build        # type check + build de produção
```
