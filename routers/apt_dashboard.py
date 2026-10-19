import os
from fastapi import FastAPI, Query
from neo4j import GraphDatabase
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter

    
# Neo4j Connection
    
router = APIRouter(tags=["APT Hunt Dashboard"])

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)


def run_query(query, params=None):
    try:
        with driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    except Exception as e:
        print("DB ERROR:", e)
        return []


def node_props(node) -> dict:
    """Return all properties from a Neo4j node as a plain dict."""
    if node is None:
        return {}
    return dict(node)


    
# FastAPI App
    



    
# GROUPS
    

@router.get("/groups_neo4j")
def get_groups():
    query = """
    MATCH (g:MitreAttackGroup)
    OPTIONAL MATCH (g)--(t:MitreAttackTechnique)
    OPTIONAL MATCH (g)--(c:MitreAttackCampaign)
    OPTIONAL MATCH (g)--(s:MitreAttackSoftware)

    RETURN g,
           count(DISTINCT t) AS techniqueCount,
           collect(DISTINCT t.id)   AS techniqueIds,
           collect(DISTINCT t.name) AS techniqueNames,
           count(DISTINCT s) AS softwareCount,
           collect(DISTINCT s.id)   AS softwareIds,
           collect(DISTINCT s.name) AS softwareNames,
           count(DISTINCT c) AS campaignCount,
           collect(DISTINCT c.id)   AS campaignIds,
           collect(DISTINCT c.name) AS campaignNames
    """

    rows = run_query(query)

    return [
        {
            # ── All node properties (future-proof) ──
            **node_props(r["g"]),
            # ── Explicit fields for clarity / guaranteed presence ──
            "id":            r["g"].get("id"),
            "name":          r["g"].get("name"),
            "alias":         r["g"].get("alias"),
            "aliases":       r["g"].get("aliases", []),
            "nation":        r["g"].get("nation"),
            "description":   r["g"].get("description"),
            "url":           r["g"].get("url"),
            "created":       r["g"].get("created"),
            "modified":      r["g"].get("modified"),
            "lastSeen":      r["g"].get("lastSeen"),
            "active":        r["g"].get("active", True),
            "risk":          r["g"].get("risk", "UNKNOWN"),
            # ── Relationship counts + id/name lists ──
            "techniqueCount":  r["techniqueCount"],
            "techniqueIds":    [i for i in r["techniqueIds"]  if i],
            "techniqueNames":  [n for n in r["techniqueNames"] if n],
            "softwareCount":   r["softwareCount"],
            "softwareIds":     [i for i in r["softwareIds"]   if i],
            "softwareNames":   [n for n in r["softwareNames"]  if n],
            "campaignCount":   r["campaignCount"],
            "campaignIds":     [i for i in r["campaignIds"]   if i],
            "campaignNames":   [n for n in r["campaignNames"]  if n],
        }
        for r in rows
    ]


    
# TECHNIQUES
    

