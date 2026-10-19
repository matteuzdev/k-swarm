"""
K-SWARM: CLI Standalone
Executa simulações sociais e oráculo de predição de mercado.
"""

from __future__ import annotations

import sys
import argparse
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from k_swarm import (
    SwarmEngine,
    SimulationScenario,
    PersonaGenerator,
    EpistemicGraph,
    SwarmSynthesizer,
)


def main():
    parser = argparse.ArgumentParser(
        prog="k-swarm",
        description="K-SWARM — Universal Swarm Intelligence & Prediction Market Engine"
    )
    parser.add_argument("scenario", help="Descrição do cenário ou oferta comercial a simular")
    parser.add_argument("--topic", "-t", default="viabilidade_comercial", help="Tópico focal")
    parser.add_argument("--rounds", "-r", type=int, default=5, help="Quantidade de rodadas (padrão: 5)")
    parser.add_argument("--personas", "-p", type=int, default=25, help="Quantidade de personas sintéticas (padrão: 25)")
    parser.add_argument("--anchor", "-a", type=float, default=0.0, help="Âncora de sentimento inicial [-1.0 a 1.0]")
    parser.add_argument("--export-md", default=None, help="Caminho para exportar o relatório Markdown")

    args = parser.parse_args()

    print("\n⚡ K-SWARM ENGINE — Disparando Simulação e Mercado AMM...")
    print(f"🎯 Cenário: '{args.scenario}'")
    print(f"📌 Tópico: [{args.topic}] | Rodadas: {args.rounds} | Personas: {args.personas}")

    start_time = time.perf_counter()

    graph = EpistemicGraph(":memory:")
    generator = PersonaGenerator(graph)

    personas = generator.generate_personas(
        count=args.personas,
        scenario_context=args.scenario,
        target_topics=[args.topic],
        sentiment_anchor=args.anchor,
    )

    scenario = SimulationScenario(
        scenario_id="standalone_run",
        title=args.scenario,
        core_question=args.topic,
        context_text=args.scenario,
        rounds_count=args.rounds,
        personas=personas,
        market_config={"initial_probability": 0.50},
    )

    engine = SwarmEngine(scenario=scenario, graph=graph)
    result = engine.run()

    synthesizer = SwarmSynthesizer(graph=graph)
    report = synthesizer.generate_report(result)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    print("\n" + "=" * 65)
    print(f"🏆 RESULTADO K-SWARM ({elapsed_ms:.1f} ms de tempo de execução total)")
    print("=" * 65)
    prob_pct = (report.market_clearing_price or 0.5) * 100
    print(f"📈 Probabilidade de Sucesso no Mercado (AMM): {prob_pct:.1f}%")
    print(f"🤝 Índice de Consenso do Enxame:            {report.consensus_score * 100:.1f}%")
    print(f"\n📝 Sumário Executivo:\n{report.executive_summary}")
    print(f"\n🧭 Diretriz Estratégica:\n> {report.strategic_recommendation}")

    if report.critical_quotes:
        print("\n💬 Citações Auditadas no K-Graph:")
        for q in report.critical_quotes[:3]:
            print(f"   • [{q['agent']}] ({q['stance']}): \"{q['quote']}\"")

    if args.export_md:
        with open(args.export_md, "w", encoding="utf-8") as f:
            f.write(synthesizer.export_markdown(report))
        print(f"\n💾 Relatório completo exportado para: {args.export_md}")

    graph.close()


if __name__ == "__main__":
    main()
