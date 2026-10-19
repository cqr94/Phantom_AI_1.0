from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import os
import uuid
import numpy as np
import faiss
import requests
from typing import List, Dict
from scapy.all import rdpcap
from fastapi import APIRouter
OLLAMA_URL = "http://localhost:11434/api/embeddings"
OLLAMA_MODEL = "nomic-embed-text"

DIM = 768  # depends on embedding model

router = APIRouter(tags=["PCAP RAG"])

# FAISS
index = faiss.IndexFlatL2(DIM)
metadata_store: Dict[int, dict] = {}
vector_id_counter = 0


from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.packet import Raw

def extract_pcap_text(file_path: str) -> List[dict]:

    packets = rdpcap(file_path)

    results = []

    for i, pkt in enumerate(packets):

        try:
            proto = "OTHER"
            sport = None
            dport = None

            if pkt.haslayer(TCP):
                proto = "TCP"
                sport = pkt[TCP].sport
                dport = pkt[TCP].dport

            elif pkt.haslayer(UDP):
                proto = "UDP"
                sport = pkt[UDP].sport
                dport = pkt[UDP].dport

            elif pkt.haslayer(ICMP):
                proto = "ICMP"

            src_ip = pkt[IP].src if pkt.haslayer(IP) else None
            dst_ip = pkt[IP].dst if pkt.haslayer(IP) else None

            payload = ""

            if pkt.haslayer(Raw):
                try:
                    payload = bytes(pkt[Raw]).decode(
                        errors="ignore"
                    )[:500]
                except Exception:
                    payload = ""

            summary = pkt.summary()

            embedding_text = f"""
            Protocol: {proto}
            Source IP: {src_ip}
            Destination IP: {dst_ip}
            Source Port: {sport}
            Destination Port: {dport}
            Summary: {summary}
            Payload: {payload}
            """

            results.append({
                "text": embedding_text,
                "metadata": {
                    "packet_number": i,
                    "protocol": proto,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": sport,
                    "dst_port": dport,
                    "summary": summary,
                    "payload": payload,
                    "length": len(pkt),
                    "timestamp": float(pkt.time),
                }
            })

        except Exception:
            continue

    return results


def get_embedding(text: str) -> List[float]:
    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": text},
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Embedding failed")

    return response.json()["embedding"]


def add_to_faiss(text: str, meta: dict):
    global vector_id_counter

    embedding = np.array(get_embedding(text), dtype="float32").reshape(1, -1)

    index.add(embedding)
    metadata_store[vector_id_counter] = meta

    vector_id_counter += 1



class QueryRequest(BaseModel):
    query: str
    top_k: int = 5



@router.post("/upload_pcap")
async def upload_pcap(file: UploadFile = File(...)):

    global vector_id_counter

    file_id = str(uuid.uuid4())
    file_path = f"/tmp/{file_id}.pcap"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    packets = extract_pcap_text(file_path)

    if not packets:
        raise HTTPException(
            status_code=400,
            detail="No packets found"
        )

    for pkt in packets:

        add_to_faiss(
            pkt["text"],
            {
                "file_id": file_id,
                **pkt["metadata"]
            }
        )

    return {
        "status": "ingested",
        "file_id": file_id,
        "packets": len(packets),
        "vectors": index.ntotal,
    }

@router.post("/query")
def query_rag(req: QueryRequest):
    query_vec = np.array(get_embedding(req.query), dtype="float32").reshape(1, -1)

    if index.ntotal == 0:
        return {"results": []}

    scores, ids = index.search(query_vec, req.top_k)

    results = []
    for i in ids[0]:
        if i == -1:
            continue
        results.append(metadata_store.get(i, {}))

    return {"query": req.query, "results": results}


@router.get("/health")
def health():
    return {
        "status": "ok",
        "vectors": index.ntotal
    }

def retrieve_pcap_context(query: str, top_k: int = 5) -> str:
    query_vec = np.array(get_embedding(query), dtype="float32").reshape(1, -1)

    if index.ntotal == 0:
        return ""

    scores, ids = index.search(query_vec, top_k)

    chunks = []
    for i in ids[0]:
        if i == -1:
            continue
        meta = metadata_store.get(i)
        if meta:
            chunks.append(meta["text"])

    return "\n".join(chunks)