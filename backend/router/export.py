"""Export task HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

"""Export task HTTP endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import quote

from crud.export import (
    create_export_task_by_id as crud_create_export_task_by_id,
    delete_export_task_by_id as crud_delete_export_task_by_id,
    get_download_file_by_id as crud_get_download_file_by_id,
    get_export_list_by_id as crud_get_export_list_by_id,
    get_export_status_by_id as crud_get_export_status_by_id,
)

from models.user import User
from schemas.export import ExportRequest
from config.database import get_db
from utils.jwt import get_current_user


router = APIRouter(
    prefix="/api/export",
    tags=["export"],
)


@router.post("/create")
async def create_export_task_by_id(
    payload: ExportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await crud_create_export_task_by_id(
        db=db,
        payload=payload,
        user_id=user.id,
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="问卷不存在或无权导出",
        )

    return {
        "code": 200,
        "message": "导出任务已创建",
        "data": {
            "id": task.id,
            "status": task.status,
            "createdAt": task.created_at,
        },
    }


@router.get("/list")
async def get_export_list_by_id(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    export_data = await crud_get_export_list_by_id(
        db=db,
        user_id=user.id,
        page=page,
        page_size=pageSize,
    )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "list": [
                {
                    "id": item.id,
                    "questionnaireId": item.questionnaire_id,
                    "questionnaireTitle": (
                        item.questionnaire.title
                        if item.questionnaire
                        else ""
                    ),
                    "format": (
                        item.format.value
                        if hasattr(item.format, "value")
                        else item.format
                    ),
                    "range": (
                        item.data_range.value
                        if hasattr(item.data_range, "value")
                        else item.data_range
                    ),
                    "startDate": item.start_date,
                    "endDate": item.end_date,
                    "includeMetadata": item.include_metadata,
                    "status": (
                        item.status.value
                        if hasattr(item.status, "value")
                        else item.status
                    ),
                    "progress": item.progress,
                    "fileName": item.file_name,
                    "fileSize": item.file_size,
                    "rowCount": item.row_count,
                    "downloadUrl": (
                        f"/api/export/download?id={item.id}"
                        if (
                                item.status == "completed"
                                or getattr(item.status, "value", None) == "completed"
                        )
                        else None
                    ),
                    "errorMessage": item.error_message,
                    "createdAt": item.created_at,
                    "completedAt": item.completed_at,
                }
                for item in export_data["list"]
            ],
            "total": export_data["total"],
            "hasMore": export_data["hasMore"],
        },
    }


@router.get("/status")
async def get_export_status_by_id(
    id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await crud_get_export_status_by_id(
        db=db,
        export_id=id,
        user_id=user.id,
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="导出任务不存在或无权查看",
        )

    download_url = None

    if task.status == "completed":
        download_url = f"/api/export/download?id={task.id}"

    return {
        "code": 200,
        "message": "success",
        "data": {
            "id": task.id,
            "status": task.status,
            "progress": task.progress,
            "downloadUrl": download_url,
            "errorMessage": task.error_message,
        },
    }


@router.get("/download")
async def get_download_file_by_id(
    id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    export_data = await crud_get_download_file_by_id(
        db=db,
        export_id=id,
        user_id=user.id,
    )

    if export_data is None:
        raise HTTPException(
            status_code=404,
            detail="导出任务不存在或无权下载",
        )

    file_name = export_data["file_name"]
    encoded_file_name = quote(file_name)

    return Response(
        content=export_data["content"],
        media_type=export_data["media_type"],
        headers={
            "Content-Disposition": (
                "attachment; "
                f"filename*=UTF-8''{encoded_file_name}"
            )
        },
    )


@router.delete("/delete")
async def delete_export_task_by_id(
    id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await crud_delete_export_task_by_id(
        db=db,
        export_id=id,
        user_id=user.id,
    )

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="导出记录不存在或无权删除",
        )

    return {
        "code": 200,
        "message": "删除成功",
        "data": None,
    }