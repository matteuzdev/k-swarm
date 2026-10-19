"""
K-SWARM: Suíte de Homologação QA - Wave 4
Responsável: Elena (Staff QA & Test Automation)
Valida sintetizador ReACT, geração de relatórios auditáveis e ramificação contrafactual.
"""

import pytest
from core.swarm import (
    SwarmEngine,
    SimulationScenario,
    PersonaGenerator,
    EpistemicGraph,
    SwarmSynthesizer,
    TimelineFork,
    CounterfactualEvent,
)


def test_swarm_synthesizer_report_generation():
    """Valida síntese executiva e renderização em Markdown."""
    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph)

    personas = generator.generate_personas(
        count=15,
        scenario_context="Software CRM com automação de WhatsApp por R$ 497/mês.",
        target_topics=["valor_percebido"],
        sentiment_anchor=0.4,
    )

    scenario = SimulationScenario(
        scenario_id="sim_synth_test",
        title="CRM WhatsApp Konig",
        core_question="valor_percebido",
        context_text="Testando tração e aceitação do plano mensal.",
        rounds_count=3,
        personas=personas,
        market_config={"initial_probability": 0.50},
    )

    engine = SwarmEngine(scenario=scenario, graph=graph)
    result = engine.run()

    synthesizer = SwarmSynthesizer(graph=graph)
    report = synthesizer.generate_report(result)

    assert report.simulation_id == "sim_synth_test"
    assert report.scenario_title == "CRM WhatsApp Konig"
    assert len(report.executive_summary) > 20
    assert 0.0 <= report.consensus_score <= 1.0
    assert report.market_clearing_price is not None
    assert len(report.key_drivers) > 0
    assert len(report.timeline_drift) == 3

    # Valida exportação em Markdown
    md_output = synthesizer.export_markdown(report)
    assert "# RELATÓRIO EXECUTIVO K-SWARM" in md_output
    assert "DIRETRIZ" in md_output
    assert "Rodada" in md_output

    graph.close()


def test_timeline_forking_counterfactual_event():
    """Valida bifurcação em duas realidades paralelas (Linha A vs Linha B)."""
    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph)

    personas = generator.generate_personas(
        count=15,
        scenario_context="Lançamento de produto inovador.",
        target_topics=["seguranca_dados"],
        sentiment_anchor=0.3,
    )

    base_scenario = SimulationScenario(
        scenario_id="sim_fork_base",
        title="Teste de Resiliência",
        core_question="seguranca_dados",
        context_text="Avaliando reação a incidente de segurança.",
        rounds_count=2,
        personas=personas,
        market_config={"initial_probability": 0.55},
    )

    # Evento negativo grave injetado na rodada 2
    negative_event = CounterfactualEvent(
        event_id="evt_leak",
        fork_at_round=2,
        headline="Falha Crítica de Segurança Expõe Credenciais",
        content="Auditoria externa identifica vazamento em massa de chaves.",
        target_topic="seguranca_dados",
        impact_magnitude=-0.90,
    )

    comparison = TimelineFork.execute_fork(
        base_scenario=base_scenario,
        event=negative_event,
        additional_rounds=2,
    )

    assert comparison.scenario_title == "Teste de Resiliência"
    assert comparison.fork_at_round == 2
    assert comparison.event_headline == negative_event.headline
    assert comparison.baseline_final_prob > 0
    assert comparison.counterfactual_final_prob > 0

    # A linha com evento negativo deve ter probabilidade menor ou divergência calculada
    assert "IMPACTO" in comparison.strategic_verdict
    assert len(comparison.counterfactual_report.executive_summary) > 0

    graph.close()
