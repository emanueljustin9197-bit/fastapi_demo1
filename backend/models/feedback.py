from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    questionnaire_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("questionnaires.id", ondelete="CASCADE"),
        nullable=False,
    )

    response_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("responses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    rating: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
    )

    issue_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="none",
        server_default="none",
    )

    content: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )