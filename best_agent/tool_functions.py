
from __future__ import annotations

import json
import logging
import os
import textwrap
from collections import defaultdict
from typing import Any, Dict, List, Optional
from agent.file_upload import metadata_store, get_embedding, index as _faiss_index
import numpy as np

# ── Neo4j driver     ─────
from neo4j import GraphDatabase

NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "jawmi6-cujbez-zeqMyz")

_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# ── Ollama     ───────────
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# ── Optional FAISS vector store (PCAP) ────────────────────────────────────────
try:
    import faiss
    from agent.file_upload import metadata_store, get_embedding, index as _faiss_index  # type: ignore
except ImportError:
    faiss          = None   # type: ignore
    metadata_store = {}
    _faiss_index   = None

    def get_embedding(text: str) -> List[float]:  # type: ignore
        raise RuntimeError("Embedding backend not available.")

logger = logging.getLogger("phantom")

# ── Ontology label constants ───────────────────────────────────────────────────
GROUP          = "MitreAttackGroup"
TECHNIQUE      = "MitreAttackTechnique"
SOFTWARE       = "MitreAttackSoftware"
CAMPAIGN       = "MitreAttackCampaign"
MITIGATION     = "MitreAttackMitigation"
TACTIC         = "MitreAttackTactic"
DATA_SOURCE    = "MitreAttackDataSource"
DATA_COMPONENT = "MitreAttackDataComponent"

TACTIC_ORDER = [
    "Reconnaissance", "Resource Development", "Initial Access", "Execution",
    "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access",
    "Discovery", "Lateral Movement", "Collection", "Command and Control",
    "Exfiltration", "Impact",
]


    # GRAPH QUERY ENGINE
    
