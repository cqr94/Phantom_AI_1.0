

# APT·HUNT v3 — Threat Intelligence & Pentest Platform (v3.0.0)

APT·HUNT v3 is an advanced Threat Intelligence and Penetration Testing platform featuring an integrated AI-driven RAG (Retrieval-Augmented Generation) system for PCAP analysis, MITRE ATT&CK mapping via Neo4j, and multi-model AI validation.

This guide covers setting up the platform using a **local, native installation of Ollama** on your host machine while running the core backend and frontend services via Docker.

---

## 🚀 Architecture Overview

* **Frontend:** React.jsx / React Phantom AI Terminal (`http://localhost:3000`)
* **Backend:** FastAPI Application (`http://localhost:8000`)
* **Database:** Neo4j Graph Database (for MITRE ATT&CK relationships)
* **Database:** Postgres SQL - Authentication
* **Database:** Redis - Session storage


* **AI Engine:** Native Host Ollama (Local LLMs) < - Must be using default port and Llama3.2 + qwen2.5-coder

---

## 🛠️ Prerequisites

Before starting, ensure you have the following installed on your host system:

1.  **Docker & Docker Compose** (for backend, database, and frontend)
2.  **Ollama** (Native installer for macOS, Linux, or Windows)

---

## ⚡ Deployment Steps

1.

Run the initialization script to pull models to your host machine, build the application containers, and seed the MITRE ATT&CK dataset.

```bash
chmod +x setup.sh
./setup.sh
```

## 🛣️ API Reference (`OAS 3.1`)

Once the backend is up, the interactive Swagger documentation is available at `http://localhost:8000/docs`.

### 1. PCAP RAG

* `POST /upload_pcap` - Upload packet capture files for indexed analysis.
* `POST /query` - Query the RAG engine regarding network anomalies.

### 2. APT Chat

* `GET /health` - Check backend API and model connection status.
* `POST /chat` - Interactive threat intelligence chat.
* `GET /models` - List available local Ollama models.
* `DELETE /session/{session_id}` - Purge a specific chat history session.

### 3. MITRE ATT&CK Dashboard

* `GET /groups_neo4j` | `GET /techniques` | `GET /campaigns` | `GET /tactics`
* `GET /software` | `GET /mitigations` | `GET /relationships`
* `GET /timeline` - View chronological attack progressions.
* `GET /stats` - High-level metrics on your threat landscape.

### 4. Authentication & Admin

* `POST /register` | `POST /login` | `POST /verify-mfa`
* `POST /auth/refresh` | `POST /auth/logout`
* `GET /admin/dashboard` - Platform administrative controls.

---


