"""
K-SWARM: Formador de Mercado Automatizado de Predição (K-AMM)
Sistema 1: Execução analítica de ordens, precificação contínua e livro sintético.
Clean-Room Architecture - Zero Dependências AGPL.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Literal
from .models import MarketOrder, MarketTradeResult, MarketSnapshot


class PredictionMarketAMM:
    """
    Automated Market Maker (AMM) para mercados de predição binários (YES / NO).
    Baseado no modelo de produto constante x * y = k com invariante de probabilidade.
    """

    def __init__(
        self,
        market_id: str,
        initial_probability_yes: float = 0.5,
        base_liquidity: float = 1000.0,
        fee_rate: float = 0.002,  # 0.2% taxa de liquidez
    ):
        self.market_id = market_id
        self.initial_probability = max(0.05, min(0.95, float(initial_probability_yes)))
        self.base_liquidity = max(100.0, float(base_liquidity))
        self.fee_rate = max(0.0, float(fee_rate))
        self.total_volume: float = 0.0
        self.trade_history: List[MarketTradeResult] = []

        # Inicializa reservas de modo que P(YES) = R_NO / (R_YES + R_NO)
        # Se P(YES) = 0.60, R_NO = L * 0.60 e R_YES = L * 0.40
        self.pool_yes = self.base_liquidity * (1.0 - self.initial_probability)
        self.pool_no = self.base_liquidity * self.initial_probability
        self.k_constant = self.pool_yes * self.pool_no

    @property
    def price_yes(self) -> float:
        """Probabilidade implícita / Preço de face da cota YES [0.01 a 0.99]."""
        total = self.pool_yes + self.pool_no
        if total <= 0:
            return 0.5
        return max(0.01, min(0.99, self.pool_no / total))

    @property
    def price_no(self) -> float:
        """Probabilidade implícita / Preço de face da cota NO [0.01 a 0.99]."""
        return 1.0 - self.price_yes

    def execute_order(self, order: MarketOrder) -> MarketTradeResult:
        """
        Executa uma ordem de compra ou venda de cotas YES/NO via produto constante.
        Calcula slippage, atualiza pools e registra a transação.
        """
        old_price_yes = self.price_yes
        capital = order.amount
        net_capital = capital * (1.0 - self.fee_rate)

        if order.outcome == "YES" and order.action == "BUY":
            # Compra de YES: capital entra na reserva NO, cotas saem da reserva YES
            new_pool_no = self.pool_no + net_capital
            new_pool_yes = self.k_constant / new_pool_no
            shares_filled = self.pool_yes - new_pool_yes

            if shares_filled <= 0:
                shares_filled = 0.0001

            self.pool_no = new_pool_no
            self.pool_yes = new_pool_yes

        elif order.outcome == "NO" and order.action == "BUY":
            # Compra de NO: capital entra na reserva YES, cotas saem da reserva NO
            new_pool_yes = self.pool_yes + net_capital
            new_pool_no = self.k_constant / new_pool_yes
            shares_filled = self.pool_no - new_pool_no

            if shares_filled <= 0:
                shares_filled = 0.0001

            self.pool_yes = new_pool_yes
            self.pool_no = new_pool_no

        elif order.outcome == "YES" and order.action == "SELL":
            # Venda de YES: cotas YES voltam à reserva, capital sai da reserva NO
            new_pool_yes = self.pool_yes + net_capital
            new_pool_no = self.k_constant / new_pool_yes
            shares_filled = net_capital
            self.pool_yes = new_pool_yes
            self.pool_no = max(1.0, new_pool_no)

        elif order.outcome == "NO" and order.action == "SELL":
            # Venda de NO: cotas NO voltam à reserva, capital sai da reserva YES
            new_pool_no = self.pool_no + net_capital
            new_pool_yes = self.k_constant / new_pool_no
            shares_filled = net_capital
            self.pool_no = new_pool_no
            self.pool_yes = max(1.0, new_pool_yes)

        # Atualiza métricas globais
        self.total_volume += capital
        new_price_yes = self.price_yes
        new_price_no = self.price_no
        price_impact = (new_price_yes - old_price_yes) / old_price_yes if old_price_yes > 0 else 0.0

        avg_price = capital / shares_filled if shares_filled > 0 else old_price_yes

        result = MarketTradeResult(
            order_id=order.order_id,
            trader_id=order.trader_id,
            outcome=order.outcome,
            action=order.action,
            shares_filled=round(shares_filled, 4),
            avg_price=round(avg_price, 4),
            new_probability_yes=round(new_price_yes, 4),
            new_probability_no=round(new_price_no, 4),
            price_impact=round(price_impact, 4),
        )

        self.trade_history.append(result)
        return result

    def trade_from_sentiment(
        self,
        trader_id: str,
        topic_stance: float,
        confidence: float,
        round_index: int,
        max_capital: float = 100.0,
    ) -> Optional[MarketTradeResult]:
        """
        Ponte Mercado-Mídia: Agente trader decide sua ordem baseado no gap
        entre sua postura cognitiva e o preço atual do mercado.
        """
        current_p_yes = self.price_yes
        
        # Mapeia postura [-1.0, 1.0] para probabilidade esperada [0.05, 0.95]
        expected_p_yes = (topic_stance + 1.0) / 2.0
        expected_p_yes = max(0.05, min(0.95, expected_p_yes))

        edge = expected_p_yes - current_p_yes

        # Se a margem percebida for menor que 5%, o trader segura a posição (HOLD)
        if abs(edge) < 0.05:
            return None

        # Alocação proporcional à convicção (Critério de Kelly heurístico)
        capital_to_risk = round(max(5.0, min(max_capital, abs(edge) * confidence * max_capital)), 2)

        outcome: Literal["YES", "NO"] = "YES" if edge > 0 else "NO"
        action: Literal["BUY", "SELL"] = "BUY"

        order = MarketOrder(
            order_id=f"ord_{round_index}_{trader_id}_{outcome}",
            trader_id=trader_id,
            round_index=round_index,
            outcome=outcome,
            action=action,
            amount=capital_to_risk,
        )

        return self.execute_order(order)

    def get_snapshot(self, round_index: int = 0) -> MarketSnapshot:
        """Exporta o estado atual das reservas e probabilidades."""
        return MarketSnapshot(
            market_id=self.market_id,
            round_index=round_index,
            price_yes=round(self.price_yes, 4),
            price_no=round(self.price_no, 4),
            pool_yes=round(self.pool_yes, 2),
            pool_no=round(self.pool_no, 2),
            total_volume=round(self.total_volume, 2),
            k_constant=round(self.k_constant, 2),
        )
