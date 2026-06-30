import logging
from functools import lru_cache
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings

from shared.config import settings

logger = logging.getLogger(__name__)

_KB_DIR = Path(__file__).parent / "knowledge_base"
_CHARS_PER_TOKEN = 4
_TARGET_CHARS = 350 * _CHARS_PER_TOKEN
_MAX_CHARS = 500 * _CHARS_PER_TOKEN


def _chunk(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if len(para) > _MAX_CHARS:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.append(para)
        elif buf and len(buf) + len(para) > _TARGET_CHARS:
            chunks.append(buf)
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        chunks.append(buf)
    return chunks


@lru_cache
def _embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache
def _store() -> FAISS:
    texts: list[str] = []
    metadatas: list[dict] = []
    for path in sorted(_KB_DIR.glob("*.md")):
        for chunk in _chunk(path.read_text(encoding="utf-8")):
            texts.append(chunk)
            metadatas.append({"source": path.name})
    logger.info("building knowledge-base index: %d chunks", len(texts))
    return FAISS.from_texts(
        texts,
        _embeddings(),
        metadatas=metadatas,
        distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT,
    )


def retrieve(query: str, k: int | None = None) -> list[str]:
    """Top-k knowledge-base passages above the relevance floor. Normalized
    embeddings + inner-product index means score is cosine similarity, so a
    one-word reply doesn't drag in unrelated advice."""
    hits = _store().similarity_search_with_score(query, k=k or settings.retrieval_top_k)
    return [
        f"(source: {doc.metadata.get('source', '?')}) {doc.page_content}"
        for doc, score in hits
        if score >= settings.retrieval_min_score
    ]
