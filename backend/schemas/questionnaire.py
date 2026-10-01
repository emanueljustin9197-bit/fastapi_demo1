"""Questionnaire, question and option request bodies."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OptionInput(BaseModel):
    id: Optional[int] = None
    label: str
    sortOrder: int = 0


QuestionType = Literal["single", "multiple", "text", "date", "rating", "number", "phone"]


class QuestionInput(BaseModel):
    id: Optional[int] = None
    type: QuestionType
    title: str
    required: bool = False
    sortOrder: int = 0
    options: list[OptionInput] = Field(default_factory=list)


class QuestionnaireInput(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    anonymous: bool = True
    oneResponse: bool = False
    showResult: bool = False
    questions: list[QuestionInput] = Field(default_factory=list)
    responseTimeoutMinutes: int = Field(default=30, ge=1, le=1440)


class QuestionnaireUpdateRequest(QuestionnaireInput):
    id: int
    responseTimeoutMinutes: int = Field(default=30, ge=1, le=1440)


class IdRequest(BaseModel):
    id: int

