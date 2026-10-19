"""
keep_phantom_tool_registry.py
────────────────────────
PHANTOM v3.0 — Optimised tool registry.

Key improvements vs v2.0:
  • TOOLS built programmatically — zero repetition, easy to extend
  • O(1) tool name → schema lookup via TOOL_MAP
  • REL_TYPES exposed as a frozenset for fast membership checks
  • TACTIC_ORDER as tuple (immutable, hashable)
  • _param() / _func() helpers eliminate copy-paste schema boilerplate
  • Tool schema string interpolation replaced by direct object reuse
  • Added TOOL_NAMES set for guard-clause checks in the agent loop
"""

from __future__ import annotations

# ── Kill-chain tactic order ────────────────────────────────────────────────────
TACTIC_ORDER: tuple[str, ...] = (
    "Reconnaissance", "Resource Development", "Initial Access", "Execution",
    "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access",
    "Discovery", "Lateral Movement", "Collection", "Command and Control",
    "Exfiltration", "Impact",
)

# ── Ontolocy node labels ───────────────────────────────────────────────────────
GROUP          = "MitreAttackGroup"
TECHNIQUE      = "MitreAttackTechnique"
SOFTWARE       = "MitreAttackSoftware"
CAMPAIGN       = "MitreAttackCampaign"
TACTIC         = "MitreAttackTactic"
MITIGATION     = "MitreAttackMitigation"
DATA_SOURCE    = "MitreAttackDataSource"
DATA_COMPONENT = "MitreAttackDataComponent"

# ── Ontolocy relationship types — frozenset for O(1) membership test ──────────
REL_TYPES: frozenset[str] = frozenset({
    "MITRE_TACTIC_INCLUDES_TECHNIQUE",
    "MITRE_ATTACK_GROUP_USES_TECHNIQUE",
    "MITRE_ATTACK_GROUP_USES_SOFTWARE",
    "MITRE_SUBTECHNIQUE_OF",
    "MITRE_CAMPAIGN_USES_SOFTWARE",
    "MITRE_CAMPAIGN_ATTRIBUTED_TO_INTRUSION_SET",
    "MITRE_CAMPAIGN_USES_TECHNIQUE",
    "MITRE_SOFTWARE_USES_TECHNIQUE",
    "MITRE_ATTACK_MITIGATION_DEFENDS_AGAINST_TECHNIQUE",
    "MITRE_ATTACK_DATA_COMPONENT_DETECTS_TECHNIQUE",
    "MITRE_ATTACK_DATA_SOURCE_HAS_COMPONENT",
})
REL_TYPES_LIST: list[str] = sorted(REL_TYPES)  # stable order for JSON Schema enum

# ── Platform options (shared across tools) ────────────────────────────────────
_PLATFORMS: list[str] = [
    "Windows", "macOS", "Linux", "Cloud", "Containers",
    "Network", "IaaS", "SaaS", "Office 365", "Azure AD", "PRE",
]

