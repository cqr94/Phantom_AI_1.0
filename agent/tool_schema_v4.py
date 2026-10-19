
from __future__ import annotations

   
# Kill-chain order (static, schema-safe)


TACTIC_ORDER = [
    "Reconnaissance",
    "Resource Development",
    "Initial Access",
    "Execution",
    "Persistence",
    "Privilege Escalation",
    "Defense Evasion",
    "Credential Access",
    "Discovery",
    "Lateral Movement",
    "Collection",
    "Command and Control",
    "Exfiltration",
    "Impact",
]

   
# Ontology labels (STATIC STRINGS ONLY — no runtime constants in schemas)
   

GROUP = "MitreAttackGroup"
TECHNIQUE = "MitreAttackTechnique"
SOFTWARE = "MitreAttackSoftware"
CAMPAIGN = "MitreAttackCampaign"
TACTIC = "MitreAttackTactic"

   
# Relationship types (STRICT ENUM — prevents graph traversal drift)
   

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

   
# GLOBAL SCHEMA PATTERNS (ANTI-HALLUCINATION / ANTI-NULL SAFETY)
   

TECHNIQUE_ID_PATTERN = r"^T\d{4}(\.\d{3})?$"

POSITIVE_INT = {"type": "integer", "minimum": 1, "maximum": 200}
LIMIT_INT = {"type": "integer", "minimum": 1, "maximum": 100}
SMALL_LIMIT_INT = {"type": "integer", "minimum": 1, "maximum": 50}

   
# TOOL DEFINITIONS
   

