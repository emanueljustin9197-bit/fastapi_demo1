"""Questionnaire database operations and validation rules."""

from __future__ import annotations

import secrets
import os
import shutil
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.questionnaire import Questionnaire,Question,QuestionOption
from models.response import Response
from models.user import User
from schemas.questionnaire import QuestionnaireInput
from models.questionnaire import QuestionnaireStatus


from sqlalchemy import select, func, case

from schemas.questionnaire import QuestionnaireUpdateRequest

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

BACKGROUND_UPLOAD_DIR = (
    Path(__file__).resolve().parent.parent / "uploads" / "backgrounds"
)
MAX_BACKGROUND_SIZE = 5 * 1024 * 1024
BACKGROUND_FORMAT_SUFFIXES = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}


def _background_file_path(background_image: Optional[str]) -> Optional[Path]:
    if not background_image:
        return None
    filename = Path(urlparse(background_image).path).name
    return BACKGROUND_UPLOAD_DIR / filename if filename else None


def _delete_background_file(background_image: Optional[str]) -> None:
    file_path = _background_file_path(background_image)
    if file_path and file_path.is_file():
        file_path.unlink()


async def update_questionnaire_background(
    questionnaire_id: int,
    user: User,
    file: UploadFile,
    db: AsyncSession,
):
    questionnaire = (await db.execute(
        select(Questionnaire).where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user.id,
        )
    )).scalar_one_or_none()

    if questionnaire is None:
        raise HTTPException(status_code=404, detail="问卷不存在或无权操作")

    if not file.content_type or file.content_type not in {
        "image/jpeg",
        "image/png",
        "image/webp",
    }:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG 或 WEBP 图片")

    content = await file.read(MAX_BACKGROUND_SIZE + 1)
    if not content:
        raise HTTPException(status_code=400, detail="背景图片不能为空")
    if len(content) > MAX_BACKGROUND_SIZE:
        raise HTTPException(status_code=400, detail="背景图片不能超过 5MB")

    try:
        with Image.open(BytesIO(content)) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise HTTPException(status_code=400, detail="图片内容无效或已经损坏") from error

    suffix = BACKGROUND_FORMAT_SUFFIXES.get(image_format or "")
    if not suffix:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG 或 WEBP 图片")

    BACKGROUND_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{questionnaire.id}_{uuid.uuid4().hex}{suffix}"
    file_path = BACKGROUND_UPLOAD_DIR / filename
    old_background = questionnaire.background_image

    file_path.write_bytes(content)
    questionnaire.background_image = f"/uploads/backgrounds/{filename}"

    try:
        await db.commit()
        await db.refresh(questionnaire)
    except Exception:
        if file_path.is_file():
            file_path.unlink()
        raise

    if old_background != questionnaire.background_image:
        _delete_background_file(old_background)

    return questionnaire


async def remove_questionnaire_background(
    questionnaire_id: int,
    user: User,
    db: AsyncSession,
):
    questionnaire = (await db.execute(
        select(Questionnaire).where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user.id,
        )
    )).scalar_one_or_none()

    if questionnaire is None:
        raise HTTPException(status_code=404, detail="问卷不存在或无权操作")

    old_background = questionnaire.background_image
    questionnaire.background_image = None
    await db.commit()
    await db.refresh(questionnaire)
    _delete_background_file(old_background)
    return questionnaire


async def get_questionnaire_statistics(user: User, db: AsyncSession) -> dict:
    stmt = select(
        # 1. 问卷总数
        func.count(func.distinct(Questionnaire.id)).label("questionnaire_count"),
        # 2. 活跃问卷数
        func.count(func.distinct(case(
            (Questionnaire.status == "active", Questionnaire.id),
            else_=None
        ))).label("active_count"),
        # 3. 总答卷数
        func.count(Response.id).label("response_count"),
        # 4. 有效答卷数
        func.count(case(
            (Response.is_valid == True, Response.id),  # noqa: E712
            else_=None
        )).label("valid_count"),
    ).outerjoin(
        Response, Response.questionnaire_id == Questionnaire.id
    ).where(
        Questionnaire.user_id == user.id
    )

    row = (await db.execute(stmt)).one()

    total = row.response_count or 0
    valid = row.valid_count or 0
    rate = round(valid / total * 100, 1) if total > 0 else 0.0

    return {
        "questionnaireCount": row.questionnaire_count,
        "responseCount": row.response_count,
        "activeCount": row.active_count,
        "averageCompletionRate": rate,
    }



