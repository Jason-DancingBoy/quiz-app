"""RAGAS evaluation runner — orchestrates end-to-end evaluation of the quiz generation pipeline.

Execution flow:
  1. Load documents from ChromaDB + SQLite
  2. For each (doc, difficulty) pair:
     a. Parse document into chunks
     b. Build difficulty-aware query and retrieve contexts via RAG
     c. Generate quiz questions via DeepSeek
     d. Convert questions to natural language for Faithfulness evaluation
     e. Check format compliance
     f. Score question quality (1-5)
     g. Build RAGAS SingleTurnSample and evaluate
  3. Aggregate results by difficulty and document length
  4. Persist results via reporter (latest JSON, history JSONL, human-readable report)
"""

import math
import random
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ragas import EvaluationDataset, SingleTurnSample, evaluate

from backend.config import DATABASE_URL
from backend.logger import get_logger
from backend.services.generator import generate_quiz
from backend.services.parser import parse_text
from backend.services.rag_service import _build_query_from_chunks, _get_collection, query_for_quiz
from backend.tests.ragas_eval.metrics import (
    build_ragas_metrics,
    check_format_compliance,
    questions_to_text,
    score_question_quality,
)
from backend.tests.ragas_eval.reporter import write_history, write_latest_json, write_report

logger = get_logger(__name__)

# Project root is 3 levels up from backend/tests/ragas_eval/
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _get_sqlite_path() -> Path:
    """Extract the SQLite database file path from DATABASE_URL.

    Handles SQLAlchemy-style ``sqlite+aiosqlite:///`` URLs:
      - ``sqlite+aiosqlite:///./data/quiz.db`` → relative path ``./data/quiz.db``
      - ``sqlite+aiosqlite:////app/data/quiz.db`` → absolute path ``/app/data/quiz.db``
    Falls back to ``PROJECT_ROOT / "data" / "quiz.db"`` if parsing fails.
    """
    raw = DATABASE_URL.replace("sqlite+aiosqlite:///", "", 1)
    path = Path(raw)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def _compute_stats(values: list[float]) -> dict[str, float]:
    """Compute mean and std for a list of numeric values.

    Returns ``{"mean": 0.0, "std": 0.0}`` when *values* is empty.
    """
    if not values:
        return {"mean": 0.0, "std": 0.0}
    return {
        "mean": round(statistics.mean(values), 4),
        "std": round(statistics.stdev(values) if len(values) > 1 else 0.0, 4),
    }


def _get_doc_ids_from_chromadb() -> set[int]:
    """Return all unique document IDs that have chunks stored in ChromaDB."""
    col = _get_collection()
    all_data = col.get()
    if not all_data or not all_data.get("metadatas"):
        return set()
    doc_ids: set[int] = set()
    for meta in all_data["metadatas"]:
        if meta and "doc_id" in meta:
            doc_ids.add(int(meta["doc_id"]))
    return doc_ids


def _get_documents_from_sqlite(doc_ids: set[int]) -> list[dict[str, Any]]:
    """Fetch document metadata from SQLite for the given IDs.

    Returns a list of dicts with keys ``id``, ``title``, ``content``.
    Returns an empty list if the database file is missing or no rows match.
    """
    if not doc_ids:
        return []

    db_path = _get_sqlite_path()
    if not db_path.exists():
        logger.warning("SQLite database not found at %s", db_path)
        return []

    logger.info("Connecting to SQLite: %s", db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        placeholders = ",".join("?" * len(doc_ids))
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, title, content FROM documents WHERE id IN ({placeholders})",
            list(doc_ids),
        )
        rows = cursor.fetchall()
        return [{"id": row[0], "title": row[1], "content": row[2]} for row in rows]
    finally:
        conn.close()


def _categorize_doc_length(content: str) -> str:
    """Classify document by content character length.

    - ``short``: < 6000 characters
    - ``medium_len``: 6000 -- 15000 characters
    - ``long``: > 15000 characters
    """
    length = len(content)
    if length < 6000:
        return "short"
    if length <= 15000:
        return "medium_len"
    return "long"


def _is_valid(v: float | None) -> bool:
    return v is not None and not math.isnan(v)


def _aggregate_metrics(samples: list[dict]) -> dict[str, Any]:
    """Compute summary statistics across a list of sample results.

    Returns a dict with keys ``faithfulness``, ``format_compliance``,
    and ``question_quality``.
    Each metric value is a dict with ``mean`` and ``std`` (except
    ``format_compliance`` which has ``rate``).
    """
    faithfulness = [
        s["faithfulness"]
        for s in samples
        if _is_valid(s.get("faithfulness"))
    ]
    quality = [
        s["question_quality_score"]
        for s in samples
        if _is_valid(s.get("question_quality_score"))
    ]

    compliance_rates = [s.get("format_compliance_rate", 1.0) for s in samples]
    avg_compliance = (
        round(statistics.mean(compliance_rates), 4) if compliance_rates else 1.0
    )

    return {
        "faithfulness": _compute_stats(faithfulness),
        "format_compliance": {"rate": avg_compliance},
        "question_quality": _compute_stats(quality),
    }


