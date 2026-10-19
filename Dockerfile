# Use the official Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies if required (e.g., for Postgres/Neo4j connections)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to utilize Docker build cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application backend code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Run FastAPI via Uvicorn automatically
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]