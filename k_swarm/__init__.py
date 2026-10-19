"""
K-SWARM: Pacote Central do Motor de Simulação Social & Predição
Clean-Room Architecture - Konig Framework 2.0
"""

from .models import (
    AgentBeliefSnapshot,
    SocialInteractionItem,
    MarketOrder,
    MarketTradeResult,
    MarketSnapshot,
    PersonaSeed,
    ChannelConfig,
    SimulationScenario,
    CounterfactualEvent,
    SimulationReport,
)
from .belief import AgentBelief
from .market import PredictionMarketAMM
from .graph import EpistemicGraph
from .generator import PersonaGenerator
from .channels import BaseChannel, MicroblogChannel, ForumChannel, ChatGroupChannel
from .engine import SwarmEngine, SimulationResult, RoundSummary
from .synthesizer import SwarmSynthesizer
from .fork import TimelineFork, ForkComparisonResult

__all__ = [
    "AgentBeliefSnapshot",
    "SocialInteractionItem",
    "MarketOrder",
    "MarketTradeResult",
    "MarketSnapshot",
    "PersonaSeed",
    "ChannelConfig",
    "SimulationScenario",
    "CounterfactualEvent",
    "SimulationReport",
    "AgentBelief",
    "PredictionMarketAMM",
    "EpistemicGraph",
    "PersonaGenerator",
    "BaseChannel",
    "MicroblogChannel",
    "ForumChannel",
    "ChatGroupChannel",
    "SwarmEngine",
    "SimulationResult",
    "RoundSummary",
    "SwarmSynthesizer",
    "TimelineFork",
    "ForkComparisonResult",
]
