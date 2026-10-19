"""
K-SWARM: Agente Sintetizador Analítico (K-Synthesizer)
Gera relatórios executivos auditáveis com citações reais, equilíbrio de consenso e P&L do mercado.
Clean-Room Architecture - Konig Framework 2.0.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from .models import SimulationReport
from .engine import SimulationResult
from .graph import EpistemicGraph


class SwarmSynthesizer:
    """
    Sintetizador analítico ReACT. Audita o rastro da simulação no K-Graph
    e formula o parecer estratégico com evidências empíricas.
    """

    def __init__(self, graph: Optional[EpistemicGraph] = None):
        self.graph = graph

    def generate_report(self, result: SimulationResult) -> SimulationReport:
        """
        Processa as métricas de rodada, cotações do AMM e postagens observadas
        para formular o relatório executivo final.
        """
        # 1. Rastreamento da Deriva Temporal (Timeline Drift)
        timeline_drift: List[Dict[str, float]] = []
        for r in result.rounds:
            drift_entry = {"round": float(r.round_index), "consensus": r.consensus_score}
            drift_entry.update(r.mean_sentiment)
            timeline_drift.append(drift_entry)

        # 2. Sentimento Final e Preço de Equilíbrio
        last_round = result.rounds[-1] if result.rounds else None
        final_consensus = last_round.consensus_score if last_round else 0.5
        clearing_price = result.final_market.price_yes if result.final_market else 0.5

        # 3. Extração de Citações Críticas com Auditoria no Grafo
        critical_quotes: List[Dict[str, str]] = []
        if self.graph:
            cursor = self.graph.conn.execute("""
                SELECT agent_id, topic, stance, content
                FROM observations
                ORDER BY abs(stance) DESC, id DESC
                LIMIT 4;
            """)
            for row in cursor.fetchall():
                critical_quotes.append({
                    "agent": row["agent_id"],
                    "topic": row["topic"],
                    "stance": f"{row['stance']:+.2f}",
                    "quote": row["content"],
                })

        # 4. Identificação dos Principais Vetores (Key Drivers)
        key_drivers = []
        if clearing_price > 0.60:
            key_drivers.append("Percepção de ROI favorável dominou os agentes executivos e especialistas.")
        elif clearing_price < 0.40:
            key_drivers.append("Ceticismo sobre promessa de entrega e precificação gerou resistência nos consumidores.")
        else:
            key_drivers.append("Equilíbrio de forças entre entusiastas de novidade e céticos tradicionais.")

        if final_consensus > 0.70:
            key_drivers.append("Alto nível de consenso no enxame; baixa dispersão de opiniões.")
        else:
            key_drivers.append("Polarização ativa; nichos distintos reagiram de formas opostas.")

        # 5. Parecer e Recomendação Estratégica
        if clearing_price >= 0.65 and final_consensus >= 0.60:
            summary = (
                f"O cenário '{result.scenario_title}' obteve forte validação sintética. "
                f"A probabilidade de sucesso no mercado preditivo fechou em {clearing_price*100:.1f}%, "
                f"com índice de consenso de {final_consensus*100:.1f}%."
            )
            recommendation = (
                "APROVAÇÃO FORTE: A tese comercial e a proposta de valor resistiram ao estresse. "
                "Recomendado avançar para escala e investimento em tráfego imediato."
            )
        elif clearing_price <= 0.40:
            summary = (
                f"O cenário '{result.scenario_title}' sofreu rejeição significativa no enxame. "
                f"A probabilidade fechou em apenas {clearing_price*100:.1f}%, evidenciando atrito comercial."
            )
            recommendation = (
                "AJUSTE CRÍTICO NECESSÁRIO: O mercado simulado identificou fragilidades na oferta. "
                "Rever garantias, prazo de entrega ou ancoragem de preço antes de gastar capital real."
            )
        else:
            summary = (
                f"O cenário '{result.scenario_title}' apresentou resultado misto (Probabilidade: {clearing_price*100:.1f}%). "
                f"Mercado receptivo, mas com atrito em sub-segmentos específicos."
            )
            recommendation = (
                "SEGMENTAÇÃO E TESTE A/B: A tese atrai nichos específicos mas afasta o público amplo. "
                "Recomendado rodar ramificação contrafactual com variações de copy."
            )

        return SimulationReport(
            simulation_id=result.scenario_id,
            scenario_title=result.scenario_title,
            executive_summary=summary,
            consensus_score=round(final_consensus, 3),
            market_clearing_price=round(clearing_price, 3),
            key_drivers=key_drivers,
            critical_quotes=critical_quotes,
            timeline_drift=timeline_drift,
            strategic_recommendation=recommendation,
        )

    def export_markdown(self, report: SimulationReport) -> str:
        """Renderiza o relatório analítico em formato Markdown de publicação executiva."""
        md = [
            f"# RELATÓRIO EXECUTIVO K-SWARM: {report.scenario_title.upper()}",
            f"**Simulação ID:** `{report.simulation_id}` | **Probabilidade AMM:** `{report.market_clearing_price*100:.1f}%` | **Consenso:** `{report.consensus_score*100:.1f}%`\n",
            "## 1. Sumário Executivo",
            f"{report.executive_summary}\n",
            "## 2. Recomendação Estratégica",
            f"> **DIRETRIZ:** {report.strategic_recommendation}\n",
            "## 3. Principais Forças do Enxame (Key Drivers)",
        ]
        for driver in report.key_drivers:
            md.append(f"* {driver}")

        if report.critical_quotes:
            md.append("\n## 4. Citações Críticas Auditadas no Grafo")
            for q in report.critical_quotes:
                md.append(f"> \"{q['quote']}\" — **{q['agent']}** (Postura: `{q['stance']}` no tópico `{q['topic']}`)")

        md.append("\n## 5. Evolução Temporal da Simulação")
        md.append("| Rodada | Probabilidade / Sentimento | Consenso |")
        md.append("|:---:|:---:|:---:|")
        for d in report.timeline_drift:
            rnd = int(d["round"])
            cons = f"{d.get('consensus', 0.0)*100:.1f}%"
            # Pega primeiro tópico que não seja round/consensus
            topic_vals = [f"{k}: {v:+.2f}" for k, v in d.items() if k not in ["round", "consensus"]]
            md.append(f"| Round {rnd} | {', '.join(topic_vals)} | {cons} |")

        return "\n".join(md)