async def get_questionnaire_list(
    db: AsyncSession,
    user_id: int,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    conditions = [
        Questionnaire.user_id == user_id
    ]

    if keyword:
        conditions.append(
            Questionnaire.title.like(f"%{keyword}%")
        )

    if status:
        conditions.append(
            Questionnaire.status == status
        )

    # 查询总数量
    count_stmt = select(
        func.count(Questionnaire.id)
    ).where(*conditions)

    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # 计算跳过的数据条数
    offset = (page - 1) * page_size

    # 查询当前页数据
    stmt = (
        select(Questionnaire)
        .options(
            selectinload(Questionnaire.questions),
            selectinload(Questionnaire.responses),
        )
        .where(*conditions)
        .order_by(
            Questionnaire.created_at.desc()
        )
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    items = result.scalars().all()

    return {
        "list": items,
        "total": total,
        "hasMore": offset + len(items) < total,
    }


async def create_questionnaire(
    payload: QuestionnaireInput,
    user: User,
    db: AsyncSession,
):
    # 创建问卷主体
    questionnaire = Questionnaire(
        user_id=user.id,
        title=payload.title.strip(),
        description=(
            payload.description.strip()
            if payload.description
            else None
        ),
        anonymous=payload.anonymous,
        response_timeout_minutes=payload.responseTimeoutMinutes,
        one_response=payload.oneResponse,
        show_result=payload.showResult,
    )

    db.add(questionnaire)
    await db.flush()

    # 创建题目
    for question_data in sorted(
        payload.questions,
        key=lambda item: item.sortOrder,
    ):
        question = Question(
            questionnaire_id=questionnaire.id,
            type=question_data.type,
            title=question_data.title.strip(),
            required=question_data.required,
            sort_order=question_data.sortOrder,
        )

        db.add(question)
        await db.flush()

        # 创建题目选项
        for option_data in sorted(
            question_data.options,
            key=lambda item: item.sortOrder,
        ):
            option = QuestionOption(
                question_id=question.id,
                label=option_data.label.strip(),
                sort_order=option_data.sortOrder,
            )

            db.add(option)

    await db.commit()
    await db.refresh(questionnaire)

    return questionnaire


async def get_questionnaire_detail_by_id(
    id: int,
    user: User,
    db: AsyncSession,
):
    stmt = (
        select(Questionnaire)
        .options(
            selectinload(
                Questionnaire.questions
            ).selectinload(
                Question.options
            )
        )
        .where(
            Questionnaire.id == id,
            Questionnaire.user_id == user.id,
        )
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()



async def update_questionnaire_by_id(
    payload: QuestionnaireUpdateRequest,
    user: User,
    db: AsyncSession,
):
    # 查询当前用户自己的问卷，并加载题目和选项
    stmt = (
        select(Questionnaire)
        .options(
            selectinload(
                Questionnaire.questions
            ).selectinload(
                Question.options
            )
        )
        .where(
            Questionnaire.id == payload.id,
            Questionnaire.user_id == user.id,
        )
    )

    result = await db.execute(stmt)
    questionnaire = result.scalar_one_or_none()

    if questionnaire is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权修改",
        )

    # 已经发布的问卷不允许直接修改
    questionnaire_status = getattr(
        questionnaire.status,
        "value",
        questionnaire.status,
    )

    if questionnaire_status == "active":
        raise HTTPException(
            status_code=400,
            detail="收集中的问卷不能直接修改，请先停止收集",
        )

    # 更新问卷主体
    questionnaire.title = payload.title.strip()

    questionnaire.description = (
        payload.description.strip()
        if payload.description
        else None
    )

    questionnaire.anonymous = payload.anonymous
    questionnaire.one_response = payload.oneResponse
    questionnaire.show_result = payload.showResult
    questionnaire.response_timeout_minutes = payload.responseTimeoutMinutes
    # 删除原来的题目
    for old_question in list(questionnaire.questions):
        await db.delete(old_question)

    await db.flush()

    # 根据前端传来的内容重新创建题目
    for question_data in sorted(
        payload.questions,
        key=lambda item: item.sortOrder,
    ):
        question = Question(
            questionnaire_id=questionnaire.id,
            type=question_data.type,
            title=question_data.title.strip(),
            required=question_data.required,
            sort_order=question_data.sortOrder,
        )

        db.add(question)
        await db.flush()

        # 创建题目的选项
        for option_data in sorted(
            question_data.options,
            key=lambda item: item.sortOrder,
        ):
            option = QuestionOption(
                question_id=question.id,
                label=option_data.label.strip(),
                sort_order=option_data.sortOrder,
            )

            db.add(option)

    await db.commit()
    await db.refresh(questionnaire)

    return questionnaire
# 删除表格

async def delete_questionnaire_by_id(
    id:int,
    user: User,
    db: AsyncSession,
):
    background_row = (await db.execute(
        select(Questionnaire.background_image).where(
            Questionnaire.user_id == user.id,
            Questionnaire.id == id,
        )
    )).one_or_none()
    if background_row is None:
        return None

    stmt = delete(Questionnaire).where(
        Questionnaire.user_id == user.id,
        Questionnaire.id == id,
    )
    result = await db.execute(stmt)
    await db.commit()
    _delete_background_file(background_row.background_image)
    return True


# 复制表格
async def copy_questionnaire(
    questionnaire_id: int,
    user: User,
    db: AsyncSession,
):
    # 查询原问卷，同时加载题目和选项
    stmt = (
        select(Questionnaire)
        .options(
            selectinload(
                Questionnaire.questions
            ).selectinload(
                Question.options
            )
        )
        .where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user.id,
        )
    )

    result = await db.execute(stmt)
    original = result.scalar_one_or_none()

    if original is None:
        raise HTTPException(
            status_code=404,
            detail="原问卷不存在或无权复制",
        )

    # 创建新的问卷
    title = f"{original.title} - 副本"

    new_questionnaire = Questionnaire(
        user_id=user.id,
        title=title[:200],
        description=original.description,
        status=QuestionnaireStatus.DRAFT,
        anonymous=original.anonymous,
        one_response=original.one_response,
        show_result=original.show_result,
        response_timeout_minutes=original.response_timeout_minutes,

        # 复制后不能继续使用原问卷的公开信息
        public_code=None,
        public_url=None,
        published_at=None,
        closed_at=None,
    )

    db.add(new_questionnaire)
    await db.flush()

    original_background_path = _background_file_path(original.background_image)
    if original_background_path and original_background_path.is_file():
        BACKGROUND_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        copied_filename = (
            f"{new_questionnaire.id}_{uuid.uuid4().hex}"
            f"{original_background_path.suffix.lower()}"
        )
        shutil.copy2(
            original_background_path,
            BACKGROUND_UPLOAD_DIR / copied_filename,
        )
        new_questionnaire.background_image = (
            f"/uploads/backgrounds/{copied_filename}"
        )

    # 复制题目
    for old_question in sorted(
        original.questions,
        key=lambda item: item.sort_order,
    ):
        new_question = Question(
            questionnaire_id=new_questionnaire.id,
            type=old_question.type,
            title=old_question.title,
            required=old_question.required,
            sort_order=old_question.sort_order,
        )

        db.add(new_question)
        await db.flush()

        # 复制选项
        for old_option in sorted(
            old_question.options,
            key=lambda item: item.sort_order,
        ):
            new_option = QuestionOption(
                question_id=new_question.id,
                label=old_option.label,
                sort_order=old_option.sort_order,
            )

            db.add(new_option)

    await db.commit()
    await db.refresh(new_questionnaire)

    return new_questionnaire

# 发布表格
async def publish_questionnaire(
    questionnaire_id: int,
    user: User,
    db: AsyncSession,
):
    # 查询当前用户自己的问卷
    stmt = (
        select(Questionnaire)
        .where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user.id,
        )
    )

    result = await db.execute(stmt)
    questionnaire = result.scalar_one_or_none()

    if questionnaire is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权发布",
        )

    status = getattr(
        questionnaire.status,
        "value",
        questionnaire.status,
    )

    if status == "active":
        raise HTTPException(
            status_code=400,
            detail="问卷已经发布",
        )

    if status == "closed":
        raise HTTPException(
            status_code=400,
            detail="已经关闭的问卷不能重新发布",
        )

    # 检查问卷是否有题目
    question_count_stmt = select(
        func.count(Question.id)
    ).where(
        Question.questionnaire_id == questionnaire.id
    )

    question_count_result = await db.execute(
        question_count_stmt
    )

    question_count = question_count_result.scalar_one()

    if question_count == 0:
        raise HTTPException(
            status_code=400,
            detail="问卷至少需要包含一道题目",
        )

    # 生成唯一公开编号
    while True:
        public_code = f"sv_{secrets.token_hex(4)}"

        check_stmt = select(
            Questionnaire.id
        ).where(
            Questionnaire.public_code == public_code
        )

        check_result = await db.execute(check_stmt)

        if check_result.scalar_one_or_none() is None:
            break

    frontend_base_url = os.getenv(
        "FRONTEND_BASE_URL",
        "http://localhost:5173",
    ).rstrip("/")

    questionnaire.status = QuestionnaireStatus.ACTIVE
    questionnaire.public_code = public_code
    questionnaire.public_url = (
        f"{frontend_base_url}/s/{public_code}"
    )
    questionnaire.published_at = datetime.utcnow()
    questionnaire.closed_at = None

    await db.commit()
    await db.refresh(questionnaire)

    return questionnaire
# 停止收集表格


async def close_questionnaire(
    questionnaire_id: int,
    user: User,
    db: AsyncSession,
):
    # 查询当前用户自己的问卷
    stmt = (
        select(Questionnaire)
        .where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user.id,
        )
    )

    result = await db.execute(stmt)
    questionnaire = result.scalar_one_or_none()

    if questionnaire is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权操作",
        )

    status = getattr(
        questionnaire.status,
        "value",
        questionnaire.status,
    )

    if status == "draft":
        raise HTTPException(
            status_code=400,
            detail="问卷尚未发布，不能停止收集",
        )

    if status == "closed":
        raise HTTPException(
            status_code=400,
            detail="问卷已经停止收集",
        )

    # 停止收集
    questionnaire.status = QuestionnaireStatus.CLOSED
    questionnaire.closed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(questionnaire)

    return questionnaire
