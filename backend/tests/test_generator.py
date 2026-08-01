import json
import pytest
from backend.services.generator import build_quiz_prompt, parse_quiz_response


def test_build_quiz_prompt():
    prompt = build_quiz_prompt(
        knowledge_summary="核心概念: Agent Loop",
        difficulty="medium",
        question_count=5,
    )
    assert "Agent Loop" in prompt
    assert "中等" in prompt
    assert "5" in prompt
    assert "JSON" in prompt


def test_parse_quiz_response_valid():
    response = json.dumps([
        {
            "content": "什么是 Agent Loop?",
            "options": ["A", "B", "C", "D"],
            "correct_index": 2,
            "explanation": "Agent Loop 是..."
        }
    ])
    questions = parse_quiz_response(response)
    assert len(questions) == 1
    assert questions[0]["content"] == "什么是 Agent Loop?"
    assert questions[0]["correct_index"] == 2


def test_parse_quiz_response_with_markdown_wrapper():
    response = '```json\n' + json.dumps([{
        "content": "Q1",
        "options": ["A", "B", "C", "D"],
        "correct_index": 0,
        "explanation": "因为..."
    }]) + '\n```'
    questions = parse_quiz_response(response)
    assert len(questions) == 1


def test_parse_quiz_response_invalid():
    with pytest.raises(ValueError):
        parse_quiz_response("not valid json {{{")