@router.get("/techniques")
def get_techniques():
    query = """
    MATCH (t:MitreAttackTechnique)
    OPTIONAL MATCH (g:MitreAttackGroup)--(t)
    OPTIONAL MATCH (t)--(ta:MitreAttackTactic)
    OPTIONAL MATCH (t)--(s:MitreAttackSoftware)
    OPTIONAL MATCH (t)--(m:MitreAttackMitigation)
    OPTIONAL MATCH (t)--(sub:MitreAttackTechnique)
        WHERE sub.isSubtechnique = true

    RETURN t,
           count(DISTINCT g)   AS groupCount,
           collect(DISTINCT g.id)   AS groupIds,
           collect(DISTINCT g.name) AS groupNames,
           collect(DISTINCT ta.id)   AS tacticIds,
           collect(DISTINCT ta.name) AS tacticNames,
           count(DISTINCT s)   AS softwareCount,
           collect(DISTINCT s.id)   AS softwareIds,
           collect(DISTINCT s.name) AS softwareNames,
           count(DISTINCT m)   AS mitigationCount,
           collect(DISTINCT m.id)   AS mitigationIds,
           collect(DISTINCT m.name) AS mitigationNames,
           count(DISTINCT sub) AS subtechniqueCount,
           collect(DISTINCT sub.id) AS subtechniqueIds
    """

    rows = run_query(query)

    return [
        {
            **node_props(r["t"]),
            "id":               r["t"].get("id"),
            "name":             r["t"].get("name"),
            "description":      r["t"].get("description"),
            "url":              r["t"].get("url"),
            "created":          r["t"].get("created"),
            "modified":         r["t"].get("modified"),
            "platforms":        r["t"].get("platforms", []),
            "dataSources":      r["t"].get("dataSources", []),
            "defenseBypass":    r["t"].get("defenseBypass", []),
            "permissions":      r["t"].get("permissions", []),
            "isSubtechnique":   r["t"].get("isSubtechnique", False),
            "parentId":         r["t"].get("parentId"),
            "severity":         r["t"].get("severity", "MEDIUM"),
            "detections":       r["t"].get("detections", 0),
            # Tactics
            "tacticIds":        [i for i in r["tacticIds"]   if i],
            "tacticNames":      [n for n in r["tacticNames"] if n],
            "tactic":           r["tacticNames"][0] if r["tacticNames"] else r["t"].get("tactic"),
            # Groups
            "groupCount":       r["groupCount"],
            "groupIds":         [i for i in r["groupIds"]   if i],
            "groupNames":       [n for n in r["groupNames"] if n],
            # Software
            "softwareCount":    r["softwareCount"],
            "softwareIds":      [i for i in r["softwareIds"]   if i],
            "softwareNames":    [n for n in r["softwareNames"] if n],
            # Mitigations
            "mitigationCount":  r["mitigationCount"],
            "mitigationIds":    [i for i in r["mitigationIds"]   if i],
            "mitigationNames":  [n for n in r["mitigationNames"] if n],
            # Subtechniques
            "subtechniqueCount": r["subtechniqueCount"],
            "subtechniqueIds":   [i for i in r["subtechniqueIds"] if i],
        }
        for r in rows
    ]


    
# CAMPAIGNS
    

@router.get("/campaigns")
def get_campaigns():
    query = """
    MATCH (c:MitreAttackCampaign)
    OPTIONAL MATCH (c)--(g:MitreAttackGroup)
    OPTIONAL MATCH (c)--(t:MitreAttackTechnique)
    OPTIONAL MATCH (c)--(s:MitreAttackSoftware)

    RETURN c,
           collect(DISTINCT g.id)   AS groupIds,
           collect(DISTINCT g.name) AS groupNames,
           count(DISTINCT t)        AS techniqueCount,
           collect(DISTINCT t.id)   AS techniqueIds,
           collect(DISTINCT t.name) AS techniqueNames,
           count(DISTINCT s)        AS softwareCount,
           collect(DISTINCT s.id)   AS softwareIds,
           collect(DISTINCT s.name) AS softwareNames
    """

    rows = run_query(query)

    return [
        {
            **node_props(r["c"]),
            "id":             r["c"].get("id"),
            "name":           r["c"].get("name"),
            "description":    r["c"].get("description"),
            "url":            r["c"].get("url"),
            "created":        r["c"].get("created"),
            "modified":       r["c"].get("modified"),
            "year":           r["c"].get("year"),
            "firstSeen":      r["c"].get("firstSeen"),
            "lastSeen":       r["c"].get("lastSeen"),
            "targets":        r["c"].get("targets", []),
            "status":         r["c"].get("status", "UNKNOWN"),
            # Groups
            "groupIds":       [i for i in r["groupIds"]   if i],
            "groupNames":     [n for n in r["groupNames"] if n],
            # Techniques
            "techniqueCount": r["techniqueCount"],
            "techniqueIds":   [i for i in r["techniqueIds"]   if i],
            "techniqueNames": [n for n in r["techniqueNames"] if n],
            # Software
            "softwareCount":  r["softwareCount"],
            "softwareIds":    [i for i in r["softwareIds"]   if i],
            "softwareNames":  [n for n in r["softwareNames"] if n],
        }
        for r in rows
    ]


    
# TACTICS
    

