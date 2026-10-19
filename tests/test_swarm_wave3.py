"""
K-SWARM: Suíte de Homologação QA - Wave 3
Responsável: Elena (Staff QA & Test Automation)
Valida execução E2E do enxame multi-canal, orquestração de rodadas e velocidade global.
"""

import time
import pytest
from k_swarm import (
    SwarmEngine,
    SimulationScenario,
    PersonaGenerator,
    EpistemicGraph,
    MicroblogChannel,
    ForumChannel,
    ChatGroupChannel,
)


def test_channels_content_generation():
    """Valida geração correta de itens em cada canal."""
    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph)
    personas = generator.generate_personas(count=10)

    stances = {p.id: {"vendas": 0.5} for p in personas}

    mb = MicroblogChannel()
    mb_items = mb.generate_interactions(personas, stances, ["vendas"], 1)
    assert len(mb_items) > 0
    assert all(i.channel_type == "microblog" for i in mb_items)

    frm = ForumChannel()
    frm_items = frm.generate_interactions(personas, stances, ["vendas"], 1)
    assert len(frm_items) > 0
    assert all(i.channel_type == "forum" for i in frm_items)

    chat = ChatGroupChannel()
    chat_items = chat.generate_interactions(personas, stances, ["vendas"], 1)
    assert len(chat_items) > 0
    assert all(i.channel_type == "chat_group" for i in chat_items)

    graph.close()


def test_swarm_simulation_end_to_end():
    """Valida uma simulação completa de 5 rodadas com 20 personas e mercado ativo."""
    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph)

    personas = generator.generate_personas(
        count=20,
        scenario_context="Lançamento do bot de agenda por R$ 799 com garantia de 7 dias.",
        target_topics=["conversao_vendas"],
        sentiment_anchor=0.2,
    )

    scenario = SimulationScenario(
        scenario_id="sim_launch_799",
        title="Lançamento Comercial Bot de Agenda",
        core_question="conversao_vendas",
        context_text="Meta de fechar 20 clientes a R$ 799 no mercado local.",
        rounds_count=5,
        personas=personas,
        market_config={"initial_probability": 0.45},
    )

    engine = SwarmEngine(scenario=scenario, graph=graph)
    
    start_time = time.perf_counter()
    result = engine.run()
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    print(f"\n[BENCHMARK] Simulação E2E (20 agentes x 5 rounds x 3 canais): {elapsed_ms:.2f} ms")

    assert result.total_rounds == 5
    assert len(result.rounds) == 5

    # Valida métricas por rodada
    for round_summary in result.rounds:
        assert "conversao_vendas" in round_summary.mean_sentiment
        assert -1.0 <= round_summary.mean_sentiment["conversao_vendas"] <= 1.0
        assert 0.0 <= round_summary.consensus_score <= 1.0
        assert round_summary.total_interactions > 0
        assert round_summary.market_snapshot is not None

    # Valida que o mercado preditivo teve movimentação
    assert result.final_market is not None
    assert 0.01 <= result.final_market.price_yes <= 0.99

    # Garante que as observações foram registradas no grafo
    obs_count = graph.conn.execute("SELECT COUNT(*) FROM observations;").fetchone()[0]
    assert obs_count > 0

    # Teste de performance: 5 rodadas completas em menos de 250 ms
    assert elapsed_ms < 250.0, f"Simulação demorou mais que o limite: {elapsed_ms:.2f} ms"

    graph.close()
