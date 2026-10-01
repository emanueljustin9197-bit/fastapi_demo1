"""Public submission request bodies."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AnswerInput(BaseModel):
    questionId: int
    optionIds: list[int] = Field(default_factory=list)
    content: Optional[str]= None


class SubmitResponseRequest(BaseModel):
    publicCode: str
    answers: list[AnswerInput]
    respondentName: Optional[str] = Field(default=None, max_length=100)
    respondentEmail: Optional[str] = Field(default=None, max_length=320)
    source: Literal["publicLink", "wechat", "qrCode"] = "publicLink"
    durationSeconds: int = Field(ge=0, default=0)
    sessionToken: Optional[str] = None


class StartResponseRequest(BaseModel):
    publicCode: str


class ActivityRequest(BaseModel):
    sessionToken: str


class AnomalyScanRequest(BaseModel):
    questionnaireId: int = Field(ge=1)


class ResponseValidityRequest(BaseModel):
    responseId: int = Field(ge=1)
    isValid: bool
__all__ = [
    "AnswerInput",
    "SubmitResponseRequest",
    "StartResponseRequest",
    "ActivityRequest",
    "AnomalyScanRequest",
    "ResponseValidityRequest",
]