class AttackGraph:
    """
    All Cypher uses property names that actually exist in the Ontolocy schema.

    Key corrections vs v2.0:
      • Technique ID field  : attack_id   (schema required field)
      • Technique URL field : ref_url     (schema required field)
      • Mitigation ID field : attack_id   (schema required field)
      • Mitigation URL field: ref_url     (schema required field)
      • DataSource URL field: ref_url     (schema required field)
      • Group name matching : name only   (aliases not in schema – removed)
      • Tactic lookup       : via MITRE_TACTIC_INCLUDES_TECHNIQUE rel,
                              not a property on Technique nodes
      • platforms / detection / x_mitre_tactic_type : not in schema – removed
        from RETURN clauses; tactic resolved through the Tactic node instead.
    """

    def __init__(self, driver):
        self.driver = driver

    def run(self, query: str, params: Optional[dict] = None) -> List[dict]:
        with self.driver.session() as s:
            return [r.data() for r in s.run(query, params or {})]

    # ── Entity resolvers ──────────────────────────────────────────────────────

    def resolve_group(self, name: str) -> Optional[dict]:
        """Match on name only (aliases property does not exist in schema)."""
        rows = self.run(f"""
            MATCH (g:{GROUP})
            WHERE toLower(g.name) CONTAINS toLower($n)
            RETURN g {{.*}} AS g LIMIT 1
        """, {"n": name})
        return rows[0]["g"] if rows else None

    def resolve_technique(self, tid: str) -> Optional[dict]:
        """Look up by attack_id (the canonical ID field in Ontolocy schema)."""
        rows = self.run(f"""
            MATCH (t:{TECHNIQUE} {{attack_id: $tid}})
            RETURN t {{.*}} AS t LIMIT 1
        """, {"tid": tid.upper()})
        return rows[0]["t"] if rows else None

    # ── Core queries     

    def techniques_for_group(self, name: str) -> List[dict]:
        """
        Returns techniques used by the group, plus the tactic(s) each belongs
        to (resolved via MitreAttackTactic → MITRE_TACTIC_INCLUDES_TECHNIQUE).
        Relationship provenance fields are all Optional in the schema so we
        guard them with coalesce().
        """
        return self.run(f"""
          MATCH (g:{GROUP})-[r:MITRE_ATTACK_GROUP_USES_TECHNIQUE]->(t:{TECHNIQUE})
WHERE toLower(g.name) CONTAINS toLower($n)

OPTIONAL MATCH (tac:{TACTIC})-[:MITRE_TACTIC_INCLUDES_TECHNIQUE]->(t)

RETURN DISTINCT
    t.attack_id      AS technique_id,
    t.name           AS technique_name,
    t.description    AS description,
    t.ref_url        AS reference_url,
    t.attack_version AS attack_version,
    t.stix_modified  AS modified,
    tac.name         AS tactic,

    r.description    AS procedure

ORDER BY t.attack_id
        """, {"n": name})

    def software_for_group(self, name: str) -> List[dict]:
        return self.run(f"""
            MATCH (g:{GROUP})-[r:MITRE_ATTACK_GROUP_USES_SOFTWARE]->(sw:{SOFTWARE})
            WHERE toLower(g.name) CONTAINS toLower($n)
            RETURN DISTINCT
                sw.attack_id        AS software_id,
                sw.name             AS software_name,
                sw.description      AS description,
                sw.ref_url          AS reference_url,
                sw.stix_type        AS stix_type,
                sw.attack_version   AS attack_version,
                sw.stix_modified    AS modified
            ORDER BY sw.name
        """, {"n": name})

    def campaigns_for_group(self, name: str) -> List[dict]:
        return self.run(f"""
            MATCH (c:{CAMPAIGN})-[r:MITRE_CAMPAIGN_ATTRIBUTED_TO_INTRUSION_SET]->(g:{GROUP})
            WHERE toLower(g.name) CONTAINS toLower($n)
            RETURN DISTINCT
                c.attack_id    AS campaign_id,
                c.name         AS campaign_name,
                c.first_seen   AS first_seen,
                c.last_seen    AS last_seen,
                c.description  AS description,
                coalesce(r.description,      '') AS attribution_note,
                coalesce(r.data_origin_name, '') AS source
            ORDER BY c.first_seen DESC
        """, {"n": name})

    def mitigations_for_technique(self, tid: str) -> List[dict]:
        return self.run(f"""
            MATCH (m:{MITIGATION})-[r:MITRE_ATTACK_MITIGATION_DEFENDS_AGAINST_TECHNIQUE]
                  ->(t:{TECHNIQUE} {{attack_id: $tid}})
            RETURN DISTINCT
                m.attack_id    AS mitigation_id,
                m.name         AS mitigation_name,
                m.description  AS description,
                m.ref_url      AS url,
                coalesce(r.description,      '') AS application_note,
                coalesce(r.data_origin_name, '') AS source
            ORDER BY m.attack_id
        """, {"tid": tid.upper()})

    def data_components_for_technique(self, tid: str) -> List[dict]:
        return self.run(f"""
            MATCH (dc:{DATA_COMPONENT})-[r:MITRE_ATTACK_DATA_COMPONENT_DETECTS_TECHNIQUE]
                  ->(t:{TECHNIQUE} {{attack_id: $tid}})
            OPTIONAL MATCH (ds:{DATA_SOURCE})-[:MITRE_ATTACK_DATA_SOURCE_HAS_COMPONENT]->(dc)
            RETURN DISTINCT
                dc.name           AS data_component,
                dc.description    AS component_description,
                ds.name           AS data_source,
                ds.description    AS source_description,
                ds.ref_url        AS source_url,
                coalesce(r.description, '') AS detection_guidance
            ORDER BY ds.name, dc.name
        """, {"tid": tid.upper()})

    def sub_techniques(self, tid: str) -> List[dict]:
        """
        Children are identified by attack_subtechnique = true and the
        MITRE_SUBTECHNIQUE_OF relationship pointing to the parent.
        """
        return self.run(f"""
            MATCH (child:{TECHNIQUE})-[:MITRE_SUBTECHNIQUE_OF]
                  ->(parent:{TECHNIQUE} {{attack_id: $tid}})
            RETURN
                child.attack_id   AS sub_id,
                child.name        AS sub_name,
                child.description AS description
            ORDER BY child.attack_id
        """, {"tid": tid.upper()})

    def parent_technique(self, tid: str) -> Optional[dict]:
        rows = self.run(f"""
            MATCH (child:{TECHNIQUE} {{attack_id: $tid}})
                  -[:MITRE_SUBTECHNIQUE_OF]->(parent:{TECHNIQUE})
            RETURN parent.attack_id AS parent_id, parent.name AS parent_name
            LIMIT 1
        """, {"tid": tid.upper()})
        return rows[0] if rows else None

    def procedure_examples(self, tid: str, limit: int = 25) -> List[dict]:
        return self.run(f"""
            MATCH (actor)-[r]->(t:{TECHNIQUE} {{attack_id: $tid}})
            WHERE type(r) IN [
                'MITRE_ATTACK_GROUP_USES_TECHNIQUE',
                'MITRE_SOFTWARE_USES_TECHNIQUE',
                'MITRE_CAMPAIGN_USES_TECHNIQUE'
            ]
            RETURN
                labels(actor)[0]                   AS actor_type,
                actor.name                         AS actor,
                coalesce(actor.attack_id, '')      AS actor_id,
                coalesce(r.description, '')        AS procedure,
                coalesce(r.data_origin_name, '')   AS source,
                coalesce(r.data_origin_reference,'') AS reference_url,
                r.ontolocy_merged                  AS last_modified
            ORDER BY actor.name
            LIMIT $limit
        """, {"tid": tid.upper(), "limit": limit})

    def search_techniques(self, query: str, tactic: Optional[str],
                          platform: Optional[str], limit: int) -> List[dict]:
        """
        Tactic filtering is done via the Tactic node (MITRE_TACTIC_INCLUDES_TECHNIQUE),
        since x_mitre_tactic_type does not exist as a Technique property.
        Platform filtering removed (platforms not in schema).
        """
        tactic_filter = (
            "AND EXISTS { MATCH (tac2:MitreAttackTactic)-[:MITRE_TACTIC_INCLUDES_TECHNIQUE]->(t) "
            "WHERE toLower(tac2.name) CONTAINS toLower($tactic) }"
            if tactic else ""
        )
        params: dict = {"q": query.strip(), "qu": query.strip().upper(), "limit": limit}
        if tactic: params["tactic"] = tactic

        return self.run(f"""
            MATCH (t:{TECHNIQUE})
            WHERE (
                t.attack_id = $qu
                OR toLower(t.name)        CONTAINS toLower($q)
                OR toLower(t.description) CONTAINS toLower($q)
            )
            {tactic_filter}
            OPTIONAL MATCH (tac:{TACTIC})-[:MITRE_TACTIC_INCLUDES_TECHNIQUE]->(t)
            OPTIONAL MATCH (child:{TECHNIQUE})-[:MITRE_SUBTECHNIQUE_OF]->(t)
            WITH t, collect(DISTINCT tac.name) AS tactics,
                    collect(DISTINCT child.attack_id) AS sub_techniques
            RETURN
                t.attack_id        AS technique_id,
                t.name             AS technique_name,
                tactics,
                t.description      AS description,
                t.ref_url          AS url,
                t.attack_version   AS attack_version,
                t.stix_modified    AS modified,
                sub_techniques
            ORDER BY
                CASE WHEN t.attack_id = $qu THEN 0 ELSE 1 END, t.attack_id
            LIMIT $limit
        """, params)

    def list_groups(self, nation: Optional[str], motivation: Optional[str],
                    sort_by: str, limit: int) -> List[dict]:
        conditions = []
        if nation:     conditions.append("toLower(g.nation) CONTAINS toLower($nation)")
        if motivation: conditions.append("toLower(g.motivation) = toLower($motivation)")
        where  = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        order  = {
            "risk_score":      "g.risk_score DESC",
            "last_seen":       "g.last_seen DESC",
            "technique_count": "technique_count DESC",
        }.get(sort_by, "g.risk_score DESC")
        params: dict = {"limit": limit}
        if nation:     params["nation"]     = nation
        if motivation: params["motivation"] = motivation

        return self.run(f"""
            MATCH (g:{GROUP})
            {where}
            OPTIONAL MATCH (g)-[:MITRE_ATTACK_GROUP_USES_TECHNIQUE]->(t:{TECHNIQUE})
            WITH g, count(DISTINCT t) AS technique_count
            RETURN
                g.name            AS name,
                g.attack_id       AS attack_id,
                g.nation          AS nation,
                g.motivation      AS motivation,
                g.risk_score      AS risk_score,
                g.last_seen       AS last_seen,
                g.first_seen      AS first_seen,
                g.target_sectors  AS target_sectors,
                g.stix_id         AS stix_id,
                technique_count
            ORDER BY {order}
            LIMIT $limit
        """, params)

    def search_software(self, query: str, sw_type: Optional[str], limit: int) -> List[dict]:
        type_filter = (
            "AND toLower(sw.stix_type) = toLower($sw_type)"
            if sw_type and sw_type != "any" else ""
        )
        params: dict = {"q": query.strip(), "qu": query.strip().upper(), "limit": limit}
        if sw_type and sw_type != "any": params["sw_type"] = sw_type

        return self.run(f"""
            MATCH (sw:{SOFTWARE})
            WHERE (
                sw.attack_id = $qu
                OR toLower(sw.name)        CONTAINS toLower($q)
                OR toLower(sw.description) CONTAINS toLower($q)
            )
            {type_filter}
            OPTIONAL MATCH (g:{GROUP})-[:MITRE_ATTACK_GROUP_USES_SOFTWARE]->(sw)
            OPTIONAL MATCH (sw)-[:MITRE_SOFTWARE_USES_TECHNIQUE]->(t:{TECHNIQUE})
            WITH sw,
                 collect(DISTINCT g.name)       AS used_by_groups,
                 collect(DISTINCT t.attack_id)  AS techniques_used
            RETURN
                sw.attack_id    AS software_id,
                sw.name         AS software_name,
                sw.stix_type    AS software_type,
                sw.description  AS description,
                sw.ref_url      AS url,
                sw.stix_id      AS stix_id,
                used_by_groups,
                techniques_used
            ORDER BY sw.name
            LIMIT $limit
        """, params)

    def search_campaigns(self, query: str, limit: int) -> List[dict]:
        return self.run(f"""
            MATCH (c:{CAMPAIGN})
            WHERE toLower(c.name)        CONTAINS toLower($q)
               OR toLower(c.description) CONTAINS toLower($q)
            OPTIONAL MATCH (c)-[:MITRE_CAMPAIGN_ATTRIBUTED_TO_INTRUSION_SET]->(g:{GROUP})
            OPTIONAL MATCH (c)-[:MITRE_CAMPAIGN_USES_TECHNIQUE]->(t:{TECHNIQUE})
            WITH c,
                 collect(DISTINCT g.name)      AS attributed_groups,
                 collect(DISTINCT t.attack_id) AS techniques
            RETURN
                c.attack_id    AS campaign_id,
                c.name         AS campaign_name,
                c.first_seen   AS first_seen,
                c.last_seen    AS last_seen,
                c.description  AS description,
                c.ref_url      AS url,
                c.stix_id      AS stix_id,
                attributed_groups,
                techniques
            ORDER BY c.first_seen DESC
            LIMIT $limit
        """, {"q": query.strip(), "limit": limit})

    def overlap_matrix(self, names: List[str]) -> List[dict]:
        return self.run(f"""
            UNWIND $names AS name
            MATCH (g:{GROUP})
            WHERE toLower(g.name) CONTAINS toLower(name)
            OPTIONAL MATCH (g)-[:MITRE_ATTACK_GROUP_USES_TECHNIQUE]->(t:{TECHNIQUE})
            RETURN g.name AS actor, collect(DISTINCT t.attack_id) AS techniques
        """, {"names": names})

    def multi_hop_traverse(self, start_label: str, start_name: str,
                           relationships: List[str], depth: int) -> List[dict]:
        rel_pattern = "|".join(relationships)
        return self.run(f"""
            MATCH path = (s:{start_label})-[:{rel_pattern}*1..{depth}]->(end)
            WHERE toLower(s.name) CONTAINS toLower($n)
            WITH
                [nd IN nodes(path) |
                    {{label: labels(nd)[0], name: nd.name,
                      id: coalesce(nd.attack_id, nd.stix_id, '')}}] AS chain,
                [r IN relationships(path) | type(r)] AS rel_types,
                length(path) AS hops
            RETURN chain, rel_types, hops
            ORDER BY hops
            LIMIT 100
        """, {"n": start_name})

    def pagerank(self, label: str, limit: int) -> List[dict]:
        return self.run(f"""
            CALL gds.pageRank.stream({{
                nodeQuery: 'MATCH (n:{label}) RETURN id(n) AS id',
                relationshipQuery: 'MATCH (a:{label})-[r]->(b:{label}) RETURN id(a) AS source, id(b) AS target',
                maxIterations: 20,
                dampingFactor: 0.85
            }})
            YIELD nodeId, score
            MATCH (n) WHERE id(n) = nodeId
            RETURN n.name AS name,
                   coalesce(n.attack_id, n.stix_id, '') AS external_id,
                   score
            ORDER BY score DESC
            LIMIT $limit
        """, {"limit": limit})

    def node_similarity(self, label: str, rel_type: str, limit: int) -> List[dict]:
        return self.run(f"""
            CALL gds.nodeSimilarity.stream({{
                nodeQuery: 'MATCH (n:{label}) RETURN id(n) AS id',
                relationshipQuery: 'MATCH (n:{label})-[:{rel_type}]->(t) RETURN id(n) AS source, id(t) AS target'
            }})
            YIELD node1, node2, similarity
            MATCH (a) WHERE id(a) = node1
            MATCH (b) WHERE id(b) = node2
            RETURN a.name AS entity1, b.name AS entity2,
                   round(similarity * 100, 1) AS similarity_pct
            ORDER BY similarity DESC
            LIMIT $limit
        """, {"limit": limit})

    # ── Kill-chain tactic lookup ───────────────────────────────────────────────

    def tactic_for_technique(self, attack_id: str) -> Optional[str]:
        """Resolve the tactic name for a technique via the Tactic node."""
        rows = self.run(f"""
            MATCH (tac:{TACTIC})-[:MITRE_TACTIC_INCLUDES_TECHNIQUE]
                  ->(t:{TECHNIQUE} {{attack_id: $tid}})
            RETURN tac.name AS tactic LIMIT 1
        """, {"tid": attack_id.upper()})
        return rows[0]["tactic"] if rows else None

    def techniques_with_tactics(self, attack_ids: List[str]) -> List[dict]:
        """
        Bulk-fetch technique name + tactic for a list of attack_ids.
        Tactic resolved through the Tactic node, not a technique property.
        """
        return self.run(f"""
            UNWIND $ids AS tid
            MATCH (t:{TECHNIQUE} {{attack_id: tid}})
            OPTIONAL MATCH (tac:{TACTIC})-[:MITRE_TACTIC_INCLUDES_TECHNIQUE]->(t)
            RETURN
                t.attack_id   AS technique_id,
                t.name        AS technique_name,
                tac.name      AS tactic,
                t.description AS description,
                t.ref_url     AS url
        """, {"ids": attack_ids})


