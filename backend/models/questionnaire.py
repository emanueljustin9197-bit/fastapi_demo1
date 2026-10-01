from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
    from models.export import ExportTask
    from models.response import  Response
    from models.answers import AnswerOption,Answer
    from models.user import User


class QuestionnaireStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class QuestionType(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    TEXT = "text"
    DATE = "date"
    RATING = "rating"
    NUMBER = "number"
    PHONE = "phone"


class Questionnaire(Base):
    __tablename__ = "questionnaires"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[QuestionnaireStatus] = mapped_column(
        SQLEnum(
            QuestionnaireStatus,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=QuestionnaireStatus.DRAFT,
        server_default="draft",
    )

    anonymous: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )

    one_response: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )

    show_result: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )

    public_code: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
    )

    public_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    background_image: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped["User"] = relationship(
        back_populates="questionnaires",
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="questionnaire",
        cascade="all, delete-orphan",
        order_by="Question.sort_order",
    )

    responses: Mapped[list["Response"]] = relationship(
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )

    export_tasks: Mapped[list["ExportTask"]] = relationship(
        back_populates="questionnaire",
        cascade="all, delete-orphan",
    )
    response_timeout_minutes: Mapped[int] = mapped_column(
        INTEGER(unsigned=True),
        nullable=False,
        default=30,
        server_default="30",
    )


class Question(Base):
    __tablename__ = "questions"

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

    type: Mapped[QuestionType] = mapped_column(
        SQLEnum(
            QuestionType,
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )

    sort_order: Mapped[int] = mapped_column(
        INTEGER,
        nullable=False,
        default=0,
        server_default="0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    questionnaire: Mapped["Questionnaire"] = relationship(
        back_populates="questions",
    )

    options: Mapped[list["QuestionOption"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.sort_order",
    )

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="question",
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    question_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        INTEGER,
        nullable=False,
        default=0,
        server_default="0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    question: Mapped["Question"] = relationship(
        back_populates="options",
    )

    answer_links: Mapped[list["AnswerOption"]] = relationship(
        back_populates="option",
    )
