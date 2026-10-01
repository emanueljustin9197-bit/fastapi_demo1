"""Questionnaire-analysis HTTP endpoints."""

from fastapi import APIRouter


"""Questionnaire-analysis HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from crud import analysis as analysis_crud
from models.user import User

from config.database import get_db
from utils.jwt import get_current_user

router = APIRouter(prefix="/api/analysis", tags=["analysis"])




router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"],
)


@router.get("/overview")
async def get_overview_by_questionnaireid(
    questionnaireId: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await analysis_crud.get_overview_by_questionnaireid(
        db=db,
        questionnaire_id=questionnaireId,
        user_id=user.id,
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权查看",
        )

    return {
        "code": 200,
        "message": "success",
        "data": data,
    }


@router.get("/trend")
async def get_response_trend_by_days(
    questionnaireId: int = Query(..., ge=1),
    days: int = Query(7, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await analysis_crud.get_response_trend_by_days(
        db=db,
        questionnaire_id=questionnaireId,
        user_id=user.id,
        days=days,
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权查看",
        )

    return {
        "code": 200,
        "message": "success",
        "data": data,
    }


@router.get("/channels")
async def get_channels_by_id(
    questionnaireId: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await analysis_crud.get_channels_by_id(
        db=db,
        questionnaire_id=questionnaireId,
        user_id=user.id,
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权查看",
        )

    return {
        "code": 200,
        "message": "success",
        "data": data,
    }


@router.get("/questions")
async def get_total_result_by_id(
    questionnaireId: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await analysis_crud.get_total_result_by_id(
        db=db,
        questionnaire_id=questionnaireId,
        user_id=user.id,
    )

    if data is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权查看",
        )

    return {
        "code": 200,
        "message": "success",
        "data": data,
    }

