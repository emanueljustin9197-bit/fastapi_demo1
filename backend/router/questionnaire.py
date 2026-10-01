"""Questionnaire management HTTP endpoints."""


from typing import Optional

import os

from io import BytesIO

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse

from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession


from crud.questionnaire import get_questionnaire_statistics, get_questionnaire_list, create_questionnaire, \
    get_questionnaire_detail_by_id, update_questionnaire_by_id, copy_questionnaire, publish_questionnaire, \
    close_questionnaire, delete_questionnaire_by_id, update_questionnaire_background, \
    remove_questionnaire_background

from models.user import User
from models.questionnaire import Questionnaire, QuestionnaireStatus
from schemas.questionnaire import QuestionnaireInput
from config.database import get_db
from schemas.questionnaire import IdRequest, QuestionnaireUpdateRequest

from utils.jwt import get_current_user

router = APIRouter(prefix="/api/questionnaire", tags=["questionnaire"])


def build_public_url(public_code: Optional[str]) -> Optional[str]:
    if not public_code:
        return None
    frontend_base_url = os.getenv(
        "FRONTEND_BASE_URL",
        "http://localhost:5173",
    ).rstrip("/")
    return f"{frontend_base_url}/s/{public_code}"


@router.get("/statistics")
async def questionnaire_statistics(
        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    data = await get_questionnaire_statistics(user, db)
    return {
        "code": 200,
        "message": "success",
        "data": {
            "questionnaireCount": data["questionnaireCount"],
            "responseCount": data["responseCount"],
            "activeCount": data["activeCount"],
            "averageCompletionRate": data["averageCompletionRate"],
        }
    }


# 获取我的问卷列表
@router.get("/list")
async def questionnaire_list(
        keyword: Optional[str] = Query(
            None,
            alias="keyword"
        ),
        status: Optional[str] = Query(
            None,
            alias="status"
        ),
        page: int = Query(
            1,
            alias="page",
            ge=1
        ),
        page_size: int = Query(
            10,
            alias="pageSize",
            ge=1,
            le=100
        ),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    questionnaire_data = await get_questionnaire_list(
        db=db,
        user_id=user.id,
        keyword=keyword,
        status=status,
        page=page,
        page_size=page_size,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": [
                {
                    "id": questionnaire.id,
                    "title": questionnaire.title,
                    "description": questionnaire.description,
                    "status": (
                        questionnaire.status.value
                        if hasattr(questionnaire.status, "value")
                        else questionnaire.status
                    ),
                    "anonymous": questionnaire.anonymous,
                    "oneResponse": questionnaire.one_response,
                    "showResult": questionnaire.show_result,
                    "publicCode": questionnaire.public_code,
                    "publicUrl": build_public_url(questionnaire.public_code),
                    "backgroundImage": questionnaire.background_image,
                    "questionCount": len(questionnaire.questions),
                    "responseCount": len(questionnaire.responses),
                    "completionRate": (
                        round(
                            sum(
                                1
                                for response in questionnaire.responses
                                if response.is_valid
                            )
                            / len(questionnaire.responses)
                            * 100,
                            1,
                        )
                        if questionnaire.responses
                        else 0.0
                    ),
                    "createdAt": questionnaire.created_at,
                    "updatedAt": questionnaire.updated_at,
                }
                for questionnaire in questionnaire_data["list"]
            ],
            "total": questionnaire_data["total"],
            "hasMore": questionnaire_data["hasMore"],
        }
    }


@router.post("/create")
async def create(
        payload: QuestionnaireInput,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    questionnaire = await create_questionnaire(
        payload=payload,
        user=user,
        db=db,
    )

    status = questionnaire.status

    if hasattr(status, "value"):
        status = status.value

    return {
        "code": 200,
        "message": "创建成功",
        "data": {
            "id": questionnaire.id,
            "title": questionnaire.title,
            "status": status,
            "createdAt": questionnaire.created_at,
        },
    }


@router.get("/detail")
async def detail(
        id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    questionnaire = await get_questionnaire_detail_by_id(
        id=id,
        user=user,
        db=db,
    )

    if questionnaire is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权查看",
        )

    status = questionnaire.status
    if hasattr(status, "value"):
        status = status.value

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": questionnaire.id,
            "title": questionnaire.title,
            "description": questionnaire.description,
            "status": status,
            "responseTimeoutMinutes": questionnaire.response_timeout_minutes,
            "anonymous": questionnaire.anonymous,
            "oneResponse": questionnaire.one_response,
            "showResult": questionnaire.show_result,
            "publicCode": questionnaire.public_code,
            "publicUrl": build_public_url(questionnaire.public_code),
            "backgroundImage": questionnaire.background_image,
            "publishedAt": questionnaire.published_at,
            "closedAt": questionnaire.closed_at,
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
            "createdAt": questionnaire.created_at,
            "updatedAt": questionnaire.updated_at,
        },
    }


