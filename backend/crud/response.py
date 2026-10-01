"""Response submission, ownership checks and answer retrieval."""

from __future__ import annotations

from datetime import datetime, timedelta, time, date
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.answers import AnswerOption,Answer
from models.questionnaire import Questionnaire
from models.response import Response


async def user_owns_questionnaire(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
):
    query=select(Questionnaire).where(Questionnaire.user_id == user_id, Questionnaire.id == questionnaire_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()



async def get_response_list_by_id_questionid(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    source: Optional[str] = None,
):
    # 确认当前用户拥有这个问卷
    if not await user_owns_questionnaire(
        db,
        questionnaire_id,
        user_id,
    ):
        return None

    conditions = [
        Response.questionnaire_id == questionnaire_id
    ]

    if start_date:
        start_time = datetime.combine(
            start_date,
            time.min,
        )

        conditions.append(
            Response.submitted_at >= start_time
        )

    if end_date:
        end_time = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
        )

        conditions.append(
            Response.submitted_at < end_time
        )

    if source:
        conditions.append(
            Response.source == source
        )

    # 查询总数
    count_stmt = select(
        func.count(Response.id)
    ).where(*conditions)

    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    # 分页查询
    offset = (page - 1) * page_size

    stmt = (
        select(Response)
        .where(*conditions)
        .order_by(
            Response.submitted_at.desc()
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



async def get_response_detail_by_responseid(
    db: AsyncSession,
    response_id: int,
    user_id: int,
):
    result = await db.execute(
        select(Response)
        .join(Response.questionnaire)
        .options(
            selectinload(Response.questionnaire),
            selectinload(Response.answers)
            .selectinload(Answer.question),
            selectinload(Response.answers)
            .selectinload(Answer.selected_options)
            .selectinload(AnswerOption.option),
        )
        .where(
            Response.id == response_id,
            Questionnaire.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()