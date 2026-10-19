"""
K-SWARM: Motor de Ramificação Contrafactual (Timeline Forking)
Permite bifurcar universos sintéticos e comparar linhas do tempo A/B com eventos injetados.
Clean-Room Architecture - Konig Framework 2.0.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel

from .models import (
    SimulationScenario,
    CounterfactualEvent,
    SocialInteractionItem,
    SimulationReport,
)
from .engine import SwarmEngine, SimulationResult
from .graph import EpistemicGraph
from .synthesizer import SwarmSynthesizer


class ForkComparisonResult(BaseModel):
    """Comparativo lado a lado entre a linha de base e a linha com evento injetado."""
    scenario_title: str
    fork_at_round: int
    event_headline: str
    baseline_final_prob: float
    counterfactual_final_prob: float
    probability_divergence: float
    baseline_consensus: float
    counterfactual_consensus: float
    baseline_report: SimulationReport
    counterfactual_report: SimulationReport
    strategic_verdict: str


class TimelineFork:
    """
    Gerenciador de bifurcações e simulações contrafactuais.
    """

    @classmethod
    def execute_fork(
        cls,
        base_scenario: SimulationScenario,
        event: CounterfactualEvent,
        additional_rounds: int = 3,
    ) -> ForkComparisonResult:
        """
        Executa a linha de base e a linha contrafactual em paralelo a partir do ponto de bifurcação.
        """
        # 1. Executa Linha do Tempo Alpha (Baseline)
        graph_alpha = EpistemicGraph(":memory:")
        scenario_alpha = copy.deepcopy(base_scenario)
        scenario_alpha.rounds_count = event.fork_at_round + additional_rounds
        
        engine_alpha = SwarmEngine(scenario=scenario_alpha, graph=graph_alpha)
        result_alpha = engine_alpha.run()
        
        synth_alpha = SwarmSynthesizer(graph=graph_alpha)
        report_alpha = synth_alpha.generate_report(result_alpha)

        # 2. Executa Linha do Tempo Beta (Contrafactual com Injeção)
        graph_beta = EpistemicGraph(":memory:")
        scenario_beta = copy.deepcopy(base_scenario)
        scenario_beta.rounds_count = event.fork_at_round + additional_rounds

        engine_beta = SwarmEngine(scenario=scenario_beta, graph=graph_beta)
        
        # Executa rounds preliminares até o fork
        rounds_beta = []
        for rnd in range(1, event.fork_at_round + 1):
            rounds_beta.append(engine_beta._step_round(rnd))

        # INJEÇÃO DO EVENTO CONTRAFACTUAL (Breaking News)
        injected_item = SocialInteractionItem(
            content_id=f"injected_{event.event_id}",
            author_id="breaking_news_oracle",
            channel_type="microblog",
            content=f"URGENTE: {event.headline} - {event.content}",
            target_topic=event.target_topic,
            expressed_stance=event.impact_magnitude,
            engagement_likes=250,
            engagement_replies=60,
            round_index=event.fork_at_round,
        )

        # Força impacto em todos os agentes
        for agent in engine_beta.agents.values():
            agent.process_interaction(injected_item)

        # Registra no grafo Beta
        graph_beta.record_observation(
            obs_id=injected_item.content_id,
            round_index=event.fork_at_round,
            agent_id=injected_item.author_id,
            topic=injected_item.target_topic,
            stance=injected_item.expressed_stance,
            content=injected_item.content,
        )

        # Continua a execução das rodadas adicionais pós-disrupção
        for rnd in range(event.fork_at_round + 1, scenario_beta.rounds_count + 1):
            rounds_beta.append(engine_beta._step_round(rnd))

        # Consolida resultados Beta
        final_stances_beta = {a_id: dict(agent.stances) for a_id, agent in engine_beta.agents.items()}
        result_beta = SimulationResult(
            scenario_id=f"{scenario_beta.scenario_id}_beta",
            scenario_title=f"{scenario_beta.title} [Pós-Disrupção]",
            total_rounds=scenario_beta.rounds_count,
            rounds=rounds_beta,
            final_stances=final_stances_beta,
            final_market=engine_beta.market.get_snapshot(scenario_beta.rounds_count),
        )

        synth_beta = SwarmSynthesizer(graph=graph_beta)
        report_beta = synth_beta.generate_report(result_beta)

        # 3. Cálculo da Divergência Estratégica
        prob_alpha = report_alpha.market_clearing_price or 0.5
        prob_beta = report_beta.market_clearing_price or 0.5
        divergence = prob_beta - prob_alpha

        if divergence > 0.15:
            verdict = (
                f"IMPACTO FORTEMENTE POSITIVO (+{divergence*100:.1f}%): "
                f"O evento '{event.headline}' alavancou o consenso e a confiança no mercado."
            )
        elif divergence < -0.15:
            verdict = (
                f"IMPACTO SEVERAMENTE NEGATIVO ({divergence*100:.1f}%): "
                f"O evento '{event.headline}' corroeu a credibilidade e colapsou a demanda."
            )
        else:
            verdict = (
                f"IMPACTO NEUTRO OU RESILIENTE ({divergence*100:+.1f}%): "
                "O enxame absorveu a notícia sem alterações estruturais na probabilidade final."
            )

        return ForkComparisonResult(
            scenario_title=base_scenario.title,
            fork_at_round=event.fork_at_round,
            event_headline=event.headline,
            baseline_final_prob=round(prob_alpha, 3),
            counterfactual_final_prob=round(prob_beta, 3),
            probability_divergence=round(divergence, 3),
            baseline_consensus=report_alpha.consensus_score,
            counterfactual_consensus=report_beta.consensus_score,
            baseline_report=report_alpha,
            counterfactual_report=report_beta,
            strategic_verdict=verdict,
        )
