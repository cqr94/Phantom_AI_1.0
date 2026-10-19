

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable

import httpx
from pydantic import BaseModel, Field, ValidationError, model_validator

from best_agent.sys_prompt_v3 import SYSTEM_PROMPT as SYSTEM_PROMPT
from best_agent.tool_functions import TOOL_FUNCTIONS
from best_agent.phantom_tools_3 import TOOLS
   
# LOGGING
   

logger = logging.getLogger("phantom-grc")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
# working prompts : in a markdown table list the most interesting payloads from pcap
   
# CONFIG  (all overridable via env)
   

OLLAMA_URL      = os.getenv("OLLAMA_URL",   "http://host.docker.internal:11434")
#OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:latest")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
VERIFIER_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:latest")

API_KEY = "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"
#VERIFIER_MODEL  = os.getenv("VERIFIER_MODEL", "llama3.2:latest")  # can point to a faster model

API_TIMEOUT            = int(os.getenv("API_TIMEOUT",            "180"))
MAX_TOOL_ITERATIONS    = int(os.getenv("MAX_TOOL_ITERATIONS",    "8"))
MAX_RETRIES            = int(os.getenv("MAX_RETRIES",            "3"))
MAX_PARALLEL_TOOLS     = int(os.getenv("MAX_PARALLEL_TOOLS",     "4"))   # semaphore cap

TEMPERATURE      = float(os.getenv("TEMPERATURE",      "0.1"))
TOP_P            = float(os.getenv("TOP_P",            "0.8"))
REPEAT_PENALTY   = float(os.getenv("REPEAT_PENALTY",   "1.1"))
NUM_CTX          = int(os.getenv("NUM_CTX",            "16384"))
NUM_PREDICT      = int(os.getenv("NUM_PREDICT",        "4096"))

# Context compression kicks in when char-count exceeds this threshold
COMPRESS_THRESHOLD_CHARS = int(os.getenv("COMPRESS_THRESHOLD_CHARS", "45000"))

# Back-off base (seconds) for retry jitter
BACKOFF_BASE = 1.5

   
# SESSION STORE
   

sessions: dict[str, list[dict]] = {}

   
# PYDANTIC SCHEMAS
   
async def rewrite_query(user_message: str) -> RewrittenQuery:
    messages = [
        {"role": "system", "content": QUERY_REWRITER_PROMPT},
        {"role": "user", "content": user_message},
    ]

    try:
        response = await ollama_chat(
            messages,
            model=VERIFIER_MODEL,  # or a small fast model like mistral
        )

        content = response.get("message", {}).get("content", "").strip()

        if content.startswith("```"):
            content = content.split("```")[1]

        parsed = json.loads(content)

        return RewrittenQuery(
            original=parsed.get("original", user_message),
            rewritten=parsed.get("rewritten", user_message),
            sub_queries=parsed.get("sub_queries", []),
            intent=parsed.get("intent", "general_search"),
            entities=[
                e.get("text") if isinstance(e, dict) else str(e)
                for e in parsed.get("entities", [])
            ],
            confidence=parsed.get("confidence", 0.5),
        )

    except Exception as e:
        logger.warning("PHANTOM query rewrite failed: %s", e)

        return RewrittenQuery(
            original=user_message,
            rewritten=user_message,
            intent="general_search",
            confidence=0.0,
        )

QUERY_REWRITER_PROMPT = """\
You are PHANTOM-FORENSIC-JSON-ENGINE — a deterministic PCAP-to-intelligence structuring system.



OUTPUT FORMAT (STRICT JSON ONLY)


{
  "session": {
    "pcap_file": string,
    "vectors": integer,
    "rag_status": "ingested | updated | partial | failed"
  },

  "operator_intent": string,

  "tool_trace": [
    {
      "tool": string,
      "parameters": object,
      "status": "success | failure | partial",
      "output_summary": string
    }
  ],

  "raw_payloads": [
    {
      "id": integer,
      "protocol": "TCP | HTTP | UDP | OTHER",
      "method": string,
      "endpoint": string,
      "raw": string,
      "relevance_score": float
    }
  ],

  "scored_payloads": [
    {
      "rank": integer,
      "payload_id": integer,
      "endpoint": string,
      "summary": string,
      "suspicion_score": float,
      "reason": [string]
    }
  ],

  "top_10_suspicious_payloads": [
    {
      "rank": integer,
      "raw": string,
      "endpoint": string,
      "suspicion_score": float,
      "relevance_score": float,
      "reason": [string]
    }
  ],

  "pcap_insights": [
    string
  ],

  "attck_hypotheses": [
    {
      "technique_id": string,
      "name": string,
      "confidence": float,
      "evidence": [string]
    }
  ],

  "execution_quality": {
    "tool_success_rate": float,
    "data_completeness": float,
    "noise_level": "low | medium | high"
  },

  "confidence": float
}


PCAP ANALYSIS RULES


- Treat HTTP requests as application-layer artifacts, not malicious by default
- Do NOT assume banking context = attack
- Session cookies = potential tracking, not proof of compromise
- localhost traffic is normal unless other evidence exists

OUTPUT STYLE


- STRICT JSON ONLY
- NO markdown
- NO explanations
- NO extra keys
"""

