"""
K-SWARM: Motor Orquestrador do Enxame (Swarm Engine)
Executa a simulação multi-canal, orquestra crenças, mercado e persistência.
Clean-Room Architecture - Konig Framework 2.0.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .models import (
    PersonaSeed,
    SimulationScenario,
    SocialInteractionItem,
    MarketSnapshot,
    MarketTradeResult,
    AgentBeliefSnapshot,
)
from .belief import AgentBelief
from .market import PredictionMarketAMM
from .graph import EpistemicGraph
from .channels import BaseChannel, MicroblogChannel, ForumChannel, ChatGroupChannel


class RoundSummary(BaseModel):
    """Resumo estatístico consolidado de uma rodada."""
    round_index: int
    mean_sentiment: Dict[str, float]
    consensus_score: float  # 0.0 (máxima polarização) a 1.0 (unanimidade total)
    total_interactions: int
    market_snapshot: Optional[MarketSnapshot] = None
    trades_executed: List[MarketTradeResult] = Field(default_factory=list)


class SimulationResult(BaseModel):
    """Registro completo de saída de uma simulação K-SWARM."""
    scenario_id: str
    scenario_title: str
    total_rounds: int
    rounds: List[RoundSummary]
    final_stances: Dict[str, Dict[str, float]]
    final_market: Optional[MarketSnapshot] = None
    all_interactions: List[SocialInteractionItem] = Field(default_factory=list)


class SwarmEngine:
    """
    Motor central que orquestra as interações entre personas, canais e mercado preditivo.
    """

    def __init__(
        self,
        scenario: SimulationScenario,
        graph: Optional[EpistemicGraph] = None,
    ):
        self.scenario = scenario
        self.graph = graph or EpistemicGraph()
        self.topics = [scenario.core_question] if scenario.core_question else ["geral"]
        
        # 1. Instancia crenças dos agentes
        self.agents: Dict[str, AgentBelief] = {}
        for p in self.scenario.personas:
            self.agents[p.id] = AgentBelief.from_archetype(
                agent_id=p.id,
                archetype=p.archetype,
                topics=self.topics,
                sentiment_bias=p.initial_sentiment,
                confidence_base=p.confidence,
            )

        # 2. Instancia formador de mercado se configurado
        initial_p = 0.5
        if self.scenario.market_config and "initial_probability" in self.scenario.market_config:
            initial_p = self.scenario.market_config["initial_probability"]

        self.market = PredictionMarketAMM(
            market_id=f"mkt_{scenario.scenario_id}",
            initial_probability_yes=initial_p,
            base_liquidity=1500.0,
        )

        # 3. Instancia canais configurados
        self.channels: List[BaseChannel] = [
            MicroblogChannel(f"mb_{scenario.scenario_id}"),
            ForumChannel(f"frm_{scenario.scenario_id}"),
            ChatGroupChannel(f"chat_{scenario.scenario_id}"),
        ]

    def run(self) -> SimulationResult:
        """
        Executa todas as rodadas da simulação sequencialmente de forma síncrona/rápida.
        """
        rounds_history: List[RoundSummary] = []
        all_interactions: List[SocialInteractionItem] = []

        for round_idx in range(1, self.scenario.rounds_count + 1):
            round_summary = self._step_round(round_idx)
            rounds_history.append(round_summary)
            all_interactions.extend(self.channels[0].history[-round_summary.total_interactions:])

        # Consolida posturas finais
        final_stances = {
            a_id: dict(agent.stances) for a_id, agent in self.agents.items()
        }

        return SimulationResult(
            scenario_id=self.scenario.scenario_id,
            scenario_title=self.scenario.title,
            total_rounds=self.scenario.rounds_count,
            rounds=rounds_history,
            final_stances=final_stances,
            final_market=self.market.get_snapshot(self.scenario.rounds_count),
            all_interactions=all_interactions,
        )

    def _step_round(self, round_index: int) -> RoundSummary:
        """Executa um ciclo completo de rodada do enxame."""
        # A. Mapeia posturas correntes
        current_stances: Dict[str, Dict[str, float]] = {
            a_id: dict(agent.stances) for a_id, agent in self.agents.items()
        }

        # B. Gera interações em todos os canais
        round_items: List[SocialInteractionItem] = []
        for channel in self.channels:
            items = channel.generate_interactions(
                personas=self.scenario.personas,
                agent_stances=current_stances,
                target_topics=self.topics,
                round_index=round_index,
            )
            round_items.extend(items)

        # C. Registra interações no grafo epistêmico
        for item in round_items:
            self.graph.record_observation(
                obs_id=item.content_id,
                round_index=round_index,
                agent_id=item.author_id,
                topic=item.target_topic,
                stance=item.expressed_stance,
                content=item.content,
            )

        # D. Atualização do Vetor de Crenças de cada agente com o que foi visto
        for agent in self.agents.values():
            agent.batch_process_round(round_items)

        # E. Ponte Mercado-Mídia: Agentes 'trader' operam no AMM
        round_trades: List[MarketTradeResult] = []
        for p in self.scenario.personas:
            if p.archetype == "trader":
                agent = self.agents[p.id]
                topic_stance = agent.stances.get(self.topics[0], 0.0)
                conf = agent.confidences.get(self.topics[0], 0.5)

                trade = self.market.trade_from_sentiment(
                    trader_id=p.id,
                    topic_stance=topic_stance,
                    confidence=conf,
                    round_index=round_index,
                    max_capital=120.0,
                )
                if trade:
                    round_trades.append(trade)

        # F. Cálculo de Métricas Agregadas
        mean_sentiment: Dict[str, float] = {}
        for topic in self.topics:
            scores = [agent.stances.get(topic, 0.0) for agent in self.agents.values()]
            avg = sum(scores) / len(scores) if scores else 0.0
            mean_sentiment[topic] = round(avg, 3)

        # Consenso: 1.0 - desvio absoluto médio (quanto menor o desvio, mais unânime)
        scores_main = [agent.stances.get(self.topics[0], 0.0) for agent in self.agents.values()]
        avg_main = mean_sentiment.get(self.topics[0], 0.0)
        mad = sum(abs(s - avg_main) for s in scores_main) / len(scores_main) if scores_main else 0.0
        consensus = round(max(0.0, min(1.0, 1.0 - (mad / 1.5))), 3)

        return RoundSummary(
            round_index=round_index,
            mean_sentiment=mean_sentiment,
            consensus_score=consensus,
            total_interactions=len(round_items),
            market_snapshot=self.market.get_snapshot(round_index),
            trades_executed=round_trades,
        )
