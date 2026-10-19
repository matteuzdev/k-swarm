"""
K-SWARM: Servidor MCP Nativo (Model Context Protocol)
Expõe o motor de simulação social e predição de mercado para IDEs e agentes de IA
via protocolo JSON-RPC 2.0 padrão sobre stdio.
Clean-Room Architecture - Konig Framework 2.0.
"""

from __future__ import annotations

import sys
import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from .models import SimulationScenario, CounterfactualEvent
    from .graph import EpistemicGraph
    from .generator import PersonaGenerator
    from .engine import SwarmEngine
    from .synthesizer import SwarmSynthesizer
    from .fork import TimelineFork
except ImportError:
    from k_swarm.models import SimulationScenario, CounterfactualEvent
    from k_swarm.graph import EpistemicGraph
    from k_swarm.generator import PersonaGenerator
    from k_swarm.engine import SwarmEngine
    from k_swarm.synthesizer import SwarmSynthesizer
    from k_swarm.fork import TimelineFork

# Configuração de log para stderr (nunca poluir stdout que é reservado para JSON-RPC)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[K-SWARM-MCP] %(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("k_swarm_mcp")


TOOLS_MANIFEST = [
    {
        "name": "k_swarm_simulate",
        "description": (
            "Executa uma simulação social multi-agente e predição de mercado preditivo (AMM) em tempo acelerado. "
            "Retorna probabilidade de sucesso (0 a 100%), índice de consenso, citações auditadas no grafo "
            "e diretrizes estratégicas para validar ofertas, copies ou produtos antes de investir."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "Descrição detalhada do produto, oferta, briefing ou tese comercial a ser simulada.",
                },
                "topic": {
                    "type": "string",
                    "description": "Tópico central a ser avaliado pelo enxame (ex: 'conversao_vendas', 'aceitacao_preco', 'confiabilidade').",
                    "default": "viabilidade_comercial",
                },
                "rounds": {
                    "type": "integer",
                    "description": "Quantidade de rodadas de interação social (padrão: 5, range: 1-15).",
                    "default": 5,
                },
                "personas": {
                    "type": "integer",
                    "description": "Quantidade de personas sintéticas distribuídas em arquétipos (padrão: 25, range: 5-50).",
                    "default": 25,
                },
                "anchor": {
                    "type": "number",
                    "description": "Âncora de sentimento inicial [-1.0 (muito cético) a +1.0 (muito otimista)].",
                    "default": 0.0,
                },
                "initial_probability": {
                    "type": "number",
                    "description": "Probabilidade inicial no formador de mercado preditivo AMM [0.05 a 0.95].",
                    "default": 0.50,
                },
            },
            "required": ["scenario"],
        },
    },
    {
        "name": "k_swarm_fork",
        "description": (
            "Executa uma ramificação contrafactual ('E se...?'). Clona a simulação e injeta um evento disruptivo "
            "(ex: vazamento, ataque de concorrente, mudança de preço, nova garantia) para comparar as duas realidades lado a lado."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "Descrição do cenário base da oferta ou negócio.",
                },
                "topic": {
                    "type": "string",
                    "description": "Tópico focal da simulação.",
                },
                "event_headline": {
                    "type": "string",
                    "description": "Manchete ou título da notícia/evento disruptivo injetado.",
                },
                "event_content": {
                    "type": "string",
                    "description": "Detalhes explicativos da disrupção.",
                },
                "impact_magnitude": {
                    "type": "number",
                    "description": "Magnitude e polaridade do impacto [-1.0 (catastrófico) a +1.0 (revolucionário)].",
                },
                "fork_at_round": {
                    "type": "integer",
                    "description": "Rodada em que a linha do tempo se divide (padrão: 2).",
                    "default": 2,
                },
            },
            "required": ["scenario", "topic", "event_headline", "event_content", "impact_magnitude"],
        },
    },
]


