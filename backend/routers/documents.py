import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.logger import get_logger
from backend.models import Document, Quiz, Question, Attempt, Answer
from backend.schemas import DocumentCreate, DocumentOut, DocumentDetail
from backend.services.parser import parse_text, parse_file, PARSERS
from backend.services.rag_service import delete_chunks
from backend.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

logger = get_logger(__name__)
router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentOut)
async def create_document_paste(
    body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Creating paste document: title='%s' len=%d", body.title, len(body.content))
    doc = Document(title=body.title, source_type="paste", content=body.content)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    logger.info("Paste document created: id=%d", doc.id)
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        created_at=doc.created_at,
        quiz_count=0,
    )


@router.post("/documents/upload", response_model=DocumentOut)
async def create_document_upload(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    logger.info("Uploading document: filename='%s'", file.filename)
    ext = os.path.splitext(file.filename or "unknown")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Upload rejected: unsupported type '%s'", ext)
        raise HTTPException(400, f"Unsupported file type: {ext}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        logger.warning("Upload rejected: file too large (%d bytes)", len(content))
        raise HTTPException(400, f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4().hex
    filepath = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(filepath, "wb") as f:
        f.write(content)
    logger.info("File saved: %s (%d bytes)", filepath, len(content))

    try:
        parsed = parse_file(filepath)
        logger.info("File parsed: %d chunks extracted", len(parsed.chunks))
    except Exception as e:
        logger.error("Failed to parse file '%s': %s", filepath, e)
        raise HTTPException(400, f"Failed to parse file: {e}")

    doc = Document(
        title=file.filename or "untitled",
        source_type="upload",
        file_path=filepath,
        content=parsed.title + "\n\n" + "\n\n".join(parsed.chunks),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    logger.info("Upload document created: id=%d title='%s'", doc.id, doc.title)
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        created_at=doc.created_at,
        quiz_count=0,
    )


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    docs = (await db.execute(
        select(Document).where(Document.source_type != "vault").order_by(Document.created_at.desc())
    )).scalars().all()
    result = []
    for doc in docs:
        count = (await db.execute(
            select(func.count(Quiz.id)).where(Quiz.document_id == doc.id)
        )).scalar()
        result.append(DocumentOut(
            id=doc.id,
            title=doc.title,
            source_type=doc.source_type,
            created_at=doc.created_at,
            quiz_count=count or 0,
        ))
    return result


@router.get("/documents/{doc_id}", response_model=DocumentOut | DocumentDetail)
async def get_document(doc_id: int, include_content: bool = False, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    count = (await db.execute(
        select(func.count(Quiz.id)).where(Quiz.document_id == doc.id)
    )).scalar()
    if include_content:
        return DocumentDetail(
            id=doc.id,
            title=doc.title,
            source_type=doc.source_type,
            created_at=doc.created_at,
            quiz_count=count or 0,
            content=doc.content,
        )
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        created_at=doc.created_at,
        quiz_count=count or 0,
    )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.source_type == "vault":
        raise HTTPException(403, "Cannot delete the vault document")

    logger.info("Deleting document: id=%d title='%s'", doc_id, doc.title)
    quizzes = (await db.execute(select(Quiz).where(Quiz.document_id == doc_id))).scalars().all()
    for quiz in quizzes:
        attempts = (await db.execute(select(Attempt).where(Attempt.quiz_id == quiz.id))).scalars().all()
        for attempt in attempts:
            await db.execute(delete(Answer).where(Answer.attempt_id == attempt.id))
        await db.execute(delete(Attempt).where(Attempt.quiz_id == quiz.id))
        await db.execute(delete(Question).where(Question.quiz_id == quiz.id))
    await db.execute(delete(Quiz).where(Quiz.document_id == doc_id))
    await db.delete(doc)

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
        logger.info("Deleted uploaded file: %s", doc.file_path)

    await db.commit()
    logger.info("Document deleted: id=%d", doc_id)

    try:
        await delete_chunks(doc_id)
    except Exception as e:
        logger.warning("Failed to delete ChromaDB chunks (non-fatal): %s", e)

    return {"ok": True}
