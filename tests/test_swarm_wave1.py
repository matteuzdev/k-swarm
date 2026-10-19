"""
K-SWARM: Suíte de Homologação QA - Wave 1
Responsável: Elena (Staff QA & Test Automation)
Valida invariantes matemáticas, estabilidade de limites e velocidade do Sistema 1.
"""

import time
import pytest
from core.swarm import (
    AgentBelief,
    PredictionMarketAMM,
    SocialInteractionItem,
    MarketOrder,
)


def test_belief_state_clamping_and_archetypes():
    """Valida se os limites matemáticos [-1.0, 1.0] e [0.1, 1.0] são respeitados."""
    agent = AgentBelief.from_archetype(
        agent_id="agent_01",
        archetype="cético",
        topics=["ia_regulation", "crypto"],
        sentiment_bias=-0.3,
    )

    snapshot = agent.get_snapshot()
    assert -1.0 <= snapshot.stances["ia_regulation"] <= 1.0
    assert 0.1 <= snapshot.confidences["ia_regulation"] <= 1.0

    # Injeta estímulo extremo
    extreme_item = SocialInteractionItem(
        content_id="post_ext",
        author_id="guru",
        channel_type="microblog",
        content="Regulação é a salvação do universo!",
        target_topic="ia_regulation",
        expressed_stance=1.0,
        engagement_likes=1000,
    )
    
    # Executa múltiplos updates repetidos
    for _ in range(30):
        agent.process_interaction(extreme_item)

    updated_snap = agent.get_snapshot()
    assert -1.0 <= updated_snap.stances["ia_regulation"] <= 1.0
    assert 0.1 <= updated_snap.confidences["ia_regulation"] <= 1.0


def test_cognitive_inertia_high_vs_low_confidence():
    """Garante que agentes com alta convicção resistem mais a mudanças."""
    agent_stubborn = AgentBelief(
        agent_id="stubborn",
        initial_stances={"pricing": 0.0},
        initial_confidences={"pricing": 0.95},  # Inabalável
    )

    agent_receptive = AgentBelief(
        agent_id="receptive",
        initial_stances={"pricing": 0.0},
        initial_confidences={"pricing": 0.15},  # Altamente influenciável
    )

    post = SocialInteractionItem(
        content_id="post_price",
        author_id="authority",
        channel_type="b2b",
        content="Cobrar R$ 799 por site é baratíssimo e converte muito!",
        target_topic="pricing",
        expressed_stance=0.8,
        engagement_likes=10,
    )

    delta_stubborn = agent_stubborn.process_interaction(post)
    delta_receptive = agent_receptive.process_interaction(post)

    assert delta_receptive > delta_stubborn, (
        f"Agente receptivo ({delta_receptive}) deveria ter mudado mais que teimoso ({delta_stubborn})"
    )


def test_novelty_multiplier_decay():
    """Garante que a primeira exposição a um argumento tem maior peso que a repetição."""
    agent = AgentBelief(
        agent_id="learner",
        initial_stances={"feature_x": 0.0},
        initial_confidences={"feature_x": 0.5},
    )

    post = SocialInteractionItem(
        content_id="arg_01",
        author_id="dev",
        channel_type="forum",
        content="Nova arquitetura sem Neo4j reduz latência em 90%",
        target_topic="feature_x",
        expressed_stance=0.9,
    )

    # Primeira visualização (novidade total)
    delta_first = agent.process_interaction(post)

    # Segunda visualização do mesmo conteúdo idêntico
    delta_second = agent.process_interaction(post)

    assert delta_first > delta_second, (
        f"Delta do primeiro impacto ({delta_first}) deve superar o segundo ({delta_second})"
    )


def test_social_proof_amplification():
    """Verifica que conteúdos com maior engajamento geram maior deslocamento de postura."""
    agent_a = AgentBelief(agent_id="a", initial_stances={"t": 0.0}, initial_confidences={"t": 0.5})
    agent_b = AgentBelief(agent_id="b", initial_stances={"t": 0.0}, initial_confidences={"t": 0.5})

    low_engagement = SocialInteractionItem(
        content_id="low",
        author_id="peer",
        channel_type="microblog",
        content="Opinião sem tração",
        target_topic="t",
        expressed_stance=0.7,
        engagement_likes=0,
        engagement_replies=0,
    )

    high_engagement = SocialInteractionItem(
        content_id="high",
        author_id="peer",
        channel_type="microblog",
        content="Opinião viral com tração",
        target_topic="t",
        expressed_stance=0.7,
        engagement_likes=50,
        engagement_replies=10,
    )

    delta_low = agent_a.process_interaction(low_engagement)
    delta_high = agent_b.process_interaction(high_engagement)

    assert delta_high > delta_low