class RewrittenQuery(BaseModel):
    original: str
    rewritten: str
    sub_queries: list[str] = Field(default_factory=list)
    intent: str = "unknown"
    entities: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

class Evidence(BaseModel):
    source: str
    query: str | None = None
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    node_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    result: dict[str, Any]
    evidence: list[Evidence] = Field(default_factory=list)
    duration_ms: float = 0.0

    @model_validator(mode="after")
    def _clamp_confidence(self) -> "ToolResult":
        for e in self.evidence:
            e.confidence = max(0.0, min(1.0, e.confidence))
        return self


class VerificationResult(BaseModel):
    status: str = "PARTIAL"          # VERIFIED | PARTIAL | REJECTED
    issues: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    @model_validator(mode="after")
    def _normalise_status(self) -> "VerificationResult":
        self.status = self.status.upper()
        if self.status not in {"VERIFIED", "PARTIAL", "REJECTED"}:
            self.status = "PARTIAL"
        return self


   
# UTILITIES
   


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_tool_call(name: str, args: dict) -> str:
    payload = json.dumps({"name": name, "args": args}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def token_estimate(messages: list[dict]) -> int:
    """Rough token count: ~4 chars per token."""
    return sum(len(json.dumps(m)) for m in messages) // 4


def _backoff(attempt: int) -> float:
    """Exponential back-off with ±25 % jitter."""
    base = BACKOFF_BASE * (2 ** (attempt - 1))
    return base * (0.75 + random.random() * 0.5)


def compress_history(messages: list[dict]) -> list[dict]:

    if len(messages) < 8:
        return messages

    system_msg = messages[0]
    recent     = messages[-6:]

    # Collect tool evidence from dropped middle so the model doesn't lose context
    middle = messages[1:-6]
    tool_evidence_msgs = [
        m for m in middle if m.get("role") == "tool"
    ]

    summary = {
        "role": "system",
        "content": (
            "[CONTEXT COMPRESSED]\n"
            "Prior analysis, conclusions, and evidence preserved below.\n"
            "Do not re-derive already-established findings."
        ),
    }

    compressed = [system_msg, summary] + tool_evidence_msgs[-4:] + recent
    logger.info(
        "Context compressed: %d → %d messages", len(messages), len(compressed)
    )
    return compressed


def calculate_confidence(
    evidence_count: int,
    corroboration_count: int,
    verifier_score: float,
) -> float:
    score = (
        min(evidence_count / 5,       1.0) * 0.4
        + min(corroboration_count / 3, 1.0) * 0.3
        + verifier_score               * 0.3
    )
    return round(min(score, 1.0), 2)


   
# OLLAMA CLIENT
   


async def check_ollama() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            r.raise_for_status()
            data = r.json()
            return {
                "available": True,
                "models": [m["name"] for m in data.get("models", [])],
            }
    except Exception as e:
        return {"available": False, "error": str(e)}


def _build_payload(
    messages: list[dict],
    *,
    tools: list[dict] | None = None,
    stream: bool = False,
    model: str | None = None,
) -> dict:
    payload: dict[str, Any] = {
        "model": model or OLLAMA_MODEL,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature":    TEMPERATURE,
            "top_p":          TOP_P,
            "repeat_penalty": REPEAT_PENALTY,
            "num_ctx":        NUM_CTX,
            "num_predict":    NUM_PREDICT,
        },
    }
    if tools:
        payload["tools"] = tools
    return payload


