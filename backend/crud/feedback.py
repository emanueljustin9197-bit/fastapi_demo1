from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feedback import UserFeedback
from models.questionnaire import Questionnaire
from models.response import Response
from schemas.feedback import FeedbackCreateRequest


async def create_feedback(db: AsyncSession, payload: FeedbackCreateRequest):
    questionnaire = (await db.execute(
        select(Questionnaire).where(
            Questionnaire.id == payload.questionnaireId,
            Questionnaire.public_code == payload.publicCode,
        )
    )).scalar_one_or_none()

    response = (await db.execute(
        select(Response).where(
            Response.id == payload.responseId,
            Response.questionnaire_id == payload.questionnaireId,
        )
    )).scalar_one_or_none()

    if questionnaire is None or response is None:
        raise HTTPException(status_code=404, detail="问卷或答卷不存在")

    existing = (await db.execute(
        select(UserFeedback).where(
            UserFeedback.response_id == payload.responseId
        )
    )).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="该答卷已经提交过反馈")

    item = UserFeedback(
        questionnaire_id=payload.questionnaireId,
        response_id=payload.responseId,
        rating=payload.rating,
        issue_type=payload.issueType,
        content=payload.content.strip() if payload.content else None,
    )
    db.add(item)
    await db.flush()
    return item


async def get_feedback_list(db: AsyncSession, questionnaire_id: int, user_id: int):
    owned = (await db.execute(
        select(Questionnaire.id).where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user_id,
        )
    )).scalar_one_or_none()

    if owned is None:
        return None

    items = (await db.execute(
        select(UserFeedback)
        .where(UserFeedback.questionnaire_id == questionnaire_id)
        .order_by(UserFeedback.created_at.desc())
    )).scalars().all()

    return {
        "total": len(items),
        "averageRating": round(
            sum(item.rating for item in items) / len(items), 1
        ) if items else 0,
        "issueCount": sum(item.issue_type != "none" for item in items),
        "list": [{
            "id": item.id,
            "responseId": item.response_id,
            "rating": item.rating,
            "issueType": item.issue_type,
            "content": item.content,
            "createdAt": item.created_at,
        } for item in items],
    }