# ── Global graph instance ──────────────────────────────────────────────────────
_graph = AttackGraph(_driver)


    # TOOL IMPLEMENTATIONS
    
def get_threat_actor_profile(actor_name: str) -> dict:
    group = _graph.resolve_group(actor_name)
    if not group:
        return {"found": False, "actor_name": actor_name,
                "message": f"No ATT&CK group found matching '{actor_name}'."}

    name       = group.get("name", actor_name)
    techniques = _graph.techniques_for_group(name)
    software   = _graph.software_for_group(name)
    campaigns  = _graph.campaigns_for_group(name)

    tactic_summary: Dict[str, List[str]] = defaultdict(list)
    for t in techniques:
        tac = t.get("tactic") or "Unknown"
        tid = t.get("technique_id")
        if tid:
            tactic_summary[tac].append(tid)

    return {
        "found":           True,
        "name":            name,
        "attack_id":       group.get("attack_id", ""),
        "stix_id":         group.get("stix_id"),
        "nation":          group.get("nation", "Unknown"),
        "motivation":      group.get("motivation", "Unknown"),
        "target_sectors":  group.get("target_sectors") or [],
        "first_seen":      group.get("first_seen"),
        "last_seen":       group.get("last_seen"),
        "risk_score":      group.get("risk_score", 0),
        "description":     group.get("description", ""),
        "url":             group.get("ref_url", ""),
        "technique_count": len(techniques),
        "techniques":      techniques,
        "tactic_summary":  dict(tactic_summary),
        "software":        software,
        "campaigns":       campaigns,
        "source":          "neo4j/ontolocy",
    }


