from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException
from pydantic import ValidationError
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud import analysis as analysis_crud
from models.answers import Answer
from models.questionnaire import Questionnaire, Question
from models.response import Response
from schemas.ai import (
    AiAnalysisInsightRequest,
    AiDimensionsRequest,
    AiGenerateRequest,
    AiOptimizeRequest,
    AiSummarizeRequest, AiAnalysisInsightResponse,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

VALID_QUESTION_TYPES = {
    "single",
    "multiple",
    "text",
    "date",
    "rating",
    "number",
    "phone",
}


def get_ai_model():
    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="未配置 DEEPSEEK_API_KEY",
        )

    return ChatOpenAI(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        api_key=api_key,
        base_url=os.getenv(
            "DEEPSEEK_BASE_URL",
            "https://api.deepseek.com",
        ),
    )

def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, Iterable):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])

        return "\n".join(parts).strip()

    return str(content).strip()


def _read_json_object(content: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else content

    start = candidate.find("{")
    end = candidate.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise HTTPException(status_code=502, detail="AI 未返回有效 JSON")

    try:
        data = json.loads(candidate[start:end + 1])
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=502, detail="AI 返回的 JSON 无法解析") from error

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="AI 返回格式不正确")

    return data


async def _ask_ai(prompt: str) -> str:
    try:
        model = get_ai_model()
        response = await model.ainvoke(prompt)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="DeepSeek 调用失败，请检查 API Key、模型名和网络",
        ) from error

    content = _content_to_text(response.content)

    if not content:
        raise HTTPException(status_code=502, detail="AI 返回内容为空")

    return content


def _normalize_questions(raw_questions: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_questions, list):
        raise HTTPException(status_code=502, detail="AI 未返回 questions 数组")

    questions: list[dict[str, Any]] = []

    for raw_question in raw_questions:
        if not isinstance(raw_question, dict):
            continue

        question_type = str(raw_question.get("type", "")).strip()
        title = str(raw_question.get("title", "")).strip()

        if question_type not in VALID_QUESTION_TYPES or not title:
            continue

        options: list[dict[str, Any]] = []

        if question_type in {"single", "multiple"}:
            raw_options = raw_question.get("options", [])

            if isinstance(raw_options, list):
                for raw_option in raw_options:
                    label = (
                        str(raw_option.get("label", "")).strip()
                        if isinstance(raw_option, dict)
                        else str(raw_option).strip()
                    )

                    if label:
                        options.append(
                            {
                                "label": label,
                                "sortOrder": len(options),
                            }
                        )

            if len(options) < 2:
                continue

        questions.append(
            {
                "type": question_type,
                "title": title,
                "required": bool(raw_question.get("required", False)),
                "sortOrder": len(questions),
                "options": options,
            }
        )

    if not questions:
        raise HTTPException(status_code=502, detail="AI 没有生成可用题目")

    return questions


async def generate_questionnaire_by_key(
    payload: AiGenerateRequest,
    user_id: int,
):
    existing_titles = [
        str(item.get("title", "")).strip()
        for item in payload.existingQuestions
        if isinstance(item, dict) and str(item.get("title", "")).strip()
    ]

    prompt = f"""你是专业问卷设计师。请根据用户需求生成一份中文问卷。
用户需求：{payload.prompt.strip()}
问卷标题建议：{payload.title or "无"}
需要生成题目数：{payload.questionCount}
已有题目，不能重复：{json.dumps(existing_titles, ensure_ascii=False)}

只能返回 JSON，不要 Markdown，不要解释。JSON 格式必须为：
{{
  "title": "问卷标题",
  "description": "一句问卷说明",
  "questions": [
    {{"type": "single", "title": "问题", "required": true, "options": [{{"label": "选项"}}]}}
  ]
}}
type 只能是 single、multiple、text、date、rating、number、phone。
single 和 multiple 必须至少有两个 options，其他题型 options 必须是空数组。"""

    data = _read_json_object(await _ask_ai(prompt))
    questions = _normalize_questions(data.get("questions"))

    return {
        "title": str(data.get("title") or payload.title or "AI 生成问卷").strip(),
        "description": str(data.get("description") or "").strip(),
        "questions": questions[:payload.questionCount],
    }


async def optimize_questions_by_key(payload: AiOptimizeRequest):
    prompt = f"""你是专业问卷设计师。优化下列问卷题目，使表述清楚、中立、简洁。
额外要求：{payload.requirement or "无"}
题目：{json.dumps([item.model_dump() for item in payload.questions], ensure_ascii=False)}

只能返回 JSON，不要 Markdown：{{"questions": [...]}}。
每个题目必须保留 type、title、required、options。single 和 multiple 至少保留两个选项。"""

    data = _read_json_object(await _ask_ai(prompt))

    return {"questions": _normalize_questions(data.get("questions"))}