# ── Shared schema fragments ────────────────────────────────────────────────────
_MAX_RESULTS_PARAM = {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
_TECH_ID_PATTERN   = r"^T\d{4}(\.\d{3})?$"

def _func(name: str, description: str, parameters: dict) -> dict:
    """Wrap a function schema in the Ollama tool envelope."""
    return {
        "type": "function",
        "function": {"name": name, "description": description, "parameters": parameters},
    }

def _params(
    required: list[str] | None = None,
    **properties: dict,
) -> dict:
    schema: dict = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

TOOLS: list[dict] = [

    # 1 ── ACTOR PROFILE ───────────────────────────────────────────────────────
    _func(
        "get_threat_actor_profile",
        (
            "Full ATT&CK intelligence profile for a named threat actor/APT. "
            "Returns nation, motivation, sectors, risk score, STIX ID, all techniques "
            "with procedure text & citations, software with usage context, attributed campaigns. "
            "CALL WHEN: analyst names a group or asks 'who is behind X'."
        ),
        _params(
            required=["actor_name"],
            actor_name={
                "type": "string",
                "description": "Canonical actor name or alias (e.g. 'APT28', 'Lazarus'). Partial/alias matching supported.",
            },
        ),
    ),

    # 2 ── LIST ACTORS ─────────────────────────────────────────────────────────
    _func(
        "list_threat_actors",
        (
            "Enumerate MitreAttackGroup nodes with optional nation/motivation filters. "
            "Returns name, aliases, STIX ID, domains, technique count, risk score, "
            "first/last seen, target sectors. "
            "CALL WHEN: landscape overview, 'show all Chinese APTs', building shortlist."
        ),
        _params(
            nation={
                "type": "string",
                "description": "Filter by nation attribution, e.g. 'Russia', 'China', 'Iran', 'North Korea'.",
            },
            motivation={
                "type": "string",
                "enum": ["espionage", "financial", "destructive", "hacktivism", "unknown"],
            },
            top_n={"type": "integer", "default": 15, "minimum": 1, "maximum": 100},
            sort_by={
                "type": "string",
                "enum": ["risk_score", "last_seen", "technique_count"],
                "default": "risk_score",
            },
        ),
    ),

    # 3 ── COMPARE ACTORS ──────────────────────────────────────────────────────
    _func(
        "compare_actors",
        (
            "Side-by-side comparison of two MitreAttackGroup nodes. "
            "Returns shared & unique TTPs, Jaccard similarity, software/sector/campaign overlap. "
            "CALL WHEN: attribution disambiguation or explicit comparison request."
        ),
        _params(
            required=["actor1", "actor2"],
            actor1={"type": "string"},
            actor2={"type": "string"},
            focus={
                "type": "string",
                "enum": ["ttps", "malware", "targets", "all"],
                "default": "all",
            },
        ),
    ),

    # 4 ── SEARCH TECHNIQUES ───────────────────────────────────────────────────
    _func(
        "search_techniques",
        (
            "Search MitreAttackTechnique by name, ID (T####.###), keyword, tactic, or platform. "
            "Returns technique ID, name, tactic, platforms, ATT&CK domains, detection notes, "
            "description, sub-technique list, last modified. "
            "CALL WHEN: before discussing any TTP; detection rule build; kill-chain mapping."
        ),
        _params(
            required=["query"],
            query={"type": "string", "description": "Technique name, ID (e.g. T1059), or keyword."},
            tactic={"type": "string", "enum": list(TACTIC_ORDER), "description": "Restrict to one ATT&CK tactic phase."},
            platform={"type": "string", "enum": _PLATFORMS},
            max_results=_MAX_RESULTS_PARAM,
        ),
    ),

    # 5 ── TECHNIQUE DETAIL ────────────────────────────────────────────────────
    _func(
        "get_technique_detail",
        (
            "Deep dive on a single MitreAttackTechnique. Returns mitigations with application notes, "
            "data components/sources, sub-technique hierarchy, real-world procedures with citations. "
            "CALL WHEN: detection engineering, hunt hypothesis, technique deep-dive."
        ),
        _params(
            required=["technique_id"],
            technique_id={
                "type": "string",
                "pattern": _TECH_ID_PATTERN,
                "description": "ATT&CK ID, e.g. T1059 or T1059.001.",
            },
            include_procedures={"type": "boolean", "default": True},
            include_mitigations={"type": "boolean", "default": True},
            include_data_sources={"type": "boolean", "default": True},
            include_sub_techniques={"type": "boolean", "default": True},
            procedure_limit={"type": "integer", "default": 20, "minimum": 1, "maximum": 50},
        ),
    ),

    # 6 ── KILL-CHAIN ANALYSIS ─────────────────────────────────────────────────
    _func(
        "get_kill_chain_analysis",
        (
            "Full ATT&CK kill-chain coverage map for an actor or technique set. "
            "Provide actor_name OR technique_ids — NEVER both. "
            "Returns tactic breakdown (kill-chain ordered), coverage %, gap tactics, "
            "top-5 detection-gap priorities, heatmap dict. "
            "CALL WHEN: coverage/gap analysis, hunt prioritisation."
        ),
        _params(
            actor_name={"type": "string", "description": "Mutually exclusive with technique_ids."},
            technique_ids={
                "type": "array",
                "items": {"type": "string", "pattern": _TECH_ID_PATTERN},
                "minItems": 1,
                "maxItems": 200,
                "description": "Explicit technique list — mutually exclusive with actor_name.",
            },
            highlight_gaps={"type": "boolean", "default": True},
        ),
    ),

    # 7 ── SEARCH SOFTWARE ─────────────────────────────────────────────────────
    _func(
        "search_software",
        (
            "Search MitreAttackSoftware (malware + tools). "
            "Returns ID, name, type, platforms, groups using it, techniques it employs, first/last seen. "
            "CALL WHEN: malware triage, 'what does Mimikatz do', tool identification."
        ),
        _params(
            required=["query"],
            query={"type": "string"},
            software_type={"type": "string", "enum": ["malware", "tool", "any"], "default": "any"},
            max_results=_MAX_RESULTS_PARAM,
        ),
    ),

    # 8 ── SEARCH CAMPAIGNS ────────────────────────────────────────────────────
    _func(
        "search_campaigns",
        (
            "Search MitreAttackCampaign nodes. "
            "Returns ID, name, first/last seen, description, attributed groups, techniques used. "
            "CALL WHEN: 'what campaigns has APT29 run', incident-to-campaign mapping."
        ),
        _params(
            required=["query"],
            query={"type": "string"},
            max_results=_MAX_RESULTS_PARAM,
        ),
    ),

    # 9 ── TRAVERSE GRAPH ──────────────────────────────────────────────────────
    _func(
        "traverse_attack_graph",
        (
            "Agentic multi-hop traversal over the Ontolocy ATT&CK graph. "
            "Follows relationship types from starting entity up to `depth` hops. "
            "Returns every path (node chain + rel types per hop). "
            "CALL WHEN: depth > 2 multi-entity reasoning, e.g. "
            "'mitigations for Lazarus techniques', 'telemetry covering FIN7 malware TTPs'."
        ),
        _params(
            required=["entity_name", "start_label", "relationships"],
            entity_name={"type": "string", "description": "Starting entity name or alias."},
            start_label={"type": "string", "enum": [GROUP, TECHNIQUE, SOFTWARE, CAMPAIGN, TACTIC]},
            relationships={
                "type": "array",
                "items": {"type": "string", "enum": REL_TYPES_LIST},
                "minItems": 1,
                "maxItems": 5,
                "description": "Ordered list of Ontolocy relationship types to follow.",
            },
            depth={"type": "integer", "default": 2, "minimum": 1, "maximum": 4},
        ),
    ),

    # 10 ── GRAPH ANALYTICS ────────────────────────────────────────────────────
    _func(
        "run_graph_analytics",
        (
            "Neo4j GDS analytics over the ATT&CK graph. "
            "pagerank → centrality ranking. similarity → pairwise Jaccard clustering. "
            "CALL WHEN: 'most widely used techniques', 'APTs most similar to Lazarus'."
        ),
        _params(
            required=["algorithm"],
            algorithm={"type": "string", "enum": ["pagerank", "similarity"]},
            node_label={"type": "string", "enum": [GROUP, TECHNIQUE, SOFTWARE, CAMPAIGN], "default": TECHNIQUE},
            limit={"type": "integer", "default": 20, "minimum": 5, "maximum": 100},
        ),
    ),

    # 11 ── HUNT HYPOTHESIS ────────────────────────────────────────────────────
    _func(
        "generate_hunt_hypothesis",
        (
            "Structured, evidence-grounded threat-hunting hypothesis. "
            "Returns hypothesis, ATT&CK mapping, required data sources/components, "
            "detection logic (Sigma/KQL/SPL/EQL), FP considerations, prioritised playbook. "
            "CALL WHEN: analyst requests hunt plan or detection rule set."
        ),
        _params(
            required=["threat_context"],
            threat_context={
                "type": "string",
                "description": "Free-text: actor, technique, incident context, or observable behaviour.",
            },
            environment={
                "type": "string",
                "enum": ["windows_ad", "cloud_aws", "cloud_azure", "cloud_gcp",
                         "linux_server", "ot_ics", "hybrid", "unknown"],
                "default": "unknown",
            },
            output_format={
                "type": "string",
                "enum": ["sigma", "kql", "spl", "eql", "pseudo"],
                "default": "sigma",
            },
        ),
    ),

    # 12 ── PCAP CONTEXT ───────────────────────────────────────────────────────
    _func(
        "search_pcap_context",
        (
            "Semantic vector search over ingested PCAP telemetry. "
            "Returns packet summaries, flow metadata, timestamps, relevance scores. "
            "CALL WHEN: PCAP loaded + analyst asks about observed network activity."
        ),
        _params(
            required=["query"],
            query={"type": "string"},
            top_k={"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
            protocol_filter={
                "type": "string",
                "enum": ["tcp", "udp", "dns", "http", "https",
                         "smb", "rdp", "icmp", "ftp", "ssh", "any"],
                "default": "any",
            },
        ),
    ),
]

# ── O(1) lookup helpers ────────────────────────────────────────────────────────
TOOL_MAP:   dict[str, dict] = {t["function"]["name"]: t for t in TOOLS}
TOOL_NAMES: frozenset[str]  = frozenset(TOOL_MAP)
