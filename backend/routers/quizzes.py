import asyncio
import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.logger import get_logger
from backend.models import Document, Quiz, Question, Attempt, Answer
from backend.schemas import (
    GenerateRequest, QuizStatus, QuizReady, QuestionPreview,
    SubmitRequest, ReviewOut, AnswerResult, QuizHistoryItem,
)
from backend.config import VAULT_DIR, LARGE_DOC_CHUNK_THRESHOLD
from backend.services.parser import parse_file, parse_text
from backend.services.rag_service import insert_chunks, query_for_quiz, sample_chunks
from backend.services.generator import generate_quiz, generate_single_question, split_knowledge_segments
from backend.services.quota import check_quota, increment_quota
from backend.services.vault_service import scan_vault_files, build_vault_content

logger = get_logger(__name__)
router = APIRouter(tags=["quizzes"])

_background_tasks: set[asyncio.Task] = set()


def _track_task(task: asyncio.Task):
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def cancel_background_tasks():
    for task in list(_background_tasks):
        task.cancel()
    if _background_tasks:
        await asyncio.gather(*_background_tasks, return_exceptions=True)


import json as json_module

_stream_queues: dict[int, asyncio.Queue] = {}


@router.post("/documents/{doc_id}/generate", response_model=QuizStatus)
async def generate_quiz_endpoint(
    doc_id: int,
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Quiz generation requested: doc_id=%d difficulty=%s count=%d", doc_id, body.difficulty, body.question_count)
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")

    existing = (await db.execute(
        select(Quiz).where(Quiz.document_id == doc_id, Quiz.status == "generating")
    )).scalar()
    if existing:
        import datetime
        elapsed = (datetime.datetime.utcnow() - existing.created_at).total_seconds()
        if elapsed < 300:
            logger.warning("Quiz generation blocked: another generation in progress for doc_id=%d", doc_id)
            raise HTTPException(409, "A quiz is already being generated for this document")
        existing.status = "failed"
        existing.progress = "生成超时，请重试"
        await db.commit()
        logger.info("Timed-out quiz reset: quiz_id=%d", existing.id)

    if not check_quota():
        logger.warning("Quiz generation blocked: daily quota exceeded")
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
    logger.info("Quiz record created: quiz_id=%d doc_id=%d", quiz.id, doc_id)

    task = asyncio.create_task(
        _run_generation(quiz.id, doc, body.difficulty, body.question_count)
    )
    _track_task(task)

    return QuizStatus(id=quiz.id, status="generating", progress="解析文档中...", total_count=body.question_count)


async def _get_or_create_vault_document(db: AsyncSession) -> Document:
    result = await db.execute(
        select(Document).where(Document.source_type == "vault")
    )
    doc = result.scalar_one_or_none()
    if not doc:
        doc = Document(
            title="Vault 笔记库",
            source_type="vault",
            content="",
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        logger.info("Vault document created: id=%d", doc.id)
    return doc


@router.post("/vault/generate", response_model=QuizStatus)
async def generate_quiz_from_vault(
    body: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Vault quiz generation requested: difficulty=%s count=%d", body.difficulty, body.question_count)

    vault_doc = await _get_or_create_vault_document(db)

    files = scan_vault_files(VAULT_DIR)
    if not files:
        raise HTTPException(400, "Vault 目录为空或不可访问")

    vault_doc.content = build_vault_content(files)
    await db.commit()
    await db.refresh(vault_doc)
    logger.info("Vault content synced: %d files, %d chars", len(files), len(vault_doc.content))

    existing = (await db.execute(
        select(Quiz).where(Quiz.document_id == vault_doc.id, Quiz.status == "generating")
    )).scalars().all()
    for q in existing:
        import datetime
        elapsed = (datetime.datetime.utcnow() - q.created_at).total_seconds()
        if elapsed < 300:
            raise HTTPException(409, "Vault 题目正在生成中，请稍后再试")
        q.status = "failed"
    await db.commit()

    if not check_quota():
        raise HTTPException(429, "Daily quota exceeded (50/day)")

    quiz = Quiz(
        document_id=vault_doc.id,
        status="generating",
        difficulty=body.difficulty,
        total=body.question_count,
        progress="解析 Vault 文档中...",
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    logger.info("Vault quiz record created: quiz_id=%d", quiz.id)

    task = asyncio.create_task(
        _run_generation(quiz.id, vault_doc, body.difficulty, body.question_count)
    )
    _track_task(task)

    return QuizStatus(id=quiz.id, status="generating", progress="解析 Vault 文档中...", total_count=body.question_count)


async def _push_progress(quiz_id: int, message: str, generated: int = 0, total: int = 0):
    """Push a progress event to the SSE queue if it exists."""
    q = _stream_queues.get(quiz_id)
    if q:
        await q.put({
            "type": "progress",
            "message": message,
            "generated_count": generated,
            "total_count": total,
        })


async def _do_generate(quiz_id: int, doc: Document, difficulty: str, count: int):
    from backend.database import async_session
    async with async_session() as db:
        try:
            quiz = await db.get(Quiz, quiz_id)

            quiz.progress = "切分文档..."
            await db.commit()
            await _push_progress(quiz_id, "切分文档...", 0, count)
            logger.info("Generation progress (quiz_id=%d): chunking document", quiz_id)

            chunks = parse_text(doc.content).chunks
            logger.info("Generation progress (quiz_id=%d): %d chunks created", quiz_id, len(chunks))

            total_chunk_text = "".join(chunks)
            SHORT_DOC_THRESHOLD = 6000  # chars — skip RAG if total content fits easily in LLM context

            if len(total_chunk_text) <= SHORT_DOC_THRESHOLD:
                quiz.progress = "文档较短，跳过检索..."
                await db.commit()
                await _push_progress(quiz_id, "文档较短，跳过检索...", 0, count)
                knowledge = total_chunk_text
                logger.info("Generation progress (quiz_id=%d): short doc (%d chars), skipping RAG", quiz_id, len(knowledge))
            elif len(chunks) <= LARGE_DOC_CHUNK_THRESHOLD:
                quiz.progress = f"构建知识索引 ({len(chunks)} 块)..."
                await db.commit()
                await _push_progress(quiz_id, f"构建知识索引 ({len(chunks)} 块)...", 0, count)

                async def _embed_progress(done, total):
                    await _push_progress(quiz_id, f"构建知识索引 ({done}/{total} 块)...", 0, count)

                await insert_chunks(doc.id, chunks, progress_callback=_embed_progress)
                logger.info("Generation progress (quiz_id=%d): embeddings inserted", quiz_id)

                quiz.progress = "检索关键知识点..."
                await db.commit()
                await _push_progress(quiz_id, "检索关键知识点...", 0, count)

                knowledge = await query_for_quiz(doc.id, difficulty, chunks)
                logger.info("Generation progress (quiz_id=%d): knowledge retrieved (%d chars)", quiz_id, len(knowledge))
            else:
                quiz.progress = f"文档较大 ({len(chunks)} 块)，均匀采样中..."
                await db.commit()
                await _push_progress(quiz_id, f"文档较大 ({len(chunks)} 块)，均匀采样中...", 0, count)

                sampled = sample_chunks(chunks)
                knowledge = "\n\n".join(sampled)
                logger.info("Generation progress (quiz_id=%d): %d chunks sampled to %d (no embedding)", quiz_id, len(chunks), len(sampled))

            quiz.progress = "规划题目覆盖范围..."
            await db.commit()
            await _push_progress(quiz_id, "规划题目覆盖范围...", 0, count)

            total = count
            segments = split_knowledge_segments(knowledge, total)
            logger.info("Generation progress (quiz_id=%d): knowledge split into %d segments for topic diversity", quiz_id, len(segments))

            quiz.progress = f"并行生成 {total} 道题目..."
            await db.commit()
            await _push_progress(quiz_id, f"并行生成 {total} 道题目...", 0, count)

            async def _gen_one(i):
                segment = segments[i] if i < len(segments) and segments[i] else knowledge
                return await generate_single_question(segment, difficulty, i + 1, total)

            tasks = [asyncio.create_task(_gen_one(i)) for i in range(total)]

            # Collect results as they complete, save to DB sequentially
            all_questions = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                order_num = len(all_questions) + 1

                question = Question(
                    quiz_id=quiz.id,
                    content=result["content"],
                    options=result["options"],
                    correct_index=result["correct_index"],
                    explanation=result["explanation"],
                    order_num=order_num,
                )
                db.add(question)
                await db.commit()
                await db.refresh(question)

                all_questions.append(result)

                # Update progress
                quiz.progress = f"已生成 {len(all_questions)}/{total} 题..."
                await db.commit()

                # Push to SSE queue
                q = _stream_queues.get(quiz_id)
                if q:
                    await q.put({
                        "type": "question",
                        "question": {
                            "id": question.id,
                            "content": question.content,
                            "options": question.options,
                            "order_num": question.order_num,
                        },
                        "generated_count": len(all_questions),
                        "total_count": total,
                    })

                logger.info("Generation progress (quiz_id=%d): generated %d/%d questions", quiz_id, len(all_questions), total)

            # All done
            quiz.status = "ready"
            quiz.progress = None
            await db.commit()
            increment_quota()

            q = _stream_queues.get(quiz_id)
            if q:
                await q.put({"type": "done", "generated_count": total, "total_count": total})
            logger.info("Background generation completed successfully: quiz_id=%d questions=%d", quiz_id, len(all_questions))

        except Exception as e:
            logger.error("Background generation failed: quiz_id=%d error=%s", quiz_id, e)
            quiz = await db.get(Quiz, quiz_id)
            if quiz:
                quiz.status = "failed"
                quiz.progress = f"生成失败: {str(e)[:200]}"
                await db.commit()
            q = _stream_queues.get(quiz_id)
            if q:
                await q.put({"type": "error", "message": str(e)[:200]})


async def _run_generation(quiz_id: int, doc: Document, difficulty: str, count: int):
    logger.info("Background generation started: quiz_id=%d difficulty=%s count=%d", quiz_id, difficulty, count)

    # Create SSE queue early so the frontend can receive progress from the start
    queue = asyncio.Queue()
    _stream_queues[quiz_id] = queue

    try:
        await asyncio.wait_for(
            _do_generate(quiz_id, doc, difficulty, count),
            timeout=300,
        )
    except asyncio.TimeoutError:
        logger.error("Background generation timed out: quiz_id=%d", quiz_id)
        from backend.database import async_session
        async with async_session() as db:
            quiz = await db.get(Quiz, quiz_id)
            if quiz:
                quiz.status = "failed"
                quiz.progress = "生成超时，请尝试上传较小的文件"
                await db.commit()
        q = _stream_queues.get(quiz_id)
        if q:
            await q.put({"type": "error", "message": "生成超时，请尝试上传较小的文件"})
    finally:
        _stream_queues.pop(quiz_id, None)


@router.get("/quizzes/{quiz_id}/stream")
async def stream_quiz(quiz_id: int, db: AsyncSession = Depends(get_db)):
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    # Query existing questions before streaming (DB session won't last in generator)
    existing = (await db.execute(
        select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_num)
    )).scalars().all()

    existing_data = [
        {
            "id": q.id,
            "content": q.content,
            "options": q.options,
            "order_num": q.order_num,
        }
        for q in existing
    ]

    current_status = quiz.status
    current_total = quiz.total
    error_msg = quiz.progress if quiz.status == "failed" else None

    async def event_generator():
        # Send any already-generated questions first
        for q in existing_data:
            event = {
                "type": "question",
                "question": q,
                "generated_count": len(existing_data),
                "total_count": current_total,
            }
            yield f"data: {json_module.dumps(event)}\n\n"

        if current_status == "ready":
            yield f"data: {json_module.dumps({'type': 'done', 'total_count': current_total})}\n\n"
            return

        if current_status == "failed":
            yield f"data: {json_module.dumps({'type': 'error', 'message': error_msg})}\n\n"
            return

        # Wait for queue (background task creates it)
        queue = None
        for _ in range(60):  # 60 * 0.5s = 30s max wait
            queue = _stream_queues.get(quiz_id)
            if queue:
                break
            await asyncio.sleep(0.5)

        if queue:
            while True:
                event = await queue.get()
                yield f"data: {json_module.dumps(event)}\n\n"
                if event["type"] in ("done", "error"):
                    break
        else:
            yield f"data: {json_module.dumps({'type': 'error', 'message': 'Generation timed out'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/quizzes/{quiz_id}")
async def get_quiz(quiz_id: int, db: AsyncSession = Depends(get_db)):
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    if quiz.status == "generating":
        partial_questions = (await db.execute(
            select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_num)
        )).scalars().all()

        return QuizStatus(
            id=quiz.id,
            status="generating",
            progress=quiz.progress,
            questions=[
                QuestionPreview(
                    id=q.id,
                    content=q.content,
                    options=q.options,
                    order_num=q.order_num,
                )
                for q in partial_questions
            ],
            generated_count=len(partial_questions),
            total_count=quiz.total,
        )

    if quiz.status == "failed":
        return QuizStatus(id=quiz.id, status="failed", progress=quiz.progress)

    questions = (await db.execute(
        select(Question).where(Question.quiz_id == quiz_id).order_by(Question.order_num)
    )).scalars().all()

    existing_attempt = (await db.execute(
        select(Attempt).where(Attempt.quiz_id == quiz_id)
    )).scalar()

    return QuizReady(
        id=quiz.id,
        status="ready",
        difficulty=quiz.difficulty,
        total=quiz.total,
        submitted=existing_attempt is not None,
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
    logger.info("Quiz submission: quiz_id=%d answer_count=%d", quiz_id, len(body.answers))
    quiz = await db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    if quiz.status != "ready":
        logger.warning("Quiz submission blocked: quiz_id=%d status=%s", quiz_id, quiz.status)
        raise HTTPException(400, "Quiz is not ready")

    existing_attempt = (await db.execute(
        select(Attempt).where(Attempt.quiz_id == quiz_id)
    )).scalar()
    if existing_attempt:
        logger.warning("Quiz submission blocked: quiz_id=%d already submitted", quiz_id)
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
    logger.info("Quiz submitted: quiz_id=%d score=%d/%d", quiz_id, correct_count, quiz.total)

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
            content=q.content,
            options=q.options,
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
