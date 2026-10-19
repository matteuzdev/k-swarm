"""
K-SWARM: Modelos de Dados e Tipagem do Motor
Clean-Room Architecture - Zero Dependências AGPL
"""

from typing import Dict, List, Optional, Set, Literal
from pydantic import BaseModel, Field


class AgentBeliefSnapshot(BaseModel):
    """Snapshot serializável do estado de crença de um agente."""
    agent_id: str
    round_index: int
    stances: Dict[str, float] = Field(
        default_factory=dict,
        description="Mapeamento de tópico para postura [-1.0 (oposição total) a +1.0 (apoio total)]"
    )
    confidences: Dict[str, float] = Field(
        default_factory=dict,
        description="Mapeamento de tópico para certeza [0.1 (volátil) a 1.0 (inabalável)]"
    )
    exposure_count: int = Field(default=0, description="Total de argumentos processados")
    last_delta: Dict[str, float] = Field(default_factory=dict, description="Última variação por tópico")


class SocialInteractionItem(BaseModel):
    """Item de conteúdo gerado ou observado em um canal de texto/rede."""
    content_id: str
    author_id: str
    channel_type: Literal["microblog", "forum", "chat_group", "b2b"]
    content: str
    target_topic: str
    expressed_stance: float = Field(ge=-1.0, le=1.0)
    engagement_likes: int = 0
    engagement_replies: int = 0
    round_index: int = 0


class MarketOrder(BaseModel):
    """Ordem de negociação no formador de mercado preditivo (AMM)."""
    order_id: str
    trader_id: str
    round_index: int
    outcome: Literal["YES", "NO"]
    action: Literal["BUY", "SELL"]
    amount: float = Field(gt=0.0, description="Quantidade de capital alocado na ordem")


class MarketTradeResult(BaseModel):
    """Resultado da execução de uma ordem no AMM."""
    order_id: str
    trader_id: str
    outcome: Literal["YES", "NO"]
    action: Literal["BUY", "SELL"]
    shares_filled: float
    avg_price: float
    new_probability_yes: float
    new_probability_no: float
    price_impact: float


class MarketSnapshot(BaseModel):
    """Estado do mercado preditivo em uma rodada."""
    market_id: str
    round_index: int
    price_yes: float
    price_no: float
    pool_yes: float
    pool_no: float
    total_volume: float
    k_constant: float


class PersonaSeed(BaseModel):
    """Definição estruturada de uma persona sintética no enxame."""
    id: str
    name: str
    archetype: Literal["consumer", "specialist", "executive", "skeptic", "influencer", "trader"]
    initial_sentiment: float = Field(ge=-1.0, le=1.0, default=0.0)
    confidence: float = Field(ge=0.1, le=1.0, default=0.5)
    influence_weight: float = Field(ge=0.0, le=1.0, default=0.5)
    attributes: Dict[str, str] = Field(default_factory=dict)
    grounded_context: str = ""


class ChannelConfig(BaseModel):
    """Configuração de um canal de interação na simulação."""
    channel_type: Literal["microblog", "forum", "chat_group", "prediction_market"]
    enabled: bool = True
    parameters: Dict[str, float] = Field(default_factory=dict)


class SimulationScenario(BaseModel):
    """Cenário completo de simulação K-SWARM."""
    scenario_id: str
    title: str
    core_question: str
    context_text: str
    rounds_count: int = 5
    personas: List[PersonaSeed] = Field(default_factory=list)
    channels: List[ChannelConfig] = Field(default_factory=list)
    market_config: Optional[Dict[str, float]] = None


class CounterfactualEvent(BaseModel):
    """Evento disruptivo injetado para forkar a linha do tempo."""
    event_id: str
    fork_at_round: int
    headline: str
    content: str
    target_topic: str
    impact_magnitude: float = Field(ge=-1.0, le=1.0)


class SimulationReport(BaseModel):
    """Relatório analítico executivo sintetizado a partir do enxame."""
    simulation_id: str
    scenario_title: str
    executive_summary: str
    consensus_score: float
    market_clearing_price: Optional[float] = None
    key_drivers: List[str] = Field(default_factory=list)
    critical_quotes: List[Dict[str, str]] = Field(default_factory=list)
    timeline_drift: List[Dict[str, float]] = Field(default_factory=list)
    strategic_recommendation: str