async def ollama_chat(
    messages: list[dict],
    *,
    tools: list[dict] | None = None,
    stream: bool = False,
    model: str | None = None,
) -> dict:
    payload = _build_payload(messages, tools=tools, stream=stream, model=model)

    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 2):           # +2: first attempt is attempt 1
        try:
            async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
                r = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
                r.raise_for_status()
                return r.json()
        except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
            last_exc = e
            if attempt > MAX_RETRIES:
                break
            wait = _backoff(attempt)
            logger.warning(
                "Ollama request failed (attempt %d/%d, retry in %.1fs): %s",
                attempt, MAX_RETRIES + 1, wait, e,
            )
            await asyncio.sleep(wait)
        except Exception as e:
            # Non-retriable errors bubble immediately
            raise

    raise RuntimeError(f"Ollama unreachable after {MAX_RETRIES + 1} attempts: {last_exc}")


async def ollama_stream(
    messages: list[dict],
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    payload = _build_payload(messages, stream=True, model=model)

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json=payload) as r:
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                except json.JSONDecodeError:
                    continue


   
# TOOL EXECUTION  (semaphore-bounded parallelism)
   

_tool_semaphore = asyncio.Semaphore(MAX_PARALLEL_TOOLS)


async def execute_tool(tool_name: str, tool_args: dict) -> ToolResult:
    fn: Callable | None = TOOL_FUNCTIONS.get(tool_name)

    if not fn:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            result={"error": f"Unknown tool: {tool_name}"},
        )

    started = time.perf_counter()

    async with _tool_semaphore:
        try:
            if asyncio.iscoroutinefunction(fn):
                raw_result = await fn(**tool_args)
            else:
                raw_result = await asyncio.to_thread(fn, **tool_args)

            duration_ms = (time.perf_counter() - started) * 1000

            evidence = [
                Evidence(
                    source="tool_execution",
                    query=json.dumps(tool_args),
                    confidence=0.9,
                )
            ]

            logger.info("Tool %-30s  %6.0f ms  ✓", tool_name, duration_ms)

            return ToolResult(
                success=True,
                tool_name=tool_name,
                result=raw_result,
                evidence=evidence,
                duration_ms=round(duration_ms, 1),
            )

        except ValidationError as e:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.warning("Tool %s — validation error: %s", tool_name, e)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                result={"validation_error": str(e)},
                duration_ms=round(duration_ms, 1),
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception("Tool %s — execution failed.", tool_name)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                result={"execution_error": str(e)},
                duration_ms=round(duration_ms, 1),
            )


   
# VERIFIER  (structural JSON guard + semantic pass)
   

VERIFIER_PROMPT = """\
You are a senior MITRE ATT&CK validation and threat intelligence verification engine \
specialising in adversary behavior modeling, including tactics, techniques, sub-techniques, \
software, and groups across MITRE ATT&CK (Enterprise, Mobile, ICS).

You also validate forensic evidence artifacts such as PCAP files, network logs, and packet-level \
observations when they are used as supporting evidence for ATT&CK claims.

Evaluate the assistant response for:

  1. Invalid or hallucinated MITRE IDs (e.g., TA*, T*, S*, G* not in ATT&CK)
  2. Incorrect technique-to-tactic mappings (techniques must belong to valid tactics)
  3. Fabricated or unsupported ATT&CK relationships (Group → Technique, Software → Technique)
  4. Non-existent or incorrectly named techniques, groups, or software
  5. Incorrect sub-technique structure (e.g., treating sub-techniques as standalone techniques incorrectly)
  6. Outdated or version-inconsistent ATT&CK references (Enterprise vs ICS vs Mobile mix-ups)
  7. Unsupported claims about adversary behavior not grounded in ATT&CK knowledge
  8. Logical inconsistencies in kill chain or attack flow representation
  9. Scope drift (response must stay strictly within MITRE ATT&CK knowledge base and retrieved evidence)
  10. Misinterpretation or hallucination of PCAP / network evidence (if PCAPs or packet data are referenced)
  11. Unsupported inference from PCAP data (e.g., claiming attacker intent, technique attribution, or group identity without sufficient evidence)
  12. Incorrect mapping between PCAP indicators (IPs, ports, protocols, payloads) and ATT&CK techniques

PCAP / NETWORK EVIDENCE RULES:
- PCAP files are LOW-LEVEL OBSERVATIONAL DATA, not attribution sources by themselves.
- Do NOT allow direct mapping from raw packets to specific ATT&CK Groups unless corroborated by external intelligence.
- Protocols, ports, and packet contents alone MUST NOT be treated as definitive indicators of adversary identity.
- PCAP-derived signals may only support hypotheses about techniques (e.g., C2, exfiltration), not confirm them.
- Any claim derived from PCAP data must be explicitly grounded in observable behavior, not speculation.

IMPORTANT RULES:
- Do NOT allow invented technique IDs, group names, or software names.
- Do NOT allow fabricated mappings between entities.
- Every ATT&CK reference must correspond to a real, verifiable MITRE ATT&CK object.
- If evidence is missing or ambiguous, mark as PARTIAL or REJECTED.
- If PCAP evidence is insufficient or speculative, downgrade confidence accordingly.

Return ONLY valid JSON — no preamble, no markdown fences:

{
  "status": "VERIFIED | PARTIAL | REJECTED",
  "issues": ["<issue description>", ...],
  "confidence": <float 0.0–1.0>
}
"""