def list_threat_actors(
    nation: Optional[str] = None,
    motivation: Optional[str] = None,
    top_n: int = 15,
    sort_by: str = "risk_score",
) -> dict:
    rows = _graph.list_groups(nation, motivation, sort_by, top_n)
    return {
        "found":       bool(rows),
        "filters":     {"nation": nation, "motivation": motivation},
        "sort_by":     sort_by,
        "actor_count": len(rows),
        "actors":      rows,
    }


def compare_actors(actor1: str, actor2: str, focus: str = "all") -> dict:
    rows = _graph.overlap_matrix([actor1, actor2])
    data: Dict[str, set] = {}
    for r in rows:
        data[r["actor"]] = set(r.get("techniques") or [])

    if len(data) < 2:
        missing = [n for n in [actor1, actor2]
                   if not any(n.lower() in k.lower() for k in data)]
        return {"error": f"Actor(s) not found: {missing}"}

    n1, n2 = list(data.keys())[:2]
    t1, t2 = data[n1], data[n2]
    sw1    = {s["software_id"] for s in _graph.software_for_group(n1) if s.get("software_id")}
    sw2    = {s["software_id"] for s in _graph.software_for_group(n2) if s.get("software_id")}
    c1     = {c["campaign_name"] for c in _graph.campaigns_for_group(n1) if c.get("campaign_name")}
    c2     = {c["campaign_name"] for c in _graph.campaigns_for_group(n2) if c.get("campaign_name")}
    union  = t1 | t2
    jaccard = round(len(t1 & t2) / len(union) * 100, 1) if union else 0.0

    result: dict = {
        "found": True, "actor1": n1, "actor2": n2,
        "similarity_score": jaccard, "focus": focus,
    }
    if focus in ("ttps", "all"):
        result["ttps"] = {
            "shared_count":  len(t1 & t2),
            "shared":        sorted(t1 & t2),
            "unique_actor1": sorted(t1 - t2),
            "unique_actor2": sorted(t2 - t1),
        }
    if focus in ("malware", "all"):
        result["malware"] = {
            "actor1_software": sorted(sw1),
            "actor2_software": sorted(sw2),
            "shared_software": sorted(sw1 & sw2),
        }
    if focus in ("targets", "all"):
        g1 = _graph.resolve_group(n1) or {}
        g2 = _graph.resolve_group(n2) or {}
        s1 = set(g1.get("target_sectors") or [])
        s2 = set(g2.get("target_sectors") or [])
        result["targets"] = {
            "actor1_sectors": sorted(s1),
            "actor2_sectors": sorted(s2),
            "shared_sectors": sorted(s1 & s2),
        }
    result["campaigns"] = {
        "actor1_campaigns": sorted(c1),
        "actor2_campaigns": sorted(c2),
        "shared_campaigns": sorted(c1 & c2),
    }
    return result


