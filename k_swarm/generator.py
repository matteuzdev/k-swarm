"""
K-SWARM: Gerador de Personas Aterradas (Grounded Persona Generator)
Gera enxames diversificados conectados ao grafo epistêmico da simulação.
Clean-Room Architecture - Konig Framework 2.0.
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional
from .models import PersonaSeed, SimulationScenario
from .graph import EpistemicGraph


class PersonaGenerator:
    """
    Motor de síntese e aterramento de personas sintéticas.
    Opera tanto em modo heurístico determinístico (offline/sem custos)
    quanto em modo enriquecido com conexões ao grafo de conhecimento.
    """

    ARCHETYPE_DISTRIBUTION = [
        ("consumer", 0.30),
        ("specialist", 0.20),
        ("skeptic", 0.20),
        ("executive", 0.15),
        ("trader", 0.10),
        ("influencer", 0.05),
    ]

    FIRST_NAMES = [
        "Alexandre", "Beatriz", "Carlos", "Daniela", "Eduardo", "Fernanda",
        "Gabriel", "Helena", "Igor", "Juliana", "Leonardo", "Mariana",
        "Nicolas", "Olivia", "Pedro", "Renata", "Samuel", "Tatiana",
        "Vinicius", "Yasmin"
    ]

    LAST_NAMES = [
        "Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima",
        "Ferreira", "Costa", "Rodrigues", "Almeida", "Nascimento", "Ribeiro"
    ]

    def __init__(self, graph: Optional[EpistemicGraph] = None):
        self.graph = graph or EpistemicGraph()

    def generate_personas(
        self,
        count: int = 20,
        scenario_context: str = "",
        target_topics: Optional[List[str]] = None,
        sentiment_anchor: float = 0.0,
    ) -> List[PersonaSeed]:
        """
        Gera uma lista balanceada de personas aterradas com posturas distribuídas.
        """
        topics = target_topics or ["produto_principal", "precificacao", "confiabilidade"]
        personas: List[PersonaSeed] = []

        # Distribuição de arquétipos baseada na contagem desejada
        for i in range(count):
            p_id = f"persona_{i+1:03d}"
            
            # Sorteio determinístico por seed se desejado
            first = self.FIRST_NAMES[i % len(self.FIRST_NAMES)]
            last = self.LAST_NAMES[(i * 3 + 1) % len(self.LAST_NAMES)]
            name = f"{first} {last}"

            # Seleciona arquétipo ciclando ou ponderando
            archetype_name = self._pick_archetype(i, count)
            
            # Calibração de sentimento inicial e confiança pelo arquétipo
            sentiment, conf, influence = self._calibrate_attributes(archetype_name, sentiment_anchor)

            # Extração de contexto de aterramento via subgrafo
            grounded_context = self._extract_grounding(p_id, archetype_name, scenario_context)

            # Atributos sociotécnicos
            attributes = {
                "seniority": "Senior" if archetype_name in ["specialist", "executive"] else "Pleno",
                "risk_profile": "Alto" if archetype_name in ["trader", "influencer"] else "Moderado",
                "focus_topic": topics[i % len(topics)],
            }

            persona = PersonaSeed(
                id=p_id,
                name=name,
                archetype=archetype_name,
                initial_sentiment=round(sentiment, 2),
                confidence=round(conf, 2),
                influence_weight=round(influence, 2),
                attributes=attributes,
                grounded_context=grounded_context,
            )

            # Registra no grafo epistêmico como nó de agente
            self.graph.add_entity(
                entity_id=p_id,
                name=name,
                entity_type=f"agent_{archetype_name}",
                attributes={
                    "initial_sentiment": sentiment,
                    "confidence": conf,
                    "influence": influence,
                },
            )

            personas.append(persona)

        return personas

    def _pick_archetype(self, index: int, total: int) -> str:
        """Seleciona o arquétipo garantindo representatividade proporcional."""
        # Cria uma lista plana ponderada
        expanded = []
        for arch, weight in self.ARCHETYPE_DISTRIBUTION:
            count = max(1, int(round(weight * total)))
            expanded.extend([arch] * count)
        
        if index < len(expanded):
            return expanded[index]
        return "consumer"

    def _calibrate_attributes(self, archetype: str, anchor: float) -> tuple[float, float, float]:
        """Calcula postura inicial, nível de confiança e peso de influência."""
        if archetype == "skeptic":
            sentiment = max(-1.0, min(-0.3, anchor - 0.4 + random.uniform(-0.2, 0.1)))
            confidence = random.uniform(0.65, 0.90)
            influence = random.uniform(0.4, 0.7)
        elif archetype == "enthusiast" or archetype == "influencer":
            sentiment = min(1.0, max(0.4, anchor + 0.5 + random.uniform(-0.1, 0.2)))
            confidence = random.uniform(0.50, 0.75)
            influence = random.uniform(0.7, 0.95)
        elif archetype == "executive":
            sentiment = max(-0.4, min(0.4, anchor + random.uniform(-0.2, 0.2)))
            confidence = random.uniform(0.70, 0.95)
            influence = random.uniform(0.6, 0.85)
        elif archetype == "specialist":
            sentiment = max(-0.5, min(0.5, anchor + random.uniform(-0.3, 0.3)))
            confidence = random.uniform(0.80, 0.98)
            influence = random.uniform(0.5, 0.75)
        elif archetype == "trader":
            sentiment = max(-0.8, min(0.8, anchor + random.uniform(-0.4, 0.4)))
            confidence = random.uniform(0.30, 0.60)
            influence = random.uniform(0.3, 0.5)
        else:  # consumer
            sentiment = max(-0.6, min(0.6, anchor + random.uniform(-0.3, 0.3)))
            confidence = random.uniform(0.35, 0.65)
            influence = random.uniform(0.2, 0.45)

        return sentiment, confidence, influence

    def _extract_grounding(self, agent_id: str, archetype: str, scenario_context: str) -> str:
        """Gera o contexto de aterramento factual da persona."""
        summary_lines = []
        if scenario_context:
            # Pega primeiras 2 linhas significativas do cenário
            lines = [l.strip() for l in scenario_context.split("\n") if l.strip()]
            summary_lines.append(" ".join(lines[:2]))

        summary_lines.append(f"Persona opera como {archetype} avaliando solidez, preço e valor prático.")
        return " | ".join(summary_lines)
