"""Calculations used by the questionnaire analysis endpoints."""
from models.answers import Answer
from models.questionnaire import Questionnaire, Question
from models.response import Response

"""Calculations used by the questionnaire analysis endpoints."""


from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.response_session import ResponseSession



async def get_overview_by_questionnaireid(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
):
    # 先确认问卷属于当前用户
    questionnaire_stmt = select(Questionnaire.id).where(
        Questionnaire.id == questionnaire_id,
        Questionnaire.user_id == user_id,
    )

    questionnaire_result = await db.execute(questionnaire_stmt)

    if questionnaire_result.scalar_one_or_none() is None:
        return None

    # 查询答卷
    stmt = (
        select(Response)
        .where(Response.questionnaire_id == questionnaire_id)
        .order_by(Response.submitted_at.asc())
    )

    result = await db.execute(stmt)
    responses = result.scalars().all()

    response_count = len(responses)

    valid_responses = [
        response
        for response in responses
        if response.is_valid
    ]

    valid_response_count = len(valid_responses)

    if response_count > 0:
        valid_rate = round(
            valid_response_count / response_count * 100,
            1,
        )
    else:
        valid_rate = 0.0

    if valid_responses:
        average_duration_seconds = round(
            sum(
                response.duration_seconds or 0
                for response in valid_responses
            ) / len(valid_responses),
            1,
        )
    else:
        average_duration_seconds = 0.0


    # 完成概率计算

    session_result = await db.execute(
        select(ResponseSession).where(
            ResponseSession.questionnaire_id == questionnaire_id
        )
    )
    sessions = session_result.scalars().all()
    now = datetime.utcnow()

    for item in sessions:
        if (
                item.status == "in_progress"
                and item.expires_at
                and item.expires_at <= now
        ):
            item.status = "expired"

    completed_count = sum(item.status == "completed" for item in sessions)
    expired_count = sum(item.status == "expired" for item in sessions)
    finished_count = completed_count + expired_count

    completion_rate = (
        round(completed_count / finished_count * 100, 1)
        if finished_count
        else 0.0
    )

    abandoned_count = expired_count

    # 计算最近 7 天答卷增长率
    now = datetime.utcnow()
    today = now.date()

    current_start = datetime.combine(
        today - timedelta(days=6),
        datetime.min.time(),
    )

    current_end = datetime.combine(
        today + timedelta(days=1),
        datetime.min.time(),
    )

    previous_start = current_start - timedelta(days=7)
    previous_end = current_start

    current_count = 0
    previous_count = 0

    for response in responses:
        if (
            current_start
            <= response.submitted_at
            < current_end
        ):
            current_count += 1

        elif (
            previous_start
            <= response.submitted_at
            < previous_end
        ):
            previous_count += 1

    if previous_count == 0:
        if current_count > 0:
            response_growth_rate = 100.0
        else:
            response_growth_rate = 0.0
    else:
        response_growth_rate = round(
            (current_count - previous_count)
            / previous_count
            * 100,
            1,
        )

    return {
        "responseCount": response_count,
        "validResponseCount": valid_response_count,
        "validRate": valid_rate,
        "averageDurationSeconds": average_duration_seconds,
        "completionRate": completion_rate,
        "abandonedCount": abandoned_count,
        "responseGrowthRate": response_growth_rate,
    }


async def get_response_trend_by_days(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
    days: int = 7,
):
    # 确认问卷权限
    questionnaire_stmt = select(Questionnaire.id).where(
        Questionnaire.id == questionnaire_id,
        Questionnaire.user_id == user_id,
    )

    questionnaire_result = await db.execute(questionnaire_stmt)

    if questionnaire_result.scalar_one_or_none() is None:
        return None

    now = datetime.utcnow()
    today = now.date()

    start_date = today - timedelta(days=days - 1)

    start_datetime = datetime.combine(
        start_date,
        datetime.min.time(),
    )

    end_datetime = datetime.combine(
        today + timedelta(days=1),
        datetime.min.time(),
    )

    stmt = (
        select(Response.submitted_at)
        .where(
            Response.questionnaire_id == questionnaire_id,
            Response.submitted_at >= start_datetime,
            Response.submitted_at < end_datetime,
        )
    )

    result = await db.execute(stmt)
    submitted_dates = result.scalars().all()

    date_counter = Counter(
        submitted_at.date()
        for submitted_at in submitted_dates
    )

    trend = []

    for index in range(days):
        current_date = start_date + timedelta(days=index)

        trend.append(
            {
                "date": current_date.isoformat(),
                "count": date_counter.get(current_date, 0),
            }
        )

    return trend


async def get_channels_by_id(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
):
    # 确认问卷权限
    questionnaire_stmt = select(Questionnaire.id).where(
        Questionnaire.id == questionnaire_id,
        Questionnaire.user_id == user_id,
    )

    questionnaire_result = await db.execute(questionnaire_stmt)

    if questionnaire_result.scalar_one_or_none() is None:
        return None

    stmt = select(Response.source).where(
        Response.questionnaire_id == questionnaire_id
    )

    result = await db.execute(stmt)
    sources = result.scalars().all()

    source_counter = Counter(sources)
    total_count = len(sources)

    source_labels = {
        "publicLink": "公开链接",
        "qrCode": "二维码",
        "wechat": "微信转发",
    }

    channels = []

    for source, label in source_labels.items():
        count = source_counter.get(source, 0)
        if total_count > 0:
            percentage = round(
                count / total_count * 100,
                1,
            )
        else:
            percentage = 0.0

        channels.append(
            {
                "source": source,
                "label": label,
                "count": count,
                "percentage": percentage,
            }
        )

    return channels


async def get_total_result_by_id(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
):
    # 查询问卷、题目、选项、答案
    stmt = (
        select(Questionnaire)
        .options(
            selectinload(
                Questionnaire.questions
            ).selectinload(
                Question.options
            ),
            selectinload(
                Questionnaire.questions
            ).selectinload(
                Question.answers
            ).selectinload(
                Answer.selected_options
            ),
            selectinload(
                Questionnaire.responses
            ),
        )
        .where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user_id,
        )
    )

    result = await db.execute(stmt)
    questionnaire = result.scalar_one_or_none()

    if questionnaire is None:
        return None

    total_response_count = len(
        questionnaire.responses
    )

    question_result = []

    for question in questionnaire.questions:
        # 统计回答过这道题的答卷数量
        answer_response_ids = {
            answer.response_id
            for answer in question.answers
        }

        answer_count = len(answer_response_ids)

        skip_count = max(
            total_response_count - answer_count,
            0,
        )

        option_counter = Counter()

        for answer in question.answers:
            for selected_option in answer.selected_options:
                option_counter[
                    selected_option.option_id
                ] += 1

        question_type = getattr(
            question.type,
            "value",
            question.type,
        )

        options = []

        for option in question.options:
            count = option_counter.get(
                option.id,
                0,
            )

            if total_response_count > 0:
                percentage = round(
                    count / total_response_count * 100,
                    1,
                )
            else:
                percentage = 0.0

            options.append(
                {
                    "optionId": option.id,
                    "label": option.label,
                    "count": count,
                    "percentage": percentage,
                }
            )

        question_result.append(
            {
                "questionId": question.id,
                "type": question_type,
                "title": question.title,
                "answerCount": answer_count,
                "skipCount": skip_count,
                "options": options,
                "keywords": [],
            }
        )

    return question_result
