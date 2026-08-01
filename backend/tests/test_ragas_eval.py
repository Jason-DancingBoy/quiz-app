"""RAGAS evaluation -- pytest entry point.

Manual run:  pytest backend/tests/test_ragas_eval.py -v
CI run:      RAGAS_CI=1 pytest backend/tests/test_ragas_eval.py -v
"""

import json
import os
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# NOTE: Environment variables (BASIC_AUTH_USER, CHROMA_PERSIST_DIR,
# DATABASE_URL, EMBEDDING_MODEL_PATH) are set in conftest.py, which is
# loaded before any test module.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ragas_evaluation_runs():
    """Verify the evaluation script completes and produces output files."""
    from backend.tests.ragas_eval.runner import run_evaluation

    results = await run_evaluation(seed=42, difficulties=["easy"], question_count=1, max_docs=1)

    # Assert structure
    assert "aggregate" in results
    assert "samples" in results
    assert "errors" in results

    # Verify output files exist
    output_dir = Path(__file__).resolve().parent / "ragas_output"
    assert (output_dir / "ragas_results_latest.json").exists(), "ragas_results_latest.json not found"
    assert (output_dir / "ragas_results_history.jsonl").exists(), "ragas_results_history.jsonl not found"
    assert (output_dir / "ragas_report.txt").exists(), "ragas_report.txt not found"

    # Verify JSON is valid
    with open(output_dir / "ragas_results_latest.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["config"]["seed"] == 42

    # Log summary
    agg = results.get("aggregate", {})
    print(f"\nRAGAS Evaluation Summary:")
    for key, val in agg.items():
        print(f"  {key}: {val}")
    print(f"  samples: {len(results['samples'])}")
    print(f"  errors: {len(results['errors'])}")

    # In CI mode, assert minimum quality thresholds
    if os.environ.get("RAGAS_CI") == "1":
        faithfulness = agg.get("faithfulness", {}).get("mean", 0)
        assert faithfulness > 0.6, f"Faithfulness too low: {faithfulness}"


@pytest.mark.asyncio
async def test_ragas_evaluation_empty_handling():
    """Verify evaluation handles missing data gracefully (smoke test)."""
    from backend.tests.ragas_eval.runner import run_evaluation

    # Should not crash, even if we don't have specific doc_ids
    results = await run_evaluation(seed=42, difficulties=["easy"], question_count=1)
    assert isinstance(results, dict)
    assert "samples" in results
