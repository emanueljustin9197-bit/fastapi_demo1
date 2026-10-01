from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class ResponseSession(Base):
    __tablename__ = "response_sessions"

    id: Mapped[int] = mapped_column(BIGINT(unsigned=True), primary_key=True)
    questionnaire_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("questionnaires.id", ondelete="CASCADE"),
        nullable=False,
    )
    response_id: Mapped[Optional[int]] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("responses.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    session_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)