def search_techniques(
    query: str,
    tactic: Optional[str] = None,
    platform: Optional[str] = None,   # kept for API compat; not used in Cypher
    max_results: int = 10,
) -> dict:
    rows = _graph.search_techniques(query, tactic, platform, max_results)
    if not rows:
        return {"found": False, "query": query, "results": [], "total": 0}
    results = [{
        "technique_id":   r.get("technique_id"),
        "technique_name": r.get("technique_name"),
        "tactics":        r.get("tactics", []),
        "description":    textwrap.shorten(r.get("description", ""), 300, placeholder="…"),
        "url":            r.get("url", ""),
        "modified":       r.get("modified"),
        "sub_techniques": r.get("sub_techniques", []),
    } for r in rows]
    return {"found": True, "query": query, "results": results, "total": len(results)}


def get_technique_detail(
    technique_id: str,
    include_procedures: bool = True,
    include_mitigations: bool = True,
    include_data_sources: bool = True,
    include_sub_techniques: bool = True,
    procedure_limit: int = 20,
) -> dict:
    tid  = technique_id.strip().upper()
    node = _graph.resolve_technique(tid)
    if not node:
        return {"found": False, "technique_id": tid}

    # Resolve tactic via relationship (not a node property)
    tactic_name = _graph.tactic_for_technique(tid) or ""

    result: dict = {
        "found":          True,
        "technique_id":   node.get("attack_id", tid),
        "technique_name": node.get("name", ""),
        "tactic":         tactic_name,
        "description":    node.get("description", ""),
        "url":            node.get("ref_url", ""),
        "stix_id":        node.get("stix_id"),
        "attack_version": node.get("attack_version", ""),
        "stix_modified":  node.get("stix_modified"),
        "is_subtechnique": bool(node.get("attack_subtechnique", False)),
        "source":         "neo4j/ontolocy",
    }
    parent = _graph.parent_technique(tid)
    if parent:
        result["parent_technique"] = parent
    if include_sub_techniques:
        result["sub_techniques"] = _graph.sub_techniques(tid)
    if include_mitigations:
        result["mitigations"]      = _graph.mitigations_for_technique(tid)
        result["mitigation_count"] = len(result["mitigations"])
    if include_data_sources:
        result["data_components"]      = _graph.data_components_for_technique(tid)
        result["data_component_count"] = len(result["data_components"])
    if include_procedures:
        result["procedure_examples"] = _graph.procedure_examples(tid, procedure_limit)
        result["procedure_count"]    = len(result["procedure_examples"])
    return result