def handle_simulate(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Processa a tool k_swarm_simulate."""
    scenario_text = arguments.get("scenario", "")
    topic = arguments.get("topic", "viabilidade_comercial")
    rounds = int(arguments.get("rounds", 5))
    personas_count = int(arguments.get("personas", 25))
    anchor = float(arguments.get("anchor", 0.0))
    initial_p = float(arguments.get("initial_probability", 0.50))

    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph)

    personas = generator.generate_personas(
        count=personas_count,
        scenario_context=scenario_text,
        target_topics=[topic],
        sentiment_anchor=anchor,
    )

    scenario = SimulationScenario(
        scenario_id="mcp_run",
        title=scenario_text[:60],
        core_question=topic,
        context_text=scenario_text,
        rounds_count=rounds,
        personas=personas,
        market_config={"initial_probability": initial_p},
    )

    engine = SwarmEngine(scenario=scenario, graph=graph)
    result = engine.run()

    synthesizer = SwarmSynthesizer(graph=graph)
    report = synthesizer.generate_report(result)
    markdown_report = synthesizer.export_markdown(report)

    graph.close()

    return {
        "report_summary": report.executive_summary,
        "market_probability_yes": report.market_clearing_price,
        "consensus_score": report.consensus_score,
        "strategic_recommendation": report.strategic_recommendation,
        "key_drivers": report.key_drivers,
        "critical_quotes": report.critical_quotes,
        "full_markdown": markdown_report,
    }


def handle_fork(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Processa a tool k_swarm_fork."""
    scenario_text = arguments.get("scenario", "")
    topic = arguments.get("topic", "viabilidade_comercial")
    event_headline = arguments.get("event_headline", "")
    event_content = arguments.get("event_content", "")
    impact_magnitude = float(arguments.get("impact_magnitude", 0.0))
    fork_at_round = int(arguments.get("fork_at_round", 2))

    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph)

    personas = generator.generate_personas(
        count=20,
        scenario_context=scenario_text,
        target_topics=[topic],
        sentiment_anchor=0.0,
    )

    base_scenario = SimulationScenario(
        scenario_id="mcp_fork_base",
        title=scenario_text[:60],
        core_question=topic,
        context_text=scenario_text,
        rounds_count=fork_at_round,
        personas=personas,
        market_config={"initial_probability": 0.50},
    )

    event = CounterfactualEvent(
        event_id="mcp_evt",
        fork_at_round=fork_at_round,
        headline=event_headline,
        content=event_content,
        target_topic=topic,
        impact_magnitude=impact_magnitude,
    )

    comparison = TimelineFork.execute_fork(
        base_scenario=base_scenario,
        event=event,
        additional_rounds=3,
    )

    graph.close()

    return {
        "scenario_title": comparison.scenario_title,
        "event_injected": comparison.event_headline,
        "baseline_probability": comparison.baseline_final_prob,
        "counterfactual_probability": comparison.counterfactual_final_prob,
        "probability_divergence": comparison.probability_divergence,
        "strategic_verdict": comparison.strategic_verdict,
        "counterfactual_summary": comparison.counterfactual_report.executive_summary,
    }


def main():
    """Loop principal JSON-RPC 2.0 sobre stdin/stdout."""
    logger.info("Servidor MCP K-SWARM pronto.")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as err:
            logger.error(f"JSON inválido: {err}")
            continue

        msg_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "k-swarm-mcp",
                        "version": "1.0.0",
                    },
                },
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            # Confirmação de inicialização do cliente
            continue

        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS_MANIFEST},
            }
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            try:
                if tool_name == "k_swarm_simulate":
                    data = handle_simulate(tool_args)
                elif tool_name == "k_swarm_fork":
                    data = handle_fork(tool_args)
                else:
                    raise ValueError(f"Ferramenta desconhecida: {tool_name}")

                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(data, indent=2, ensure_ascii=False),
                            }
                        ]
                    },
                }
            except Exception as exc:
                logger.error(f"Erro na execução da tool {tool_name}: {exc}", exc_info=True)
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "isError": True,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Erro na execução do K-SWARM: {str(exc)}",
                            }
                        ]
                    },
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        elif method == "ping":
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": {}}) + "\n")
            sys.stdout.flush()

        else:
            if msg_id is not None:
                sys.stdout.write(
                    json.dumps({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {"code": -32601, "message": f"Método não suportado: {method}"},
                    }) + "\n"
                )
                sys.stdout.flush()


if __name__ == "__main__":
    main()
