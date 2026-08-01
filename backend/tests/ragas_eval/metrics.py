"""RAGAS evaluation metrics for quiz generation.

Provides:
- build_evaluator_llm / build_ragas_metrics: standard RAGAS metrics
- questions_to_text: convert JSON questions to natural language for Faithfulness
- check_format_compliance: validate question structure
- score_question_quality: LLM-based single-question quality scoring 1-5
"""

import json
import os
from typing import Any

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness

from backend.logger import get_logger

logger = get_logger(__name__)

EVALUATOR_MODEL = "deepseek-v4-pro"


def build_evaluator_llm() -> LangchainLLMWrapper:
    """Create RAGAS evaluator LLM (temperature=0 for reproducibility).

    Uses DeepSeek API configured via environment variables.
    """
    return LangchainLLMWrapper(ChatOpenAI(
        model=EVALUATOR_MODEL,
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
        temperature=0,
    ))


def build_ragas_metrics():
    """Return RAGAS standard metrics list with evaluator LLM injected.

    Metrics:
      - Faithfulness: whether the answer is faithful to the retrieved context
    """
    evaluator_llm = build_evaluator_llm()
    return [
        Faithfulness(llm=evaluator_llm),
    ]


def questions_to_text(questions: list[dict]) -> str:
    """Convert question JSON list to natural language paragraphs.

    RAGAS Faithfulness and answer-correctness metrics rely on claim extraction
    from natural language.  Converting structured JSON to paragraphs prevents
    the evaluator from extracting formatting-based "claims" and lets it focus
    on the actual question content.

    Each question is rendered as:

       题目：{content}
       选项：A. {options[0]}  B. {options[1]}  C. {options[2]}  D. {options[3]}
       正确答案：{letter}
       解析：{explanation}

    Questions are separated by a blank line.
    """
    paragraphs: list[str] = []
    for q in questions:
        letter = chr(65 + q["correct_index"])
        lines = [
            f"题目：{q['content']}",
            f"选项：A. {q['options'][0]}  B. {q['options'][1]}  C. {q['options'][2]}  D. {q['options'][3]}",
            f"正确答案：{letter}",
            f"解析：{q['explanation']}",
        ]
        paragraphs.append("\n".join(lines))
    return "\n\n".join(paragraphs)


def check_format_compliance(questions: list[dict]) -> dict:
    """Check question format compliance.

    Validates every question against the schema defined in SYSTEM_PROMPT:
      - Required fields: content, options, correct_index, explanation
      - options must be a list of exactly 4 items
      - correct_index must be an integer in 0-3
      - content must be a non-empty string

    Returns:
        dict with keys:
          - total (int): number of questions checked
          - passed (int): questions that passed all checks
          - rate (float): passed / total (1.0 if total == 0)
          - errors (list[dict]): each entry has {"index": int, "errors": [str, ...]}
    """
    total = len(questions)
    errors: list[dict[str, Any]] = []

    for i, q in enumerate(questions):
        issues = _validate_question(q)
        if issues:
            errors.append({"index": i, "errors": issues})

    passed = total - len(errors)
    rate = passed / total if total > 0 else 1.0

    return {
        "total": total,
        "passed": passed,
        "rate": rate,
        "errors": errors,
    }


def _validate_question(q: dict) -> list[str]:
    """Validate a single question dict and return a list of issue descriptions."""
    issues: list[str] = []

    required_fields = ["content", "options", "correct_index", "explanation"]
    for field in required_fields:
        if field not in q:
            issues.append(f"缺少字段 '{field}'")

    if "options" in q:
        if not isinstance(q["options"], list):
            issues.append("options 必须是列表")
        elif len(q["options"]) != 4:
            issues.append(f"options 数量为 {len(q['options'])}，应为 4")

    if "correct_index" in q:
        if not isinstance(q["correct_index"], int):
            issues.append("correct_index 必须是整数")
        elif q["correct_index"] not in range(4):
            issues.append(
                f"correct_index 值 {q['correct_index']} 不在 0-3 范围内"
            )

    if "content" in q and (
        not isinstance(q["content"], str) or not q["content"].strip()
    ):
        issues.append("content 为空")

    return issues


async def score_question_quality(
    question: dict,
    knowledge_context: str,
) -> dict[str, Any]:
    """Score a single question 1-5 using LLM.

    Evaluates the question against the SYSTEM_PROMPT specification in
    generator.py.  The LLM (DeepSeek, temperature=0) returns a JSON response
    with ``score`` (int 1-5) and ``reason`` (str).

    Scoring dimensions:
      5 -- Correct answer is unique and unambiguous; distractors all come from
           the document and belong to the same category as the correct answer;
           the explanation cites original text evidence.
      4 -- Mostly satisfied but with 1 minor issue (e.g., one weak distractor).
      3 -- Partially satisfied with obvious shortcomings (e.g., distractors not
           from the document).
      2 -- Multiple specification violations.
      1 -- Factual error or completely unrelated to the document.

    Args:
        question: single question dict with keys content, options,
                  correct_index, explanation.
        knowledge_context: source document passages used to generate the
                           question (retrieved chunks).

    Returns:
        dict with keys ``score`` (int 1-5) and ``reason`` (str).
    """
    options_text = ", ".join(
        f"{chr(65 + i)}. {opt}"
        for i, opt in enumerate(question.get("options", []))
    )

    prompt = (
        "你是一个题目质量评估专家。请根据以下评分标准，评估这道题的质量（1-5分）。\n\n"
        "【评分标准】\n"
        "5分：正确选项唯一无争议，干扰项全部来自文档且与正确答案属同一范畴，解析引用原文依据\n"
        "4分：基本满足，但有1处小问题（如一个干扰项稍弱）\n"
        "3分：部分满足，有明显不足（如干扰项未来自文档）\n"
        "2分：多项不满足规范\n"
        "1分：题目有事实性错误或完全脱离文档\n\n"
        "【知识上下文】\n"
        f"{knowledge_context}\n\n"
        "【题目】\n"
        f"content: {question.get('content', '')}\n"
        f"options: {options_text}\n"
        f"correct_index: {question.get('correct_index', '')} "
        f"(选项{chr(65 + question.get('correct_index', 0))})\n"
        f"explanation: {question.get('explanation', '')}\n\n"
        "请以 JSON 格式输出评分结果，不要包含其他内容：\n"
        '{"score": <整数1-5>, "reason": "<评分理由>"}'
    )

    logger.info("Evaluating question quality: %s", question.get("content", "")[:60])

    client = AsyncOpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )

    response = await client.chat.completions.create(
        model=EVALUATOR_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content
    result = json.loads(text)

    logger.info("Question scored %d/5 — %s", result["score"], result.get("reason", "")[:80])
    return result
