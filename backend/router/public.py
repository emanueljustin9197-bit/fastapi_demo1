"""Unauthenticated questionnaire viewing and submission endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from crud.feedback import create_feedback
from crud.public import submit_response, get_questionnaire_by_publiccode
from schemas.feedback import FeedbackCreateRequest
from schemas.response import SubmitResponseRequest
from config.database import get_db
from datetime import datetime, timedelta
import secrets
from sqlalchemy import select

from models.response_session import ResponseSession
from schemas.response import StartResponseRequest, ActivityRequest
router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/questionnaire")
async def get_public_questionnaire(
        publicCode: str,
        db: AsyncSession = Depends(get_db),
):
    questionnaire = await get_questionnaire_by_publiccode(
        db=db,
        public_code=publicCode,
    )

    if questionnaire is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或已停止收集",
        )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": questionnaire.id,
            "title": questionnaire.title,
            "description": questionnaire.description,
            "anonymous": questionnaire.anonymous,
            "backgroundImage": questionnaire.background_image,
            "questions": [
                {
                    "id": question.id,
                    "type": (
                        question.type.value
                        if hasattr(question.type, "value")
                        else question.type
                    ),
                    "title": question.title,
                    "required": question.required,
                    "sortOrder": question.sort_order,
                    "options": [
                        {
                            "id": option.id,
                            "label": option.label,
                            "sortOrder": option.sort_order,
                        }
                        for option in question.options
                    ],
                }
                for question in questionnaire.questions
            ],
        },
    }


@router.post("/response/submit")
async def submit(
        payload: SubmitResponseRequest,
        request: Request,
        db: AsyncSession = Depends(get_db),
):
    response, questionnaire = await submit_response(
        db=db,
        payload=payload,
        submitted_ip=(
            request.client.host
            if request.client
            else None
        ),
        user_agent=request.headers.get("user-agent"),
    )

    await db.commit()
    await db.refresh(response)

    return {
        "code": 200,
        "message": "提交成功",
        "data": {
            "responseId": response.id,
            "submittedAt": response.submitted_at,
            "showResult": questionnaire.show_result,
        },
    }


# 完成概率
@router.post("/response/start")
async def start_response(payload: StartResponseRequest, db: AsyncSession = Depends(get_db)):
    questionnaire = await get_questionnaire_by_publiccode(db, payload.publicCode)
    if questionnaire is None:
        raise HTTPException(status_code=404, detail="问卷不存在或已停止收集")

    now = datetime.utcnow()

    session = ResponseSession(
        questionnaire_id=questionnaire.id,
        session_token=secrets.token_urlsafe(32),
        status="in_progress",
        started_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(
            minutes=questionnaire.response_timeout_minutes
        ),
    )
    db.add(session)
    await db.commit()
    return {"code": 200, "message": "success",
            "data": {"sessionToken": session.session_token}}

# 时间限制
@router.post("/response/activity")
async def update_activity(payload: ActivityRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResponseSession).where(
            ResponseSession.session_token == payload.sessionToken,
            ResponseSession.status == "in_progress",
        )
    )
    session = result.scalar_one_or_none()
    if session:
        session.last_activity_at = datetime.utcnow()
        await db.commit()
    return {"code": 200, "message": "success", "data": None}



@router.post("/feedback")
async def submit_feedback(
    payload: FeedbackCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    feedback = await create_feedback(db, payload)
    await db.commit()
    return {"code": 200, "message": "反馈提交成功", "data": {"id": feedback.id}}
