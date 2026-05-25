"""
Cognee Knowledge Graph Builder with Ollama
Builds a context graph from text/documents using local Ollama models.
"""

import asyncio
import os
import json
import logging
from pathlib import Path

import cognee

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── Sample documents to ingest ──────────────────────────────────────────────
SAMPLE_DOCUMENTS = [
    """
    Artificial Intelligence (AI) is the simulation of human intelligence by machines.
    Machine learning is a subset of AI that enables systems to learn from data.
    Deep learning uses neural networks with many layers to model complex patterns.
    Natural Language Processing (NLP) allows computers to understand human language.
    """,
    """
    Python is a high-level programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991.
    Python supports multiple programming paradigms including procedural, object-oriented,
    and functional programming. It is widely used in data science, web development, and AI.
    """,
    """
    Docker is a platform for developing, shipping, and running applications in containers.
    Containers package code and dependencies together for consistent environments.
    Kubernetes orchestrates containers at scale across multiple hosts.
    DevOps combines development and operations for faster software delivery.
    """,
    """
    Knowledge graphs represent information as entities and relationships.
    They are used in search engines, recommendation systems, and AI assistants.
    Graph databases like Neo4j store and query interconnected data efficiently.
    Ontologies define formal vocabularies and relationships within a domain.
    """,
]


async def wait_for_ollama(max_retries: int = 30, delay: int = 5) -> bool:
    """Poll Ollama until it's ready."""
    import httpx

    ollama_url = os.getenv("LLM_ENDPOINT", "http://ollama:11434/v1")
    base_url = ollama_url.rstrip("/v1").rstrip("/")
    health_url = f"{base_url}/api/tags"

    logger.info("Waiting for Ollama at %s …", base_url)
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(health_url)
                if resp.status_code == 200:
                    logger.info("Ollama is ready.")
                    return True
        except Exception:
            pass
        logger.info("  attempt %d/%d – retrying in %ds …", attempt, max_retries, delay)
        await asyncio.sleep(delay)
    return False


async def pull_model_if_missing(model_name: str) -> None:
    """Pull an Ollama model if it is not already present."""
    import httpx

    ollama_url = os.getenv("LLM_ENDPOINT", "http://ollama:11434/v1")
    base_url = ollama_url.rstrip("/v1").rstrip("/")

    async with httpx.AsyncClient(timeout=300) as client:
        # Check if already pulled
        tags_resp = await client.get(f"{base_url}/api/tags")
        if tags_resp.status_code == 200:
            models = [m["name"] for m in tags_resp.json().get("models", [])]
            # normalize: "llama3.2:latest" matches "llama3.2"
            if any(model_name.split(":")[0] in m for m in models):
                logger.info("Model '%s' already present.", model_name)
                return

        logger.info("Pulling model '%s' (this may take a while) …", model_name)
        async with client.stream(
            "POST",
            f"{base_url}/api/pull",
            json={"name": model_name},
            timeout=600,
        ) as stream:
            async for line in stream.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if "pulling" in status or "verifying" in status or "success" in status:
                            logger.info("  %s", status)
                    except json.JSONDecodeError:
                        pass
        logger.info("Model '%s' pulled successfully.", model_name)


async def build_knowledge_graph() -> None:
    """Main pipeline: ingest documents and cognify into a knowledge graph."""

    llm_model = os.getenv("LLM_MODEL", "llama3.2:latest")
    embed_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")

    # ── 1. Wait for Ollama ───────────────────────────────────────────────────
    ready = await wait_for_ollama()
    if not ready:
        raise RuntimeError("Ollama did not become ready in time. Aborting.")

    # ── 2. Pull models ───────────────────────────────────────────────────────
    await pull_model_if_missing(llm_model)
    await pull_model_if_missing(embed_model)

    # ── 3. Reset previous state ──────────────────────────────────────────────
    logger.info("Resetting cognee state …")
    await cognee.prune.prune_data()
    await cognee.prune.prune_system(metadata=True)

    # ── 4. Add documents ─────────────────────────────────────────────────────
    logger.info("Adding %d documents …", len(SAMPLE_DOCUMENTS))
    for i, doc in enumerate(SAMPLE_DOCUMENTS, 1):
        await cognee.add(doc, dataset_name="knowledge_base")
        logger.info("  Added document %d", i)

    # Also ingest any .txt files mounted under /app/data/
    data_dir = Path("/app/data")
    txt_files = list(data_dir.glob("*.txt"))
    if txt_files:
        for fp in txt_files:
            text = fp.read_text(encoding="utf-8")
            await cognee.add(text, dataset_name="knowledge_base")
            logger.info("  Added file: %s", fp.name)

    # ── 5. Cognify – build the knowledge graph ───────────────────────────────
    logger.info("Cognifying – building the knowledge graph …")
    await cognee.cognify(datasets=["knowledge_base"])
    logger.info("Knowledge graph built successfully.")

    # ── 6. Query the graph ───────────────────────────────────────────────────
    queries = [
        "What is artificial intelligence?",
        "How does machine learning relate to deep learning?",
        "What is Docker used for?",
        "How are knowledge graphs used?",
        "What is Python programming language?",
    ]

    logger.info("\n%s\nQuerying the knowledge graph\n%s", "=" * 60, "=" * 60)
    for query in queries:
        logger.info("\nQuery: %s", query)
        results = await cognee.search(
            query_text=query,
            query_type="insights",
        )
        if results:
            for result in results[:3]:  # top-3
                if isinstance(result, dict):
                    logger.info("  → %s", result)
                else:
                    logger.info("  → %s", result)
        else:
            logger.info("  (no results)")

    logger.info("\n%s\nDone!\n%s", "=" * 60, "=" * 60)


if __name__ == "__main__":
    asyncio.run(build_knowledge_graph())
