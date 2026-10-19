# ⚡ K-SWARM: Universal Swarm Intelligence & Prediction Market Engine

> **"Simulate Before Reality"** — High-frequency multi-agent social simulation, epistemic memory graphs, and automated prediction markets running in under **100 milliseconds** with zero token burn per tick.

[![Tests](https://img.shields.io/badge/tests-16%20passed-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![MCP Ready](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)]()

---

## 🎯 What is K-SWARM?

K-SWARM is an enterprise-grade, clean-room autonomous simulation engine. It allows business strategists, product managers, and software engineers to stress-test offers, product launches, copies, or regulatory scenarios against swarms of 20 to 100+ grounded personas.

Unlike naive agent frameworks that incur astronomical API costs by querying frontier LLMs for every micro-decision, K-SWARM decouples **System 1 (Deterministic High-Frequency State Transitions)** from **System 2 (Frontier Reasoning & Synthesis)**:

* **System 1 (Tick Execution):** Belief updates, cognitive inertia, social proof heuristics, and constant-product AMM market orders run in pure, vectorized Python in **microssegundos** at **zero token cost**.
* **System 2 (Synthesis & Auditing):** Frontier models (Gemini, Claude, DeepSeek) are invoked strictly for initial grounded persona setup and final ReACT evidence-backed executive reporting.

---

## 🏗️ Core Architecture (Clean-Room Mechanisms)

```
┌────────────────────────────────────────────────────────────────────────┐
│                          K-SWARM ENGINE CORE                           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
               ┌───────────────────┴───────────────────┐
               ▼                                       ▼
    ┌──────────────────────┐               ┌──────────────────────┐
    │  Epistemic K-Graph   │               │     K-Belief State   │
    │  (Embedded SQLite /  │               │  (Vector Heuristic   │
    │   PostgreSQL Vector) │               │   Zero Token / Tick) │
    └──────────┬───────────┘               └──────────┬───────────┘
               │                                      │
               └───────────────────┬──────────────────┘
                                   ▼
        ┌────────────────────────────────────────────────────┐
        │       Omnichannel Social Simulation Engine         │
        │   ┌───────────────┐ ┌──────────────┐ ┌───────────┐ │
        │   │  Microblog    │ │  B2B Forums  │ │  Market   │ │
        │   │ (Posts / RT)  │ │ (WhatsApp/TG)│ │  (AMM k)  │ │
        │   └───────┬───────┘ └──────┬───────┘ └─────┬─────┘ │
        └───────────┼────────────────┼───────────────┼───────┘
                    └────────────────┴───────────────┘
                                     │
                         Market-Media Bridge (k)
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────┐
        │             K-Synthesizer (ReACT + Nash)           │
        │     Evidence Reports with Graph-Audited Quotes     │
        └────────────────────────────────────────────────────┘
```

### 1. K-Belief State (Heuristic Opinion Dynamics)
Each persona maintains:
$$\text{Stance} \in [-1.0, +1.0], \quad \text{Confidence} \in [0.1, 1.0], \quad \text{Trust}(\text{author}) \in [0.0, 1.0]$$
The belief update is modulated by novelty decay, engagement proof, and cognitive inertia without calling external LLM APIs.

### 2. K-AMM (Constant-Product Prediction Market)
* **Invariant:** $x \cdot y = k$
* **Market-Media Bridge:** Personas with trader archetypes assess the spread between their internal belief and current market probability, executing automated buy/sell orders that move token prices in real time.

### 3. Epistemic K-Graph
Zero-Docker, embedded relational graph storage over SQLite. Features BFS k-hop neighborhood expansion, temporal query validity (`as_of_round`), and contradiction invalidation.

### 4. Timeline Forking ("What-if" Branching)
Forks a running simulation at round $R$, injects a black-swan disruption event, and evaluates side-by-side divergence in market probability and community consensus.

---

## ⚡ Quickstart

### Installation
```bash
git clone https://github.com/matteuzdev/k-swarm.git
cd k-swarm
pip install -e .
```

### Run Simulation via CLI
```bash
python cli.py "Launch AI Scheduler for local medical clinics at $149/mo" \
  --topic "sales_conversion" \
  --rounds 5 \
  --personas 25 \
  --export-md "report.md"
```

Output benchmark:
```text
=================================================================
🏆 K-SWARM RESULT (78.9 ms total execution time)
=================================================================
📈 Market Probability (AMM): 64.2%
🤝 Swarm Consensus Index:   88.5%

📝 Executive Summary:
Market validation confirmed. Receptive demand with high willingness to pay.
```

---

## 🔌 Model Context Protocol (MCP) Server

K-SWARM includes a native stdio-based MCP server compatible with **Antigravity**, **Cursor**, **Claude Desktop**, and **OpenCode**:

```json
{
  "mcpServers": {
    "k-swarm": {
      "command": "python",
      "args": ["-m", "k_swarm.mcp_server"],
      "cwd": "/path/to/k-swarm"
    }
  }
}
```

Exposed Tools:
* `k_swarm_simulate(scenario, topic, rounds, personas, anchor)`
* `k_swarm_fork(scenario, topic, event_headline, event_content, impact_magnitude)`

---

## 🧪 Testing

```bash
pytest tests/ -v
```
All 16 tests pass deterministically in under **0.7 seconds**.

---

## 📄 License
MIT License. Clean-Room reconstructed and maintained by the KONIG Engineering Bench.