TOOLS: list[dict] = [

     
    # 1. ACTOR PROFILE (HARDENED)
     
    {
        "type": "function",
        "function": {
            "name": "get_threat_actor_profile",
            "description": (
                "Retrieve authoritative ATT&CK graph profile for a threat actor. "
                "STRICT: Do not infer actor existence; must match graph entity. "
                "Returns groups, techniques, software, campaigns, and citations."
            ),
            "parameters": {
                "type": "object",
                "required": ["actor_name"],
                "properties": {
                    "actor_name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 80,
                        "description": "APT/group name (e.g., APT28, FIN7). No technique IDs allowed.",
                    }
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 2. LIST ACTORS (SAFE PAGINATION)
     
    {
        "type": "function",
        "function": {
            "name": "list_threat_actors",
            "description": (
                "List ATT&CK groups with optional filters. Safe paginated retrieval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nation": {"type": "string", "maxLength": 40},
                    "motivation": {
                        "type": "string",
                        "enum": ["espionage", "financial", "destructive", "hacktivism", "unknown"],
                    },
                    "top_n": {
                        "type": "integer",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 50
                    },
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

 
    {
        "type": "function",
        "function": {
            "name": "compare_actors",
            "description": (
                "Compare two ATT&CK groups. Ensures deterministic similarity outputs."
            ),
            "parameters": {
                "type": "object",
                "required": ["actor1", "actor2"],
                "properties": {
                    "actor1": {"type": "string", "minLength": 1, "maxLength": 80},
                    "actor2": {"type": "string", "minLength": 1, "maxLength": 80},
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

   
    {
        "type": "function",
        "function": {
            "name": "search_techniques",
            "description": (
                "Search ATT&CK techniques. STRICT: only technique IDs allowed here. "
                "Prevents mixing software/actor identifiers."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 120,
                    },
                    "tactic": {
                        "type": "string",
                        "enum": TACTIC_ORDER,
                    },
                    "platform": {
                        "type": "string",
                        "enum": [
                            "Windows", "macOS", "Linux", "Cloud",
                            "Containers", "Network", "SaaS", "Azure AD", "PRE",
                        ],
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 25,
                    },
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 5. TECHNIQUE DETAIL (DEFENSIVE NULL-SAFE FLAGS)
     
    {
        "type": "function",
        "function": {
            "name": "get_technique_detail",
            "description": (
                "Deep ATT&CK technique enrichment. Returns mitigations, detections, "
                "data sources, and procedures. MUST NOT return null numeric fields."
            ),
            "parameters": {
                "type": "object",
                "required": ["technique_id"],
                "properties": {
                    "technique_id": {
                        "type": "string",
                        "pattern": TECHNIQUE_ID_PATTERN,
                        "description": "Valid ATT&CK ID only (T#### or T####.###).",
                    },
                    "include_procedures": {"type": "boolean", "default": True},
                    "include_mitigations": {"type": "boolean", "default": True},
                    "include_data_sources": {"type": "boolean", "default": True},
                    "include_sub_techniques": {"type": "boolean", "default": True},
                    "procedure_limit": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20,
                    },
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 6. KILL CHAIN ANALYSIS (FORCED SINGLE SOURCE OF TRUTH)
     
    {
        "type": "function",
        "function": {
            "name": "get_kill_chain_analysis",
            "description": (
                "ATT&CK kill-chain coverage analysis. Either actor OR technique_ids."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "actor_name": {
                        "type": "string",
                        "maxLength": 80,
                    },
                    "technique_ids": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": TECHNIQUE_ID_PATTERN,
                        },
                        "minItems": 1,
                        "maxItems": 100,
                    },
                    "highlight_gaps": {"type": "boolean", "default": True},
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 7. SOFTWARE SEARCH (STRICT DOMAIN SEPARATION FIX)
     
    {
        "type": "function",
        "function": {
            "name": "search_software",
            "description": (
                "Search malware/tools ONLY. STRICT: do not pass technique IDs."
            ),
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 120},
                    "software_type": {
                        "type": "string",
                        "enum": ["malware", "tool", "any"],
                        "default": "any",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 25,
                    },
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 8. CAMPAIGNS (SAFE RETRIEVAL)
     
    {
        "type": "function",
        "function": {
            "name": "search_campaigns",
            "description": "Search ATT&CK campaigns with attribution mapping.",
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1, "maxLength": 120},
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 25,
                    },
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 9. GRAPH TRAVERSAL (HARDENED AGAINST EXPLOSIVE QUERIES)
     
    {
        "type": "function",
        "function": {
            "name": "traverse_attack_graph",
            "description": (
                "Multi-hop graph traversal. STRICT: bounded depth + bounded edges."
            ),
            "parameters": {
                "type": "object",
                "required": ["entity_name", "start_label", "relationships"],
                "properties": {
                    "entity_name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 80,
                    },
                    "start_label": {
                        "type": "string",
                        "enum": [GROUP, TECHNIQUE, SOFTWARE, CAMPAIGN, TACTIC],
                    },
                    "relationships": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": REL_TYPES,
                        },
                        "minItems": 1,
                        "maxItems": 3,
                    },
                    "depth": {
                        "type": "integer",
                        "default": 2,
                        "minimum": 1,
                        "maximum": 3,
                    },
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 10. GRAPH ANALYTICS (SAFE LIMITS PREVENT NULL / OVERFLOW ERRORS)
     
    {
        "type": "function",
        "function": {
            "name": "run_graph_analytics",
            "description": "Run Neo4j GDS analytics safely with bounded outputs.",
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
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "minimum": 5,
                        "maximum": 50,
                    },
                },
                "additionalProperties": False,
            },
        },
    },

     
    # 11. HUNT HYPOTHESIS (FORCED STRUCTURED OUTPUT)
     
    {
        "type": "function",
        "function": {
            "name": "generate_hunt_hypothesis",
            "description": (
                "Generate structured hunt hypothesis with ATT&CK mapping."
            ),
            "parameters": {
                "type": "object",
                "required": ["threat_context"],
                "properties": {
                    "threat_context": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 500,
                    },
                    "environment": {
                        "type": "string",
                        "enum": [
                            "windows_ad", "cloud_aws", "cloud_azure",
                            "cloud_gcp", "linux_server", "hybrid", "unknown"
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

     
    # 12. PCAP SEARCH (SAFE VECTOR QUERY BOUNDING)
     
    {
        "type": "function",
        "function": {
            "name": "search_pcap_context",
            "description": "Vector search over PCAP telemetry with strict limits.",
            "parameters": {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
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