from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class ExportTask(Base):
    __tablename__ = "export_tasks"

    id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        comment="导出任务 ID，如 exp_20260831_001",
    )

    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            name="fk_export_tasks_user",
        ),
        nullable=False,
    )

    questionnaire_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "questionnaires.id",
            ondelete="CASCADE",
            name="fk_export_tasks_questionnaire",
        ),
        nullable=False,
    )

    format: Mapped[str] = mapped_column(
        Enum(
            "xlsx",
            "csv",
            "json",
            name="export_format",
        ),
        nullable=False,
    )

    data_range: Mapped[str] = mapped_column(
        Enum(
            "all",
            "week",
            "custom",
            name="export_data_range",
        ),
        nullable=False,
        default="all",
        server_default="all",
    )

    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    include_metadata: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "processing",
            "completed",
            "failed",
            name="export_status",
        ),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    progress: Mapped[int] = mapped_column(
        TINYINT(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
    )

    file_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    file_size: Mapped[Optional[int]] = mapped_column(
        BIGINT(unsigned=True),
        nullable=True,
    )

    row_count: Mapped[Optional[int]] = mapped_column(
        INTEGER(unsigned=True),
        nullable=True,
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "idx_export_tasks_user_created",
            "user_id",
            "created_at",
        ),
        Index(
            "idx_export_tasks_questionnaire",
            "questionnaire_id",
        ),
    )

    owner: Mapped["User"] = relationship(
        back_populates="export_tasks",
    )

    questionnaire: Mapped["Questionnaire"] = relationship(
        back_populates="export_tasks",
    )
