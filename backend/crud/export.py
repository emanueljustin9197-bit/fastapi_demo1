"""Durable export-task operations and in-memory download content.

The database owns task metadata (the real ``export_tasks`` table); export
bytes stay in memory for now because the recovered project has no storage
directory configuration yet. This preserves the existing download API without
inventing a hidden file path.
"""



from __future__ import annotations

import csv
import io
import json
import secrets
from datetime import datetime, time, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.answers import AnswerOption, Answer
from models.export import ExportTask
from models.questionnaire import Questionnaire
from models.response import Response
from schemas.export import ExportRequest

_export_contents: dict[str, dict[str, Any]] = {}


async def create_export_task_by_id(
    db: AsyncSession,
    payload: ExportRequest,
    user_id: int,
):
    questionnaire_stmt = (
        select(Questionnaire)
        .options(
            selectinload(Questionnaire.questions).selectinload(
                Questionnaire.questions.property.mapper.class_.options
            )
        )
        .where(
            Questionnaire.id == payload.questionnaireId,
            Questionnaire.user_id == user_id,
        )
    )

    questionnaire_result = await db.execute(
        questionnaire_stmt
    )

    questionnaire = questionnaire_result.scalar_one_or_none()

    if questionnaire is None:
        return None

    if payload.range == "custom":
        if not payload.startDate or not payload.endDate:
            raise HTTPException(
                status_code=400,
                detail="自定义范围必须填写开始日期和结束日期",
            )

        if payload.startDate > payload.endDate:
            raise HTTPException(
                status_code=400,
                detail="开始日期不能晚于结束日期",
            )

    response_conditions = [
        Response.questionnaire_id == questionnaire.id
    ]

    if payload.range == "week":
        start_date = datetime.utcnow().date() - timedelta(days=6)
        start_datetime = datetime.combine(
            start_date,
            time.min,
        )

        response_conditions.append(
            Response.submitted_at >= start_datetime
        )

    if payload.range == "custom":
        start_datetime = datetime.combine(
            payload.startDate,
            time.min,
        )

        end_datetime = datetime.combine(
            payload.endDate + timedelta(days=1),
            time.min,
        )

        response_conditions.append(
            Response.submitted_at >= start_datetime
        )

        response_conditions.append(
            Response.submitted_at < end_datetime
        )

    response_stmt = (
        select(Response)
        .options(
            selectinload(Response.answers).selectinload(
                Answer.selected_options
            ).selectinload(
                AnswerOption.option
            )
        )
        .where(*response_conditions)
        .order_by(Response.submitted_at.asc())
    )

    response_result = await db.execute(response_stmt)
    responses = response_result.scalars().all()

    task_id = (
        f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_"
        f"{secrets.token_hex(2)}"
    )

    safe_title = "".join(
        "_"
        if char in '\\/:*?"<>|'
        else char
        for char in questionnaire.title
    ).strip()

    safe_title = safe_title[:100] or "questionnaire"

    file_name = (
        f"{safe_title}_"
        f"{datetime.utcnow().strftime('%Y%m%d')}"
        f".{payload.format}"
    )

    headers = []

    if payload.includeMetadata:
        headers.extend(
            [
                "responseId",
                "respondentName",
                "respondentEmail",
                "source",
                "durationSeconds",
                "isValid",
                "submittedAt",
            ]
        )

    question_headers = []

    for question in questionnaire.questions:
        question_header = f"{question.title}（题目ID:{question.id}）"
        question_headers.append(question_header)

    headers.extend(question_headers)

    rows = []
    json_rows = []

    for response in responses:
        answer_map = {
            answer.question_id: answer
            for answer in response.answers
        }

        row = []

        if payload.includeMetadata:
            row.extend(
                [
                    response.id,
                    response.respondent_name,
                    response.respondent_email,
                    response.source,
                    response.duration_seconds,
                    response.is_valid,
                    response.submitted_at.isoformat(
                        sep=" ",
                        timespec="seconds",
                    ),
                ]
            )

        json_row = {}

        if payload.includeMetadata:
            json_row = {
                "responseId": response.id,
                "respondentName": response.respondent_name,
                "respondentEmail": response.respondent_email,
                "source": response.source,
                "durationSeconds": response.duration_seconds,
                "isValid": response.is_valid,
                "submittedAt": response.submitted_at.isoformat(
                    sep=" ",
                    timespec="seconds",
                ),
            }

        for question in questionnaire.questions:
            answer = answer_map.get(question.id)

            if answer is None:
                value = ""
            else:
                option_labels = [
                    selected_option.option.label
                    for selected_option in answer.selected_options
                    if selected_option.option
                ]

                if option_labels:
                    value = "、".join(option_labels)
                else:
                    value = answer.content or ""

            row.append(value)

            json_row[f"question_{question.id}"] = value

        rows.append(row)
        json_rows.append(json_row)

    if payload.format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)

        content = output.getvalue().encode("utf-8-sig")
        media_type = "text/csv"

    elif payload.format == "json":
        content = json.dumps(
            json_rows,
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")

        media_type = "application/json"

    else:
        try:
            from openpyxl import Workbook
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="导出 XLSX 需要安装 openpyxl",
            )

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "问卷结果"

        worksheet.append(headers)

        for row in rows:
            worksheet.append(row)

        output = io.BytesIO()
        workbook.save(output)

        content = output.getvalue()

        media_type = (
            "application/"
            "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    task = ExportTask(
        id=task_id,
        user_id=user_id,
        questionnaire_id=questionnaire.id,
        format=payload.format,
        data_range=payload.range,
        start_date=payload.startDate,
        end_date=payload.endDate,
        include_metadata=payload.includeMetadata,
        status="completed",
        progress=100,
        file_name=file_name,
        file_size=len(content),
        row_count=len(rows),
        completed_at=datetime.utcnow(),
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    _export_contents[task.id] = {
        "content": content,
        "media_type": media_type,
        "file_name": file_name,
    }

    return task


async def get_export_list_by_id(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
):
    count_stmt = select(
        func.count(ExportTask.id)
    ).where(
        ExportTask.user_id == user_id
    )

    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    offset = (page - 1) * page_size

    stmt = (
        select(ExportTask)
        .options(
            selectinload(ExportTask.questionnaire)
        )
        .where(
            ExportTask.user_id == user_id
        )
        .order_by(
            ExportTask.created_at.desc()
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


async def get_export_status_by_id(
    db: AsyncSession,
    export_id: str,
    user_id: int,
):
    stmt = (
        select(ExportTask)
        .options(
            selectinload(ExportTask.questionnaire)
        )
        .where(
            ExportTask.id == export_id,
            ExportTask.user_id == user_id,
        )
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def get_download_file_by_id(
    db: AsyncSession,
    export_id: str,
    user_id: int,
):
    task = await get_export_status_by_id(
        db=db,
        export_id=export_id,
        user_id=user_id,
    )

    if task is None:
        return None

    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="导出任务尚未完成",
        )

    export_content = _export_contents.get(task.id)

    if export_content is None:
        raise HTTPException(
            status_code=404,
            detail="导出文件不存在，请重新创建导出任务",
        )

    return {
        "task": task,
        "content": export_content["content"],
        "media_type": export_content["media_type"],
        "file_name": export_content["file_name"],
    }


async def delete_export_task_by_id(
    db: AsyncSession,
    export_id: str,
    user_id: int,
):
    task = await get_export_status_by_id(
        db=db,
        export_id=export_id,
        user_id=user_id,
    )

    if task is None:
        return None

    await db.delete(task)
    await db.commit()

    _export_contents.pop(export_id, None)

    return True
