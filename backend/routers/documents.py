import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Document, Quiz, Question
from backend.schemas import DocumentCreate, DocumentOut
from backend.services.parser import parse_text, parse_file, PARSERS
from backend.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentOut)
async def create_document_paste(
    body: DocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    doc = Document(title=body.title, source_type="paste", content=body.content)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
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
    ext = os.path.splitext(file.filename or "unknown")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 10MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4().hex
    filepath = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(filepath, "wb") as f:
        f.write(content)

    try:
        parsed = parse_file(filepath)
    except Exception as e:
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
    return DocumentOut(
        id=doc.id,
        title=doc.title,
        source_type=doc.source_type,
        created_at=doc.created_at,
        quiz_count=0,
    )


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    docs = (await db.execute(select(Document).order_by(Document.created_at.desc()))).scalars().all()
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


@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    count = (await db.execute(
        select(func.count(Quiz.id)).where(Quiz.document_id == doc.id)
    )).scalar()
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

    quizzes = (await db.execute(select(Quiz).where(Quiz.document_id == doc_id))).scalars().all()
    for quiz in quizzes:
        await db.execute(delete(Question).where(Question.quiz_id == quiz.id))
    await db.execute(delete(Quiz).where(Quiz.document_id == doc_id))
    await db.delete(doc)

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.commit()
    return {"ok": True}
