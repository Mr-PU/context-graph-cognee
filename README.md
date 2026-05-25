# Cognee + Ollama – Dockerized Knowledge Graph

Build a local knowledge graph from your documents using **Cognee** and **Ollama**.
No API keys required – everything runs on your own hardware.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Docker Compose                                  │
│                                                  │
│  ┌─────────────────┐     ┌──────────────────┐   │
│  │   ollama        │     │   cognee_app     │   │
│  │  :11434         │◄────│                  │   │
│  │  llama3.2       │     │  • ingests docs  │   │
│  │  nomic-embed    │     │  • cognifies     │   │
│  └─────────────────┘     │  • queries graph │   │
│                           └──────────────────┘   │
└─────────────────────────────────────────────────┘
```

## Requirements

- Docker & Docker Compose
- 8 GB RAM minimum (16 GB+ recommended)
- ~5 GB disk for model weights

## Quick Start

```bash
# 1. Clone / copy this project
cd cognee-ollama

# 2. (Optional) Add your own .txt files
cp your_document.txt data/

# 3. Build and run
docker compose up --build
```

The first run will:
1. Start Ollama
2. Pull `llama3.2:latest` (~2 GB) and `nomic-embed-text:latest` (~270 MB)
3. Ingest the sample documents + any `.txt` files in `data/`
4. Build a knowledge graph via Cognee's cognify pipeline
5. Run example queries and print results

Subsequent runs skip model downloads (models are cached in a Docker volume).

## Changing the Models

Edit `.env` to swap models:

```dotenv
# Larger, more accurate (needs 16 GB+ RAM)
LLM_MODEL=llama3.3:70b

# Good mid-range option
LLM_MODEL=mistral:7b

# Faster, lighter
LLM_MODEL=phi3:mini
```

The `nomic-embed-text` embedding model works well with all LLM choices.

## Adding Your Own Documents

Drop `.txt` files into the `data/` directory before running:

```
data/
├── example.txt        ← included sample
├── my_report.txt      ← your file
└── research_notes.txt ← your file
```

## GPU Acceleration

Uncomment in `docker-compose.yml`:

```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

## Project Structure

```
cognee-ollama/
├── app/
│   └── main.py          # cognee pipeline
├── data/
│   └── example.txt      # sample document
├── Dockerfile           # cognee app image
├── docker-compose.yml   # orchestration
├── .env                 # provider config
└── README.md
```
