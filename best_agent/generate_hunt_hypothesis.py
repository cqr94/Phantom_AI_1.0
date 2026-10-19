from typing import Dict, List, Set

from utils.neo4_conn import run_neo4j


def generate_hunt_hypothesis(threat_context: str) -> Dict:
    """
    Generate ATT&CK-driven hunt hypotheses directly from Neo4j.

    Enhancements:
    - Fully graph-native
    - Wireshark display-filter compliant
    - Dynamic ATT&CK tactic correlation
    - PCAP-aware hunt generation
    - Detection engineering ready
    - Query deduplication
    - Risk scoring
    """

    context = threat_context.lower().strip()

    # =========================================================================
    # STEP 1 — Retrieve ATT&CK techniques from Neo4j
    # =========================================================================

    technique_query = """
    MATCH (t:MitreAttackTechnique)

    OPTIONAL MATCH (ta:MitreAttackTactic)-[:HAS_TECHNIQUE]->(t)
    OPTIONAL MATCH (m:MitreAttackMitigation)-[:MITIGATES]->(t)

    WHERE
        toLower(t.name) CONTAINS toLower($context)
        OR toLower(coalesce(t.description, "")) CONTAINS toLower($context)
        OR any(
            k IN coalesce(t.keywords, [])
            WHERE toLower($context) CONTAINS toLower(k)
        )

    RETURN
        t.external_id AS technique_id,
        t.name AS technique_name,
        t.description AS description,
        collect(DISTINCT ta.name) AS tactics,
        collect(DISTINCT {
            id: m.external_id,
            name: m.name
        }) AS mitigations

    LIMIT 15
    """

    rows = run_neo4j(
        technique_query,
        {"context": context}
    )

    if not rows:
        return {
            "found": False,
            "context": threat_context,
            "message": "No matching ATT&CK techniques identified."
        }

    # =========================================================================
    # STEP 2 — Build ATT&CK mappings
    # =========================================================================

    tactics: Set[str] = set()
    techniques: List[Dict] = []

    for row in rows:

        row_tactics = row.get("tactics", [])

        tactics.update(
            t for t in row_tactics if t
        )

        techniques.append({
            "id": row["technique_id"],
            "name": row["technique_name"],
            "description": row.get("description", ""),
            "mitigations": [
                m for m in row.get("mitigations", [])
                if m.get("id")
            ]
        })

    # =========================================================================
    # STEP 3 — Generate Wireshark display filters
    # =========================================================================

    wireshark_filters = set()
    hunt_queries = set()

    for tactic in tactics:

        t = tactic.lower()

        # ---------------------------------------------------------------------
        # INITIAL ACCESS
        # ---------------------------------------------------------------------

        if "initial access" in t:

            wireshark_filters.update({

                # Suspicious HTTP POST uploads
                'http.request.method == "POST"',

                # SMTP traffic
                'smtp',

                # Office docs over HTTP
                'http contains "docm" or http contains "xlsm"',

                # Suspicious URLs
                'http.request.uri matches "(?i)(login|verify|update|invoice)"',

                # Encoded payloads
                'http.file_data matches "[A-Za-z0-9+/]{100,}={0,2}"',
            })

            hunt_queries.update({
                "index=o365 attachment=true",
                "EventCode=4688 winword.exe spawning powershell.exe",
            })

        # ---------------------------------------------------------------------
        # EXECUTION
        # ---------------------------------------------------------------------

        elif "execution" in t:

            wireshark_filters.update({

                # PowerShell over HTTP
                'http contains "powershell"',

                # Encoded PowerShell
                'http matches "(?i)encodedcommand"',

                # Reverse shell indicators
                'tcp.port in {4444,5555,1337}',

                # Suspicious TLS SNI
                'tls.handshake.extensions_server_name matches "(?i)(temp|cdn|update)"',

                # Shell traffic
                'tcp.payload matches "(?i)(cmd.exe|powershell.exe|wget|curl)"',
            })

            hunt_queries.update({
                "Sysmon EventCode=1 powershell.exe",
                "EventCode=4688 cmd.exe",
            })

        # ---------------------------------------------------------------------
        # COMMAND & CONTROL
        # ---------------------------------------------------------------------

        elif "command and control" in t:

            wireshark_filters.update({

                # DNS tunneling
                'dns.qry.name.len > 50',

                # High entropy DNS
                'dns.qry.name matches "[A-Za-z0-9]{25,}"',

                # Beaconing
                'tcp.flags.syn == 1 && tcp.flags.ack == 0',

                # Tor traffic
                'tcp.port in {9001,9030,9050,9150}',

                # Suspicious user agents
                'http.user_agent matches "(?i)(curl|python|wget|powershell)"',

                # JA3/TLS anomalies
                'tls.handshake.type == 1',

                # ICMP tunneling
                'icmp.data',

                # Long DNS TXT records
                'dns.txt',
            })

            hunt_queries.update({
                "index=dns query_length > 50",
                "index=proxy user_agent IN (curl,wget,powershell)",
            })

        # ---------------------------------------------------------------------
        # EXFILTRATION
        # ---------------------------------------------------------------------

        elif "exfiltration" in t:

            wireshark_filters.update({

                # Large outbound payloads
                'tcp.len > 1400',

                # FTP uploads
                'ftp-data',

                # PUT uploads
                'http.request.method == "PUT"',

                # Suspicious ZIP/RAR transfers
                'http contains ".zip" or http contains ".rar"',

                # SMB transfers
                'smb2.write_length > 1000000',

                # DNS exfil
                'dns.qry.name.len > 80',

                # Non-RFC1918 outbound
                '!ip_rfc1918(ip.dst)',
            })

            hunt_queries.update({
                "bytes_out > 10000000",
                "large SMB transfer detection",
            })

        # ---------------------------------------------------------------------
        # LATERAL MOVEMENT
        # ---------------------------------------------------------------------

        elif "lateral movement" in t:

            wireshark_filters.update({

                # SMB
                'tcp.port == 445',

                # RDP
                'tcp.port == 3389',

                # WMI/DCOM
                'dcerpc',

                # PsExec indicators
                'smb contains "PSEXESVC"',

                # Remote service creation
                'smb2',

                # WinRM
                'tcp.port == 5985 or tcp.port == 5986',
            })

            hunt_queries.update({
                "EventCode=4624 LogonType=3",
                "SMB lateral movement activity",
            })

        # ---------------------------------------------------------------------
        # CREDENTIAL ACCESS
        # ---------------------------------------------------------------------

        elif "credential access" in t:

            wireshark_filters.update({

                # Kerberos
                'kerberos',

                # NTLM auth
                'ntlmssp',

                # LDAP auth
                'ldap',

                # Kerberoasting
                'kerberos.CNameString',

                # Excessive auth failures
                'tcp.port == 88',

                # SMB auth
                'smb2.session_setup_response',
            })

            hunt_queries.update({
                "LSASS access attempt",
                "Credential dumping behavior",
            })

        # ---------------------------------------------------------------------
        # DISCOVERY
        # ---------------------------------------------------------------------

        elif "discovery" in t:

            wireshark_filters.update({

                # Network scanning
                'tcp.flags.syn == 1 && tcp.flags.ack == 0',

                # ARP sweep
                'arp',

                # ICMP ping sweep
                'icmp.type == 8',

                # NBNS discovery
                'nbns',

                # LLMNR
                'llmnr',
            })

            hunt_queries.update({
                "Internal reconnaissance detection",
            })

    # =========================================================================
    # STEP 4 — Threat scoring
    # =========================================================================

    severity_terms = {
        "ransomware",
        "apt",
        "nation-state",
        "exfiltration",
        "domain admin",
        "zero-day",
    }

    priority = (
        "HIGH"
        if any(term in context for term in severity_terms)
        else "MEDIUM"
    )

    confidence_score = min(
        100,
        len(techniques) * 12 + len(tactics) * 8
    )

    # =========================================================================
    # STEP 5 — Final response
    # =========================================================================

    return {

        "found": True,

        "source": "neo4j",

        "context": threat_context,

        "priority": priority,

        "confidence_score": confidence_score,

        "hypothesis": (
            f"Threat activity aligns with "
            f"{', '.join(sorted(tactics))} "
            f"ATT&CK tactics indicating possible adversary operations."
        ),

        "mitre_tactics": sorted(tactics),

        "techniques": techniques,

        "wireshark_filters": sorted(wireshark_filters),

        "hunt_queries": sorted(hunt_queries),

        "data_sources": [
            "PCAP",
            "Zeek",
            "Sysmon",
            "Windows Event Logs",
            "DNS Logs",
            "Proxy Logs",
            "EDR Telemetry",
            "NetFlow",
        ],

        "playbook_steps": [
            "Acquire relevant PCAP and endpoint telemetry",
            "Apply Wireshark display filters to isolate suspicious traffic",
            "Pivot on IPs, domains, JA3 hashes, and processes",
            "Correlate findings with ATT&CK techniques",
            "Validate malicious indicators against threat intelligence",
            "Escalate confirmed activity to incident response",
        ],
    }