def get_kill_chain_analysis(
    actor_name: Optional[str] = None,
    technique_ids: Optional[List[str]] = None,
    highlight_gaps: bool = True,
) -> dict:
    if actor_name and technique_ids:
        return {"error": "Provide actor_name OR technique_ids — not both."}
    if not actor_name and not technique_ids:
        return {"error": "Provide either actor_name or technique_ids."}

    resolved_actor  = None
    proc_meta: Dict[str, dict] = {}

    if actor_name:
        rows = _graph.techniques_for_group(actor_name)
        if not rows:
            return {
                "found":      False,
                "actor_name": actor_name,
                "message":    f"No techniques found for '{actor_name}'.",
            }
        resolved_actor = actor_name
        technique_ids  = [r["technique_id"] for r in rows if r.get("technique_id")]
        proc_meta      = {r["technique_id"]: r for r in rows}
    else:
        technique_ids = [t.strip().upper() for t in technique_ids]  # type: ignore

    # Bulk-fetch technique details with tactic resolved via Tactic node
    detail_rows = _graph.techniques_with_tactics(technique_ids)

    tactic_map: Dict[str, List[dict]] = defaultdict(list)
    for r in detail_rows:
        tac = r.get("tactic") or "Unknown"
        tid = r["technique_id"]
        tactic_map[tac].append({
            "technique_id":   tid,
            "technique_name": r.get("technique_name", ""),
            "url":            r.get("url", ""),
            "procedure":      proc_meta.get(tid, {}).get("procedure", ""),
            "source":         proc_meta.get(tid, {}).get("source", ""),
            "reference_url":  proc_meta.get(tid, {}).get("reference_url", ""),
        })

    covered      = set(tactic_map.keys()) - {"Unknown"}
    gap_tactics  = sorted(
        set(TACTIC_ORDER) - covered,
        key=lambda t: TACTIC_ORDER.index(t) if t in TACTIC_ORDER else 99,
    )
    coverage_pct = round(len(covered) / len(TACTIC_ORDER) * 100, 1) if TACTIC_ORDER else 0.0
    heatmap      = {t: len(tactic_map.get(t, [])) for t in TACTIC_ORDER}

    result = {
        "found":           True,
        "actor_name":      resolved_actor,
        "technique_count": len(detail_rows),
        "coverage_pct":    coverage_pct,
        "covered_tactics": sorted(covered, key=lambda t: TACTIC_ORDER.index(t)
                                   if t in TACTIC_ORDER else 99),
        "tactic_breakdown": {t: tactic_map.get(t, []) for t in TACTIC_ORDER},
        "heatmap":         heatmap,
        "source":          "neo4j/ontolocy",
    }
    if highlight_gaps:
        result["gap_tactics"] = gap_tactics
    return result


