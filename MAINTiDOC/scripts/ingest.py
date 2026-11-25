"""CLI d'ingestion : catalogue YAML -> Qdrant."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from maintidoc.config import ROOT, get_settings  # noqa: E402
from maintidoc.embeddings import get_embedding_client  # noqa: E402
from maintidoc.ingestion.catalog import load_catalog, resolve_pdf  # noqa: E402
from maintidoc.ingestion.chunking import passages_from_pages  # noqa: E402
from maintidoc.ingestion.clip_describe import CLIP_DIM, get_clip_describer  # noqa: E402
from maintidoc.ingestion.images import extract_pdf_images, passages_from_images  # noqa: E402
from maintidoc.ingestion.pdf_extract import extract_pages  # noqa: E402
from maintidoc.logging_setup import configure_logging  # noqa: E402
from maintidoc.vectorstore import connect, ensure_collection, upsert_passages  # noqa: E402


def run(catalog_path: Path | None = None, corpus_dir: Path | None = None) -> int:
    """Ingère tous les PDF du catalogue et retourne le nombre de passages."""
    settings = get_settings()
    configure_logging(settings.log_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
    catalog = load_catalog(catalog_path or settings.resolve_catalog())
    corpus = corpus_dir or settings.resolve_corpus()

    client = connect(settings.qdrant_url)
    embedder = get_embedding_client(settings.embedding_model, settings.embedding_device)
    ensure_collection(client, settings.qdrant_collection, embedder.dim)
    ensure_collection(client, settings.qdrant_clip_collection, CLIP_DIM)

    total = 0
    logger = logging.getLogger("maintidoc.ingest")
    for record in catalog:
        pdf = resolve_pdf(corpus, record)
        pages = extract_pages(pdf)
        page_pairs = [(page.page, page.text) for page in pages]
        passages = passages_from_pages(
            record, page_pairs, settings.chunk_size, settings.chunk_overlap
        )
        images = extract_pdf_images(
            pdf,
            settings.resolve_images() / record.document_id,
            max_images=settings.max_images_per_doc,
        )
        image_passages: list = []
        if images:
            clip = get_clip_describer(settings.clip_model, settings.embedding_device)
            captions = clip.describe_many([str(item.path) for item in images])
            image_passages = passages_from_images(record, images, captions, ROOT)
            passages.extend(image_passages)
            clip_vectors = clip.encode_images([str(item.path) for item in images])
            upsert_passages(
                client, settings.qdrant_clip_collection, image_passages, clip_vectors
            )
        if not passages:
            logger.warning("aucun_passage document_id=%s", record.document_id)
            continue
        logger.info("encodage document_id=%s passages=%s", record.document_id, len(passages))
        vectors = embedder.embed([p.text for p in passages])
        total += upsert_passages(client, settings.qdrant_collection, passages, vectors)
        logger.info("index_ok document_id=%s passages=%s", record.document_id, len(passages))
    logger.info("ingest_termine passages=%s", total)
    return total


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexation MAINTiDOC")
    parser.add_argument("--catalog", type=Path, default=None)
    parser.add_argument("--corpus", type=Path, default=None)
    args = parser.parse_args()
    count = run(args.catalog, args.corpus)
    print(f"Passages indexés : {count}")


if __name__ == "__main__":
    main()