@router.put("/update")
async def update_questionnaire(
        payload: QuestionnaireUpdateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    questionnaire = await update_questionnaire_by_id(
        payload=payload,
        user=user,
        db=db,
    )

    return {
        "code": 200,
        "message": "保存成功",
        "data": {
            "id": questionnaire.id,
            "updatedAt": questionnaire.updated_at,
        },
    }


@router.post("/background")
async def upload_background(
    id: int = Query(..., ge=1),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    questionnaire = await update_questionnaire_background(
        questionnaire_id=id,
        user=user,
        file=file,
        db=db,
    )
    return {
        "code": 200,
        "message": "背景图片已保存",
        "data": {"backgroundImage": questionnaire.background_image},
    }


@router.delete("/background")
async def delete_background(
    id: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await remove_questionnaire_background(
        questionnaire_id=id,
        user=user,
        db=db,
    )
    return {"code": 200, "message": "背景图片已移除", "data": None}


@router.delete("/delete")
async def delete_questionnaire(
    id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_questionnaire_by_id(
        id=id,
        user=user,
        db=db,
    )

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="表格不存在或无权删除",
        )

    return {
        "code": 200,
        "message": "删除成功",
        "data": None,
    }

@router.post("/copy")
async def copy(
        payload: IdRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    questionnaire = await copy_questionnaire(
        questionnaire_id=payload.id,
        user=user,
        db=db,
    )

    status = questionnaire.status

    if hasattr(status, "value"):
        status = status.value

    return {
        "code": 200,
        "message": "复制成功",
        "data": {
            "id": questionnaire.id,
            "title": questionnaire.title,
            "status": status,
        },
    }


@router.post("/publish")
async def publish(
        payload: IdRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    questionnaire = await publish_questionnaire(
        questionnaire_id=payload.id,
        user=user,
        db=db,
    )

    status = questionnaire.status

    if hasattr(status, "value"):
        status = status.value

    qr_code_url = (
        "/api/questionnaire/qrcode"
        f"?publicCode={questionnaire.public_code}"
    )

    return {
        "code": 200,
        "message": "发布成功",
        "data": {
            "id": questionnaire.id,
            "status": status,
            "publicCode": questionnaire.public_code,
            "publicUrl": build_public_url(questionnaire.public_code),
            "qrCodeUrl": qr_code_url,
            "publishedAt": questionnaire.published_at,
        },
    }


@router.get("/qrcode")
async def questionnaire_qrcode(
    publicCode: str = Query(..., min_length=1, max_length=64),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(
        Questionnaire.public_url,
        Questionnaire.public_code,
    ).where(
        Questionnaire.public_code == publicCode,
        Questionnaire.status == QuestionnaireStatus.ACTIVE,
    )
    questionnaire = (await db.execute(stmt)).one_or_none()

    if questionnaire is None:
        raise HTTPException(status_code=404, detail="公开问卷不存在或未发布")

    public_url = build_public_url(questionnaire.public_code)
    if not public_url:
        raise HTTPException(status_code=404, detail="公开问卷缺少分享编码")

    separator = "&" if "?" in public_url else "?"
    tracked_public_url = f"{public_url}{separator}source=qrCode"
    image = qrcode.make(tracked_public_url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="image/png",
        headers={
            "Content-Disposition": (
                f'inline; filename="questionnaire-{publicCode}.png"'
            ),
            "Cache-Control": "no-store, max-age=0",
        },
    )


@router.post("/close")
async def close(
        payload: IdRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    questionnaire = await close_questionnaire(
        questionnaire_id=payload.id,
        user=user,
        db=db,
    )

    status = questionnaire.status

    if hasattr(status, "value"):
        status = status.value

    return {
        "code": 200,
        "message": "问卷已停止收集",
        "data": {
            "id": questionnaire.id,
            "status": status,
        },
    }