async def run_evaluation(
    seed: int = 42,
    difficulties: list[str] | None = None,
    question_count: int = 3,
    max_docs: int | None = None,
) -> dict[str, Any]:
    """Run the full RAGAS evaluation pipeline end-to-end.

    Args:
        seed: Random seed for reproducibility.
        difficulties: List of difficulty levels to evaluate
            (``"easy"``, ``"medium"``, ``"hard"``).  Defaults to all three.
        question_count: Number of questions to generate per (doc, difficulty)
            sample.
        max_docs: Maximum number of documents to evaluate (for quick smoke
            tests).  ``None`` means all documents.

    Returns:
        A dict containing the complete evaluation results:

        .. code-block:: python

            {
                "commit": str,
                "timestamp": str,            # ISO-8601 UTC
                "config": { ... },
                "aggregate": { ... },         # overall metrics
                "by_difficulty": { ... },     # per-difficulty metrics
                "by_doc_length": { ... },     # per-length-category metrics
                "samples": [ ... ],           # per-sample results
                "errors": [ ... ],            # per-sample error records
            }
    """
    random.seed(seed)

    if difficulties is None:
        difficulties = ["easy", "medium", "hard"]

    logger.info(
        "Starting RAGAS evaluation: seed=%s difficulties=%s question_count=%d",
        seed,
        difficulties,
        question_count,
    )

    # ------------------------------------------------------------------
    # 3.  Collect document IDs from ChromaDB
    # ------------------------------------------------------------------
    doc_ids = _get_doc_ids_from_chromadb()
    if not doc_ids:
        logger.warning("ChromaDB contains no document chunks; returning empty result")
        empty: dict[str, Any] = {
            "commit": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "seed": seed,
                "difficulties": difficulties,
                "question_count": question_count,
            },
            "aggregate": {},
            "by_difficulty": {},
            "by_doc_length": {},
            "samples": [],
            "errors": ["ChromaDB contains no document chunks"],
        }
        return empty

    logger.info("Found %d document IDs in ChromaDB: %s", len(doc_ids), sorted(doc_ids))

    # ------------------------------------------------------------------
    # 4.  Load document metadata from SQLite
    # ------------------------------------------------------------------
    documents = _get_documents_from_sqlite(doc_ids)
    if not documents:
        logger.warning("No documents found in SQLite for ChromaDB IDs")
        empty = {
            "commit": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "seed": seed,
                "difficulties": difficulties,
                "question_count": question_count,
            },
            "aggregate": {},
            "by_difficulty": {},
            "by_doc_length": {},
            "samples": [],
            "errors": ["No documents found in SQLite for ChromaDB IDs"],
        }
        return empty

    logger.info("Loaded %d documents from SQLite", len(documents))

    # Limit documents when max_docs is specified (for quick smoke tests)
    if max_docs is not None and max_docs < len(documents):
        logger.info("Limiting evaluation to %d documents (max_docs=%d)", max_docs, max_docs)
        documents = documents[:max_docs]

    # Pre-build metrics once (reused across all evaluate() calls)
    metrics = build_ragas_metrics()

    samples: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 5.  Evaluate each (doc, difficulty) pair
    # ------------------------------------------------------------------
    for doc in documents:
        doc_id: int = doc["id"]
        content: str = doc["content"]
        title: str = doc["title"]
        doc_length_cat = _categorize_doc_length(content)

        # 5a.  Parse document into chunks
        parsed = parse_text(content)
        chunks = parsed.chunks

        logger.info(
            "Processing doc_id=%d title=%s chunks=%d length_cat=%s",
            doc_id,
            title,
            len(chunks),
            doc_length_cat,
        )

        for difficulty in difficulties:
            logger.info(
                "Evaluating sample: doc_id=%d difficulty=%s",
                doc_id,
                difficulty,
            )

            try:
                # 5b.  Build difficulty-aware query
                query_text = _build_query_from_chunks(chunks, difficulty)

                # 5c.  Retrieve contexts via RAG
                retrieved_contexts = await query_for_quiz(
                    document_id=doc_id,
                    difficulty=difficulty,
                    chunks=chunks,
                )
                if not retrieved_contexts:
                    logger.warning(
                        "Empty retrieval for doc_id=%d difficulty=%s; skipping",
                        doc_id,
                        difficulty,
                    )
                    continue

                # 5d.  Generate quiz questions via DeepSeek
                questions = await generate_quiz(
                    knowledge_summary=retrieved_contexts,
                    difficulty=difficulty,
                    question_count=question_count,
                    batch_size=question_count,
                )

                # 5e.  Convert questions to natural language paragraphs
                questions_text = questions_to_text(questions)

                # 5f.  Check format compliance
                compliance = check_format_compliance(questions)
                format_compliance_rate = compliance["rate"]

                # 5g.  Score question quality (average across questions)
                quality_scores: list[float] = []
                for q in questions:
                    try:
                        quality_result = await score_question_quality(
                            question=q,
                            knowledge_context=retrieved_contexts,
                        )
                        quality_scores.append(float(quality_result["score"]))
                    except Exception as exc:
                        logger.warning(
                            "Quality scoring failed for q=%s: %s",
                            q.get("content", "?")[:40],
                            exc,
                        )
                        quality_scores.append(0.0)

                avg_quality = (
                    round(statistics.mean(quality_scores), 4)
                    if quality_scores
                    else 0.0
                )

                # 5h.  Build RAGAS SingleTurnSample
                sample = SingleTurnSample(
                    user_input=query_text,
                    retrieved_contexts=retrieved_contexts.split("\n\n"),
                    response=questions_text,
                )

                # 5i.  Evaluate with RAGAS metrics
                dataset = EvaluationDataset([sample])
                eval_result = evaluate(dataset, metrics=metrics)
                df = eval_result.to_pandas()

                ragas_scores = {
                    "faithfulness": float(df["faithfulness"].iloc[0]) if "faithfulness" in df.columns else 0.0,
                }

                logger.info(
                    "RAGAS: doc_id=%d diff=%s faithfulness=%.4f",
                    doc_id,
                    difficulty,
                    ragas_scores["faithfulness"],
                )

                # 5j.  Assemble sample result
                samples.append(
                    {
                        "doc_id": doc_id,
                        "title": title,
                        "difficulty": difficulty,
                        "doc_length_category": doc_length_cat,
                        "doc_length": len(content),
                        "chunk_count": len(chunks),
                        "query": query_text,
                        "retrieved_chunks_count": len(
                            retrieved_contexts.split("\n\n")
                        ),
                        "questions_count": len(questions),
                        "format_compliance_rate": format_compliance_rate,
                        "format_compliance_errors": compliance["errors"],
                        "question_quality_score": avg_quality,
                        "question_quality_scores": quality_scores,
                        **ragas_scores,
                    }
                )

            except Exception as exc:
                logger.exception(
                    "Failed sample: doc_id=%d difficulty=%s — %s",
                    doc_id,
                    difficulty,
                    exc,
                )
                errors.append(
                    {
                        "doc_id": doc_id,
                        "title": title,
                        "difficulty": difficulty,
                        "error": str(exc),
                    }
                )

    # ------------------------------------------------------------------
    # 6.  Aggregate scores (overall)
    # ------------------------------------------------------------------
    aggregate = _aggregate_metrics(samples)

    # ------------------------------------------------------------------
    # 7.  Aggregate by difficulty
    # ------------------------------------------------------------------
    by_difficulty: dict[str, dict[str, Any]] = {}
    for diff in difficulties:
        diff_samples = [s for s in samples if s["difficulty"] == diff]
        if diff_samples:
            by_difficulty[diff] = _aggregate_metrics(diff_samples)

    # ------------------------------------------------------------------
    # 8.  Aggregate by document length
    # ------------------------------------------------------------------
    by_doc_length: dict[str, dict[str, Any]] = {}
    for length_cat in ("short", "medium_len", "long"):
        length_samples = [
            s for s in samples if s.get("doc_length_category") == length_cat
        ]
        if length_samples:
            by_doc_length[length_cat] = _aggregate_metrics(length_samples)

    # ------------------------------------------------------------------
    # 9.  Assemble final results dict
    # ------------------------------------------------------------------
    results: dict[str, Any] = {
        "commit": "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "seed": seed,
            "difficulties": difficulties,
            "question_count": question_count,
        },
        "aggregate": aggregate,
        "by_difficulty": by_difficulty,
        "by_doc_length": by_doc_length,
        "samples": samples,
        "errors": errors,
    }

    # ------------------------------------------------------------------
    # 10.  Persist results via reporter
    # ------------------------------------------------------------------
    try:
        write_latest_json(results)
        write_history(results)
        write_report(results)
        logger.info("Evaluation results persisted to ragas_output/")
    except Exception as exc:
        logger.error("Failed to persist evaluation results: %s", exc)
        errors.append({"phase": "persist", "error": str(exc)})
        results["errors"] = errors

    logger.info(
        "RAGAS evaluation complete: %d samples, %d errors",
        len(samples),
        len(errors),
    )

    return results
