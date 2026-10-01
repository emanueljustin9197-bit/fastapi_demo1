"""Authenticated response-list and response-detail endpoints."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from crud.response import get_response_list_by_id_questionid, get_response_detail_by_responseid
from models.user import User
from config.database import get_db
from utils.jwt import get_current_user
from crud.anomaly import (
    get_anomalous_responses,
    scan_questionnaire_responses,
    update_response_validity,
)
from crud.response import user_owns_questionnaire
from schemas.response import AnomalyScanRequest, ResponseValidityRequest
router = APIRouter(prefix="/api/response", tags=["response"])


@router.get("/list")
async def get_response_list(
        questionnaireId: int,
        page: int = Query(1, ge=1),
        pageSize: int = Query(
            10,
            ge=1,
            le=100,
        ),
        startDate: Optional[date] = None,
        endDate: Optional[date] = None,
        source: Optional[str] = None,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    response_data = await get_response_list_by_id_questionid(
        db=db,
        questionnaire_id=questionnaireId,
        user_id=user.id,
        page=page,
        page_size=pageSize,
        start_date=startDate,
        end_date=endDate,
        source=source,
    )

    if response_data is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权查看",
        )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": [
                {
                    "id": item.id,
                    "respondentName": item.respondent_name,
                    "respondentEmail": item.respondent_email,
                    "source": item.source,
                    "durationSeconds": item.duration_seconds,
                    "isValid": item.is_valid,
                    "submittedAt": item.submitted_at,
                }
                for item in response_data["list"]
            ],
            "total": response_data["total"],
            "hasMore": response_data["hasMore"],
        },
    }


@router.get("/detail")
async def get_response_detail(
        id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    response = await get_response_detail_by_responseid(
        db=db,
        response_id=id,
        user_id=user.id,
    )

    if response is None:
        raise HTTPException(
            status_code=404,
            detail="答卷不存在或无权查看",
        )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": response.id,
            "questionnaireId": response.questionnaire_id,
            "respondentName": response.respondent_name,
            "respondentEmail": response.respondent_email,
            "source": response.source,
            "durationSeconds": response.duration_seconds,
            "isValid": response.is_valid,
            "submittedAt": response.submitted_at,
            "answers": [
                {
                    "questionId": answer.question_id,
                    "questionTitle": (
                        answer.question.title
                        if answer.question
                        else None
                    ),
                    "optionIds": [
                        item.option_id
                        for item in answer.selected_options
                    ],
                    "optionLabels": [
                        item.option.label
                        for item in answer.selected_options
                        if item.option
                    ],
                    "content": answer.content,
                }
                for answer in response.answers
            ],
        },
    }


@router.get("/anomalies")
async def anomalies(
    questionnaireId: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not await user_owns_questionnaire(db, questionnaireId, user.id):
        raise HTTPException(status_code=404, detail="问卷不存在或无权查看")

    data = await get_anomalous_responses(db, questionnaireId, user.id)
    return {"code": 200, "message": "success", "data": data}


@router.post("/anomalies/scan")
async def scan_anomalies(
    payload: AnomalyScanRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await scan_questionnaire_responses(
        db, payload.questionnaireId, user.id
    )
    if data is None:
        raise HTTPException(status_code=404, detail="问卷不存在或无权查看")
    await db.commit()
    return {"code": 200, "message": "检测完成", "data": data}


@router.put("/validity")
async def change_validity(
    payload: ResponseValidityRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response = await update_response_validity(
        db, payload.responseId, payload.isValid, user.id
    )
    if response is None:
        raise HTTPException(status_code=404, detail="答卷不存在或无权操作")
    await db.commit()
    return {"code": 200, "message": "更新成功", "data": {
        "responseId": response.id,
        "isValid": response.is_valid,
        "reviewStatus": response.review_status,
    }}