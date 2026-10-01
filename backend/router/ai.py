from crud.ai_chat import chat_with_analysis, clear_analysis_chat
from models.user import User
from schemas.ai import (
    AiAnalysisInsightRequest,
    AiDimensionsRequest,
    AiGenerateRequest,
    AiOptimizeRequest,
    AiSummarizeRequest, AiAnalysisChatRequest, AiAnalysisChatClearRequest,
)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from crud.ai import (
    generate_questionnaire_by_key as crud_generate_questionnaire_by_key,
    optimize_questions_by_key as crud_optimize_questions_by_key,
    recommend_dimensions_by_key as crud_recommend_dimensions_by_key,
    summarize_text_answers_by_ai as crud_summarize_text_answers_by_ai,
    create_analysis_insight_by_ai as crud_create_analysis_insight_by_ai,
)


from config.database import get_db
from utils.jwt import get_current_user


router = APIRouter(
    prefix="/api/ai",
    tags=["ai"],
)


@router.post("/questionnaire/generate")
async def generate_questionnaire(
    payload: AiGenerateRequest,
    user: User = Depends(get_current_user),
):
    data = await crud_generate_questionnaire_by_key(
        payload=payload,
        user_id=user.id,
    )

    return {
        "code": 200,
        "message": "生成成功",
        "data": data,
    }


@router.post("/question/optimize")
async def optimize_questions(
    payload: AiOptimizeRequest,
    user: User = Depends(get_current_user),
):
    data = await crud_optimize_questions_by_key(
        payload=payload,
    )

    return {
        "code": 200,
        "message": "优化成功",
        "data": data,
    }


@router.post("/questionnaire/dimensions")
async def recommend_dimensions(
    payload: AiDimensionsRequest,
    user: User = Depends(get_current_user),
):
    data = await crud_recommend_dimensions_by_key(
        payload=payload,
    )

    return {
        "code": 200,
        "message": "success",
        "data": data,
    }


@router.post("/response/summarize")
async def summarize_text_answers(
    payload: AiSummarizeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await crud_summarize_text_answers_by_ai(
        db=db,
        payload=payload,
        user_id=user.id,
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="问卷或题目不存在，或者无权查看",
        )

    return {
        "code": 200,
        "message": "总结成功",
        "data": data,
    }


@router.post("/analysis/insight")
async def create_analysis_insight(
    payload: AiAnalysisInsightRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await crud_create_analysis_insight_by_ai(
        db=db,
        payload=payload,
        user_id=user.id,
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权查看",
        )

    return {
        "code": 200,
        "message": "分析成功",
        "data": data,
    }


@router.post("/analysis/chat")
async def analysis_chat(
    payload: AiAnalysisChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await chat_with_analysis(db, payload, user.id)
    if data is None:
        raise HTTPException(status_code=404, detail="问卷不存在或无权查看")

    return {"code": 200, "message": "success", "data": data}


@router.post("/analysis/chat/clear")
async def clear_chat(
    payload: AiAnalysisChatClearRequest,
    user: User = Depends(get_current_user),
):
    await clear_analysis_chat(
        user.id,
        payload.questionnaireId,
        payload.conversationId,
    )
    return {"code": 200, "message": "对话已清空", "data": None}