@router.get("/tactics")
def get_tactics():
    query = """
    MATCH (ta:MitreAttackTactic)
    OPTIONAL MATCH (ta)--(t:MitreAttackTechnique)
    RETURN ta,
           count(DISTINCT t)        AS techniqueCount,
           collect(DISTINCT t.id)   AS techniqueIds,
           collect(DISTINCT t.name) AS techniqueNames
    ORDER BY techniqueCount DESC
    """

    rows = run_query(query)

    # Fallback: group by Technique.tactic property
    if not rows:
        query = """
        MATCH (t:MitreAttackTechnique)
        WHERE t.tactic IS NOT NULL
        RETURN t.tactic AS tactic,
               count(*) AS techniqueCount,
               collect(DISTINCT t.id)   AS techniqueIds,
               collect(DISTINCT t.name) AS techniqueNames
        ORDER BY techniqueCount DESC
        """
        fallback_rows = run_query(query)
        return [
            {
                "id":             None,
                "tactic":         r["tactic"],
                "name":           r["tactic"],
                "description":    None,
                "url":            None,
                "shortName":      None,
                "techniqueCount": r["techniqueCount"],
                "techniqueIds":   [i for i in r["techniqueIds"]   if i],
                "techniqueNames": [n for n in r["techniqueNames"] if n],
                "score":          min(100, r["techniqueCount"] * 4),
            }
            for r in fallback_rows
        ]

    return [
        {
            **node_props(r["ta"]),
            "id":             r["ta"].get("id"),
            "name":           r["ta"].get("name"),
            "tactic":         r["ta"].get("name"),
            "description":    r["ta"].get("description"),
            "url":            r["ta"].get("url"),
            "shortName":      r["ta"].get("shortName"),
            "created":        r["ta"].get("created"),
            "modified":       r["ta"].get("modified"),
            "techniqueCount": r["techniqueCount"],
            "techniqueIds":   [i for i in r["techniqueIds"]   if i],
            "techniqueNames": [n for n in r["techniqueNames"] if n],
            "score":          min(100, r["techniqueCount"] * 4),
        }
        for r in rows
    ]


    
# SOFTWARE
    

@router.get("/software")
def get_software():
    query = """
    MATCH (s:MitreAttackSoftware)
    OPTIONAL MATCH (s)--(t:MitreAttackTechnique)
    OPTIONAL MATCH (s)--(g:MitreAttackGroup)
    OPTIONAL MATCH (s)--(c:MitreAttackCampaign)

    RETURN s,
           count(DISTINCT t)        AS techniqueCount,
           collect(DISTINCT t.id)   AS techniqueIds,
           collect(DISTINCT t.name) AS techniqueNames,
           count(DISTINCT g)        AS groupCount,
           collect(DISTINCT g.id)   AS groupIds,
           collect(DISTINCT g.name) AS groupNames,
           count(DISTINCT c)        AS campaignCount,
           collect(DISTINCT c.id)   AS campaignIds,
           collect(DISTINCT c.name) AS campaignNames
    """

    rows = run_query(query)

    return [
        {
            **node_props(r["s"]),
            "id":             r["s"].get("id"),
            "name":           r["s"].get("name"),
            "type":           r["s"].get("type"),
            "description":    r["s"].get("description"),
            "url":            r["s"].get("url"),
            "created":        r["s"].get("created"),
            "modified":       r["s"].get("modified"),
            "aliases":        r["s"].get("aliases", []),
            "platforms":      r["s"].get("platforms", []),
            "version":        r["s"].get("version"),
            # Techniques
            "techniqueCount": r["techniqueCount"],
            "techniqueIds":   [i for i in r["techniqueIds"]   if i],
            "techniqueNames": [n for n in r["techniqueNames"] if n],
            # Groups
            "groupCount":     r["groupCount"],
            "groupIds":       [i for i in r["groupIds"]   if i],
            "groupNames":     [n for n in r["groupNames"] if n],
            # Campaigns
            "campaignCount":  r["campaignCount"],
            "campaignIds":    [i for i in r["campaignIds"]   if i],
            "campaignNames":  [n for n in r["campaignNames"] if n],
        }
        for r in rows
    ]


    
# MITIGATIONS
    

