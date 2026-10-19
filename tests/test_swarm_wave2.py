"""
K-SWARM: Suíte de Homologação QA - Wave 2
Responsável: Elena (Staff QA & Test Automation)
Valida grafo epistêmico embarcado, travessia BFS, validade temporal e gerador de personas.
"""

import pytest
from core.swarm import (
    EpistemicGraph,
    PersonaGenerator,
    PersonaSeed,
)


def test_epistemic_graph_entity_crud():
    """Valida inserção, busca e recuperação de nós no grafo."""
    graph = EpistemicGraph(":memory:")

    graph.add_entity(
        entity_id="prod_01",
        name="Plataforma Konig Swarm",
        entity_type="SoftwareProduct",
        attributes={"price": 799.0, "category": "AI Sim"},
    )

    entity = graph.get_entity("prod_01")
    assert entity is not None
    assert entity["name"] == "Plataforma Konig Swarm"
    assert entity["attributes"]["price"] == 799.0

    # Busca parcial
    results = graph.search_entities("Konig")
    assert len(results) == 1
    assert results[0]["id"] == "prod_01"

    graph.close()


def test_epistemic_graph_bfs_traversal():
    """Valida travessia em largura (k-hops) conectando entidades."""
    graph = EpistemicGraph(":memory:")

    # Cria cadeia: Empresa -> Produto -> Feature -> Benchmark
    graph.add_entity("org_konig", "Konig Imperio", "Organization")
    graph.add_entity("prod_swarm", "K-SWARM", "Product")
    graph.add_entity("feat_amm", "K-AMM", "Feature")
    graph.add_entity("bench_speed", "21ms Latency", "Metric")

    graph.add_relation("rel_1", "org_konig", "prod_swarm", "OWNS")
    graph.add_relation("rel_2", "prod_swarm", "feat_amm", "HAS_FEATURE")
    graph.add_relation("rel_3", "feat_amm", "bench_speed", "ACHIEVES")

    # Hop 1 a partir da organização: deve ver apenas [Konig, K-SWARM]
    subgraph_1 = graph.traverse_subgraph("org_konig", max_hops=1)
    node_ids_1 = {n["id"] for n in subgraph_1["nodes"]}
    assert node_ids_1 == {"org_konig", "prod_swarm"}
    assert len(subgraph_1["edges"]) == 1

    # Hop 3 a partir da organização: deve ver toda a cadeia até a métrica
    subgraph_3 = graph.traverse_subgraph("org_konig", max_hops=3)
    node_ids_3 = {n["id"] for n in subgraph_3["nodes"]}
    assert node_ids_3 == {"org_konig", "prod_swarm", "feat_amm", "bench_speed"}
    assert len(subgraph_3["edges"]) == 3

    graph.close()


def test_epistemic_graph_temporal_invalidation():
    """Valida resolução de contradições e consultas no passado (as-of temporal)."""
    graph = EpistemicGraph(":memory:")

    graph.add_entity("person_ceo", "Fundador X", "Person")
    graph.add_entity("comp_y", "Empresa Y", "Company")

    # No round 0, CEO é diretor da Empresa Y
    graph.add_relation("rel_role", "person_ceo", "comp_y", "CEO_OF", valid_from_round=0)

    # Consulta no round 1: a relação é ativa
    state_r1 = graph.traverse_subgraph("person_ceo", max_hops=1, as_of_round=1)
    assert len(state_r1["edges"]) == 1

    # No round 2, ele é destituído (invalidação)
    updated = graph.invalidate_relation("person_ceo", "comp_y", "CEO_OF", invalidated_at_round=2)
    assert updated == 1

    # Consulta retrospectiva no round 1 (como o mundo era antes da demissão): ativa!
    state_retro = graph.traverse_subgraph("person_ceo", max_hops=1, as_of_round=1)
    assert len(state_retro["edges"]) == 1

    # Consulta no round 3 (após a destituição): aresta expulsa do subgrafo temporal
    state_r3 = graph.traverse_subgraph("person_ceo", max_hops=1, as_of_round=3)
    assert len(state_r3["edges"]) == 0

    graph.close()


def test_persona_generator_diversity_and_grounding():
    """Valida geração de personas com representatividade equilibrada e ancoragem no grafo."""
    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph=graph)

    scenario_text = (
        "Lançamento do software de vendas por R$ 799.\n"
        "Promessa de entrega de sites em 48h sem custos ocultos."
    )

    personas = generator.generate_personas(
        count=25,
        scenario_context=scenario_text,
        target_topics=["preco", "prazo_entrega", "suporte"],
        sentiment_anchor=0.1,
    )

    assert len(personas) == 25

    # Garante que múltiplos arquétipos foram instanciados
    archetypes = {p.archetype for p in personas}
    assert "skeptic" in archetypes
    assert "consumer" in archetypes
    assert "specialist" in archetypes
    assert "executive" in archetypes
    assert "trader" in archetypes

    # Garante que cada persona foi registrada no grafo epistêmico
    for p in personas:
        assert -1.0 <= p.initial_sentiment <= 1.0
        assert 0.1 <= p.confidence <= 1.0
        assert "799" in p.grounded_context or "opera como" in p.grounded_context
        
        node = graph.get_entity(p.id)
        assert node is not None
        assert node["name"] == p.name

    graph.close()