def test_market_amm_initialization_and_parity():
    """Valida paridade e conservação do produto no formador de mercado."""
    market = PredictionMarketAMM(market_id="mkt_test", initial_probability_yes=0.65, base_liquidity=2000.0)

    assert pytest.approx(market.price_yes, 0.01) == 0.65
    assert pytest.approx(market.price_no, 0.01) == 0.35
    assert pytest.approx(market.price_yes + market.price_no, 0.0001) == 1.0


def test_market_amm_price_movement_on_trades():
    """Verifica se compras de YES valorizam YES e compras de NO valorizam NO."""
    market = PredictionMarketAMM(market_id="mkt_vol", initial_probability_yes=0.50, base_liquidity=1000.0)
    p0 = market.price_yes

    # 1. Compra de YES
    buy_yes = MarketOrder(
        order_id="o1",
        trader_id="bull",
        round_index=1,
        outcome="YES",
        action="BUY",
        amount=150.0,
    )
    res_yes = market.execute_order(buy_yes)

    assert market.price_yes > p0, "Compra de YES deve elevar o preço de YES"
    assert res_yes.shares_filled > 0
    assert pytest.approx(market.price_yes + market.price_no, 0.0001) == 1.0

    # 2. Compra pesada de NO revertendo a tendência
    p1 = market.price_yes
    buy_no = MarketOrder(
        order_id="o2",
        trader_id="bear",
        round_index=1,
        outcome="NO",
        action="BUY",
        amount=300.0,
    )
    market.execute_order(buy_no)

    assert market.price_yes < p1, "Compra de NO deve derrubar o preço de YES"
    assert market.price_no > (1.0 - p1)


def test_market_media_bridge_integration():
    """Testa a conversão de postura cognitiva em ordens financeiras de arbitragem."""
    market = PredictionMarketAMM(market_id="mkt_bridge", initial_probability_yes=0.40)

    # Agente muito otimista (+0.80) frente a um mercado precificado a 0.40
    # Espera-se ordem de COMPRA de YES
    res_bull = market.trade_from_sentiment(
        trader_id="trader_alpha",
        topic_stance=0.80,
        confidence=0.85,
        round_index=1,
    )

    assert res_bull is not None
    assert res_bull.outcome == "YES"
    assert res_bull.action == "BUY"
    assert market.price_yes > 0.40

    # Agente alinhado com o mercado atual não negocia (HOLD)
    # Mercado subiu ligeiramente; postura calibrada para a probabilidade atual
    aligned_stance = (market.price_yes * 2.0) - 1.0
    res_hold = market.trade_from_sentiment(
        trader_id="trader_hold",
        topic_stance=aligned_stance,
        confidence=0.5,
        round_index=1,
    )
    assert res_hold is None


def test_system_one_high_frequency_performance():
    """Valida o requisito de alta velocidade do Sistema 1 (1.000 updates + 500 trades em < 100ms)."""
    agent = AgentBelief(agent_id="speed_agent", initial_stances={"bench": 0.0}, initial_confidences={"bench": 0.5})
    market = PredictionMarketAMM(market_id="speed_market", initial_probability_yes=0.5)

    post = SocialInteractionItem(
        content_id="bench_post",
        author_id="bench_author",
        channel_type="microblog",
        content="Micro-benchmark de alta vazão sem LLM",
        target_topic="bench",
        expressed_stance=0.5,
    )

    start = time.perf_counter()

    # 1.000 iterações do vetor de crenças
    for i in range(1000):
        agent.process_interaction(post)

    # 500 trades alternados no mercado
    for i in range(500):
        outcome = "YES" if i % 2 == 0 else "NO"
        market.execute_order(
            MarketOrder(
                order_id=f"o_{i}",
                trader_id="bot",
                round_index=1,
                outcome=outcome,
                action="BUY",
                amount=10.0,
            )
        )

    elapsed_ms = (time.perf_counter() - start) * 1000.0
    print(f"\n[BENCHMARK] 1.000 updates + 500 trades executados em: {elapsed_ms:.2f} ms")

    # Garante que 1.500 operações ocorreram em menos de 100 milissegundos
    assert elapsed_ms < 100.0, f"Tempo excessivo: {elapsed_ms:.2f} ms (limite: 100 ms)"