@router.get("/mitigations")
def get_mitigations():
    query = """
    MATCH (m:MitreAttackMitigation)
    OPTIONAL MATCH (m)--(t:MitreAttackTechnique)

    RETURN m,
           count(DISTINCT t)        AS techniqueCount,
           collect(DISTINCT t.id)   AS techniqueIds,
           collect(DISTINCT t.name) AS techniqueNames,
           collect(DISTINCT t.tactic) AS tacticsCovered
    """

    rows = run_query(query)

    return [
        {
            **node_props(r["m"]),
            "id":              r["m"].get("id"),
            "name":            r["m"].get("name"),
            "description":     r["m"].get("description"),
            "url":             r["m"].get("url"),
            "created":         r["m"].get("created"),
            "modified":        r["m"].get("modified"),
            # Techniques
            "techniqueCount":  r["techniqueCount"],
            "techniqueIds":    [i for i in r["techniqueIds"]   if i],
            "techniqueNames":  [n for n in r["techniqueNames"] if n],
            "tacticsCovered":  [t for t in r["tacticsCovered"] if t],
        }
        for r in rows
    ]


    
# ALERTS
    

@router.get("/alerts")
def get_alerts(limit: int = Query(20, ge=1, le=100)):
    query = """
    MATCH (a:Alert)
    OPTIONAL MATCH (a)--(t:MitreAttackTechnique)
    OPTIONAL MATCH (a)--(g:MitreAttackGroup)
    OPTIONAL MATCH (a)--(ta:MitreAttackTactic)

    RETURN a,
           t.id   AS techniqueId,
           t.name AS techniqueName,
           g.id   AS groupId,
           g.name AS groupName,
           ta.name AS tacticName
    ORDER BY a.timestamp DESC
    LIMIT $limit
    """

    rows = run_query(query, {"limit": limit})

    return [
        {
            **node_props(r["a"]),
            "id":            r["a"].get("id"),
            "severity":      r["a"].get("severity"),
            "msg":           r["a"].get("msg"),
            "message":       r["a"].get("message") or r["a"].get("msg"),
            "timestamp":     r["a"].get("timestamp"),
            "time":          r["a"].get("time") or r["a"].get("timestamp"),
            "source":        r["a"].get("source"),
            "destination":   r["a"].get("destination"),
            "status":        r["a"].get("status"),
            "raw":           r["a"].get("raw"),
            # Related entities resolved from relationships (preferred) or stored property
            "techniqueId":   r.get("techniqueId")  or r["a"].get("techniqueId"),
            "techniqueName": r.get("techniqueName") or r["a"].get("techniqueName"),
            "groupId":       r.get("groupId")   or r["a"].get("groupId"),
            "group":         r.get("groupName") or r["a"].get("group"),
            "tactic":        r.get("tacticName") or r["a"].get("tactic"),
        }
        for r in rows
    ]


    
# TIMELINE
    

@router.get("/timeline")
def get_timeline():
    # Detection nodes
    query = """
    MATCH (d:Detection)
    WHERE d.timestamp IS NOT NULL
    WITH date(d.timestamp) AS day,
         count(*) AS detections,
         collect(DISTINCT d.severity) AS severities,
         collect(DISTINCT d.techniqueId) AS techniqueIds
    RETURN toString(day) AS day,
           detections,
           severities,
           techniqueIds
    ORDER BY day
    """
    rows = run_query(query)

    # Fallback to Alert nodes
    if not rows:
        query = """
        MATCH (a:Alert)
        WHERE a.timestamp IS NOT NULL
        WITH date(a.timestamp) AS day,
             count(*) AS detections,
             collect(DISTINCT a.severity) AS severities,
             collect(DISTINCT a.techniqueId) AS techniqueIds
        RETURN toString(day) AS day,
               detections,
               severities,
               techniqueIds
        ORDER BY day
        """
        rows = run_query(query)

    return [
        {
            "day":          r["day"],
            "detections":   r["detections"],
            "severities":   [s for s in r.get("severities", []) if s],
            "techniqueIds": [t for t in r.get("techniqueIds", []) if t],
        }
        for r in rows
    ]


    
# STATS
    

