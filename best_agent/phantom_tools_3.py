

from __future__ import annotations

# ── Kill-chain tactic order ────────────────────────────────────────────────────
TACTIC_ORDER = [
    "Reconnaissance", "Resource Development", "Initial Access", "Execution",
    "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access",
    "Discovery", "Lateral Movement", "Collection", "Command and Control",
    "Exfiltration", "Impact",
]

# ── Ontolocy node labels ───────────────────────────────────────────────────────
GROUP          = "MitreAttackGroup"
TECHNIQUE      = "MitreAttackTechnique"
SOFTWARE       = "MitreAttackSoftware"
CAMPAIGN       = "MitreAttackCampaign"
TACTIC         = "MitreAttackTactic"
MITIGATION     = "MitreAttackMitigation"
DATA_SOURCE    = "MitreAttackDataSource"
DATA_COMPONENT = "MitreAttackDataComponent"

# ── Ontolocy relationship types ────────────────────────────────────────────────
REL_TYPES = [
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
]

# =============================================================================
# TOOL DEFINITIONS  (Ollama-compatible strict JSON Schema)
# =============================================================================

TOOLS: list[dict] = [

    # ── 1. ACTOR PROFILE ──────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_threat_actor_profile",
            "description": (
                "Full ATT&CK intelligence profile for a named threat actor / APT group. "
                "Returns: nation, motivation, target sectors, risk score, STIX ID, ATT&CK domains, "
                "ALL techniques with procedure text & citations "
                "(via MITRE_ATTACK_GROUP_USES_TECHNIQUE edges), "
                "associated software with usage context "
                "(via MITRE_ATTACK_GROUP_USES_SOFTWARE edges), "
                "and attributed campaigns "
                "(via MITRE_CAMPAIGN_ATTRIBUTED_TO_INTRUSION_SET edges). "
                "CALL WHEN: analyst names a group or asks 'who is behind X'."
            ),
            "parameters": {
                "type": "object",
                "required": ["actor_name"],
                "properties": {
                    "actor_name": {
                        "type": "string",
                        "description": (
                            "Canonical actor name or alias, e.g. 'APT28', 'Lazarus', "
                            "'Sandworm', 'FIN7'. Partial / alias matching is supported."
                        ),
                    }
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 2. LIST ACTORS ────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_threat_actors",
            "description": (
                "Enumerate MitreAttackGroup nodes with optional nation / motivation filters. "
                "Returns name, aliases, STIX ID, domains, technique count, risk score, "
                "first/last seen, target sectors. "
                "CALL WHEN: landscape overview, 'show all Chinese APTs', building shortlist."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nation": {
                        "type": "string",
                        "description": "Filter by nation attribution, e.g. 'Russia', 'China', 'Iran', 'North Korea'.",
                    },
                    "motivation": {
                        "type": "string",
                        "enum": ["espionage", "financial", "destructive", "hacktivism", "unknown"],
                    },
                    "top_n":   {"type": "integer", "default": 15, "minimum": 1, "maximum": 100},
                    "sort_by": {
                        "type": "string",
                        "enum": ["risk_score", "last_seen", "technique_count"],
                        "default": "risk_score",
                    },
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 3. COMPARE ACTORS ─────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "compare_actors",
            "description": (
                "Side-by-side comparison of two MitreAttackGroup nodes. "
                "Returns: shared & unique TTPs, Jaccard similarity score, "
                "software overlap, sector overlap, campaign overlap. "
                "CALL WHEN: attribution disambiguation or explicit comparison request."
            ),
            "parameters": {
                "type": "object",
                "required": ["actor1", "actor2"],
                "properties": {
                    "actor1": {"type": "string"},
                    "actor2": {"type": "string"},
                    "focus": {
                        "type": "string",
                        "enum": ["ttps", "malware", "targets", "all"],
                        "default": "all",
                    },
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 4. SEARCH TECHNIQUES ──────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_techniques",
            "description": (
                "Search MitreAttackTechnique nodes by name, ID (T####.###), keyword, "
                "tactic, or platform. "
                "Returns technique ID, name, tactic, platforms, ATT&CK domains, "
                "detection notes, description, sub-technique list, last modified. "
                "CALL WHEN: before discussing any TTP; detection rule build; kill-chain mapping."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Technique name, ID (e.g. T1059), or keyword.",
                    },
                    "tactic": {
                        "type": "string",
                        "enum": TACTIC_ORDER,
                        "description": "Optional: restrict to one ATT&CK tactic phase.",
                    },
                    "platform": {
                        "type": "string",
                        "enum": [
                            "Windows", "macOS", "Linux", "Cloud", "Containers",
                            "Network", "IaaS", "SaaS", "Office 365", "Azure AD", "PRE",
                        ],
                    },
                    "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 5. TECHNIQUE DETAIL ───────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_technique_detail",
            "description": (
                "Deep dive on a single MitreAttackTechnique. Returns: "
                "mitigations with application notes "
                "(MITRE_ATTACK_MITIGATION_DEFENDS_AGAINST_TECHNIQUE), "
                "data components / sources for detection "
                "(MITRE_ATTACK_DATA_COMPONENT_DETECTS_TECHNIQUE, "
                " MITRE_ATTACK_DATA_SOURCE_HAS_COMPONENT), "
                "sub-technique hierarchy (MITRE_SUBTECHNIQUE_OF), "
                "and real-world procedure examples with citations from groups, "
                "software, and campaigns. "
                "CALL WHEN: detection engineering, hunt hypothesis, technique deep-dive."
            ),
            "parameters": {
                "type": "object",
                "required": ["technique_id"],
                "properties": {
                    "technique_id": {
                        "type": "string",
                        "pattern": r"^T\d{4}(\.\d{3})?$",
                        "description": "ATT&CK ID, e.g. T1059 or T1059.001.",
                    },
                    "include_procedures":     {"type": "boolean", "default": True},
                    "include_mitigations":    {"type": "boolean", "default": True},
                    "include_data_sources":   {"type": "boolean", "default": True},
                    "include_sub_techniques": {"type": "boolean", "default": True},
                    "procedure_limit":        {"type": "integer", "default": 20, "minimum": 1, "maximum": 50},
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 6. KILL-CHAIN ANALYSIS ────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_kill_chain_analysis",
            "description": (
                "Build a full ATT&CK kill-chain coverage map for an actor or technique set. "
                "Provide actor_name OR technique_ids — never both. "
                "Returns: tactic-by-tactic breakdown (ordered by kill-chain), "
                "coverage %, gap tactics, top-5 detection-gap priorities, heatmap dict. "
                "Traverses MITRE_TACTIC_INCLUDES_TECHNIQUE and "
                "MITRE_ATTACK_GROUP_USES_TECHNIQUE relationships. "
                "CALL WHEN: coverage assessment, gap analysis, hunt prioritisation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "actor_name": {
                        "type": "string",
                        "description": "Actor name — mutually exclusive with technique_ids.",
                    },
                    "technique_ids": {
                        "type": "array",
                        "items": {"type": "string", "pattern": r"^T\d{4}(\.\d{3})?$"},
                        "minItems": 1,
                        "maxItems": 200,
                        "description": "Explicit technique list — mutually exclusive with actor_name.",
                    },
                    "highlight_gaps": {"type": "boolean", "default": True},
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 7. SEARCH SOFTWARE ────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_software",
            "description": (
                "Search MitreAttackSoftware nodes (malware and tools). "
                "Returns: software ID, name, type, platforms, STIX ID, "
                "groups that use it (MITRE_ATTACK_GROUP_USES_SOFTWARE), "
                "techniques it employs (MITRE_SOFTWARE_USES_TECHNIQUE), "
                "first/last seen. "
                "CALL WHEN: malware triage, 'what does Mimikatz do', tool identification."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "software_type": {
                        "type": "string",
                        "enum": ["malware", "tool", "any"],
                        "default": "any",
                    },
                    "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 8. SEARCH CAMPAIGNS ───────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_campaigns",
            "description": (
                "Search MitreAttackCampaign nodes. "
                "Returns: campaign ID, name, first/last seen, description, STIX ID, "
                "attributed groups (MITRE_CAMPAIGN_ATTRIBUTED_TO_INTRUSION_SET), "
                "techniques used (MITRE_CAMPAIGN_USES_TECHNIQUE). "
                "CALL WHEN: 'what campaigns has APT29 run', incident-to-campaign mapping."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query":       {"type": "string"},
                    "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 9. TRAVERSE GRAPH ─────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "traverse_attack_graph",
            "description": (
                "Agentic multi-hop traversal over the Ontolocy ATT&CK graph. "
                "Follows specified Ontolocy relationship types from a starting entity "
                "up to `depth` hops. Returns every path (node chain + rel types per hop). "
                "CALL WHEN: complex multi-entity reasoning, e.g. "
                "'mitigations for techniques used by Lazarus', "
                "'telemetry covering FIN7 malware techniques', "
                "'which campaigns used T1059.001'."
            ),
            "parameters": {
                "type": "object",
                "required": ["entity_name", "start_label", "relationships"],
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "description": "Starting entity name or alias.",
                    },
                    "start_label": {
                        "type": "string",
                        "enum": [GROUP, TECHNIQUE, SOFTWARE, CAMPAIGN, TACTIC],
                        "description": "Ontolocy node label of the starting entity.",
                    },
                    "relationships": {
                        "type": "array",
                        "items": {"type": "string", "enum": REL_TYPES},
                        "minItems": 1,
                        "maxItems": 5,
                        "description": "Ordered list of Ontolocy relationship types to follow.",
                    },
                    "depth": {
                        "type": "integer",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 4,
                        "description": "Maximum traversal depth (hops).",
                    },
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 10. GRAPH ANALYTICS ───────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "run_graph_analytics",
            "description": (
                "Run Neo4j GDS analytics over the ATT&CK graph. "
                "pagerank   → centrality ranking of high-impact techniques or actors. "
                "similarity → pairwise Jaccard clustering by TTP overlap. "
                "CALL WHEN: 'most widely used techniques', "
                "'which APTs are most similar to Lazarus', emerging TTP trends."
            ),
            "parameters": {
                "type": "object",
                "required": ["algorithm"],
                "properties": {
                    "algorithm": {
                        "type": "string",
                        "enum": ["pagerank", "similarity"],
                    },
                    "node_label": {
                        "type": "string",
                        "enum": [GROUP, TECHNIQUE, SOFTWARE, CAMPAIGN],
                        "default": TECHNIQUE,
                    },
                    "limit": {"type": "integer", "default": 20, "minimum": 5, "maximum": 100},
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 11. HUNT HYPOTHESIS ───────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "generate_hunt_hypothesis",
            "description": (
                "Generate a structured, evidence-grounded threat-hunting hypothesis. "
                "Returns: hypothesis statement, ATT&CK mapping, required "
                "MitreAttackDataSource / MitreAttackDataComponent telemetry, "
                "detection logic (Sigma / KQL / SPL / EQL), "
                "false-positive considerations, prioritised playbook. "
                "CALL WHEN: analyst requests a hunt plan or detection rule set."
            ),
            "parameters": {
                "type": "object",
                "required": ["threat_context"],
                "properties": {
                    "threat_context": {
                        "type": "string",
                        "description": (
                            "Free-text description: actor, technique, incident context, "
                            "or observable behaviour to hunt for."
                        ),
                    },
                    "environment": {
                        "type": "string",
                        "enum": [
                            "windows_ad", "cloud_aws", "cloud_azure", "cloud_gcp",
                            "linux_server", "ot_ics", "hybrid", "unknown",
                        ],
                        "default": "unknown",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["sigma", "kql", "spl", "eql", "pseudo"],
                        "default": "sigma",
                    },
                },
                "additionalProperties": False,
            },
        },
    },

    # ── 12. PCAP CONTEXT ──────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_pcap_context",
            "description": (
                "Semantic vector search over ingested PCAP telemetry. "
                "Returns matching packet summaries, flow metadata, timestamps, "
                "relevance scores. "
                "CALL WHEN: PCAP data has been loaded and analyst asks about "
                "observed network activity or wants to correlate traffic with TTPs."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
                    "protocol_filter": {
                        "type": "string",
                        "enum": [
                            "tcp", "udp", "dns", "http", "https",
                            "smb", "rdp", "icmp", "ftp", "ssh", "any",
                        ],
                        "default": "any",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
]