from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from crud.feedback import get_feedback_list
from models.user import User
from utils.jwt import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.get("/list")
async def feedback_list(
    questionnaireId: int = Query(..., ge=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await get_feedback_list(db, questionnaireId, user.id)
    if data is None:
        raise HTTPException(status_code=404, detail="问卷不存在或无权查看")
    return {"code": 200, "message": "success", "data": data}