async def recommend_dimensions_by_key(payload: AiDimensionsRequest):
    prompt = f"""你是专业问卷设计师。为以下问卷推荐 3 到 6 个调研维度。
标题：{payload.title}
说明：{payload.description or "无"}
已有题目：{json.dumps([item.model_dump() for item in payload.questions], ensure_ascii=False)}

只能返回 JSON，不要 Markdown：
{{"dimensions": [{{"name": "维度名称", "description": "说明"}}]}}"""

    data = _read_json_object(await _ask_ai(prompt))
    dimensions = data.get("dimensions")

    if not isinstance(dimensions, list):
        raise HTTPException(status_code=502, detail="AI 未返回 dimensions 数组")

    return {
        "dimensions": [
            {
                "name": str(item.get("name", "")).strip(),
                "description": str(item.get("description", "")).strip(),
            }
            for item in dimensions
            if isinstance(item, dict) and str(item.get("name", "")).strip()
        ]
    }


async def summarize_text_answers_by_ai(
    db: AsyncSession,
    payload: AiSummarizeRequest,
    user_id: int,
):
    question_stmt = (
        select(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .where(
            Question.id == payload.questionId,
            Question.questionnaire_id == payload.questionnaireId,
            Questionnaire.user_id == user_id,
        )
    )
    question = (await db.execute(question_stmt)).scalar_one_or_none()

    if question is None:
        return None

    answer_stmt = (
        select(Answer.content)
        .join(Response, Response.id == Answer.response_id)
        .where(
            Answer.question_id == payload.questionId,
            Response.questionnaire_id == payload.questionnaireId,
            Answer.content.is_not(None),
        )
    )
    texts = [text.strip() for text in (await db.execute(answer_stmt)).scalars().all() if text and text.strip()]

    if not texts:
        return {"answerCount": 0, "summary": "目前还没有文本回答。", "keywords": []}

    prompt = f"""请总结以下问卷开放题回答。题目：{question.title}
回答：{json.dumps(texts[:200], ensure_ascii=False)}
只能返回 JSON，不要 Markdown：
{{"summary": "两到四句客观总结", "keywords": ["关键词1", "关键词2"]}}"""
    data = _read_json_object(await _ask_ai(prompt))
    keywords = data.get("keywords", [])

    return {
        "answerCount": len(texts),
        "summary": str(data.get("summary") or "暂未生成总结。").strip(),
        "keywords": [
            {"text": str(item).strip(), "count": None}
            for item in keywords[:8]
            if str(item).strip()
        ] if isinstance(keywords, list) else [],
    }


async def create_analysis_insight_by_ai(
    db: AsyncSession,
    payload: AiAnalysisInsightRequest,
    user_id: int,
):
    overview = await analysis_crud.get_overview_by_questionnaireid(
        db=db,
        questionnaire_id=payload.questionnaireId,
        user_id=user_id,
    )

    if overview is None:
        return None

    days = 7 if payload.range == "7d" else 30
    trend = await analysis_crud.get_response_trend_by_days(
        db=db,
        questionnaire_id=payload.questionnaireId,
        user_id=user_id,
        days=days,
    )
    questions = await analysis_crud.get_total_result_by_id(
        db=db,
        questionnaire_id=payload.questionnaireId,
        user_id=user_id,
    )

    prompt = f"""
    你是一名问卷数据分析师，只能根据下面提供的真实数据分析。

    统计时间：最近 {days} 天
    总览：{json.dumps(overview, ensure_ascii=False, default=str)}
    趋势：{json.dumps(trend, ensure_ascii=False, default=str)}
    题目统计：{json.dumps(questions, ensure_ascii=False, default=str)}

    要求：
    1. 返回 3 条关键发现和 2 条建议。
    2. 每条发现至少包含一个数据依据。
    3. 所有数字必须来自输入数据，禁止推测或编造。
    4. 只能返回 JSON，不要 Markdown。

    返回格式：
    {{
      "findings": [
        {{
          "conclusion": "结论",
          "evidence": [
            {{
              "sourceType": "question",
              "sourceId": "题目ID或指标名称",
              "text": "题目3中不满意占32.5%，共13份回答"
            }}
          ]
        }}
      ],
      "suggestions": ["建议1", "建议2"]
    }}
    """

    raw = _read_json_object(await _ask_ai(prompt))
    try:
        validated = AiAnalysisInsightResponse.model_validate(raw)
    except ValidationError as error:
        raise HTTPException(
            status_code=502,
            detail="AI 返回的分析结构不正确，请重新生成",
        ) from error
    return validated.model_dump()