def search_software(
    query: str,
    software_type: str = "any",
    max_results: int = 10,
) -> dict:
    rows = _graph.search_software(query, software_type, max_results)
    if not rows:
        return {"found": False, "query": query, "results": [], "total": 0}
    return {"found": True, "query": query, "results": rows, "total": len(rows)}


def search_campaigns(query: str, max_results: int = 10) -> dict:
    rows = _graph.search_campaigns(query, max_results)
    if not rows:
        return {"found": False, "query": query, "results": [], "total": 0}
    return {"found": True, "query": query, "results": rows, "total": len(rows)}


def traverse_attack_graph(
    entity_name: str,
    start_label: str,
    relationships: List[str],
    depth: int = 2,
) -> dict:
    rows = _graph.multi_hop_traverse(start_label, entity_name, relationships, depth)
    if not rows:
        return {"found": False, "entity_name": entity_name,
                "relationships": relationships, "depth": depth, "paths": []}
    return {
        "found":         True,
        "entity_name":   entity_name,
        "start_label":   start_label,
        "relationships": relationships,
        "depth":         depth,
        "path_count":    len(rows),
        "paths":         rows,
        "source":        "neo4j/ontolocy",
    }


def run_graph_analytics(
    algorithm: str,
    node_label: str = TECHNIQUE,
    limit: int = 20,
) -> dict:
    try:
        if algorithm == "pagerank":
            rows = _graph.pagerank(node_label, limit)
            return {
                "found":     bool(rows),
                "algorithm": "pagerank",
                "label":     node_label,
                "results":   rows,
                "note":      "Score = PageRank centrality. Higher = more referenced in the graph.",
            }
        elif algorithm == "similarity":
            rel = ("MITRE_ATTACK_GROUP_USES_TECHNIQUE"
                   if node_label in (GROUP, SOFTWARE, CAMPAIGN)
                   else "MITRE_TACTIC_INCLUDES_TECHNIQUE")
            rows = _graph.node_similarity(node_label, rel, limit)
            return {
                "found":     bool(rows),
                "algorithm": "jaccard_similarity",
                "label":     node_label,
                "results":   rows,
                "note":      "similarity_pct = Jaccard % based on shared TTP targets.",
            }
    except Exception as exc:
        return {"error": "gds_unavailable",
                "message": f"Neo4j GDS plugin required. Details: {exc}"}
    return {"error": "unknown_algorithm", "algorithm": algorithm}


