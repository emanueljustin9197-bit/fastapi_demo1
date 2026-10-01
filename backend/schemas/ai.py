"""Request bodies for the AI helper endpoints."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .questionnaire import QuestionInput


class AiGenerateRequest(BaseModel):
    prompt: str
    questionCount: int = Field(default=8, ge=1, le=50)
    language: str = "zh-CN"
    title: Optional[str] = None
    existingQuestions: list[dict[str, Any]] = Field(default_factory=list)


class AiOptimizeRequest(BaseModel):
    questions: list[QuestionInput]
    requirement: Optional[str] = None


class AiDimensionsRequest(BaseModel):
    title: str
    description: Optional[str] = None
    questions: list[QuestionInput] = Field(default_factory=list)


class AiSummarizeRequest(BaseModel):
    questionnaireId: int
    questionId: int


class AiAnalysisInsightRequest(BaseModel):
    questionnaireId: int
    range: Literal["7d", "30d"] = "7d"


class AiEvidence(BaseModel):
    sourceType: Literal["overview", "trend", "question"]
    sourceId: str
    text: str


class AiFinding(BaseModel):
    conclusion: str
    evidence: list[AiEvidence] = Field(min_length=1)


class AiAnalysisInsightResponse(BaseModel):
    findings: list[AiFinding]
    suggestions: list[str]


class AiAnalysisChatRequest(BaseModel):
    questionnaireId: int = Field(ge=1)
    range: Literal["7d", "30d"] = "7d"
    conversationId: str = Field(min_length=8, max_length=100)
    message: str = Field(min_length=1, max_length=500)

class AiAnalysisChatClearRequest(BaseModel):
    questionnaireId: int = Field(ge=1)
    conversationId: str = Field(min_length=8, max_length=100)

__all__ = [
    "AiGenerateRequest",
    "AiOptimizeRequest",
    "AiDimensionsRequest",
    "AiSummarizeRequest",
    "AiAnalysisInsightRequest",
]