VERIFIER_PROMPT_V2 = """
Validate the assistant response against MITRE ATT&CK knowledge and provided evidence.

Check for:
- invalid ATT&CK IDs
- incorrect tactic-technique mappings
- fabricated ATT&CK entities
- unsupported relationships
- incorrect sub-technique usage
- ATT&CK domain/version inconsistencies
- unsupported claims
- logical inconsistencies
- evidence mismatch

Rules:
- Never invent ATT&CK entities.
- If evidence is insufficient, use PARTIAL or REJECTED.
- Return ONLY valid JSON.
- No markdown.
- No explanations outside JSON.

Schema:
{
  "status": "VERIFIED|PARTIAL|REJECTED",
  "issues": ["string"],
  "confidence": 0.0
}
"""

async def verify_response(response_text: str) -> VerificationResult:
    messages = [
        {"role": "system", "content": VERIFIER_PROMPT},
        {"role": "user",   "content": response_text},
    ]

    try:
        response = await ollama_chat(messages, model=VERIFIER_MODEL)
        content  = response.get("message", {}).get("content", "{}").strip()

        # Strip accidental markdown fences
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        parsed = json.loads(content)
        return VerificationResult(**parsed)

    except json.JSONDecodeError as e:
        logger.warning("Verifier returned non-JSON: %s", e)
        return VerificationResult(status="PARTIAL", issues=["Verifier non-JSON response"], confidence=0.5)

    except Exception as e:
        logger.warning("Verifier call failed: %s", e)
        return VerificationResult(status="PARTIAL", issues=[f"Verifier failed: {e}"], confidence=0.5)


   
# SSE HELPERS
   


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def sse_error(message: str) -> str:
    return sse("error", {"message": message, "timestamp": utc_now()})


   
# TOOL-CALL ARGUMENT COERCION
   


