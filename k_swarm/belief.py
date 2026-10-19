"""
K-SWARM: Motor de Dinâmica de Crenças (K-Belief State)
Sistema 1: Execução determinística de alta frequência, zero token por tick.
Clean-Room Architecture - Zero Dependências AGPL.
"""

from __future__ import annotations

import hashlib
from collections import deque
from typing import Dict, List, Optional, Set
from .models import AgentBeliefSnapshot, SocialInteractionItem


class AgentBelief:
    """
    Controlador de crenças, confiança e inércia cognitiva de um agente.
    Opera como um motor vetorial determinístico de alta velocidade.
    """

    MAX_SEEN_HISTORY: int = 1000
    BASE_LEARNING_RATE: float = 0.08

    def __init__(
        self,
        agent_id: str,
        initial_stances: Optional[Dict[str, float]] = None,
        initial_confidences: Optional[Dict[str, float]] = None,
        trust_network: Optional[Dict[str, float]] = None,
    ):
        self.agent_id = agent_id
        self.stances: Dict[str, float] = {}
        self.confidences: Dict[str, float] = {}
        self.trust_network: Dict[str, float] = trust_network or {}
        self.seen_hashes: Set[str] = set()
        self.history_queue: deque = deque(maxlen=self.MAX_SEEN_HISTORY)
        self.exposure_count: int = 0
        self.last_round_deltas: Dict[str, float] = {}

        # Inicializa posturas garantindo limites [-1.0, +1.0]
        if initial_stances:
            for topic, val in initial_stances.items():
                self.stances[topic] = max(-1.0, min(1.0, float(val)))

        # Inicializa níveis de confiança garantindo limites [0.1, 1.0]
        if initial_confidences:
            for topic, val in initial_confidences.items():
                self.confidences[topic] = max(0.1, min(1.0, float(val)))

    @classmethod
    def from_archetype(
        cls,
        agent_id: str,
        archetype: str,
        topics: List[str],
        sentiment_bias: float = 0.0,
        confidence_base: float = 0.5,
    ) -> AgentBelief:
        """
        Gera um perfil de crença calibrado com base em arquétipos comportamentais.
        """
        archetype_lower = archetype.lower().strip()
        
        # Mapeamento base por arquétipo
        archetype_presets = {
            "cético": {"stance": -0.5, "conf": 0.7},
            "skeptic": {"stance": -0.5, "conf": 0.7},
            "entusiasta": {"stance": 0.7, "conf": 0.6},
            "enthusiast": {"stance": 0.7, "conf": 0.6},
            "institucional": {"stance": 0.0, "conf": 0.9},
            "institutional": {"stance": 0.0, "conf": 0.9},
            "influencer": {"stance": 0.4, "conf": 0.5},
            "trader": {"stance": 0.1, "conf": 0.4},
            "neutro": {"stance": 0.0, "conf": 0.3},
            "neutral": {"stance": 0.0, "conf": 0.3},
        }

        preset = archetype_presets.get(archetype_lower, {"stance": 0.0, "conf": confidence_base})
        base_stance = max(-1.0, min(1.0, preset["stance"] + sentiment_bias))
        base_conf = max(0.1, min(1.0, preset["conf"]))

        stances = {t: base_stance for t in topics}
        confidences = {t: base_conf for t in topics}

        return cls(
            agent_id=agent_id,
            initial_stances=stances,
            initial_confidences=confidences,
        )

    def process_interaction(self, item: SocialInteractionItem) -> float:
        """
        Atualiza o vetor de crença frente a um estímulo de conteúdo observado.
        Retorna o delta aplicado ao tópico alvo.
        """
        topic = item.target_topic
        if topic not in self.stances:
            # Novo tópico descoberto: inicializa com confiança moderada
            self.stances[topic] = 0.0
            self.confidences[topic] = 0.4

        # 1. Deduplicação semântica por hash do conteúdo
        content_hash = hashlib.sha256(item.content.strip().encode("utf-8")).hexdigest()[:16]
        is_novel = content_hash not in self.seen_hashes
        
        if is_novel:
            if len(self.history_queue) >= self.MAX_SEEN_HISTORY:
                evicted = self.history_queue.popleft()
                self.seen_hashes.discard(evicted)
            self.history_queue.append(content_hash)
            self.seen_hashes.add(content_hash)

        # 2. Fatores de Modulação Heurística
        author_trust = self.trust_network.get(item.author_id, 0.5)
        
        # Prova social: likes e replies pesam na credibilidade percebida
        social_weight = min(1.0, 0.3 + (item.engagement_likes * 0.04) + (item.engagement_replies * 0.08))
        
        # Multiplicador de novidade: argumento novo tem impacto maior
        novelty_mult = 1.5 if is_novel else 0.4

        # Inércia cognitiva: agentes com alta certeza resistem a mudanças
        current_stance = self.stances[topic]
        current_conf = self.confidences[topic]
        resistance = 0.3 + (0.7 * current_conf)

        # 3. Cálculo do Delta de Opinião
        directional_gap = item.expressed_stance - current_stance
        delta = (
            directional_gap
            * author_trust
            * social_weight
            * novelty_mult
            * self.BASE_LEARNING_RATE
        ) / resistance

        # 4. Aplicação e Clamp
        new_stance = max(-1.0, min(1.0, current_stance + delta))
        self.stances[topic] = new_stance
        self.exposure_count += 1
        self.last_round_deltas[topic] = delta

        # 5. Ajuste Dinâmico de Confiança
        # Se o post reforça a opinião já mantida, a confiança do agente sobe ligeiramente
        if (delta >= 0 and current_stance > 0) or (delta <= 0 and current_stance < 0):
            reinforcement = 0.02 * social_weight
            self.confidences[topic] = min(1.0, current_conf + reinforcement)
        else:
            # Contradição enfraquece levemente a certeza
            erosion = 0.01 * novelty_mult
            self.confidences[topic] = max(0.1, current_conf - erosion)

        return delta

    def batch_process_round(self, items: List[SocialInteractionItem]) -> Dict[str, float]:
        """Processa todos os itens de uma rodada e retorna os deltas consolidados."""
        round_deltas: Dict[str, float] = {}
        for item in items:
            delta = self.process_interaction(item)
            topic = item.target_topic
            round_deltas[topic] = round_deltas.get(topic, 0.0) + delta
        return round_deltas

    def set_author_trust(self, author_id: str, trust_score: float) -> None:
        """Define o nível de confiança atribuído a outro autor [0.0 a 1.0]."""
        self.trust_network[author_id] = max(0.0, min(1.0, float(trust_score)))

    def get_snapshot(self, round_index: int = 0) -> AgentBeliefSnapshot:
        """Exporta o estado atual em formato estruturado auditável."""
        return AgentBeliefSnapshot(
            agent_id=self.agent_id,
            round_index=round_index,
            stances=dict(self.stances),
            confidences=dict(self.confidences),
            exposure_count=self.exposure_count,
            last_delta=dict(self.last_round_deltas),
        )
