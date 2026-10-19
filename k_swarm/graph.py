"""
K-SWARM: Armazenamento em Grafo Epistêmico Leve (K-Graph)
Sistema 1 / 2: Grafo temporal relacional embarcado sem dependências externas (Zero Neo4j).
Clean-Room Architecture - Konig Framework 2.0.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple


class EpistemicGraph:
    """
    Grafo de conhecimento relacional e epistêmico embarcado sobre SQLite.
    Permite busca por nós, travessia BFS em k-hops, filtros temporais e resolução de contradições.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Inicializa tabelas relacionais de entidades, arestas e observações."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    attributes TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    evidence TEXT DEFAULT '',
                    valid_from_round INTEGER DEFAULT 0,
                    valid_to_round INTEGER DEFAULT 999999,
                    FOREIGN KEY(source_id) REFERENCES entities(id),
                    FOREIGN KEY(target_id) REFERENCES entities(id)
                );
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relations_temporal ON relations(valid_from_round, valid_to_round);
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    round_index INTEGER NOT NULL,
                    agent_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    stance REAL NOT NULL,
                    content TEXT NOT NULL
                );
            """)

    def add_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insere ou atualiza uma entidade no grafo."""
        attrs_json = json.dumps(attributes or {}, ensure_ascii=False)
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO entities (id, name, entity_type, attributes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    entity_type = excluded.entity_type,
                    attributes = excluded.attributes;
                """,
                (entity_id, name, entity_type, attrs_json),
            )

    def add_relation(
        self,
        relation_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 1.0,
        evidence: str = "",
        valid_from_round: int = 0,
    ) -> None:
        """Cria uma aresta direcionada entre duas entidades."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO relations (id, source_id, target_id, relation_type, weight, evidence, valid_from_round)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    weight = excluded.weight,
                    evidence = excluded.evidence;
                """,
                (relation_id, source_id, target_id, relation_type, weight, evidence, valid_from_round),
            )

    def invalidate_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        invalidated_at_round: int,
    ) -> int:
        """
        Tratamento de contradições: encerra a validade temporal de uma aresta.
        Permite consultas de 'como o mundo era entendido no round R'.
        """
        with self.conn:
            cursor = self.conn.execute(
                """
                UPDATE relations
                SET valid_to_round = ?
                WHERE source_id = ? AND target_id = ? AND relation_type = ? AND valid_to_round > ?;
                """,
                (invalidated_at_round, source_id, target_id, relation_type, invalidated_at_round),
            )
            return cursor.rowcount

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna uma entidade com seus atributos decodificados."""
        cursor = self.conn.execute(
            "SELECT id, name, entity_type, attributes FROM entities WHERE id = ?;",
            (entity_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "entity_type": row["entity_type"],
            "attributes": json.loads(row["attributes"]),
        }

    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca entidades por correspondência textual parcial em nome ou tipo."""
        wildcard = f"%{query}%"
        cursor = self.conn.execute(
            """
            SELECT id, name, entity_type, attributes
            FROM entities
            WHERE name LIKE ? OR entity_type LIKE ?
            LIMIT ?;
            """,
            (wildcard, wildcard, limit),
        )
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "name": row["name"],
                "entity_type": row["entity_type"],
                "attributes": json.loads(row["attributes"]),
            })
        return results

    def traverse_subgraph(
        self,
        seed_entity_id: str,
        max_hops: int = 2,
        as_of_round: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Travessia em largura (BFS) a partir de uma entidade semente.
        Retorna o subgrafo de contexto com nós e arestas válidas no round especificado.
        """
        visited_nodes: Set[str] = {seed_entity_id}
        queue: List[Tuple[str, int]] = [(seed_entity_id, 0)]
        collected_edges: List[Dict[str, Any]] = []

        temporal_clause = ""
        params: List[Any] = []
        if as_of_round is not None:
            temporal_clause = "AND valid_from_round <= ? AND valid_to_round > ?"

        while queue:
            current_id, current_hop = queue.pop(0)
            if current_hop >= max_hops:
                continue

            query = f"""
                SELECT id, source_id, target_id, relation_type, weight, evidence
                FROM relations
                WHERE (source_id = ? OR target_id = ?) {temporal_clause};
            """
            exec_params = [current_id, current_id]
            if as_of_round is not None:
                exec_params.extend([as_of_round, as_of_round])

            cursor = self.conn.execute(query, exec_params)
            for row in cursor.fetchall():
                edge_dict = {
                    "id": row["id"],
                    "source": row["source_id"],
                    "target": row["target_id"],
                    "relation": row["relation_type"],
                    "weight": row["weight"],
                    "evidence": row["evidence"],
                }
                if edge_dict not in collected_edges:
                    collected_edges.append(edge_dict)

                next_id = row["target_id"] if row["source_id"] == current_id else row["source_id"]
                if next_id not in visited_nodes:
                    visited_nodes.add(next_id)
                    queue.append((next_id, current_hop + 1))

        # Recupera dados dos nós visitados
        nodes: List[Dict[str, Any]] = []
        for node_id in visited_nodes:
            entity = self.get_entity(node_id)
            if entity:
                nodes.append(entity)

        return {"nodes": nodes, "edges": collected_edges}

    def record_observation(
        self,
        obs_id: str,
        round_index: int,
        agent_id: str,
        topic: str,
        stance: float,
        content: str,
    ) -> None:
        """Registra uma observação/post no histórico auditável da simulação."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO observations (id, round_index, agent_id, topic, stance, content)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (obs_id, round_index, agent_id, topic, stance, content),
            )

    def close(self) -> None:
        """Fecha a conexão com a base SQLite."""
        self.conn.close()
