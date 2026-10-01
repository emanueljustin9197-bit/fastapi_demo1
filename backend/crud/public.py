import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.answers import Answer, AnswerOption
from models.questionnaire import QuestionnaireStatus, Questionnaire, Question

from sqlalchemy import select, func, case

from models.response import Response
from schemas.response import SubmitResponseRequest
from models.response_session import ResponseSession

# 获取公开问卷
async def get_questionnaire_by_publiccode(
    db: AsyncSession,
    public_code: str,
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
            Questionnaire.public_code == public_code,
            Questionnaire.status == QuestionnaireStatus.ACTIVE,
        )
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()

# 提交问卷1
async def submit_response(
    db: AsyncSession,
    payload: SubmitResponseRequest,
    submitted_ip: Optional[str] = None,
    user_agent:  Optional[str]= None,
):
    questionnaire = await get_questionnaire_by_publiccode(
        db,
        payload.publicCode,
    )

    if questionnaire is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或已停止收集",
        )
    if not payload.sessionToken:
        raise HTTPException(status_code=400, detail="填写会话不存在，请刷新页面")

    session_result = await db.execute(
        select(ResponseSession).where(
            ResponseSession.session_token == payload.sessionToken,
            ResponseSession.questionnaire_id == questionnaire.id,
        )
    )
    session = session_result.scalar_one_or_none()

    if session is None:
        raise HTTPException(status_code=400, detail="填写会话无效")

    if session.status == "completed":
        raise HTTPException(status_code=400, detail="该问卷已经提交")

    now = datetime.utcnow()

    if session.expires_at and now >= session.expires_at:
        session.status = "expired"
        await db.commit()
        raise HTTPException(
            status_code=400,
            detail="填写时间已结束，本次填写已记为无效",
        )
    # 非匿名问卷必须填写姓名和邮箱
    if not questionnaire.anonymous:
        if not payload.respondentName:
            raise HTTPException(
                status_code=400,
                detail="请输入姓名",
            )

        if not payload.respondentEmail:
            raise HTTPException(
                status_code=400,
                detail="请输入邮箱",
            )

    if questionnaire.one_response:
        duplicate_conditions = [
            Response.questionnaire_id == questionnaire.id,
        ]

        if questionnaire.anonymous:
            if not submitted_ip:
                raise HTTPException(
                    status_code=400,
                    detail="无法识别填写者，不能验证是否重复提交",
                )
            duplicate_conditions.append(
                Response.submitted_ip == submitted_ip
            )
        else:
            duplicate_conditions.append(
                func.lower(Response.respondent_email)
                == payload.respondentEmail.strip().lower()
            )

        existing_response_id = await db.scalar(
            select(Response.id)
            .where(*duplicate_conditions)
            .limit(1)
        )

        if existing_response_id is not None:
            raise HTTPException(
                status_code=409,
                detail="该问卷仅允许每人提交一次",
            )

    questions_by_id = {
        question.id: question
        for question in questionnaire.questions
    }

    received = {
        answer.questionId: answer
        for answer in payload.answers
    }

    # 检查必填题和选项
    for question in questionnaire.questions:
        answer = received.get(question.id)

        if question.required and (
            answer is None
            or (
                not answer.content
                and not answer.optionIds
            )
        ):
            raise HTTPException(
                status_code=400,
                detail=f"请完成必填题：{question.title}",
            )

        if answer and question.type == "single":
            if len(answer.optionIds) > 1:
                raise HTTPException(
                    status_code=400,
                    detail="单选题只能选择一个选项",
                )

        if answer and question.type in {
            "single",
            "multiple",
        }:
            valid_option_ids = {
                option.id
                for option in question.options
            }

            if any(
                option_id not in valid_option_ids
                for option_id in answer.optionIds
            ):
                raise HTTPException(
                    status_code=400,
                    detail="提交的选项不属于该题目",
                )

    response = Response(
        questionnaire_id=questionnaire.id,
        respondent_name=payload.respondentName,
        respondent_email=payload.respondentEmail,
        source=payload.source,
        duration_seconds=payload.durationSeconds,
        submitted_ip=submitted_ip,
        user_agent=(
            user_agent[:500]
            if user_agent
            else None
        ),
    )

    db.add(response)
    await db.flush()


    if payload.sessionToken:
        result = await db.execute(
            select(ResponseSession).where(
                ResponseSession.session_token == payload.sessionToken,
                ResponseSession.questionnaire_id == questionnaire.id,
            )
        )
        session = result.scalar_one_or_none()

        if session:
            session.status = "completed"
            session.response_id = response.id
            session.completed_at = now
            session.last_activity_at = now
    # 创建答案
    for question_id, answer_data in received.items():
        if question_id not in questions_by_id:
            continue

        answer = Answer(
            response_id=response.id,
            question_id=question_id,
            content=answer_data.content,
        )

        db.add(answer)
        await db.flush()

        for option_id in answer_data.optionIds:
            answer_option = AnswerOption(
                answer_id=answer.id,
                option_id=option_id,
            )

            db.add(answer_option)

    await db.flush()

    return response, questionnaire
