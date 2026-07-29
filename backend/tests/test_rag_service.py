import pytest
from backend.services.rag_service import sample_chunks, delete_chunks, insert_chunks


class TestSampleChunks:
    def test_short_input_returns_all(self):
        chunks = [f"chunk {i}" for i in range(10)]
        result = sample_chunks(chunks, n_buckets=30)
        assert len(result) == 10

    def test_large_input_samples_down(self):
        chunks = [f"chunk {i} unique content {i} " * 5 for i in range(1000)]
        result = sample_chunks(chunks, n_buckets=30)
        assert 15 <= len(result) <= 30

    def test_coverage_spans_entire_document(self):
        """Stratified sampling should pick chunks from across the full range."""
        chunks = [f"section {i:04d}" for i in range(1000)]
        result = sample_chunks(chunks, n_buckets=30)
        indices = [chunks.index(r) for r in result]
        # At least one chunk from first third and one from last third
        assert any(i < 333 for i in indices), "no chunk from first third"
        assert any(i > 666 for i in indices), "no chunk from last third"

    def test_overlap_dedup_removes_duplicates(self):
        chunks = ["the quick brown fox jumps over the lazy dog. " * 5] * 100
        result = sample_chunks(chunks, n_buckets=10)
        assert len(result) == 1

    def test_empty_input(self):
        assert sample_chunks([], n_buckets=30) == []
