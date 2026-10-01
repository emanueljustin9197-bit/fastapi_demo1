from collections import Counter

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.answers import Answer
from models.questionnaire import Questionnaire, Question
from models.response import Response


def calculate_risk(response: Response, questionnaire: Questionnaire):
    score = 0
    reasons: list[str] = []
    question_count = len(questionnaire.questions)

    # 1. 填写速度异常
    minimum_seconds = max(5, question_count * 2)
    if response.duration_seconds < minimum_seconds:
        score += 40
        reasons.append(
            f"填写时间异常短：{response.duration_seconds} 秒"
        )

    # 2. 回答比例过低
    answered = [
        answer
        for answer in response.answers
        if (
            answer.content
            and answer.content.strip()
        ) or answer.selected_options
    ]

    if question_count and len(answered) / question_count < 0.3:
        score += 25
        reasons.append("作答题目比例低于 30%")

    # 建立“选项 ID -> 选项位置”映射
    option_positions: dict[int, int] = {}

    for question in questionnaire.questions:
        for index, option in enumerate(question.options):
            option_positions[option.id] = index

    # 3. 连续选择相同位置
    selected_positions: list[int] = []

    for answer in response.answers:
        if len(answer.selected_options) == 1:
            option_id = answer.selected_options[0].option_id
            position = option_positions.get(option_id)

            if position is not None:
                selected_positions.append(position)

    if len(selected_positions) >= 5:
        most_common_count = Counter(
            selected_positions
        ).most_common(1)[0][1]

        if most_common_count / len(selected_positions) >= 0.8:
            score += 25
            reasons.append("80% 以上选择题选择了相同位置")

    # 4. 文本答案高度重复
    texts = [
        answer.content.strip().lower()
        for answer in response.answers
        if answer.content and answer.content.strip()
    ]

    if len(texts) >= 3:
        most_common_text_count = Counter(
            texts
        ).most_common(1)[0][1]

        if most_common_text_count / len(texts) >= 0.8:
            score += 20
            reasons.append("多个文本答案内容高度重复")

    return min(score, 100), reasons


async def scan_questionnaire_responses(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
):
    stmt = (
        select(Questionnaire)
        .options(
            selectinload(
                Questionnaire.questions
            ).selectinload(
                Question.options
            ),
            selectinload(
                Questionnaire.responses
            ).selectinload(
                Response.answers
            ).selectinload(
                Answer.selected_options
            ),
        )
        .where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.user_id == user_id,
        )
    )

    questionnaire = (
        await db.execute(stmt)
    ).scalar_one_or_none()

    if questionnaire is None:
        return None

    for response in questionnaire.responses:
        score, reasons = calculate_risk(
            response,
            questionnaire,
        )

        response.risk_score = score
        response.risk_reasons = reasons

        # 不覆盖管理员已经作出的人工判断
        if response.review_status not in {
            "confirmed",
            "dismissed",
        }:
            response.review_status = "pending"

    await db.flush()

    return {
        "scannedCount": len(questionnaire.responses),
        "anomalyCount": sum(
            response.risk_score >= 40
            for response in questionnaire.responses
        ),
    }


async def get_anomalous_responses(
    db: AsyncSession,
    questionnaire_id: int,
    user_id: int,
):
    stmt = (
        select(Response)
        .join(
            Questionnaire,
            Questionnaire.id == Response.questionnaire_id,
        )
        .where(
            Response.questionnaire_id == questionnaire_id,
            Questionnaire.user_id == user_id,
            or_(
                Response.risk_score >= 40,
                Response.review_status == "confirmed",
            ),
        )
        .order_by(
            Response.risk_score.desc(),
            Response.submitted_at.desc(),
        )
    )

    responses = (
        await db.execute(stmt)
    ).scalars().all()

    return {
        "list": [
            {
                "id": response.id,
                "respondentName": response.respondent_name,
                "respondentEmail": response.respondent_email,
                "durationSeconds": response.duration_seconds,
                "submittedAt": response.submitted_at,
                "isValid": response.is_valid,
                "riskScore": response.risk_score,
                "riskReasons": response.risk_reasons or [],
                "reviewStatus": response.review_status,
            }
            for response in responses
        ],
        "total": len(responses),
    }


async def update_response_validity(
    db: AsyncSession,
    response_id: int,
    is_valid: bool,
    user_id: int,
):
    stmt = (
        select(Response)
        .join(
            Questionnaire,
            Questionnaire.id == Response.questionnaire_id,
        )
        .where(
            Response.id == response_id,
            Questionnaire.user_id == user_id,
        )
    )

    response = (
        await db.execute(stmt)
    ).scalar_one_or_none()

    if response is None:
        return None

    response.is_valid = is_valid
    response.review_status = (
        "dismissed"
        if is_valid
        else "confirmed"
    )

    await db.flush()
    return response