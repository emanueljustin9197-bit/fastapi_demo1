from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    String,
    func,
)
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
    from models.questionnaire import Questionnaire
    from models.answers import Answer

class Response(Base):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="答卷 ID",
    )


    questionnaire_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "questionnaires.id",
            ondelete="CASCADE",
            name="fk_responses_questionnaire",
        ),
        nullable=False,
    )

    respondent_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="填写者姓名",
    )

    respondent_email: Mapped[Optional[str]] = mapped_column(
        String(320),
        nullable=True,
        comment="填写者邮箱",
    )

    source: Mapped[str] = mapped_column(
        Enum(
            "publicLink",
            "wechat",
            "qrCode",
            name="response_source",
        ),
        nullable=False,
        default="publicLink",
        server_default="publicLink",
    )

    duration_seconds: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="填写耗时（秒）",
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="是否有效答卷",
    )

    risk_score: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=0,
        server_default="0",
        comment="异常风险分，0 到 100",
    )

    risk_reasons: Mapped[Optional[list[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="异常原因列表",
    )

    review_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        comment="pending/confirmed/dismissed",
    )

    submitted_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="提交 IP，可选",
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="浏览器信息，可选",
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )

    __table_args__ = (
        Index(
            "idx_responses_questionnaire_time",
            "questionnaire_id",
            "submitted_at",
        ),
        Index(
            "idx_responses_source",
            "source",
        ),
    )

    questionnaire: Mapped["Questionnaire"] = relationship(
        back_populates="responses",
    )

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="response",
        cascade="all, delete-orphan",
    )
