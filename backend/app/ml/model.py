"""Arquitetura LSTM para previsão de vendas diárias."""
import torch
from torch import nn


class SalesLSTM(nn.Module):
    """LSTM que lê a janela de dias anteriores e prevê o alvo do dia seguinte.

    Entrada:
        sequencia    (lote, janela, 1 + n_exogenas)  alvo passado + features de cada dia passado
        exogenas_dia (lote, n_exogenas)              features conhecidas do dia a prever
    Saída:
        (lote,) alvo previsto (escala padronizada)

    O estado oculto final da LSTM resume o histórico recente; ele é concatenado
    às informações já conhecidas do dia previsto (dia da semana, promoção,
    feriado, lojas abertas) e passa por uma pequena rede densa.
    """

    def __init__(self, n_exogenas: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=1 + n_exogenas,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.cabeca = nn.Sequential(
            nn.Linear(hidden_size + n_exogenas, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, sequencia: torch.Tensor, exogenas_dia: torch.Tensor) -> torch.Tensor:
        saida, _ = self.lstm(sequencia)
        ultimo_estado = saida[:, -1, :]
        return self.cabeca(torch.cat([ultimo_estado, exogenas_dia], dim=1)).squeeze(-1)


def contar_parametros(modelo: nn.Module) -> int:
    return sum(p.numel() for p in modelo.parameters() if p.requires_grad)