def generate_hunt_hypothesis(
    threat_context: str,
    environment: str = "unknown",
    output_format: str = "sigma",
) -> dict:
    try:
        from best_agent import generate_hunt_hypothesis as impl  # type: ignore
        return impl(threat_context=threat_context,
                    environment=environment,
                    output_format=output_format)
    except ImportError:
        return {"error": "not_implemented",
                "message": "Hunt hypothesis generator not loaded. Ensure agent.py is present."}


def search_pcap_context(
    query: str,
    top_k: int = 5,
    protocol_filter: str = "any",
) -> dict:

    try:
        top_k = int(top_k)
    except:
        top_k = 5

    if _faiss_index is None or _faiss_index.ntotal == 0:
        return {
            "found": False,
            "results": [],
            "total_matches": 0,
            "message": "No PCAP data ingested."
        }

    qv = np.array(
        get_embedding(query),
        dtype="float32"
    ).reshape(1, -1)

    k = min(max(top_k * 4, 10), _faiss_index.ntotal)

    scores, ids = _faiss_index.search(qv, k)

    results = []

    for score, idx in zip(scores[0], ids[0]):

        if idx == -1:
            continue

        entry = metadata_store.get(int(idx))

        if not entry:
            continue

        proto = entry.get("protocol", "").lower()

        if (
            protocol_filter != "any"
            and proto != protocol_filter.lower()
        ):
            continue

        results.append({
            "packet_number": entry.get("packet_number"),
            "protocol": entry.get("protocol"),
            "src_ip": entry.get("src_ip"),
            "dst_ip": entry.get("dst_ip"),
            "src_port": entry.get("src_port"),
            "dst_port": entry.get("dst_port"),
            "summary": entry.get("summary"),
            "payload": entry.get("payload"),
            "relevance_score": round(float(score), 4),
        })

        if len(results) >= top_k:
            break

    return {
        "found": bool(results),
        "query": query,
        "protocol_filter": protocol_filter,
        "total_matches": len(results),
        "results": results,
    }

    # TOOL REGISTRY & DISPATCHER
    
TOOL_FUNCTIONS: Dict[str, Any] = {
    "get_threat_actor_profile": get_threat_actor_profile,
    "list_threat_actors":       list_threat_actors,
    "compare_actors":           compare_actors,
    "search_techniques":        search_techniques,
    "get_technique_detail":     get_technique_detail,
    "get_kill_chain_analysis":  get_kill_chain_analysis,
    "search_software":          search_software,
    "search_campaigns":         search_campaigns,
    "traverse_attack_graph":    traverse_attack_graph,
    "run_graph_analytics":      run_graph_analytics,
    "generate_hunt_hypothesis": generate_hunt_hypothesis,
    "search_pcap_context":      search_pcap_context,
}


def dispatch_tool(name: str, args: dict) -> dict:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        logger.error("Unknown tool: %s", name)
        return {"error": "unknown_tool", "tool_name": name}
    try:
        return fn(**args)
    except TypeError as exc:
        logger.exception("Bad args for %s: %s", name, exc)
        return {"error": "invalid_arguments", "tool_name": name, "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Tool %s error: %s", name, exc)
        return {"error": "execution_error", "tool_name": name, "message": str(exc)}