def _coerce_args(raw: Any) -> dict:
    """Ensure tool arguments are always a plain dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


   
# AGENT LOOP
   


async def agent_stream(
    user_message: str,
    history: list[dict],
) -> AsyncGenerator[str, None]:

    # ==========================================================
    # QUERY REWRITER LAYER (GraphRAG enhancement)
    # ==========================================================

    #rewritten_query = await rewrite_query(user_message)
    """
    logger.info(
        "Query rewritten: %s → %s",
        user_message,
        rewritten_query.rewritten,
    )
    """
    # Replace user message with enhanced version
    #user_message = rewritten_query.rewritten

    # Optional: inject structured intent as system hint
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {
            "role": "system",
            "content": (
                f"[QUERY INTENT]: {rewritten_query.intent}\n"
                f"[EXTRACTED ENTITIES]: {rewritten_query.entities}\n"
                f"[SUB-QUERIES]: {rewritten_query.sub_queries}"
            ),
        },
        {"role": "user", "content": user_message},
    ]

    
    Main agentic loop.

    Flow per iteration:
      1. Call Ollama with tools
      2. If tool_calls present → execute in parallel (semaphore-bounded)
      3. Append tool results; loop
      4. On final text response → verify → stream tokens → emit done
    """

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user",   "content": user_message},
    ]

    seen_tool_hashes: set[str] = set()   # loop-detection window
    tool_usage_counter: Counter = Counter()
    all_evidence: list[Evidence] = []

    # =========================================================================
    # MAIN AGENTIC LOOP
    # =========================================================================

    for iteration in range(MAX_TOOL_ITERATIONS):

        # Adaptive context compression
        if token_estimate(messages) > COMPRESS_THRESHOLD_CHARS:
            messages = compress_history(messages)

        # ------------------------------------------------------------------
        # LLM CALL
        # ------------------------------------------------------------------
        try:
            response = await ollama_chat(messages, tools=TOOLS)
        except Exception as e:
            yield sse_error(f"LLM call failed: {e}")
            return

        assistant_msg = response.get("message", {})
        tool_calls    = assistant_msg.get("tool_calls", [])

        # ==================================================================
        # FINAL RESPONSE — no more tool calls
        # ==================================================================

        if not tool_calls:
            content = assistant_msg.get("content", "").strip()

            if not content:
                yield sse_error("Model returned an empty response.")
                return

            # --- Verifier pass ---
            verifier = await verify_response(content)

            if verifier.status == "REJECTED":
                logger.warning(
                    "Verifier REJECTED response. Issues: %s", verifier.issues
                )
                # Surface to caller but still stream (caller can decide to suppress)

            confidence = calculate_confidence(
                evidence_count=len(all_evidence),
                corroboration_count=len(tool_usage_counter),
                verifier_score=verifier.confidence,
            )

            metadata = {
                "verification":        verifier.status,
                "verification_issues": verifier.issues,
                "confidence":          confidence,
                "tools_used":          list(tool_usage_counter.keys()),
                "tool_call_counts":    dict(tool_usage_counter),
                "iterations":          iteration + 1,
                "timestamp":           utc_now(),
            }

            yield sse("metadata", metadata)

            # --- Stream final tokens ---
            final_messages = [*messages, {"role": "assistant", "content": content}]
            async for token in ollama_stream(final_messages):
                yield sse("token", {"text": token})

            yield sse("done", {"content": content, "metadata": metadata})
            return

        # ==================================================================
        # TOOL EXECUTION PHASE
        # ==================================================================

        # Append assistant's tool-calling turn to history
        messages.append(
            {
                "role":       "assistant",
                "content":    assistant_msg.get("content", ""),
                "tool_calls": tool_calls,
            }
        )

        parallel_tasks: list[asyncio.Task] = []
        scheduled_names: list[str] = []

        for tc in tool_calls:
            fn_spec   = tc.get("function", {})
            tool_name = fn_spec.get("name", "").strip()
            tool_args = _coerce_args(fn_spec.get("arguments", {}))

            if not tool_name:
                logger.warning("Skipping tool call with empty name.")
                continue

            # ---- Loop detection ----------------------------------------
            call_hash = hash_tool_call(tool_name, tool_args)
            if call_hash in seen_tool_hashes:
                yield sse(
                    "warning",
                    {
                        "message":   f"Duplicate tool call blocked: {tool_name}",
                        "tool":      tool_name,
                        "iteration": iteration,
                    },
                )
                continue

            seen_tool_hashes.add(call_hash)
            tool_usage_counter[tool_name] += 1

            yield sse("tool_call", {"tool": tool_name, "args": tool_args, "iteration": iteration})

            parallel_tasks.append(
                asyncio.ensure_future(execute_tool(tool_name, tool_args))
            )
            scheduled_names.append(tool_name)

        if not parallel_tasks:
            # All tool calls were duplicates — force model toward a final answer
            messages.append(
                {
                    "role":    "system",
                    "content": (
                        "All requested tool calls were duplicates and were skipped. "
                        "Synthesise a final response from available evidence."
                    ),
                }
            )
            continue

        # ---- Execute all tools in parallel (semaphore caps concurrency) ---
        results: list[ToolResult] = await asyncio.gather(*parallel_tasks)

        for result in results:
            all_evidence.extend(result.evidence)
            validated = result.model_dump()

            messages.append(
                {
                    "role":      "tool",
                    "tool_name": result.tool_name,
                    "content":   json.dumps(validated, default=str),
                }
            )

            yield sse(
                "tool_result",
                {
                    "tool":        result.tool_name,
                    "success":     result.success,
                    "duration_ms": result.duration_ms,
                },
            )

    # =========================================================================
    # ITERATION CAP
    # =========================================================================

    yield sse_error(
        f"Max tool iterations ({MAX_TOOL_ITERATIONS}) reached without a final answer. "
        "Consider narrowing the query or increasing MAX_TOOL_ITERATIONS."
    )


   
# SIMPLE TEST HARNESS
   

if __name__ == "__main__":

    async def main() -> None:
        history: list[dict] = []

        async for chunk in agent_stream(
            "",
            history,
        ):
            print(chunk, end="", flush=True)

    asyncio.run(main())
