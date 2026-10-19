"""
K-SWARM: Adaptadores de Canais Omnichannel (K-Channels)
Clean-Room Architecture - Konig Framework 2.0.
"""

from __future__ import annotations

import abc
import random
from typing import Any, Dict, List, Optional
from .models import SocialInteractionItem, PersonaSeed


class BaseChannel(abc.ABC):
    """Contrato base universal para qualquer canal de interação no enxame."""

    def __init__(self, channel_id: str, channel_type: str):
        self.channel_id = channel_id
        self.channel_type = channel_type
        self.history: List[SocialInteractionItem] = []

    @abc.abstractmethod
    def generate_interactions(
        self,
        personas: List[PersonaSeed],
        agent_stances: Dict[str, Dict[str, float]],
        target_topics: List[str],
        round_index: int,
    ) -> List[SocialInteractionItem]:
        """Gera as postagens, comentários ou mensagens da rodada."""
        pass


class MicroblogChannel(BaseChannel):
    """Canal estilo Twitter/X: postagens curtas, retweets e viralidade."""

    def __init__(self, channel_id: str = "microblog_01"):
        super().__init__(channel_id, "microblog")

    def generate_interactions(
        self,
        personas: List[PersonaSeed],
        agent_stances: Dict[str, Dict[str, float]],
        target_topics: List[str],
        round_index: int,
    ) -> List[SocialInteractionItem]:
        items: List[SocialInteractionItem] = []
        
        # Amostra um subconjunto de personas ativas na rodada (ex: 60%)
        active_count = max(2, int(len(personas) * 0.6))
        active_personas = random.sample(personas, active_count)

        for p in active_personas:
            topic = p.attributes.get("focus_topic", target_topics[0])
            stance = agent_stances.get(p.id, {}).get(topic, p.initial_sentiment)

            # Gera texto representativo baseado no arquétipo e postura
            content = self._craft_post(p.name, p.archetype, topic, stance, round_index)

            # Engajamento amplificado para influencers
            base_likes = 5 if p.archetype != "influencer" else 50
            likes = int(base_likes * p.influence_weight * random.uniform(0.8, 2.5))
            replies = int(likes * 0.25)

            item = SocialInteractionItem(
                content_id=f"mb_{round_index}_{p.id}_{topic[:4]}",
                author_id=p.id,
                channel_type="microblog",
                content=content,
                target_topic=topic,
                expressed_stance=stance,
                engagement_likes=likes,
                engagement_replies=replies,
                round_index=round_index,
            )
            items.append(item)
            self.history.append(item)

        return items

    def _craft_post(self, name: str, archetype: str, topic: str, stance: float, rnd: int) -> str:
        polarity = "apoia fortemente" if stance > 0.3 else ("rejeita com vigor" if stance < -0.3 else "avalia com cautela")
        return f"[{name} - R{rnd}]: Analisando o tópico #{topic}. Minha posição é que o mercado {polarity} este modelo."


class ForumChannel(BaseChannel):
    """Canal estilo Reddit / Fórum B2B: debates mais longos com viés analítico."""

    def __init__(self, channel_id: str = "forum_b2b_01"):
        super().__init__(channel_id, "forum")

    def generate_interactions(
        self,
        personas: List[PersonaSeed],
        agent_stances: Dict[str, Dict[str, float]],
        target_topics: List[str],
        round_index: int,
    ) -> List[SocialInteractionItem]:
        items: List[SocialInteractionItem] = []

        # No fórum, especialistas e executivos têm maior frequência de postagem
        for p in personas:
            if p.archetype in ["specialist", "executive", "skeptic"] or random.random() < 0.35:
                topic = p.attributes.get("focus_topic", target_topics[0])
                stance = agent_stances.get(p.id, {}).get(topic, p.initial_sentiment)
                
                content = (
                    f"Thread detalhada por {p.name} ({p.archetype}) sobre {topic}: "
                    f"A evidência técnica e econômica indica que a tese se sustenta com score {stance:+.2f}."
                )

                item = SocialInteractionItem(
                    content_id=f"frm_{round_index}_{p.id}",
                    author_id=p.id,
                    channel_type="forum",
                    content=content,
                    target_topic=topic,
                    expressed_stance=stance,
                    engagement_likes=int(random.uniform(2, 25)),
                    engagement_replies=int(random.uniform(1, 10)),
                    round_index=round_index,
                )
                items.append(item)
                self.history.append(item)

        return items


class ChatGroupChannel(BaseChannel):
    """Canal estilo WhatsApp / Telegram: mensagens ágeis em grupos restritos."""

    def __init__(self, channel_id: str = "whatsapp_group_01"):
        super().__init__(channel_id, "chat_group")

    def generate_interactions(
        self,
        personas: List[PersonaSeed],
        agent_stances: Dict[str, Dict[str, float]],
        target_topics: List[str],
        round_index: int,
    ) -> List[SocialInteractionItem]:
        items: List[SocialInteractionItem] = []

        # Mensagens curtas em grupo
        active_sample = random.sample(personas, min(5, len(personas)))
        for p in active_sample:
            topic = target_topics[0]
            stance = agent_stances.get(p.id, {}).get(topic, p.initial_sentiment)

            msg = f"Fala pessoal, sobre {topic}: {'fecho totalmente' if stance > 0 else 'achei furada'}."

            item = SocialInteractionItem(
                content_id=f"chat_{round_index}_{p.id}",
                author_id=p.id,
                channel_type="chat_group",
                content=msg,
                target_topic=topic,
                expressed_stance=stance,
                engagement_likes=random.randint(0, 8),
                engagement_replies=random.randint(0, 4),
                round_index=round_index,
            )
            items.append(item)
            self.history.append(item)

        return items
