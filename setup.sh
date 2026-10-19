#!/bin/bash

# --- Configuration Variables ---
export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:latest}"
export VERIFIER_MODEL="${VERIFIER_MODEL:-qwen2.5-coder:latest}"

echo "🚀 Spinning up Ontolocy Stack..."
docker-compose up -d --build

echo "⏳ Waiting for backend to initialize database connections..."
# Loops until the container is up and responding
while ! docker exec phantom_backend uvicorn --version >/dev/null 2>&1; do
    sleep 2
done

export OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:latest}"
export VERIFIER_MODEL="${VERIFIER_MODEL:-qwen2.5-coder:latest}"


echo "🤖 Pulling Ollama Models (if not already present)..."
# Checks if Ollama is running inside Docker or as a native host service
if docker ps | grep -q "phantom_ollama"; then
    echo "-> Downloading $OLLAMA_MODEL into Ollama container..."
    docker exec -it phantom_ollama ollama pull "$OLLAMA_MODEL"
    echo "-> Downloading $VERIFIER_MODEL into Ollama container..."
    docker exec -it phantom_ollama ollama pull "$VERIFIER_MODEL"
else
    echo "-> Assuming Native macOS Ollama. pulling models via host..."
    ollama pull "$OLLAMA_MODEL"
    ollama pull "$VERIFIER_MODEL"
fi

echo "📦 Automating MITRE-Attack parsing command..."
docker exec -it phantom_backend ontolocy parse mitre-attack

echo "✅ All done! Frontend available at http://localhost:3000"