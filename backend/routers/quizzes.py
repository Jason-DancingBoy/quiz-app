import asyncio
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Document, Quiz, Question, Attempt, Answer
from backend.schemas import (
    GenerateRequest, QuizStatus, QuizReady, QuestionPreview,
    SubmitRequest, ReviewOut, AnswerResult, QuizHistoryItem,
)
from backend.services.parser import parse_file, parse_text
from backend.services.rag_service import insert_chunks, query_for_quiz
from backend.services.generator import generate_quiz
from backend.services.quota import check_quota, increment_quota

router = APIRouter(tags=["quizzes"])

MAX_CONTEXT_CHARS = 12000


@router.post("/documents/{doc_id}/generate", response_model=QuizStatus)
async def generate_quiz_endpoint(
    doc_id: int,
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    existing = (await db.execute(
        select(Quiz).where(Quiz.document_id == doc_id, Quiz.status == "generating")
    )).scalar()
    if existing:
        raise HTTPException(409, "A quiz is already being generated for this document")

    if not check_quota():
        raise HTTPException(429, "Daily quota exceeded (50/day)")

    quiz = Quiz(
        document_id=doc_id,
        status="generating",
        difficulty=body.difficulty,
        total=body.question_count,
        progress="解析文档中...",
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)

    asyncio.create_task(
        _run_generation(quiz.id, doc, body.difficulty, body.question_count)
    )

    return QuizStatus(id=quiz.id, status="generating", progress="解析文档中...")


async def _run_generation(quiz_id: int, doc: Document, difficulty: str, count: int):
    from backend.database import async_session
    async with async_session() as db:
        try:
            quiz = await db.get(Quiz, quiz_id)

            quiz.progress = "切分文档..."
            await db.commit()

            chunks = parse_text(doc.content).chunks

            quiz.progress = f"构建知识索引 ({len(chunks)} 块)..."
            await db.commit()

            await insert_chunks(doc.id, chunks)

            quiz.progress = "检索关键知识点..."
            await db.commit()

            knowledge = await query_for_quiz(doc.id, difficulty)

            context = "\n\n".join(chunks)
            if len(context) > MAX_CONTEXT_CHARS:
                context = context[:MAX_CONTEXT_CHARS]

            quiz.progress = f"生成 {count} 道题目..."
            await db.commit()

            questions = await generate_quiz(context, knowledge, difficulty, count)

            quiz.progress = "保存题目..."
            await db.commit()

            for i, q in enumerate(questions):
                question = Question(
                    quiz_id=quiz.id,
                    content=q["content"],
                    options=q["options"],
                    correct_index=q["correct_index"],
                    explanation=q["explanation"],
                    order_num=i + 1,
                )
                db.add(question)

            quiz.status = "ready"
            quiz.progress = None
            await db.commit()
            increment_quota()

        except Exception as e:
            quiz = await db.get(Quiz, quiz_id)
            if quiz:
                quiz.status = "failed"
                quiz.progress = f"生成失败: {str(e)[:200]}"
                await db.commit()


@router.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: int, db: AsyncSession = Depends(get_db)):
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    if quiz.status == "generating":
        return QuizStatus(id=quiz.id, status="generating", progress=quiz.progress)

    if quiz.status == "failed":
        return QuizStatus(id=quiz.id, status="failed", progress=quiz.progress)

    questions = (await db.execute(
        select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_num)
    )).scalars().all()

    return QuizReady(
        id=quiz.id,
        status="ready",
        difficulty=quiz.difficulty,
        total=quiz.total,
        questions=[
            QuestionPreview(
                id=q.id,
                content=q.content,
                options=q.options,
                order_num=q.order_num,
            )
            for q in questions
        ],
    )


@router.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: int, body: SubmitRequest, db: AsyncSession = Depends(get_db)):
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    if quiz.status != "ready":
        raise HTTPException(400, "Quiz is not ready")

    existing_attempt = (await db.execute(
        select(Attempt).where(Attempt.quiz_id == quiz_id)
    )).scalar()
    if existing_attempt:
        raise HTTPException(409, "This quiz has already been submitted")

    questions = (await db.execute(
        select(Question).where(Question.quiz_id == quiz_id)
    )).scalars().all()
    question_map = {q.id: q for q in questions}

    attempt = Attempt(quiz_id=quiz_id)
    db.add(attempt)
    await db.flush()

    correct_count = 0
    for ans in body.answers:
        question = question_map.get(ans.question_id)
        if not question:
            continue
        is_correct = 1 if ans.selected_index == question.correct_index else 0
        correct_count += is_correct
        answer = Answer(
            attempt_id=attempt.id,
            question_id=ans.question_id,
            selected_index=ans.selected_index,
            is_correct=is_correct,
        )
        db.add(answer)

    import datetime
    attempt.completed_at = datetime.datetime.utcnow()
    quiz.score = correct_count
    await db.commit()

    review = await _build_review(quiz_id, attempt.id, db)
    return review


async def _build_review(quiz_id: int, attempt_id: int, db: AsyncSession) -> dict:
    quiz = await db.get(Quiz, quiz_id)
    questions = (await db.execute(
        select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_num)
    )).scalars().all()
    answers = (await db.execute(
        select(Answer).where(Answer.attempt_id == attempt_id)
    )).scalars().all()
    answer_map = {a.question_id: a for a in answers}

    results = []
    for q in questions:
        ans = answer_map.get(q.id)
        results.append(AnswerResult(
            question_id=q.id,
            selected_index=ans.selected_index if ans else -1,
            correct_index=q.correct_index,
            is_correct=bool(ans.is_correct) if ans else False,
            explanation=q.explanation,
        ))

    return ReviewOut(
        quiz_id=quiz_id,
        score=quiz.score or 0,
        total=quiz.total,
        answers=results,
    ).model_dump()


@router.get("/quizzes/{quiz_id}/review", response_model=ReviewOut)
async def get_review(quiz_id: int, db: AsyncSession = Depends(get_db)):
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    attempt = (await db.execute(
        select(Attempt).where(Attempt.quiz_id == quiz_id)
    )).scalar()
    if not attempt:
        raise HTTPException(400, "Quiz has not been submitted yet")

    return await _build_review(quiz_id, attempt.id, db)


@router.get("/quizzes", response_model=list[QuizHistoryItem])
async def list_quizzes(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Quiz, Document.title).join(Document, Quiz.document_id == Document.id)
        .order_by(Quiz.created_at.desc())
    )).all()

    return [
        QuizHistoryItem(
            id=quiz.id,
            document_title=doc_title,
            difficulty=quiz.difficulty,
            total=quiz.total,
            score=quiz.score,
            created_at=quiz.created_at,
        )
        for quiz, doc_title in rows
    ]
