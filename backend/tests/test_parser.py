import pytest
from backend.services.parser import parse_text, chunk_text, ParsedDocument


def test_parse_markdown_text():
    text = "# Title\n\nParagraph one with enough content.\n\n## Section 2\n\nParagraph two here."
    doc = parse_text(text, title="test.md")
    assert doc.title == "test.md"
    assert len(doc.chunks) > 0


def test_chunk_text_short():
    text = "This is a short document with only one paragraph."
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long():
    text = "word " * 2000
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    assert len(chunks) > 1
    assert all(len(c) <= 550 for c in chunks)  # 500 + overlap buffer


def test_chunk_text_overlap():
    text = "word " * 800
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    first_end = chunks[0][-50:]
    second_start = chunks[1][:50]
    assert any(word in second_start for word in first_end.split())


class TestParsedDocument:
    def test_parsed_doc_creation(self):
        doc = ParsedDocument(title="test", chunks=["chunk1", "chunk2"])
        assert doc.title == "test"
        assert len(doc.chunks) == 2
