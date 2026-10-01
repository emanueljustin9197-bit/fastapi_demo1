from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base
from .questionnaire import Question, QuestionOption
from .response import Response
class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
    )

    response_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "responses.id",
            ondelete="CASCADE",
            name="fk_answers_response",
        ),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "questions.id",
            ondelete="CASCADE",
            name="fk_answers_question",
        ),
        nullable=False,
    )

    content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="文本、日期、评分、数字、电话等内容",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )

    __table_args__ = (
        UniqueConstraint(
            "response_id",
            "question_id",
            name="uk_answers_response_question",
        ),
        Index(
            "idx_answers_question",
            "question_id",
        ),
    )

    response: Mapped["Response"] = relationship(
        back_populates="answers",
    )

    question: Mapped["Question"] = relationship(
        back_populates="answers",
    )

    selected_options: Mapped[list["AnswerOption"]] = relationship(
        back_populates="answer",
        cascade="all, delete-orphan",
    )



class AnswerOption(Base):
    __tablename__ = "answer_options"

    answer_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "answers.id",
            ondelete="CASCADE",
            name="fk_answer_options_answer",
        ),
        primary_key=True,
        nullable=False,
    )

    option_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True),
        ForeignKey(
            "question_options.id",
            ondelete="CASCADE",
            name="fk_answer_options_option",
        ),
        primary_key=True,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "idx_answer_options_option",
            "option_id",
        ),
    )

    answer: Mapped["Answer"] = relationship(
        back_populates="selected_options",
    )

    option: Mapped["QuestionOption"] = relationship(
        back_populates="answer_links",
    )