@router.get("/stats")
def get_stats():
    labels = [
        ("MitreAttackTechnique",  "techniques"),
        ("MitreAttackGroup",      "groups"),
        ("MitreAttackSoftware",   "software"),
        ("MitreAttackCampaign",   "campaigns"),
        ("MitreAttackMitigation", "mitigations"),
        ("MitreAttackTactic",     "tactics"),
        ("Alert",                 "alerts"),
        ("Detection",             "detections"),
    ]

    counts = {}
    for label, key in labels:
        rows = run_query(f"MATCH (n:{label}) RETURN count(n) AS count")
        counts[key] = rows[0]["count"] if rows else 0

    # Relationship counts
    rel_rows = run_query("MATCH ()-[r]->() RETURN count(r) AS count")
    counts["relationships"] = rel_rows[0]["count"] if rel_rows else 0

    # High-severity alert count
    hs_rows = run_query(
        "MATCH (a:Alert) WHERE a.severity IN ['HIGH','CRITICAL'] RETURN count(a) AS count"
    )
    counts["highSeverityAlerts"] = hs_rows[0]["count"] if hs_rows else 0

    return counts


    
# RELATIONSHIPS  (new – generic graph traversal endpoint)
    

@router.get("/relationships")
def get_relationships(
    node_id: str = Query(..., description="MITRE ATT&CK ID of the starting node"),
    depth:   int = Query(1, ge=1, le=3, description="Traversal depth (1–3)"),
):
    """Return all nodes and relationships reachable from a given node ID."""
    query = """
    MATCH path = (start)-[*1..$depth]-(end)
    WHERE start.id = $node_id
    UNWIND relationships(path) AS rel
    RETURN
        startNode(rel).id   AS sourceId,
        startNode(rel).name AS sourceName,
        labels(startNode(rel))[0] AS sourceLabel,
        type(rel)           AS relationship,
        endNode(rel).id     AS targetId,
        endNode(rel).name   AS targetName,
        labels(endNode(rel))[0] AS targetLabel
    """
    rows = run_query(query, {"node_id": node_id, "depth": depth})
    return rows


    
# SEARCH  (new – cross-entity full-text search)
    

@router.get("/search")
def search(
    q:     str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(50, ge=1, le=200),
):
    """Case-insensitive substring search across all major entity types."""
    query = """
    CALL {
        MATCH (n:MitreAttackGroup)      WHERE toLower(n.name) CONTAINS toLower($q) OR toLower(coalesce(n.alias,'')) CONTAINS toLower($q)
        RETURN n AS node, 'Group'     AS entityType LIMIT $limit
        UNION
        MATCH (n:MitreAttackTechnique)  WHERE toLower(n.name) CONTAINS toLower($q) OR toLower(coalesce(n.id,''))   CONTAINS toLower($q)
        RETURN n AS node, 'Technique' AS entityType LIMIT $limit
        UNION
        MATCH (n:MitreAttackCampaign)   WHERE toLower(n.name) CONTAINS toLower($q)
        RETURN n AS node, 'Campaign'  AS entityType LIMIT $limit
        UNION
        MATCH (n:MitreAttackSoftware)   WHERE toLower(n.name) CONTAINS toLower($q)
        RETURN n AS node, 'Software'  AS entityType LIMIT $limit
        UNION
        MATCH (n:MitreAttackMitigation) WHERE toLower(n.name) CONTAINS toLower($q)
        RETURN n AS node, 'Mitigation' AS entityType LIMIT $limit
        UNION
        MATCH (n:MitreAttackTactic)     WHERE toLower(n.name) CONTAINS toLower($q)
        RETURN n AS node, 'Tactic'    AS entityType LIMIT $limit
    }
    RETURN node, entityType
    LIMIT $limit
    """
    rows = run_query(query, {"q": q, "limit": limit})

    return [
        {
            **node_props(r["node"]),
            "entityType": r["entityType"],
        }
        for r in rows
    ]


    
# HEALTH CHECK
    

@router.get("/health")
def health():
    try:
        rows = run_query("RETURN 1 AS ok")
        db_ok = bool(rows and rows[0].get("ok") == 1)
    except Exception:
        db_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok}
