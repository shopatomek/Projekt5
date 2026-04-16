# backend/embeddings.py

import logging
from sentence_transformers import SentenceTransformer  # type: ignore
from database import execute_query

logger = logging.getLogger(__name__)

# Model do generowania embeddingów (384 wymiary)
_model = None


def get_model():
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model...")
        _model = SentenceTransformer("paraphrase-MiniLM-L3-v2")
        logger.info("Model loaded")
    return _model


def generate_embedding(text: str) -> list:
    """Generuje embedding dla tekstu."""
    model = get_model()
    # Ograniczenie długości (model ma limit 512 tokenów)
    full_text = text[:1000]
    embedding = model.encode(full_text).tolist()
    return embedding


def embed_existing_articles():
    """Generuje embeddingi dla istniejących artykułów (jednorazowo)."""
    logger.info("Generating embeddings for existing articles...")

    result = execute_query("SELECT id, title, COALESCE(description, '') as description FROM news_articles WHERE embedding IS NULL LIMIT 100")

    if not result:
        logger.info("No articles without embeddings found")
        return

    articles = result
    count = 0

    for article in articles:
        text = f"{article['title']} {article['description']}"
        embedding = generate_embedding(text)
        execute_query("UPDATE news_articles SET embedding = :embedding WHERE id = :id", {"embedding": embedding, "id": article["id"]})
        count += 1
        if count % 10 == 0:
            logger.info(f"Embedded {count} articles")

    logger.info(f"Done. Embedded {count} articles")


def embed_new_article(title: str, description: str):
    """Generuje embedding dla nowego artykułu przy zapisie."""
    text = f"{title} {description or ''}"
    return generate_embedding(text)
